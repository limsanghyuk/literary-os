"""V329 Task1: NKG Schema 테스트 — NKGNodeType, NKGEdgeType, 노드 dataclass 전체 검증."""
import pytest
import time
from literary_system.nkg.schema import (
    NKGNodeType, NKGEdgeType, NKGEdge,
    NKGSceneNode, NKGCharacterNode, NKGEventNode,
    NKGForeshadowNode, NKGEpisodeNode, NKGArcNode, NKGThemeNode,
    CAUSAL_EDGE_TYPES, EMOTIONAL_EDGE_TYPES,
    FORESHADOW_EDGE_TYPES, REFERENCE_EDGE_TYPES,
    _sha256_short,
)


# ── NKGNodeType ──────────────────────────────────────────────
class TestNKGNodeType:
    def test_all_seven_types_defined(self):
        types = {t.value for t in NKGNodeType}
        assert types == {"scene","character","event","foreshadow","episode","arc","theme"}

    def test_scene_value(self):
        assert NKGNodeType.SCENE.value == "scene"

    def test_character_value(self):
        assert NKGNodeType.CHARACTER.value == "character"


# ── NKGEdgeType ──────────────────────────────────────────────
class TestNKGEdgeType:
    def test_twelve_types_defined(self):
        assert len(NKGEdgeType) == 12

    def test_causal_types_in_set(self):
        assert "CausalLink" in CAUSAL_EDGE_TYPES
        assert "Enables" in CAUSAL_EDGE_TYPES
        assert "Blocks" in CAUSAL_EDGE_TYPES

    def test_emotional_types_in_set(self):
        assert "EmotionalEcho" in EMOTIONAL_EDGE_TYPES
        assert "Resonance" in EMOTIONAL_EDGE_TYPES

    def test_foreshadow_types_in_set(self):
        assert "ForeshadowingOf" in FORESHADOW_EDGE_TYPES
        assert "PayoffOf" in FORESHADOW_EDGE_TYPES

    def test_reference_types_in_set(self):
        assert "TemporalBackRef" in REFERENCE_EDGE_TYPES
        assert "Involves" in REFERENCE_EDGE_TYPES

    def test_no_overlap_between_layers(self):
        layers = [CAUSAL_EDGE_TYPES, EMOTIONAL_EDGE_TYPES,
                  FORESHADOW_EDGE_TYPES, REFERENCE_EDGE_TYPES]
        all_vals = []
        for L in layers:
            all_vals.extend(L)
        assert len(all_vals) == len(set(all_vals)), "레이어 간 엣지 타입 중복"


# ── NKGSceneNode ─────────────────────────────────────────────
class TestNKGSceneNode:
    def _make(self, **kw):
        defaults = dict(scene_id="s1", episode_id="ep1",
                        content="첫 번째 장면 내용")
        defaults.update(kw)
        return NKGSceneNode(**defaults)

    def test_basic_creation(self):
        node = self._make()
        assert node.scene_id == "s1"
        assert node.episode_id == "ep1"
        assert node.node_type == NKGNodeType.SCENE

    def test_content_hash_auto_computed(self):
        node = self._make(content="테스트 내용")
        assert len(node.content_hash) == 16
        assert node.content_hash == _sha256_short("테스트 내용")

    def test_emotional_vector_defaults(self):
        node = self._make()
        assert len(node.emotional_vector) == 4
        assert all(0.0 <= v <= 1.0 for v in node.emotional_vector)

    def test_emotional_vector_clamped(self):
        node = self._make(emotional_vector=[2.0, -1.0, 0.5, 0.3])
        assert node.emotional_vector[0] == 1.0
        assert node.emotional_vector[1] == 0.0

    def test_emotional_vector_padded_if_short(self):
        node = self._make(emotional_vector=[0.8, 0.6])
        assert len(node.emotional_vector) == 4

    def test_tension_property(self):
        node = self._make(emotional_vector=[0.9, 0.5, 0.3, 0.1])
        assert node.tension == 0.9

    def test_sympathy_property(self):
        node = self._make(emotional_vector=[0.9, 0.5, 0.3, 0.1])
        assert node.sympathy == 0.5

    def test_is_stale_true_on_change(self):
        node = self._make(content="원본 내용")
        assert node.is_stale("수정된 내용") is True

    def test_is_stale_false_same_content(self):
        node = self._make(content="동일 내용")
        assert node.is_stale("동일 내용") is False

    def test_node_id_format(self):
        node = self._make(scene_id="s05", episode_id="ep02")
        assert node.node_id() == "scene:ep02:s05"

    def test_mae_score_clamped(self):
        node = self._make(mae_score=1.5)
        assert node.mae_score == 1.0


