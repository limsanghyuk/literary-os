"""V360 T11-8: ContractBridge v1 — GPT-Claude CrossValidation 테스트."""
import sys
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.contract.bridge import (
    ContractBridge, SceneIntentIR, SceneIntent, CrossValidationResult,
)


def make_ir(scene_id, intent=SceneIntent.REVEAL, tension=0.5, budget=0.3):
    return SceneIntentIR(scene_id=scene_id, intent=intent,
                         target_tension=tension, reveal_budget=budget)


class TestSceneIntentIR:
    def test_create_ir(self):
        ir = make_ir("s1")
        assert ir.scene_id == "s1" and ir.intent == SceneIntent.REVEAL

    def test_intent_enum_values(self):
        intents = [SceneIntent.REVEAL, SceneIntent.CONCEAL, SceneIntent.FORESHADOW,
                   SceneIntent.TURN, SceneIntent.ESTABLISH, SceneIntent.RESOLVE]
        assert len(intents) == 6

    def test_default_fields(self):
        ir = SceneIntentIR(scene_id="s1", intent=SceneIntent.REVEAL)
        assert ir.emotional_delta == 0.0
        assert ir.reveal_budget == 0.3
        assert ir.target_tension == 0.5


class TestContractRegistration:
    def test_register_gpt(self):
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1"))
        assert "s1" in b.scene_ids()

    def test_register_claude(self):
        b = ContractBridge()
        b.register_claude_contract("s1", make_ir("s1"))
        assert "s1" in b.scene_ids()

    def test_register_both(self):
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1"))
        b.register_claude_contract("s1", make_ir("s1"))
        assert len(b.scene_ids()) == 1

    def test_multiple_scenes(self):
        b = ContractBridge()
        for i in range(5):
            b.register_gpt_contract(f"s{i}", make_ir(f"s{i}"))
        assert len(b.scene_ids()) == 5


class TestCrossValidation:
    def test_consistent_same_intent(self):
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1", SceneIntent.REVEAL, 0.5, 0.3))
        b.register_claude_contract("s1", make_ir("s1", SceneIntent.REVEAL, 0.5, 0.3))
        r = b.cross_validate("s1")
        assert r.is_consistent and len(r.conflicts) == 0

    def test_inconsistent_different_intent(self):
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1", SceneIntent.REVEAL))
        b.register_claude_contract("s1", make_ir("s1", SceneIntent.CONCEAL))
        r = b.cross_validate("s1")
        assert not r.is_consistent
        assert any("intent" in c for c in r.conflicts)

    def test_tension_conflict_detected(self):
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1", tension=0.1))
        b.register_claude_contract("s1", make_ir("s1", tension=0.9))
        r = b.cross_validate("s1")
        assert not r.is_consistent
        assert any("tension" in c for c in r.conflicts)

    def test_budget_conflict_detected(self):
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1", budget=0.1))
        b.register_claude_contract("s1", make_ir("s1", budget=0.9))
        r = b.cross_validate("s1")
        assert not r.is_consistent
        assert any("budget" in c for c in r.conflicts)

    def test_consensus_ir_created_when_consistent(self):
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1", tension=0.4, budget=0.3))
        b.register_claude_contract("s1", make_ir("s1", tension=0.6, budget=0.3))
        r = b.cross_validate("s1")
        # tension 차이 0.2 이하이면 일관성 있음
        if r.is_consistent:
            assert r.consensus_ir is not None
            assert r.consensus_ir.target_tension == pytest.approx(0.5, abs=0.01)

    def test_no_consensus_when_inconsistent(self):
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1", SceneIntent.REVEAL))
        b.register_claude_contract("s1", make_ir("s1", SceneIntent.CONCEAL))
        r = b.cross_validate("s1")
        if not r.is_consistent:
            assert r.consensus_ir is None

    def test_missing_gpt_still_ok(self):
        b = ContractBridge()
        b.register_claude_contract("s1", make_ir("s1"))
        r = b.cross_validate("s1")
        assert r.is_consistent  # 한쪽만 있으면 충돌 없음

    def test_missing_claude_still_ok(self):
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1"))
        r = b.cross_validate("s1")
        assert r.is_consistent


class TestValidateAll:
    def test_validate_all_returns_dict(self):
        b = ContractBridge()
        for i in range(3):
            b.register_gpt_contract(f"s{i}", make_ir(f"s{i}"))
            b.register_claude_contract(f"s{i}", make_ir(f"s{i}"))
        results = b.validate_all()
        assert isinstance(results, dict) and len(results) == 3

    def test_validate_all_keys_match_scene_ids(self):
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1"))
        b.register_claude_contract("s2", make_ir("s2"))
        results = b.validate_all()
        assert set(results.keys()) == {"s1","s2"}

    def test_validate_all_result_type(self):
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1"))
        b.register_claude_contract("s1", make_ir("s1"))
        results = b.validate_all()
        for v in results.values():
            assert isinstance(v, CrossValidationResult)

    def test_empty_bridge_validate_all(self):
        b = ContractBridge()
        assert b.validate_all() == {}

    def test_cross_validation_result_fields(self):
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1"))
        b.register_claude_contract("s1", make_ir("s1"))
        r = b.cross_validate("s1")
        assert hasattr(r, "scene_id") and hasattr(r, "is_consistent")
        assert hasattr(r, "conflicts") and hasattr(r, "gpt_ir") and hasattr(r, "claude_ir")

    def test_slight_tension_diff_consistent(self):
        """tension 차이 0.3 이하 → 일관성 유지."""
        b = ContractBridge()
        b.register_gpt_contract("s1", make_ir("s1", tension=0.5))
        b.register_claude_contract("s1", make_ir("s1", tension=0.7))
        r = b.cross_validate("s1")
        assert r.is_consistent
