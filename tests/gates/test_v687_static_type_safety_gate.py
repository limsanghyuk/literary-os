"""
tests/gates/test_v687_static_type_safety_gate.py
V687 — G82: Static Type Safety Gate 검증 (ADR-149/150)

TC-01~TC-20: ST-1~ST-5 체크포인트 + run_g82_gate() 인터페이스 검증
"""
from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from literary_system.gates.static_type_safety_gate import (
    TypeSafetyCheckpoint,
    StaticTypeSafetyReport,
    GATE_ID,
    REQUIRED_HOOKS,
    REQUIRED_PROTOCOLS,
    run_static_type_safety_gate,
    run_g82_gate,
    _check_st1_pre_commit_config,
    _check_st2_type_stubs,
    _check_st3_mypy_config,
    _check_st4_requirements_lock,
    _check_st5_all_pass,
)


# ─── TC-01~TC-03: 데이터클래스 기본 ─────────────────────────────────────────

def test_tc01_type_safety_checkpoint_pass():
    """TC-01: TypeSafetyCheckpoint.passed=True"""
    cp = TypeSafetyCheckpoint("test", True, "ok")
    assert cp.passed is True


def test_tc02_static_type_safety_report_counts():
    """TC-02: passed_count / failed_count"""
    report = StaticTypeSafetyReport()
    report.add(TypeSafetyCheckpoint("a", True))
    report.add(TypeSafetyCheckpoint("b", False))
    assert report.passed_count == 1
    assert report.failed_count == 1


def test_tc03_gate_id_g82():
    """TC-03: GATE_ID == 'G82'"""
    assert GATE_ID == "G82"


# ─── TC-04~TC-05: 상수 검증 ──────────────────────────────────────────────────

def test_tc04_required_hooks_set():
    """TC-04: REQUIRED_HOOKS 4종 포함"""
    assert "mypy" in REQUIRED_HOOKS
    assert "bandit" in REQUIRED_HOOKS
    assert "ruff" in REQUIRED_HOOKS
    assert "black" in REQUIRED_HOOKS


def test_tc05_required_protocols_set():
    """TC-05: REQUIRED_PROTOCOLS 4종 포함"""
    assert "LiteraryCoreProtocol" in REQUIRED_PROTOCOLS
    assert "GateProtocol" in REQUIRED_PROTOCOLS
    assert "SerializableProtocol" in REQUIRED_PROTOCOLS
    assert "AnalyzerProtocol" in REQUIRED_PROTOCOLS


# ─── TC-06~TC-09: 개별 체크포인트 PASS 검증 ─────────────────────────────────

def test_tc06_st1_pre_commit_config_pass():
    """TC-06: ST-1 pre-commit-config PASS"""
    cp = _check_st1_pre_commit_config()
    assert cp.passed is True, cp.detail


def test_tc07_st2_type_stubs_pass():
    """TC-07: ST-2 type_stubs.py PASS"""
    cp = _check_st2_type_stubs()
    assert cp.passed is True, cp.detail


def test_tc08_st3_mypy_config_pass():
    """TC-08: ST-3 mypy config PASS"""
    cp = _check_st3_mypy_config()
    assert cp.passed is True, cp.detail


def test_tc09_st4_requirements_lock_pass():
    """TC-09: ST-4 requirements-lock PASS"""
    cp = _check_st4_requirements_lock()
    assert cp.passed is True, cp.detail


# ─── TC-10~TC-12: ST-5 통합 논리 ─────────────────────────────────────────────

def test_tc10_st5_all_pass_true():
    """TC-10: 4개 모두 PASS → ST-5 True"""
    cps = [TypeSafetyCheckpoint("x", True) for _ in range(4)]
    st5 = _check_st5_all_pass(cps)
    assert st5.passed is True


def test_tc11_st5_any_fail():
    """TC-11: 1개 FAIL → ST-5 False"""
    cps = [TypeSafetyCheckpoint("x", True) for _ in range(3)]
    cps.append(TypeSafetyCheckpoint("y", False))
    st5 = _check_st5_all_pass(cps)
    assert st5.passed is False


def test_tc12_st5_empty():
    """TC-12: 빈 리스트 → ST-5 True (all([]) == True)"""
    st5 = _check_st5_all_pass([])
    assert st5.passed is True


# ─── TC-13~TC-16: 파일 존재 통합 검증 ───────────────────────────────────────

def test_tc13_pre_commit_file_exists():
    """TC-13: .pre-commit-config.yaml 실제 파일 존재"""
    repo = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    assert os.path.isfile(os.path.join(repo, ".pre-commit-config.yaml"))


def test_tc14_type_stubs_file_exists():
    """TC-14: literary_system/core/type_stubs.py 실제 파일 존재"""
    repo = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    assert os.path.isfile(
        os.path.join(repo, "literary_system", "core", "type_stubs.py")
    )


def test_tc15_requirements_lock_file_exists():
    """TC-15: requirements-lock.txt 실제 파일 존재"""
    repo = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    assert os.path.isfile(os.path.join(repo, "requirements-lock.txt"))


def test_tc16_pyproject_has_mypy_strict():
    """TC-16: pyproject.toml에 [tool.mypy] + strict = true 존재"""
    repo = os.path.normpath(
        os.path.join(os.path.dirname(__file__), "..", "..")
    )
    toml = os.path.join(repo, "pyproject.toml")
    content = open(toml).read()
    assert "[tool.mypy]" in content
    assert "strict = true" in content or "strict=true" in content


# ─── TC-17~TC-20: run_static_type_safety_gate() + run_g82_gate() ─────────────

def test_tc17_run_gate_passes():
    """TC-17: run_static_type_safety_gate() gate_passed True"""
    report = run_static_type_safety_gate()
    assert report.gate_passed is True, str(
        [(c.name, c.detail) for c in report.checkpoints if not c.passed]
    )


def test_tc18_run_gate_5_checkpoints():
    """TC-18: 체크포인트 5개 생성"""
    report = run_static_type_safety_gate()
    assert len(report.checkpoints) == 5


def test_tc19_run_g82_gate_pass():
    """TC-19: run_g82_gate() pass=True"""
    result = run_g82_gate()
    assert result["pass"] is True


def test_tc20_run_g82_gate_structure():
    """TC-20: run_g82_gate() 딕셔너리 구조 검증"""
    result = run_g82_gate()
    for key in ("pass", "gate_id", "passed_count", "failed_count", "checkpoints"):
        assert key in result, "missing: {}".format(key)
    assert result["gate_id"] == "G82"
    assert result["passed_count"] == 5
    assert result["failed_count"] == 0
