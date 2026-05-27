"""
V654 — test_v654_mae_multiwork_gate.py
MAEMultiWorkGate G66 테스트 — 33 TC
"""
from __future__ import annotations

import time
import pytest

from literary_system.ensemble.mae_multiwork_gate import (
    MAEMultiWorkGate,
    MultiWorkGateResult,
    ProjectRunResult,
    ProjectRunSpec,
    _percentile,
    GATE_ID,
    GATE_NAME,
    P95_THRESHOLD_SEC,
    MIN_PROJECTS,
)


# ── 픽스처 ────────────────────────────────────────────────────────────────────

def make_specs(n: int = 3, scenes_each: int = 2) -> list:
    return [
        ProjectRunSpec(
            project_id=f"proj_{i}",
            scenes=[{"scene_id": f"s{i}_{j}", "content": "테스트 씬"} for j in range(scenes_each)],
        )
        for i in range(n)
    ]


@pytest.fixture
def gate():
    return MAEMultiWorkGate()


@pytest.fixture
def three_specs():
    return make_specs(3, 2)


# ── TC01~TC05: 상수 및 데이터클래스 ─────────────────────────────────────────

def test_tc01_gate_id():
    assert GATE_ID == "G66"

def test_tc02_gate_name():
    assert "MultiWork" in GATE_NAME

def test_tc03_p95_threshold():
    assert P95_THRESHOLD_SEC == 8.0

def test_tc04_min_projects():
    assert MIN_PROJECTS == 3

def test_tc05_project_run_spec_defaults():
    spec = ProjectRunSpec(project_id="p1")
    assert spec.scenes == []
    assert spec.max_rounds == 3


# ── TC06~TC10: ProjectRunResult ───────────────────────────────────────────────

def test_tc06_project_run_result_to_dict():
    r = ProjectRunResult(project_id="p1", latency_sec=1.5, scene_count=2, success=True)
    d = r.to_dict()
    assert d["project_id"] == "p1"
    assert d["latency_sec"] == 1.5
    assert d["success"] is True

def test_tc07_project_run_result_error_field():
    r = ProjectRunResult(project_id="p2", latency_sec=0.0, scene_count=1, success=False, error="timeout")
    assert r.error == "timeout"
    assert r.to_dict()["error"] == "timeout"

def test_tc08_project_run_result_scores():
    r = ProjectRunResult(project_id="p3", latency_sec=2.0, scene_count=3, success=True,
                         ensemble_scores=[0.8, 0.9, 0.85])
    assert len(r.ensemble_scores) == 3

def test_tc09_project_run_result_to_dict_keys():
    r = ProjectRunResult(project_id="x", latency_sec=1.0, scene_count=1, success=True)
    keys = set(r.to_dict().keys())
    assert {"project_id", "latency_sec", "scene_count", "success", "error", "ensemble_scores"} <= keys

def test_tc10_project_run_result_default_scores():
    r = ProjectRunResult(project_id="p0", latency_sec=0.1, scene_count=0, success=True)
    assert r.ensemble_scores == []


# ── TC11~TC15: MultiWorkGateResult ───────────────────────────────────────────

def test_tc11_gate_result_defaults():
    r = MultiWorkGateResult()
    assert r.gate_id == GATE_ID
    assert r.passed is False

def test_tc12_gate_result_to_dict():
    r = MultiWorkGateResult(passed=True, project_count=3, p95_latency_sec=2.5)
    d = r.to_dict()
    assert d["passed"] is True
    assert d["p95_latency_sec"] == 2.5

def test_tc13_gate_result_from_dict_roundtrip():
    orig = MultiWorkGateResult(
        passed=True, project_count=3,
        p95_latency_sec=1.2, p50_latency_sec=0.8, max_latency_sec=1.5,
        all_latencies=[0.8, 1.0, 1.5],
    )
    restored = MultiWorkGateResult.from_dict(orig.to_dict())
    assert restored.passed is True
    assert restored.p95_latency_sec == 1.2

