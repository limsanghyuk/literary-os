"""
test_v619_optimization_orchestrator.py
V619 OptimizationOrchestrator v1.0 단위·통합 테스트 (25 TC)

클래스 구성
-----------
TestOptOrchestratorConfig      (5 TC) — 설정 검증 + helper 변환
TestStageResult             (4 TC) — StageResult 필드 + to_dict
TestOptimizationReport      (6 TC) — 집계 프로퍼티 + summary + to_dict
TestOptimizationOrchestrator(7 TC) — 파이프라인 실행 시나리오
TestOrchestratorEdgeCases   (3 TC) — 경계·오류 경로
"""
from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

import pytest

from literary_system.optimization.optimization_orchestrator import (
    OptimizationOrchestrator,
    OptimizationReport,
    OptOrchestratorConfig,
    StageResult,
)
from literary_system.optimization.adaptive_throttler import ThrottleConfig
from literary_system.optimization.long_run_monitor import LongRunConfig
from literary_system.optimization.stress_tester import StressConfig


# ---------------------------------------------------------------------------
# 공통 헬퍼
# ---------------------------------------------------------------------------

def _fast_fn() -> None:
    """즉시 반환하는 목업 fn."""
    time.sleep(0.001)


def _orch(**kw) -> OptimizationOrchestrator:
    """최소 설정 오케스트레이터 생성."""
    defaults = dict(
        warmup_iters=1,
        sustained_iters=3,
        cooldown_iters=1,
        target_p95_ms=5000.0,
        leak_threshold_mb=50.0,
        epochs=1,
        initial_concurrency=2,
        warn_threshold_ms=3000.0,
        recover_threshold_ms=100.0,
        throttle_calls=5,
    )
    defaults.update(kw)
    return OptimizationOrchestrator(OptOrchestratorConfig(**defaults))


# ===========================================================================
# TestOptOrchestratorConfig  (5 TC)
# ===========================================================================

class TestOptOrchestratorConfig:

    def test_defaults(self):
        cfg = OptOrchestratorConfig()
        assert cfg.warmup_iters == 2
        assert cfg.sustained_iters == 10
        assert cfg.cooldown_iters == 2
        assert cfg.target_p95_ms == 1500.0
        assert cfg.leak_threshold_mb == 10.0
        assert cfg.epochs == 3
        assert cfg.initial_concurrency == 4
        assert cfg.warn_threshold_ms == 1200.0
        assert cfg.recover_threshold_ms == 800.0
        assert cfg.throttle_calls == 20
        assert cfg.memory_budget_mb is None

    def test_custom_values(self):
        cfg = OptOrchestratorConfig(epochs=5, target_p95_ms=999.0, memory_budget_mb=500.0)
        assert cfg.epochs == 5
        assert cfg.target_p95_ms == 999.0
        assert cfg.memory_budget_mb == 500.0

    def test_to_stress_config(self):
        cfg = OptOrchestratorConfig(warmup_iters=3, sustained_iters=7, target_p95_ms=800.0)
        sc = cfg.to_stress_config()
        assert isinstance(sc, StressConfig)
        assert sc.warmup_iters == 3
        assert sc.sustained_iters == 7
        assert sc.target_p95_ms == 800.0

    def test_to_longrun_config(self):
        cfg = OptOrchestratorConfig(epochs=4, leak_threshold_mb=20.0, memory_budget_mb=300.0)
        lr = cfg.to_longrun_config()
        assert isinstance(lr, LongRunConfig)
        assert lr.epochs == 4
        assert lr.leak_threshold_mb == 20.0
        assert lr.memory_budget_mb == 300.0

    def test_to_throttle_config(self):
        cfg = OptOrchestratorConfig(
            initial_concurrency=8, warn_threshold_ms=999.9, recover_threshold_ms=400.0
        )
        tc = cfg.to_throttle_config()
        assert isinstance(tc, ThrottleConfig)
        assert tc.initial_concurrency == 8
        assert tc.warn_threshold_ms == 999.9
        assert tc.recover_threshold_ms == 400.0


# ===========================================================================
# TestStageResult  (4 TC)
# ===========================================================================

