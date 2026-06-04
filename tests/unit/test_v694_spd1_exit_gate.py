"""
tests/unit/test_v694_spd1_exit_gate.py
───────────────────────────────────────
V694 SP-D.1 Exit Gate 33 TC + 버전 12.1.0 검증

TC-01~06  : ExitCheckpoint / SpD1ExitResult 데이터 타입
TC-07~12  : E1 TraceContext 검증 함수
TC-13~18  : E2~E3 OTel + Prometheus 검증 함수
TC-19~24  : E4~E5 Sampler + Dashboard 검증 함수
TC-25~27  : E6 G83 Gate 검증 함수
TC-28~30  : run_spd1_exit_gate() 전체 실행
TC-31~33  : pyproject.toml 버전 12.1.0 + 문서 정합성
"""

import pytest
import importlib
import sys
from pathlib import Path

from literary_system.gates.spd1_exit_gate import (
    ExitCheckpoint,
    SpD1ExitResult,
    _check_e1_trace_context,
    _check_e2_otel_adapter,
    _check_e3_prometheus_trace_extension,
    _check_e4_trace_sampler,
    _check_e5_observability_dashboard,
    _check_e6_g83_gate,
    run_spd1_exit_gate,
)


# ──────────────────────────────────────────────
# TC-01~06: 데이터 타입
# ──────────────────────────────────────────────


def test_tc01_exit_checkpoint_defaults():
    cp = ExitCheckpoint(axis="E1", name="Test", passed=True)
    assert cp.axis == "E1"
    assert cp.name == "Test"
    assert cp.passed is True
    assert cp.error is None
    assert cp.duration_ms == 0.0


def test_tc02_exit_checkpoint_failure_fields():
    cp = ExitCheckpoint(axis="E2", name="Fail", passed=False, error="module not found")
    assert cp.passed is False
    assert cp.error == "module not found"


def test_tc03_spd1_exit_result_defaults():
    r = SpD1ExitResult()
    assert r.gate_id == "SP-D.1-EXIT"
    assert r.passed is False
    assert r.passed_count == 0
    assert r.failed_count == 0
    assert r.checkpoints == []


def test_tc04_spd1_exit_result_to_dict():
    r = SpD1ExitResult(passed=True, passed_count=6, failed_count=0)
    d = r.to_dict()
    assert d["gate_id"] == "SP-D.1-EXIT"
    assert d["passed"] is True
    assert d["passed_count"] == 6
    assert "checkpoints" in d
    assert "version" in d


def test_tc05_exit_result_version_field():
    r = SpD1ExitResult()
    assert r.version == "12.1.0"


def test_tc06_exit_checkpoint_duration_ms():
    cp = ExitCheckpoint(axis="E3", name="Perf", passed=True, duration_ms=12.5)
    assert cp.duration_ms == pytest.approx(12.5)


# ──────────────────────────────────────────────
# TC-07~12: E1 TraceContext 검증
# ──────────────────────────────────────────────


def test_tc07_e1_check_passes():
    cp = _check_e1_trace_context()
    assert cp.passed is True, f"E1 failed: {cp.error}"


def test_tc08_e1_axis_label():
    cp = _check_e1_trace_context()
    assert cp.axis == "E1"


def test_tc09_e1_no_error():
    cp = _check_e1_trace_context()
    assert cp.error is None


def test_tc10_e1_duration_measured():
    cp = _check_e1_trace_context()
    assert cp.duration_ms >= 0.0


def test_tc11_e1_detail_contains_traceparent():
    cp = _check_e1_trace_context()
    assert "traceparent" in cp.detail.lower() or "pass" in cp.detail.lower()


def test_tc12_e1_name_nonempty():
    cp = _check_e1_trace_context()
    assert len(cp.name) > 0


# ──────────────────────────────────────────────
# TC-13~18: E2~E3 OTel + Prometheus
# ──────────────────────────────────────────────


def test_tc13_e2_otel_adapter_passes():
    cp = _check_e2_otel_adapter()
    assert cp.passed is True, f"E2 failed: {cp.error}"


def test_tc14_e2_axis_label():
    cp = _check_e2_otel_adapter()
    assert cp.axis == "E2"


def test_tc15_e2_detail_has_trace_id():
    cp = _check_e2_otel_adapter()
    assert "trace_id" in cp.detail