# ── NKGCharacterNode ─────────────────────────────────────────
class TestNKGCharacterNode:
    def test_basic_creation(self):
        node = NKGCharacterNode(char_id="c1", name="주인공",
                                motivation="복수")
        assert node.char_id == "c1"
        assert node.node_type == NKGNodeType.CHARACTER

    def test_invalid_arc_phase_defaults(self):
        node = NKGCharacterNode(char_id="c2", name="악당",
                                arc_phase="unknown_phase")
        assert node.arc_phase == "setup"

    def test_valid_arc_phases(self):
        for phase in ("setup","development","climax","resolution"):
            node = NKGCharacterNode(char_id="c3", name="X", arc_phase=phase)
            assert node.arc_phase == phase

    def test_node_id_format(self):
        node = NKGCharacterNode(char_id="hero1", name="영웅")
        assert node.node_id() == "character:hero1"


# ── NKGForeshadowNode ────────────────────────────────────────
class TestNKGForeshadowNode:
    def test_reveal_budget_clamped(self):
        node = NKGForeshadowNode(fsh_id="f1", description="복선",
                                 planted_scene="s1", reveal_budget=2.0)
        assert node.reveal_budget == 1.0

    def test_consume_reduces_budget(self):
        node = NKGForeshadowNode(fsh_id="f2", description="복선",
                                 planted_scene="s2", reveal_budget=1.0)
        consumed = node.consume(0.3)
        assert abs(consumed - 0.3) < 1e-9
        assert abs(node.reveal_budget - 0.7) < 1e-9

    def test_consume_resolves_when_empty(self):
        node = NKGForeshadowNode(fsh_id="f3", description="복선",
                                 planted_scene="s3", reveal_budget=0.05)
        node.consume(0.05)
        assert node.is_resolved is True

    def test_node_id_format(self):
        node = NKGForeshadowNode(fsh_id="fsh01", description="X",
                                 planted_scene="s1")
        assert node.node_id() == "foreshadow:fsh01"


# ── NKGEdge ──────────────────────────────────────────────────
class TestNKGEdge:
    def test_layer_causal(self):
        e = NKGEdge("a", "b", NKGEdgeType.CAUSAL_LINK)
        assert e.layer == "causal"

    def test_layer_emotional(self):
        e = NKGEdge("a", "b", NKGEdgeType.EMOTIONAL_ECHO)
        assert e.layer == "emotional"

    def test_layer_foreshadow(self):
        e = NKGEdge("a", "b", NKGEdgeType.FORESHADOWING)
        assert e.layer == "foreshadow"

    def test_layer_reference(self):
        e = NKGEdge("a", "b", NKGEdgeType.TEMPORAL_BACK)
        assert e.layer == "reference"

    def test_weight_clamped(self):
        e = NKGEdge("a", "b", NKGEdgeType.ENABLES, weight=3.0)
        assert e.weight == 1.0

    def test_confidence_clamped(self):
        e = NKGEdge("a", "b", NKGEdgeType.ENABLES, confidence=-0.5)
        assert e.confidence == 0.0