class TestStageResult:

    def test_pass_stage(self):
        s = StageResult(stage="BASELINE", passed=True, duration_s=0.5, detail="ok")
        assert s.stage == "BASELINE"
        assert s.passed is True
        assert s.duration_s == 0.5
        assert s.detail == "ok"

    def test_fail_stage(self):
        s = StageResult(stage="STRESS", passed=False, duration_s=1.2, detail="P95 초과")
        assert s.passed is False

    def test_to_dict_keys(self):
        s = StageResult(stage="LEAK", passed=True, duration_s=0.3)
        d = s.to_dict()
        assert set(d.keys()) == {"stage", "passed", "duration_s", "detail"}
        assert d["stage"] == "LEAK"
        assert d["passed"] is True

    def test_to_dict_rounding(self):
        s = StageResult(stage="LONGRUN", passed=True, duration_s=1.23456789)
        d = s.to_dict()
        assert d["duration_s"] == round(1.23456789, 4)


# ===========================================================================
# TestOptimizationReport  (6 TC)
# ===========================================================================

class TestOptimizationReport:

    def _report(self, results) -> OptimizationReport:
        cfg = OptOrchestratorConfig()
        r = OptimizationReport(config=cfg)
        for stage, passed in results:
            r.stages.append(StageResult(stage=stage, passed=passed, duration_s=0.1))
        r.total_duration_s = 1.0
        return r

    def test_all_pass_true(self):
        r = self._report([("BASELINE", True), ("STRESS", True), ("LEAK", True)])
        assert r.all_pass is True

    def test_all_pass_false(self):
        r = self._report([("BASELINE", True), ("STRESS", False)])
        assert r.all_pass is False

    def test_failed_stages(self):
        r = self._report([("BASELINE", True), ("STRESS", False), ("LEAK", False)])
        assert set(r.failed_stages) == {"STRESS", "LEAK"}

    def test_passed_count(self):
        r = self._report([("BASELINE", True), ("STRESS", True), ("LEAK", False)])
        assert r.passed_count == 2
        assert r.total_count == 3

    def test_summary_pass(self):
        r = self._report([("BASELINE", True), ("STRESS", True)])
        s = r.summary()
        assert "PASS" in s
        assert "2/2" in s

    def test_to_dict_structure(self):
        r = self._report([("BASELINE", True)])
        d = r.to_dict()
        assert "all_pass" in d
        assert "stages" in d
        assert isinstance(d["stages"], list)


# ===========================================================================
# TestOptimizationOrchestrator  (7 TC)
# ===========================================================================

class TestOptimizationOrchestrator:

    def test_run_returns_report(self):
        orch = _orch()
        report = orch.run(_fast_fn)
        assert isinstance(report, OptimizationReport)

    def test_run_five_stages(self):
        orch = _orch()
        report = orch.run(_fast_fn)
        names = [s.stage for s in report.stages]
        assert names == ["BASELINE", "STRESS", "LEAK", "LONGRUN", "THROTTLE"]

    def test_run_all_pass_fast_fn(self):
        orch = _orch()
        report = orch.run(_fast_fn)
        assert report.all_pass, f"실패 단계: {report.failed_stages}"

    def test_run_populates_sub_reports(self):
        orch = _orch()
        report = orch.run(_fast_fn)
        assert report.stress_result is not None
        assert report.leak_report is not None
        assert report.longrun_report is not None
        assert report.throttle_report is not None

    def test_run_total_duration_positive(self):
        orch = _orch()
        report = orch.run(_fast_fn)
        assert report.total_duration_s > 0

    def test_quick_run(self):
        report = OptimizationOrchestrator.quick_run(_fast_fn, target_p95_ms=5000.0, epochs=1)
        assert isinstance(report, OptimizationReport)
        assert len(report.stages) == 5

    def test_run_with_memory_sampler(self):
        call_count = [0]

        def _sampler() -> float:
            call_count[0] += 1
            return 50.0

        orch = _orch(memory_budget_mb=200.0)
        report = orch.run(_fast_fn, memory_sampler=_sampler)
        assert report.all_pass
        assert call_count[0] > 0


# ===========================================================================
# TestOrchestratorEdgeCases  (3 TC)
# ===========================================================================

class TestOrchestratorEdgeCases:

    def test_default_config_on_init(self):
        orch = OptimizationOrchestrator()
        assert isinstance(orch.config, OptOrchestratorConfig)
        assert orch.config.epochs == 3

    def test_to_dict_contains_stress_p95(self):
        orch = _orch()
        report = orch.run(_fast_fn)
        d = report.to_dict()
        assert "stress_p95_ms" in d
        # fast_fn 이므로 P95 는 양수
        assert d["stress_p95_ms"] is not None
        assert d["stress_p95_ms"] >= 0

    def test_summary_fail_label(self):
        cfg = OptOrchestratorConfig()
        report = OptimizationReport(config=cfg)
        report.stages.append(StageResult(stage="BASELINE", passed=False, duration_s=0.1))
        assert "FAIL" in report.summary()