def test_tc14_gate_result_from_dict_project_results():
    r = ProjectRunResult(project_id="p1", latency_sec=1.0, scene_count=2, success=True)
    gate_r = MultiWorkGateResult(project_results=[r])
    d = gate_r.to_dict()
    restored = MultiWorkGateResult.from_dict(d)
    assert len(restored.project_results) == 1
    assert restored.project_results[0].project_id == "p1"

def test_tc15_gate_result_failure_reason_none_on_pass():
    r = MultiWorkGateResult(passed=True, failure_reason=None)
    assert r.failure_reason is None


# ── TC16~TC20: _percentile 함수 ──────────────────────────────────────────────

def test_tc16_percentile_empty():
    assert _percentile([], 95) == 0.0

def test_tc17_percentile_single():
    assert _percentile([5.0], 95) == 5.0

def test_tc18_percentile_p50():
    data = [1.0, 2.0, 3.0, 4.0, 5.0]
    p50 = _percentile(data, 50)
    assert 2.5 <= p50 <= 3.5

def test_tc19_percentile_p95_large():
    data = list(range(1, 101))  # 1~100
    p95 = _percentile([float(x) for x in data], 95)
    assert 94.0 <= p95 <= 96.0

def test_tc20_percentile_p95_all_same():
    data = [3.0] * 10
    assert _percentile(data, 95) == 3.0


# ── TC21~TC25: MAEMultiWorkGate 초기화 ───────────────────────────────────────

def test_tc21_gate_init_defaults(gate):
    assert gate.p95_threshold == P95_THRESHOLD_SEC
    assert gate.coordinator is None

def test_tc22_gate_init_custom_threshold():
    g = MAEMultiWorkGate(p95_threshold_sec=5.0)
    assert g.p95_threshold == 5.0

def test_tc23_gate_init_with_coordinator():
    class FakeCoord:
        pass
    g = MAEMultiWorkGate(coordinator=FakeCoord())
    assert g.coordinator is not None

def test_tc24_gate_max_workers_default(gate):
    assert gate.max_workers == 4

def test_tc25_gate_init_custom_workers():
    g = MAEMultiWorkGate(max_workers=2)
    assert g.max_workers == 2


# ── TC26~TC30: run_gate 동작 ─────────────────────────────────────────────────

def test_tc26_run_gate_too_few_projects(gate):
    specs = make_specs(2)
    result = gate.run_gate(specs)
    assert result.passed is False
    assert "부족" in result.failure_reason

def test_tc27_run_gate_three_projects_pass(gate, three_specs):
    result = gate.run_gate(three_specs)
    assert result.project_count == 3
    # 스텁 지연 = 2 scenes * 0.05s = 0.1s << 8.0s → PASS
    assert result.passed is True

def test_tc28_run_gate_p95_below_threshold(gate, three_specs):
    result = gate.run_gate(three_specs)
    assert result.p95_latency_sec <= P95_THRESHOLD_SEC

def test_tc29_run_gate_all_latencies_populated(gate, three_specs):
    result = gate.run_gate(three_specs)
    assert len(result.all_latencies) == 3

def test_tc30_run_gate_project_results_count(gate, three_specs):
    result = gate.run_gate(three_specs)
    assert len(result.project_results) == 3


# ── TC31~TC33: 추가 검증 ─────────────────────────────────────────────────────

def test_tc31_run_gate_five_projects(gate):
    specs = make_specs(5, 1)
    result = gate.run_gate(specs)
    assert result.passed is True
    assert result.project_count == 5

def test_tc32_run_gate_high_threshold_pass():
    # 매우 낮은 임계값 → FAIL 시나리오
    g = MAEMultiWorkGate(p95_threshold_sec=0.001)  # 1ms → 실제론 FAIL
    specs = make_specs(3, 1)
    result = g.run_gate(specs)
    # 스텁 0.05s * 1 scene = ~0.05s > 0.001s → FAIL
    assert result.passed is False
    assert result.failure_reason is not None

def test_tc33_benchmark_repeat(gate, three_specs):
    result = gate.benchmark(three_specs, repeat=2)
    assert result.passed is True
    # 2 반복 * 3 프로젝트 = 6 latencies
    assert len(result.all_latencies) == 6
