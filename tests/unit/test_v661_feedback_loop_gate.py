"""V661 — FeedbackLoopGate G69 테스트 (33 TC).

ADR-121: 24h 무중단 피드백 파이프라인 안정성 게이트
"""
from __future__ import annotations

import pytest

from literary_system.feedback.reader_feedback_collector import (
    ConsentLevel,
    FeedbackType,
    PIIPurgePolicy,
    ReaderFeedbackCollector,
)
from literary_system.feedback.feedback_to_rlhf import (
    FeedbackToRLHFAdapter,
    OutlierPolicy,
)
from literary_system.gates.feedback_loop_gate import (
    FeedbackLoopGate,
    LoopSimReport,
    LoopTickResult,
    TICK_COUNT,
    MIN_FEEDBACK_PER_TICK,
    PURGE_EVERY_N_TICKS,
    MAX_ALLOWED_ERRORS,
    run_g69,
)


# ── 헬퍼 ──────────────────────────────────────────────────────────────

def _make_gate(feedbacks_per_tick: int = MIN_FEEDBACK_PER_TICK, **kwargs) -> FeedbackLoopGate:
    collector = ReaderFeedbackCollector(
        policy=PIIPurgePolicy(retention_days=14),
        required_consent=ConsentLevel.ANONYMOUS,
    )
    adapter = FeedbackToRLHFAdapter(
        policy=OutlierPolicy(z_threshold=2.0, min_samples_after_filter=1),
    )
    return FeedbackLoopGate(
        collector=collector,
        adapter=adapter,
        feedbacks_per_tick=feedbacks_per_tick,
        **kwargs,
    )


# ── TC-01~05: 상수 및 파라미터 ───────────────────────────────────────

class TestConstants:
    def test_tc01_tick_count(self):
        """TC-01: TICK_COUNT == 24."""
        assert TICK_COUNT == 24

    def test_tc02_min_feedback_per_tick(self):
        """TC-02: MIN_FEEDBACK_PER_TICK >= 5."""
        assert MIN_FEEDBACK_PER_TICK >= 5

    def test_tc03_purge_interval(self):
        """TC-03: PURGE_EVERY_N_TICKS == 6 (6h 주기)."""
        assert PURGE_EVERY_N_TICKS == 6

    def test_tc04_max_errors(self):
        """TC-04: MAX_ALLOWED_ERRORS == 0 (무중단 조건)."""
        assert MAX_ALLOWED_ERRORS == 0

    def test_tc05_gate_id(self):
        """TC-05: 게이트 ID 검증."""
        gate = _make_gate()
        report = gate.run()
        assert report.gate_id == "G69"


# ── TC-06~10: LoopTickResult ─────────────────────────────────────────

class TestLoopTickResult:
    def test_tc06_success_property_true(self):
        """TC-06: error=None → success=True."""
        r = LoopTickResult(0, 0, 5, 5, 5, 0, -1, None, 1.0)
        assert r.success is True

    def test_tc07_success_property_false(self):
        """TC-07: error 존재 → success=False."""
        r = LoopTickResult(0, 0, 0, 0, 0, 0, -1, "err", 1.0)
        assert r.success is False

    def test_tc08_loss_count_zero(self):
        """TC-08: collected==converted+outliers → loss_count=0."""
        r = LoopTickResult(0, 0, 7, 5, 5, 2, -1, None, 1.0)
        assert r.loss_count == 0

    def test_tc09_loss_count_positive(self):
        """TC-09: loss 발생 시 loss_count > 0."""
        r = LoopTickResult(0, 0, 10, 6, 6, 1, -1, None, 1.0)
        # collected=10, converted=6, outliers=1 → loss=10-6-1=3
        assert r.loss_count == 3

    def test_tc10_purge_count_minus1_means_skipped(self):
        """TC-10: purge_count=-1 은 purge 미실행."""
        r = LoopTickResult(0, 0, 5, 5, 5, 0, -1, None, 1.0)
        assert r.purge_count == -1


# ── TC-11~17: LoopSimReport 기본 구조 ───────────────────────────────

class TestLoopSimReport:
    def test_tc11_passed_is_bool(self):
        """TC-11: passed 필드 bool 타입."""
        r = LoopSimReport()
        assert isinstance(r.passed, bool)

    def test_tc12_to_dict_has_required_keys(self):
        """TC-12: to_dict() 필수 키 존재."""
        r = LoopSimReport()
        d = r.to_dict()
        for key in ("gate_id", "gate_name", "passed", "tick_count",
                    "success_ticks", "error_ticks", "total_collected",
                    "total_converted", "total_loss", "errors", "summary"):
            assert key in d, f"missing key: {key}"

    def test_tc13_to_dict_gate_name(self):
        """TC-13: gate_name == 'FeedbackLoopGate'."""
        r = LoopSimReport()
        assert r.to_dict()["gate_name"] == "FeedbackLoopGate"

    def test_tc14_ticks_list_default_empty(self):
        """TC-14: ticks 기본값 빈 리스트."""
        r = LoopSimReport()
        assert r.ticks == []

    def test_tc15_errors_list_default_empty(self):
        """TC-15: errors 기본값 빈 리스트."""
        r = LoopSimReport()
        assert r.errors == []

    def test_tc16_elapsed_ms_float(self):
        """TC-16: elapsed_ms float 타입."""
        r = LoopSimReport(elapsed_ms=123.456)
        d = r.to_dict()
        assert isinstance(d["elapsed_ms"], float)

    def test_tc17_summary_in_dict(self):
        """TC-17: summary 키 존재."""
        r = LoopSimReport(summary="test")
        assert r.to_dict()["summary"] == "test"


