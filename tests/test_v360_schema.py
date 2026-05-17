"""V360: NKG 스키마 확장 테스트 — 신규 타입 검증."""
import sys, time
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.nkg.schema import (
    NKGNodeType, NKGEdgeType, SemanticModelState, ConflictType,
    SceneNode, CharacterNode, EventNode, ForeshadowNode,
    ConflictClusterNode, NarrativeProcessNode, NKGEdge,
    make_cluster_id, make_process_id,
    CAUSAL_EDGE_TYPES, EMOTIONAL_EDGE_TYPES, FORESHADOW_EDGE_TYPES,
    PROCESS_EDGE_TYPES,
)


class TestNKGNodeTypeV360:
    def test_conflict_cluster_exists(self):
        assert NKGNodeType.CONFLICT_CLUSTER.value == "conflict_cluster"

    def test_narrative_process_exists(self):
        assert NKGNodeType.NARRATIVE_PROCESS.value == "narrative_process"

    def test_all_v360_types(self):
        types = {t.value for t in NKGNodeType}
        assert "conflict_cluster" in types and "narrative_process" in types

    def test_legacy_types_preserved(self):
        types = {t.value for t in NKGNodeType}
        for t in ["scene","character","event","foreshadow","episode","arc","theme"]:
            assert t in types


class TestNKGEdgeTypeV360:
    def test_step_in_narrative_exists(self):
        assert NKGEdgeType.STEP_IN_NARRATIVE.value == "StepInNarrative"

    def test_in_cluster_exists(self):
        assert NKGEdgeType.IN_CLUSTER.value == "InCluster"

    def test_cluster_link_exists(self):
        assert NKGEdgeType.CLUSTER_LINK.value == "ClusterLink"

    def test_contract_link_exists(self):
        assert NKGEdgeType.CONTRACT_LINK.value == "ContractLink"

    def test_process_edge_types_set(self):
        assert "StepInNarrative" in PROCESS_EDGE_TYPES
        assert "InCluster" in PROCESS_EDGE_TYPES
        assert "ClusterLink" in PROCESS_EDGE_TYPES

    def test_causal_edge_types_preserved(self):
        assert "CausalLink" in CAUSAL_EDGE_TYPES
        assert "Enables" in CAUSAL_EDGE_TYPES

    def test_emotional_edge_types_preserved(self):
        assert "EmotionalEcho" in EMOTIONAL_EDGE_TYPES


class TestSemanticModelState:
    def test_write_state(self):
        assert SemanticModelState.WRITE.value == "write"

    def test_reconcile_state(self):
        assert SemanticModelState.RECONCILE.value == "reconcile"

    def test_frozen_state(self):
        assert SemanticModelState.FROZEN.value == "frozen"

    def test_all_three_states(self):
        states = {s.value for s in SemanticModelState}
        assert states == {"write","reconcile","frozen"}


class TestConflictType:
    def test_antagonist(self):
        assert ConflictType.ANTAGONIST.value == "antagonist"

    def test_rival(self):
        assert ConflictType.RIVAL.value == "rival"

    def test_neutral(self):
        assert ConflictType.NEUTRAL.value == "neutral"

    def test_complex(self):
        assert ConflictType.COMPLEX.value == "complex"

    def test_ally(self):
        assert ConflictType.ALLY.value == "ally"


class TestConflictClusterNode:
    def test_node_type_auto(self):
        cn = ConflictClusterNode(node_type=NKGNodeType.CONFLICT_CLUSTER,
                                  node_id="cl1", label="군집",
                                  cluster_id="cl1", conflict_type=ConflictType.RIVAL)
        assert cn.node_type == NKGNodeType.CONFLICT_CLUSTER

    def test_member_ids_default_empty(self):
        cn = ConflictClusterNode(node_type=NKGNodeType.CONFLICT_CLUSTER,
                                  node_id="cl1", label="군집",
                                  cluster_id="cl1", conflict_type=ConflictType.NEUTRAL)
        assert cn.member_ids == []

    def test_cohesion_default_zero(self):
        cn = ConflictClusterNode(node_type=NKGNodeType.CONFLICT_CLUSTER,
                                  node_id="cl1", label="군집",
                                  cluster_id="cl1", conflict_type=ConflictType.NEUTRAL)
        assert cn.cohesion_score == 0.0

    def test_content_hash(self):
        cn = ConflictClusterNode(node_type=NKGNodeType.CONFLICT_CLUSTER,
                                  node_id="cl1", label="군집",
                                  cluster_id="cl1", conflict_type=ConflictType.NEUTRAL)
        h = cn.content_hash()
        assert isinstance(h, str) and len(h) == 12

    def test_to_dict(self):
        cn = ConflictClusterNode(node_type=NKGNodeType.CONFLICT_CLUSTER,
                                  node_id="cl1", label="군집",
                                  cluster_id="cl1", conflict_type=ConflictType.NEUTRAL)
        d = cn.to_dict()
        assert d["node_id"] == "cl1" and d["node_type"] == "conflict_cluster"


class TestNarrativeProcessNode:
    def test_node_type_auto(self):
        pn = NarrativeProcessNode(node_type=NKGNodeType.NARRATIVE_PROCESS,
                                   node_id="p1", label="프로세스",
                                   process_id="p1")
        assert pn.node_type == NKGNodeType.NARRATIVE_PROCESS

    def test_steps_default_empty(self):
        pn = NarrativeProcessNode(node_type=NKGNodeType.NARRATIVE_PROCESS,
                                   node_id="p1", label="프로세스",
                                   process_id="p1")
        assert pn.steps == [] and pn.tension_arc == []

    def test_foreshadow_candidates_default_empty(self):
        pn = NarrativeProcessNode(node_type=NKGNodeType.NARRATIVE_PROCESS,
                                   node_id="p1", label="프로세스",
                                   process_id="p1")
        assert pn.foreshadow_candidates == []


class TestMakeIds:
    def test_cluster_id_format(self):
        assert make_cluster_id(0)  == "cluster_0000"
        assert make_cluster_id(99) == "cluster_0099"

    def test_process_id_format(self):
        assert make_process_id(0)  == "process_0000"
        assert make_process_id(10) == "process_0010"

    def test_ids_are_strings(self):
        assert isinstance(make_cluster_id(0), str)
        assert isinstance(make_process_id(0), str)


class TestNKGEdge:
    def test_edge_fields(self):
        e = NKGEdge("s0","s1", NKGEdgeType.CAUSAL_LINK, weight=1.5, confidence=0.9)
        assert e.source == "s0" and e.target == "s1"
        assert e.weight == 1.5 and e.confidence == 0.9

    def test_step_in_narrative_edge(self):
        e = NKGEdge("s0","s1", NKGEdgeType.STEP_IN_NARRATIVE, weight=1.0, confidence=1.0)
        assert e.edge_type == NKGEdgeType.STEP_IN_NARRATIVE

    def test_in_cluster_edge(self):
        e = NKGEdge("c0","cl1", NKGEdgeType.IN_CLUSTER, weight=1.0, confidence=1.0)
        assert e.edge_type == NKGEdgeType.IN_CLUSTER

    def test_contract_link_edge(self):
        e = NKGEdge("s0","s1", NKGEdgeType.CONTRACT_LINK, weight=0.8, confidence=0.9)
        assert e.edge_type == NKGEdgeType.CONTRACT_LINK
