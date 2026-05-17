"""
V324 - test_v324_scene_metrics.py
SceneMetricsCollector 단위 테스트 (20개)
"""
import pytest
from literary_system.evaluation.scene_metrics_collector import (
    SceneMetrics, SceneMetricsCollector,
)


@pytest.fixture
def collector():
    return SceneMetricsCollector()


# ════════════════════════════════════════════════════════════════════
# 1. SceneMetrics DTO
# ════════════════════════════════════════════════════════════════════

class TestSceneMetrics:
    def test_compute_sets_composite(self):
        m = SceneMetrics.compute(
            scene_id="s1",
            reader_pull=0.6,
            reader_afterimage=0.5,
            reader_uncertainty=0.3,
        )
        expected = (0.6 + 0.5 - 0.3) / 3.0
        assert m.reader_composite_score == pytest.approx(expected, abs=1e-6)

    def test_compute_defaults(self):
        m = SceneMetrics.compute(scene_id="s1")
        assert m.drse_gate_pass_rate == 1.0
        assert m.spatial_violation_count == 0
        assert m.character_state_valid is True
        assert m.relation_consistency == 1.0

    def test_to_dict_keys(self):
        m = SceneMetrics.compute(scene_id="s1")
        d = m.to_dict()
        for k in ["scene_id", "drse_gate_pass_rate", "spatial_violation_count",
                  "character_state_valid", "reader_pull", "reader_afterimage",
                  "reader_uncertainty", "reader_composite_score", "relation_consistency"]:
            assert k in d

    def test_scene_id_preserved(self):
        m = SceneMetrics.compute(scene_id="my_unique_scene")
        assert m.scene_id == "my_unique_scene"

    def test_negative_composite_possible(self):
        # uncertainty가 매우 높으면 composite가 음수 가능
        m = SceneMetrics.compute(
            scene_id="s1", reader_pull=0.1, reader_afterimage=0.1, reader_uncertainty=0.9
        )
        assert m.reader_composite_score < 0.2


# ════════════════════════════════════════════════════════════════════
# 2. SceneMetricsCollector — 컴포넌트 추출
# ════════════════════════════════════════════════════════════════════

class TestCollectorFromComponents:
    def test_none_inputs_give_defaults(self, collector):
        m = collector.collect_from_components("s1")
        assert m.drse_gate_pass_rate == 1.0
        assert m.spatial_violation_count == 0
        assert m.character_state_valid is True

    def test_drse_result_dict(self, collector):
        drse_result = {"gate_pass_rate": 0.75}
        m = collector.collect_from_components("s1", drse_result=drse_result)
        assert m.drse_gate_pass_rate == pytest.approx(0.75)

    def test_drse_result_object(self, collector):
        class FakeDRSE:
            gate_pass_rate = 0.85
        m = collector.collect_from_components("s1", drse_result=FakeDRSE())
        assert m.drse_gate_pass_rate == pytest.approx(0.85)

    def test_spatial_violations_from_object(self, collector):
        class FakeSpatial:
            violations = [1, 2, 3]
        m = collector.collect_from_components("s1", spatial_result=FakeSpatial())
        assert m.spatial_violation_count == 3

    def test_spatial_violations_from_dict(self, collector):
        m = collector.collect_from_components(
            "s1", spatial_result={"violation_count": 5}
        )
        assert m.spatial_violation_count == 5

    def test_char_valid_from_object(self, collector):
        class FakeChar:
            passed = False
        m = collector.collect_from_components("s1", char_result=FakeChar())
        assert m.character_state_valid is False

    def test_char_valid_from_dict(self, collector):
        m = collector.collect_from_components(
            "s1", char_result={"passed": True}
        )
        assert m.character_state_valid is True

    def test_reader_from_object(self, collector):
        class FakeReader:
            reader_pull = 0.7
            reader_afterimage = 0.6
            reader_uncertainty = 0.2
        m = collector.collect_from_components("s1", reader_est=FakeReader())
        assert m.reader_pull == pytest.approx(0.7)
        assert m.reader_afterimage == pytest.approx(0.6)
        assert m.reader_uncertainty == pytest.approx(0.2)

    def test_composite_computed_correctly(self, collector):
        class FakeReader:
            reader_pull = 0.6
            reader_afterimage = 0.5
            reader_uncertainty = 0.3
        m = collector.collect_from_components("s1", reader_est=FakeReader())
        expected = (0.6 + 0.5 - 0.3) / 3.0
        assert m.reader_composite_score == pytest.approx(expected, abs=1e-6)

    def test_no_rgs_gives_full_consistency(self, collector):
        m = collector.collect_from_components("s1")
        assert m.relation_consistency == pytest.approx(1.0)

    def test_all_components_combined(self, collector):
        class FakeDRSE:
            gate_pass_rate = 0.9
        class FakeSpatial:
            violations = []
        class FakeChar:
            passed = True
        class FakeReader:
            reader_pull = 0.65
            reader_afterimage = 0.55
            reader_uncertainty = 0.25
        m = collector.collect_from_components(
            "full_scene",
            drse_result=FakeDRSE(),
            spatial_result=FakeSpatial(),
            char_result=FakeChar(),
            reader_est=FakeReader(),
        )
        assert m.drse_gate_pass_rate == pytest.approx(0.9)
        assert m.spatial_violation_count == 0
        assert m.character_state_valid is True
        assert m.reader_pull == pytest.approx(0.65)


