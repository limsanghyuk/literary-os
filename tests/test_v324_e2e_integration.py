"""
V324 - test_v324_e2e_integration.py
전 계층 E2E 통합 테스트 (20개)

V324 전체 파이프라인:
  LLMBridge → ActionPacketParser → SpatialConstraintGate
  → CharacterStateGate → ItemNodeExtension
  → SceneMetricsCollector → MAEOrchestrator
  → CoefficientMapper → LearnedCoefficientStore → 계수 갱신

테스트 원칙: Mock 최소화, 실제 컴포넌트 연결.
"""
import pytest

from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
from literary_system.action_compiler.action_packet import ActionPacket, ActionPacketParser
from literary_system.action_compiler.spatial_constraint_gate import SpatialConstraintGate
from literary_system.gate.character_state_gate import CharacterStateGate, CharacterState
from literary_system.graph.item_node_extension import ExtendedItemNode, ItemNodeExtension
from literary_system.evaluation.scene_metrics_collector import SceneMetrics, SceneMetricsCollector
from literary_system.evaluation.mae_orchestrator import MAEOrchestrator
from literary_system.evaluation.mae_agents import AlphaAgent, BetaAgent, GammaAgent
from literary_system.validation.coefficient_mapper import CoefficientMapper, MAEWeights
from literary_system.validation.learned_coefficient_store import (
    LearnedCoefficientStore, CoefficientRecord,
)


# ════════════════════════════════════════════════════════════════════
# 1. LLMBridge → ActionPacket 파이프라인
# ════════════════════════════════════════════════════════════════════

class TestLLMToActionPacket:
    def test_mock_bridge_to_action_packet(self):
        bridge = MockLLMBridge()
        raw = bridge.generate("씬을 작성하라", {"scene_id": "s1"})
        packet = bridge.parse_action_packet(raw)
        assert isinstance(packet, ActionPacket)

    def test_call_count_increments(self):
        bridge = MockLLMBridge()
        bridge.generate("p1", {})
        bridge.generate("p2", {})
        assert bridge.call_count == 2

    def test_multiple_scenes_sequential(self):
        bridge = MockLLMBridge(scripted_responses=[
            '{"action": "MOVE", "source": "char_a", "target": "loc_b"}',
            '{"action": "INTERACT", "source": "char_a", "target": "char_b"}',
        ])
        p1 = bridge.parse_action_packet(bridge.generate("scene1", {}))
        p2 = bridge.parse_action_packet(bridge.generate("scene2", {}))
        assert isinstance(p1, ActionPacket)
        assert isinstance(p2, ActionPacket)


# ════════════════════════════════════════════════════════════════════
# 2. CharacterStateGate 파이프라인
# ════════════════════════════════════════════════════════════════════

class TestCharacterStatePipeline:
    def test_alive_char_can_move(self):
        gate = CharacterStateGate()
        state = CharacterState(is_alive=True, is_hidden=False)
        result = gate.check_transition("char_hero", "MOVE", state)
        assert result.passed is True

    def test_dead_char_blocked(self):
        gate = CharacterStateGate()
        state = CharacterState(is_alive=False)
        result = gate.check_transition("char_villain", "INTERACT", state)
        assert result.passed is False

    def test_full_state_transition_chain(self):
        gate = CharacterStateGate()
        state = CharacterState(is_alive=True, is_hidden=False)
        # 살아있는 상태로 시작 → HIDE
        state = gate.apply_transition("char_a", "HIDE", state)
        assert state.is_hidden is True
        # 은신 중 → REVEAL
        state = gate.apply_transition("char_a", "REVEAL", state)
        assert state.is_hidden is False
        # KILL
        state = gate.apply_transition("char_a", "KILL", state)
        assert state.is_alive is False
        # 사망 후 MOVE 검사 → 위반
        result = gate.check_transition("char_a", "MOVE", state)
        assert result.passed is False

    def test_violations_accumulated_across_calls(self):
        gate = CharacterStateGate()
        dead = CharacterState(is_alive=False)
        gate.check_transition("c1", "MOVE", dead)
        gate.check_transition("c2", "HIDE", dead)
        assert len(gate.get_violations()) == 2


# ════════════════════════════════════════════════════════════════════
# 3. ItemNodeExtension 파이프라인
# ════════════════════════════════════════════════════════════════════

class TestItemPipeline:
    def test_register_and_acquire(self):
        ext = ItemNodeExtension()
        item = ExtendedItemNode("map_1", "지도", location_id="forest")
        ext.register(item)
        assert ext.validate_acquire(char_location_id="forest", item_id="map_1") is True

    def test_transfer_and_validate(self):
        ext = ItemNodeExtension()
        item = ExtendedItemNode("sword_1", "검", owner_id="char_a", location_id="castle")
        ext.register(item)
        ext.transfer_ownership("sword_1", from_id="char_a", to_id="char_b")
        assert ext.get_item("sword_1").owner_id == "char_b"


