"""test_v360_contract_extended.py — ContractBridge v1 심화 테스트 (V360)"""
import pytest
from literary_system.contract.bridge import (
    ContractBridge, SceneIntent, SceneIntentIR, CrossValidationResult
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def make_ir(scene_id="s1", intent=SceneIntent.REVEAL, tension=0.5,
            budget=0.3, delta=0.0, pov="주인공"):
    return SceneIntentIR(
        scene_id=scene_id, intent=intent,
        emotional_delta=delta, reveal_budget=budget,
        target_tension=tension, pov_character=pov,
    )


# ---------------------------------------------------------------------------
# TestSceneIntentEnum
# ---------------------------------------------------------------------------
class TestSceneIntentEnum:
    def test_all_six_intents_exist(self):
        intents = {i.value for i in SceneIntent}
        assert intents == {"reveal", "conceal", "foreshadow", "turn", "establish", "resolve"}

    def test_reveal_value(self):
        assert SceneIntent.REVEAL.value == "reveal"

    def test_conceal_value(self):
        assert SceneIntent.CONCEAL.value == "conceal"

    def test_foreshadow_value(self):
        assert SceneIntent.FORESHADOW.value == "foreshadow"

    def test_turn_value(self):
        assert SceneIntent.TURN.value == "turn"

    def test_establish_value(self):
        assert SceneIntent.ESTABLISH.value == "establish"

    def test_resolve_value(self):
        assert SceneIntent.RESOLVE.value == "resolve"

    def test_enum_count(self):
        assert len(list(SceneIntent)) == 6


# ---------------------------------------------------------------------------
# TestSceneIntentIR
# ---------------------------------------------------------------------------
class TestSceneIntentIR:
    def test_default_emotional_delta(self):
        ir = SceneIntentIR(scene_id="s1", intent=SceneIntent.REVEAL)
        assert ir.emotional_delta == 0.0

    def test_default_reveal_budget(self):
        ir = SceneIntentIR(scene_id="s1", intent=SceneIntent.ESTABLISH)
        assert ir.reveal_budget == pytest.approx(0.3)

    def test_default_target_tension(self):
        ir = SceneIntentIR(scene_id="s1", intent=SceneIntent.CONCEAL)
        assert ir.target_tension == pytest.approx(0.5)

    def test_custom_pov(self):
        ir = make_ir(pov="형사 김민준")
        assert ir.pov_character == "형사 김민준"

    def test_metadata_default_empty(self):
        ir = SceneIntentIR(scene_id="s1", intent=SceneIntent.TURN)
        assert ir.metadata == {}

    def test_metadata_set(self):
        ir = SceneIntentIR(scene_id="s1", intent=SceneIntent.FORESHADOW,
                           metadata={"tag": "cold_open"})
        assert ir.metadata["tag"] == "cold_open"


# ---------------------------------------------------------------------------
# TestContractBridgeRegister
# ---------------------------------------------------------------------------
class TestContractBridgeRegister:
    def test_register_gpt_contract(self):
        cb = ContractBridge()
        ir = make_ir("s1", SceneIntent.REVEAL)
        cb.register_gpt_contract("s1", ir)
        assert "s1" in cb.scene_ids()

    def test_register_claude_contract(self):
        cb = ContractBridge()
        ir = make_ir("s2", SceneIntent.ESTABLISH)
        cb.register_claude_contract("s2", ir)
        assert "s2" in cb.scene_ids()

    def test_scene_ids_union(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1"))
        cb.register_claude_contract("s2", make_ir("s2"))
        assert set(cb.scene_ids()) == {"s1", "s2"}

    def test_overwrite_gpt_contract(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1", SceneIntent.REVEAL))
        cb.register_gpt_contract("s1", make_ir("s1", SceneIntent.CONCEAL))
        result = cb.cross_validate("s1")
        assert result.gpt_ir.intent == SceneIntent.CONCEAL


# ---------------------------------------------------------------------------
# TestCrossValidateConsistent
# ---------------------------------------------------------------------------
class TestCrossValidateConsistent:
    def test_consistent_same_intent(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1", SceneIntent.REVEAL, tension=0.5, budget=0.3))
        cb.register_claude_contract("s1", make_ir("s1", SceneIntent.REVEAL, tension=0.5, budget=0.3))
        r = cb.cross_validate("s1")
        assert r.is_consistent is True
        assert r.conflicts == []

    def test_consensus_ir_created_when_consistent(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1", SceneIntent.FORESHADOW, tension=0.4, budget=0.2))
        cb.register_claude_contract("s1", make_ir("s1", SceneIntent.FORESHADOW, tension=0.6, budget=0.2))
        r = cb.cross_validate("s1")
        assert r.is_consistent is True
        assert r.consensus_ir is not None
        assert r.consensus_ir.target_tension == pytest.approx(0.5)

    def test_consensus_budget_average(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1", SceneIntent.TURN, budget=0.2))
        cb.register_claude_contract("s1", make_ir("s1", SceneIntent.TURN, budget=0.4))
        r = cb.cross_validate("s1")
        assert r.consensus_ir.reveal_budget == pytest.approx(0.3)

    def test_consistent_tension_within_threshold(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1", SceneIntent.ESTABLISH, tension=0.5))
        cb.register_claude_contract("s1", make_ir("s1", SceneIntent.ESTABLISH, tension=0.79))
        r = cb.cross_validate("s1")
        # delta=0.29 < 0.30 threshold → consistent
        assert r.is_consistent is True


# ---------------------------------------------------------------------------
# TestCrossValidateConflict
# ---------------------------------------------------------------------------
class TestCrossValidateConflict:
    def test_conflict_different_intent(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1", SceneIntent.REVEAL))
        cb.register_claude_contract("s1", make_ir("s1", SceneIntent.CONCEAL))
        r = cb.cross_validate("s1")
        assert r.is_consistent is False
        assert any("intent" in c for c in r.conflicts)

    def test_conflict_tension_too_far(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1", SceneIntent.FORESHADOW, tension=0.1))
        cb.register_claude_contract("s1", make_ir("s1", SceneIntent.FORESHADOW, tension=0.9))
        r = cb.cross_validate("s1")
        assert r.is_consistent is False
        assert any("tension" in c for c in r.conflicts)

    def test_conflict_budget_too_far(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1", SceneIntent.TURN, budget=0.0))
        cb.register_claude_contract("s1", make_ir("s1", SceneIntent.TURN, budget=0.5))
        r = cb.cross_validate("s1")
        assert r.is_consistent is False
        assert any("budget" in c for c in r.conflicts)

    def test_no_consensus_when_conflict(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1", SceneIntent.REVEAL))
        cb.register_claude_contract("s1", make_ir("s1", SceneIntent.CONCEAL))
        r = cb.cross_validate("s1")
        assert r.consensus_ir is None

    def test_multiple_conflicts_accumulated(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1", SceneIntent.REVEAL, tension=0.0, budget=0.0))
        cb.register_claude_contract("s1", make_ir("s1", SceneIntent.CONCEAL, tension=1.0, budget=1.0))
        r = cb.cross_validate("s1")
        assert len(r.conflicts) >= 2


# ---------------------------------------------------------------------------
# TestCrossValidateMissing
# ---------------------------------------------------------------------------
class TestCrossValidateMissing:
    def test_missing_claude_consistent(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1"))
        r = cb.cross_validate("s1")
        assert r.is_consistent is True
        assert r.claude_ir is None

    def test_missing_gpt_consistent(self):
        cb = ContractBridge()
        cb.register_claude_contract("s1", make_ir("s1"))
        r = cb.cross_validate("s1")
        assert r.is_consistent is True
        assert r.gpt_ir is None

    def test_missing_both_returns_consistent(self):
        cb = ContractBridge()
        r = cb.cross_validate("s_unknown")
        assert r.is_consistent is True


# ---------------------------------------------------------------------------
# TestValidateAll
# ---------------------------------------------------------------------------
class TestValidateAll:
    def test_validate_all_empty(self):
        cb = ContractBridge()
        results = cb.validate_all()
        assert results == {}

    def test_validate_all_multiple_scenes(self):
        cb = ContractBridge()
        for i in range(5):
            cb.register_gpt_contract(f"s{i}", make_ir(f"s{i}", SceneIntent.REVEAL))
            cb.register_claude_contract(f"s{i}", make_ir(f"s{i}", SceneIntent.REVEAL))
        results = cb.validate_all()
        assert len(results) == 5
        assert all(v.is_consistent for v in results.values())

    def test_validate_all_mixed_results(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1", SceneIntent.REVEAL))
        cb.register_claude_contract("s1", make_ir("s1", SceneIntent.REVEAL))
        cb.register_gpt_contract("s2", make_ir("s2", SceneIntent.REVEAL))
        cb.register_claude_contract("s2", make_ir("s2", SceneIntent.CONCEAL))
        results = cb.validate_all()
        assert results["s1"].is_consistent is True
        assert results["s2"].is_consistent is False

    def test_validate_all_returns_cross_validation_result(self):
        cb = ContractBridge()
        cb.register_gpt_contract("s1", make_ir("s1"))
        results = cb.validate_all()
        assert isinstance(results["s1"], CrossValidationResult)

class TestContractBridgeEdge:
    def test_scene_ids_no_duplicates(self):
        cb = ContractBridge()
        ir = make_ir("dup_scene")
        cb.register_gpt_contract("dup_scene", ir)
        cb.register_claude_contract("dup_scene", ir)
        ids = cb.scene_ids()
        assert ids.count("dup_scene") == 1