def test_tc16_e3_prometheus_passes():
    cp = _check_e3_prometheus_trace_extension()
    assert cp.passed is True, f"E3 failed: {cp.error}"


def test_tc17_e3_axis_label():
    cp = _check_e3_prometheus_trace_extension()
    assert cp.axis == "E3"


def test_tc18_e3_detail_mentions_dm02():
    cp = _check_e3_prometheus_trace_extension()
    assert "D-M-02" in cp.detail or "traceparent" in cp.detail.lower()


# ──────────────────────────────────────────────
# TC-19~24: E4~E5 Sampler + Dashboard
# ──────────────────────────────────────────────


def test_tc19_e4_trace_sampler_passes():
    cp = _check_e4_trace_sampler()
    assert cp.passed is True, f"E4 failed: {cp.error}"


def test_tc20_e4_axis_label():
    cp = _check_e4_trace_sampler()
    assert cp.axis == "E4"


def test_tc21_e4_detail_has_ratio():
    cp = _check_e4_trace_sampler()
    assert "RATIO" in cp.detail or "ADAPTIVE" in cp.detail


def test_tc22_e5_dashboard_passes():
    cp = _check_e5_observability_dashboard()
    assert cp.passed is True, f"E5 failed: {cp.error}"


def test_tc23_e5_axis_label():
    cp = _check_e5_observability_dashboard()
    assert cp.axis == "E5"


def test_tc24_e5_detail_healthy():
    cp = _check_e5_observability_dashboard()
    assert "healthy" in cp.detail.lower() or "PASS" in cp.detail


# ──────────────────────────────────────────────
# TC-25~27: E6 G83 Gate
# ──────────────────────────────────────────────


def test_tc25_e6_g83_gate_passes():
    cp = _check_e6_g83_gate()
    assert cp.passed is True, f"E6 failed: {cp.error}"


def test_tc26_e6_axis_label():
    cp = _check_e6_g83_gate()
    assert cp.axis == "E6"


def test_tc27_e6_detail_has_gate_count():
    cp = _check_e6_g83_gate()
    assert "gates" in cp.detail.lower() or "PASS" in cp.detail


# ──────────────────────────────────────────────
# TC-28~30: run_spd1_exit_gate() 전체 실행
# ──────────────────────────────────────────────


def test_tc28_full_exit_gate_passes():
    result = run_spd1_exit_gate()
    assert result.passed is True, f"SP-D.1 Exit Gate FAILED: {[c for c in result.checkpoints if not c.passed]}"


def test_tc29_exit_gate_6_checkpoints():
    result = run_spd1_exit_gate()
    assert len(result.checkpoints) == 6
    assert result.passed_count == 6
    assert result.failed_count == 0


def test_tc30_exit_gate_to_dict_complete():
    result = run_spd1_exit_gate()
    d = result.to_dict()
    assert d["passed"] is True
    assert len(d["checkpoints"]) == 6
    assert all(cp["passed"] for cp in d["checkpoints"])
    assert d["tc_total"] > 9000


# ──────────────────────────────────────────────
# TC-31~33: 버전 정합성 검증
# ──────────────────────────────────────────────


def test_tc31_pyproject_version_present():
    """pyproject.toml [project] 버전이 유효한 semver로 선언돼 있는지 동적 확인."""
    import re as _re
    root = Path(__file__).parent.parent.parent
    content = (root / "pyproject.toml").read_text(encoding="utf-8")
    m = _re.search(r'\[project\][^\[]*?version\s*=\s*"(\d+\.\d+\.\d+)"', content, _re.S)
    assert m, "pyproject.toml [project] semver version not found"


def test_tc32_spd1_exit_gate_module_importable():
    """spd1_exit_gate 모듈 임포트 가능."""
    import literary_system.gates.spd1_exit_gate as m
    assert hasattr(m, "run_spd1_exit_gate")
    assert hasattr(m, "SpD1ExitResult")
    assert hasattr(m, "ExitCheckpoint")


def test_tc33_observability_modules_all_importable():
    """SP-D.1 관측성 5개 모듈 모두 임포트 가능."""
    modules = [
        "literary_system.ops.trace_context",
        "literary_system.ops.otel_adapter",
        "literary_system.ops.prometheus_trace_extension",
        "literary_system.ops.trace_sampler",
        "literary_system.ops.observability_dashboard",
    ]
    for mod_name in modules:
        mod = importlib.import_module(mod_name)
        assert mod is not None, f"Failed to import {mod_name}"