# ════════════════════════════════════════════════════════════════════
# 4. SceneMetrics → MAEOrchestrator 파이프라인
# ════════════════════════════════════════════════════════════════════

class TestSceneToMAEPipeline:
    def test_good_scene_consensus(self):
        m = SceneMetrics.compute(
            "good_scene",
            drse_gate_pass_rate=0.9,
            reader_pull=0.7, reader_afterimage=0.6, reader_uncertainty=0.2,
        )
        orc = MAEOrchestrator(weights=MAEWeights())
        result = orc.evaluate(m.scene_id, m)
        assert result.consensus is True

    def test_bad_scene_no_consensus(self):
        m = SceneMetrics.compute(
            "bad_scene",
            drse_gate_pass_rate=0.1,
            spatial_violation_count=8,
            character_state_valid=False,
            reader_pull=0.05, reader_afterimage=0.05, reader_uncertainty=0.95,
        )
        orc = MAEOrchestrator(weights=MAEWeights())
        result = orc.evaluate(m.scene_id, m)
        assert result.consensus is False

    def test_mae_result_has_three_agents(self):
        m = SceneMetrics.compute("s1")
        orc = MAEOrchestrator()
        result = orc.evaluate("s1", m)
        names = {v.agent_name for v in result.votes}
        assert "alpha" in names
        assert "beta" in names
        assert "gamma" in names


# ════════════════════════════════════════════════════════════════════
# 5. CoefficientMapper ↔ MAE ↔ LearnedCoefficientStore 전체 루프
# ════════════════════════════════════════════════════════════════════

class TestFullLearningLoop:
    def test_coeff_to_mae_to_coeff_roundtrip(self):
        mapper = CoefficientMapper()
        from literary_system.validation.learned_coefficient_store import LearnedCoefficients
        original = LearnedCoefficients(decay_lambda=0.05, residue_boost=1.5)
        mae_w = mapper.map_to_mae(original)
        reconstructed = mapper.map_from_mae(mae_w)
        assert abs(original.decay_lambda - reconstructed.decay_lambda) < 0.05

    def test_store_records_with_mae_metadata(self):
        store = LearnedCoefficientStore(update_interval=1)
        m = SceneMetrics.compute("s1", drse_gate_pass_rate=0.85)
        orc = MAEOrchestrator()
        mae_result = orc.evaluate(m.scene_id, m)
        rec = CoefficientRecord(
            scene_id="s1",
            judgment_label="GOOD" if mae_result.consensus else "BAD",
            gold_label="GOOD",
            reader_pull=m.reader_pull,
            reader_afterimage=m.reader_afterimage,
            reader_uncertainty=m.reader_uncertainty,
            final_drse_score=m.drse_gate_pass_rate,
            metadata={"mae_consensus": mae_result.consensus},
        )
        store.record(rec)
        assert store.total_records == 1

    def test_coefficient_update_after_records(self):
        store = LearnedCoefficientStore(update_interval=1)
        rec = CoefficientRecord(
            scene_id="s1", judgment_label="GOOD", gold_label="GOOD",
            reader_pull=0.7, reader_afterimage=0.6, reader_uncertainty=0.2,
            final_drse_score=0.85,
        )
        store.record(rec)
        assert store.updates_count == 1

    def test_mapper_ledger_records_change(self):
        from literary_system.validation.learned_coefficient_store import LearnedCoefficients
        mapper = CoefficientMapper()
        before = LearnedCoefficients()
        after = LearnedCoefficients(decay_lambda=0.08)
        mapper.record_change(before, after, reason="e2e_test")
        assert len(mapper.get_ledger()) == 1

    def test_full_pipeline_no_exceptions(self):
        """전체 파이프라인이 예외 없이 완주해야 한다."""
        bridge = MockLLMBridge()
        gate = CharacterStateGate()
        ext = ItemNodeExtension()
        collector = SceneMetricsCollector()
        mapper = CoefficientMapper()
        store = LearnedCoefficientStore(update_interval=3)
        orc = MAEOrchestrator()

        for i in range(3):
            raw = bridge.generate(f"scene_{i}", {})
            _ = bridge.parse_action_packet(raw)

            char_state = CharacterState()
            gate.check_transition(f"char_{i}", "MOVE", char_state)

            m = SceneMetrics.compute(f"scene_{i}", drse_gate_pass_rate=0.8)
            mae_result = orc.evaluate(m.scene_id, m)

            rec = CoefficientRecord(
                scene_id=f"scene_{i}",
                judgment_label="GOOD" if mae_result.consensus else "BAD",
                gold_label="GOOD",
                reader_pull=m.reader_pull,
                reader_afterimage=m.reader_afterimage,
                reader_uncertainty=m.reader_uncertainty,
                final_drse_score=m.drse_gate_pass_rate,
                metadata={"mae": mae_result.to_dict()},
            )
            store.record(rec)

        assert store.total_records == 3
        assert store.updates_count == 1
