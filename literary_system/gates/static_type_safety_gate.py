"""
literary_system/gates/static_type_safety_gate.py
=================================================
V687 — G82: Static Type Safety Gate (ADR-149/150)

pre-commit 4종(mypy/bandit/ruff/black) + core/type_stubs.py 존재를
통합 검증하는 Gate.

검증 항목 (5축):
  ST-1: .pre-commit-config.yaml 존재 및 4종 hook 포함 확인
  ST-2: core/type_stubs.py 존재 및 Protocol 4종 확인
  ST-3: pyproject.toml [tool.mypy] strict=true 설정 확인
  ST-4: requirements-lock.txt 존재 및 핵심 의존성 포함 확인
  ST-5: 통합 ALL PASS → gate_passed True

ADR-149/150 참조.
LLM-0 원칙 완전 준수 (외부 LLM 호출 없음)
"""
from __future__ import annotations

import os
import sys
from dataclasses import dataclass, field
from typing import List, Optional

GATE_ID: str = "G82"

# 저장소 루트 탐색
_HERE = os.path.dirname(os.path.abspath(__file__))
_REPO_ROOT = os.path.normpath(os.path.join(_HERE, "..", ".."))

# 독립 실행 시 repo root를 sys.path에 추가
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

# 필수 pre-commit hook 식별자
REQUIRED_HOOKS = {"mypy", "bandit", "ruff", "black"}

# core/type_stubs.py 에서 확인할 Protocol 이름
REQUIRED_PROTOCOLS = {
    "LiteraryCoreProtocol",
    "GateProtocol",
    "SerializableProtocol",
    "AnalyzerProtocol",
}


# ---------------------------------------------------------------------------
# 결과 데이터클래스
# ---------------------------------------------------------------------------

@dataclass
class TypeSafetyCheckpoint:
    """개별 검증 결과."""
    name: str
    passed: bool
    detail: str = ""


@dataclass
class StaticTypeSafetyReport:
    """G82 통합 결과 리포트."""
    checkpoints: List[TypeSafetyCheckpoint] = field(default_factory=list)
    gate_passed: bool = False

    def add(self, checkpoint: TypeSafetyCheckpoint) -> None:
        self.checkpoints.append(checkpoint)

    @property
    def passed_count(self) -> int:
        return sum(1 for c in self.checkpoints if c.passed)

    @property
    def failed_count(self) -> int:
        return sum(1 for c in self.checkpoints if not c.passed)


# ---------------------------------------------------------------------------
# ST-1: .pre-commit-config.yaml 존재 및 4종 hook
# ---------------------------------------------------------------------------

def _check_st1_pre_commit_config() -> TypeSafetyCheckpoint:
    """ST-1: .pre-commit-config.yaml 존재 + REQUIRED_HOOKS 포함 확인."""
    try:
        config_path = os.path.join(_REPO_ROOT, ".pre-commit-config.yaml")
        if not os.path.isfile(config_path):
            return TypeSafetyCheckpoint("ST-1 pre-commit-config", False, ".pre-commit-config.yaml 없음")

        with open(config_path, encoding="utf-8") as f:
            content = f.read()

        found_hooks = {hook for hook in REQUIRED_HOOKS if hook in content}
        missing = REQUIRED_HOOKS - found_hooks
        ok = not missing
        detail = (
            "hooks found: {}".format(sorted(found_hooks))
            if ok
            else "missing hooks: {}".format(sorted(missing))
        )
        return TypeSafetyCheckpoint("ST-1 pre-commit-config", ok, detail)
    except Exception as exc:
        return TypeSafetyCheckpoint("ST-1 pre-commit-config", False, str(exc))


# ---------------------------------------------------------------------------
# ST-2: core/type_stubs.py 존재 및 Protocol 4종
# ---------------------------------------------------------------------------

def _check_st2_type_stubs() -> TypeSafetyCheckpoint:
    """ST-2: literary_system/core/type_stubs.py 존재 + Protocol 4종 확인."""
    try:
        stubs_path = os.path.join(
            _REPO_ROOT, "literary_system", "core", "type_stubs.py"
        )
        if not os.path.isfile(stubs_path):
            return TypeSafetyCheckpoint("ST-2 type_stubs.py", False, "type_stubs.py 없음")

        with open(stubs_path, encoding="utf-8") as f:
            content = f.read()

        found_protocols = {p for p in REQUIRED_PROTOCOLS if p in content}
        missing = REQUIRED_PROTOCOLS - found_protocols
        ok = not missing

        # 실제 import 검증
        if ok:
            try:
                from literary_system.core.type_stubs import (  # noqa: PLC0415
                    LiteraryCoreProtocol,
                    GateProtocol,
                    SerializableProtocol,
                    AnalyzerProtocol,
                )
            except ImportError as ie:
                return TypeSafetyCheckpoint("ST-2 type_stubs.py", False, "import 실패: {}".format(ie))

        detail = (
            "protocols found: {}".format(sorted(found_protocols))
            if ok
            else "missing protocols: {}".format(sorted(missing))
        )
        return TypeSafetyCheckpoint("ST-2 type_stubs.py", ok, detail)
    except Exception as exc:
        return TypeSafetyCheckpoint("ST-2 type_stubs.py", False, str(exc))