# ════════════════════════════════════════════════════════════════════
# 3. SceneMetrics → MAEOrchestrator 연동 통합
# ════════════════════════════════════════════════════════════════════

class TestSceneMetricsMAEIntegration:
    def test_metrics_feed_to_mae(self):
        from literary_system.evaluation.mae_orchestrator import MAEOrchestrator
        from literary_system.validation.coefficient_mapper import MAEWeights
        m = SceneMetrics.compute(
            "integration_scene",
            drse_gate_pass_rate=0.85,
            reader_pull=0.65,
            reader_afterimage=0.55,
            reader_uncertainty=0.25,
        )
        orc = MAEOrchestrator(weights=MAEWeights())
        result = orc.evaluate(m.scene_id, m)
        assert result.scene_id == "integration_scene"

    def test_collector_output_usable_by_mae(self, collector):
        from literary_system.evaluation.mae_orchestrator import MAEOrchestrator
        from literary_system.validation.coefficient_mapper import MAEWeights
        class FakeReader:
            reader_pull = 0.7
            reader_afterimage = 0.6
            reader_uncertainty = 0.2
        m = collector.collect_from_components("pipe_scene", reader_est=FakeReader())
        orc = MAEOrchestrator(weights=MAEWeights())
        result = orc.evaluate(m.scene_id, m)
        assert isinstance(result.consensus, bool)

    def test_bad_metrics_propagate_to_mae(self, collector):
        from literary_system.evaluation.mae_orchestrator import MAEOrchestrator
        from literary_system.validation.coefficient_mapper import MAEWeights
        class BadReader:
            reader_pull = 0.05
            reader_afterimage = 0.05
            reader_uncertainty = 0.95
        m = collector.collect_from_components(
            "bad_scene",
            drse_result={"gate_pass_rate": 0.1},
            spatial_result={"violation_count": 8},
            char_result={"passed": False},
            reader_est=BadReader(),
        )
        orc = MAEOrchestrator(weights=MAEWeights())
        result = orc.evaluate(m.scene_id, m)
        assert result.consensus is False

    def test_coefficient_mapper_mae_chain(self):
        from literary_system.validation.learned_coefficient_store import LearnedCoefficients
        from literary_system.validation.coefficient_mapper import CoefficientMapper
        from literary_system.evaluation.mae_orchestrator import MAEOrchestrator
        coeff = LearnedCoefficients(decay_lambda=0.08, residue_boost=2.0, arc_pressure_boost=1.8)
        mapper = CoefficientMapper()
        mae_w = mapper.map_to_mae(coeff)
        orc = MAEOrchestrator(weights=mae_w)
        m = SceneMetrics.compute("chain_scene", drse_gate_pass_rate=0.9,
                                  reader_pull=0.7, reader_afterimage=0.6, reader_uncertainty=0.2)
        result = orc.evaluate(m.scene_id, m)
        assert result.pass_count >= 0

    def test_roundtrip_coeff_update_via_mae(self):
        from literary_system.validation.learned_coefficient_store import LearnedCoefficients
        from literary_system.validation.coefficient_mapper import CoefficientMapper
        coeff_before = LearnedCoefficients()
        mapper = CoefficientMapper()
        mae_w = mapper.map_to_mae(coeff_before)
        coeff_after = mapper.map_from_mae(mae_w)
        mapper.record_change(coeff_before, coeff_after, reason="mae_integration")
        assert len(mapper.get_ledger()) == 1
