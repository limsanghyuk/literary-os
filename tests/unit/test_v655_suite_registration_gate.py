"""
V655 — test_v655_suite_registration_gate.py
SuiteRegistrationGate G67 테스트 — 33 TC
"""
from __future__ import annotations

import json
import pytest

from literary_system.ensemble.suite_registration_gate import (
    SuiteRegistrationGate,
    SuiteRegistrationResult,
    ModelCardMetadata,
    GATE_ID,
    GATE_NAME,
    MIN_ENSEMBLE_SCORE,
    MIN_TEST_COUNT,
    ATIA_MIN_SCORE,
    REQUIRED_GATES,
    SUITE_VERSION,
)


# ── 픽스처 ────────────────────────────────────────────────────────────────────

@pytest.fixture
def gate():
    return SuiteRegistrationGate()


@pytest.fixture
def passing_params():
    return {
        "gates_passed": ["G64", "G65", "G66"],
        "ensemble_score": 0.85,
        "test_count": 600,
        "atia_score": 0.80,
    }


# ── TC01~TC05: 상수 및 기본 설정 ─────────────────────────────────────────────

def test_tc01_gate_id():
    assert GATE_ID == "G67"

def test_tc02_gate_name():
    assert "Registration" in GATE_NAME

def test_tc03_required_gates():
    assert set(REQUIRED_GATES) == {"G64", "G65", "G66"}

def test_tc04_min_ensemble_score():
    assert MIN_ENSEMBLE_SCORE == 0.83

def test_tc05_min_test_count():
    assert MIN_TEST_COUNT == 500


# ── TC06~TC10: ModelCardMetadata ─────────────────────────────────────────────

def test_tc06_model_card_defaults():
    mc = ModelCardMetadata()
    assert mc.version == SUITE_VERSION
    assert mc.language == "ko"
    assert mc.license == "Apache-2.0"

def test_tc07_model_card_components():
    mc = ModelCardMetadata()
    assert "DirectorAgent" in mc.components
    assert "AgentSafetyGuard" in mc.components
    assert "MAEMultiWorkGate" in mc.components

def test_tc08_model_card_to_dict():
    mc = ModelCardMetadata(gates_passed=["G64", "G65", "G66"], ensemble_score=0.87)
    d = mc.to_dict()
    assert d["ensemble_score"] == 0.87
    assert "G64" in d["gates_passed"]

def test_tc09_model_card_from_dict_roundtrip():
    mc = ModelCardMetadata(atia_score=0.75, ensemble_score=0.88)
    restored = ModelCardMetadata.from_dict(mc.to_dict())
    assert restored.atia_score == 0.75
    assert restored.ensemble_score == 0.88

def test_tc10_model_card_to_markdown():
    mc = ModelCardMetadata(gates_passed=["G64", "G65", "G66"],
                           ensemble_score=0.85, atia_score=0.80)
    md = mc.to_markdown()
    assert "---" in md
    assert "literary-os" in md
    assert "DirectorAgent" in md


# ── TC11~TC15: SuiteRegistrationResult ───────────────────────────────────────

def test_tc11_result_defaults():
    r = SuiteRegistrationResult()
    assert r.gate_id == GATE_ID
    assert r.passed is False
    assert r.failure_reasons == []

def test_tc12_result_to_dict():
    r = SuiteRegistrationResult(passed=True, ensemble_score=0.86, test_count=550)
    d = r.to_dict()
    assert d["passed"] is True
    assert d["test_count"] == 550

def test_tc13_result_from_dict_roundtrip():
    orig = SuiteRegistrationResult(
        passed=True, gates_check=True,
        ensemble_score=0.85, test_count=600, atia_score=0.80,
    )
    restored = SuiteRegistrationResult.from_dict(orig.to_dict())
    assert restored.passed is True
    assert restored.atia_score == 0.80

def test_tc14_result_from_dict_with_model_card():
    mc = ModelCardMetadata(ensemble_score=0.85)
    r = SuiteRegistrationResult(passed=True, model_card=mc)
    d = r.to_dict()
    restored = SuiteRegistrationResult.from_dict(d)
    assert restored.model_card is not None
    assert restored.model_card.ensemble_score == 0.85

def test_tc15_result_from_dict_no_model_card():
    r = SuiteRegistrationResult(passed=False)
    d = r.to_dict()
    restored = SuiteRegistrationResult.from_dict(d)
    assert restored.model_card is None