# ── TC-18~25: FeedbackLoopGate 실행 ─────────────────────────────────

class TestFeedbackLoopGateRun:
    def test_tc18_run_returns_report(self):
        """TC-18: run() → LoopSimReport 반환."""
        gate = _make_gate()
        result = gate.run()
        assert isinstance(result, LoopSimReport)

    def test_tc19_tick_count_equals_24(self):
        """TC-19: 시뮬레이션 완주 — tick_count == 24."""
        gate = _make_gate()
        result = gate.run()
        assert result.tick_count == TICK_COUNT

    def test_tc20_ticks_length_24(self):
        """TC-20: ticks 리스트 길이 == 24."""
        gate = _make_gate()
        result = gate.run()
        assert len(result.ticks) == TICK_COUNT

    def test_tc21_passes_g69(self):
        """TC-21: 정상 실행 시 G69 PASS."""
        gate = _make_gate()
        result = gate.run()
        assert result.passed is True

    def test_tc22_zero_error_ticks(self):
        """TC-22: 정상 실행 — error_ticks == 0."""
        gate = _make_gate()
        result = gate.run()
        assert result.error_ticks == 0

    def test_tc23_zero_data_loss(self):
        """TC-23: 데이터 손실 0건."""
        gate = _make_gate()
        result = gate.run()
        assert result.total_loss == 0

    def test_tc24_purge_cycles_gte_1(self):
        """TC-24: purge 사이클 최소 1회."""
        gate = _make_gate()
        result = gate.run()
        assert result.purge_cycles >= 1

    def test_tc25_purge_count_correct(self):
        """TC-25: purge는 PURGE_EVERY_N_TICKS 배수 tick에서 실행."""
        gate = _make_gate()
        result = gate.run()
        purge_ticks = [t for t in result.ticks if t.purge_count >= 0]
        # tick 6, 12, 18, (24는 없음) → 3회
        assert len(purge_ticks) >= 1
        for t in purge_ticks:
            assert t.tick_index % PURGE_EVERY_N_TICKS == 0


# ── TC-26~30: 집계 통계 ──────────────────────────────────────────────

class TestAggregateStats:
    def test_tc26_total_collected_gte_tick_times_min(self):
        """TC-26: 총 수집 건수 >= TICK_COUNT * MIN_FEEDBACK_PER_TICK."""
        gate = _make_gate()
        result = gate.run()
        assert result.total_collected >= TICK_COUNT * MIN_FEEDBACK_PER_TICK

    def test_tc27_total_converted_positive(self):
        """TC-27: 총 변환 건수 > 0."""
        gate = _make_gate()
        result = gate.run()
        assert result.total_converted > 0

    def test_tc28_summary_contains_pass(self):
        """TC-28: 합격 시 summary에 'PASS' 포함."""
        gate = _make_gate()
        result = gate.run()
        if result.passed:
            assert "PASS" in result.summary

    def test_tc29_elapsed_ms_positive(self):
        """TC-29: elapsed_ms > 0."""
        gate = _make_gate()
        result = gate.run()
        assert result.elapsed_ms > 0

    def test_tc30_success_ticks_sum(self):
        """TC-30: success_ticks + error_ticks == tick_count."""
        gate = _make_gate()
        result = gate.run()
        assert result.success_ticks + result.error_ticks == result.tick_count


# ── TC-31~33: run_g69 진입점 및 엣지 케이스 ──────────────────────────

class TestRunG69:
    def test_tc31_run_g69_returns_dict(self):
        """TC-31: run_g69() → dict 반환."""
        result = run_g69()
        assert isinstance(result, dict)

    def test_tc32_run_g69_passed_true(self):
        """TC-32: run_g69() 기본 실행 → passed=True."""
        result = run_g69()
        assert result["passed"] is True

    def test_tc33_run_g69_custom_components(self):
        """TC-33: 커스텀 컴포넌트 주입 시에도 PASS."""
        collector = ReaderFeedbackCollector(
            policy=PIIPurgePolicy(retention_days=14),
            required_consent=ConsentLevel.ANONYMOUS,
        )
        adapter = FeedbackToRLHFAdapter(
            policy=OutlierPolicy(z_threshold=2.0, min_samples_after_filter=1),
        )
        result = run_g69(collector=collector, adapter=adapter)
        assert result["passed"] is True
        assert result["error_ticks"] == 0
