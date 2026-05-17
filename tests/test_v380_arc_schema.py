"""
V380 테스트 — arc/schema.py
ArcAct, ArcPlotEdgeType, ArcPlotNode, ArcPlotEdge
"""
import pytest
from literary_system.arc.schema import (
    ArcAct, ArcPlotEdgeType, ArcPlotNode, ArcPlotEdge,
)


class TestArcAct:
    def test_all_four_acts_exist(self):
        acts = {a.value for a in ArcAct}
        assert "기" in acts and "승" in acts and "전" in acts and "결" in acts

    def test_arc_act_is_str_enum(self):
        assert isinstance(ArcAct.GI, str)
        assert ArcAct.GI == "기"

    def test_arc_act_from_value(self):
        assert ArcAct("기") == ArcAct.GI
        assert ArcAct("결") == ArcAct.GYEOL


class TestArcPlotEdgeType:
    def test_four_edge_types(self):
        types = {e.value for e in ArcPlotEdgeType}
        assert "CAUSAL" in types
        assert "FORESHADOW" in types
        assert "CALLBACK" in types
        assert "EMOTIONAL_ESCALATION" in types

    def test_edge_type_from_value(self):
        assert ArcPlotEdgeType("CAUSAL") == ArcPlotEdgeType.CAUSAL


class TestArcPlotNode:
    def test_basic_creation(self):
        node = ArcPlotNode(episode_id="ep_01", episode_index=1)
        assert node.episode_id == "ep_01"
        assert node.episode_index == 1
        assert node.act == ArcAct.GI  # 기본값

    def test_full_creation(self):
        node = ArcPlotNode(
            episode_id="ep_08",
            episode_index=8,
            title="비밀의 숲 8화",
            act=ArcAct.JEON,
            reveal_budget=0.7,
            emotional_target="충격",
            causal_inputs=["ep_07"],
            tension_level=0.85,
            forbidden_reveals=["fact_killer"],
        )
        assert node.title == "비밀의 숲 8화"
        assert node.act == ArcAct.JEON
        assert node.reveal_budget == 0.7
        assert node.tension_level == 0.85
        assert "fact_killer" in node.forbidden_reveals

    def test_to_dict_keys(self):
        node = ArcPlotNode(episode_id="ep_01", episode_index=1)
        d = node.to_dict()
        for key in ("episode_id", "episode_index", "act", "reveal_budget",
                    "emotional_target", "causal_inputs", "tension_level"):
            assert key in d

    def test_to_dict_act_is_value(self):
        node = ArcPlotNode(episode_id="ep_01", episode_index=1, act=ArcAct.SEUNG)
        assert node.to_dict()["act"] == "승"

    def test_default_causal_inputs_empty(self):
        node = ArcPlotNode(episode_id="ep_01", episode_index=1)
        assert node.causal_inputs == []

    def test_default_forbidden_reveals_empty(self):
        node = ArcPlotNode(episode_id="ep_01", episode_index=1)
        assert node.forbidden_reveals == []

    def test_metadata_field(self):
        node = ArcPlotNode(episode_id="ep_01", episode_index=1,
                           metadata={"writer": "홍길동"})
        assert node.metadata["writer"] == "홍길동"


class TestArcPlotEdge:
    def test_basic_creation(self):
        edge = ArcPlotEdge(
            source="ep_01", target="ep_02",
            edge_type=ArcPlotEdgeType.CAUSAL,
        )
        assert edge.source == "ep_01"
        assert edge.target == "ep_02"
        assert edge.edge_type == ArcPlotEdgeType.CAUSAL

    def test_default_weight(self):
        edge = ArcPlotEdge("ep_01", "ep_05", ArcPlotEdgeType.FORESHADOW)
        assert edge.weight == 1.0

    def test_to_dict(self):
        edge = ArcPlotEdge("ep_01", "ep_05", ArcPlotEdgeType.FORESHADOW,
                           weight=0.8, description="복선")
        d = edge.to_dict()
        assert d["source"] == "ep_01"
        assert d["target"] == "ep_05"
        assert d["edge_type"] == "FORESHADOW"
        assert d["weight"] == 0.8
        assert d["description"] == "복선"

    def test_callback_edge_type(self):
        edge = ArcPlotEdge("ep_14", "ep_03", ArcPlotEdgeType.CALLBACK)
        assert edge.edge_type == ArcPlotEdgeType.CALLBACK

    def test_emotional_escalation_edge(self):
        edge = ArcPlotEdge("ep_05", "ep_06", ArcPlotEdgeType.EMOTIONAL_ESCALATION,
                           weight=0.3)
        assert edge.weight == 0.3