# ── TC16~TC20: SuiteRegistrationGate 초기화 ──────────────────────────────────

def test_tc16_gate_init_defaults(gate):
    assert gate.min_ensemble_score == MIN_ENSEMBLE_SCORE
    assert gate.min_test_count == MIN_TEST_COUNT
    assert gate.atia_min_score == ATIA_MIN_SCORE

def test_tc17_gate_init_custom():
    g = SuiteRegistrationGate(min_ensemble_score=0.90, min_test_count=1000)
    assert g.min_ensemble_score == 0.90
    assert g.min_test_count == 1000

def test_tc18_gate_required_gates(gate):
    assert set(gate.required_gates) == {"G64", "G65", "G66"}

def test_tc19_gate_custom_required_gates():
    g = SuiteRegistrationGate(required_gates=["G64", "G65"])
    assert g.required_gates == ["G64", "G65"]

def test_tc20_gate_callable(gate):
    assert callable(gate.run_gate)


# ── TC21~TC27: run_gate 통과 시나리오 ────────────────────────────────────────

def test_tc21_run_gate_all_pass(gate, passing_params):
    result = gate.run_gate(**passing_params)
    assert result.passed is True

def test_tc22_run_gate_pass_checks(gate, passing_params):
    result = gate.run_gate(**passing_params)
    assert result.gates_check is True
    assert result.ensemble_score_check is True
    assert result.test_count_check is True
    assert result.atia_check is True

def test_tc23_run_gate_model_card_generated(gate, passing_params):
    result = gate.run_gate(**passing_params)
    assert result.model_card is not None
    assert "G64" in result.model_card.gates_passed

def test_tc24_run_gate_model_card_scores(gate, passing_params):
    result = gate.run_gate(**passing_params)
    assert result.model_card.ensemble_score == 0.85
    assert result.model_card.atia_score == 0.80

def test_tc25_run_gate_no_failure_reasons_on_pass(gate, passing_params):
    result = gate.run_gate(**passing_params)
    assert result.failure_reasons == []

def test_tc26_run_gate_atia_dimensions_auto(gate, passing_params):
    result = gate.run_gate(**passing_params)
    assert "transparency" in result.model_card.atia_dimensions
    assert "accountability" in result.model_card.atia_dimensions

def test_tc27_run_gate_registered_at_set(gate, passing_params):
    result = gate.run_gate(**passing_params)
    assert result.model_card.registered_at != ""


# ── TC28~TC33: run_gate 실패 시나리오 ────────────────────────────────────────

def test_tc28_missing_gate_fails(gate):
    result = gate.run_gate(
        gates_passed=["G64", "G65"],  # G66 없음
        ensemble_score=0.85, test_count=600, atia_score=0.80,
    )
    assert result.passed is False
    assert result.gates_check is False
    assert any("G66" in r for r in result.failure_reasons)

def test_tc29_low_ensemble_score_fails(gate):
    result = gate.run_gate(
        gates_passed=["G64", "G65", "G66"],
        ensemble_score=0.75,  # < 0.83
        test_count=600, atia_score=0.80,
    )
    assert result.passed is False
    assert result.ensemble_score_check is False

def test_tc30_low_test_count_fails(gate):
    result = gate.run_gate(
        gates_passed=["G64", "G65", "G66"],
        ensemble_score=0.85,
        test_count=300,  # < 500
        atia_score=0.80,
    )
    assert result.passed is False
    assert result.test_count_check is False

def test_tc31_low_atia_score_fails(gate):
    result = gate.run_gate(
        gates_passed=["G64", "G65", "G66"],
        ensemble_score=0.85, test_count=600,
        atia_score=0.60,  # < 0.70
    )
    assert result.passed is False
    assert result.atia_check is False

def test_tc32_model_card_none_on_fail(gate):
    result = gate.run_gate(
        gates_passed=["G64"],  # 실패 케이스
        ensemble_score=0.85, test_count=600, atia_score=0.80,
    )
    assert result.model_card is None

def test_tc33_generate_registration_package(gate, passing_params):
    result = gate.run_gate(**passing_params)
    package = gate.generate_registration_package(result)
    assert "README.md" in package
    assert "gate_result.json" in package
    # JSON 파싱 가능한지 확인
    parsed = json.loads(package["gate_result.json"])
    assert parsed["passed"] is True
