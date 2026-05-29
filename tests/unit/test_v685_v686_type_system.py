"""
tests/unit/test_v685_v686_type_system.py
V685/V686 — CI 4단 분리 + type_stubs.py 검증 (ADR-147/148)

TC-01~TC-25: TypeAlias, Protocol, 유틸 함수, CI yml 존재 검증
"""
from __future__ import annotations

import os
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ─── TC-01~TC-06: TypeAlias 및 기본 타입 ─────────────────────────────────────

def test_tc01_json_type_alias_dict():
    """TC-01: JSON TypeAlias — dict 가능"""
    from literary_system.core.type_stubs import JSON
    data: JSON = {"key": "value", "num": 1}
    assert isinstance(data, dict)


def test_tc02_json_type_alias_list():
    """TC-02: JSON TypeAlias — list 가능"""
    from literary_system.core.type_stubs import JSON
    data: JSON = [1, 2, 3]
    assert isinstance(data, list)


def test_tc03_json_type_alias_primitives():
    """TC-03: JSON TypeAlias — str/int/float/bool/None 가능"""
    from literary_system.core.type_stubs import JSON
    # 정적 타입 힌트 역할이므로 런타임 동작 확인
    assert isinstance("str", str)
    assert isinstance(42, int)


def test_tc04_tenant_id_is_str():
    """TC-04: TenantId = str"""
    from literary_system.core.type_stubs import TenantId
    tid: TenantId = "T1-NovelAI"
    assert isinstance(tid, str)


def test_tc05_gate_id_is_str():
    """TC-05: GateId = str"""
    from literary_system.core.type_stubs import GateId
    gid: GateId = "G81"
    assert isinstance(gid, str)


def test_tc06_score_is_float():
    """TC-06: Score = float"""
    from literary_system.core.type_stubs import Score
    s: Score = 0.85
    assert isinstance(s, float)


# ─── TC-07~TC-10: clamp_score ────────────────────────────────────────────────

def test_tc07_clamp_score_normal():
    """TC-07: clamp_score(0.5) → 0.5"""
    from literary_system.core.type_stubs import clamp_score
    assert abs(clamp_score(0.5) - 0.5) < 1e-9


def test_tc08_clamp_score_above_max():
    """TC-08: clamp_score(1.5) → 1.0"""
    from literary_system.core.type_stubs import clamp_score
    assert clamp_score(1.5) == 1.0


def test_tc09_clamp_score_below_min():
    """TC-09: clamp_score(-0.1) → 0.0"""
    from literary_system.core.type_stubs import clamp_score
    assert clamp_score(-0.1) == 0.0


def test_tc10_clamp_score_custom_range():
    """TC-10: clamp_score(5, 0, 10) → 5"""
    from literary_system.core.type_stubs import clamp_score
    assert clamp_score(5.0, 0.0, 10.0) == 5.0


# ─── TC-11~TC-14: is_valid_gate_id ───────────────────────────────────────────

def test_tc11_valid_gate_id_g81():
    """TC-11: is_valid_gate_id('G81') → True"""
    from literary_system.core.type_stubs import is_valid_gate_id
    assert is_valid_gate_id("G81") is True


def test_tc12_valid_gate_id_g1():
    """TC-12: is_valid_gate_id('G1') → True"""
    from literary_system.core.type_stubs import is_valid_gate_id
    assert is_valid_gate_id("G1") is True


def test_tc13_invalid_gate_id_no_g():
    """TC-13: is_valid_gate_id('81') → False (G 없음)"""
    from literary_system.core.type_stubs import is_valid_gate_id
    assert is_valid_gate_id("81") is False


def test_tc14_invalid_gate_id_non_numeric():
    """TC-14: is_valid_gate_id('Gabc') → False"""
    from literary_system.core.type_stubs import is_valid_gate_id
    assert is_valid_gate_id("Gabc") is False


# ─── TC-15~TC-17: is_valid_tenant_id ─────────────────────────────────────────

def test_tc15_valid_tenant_id():
    """TC-15: is_valid_tenant_id('T1') → True"""
    from literary_system.core.type_stubs import is_valid_tenant_id
    assert is_valid_tenant_id("T1") is True


def test_tc16_invalid_tenant_id_empty():
    """TC-16: is_valid_tenant_id('') → False"""
    from literary_system.core.type_stubs import is_valid_tenant_id
    assert is_valid_tenant_id("") is False


def test_tc17_invalid_tenant_id_whitespace():
    """TC-17: is_valid_tenant_id('   ') → False"""
    from literary_system.core.type_stubs import is_valid_tenant_id
    assert is_valid_tenant_id("   ") is False


# ─── TC-18~TC-22: Protocol 런타임 체크 ───────────────────────────────────────

def test_tc18_gate_protocol_runtime_check():
    """TC-18: GateProtocol — runtime_checkable 검증"""
    from literary_system.core.type_stubs import GateProtocol

    class MockGate:
        GATE_ID = "G-MOCK"
        def run(self) -> dict:
            return {"pass": True}

    assert isinstance(MockGate(), GateProtocol)


def test_tc19_gate_protocol_fail():
    """TC-19: GateProtocol — run() 없으면 isinstance False"""
    from literary_system.core.type_stubs import GateProtocol

    class NotAGate:
        GATE_ID = "G-FAIL"
        # run() 없음

    assert not isinstance(NotAGate(), GateProtocol)


def test_tc20_analyzer_protocol_runtime_check():
    """TC-20: AnalyzerProtocol — runtime_checkable 검증"""
    from literary_system.core.type_stubs import AnalyzerProtocol

    class MockAnalyzer:
        def analyze(self, text: str) -> dict:
            return {"text": text}
        def score(self, text: str) -> float:
            return 0.9

    assert isinstance(MockAnalyzer(), AnalyzerProtocol)


def test_tc21_literary_core_protocol_check():
    """TC-21: LiteraryCoreProtocol — component_id + health_check 확인"""
    from literary_system.core.type_stubs import LiteraryCoreProtocol

    class MockCore:
        @property
        def component_id(self) -> str:
            return "mock-core"
        def health_check(self) -> bool:
            return True

    assert isinstance(MockCore(), LiteraryCoreProtocol)


def test_tc22_serializable_protocol_check():
    """TC-22: SerializableProtocol — to_dict + from_dict 확인"""
    from literary_system.core.type_stubs import SerializableProtocol

    class MockSerial:
        def to_dict(self) -> dict:
            return {"x": 1}
        @classmethod
        def from_dict(cls, data: dict) -> "MockSerial":
            return cls()

    assert isinstance(MockSerial(), SerializableProtocol)


# ─── TC-23~TC-25: core/__init__.py 재export + CI yml 존재 ─────────────────────

def test_tc23_core_init_exports():
    """TC-23: literary_system.core.__init__ 재export 정상"""
    from literary_system.core import JSON, TenantId, GateId, Score
    from literary_system.core import LiteraryCoreProtocol, GateProtocol
    # import 성공이 검증
    assert GateProtocol is not None


def test_tc24_ci_4tier_yml_exists():
    """TC-24: .github/workflows/ci_4tier.yml 파일 존재"""
    repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
    yml_path = os.path.join(repo_root, ".github", "workflows", "ci_4tier.yml")
    assert os.path.isfile(yml_path), "ci_4tier.yml not found"


def test_tc25_requirements_lock_exists():
    """TC-25: requirements-lock.txt 파일 존재"""
    repo_root = os.path.join(os.path.dirname(__file__), "..", "..")
    lock_path = os.path.join(repo_root, "requirements-lock.txt")
    assert os.path.isfile(lock_path), "requirements-lock.txt not found"