# ---------------------------------------------------------------------------
# ST-3: pyproject.toml [tool.mypy] strict=true
# ---------------------------------------------------------------------------

def _check_st3_mypy_config() -> TypeSafetyCheckpoint:
    """ST-3: pyproject.toml 에 [tool.mypy] strict=true 설정 확인."""
    try:
        toml_path = os.path.join(_REPO_ROOT, "pyproject.toml")
        if not os.path.isfile(toml_path):
            return TypeSafetyCheckpoint("ST-3 mypy config", False, "pyproject.toml 없음")

        with open(toml_path, encoding="utf-8") as f:
            content = f.read()

        has_mypy_section = "[tool.mypy]" in content
        has_strict = "strict = true" in content or "strict=true" in content
        ok = has_mypy_section and has_strict
        detail = "mypy_section={}, strict={}".format(has_mypy_section, has_strict)
        return TypeSafetyCheckpoint("ST-3 mypy config", ok, detail)
    except Exception as exc:
        return TypeSafetyCheckpoint("ST-3 mypy config", False, str(exc))


# ---------------------------------------------------------------------------
# ST-4: requirements-lock.txt 존재 및 핵심 의존성
# ---------------------------------------------------------------------------

def _check_st4_requirements_lock() -> TypeSafetyCheckpoint:
    """ST-4: requirements-lock.txt 존재 + 핵심 패키지 포함 확인."""
    try:
        lock_path = os.path.join(_REPO_ROOT, "requirements-lock.txt")
        if not os.path.isfile(lock_path):
            return TypeSafetyCheckpoint("ST-4 requirements-lock", False, "requirements-lock.txt 없음")

        with open(lock_path, encoding="utf-8") as f:
            content = f.read()

        required_pkgs = {"networkx", "pydantic", "pytest"}
        found_pkgs = {p for p in required_pkgs if p in content}
        missing = required_pkgs - found_pkgs
        ok = not missing
        detail = (
            "pkgs found: {}".format(sorted(found_pkgs))
            if ok
            else "missing: {}".format(sorted(missing))
        )
        return TypeSafetyCheckpoint("ST-4 requirements-lock", ok, detail)
    except Exception as exc:
        return TypeSafetyCheckpoint("ST-4 requirements-lock", False, str(exc))


# ---------------------------------------------------------------------------
# ST-5: 통합 PASS
# ---------------------------------------------------------------------------

def _check_st5_all_pass(checkpoints: List[TypeSafetyCheckpoint]) -> TypeSafetyCheckpoint:
    """ST-5: ST-1~ST-4 ALL PASS → gate_passed True."""
    all_pass = all(c.passed for c in checkpoints)
    detail = "{}/{} checkpoints passed".format(
        sum(c.passed for c in checkpoints), len(checkpoints)
    )
    return TypeSafetyCheckpoint("ST-5 통합 ALL-PASS", all_pass, detail)


# ---------------------------------------------------------------------------
# 메인 실행 함수
# ---------------------------------------------------------------------------

def run_static_type_safety_gate() -> StaticTypeSafetyReport:
    """G82: Static Type Safety Gate 실행."""
    report = StaticTypeSafetyReport()

    st1 = _check_st1_pre_commit_config()
    report.add(st1)

    st2 = _check_st2_type_stubs()
    report.add(st2)

    st3 = _check_st3_mypy_config()
    report.add(st3)

    st4 = _check_st4_requirements_lock()
    report.add(st4)

    st5 = _check_st5_all_pass([st1, st2, st3, st4])
    report.add(st5)

    report.gate_passed = st5.passed
    return report


def run_g82_gate(
    _rg_results_override: Optional[dict] = None,
) -> dict:
    """release_gate.py 통합용 딕셔너리 반환."""
    report = run_static_type_safety_gate()
    return {
        "pass": report.gate_passed,
        "gate_id": GATE_ID,
        "passed_count": report.passed_count,
        "failed_count": report.failed_count,
        "checkpoints": [
            {"name": c.name, "passed": c.passed, "detail": c.detail}
            for c in report.checkpoints
        ],
    }


if __name__ == "__main__":
    result = run_static_type_safety_gate()
    status = "PASS" if result.gate_passed else "FAIL"
    sys.stdout.write("[{}] G82 Static Type Safety Gate\n".format(status))
    for cp in result.checkpoints:
        icon = "OK" if cp.passed else "FAIL"
        sys.stdout.write("  [{}] {}: {}\n".format(icon, cp.name, cp.detail))
    sys.exit(0 if result.gate_passed else 1)
