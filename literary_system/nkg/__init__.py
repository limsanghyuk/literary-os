"""V360: Narrative Knowledge Graph (NKG) 패키지."""
from literary_system.nkg.schema import (
    NKGNodeType, NKGEdgeType, NKGEdge,
    SceneNode as NKGSceneNode,
    CharacterNode as NKGCharacterNode,
    EventNode as NKGEventNode,
    ForeshadowNode as NKGForeshadowNode,
    EpisodeNode as NKGEpisodeNode,
    ArcNode as NKGArcNode,
    ThemeNode as NKGThemeNode,
    ConflictClusterNode, NarrativeProcessNode,
    SemanticModelState, ConflictType,
    CAUSAL_EDGE_TYPES, EMOTIONAL_EDGE_TYPES,
    FORESHADOW_EDGE_TYPES, REFERENCE_EDGE_TYPES, PROCESS_EDGE_TYPES,
    make_cluster_id, make_process_id,
)
from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.staleness import DKGStalenessTrackerV2 as NKGStalenessTracker

__all__ = [
    "NKGNodeType", "NKGEdgeType", "NKGEdge",
    "NKGSceneNode", "NKGCharacterNode", "NKGEventNode",
    "NKGForeshadowNode", "NKGEpisodeNode", "NKGArcNode", "NKGThemeNode",
    "ConflictClusterNode", "NarrativeProcessNode",
    "SemanticModelState", "ConflictType",
    "CAUSAL_EDGE_TYPES", "EMOTIONAL_EDGE_TYPES",
    "FORESHADOW_EDGE_TYPES", "REFERENCE_EDGE_TYPES", "PROCESS_EDGE_TYPES",
    "NKGGraphStore", "NKGStalenessTracker",
    "make_cluster_id", "make_process_id",
]
