"""V360: NKG 스키마 — CONFLICT_CLUSTER/NARRATIVE_PROCESS 추가."""
from __future__ import annotations
import hashlib, time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

class NKGNodeType(Enum):
    SCENE             = "scene"
    CHARACTER         = "character"
    EVENT             = "event"
    FORESHADOW        = "foreshadow"
    EPISODE           = "episode"
    ARC               = "arc"
    THEME             = "theme"
    CONFLICT_CLUSTER  = "conflict_cluster"
    NARRATIVE_PROCESS = "narrative_process"

class NKGEdgeType(Enum):
    CAUSAL_LINK       = "CausalLink"
    ENABLES           = "Enables"
    BLOCKS            = "Blocks"
    FORESHADOWING     = "ForeshadowingOf"
    PAYOFF            = "PayoffOf"
    EMOTIONAL_ECHO    = "EmotionalEcho"
    RESONANCE         = "Resonance"
    TEMPORAL_BACK     = "TemporalBackRef"
    INVOLVES          = "Involves"
    TRIGGERS_EVENT    = "TriggersEvent"
    PART_OF_ARC       = "PartOfArc"
    EXEMPLIFY_THEME   = "ExemplifyTheme"
    STEP_IN_NARRATIVE = "StepInNarrative"
    IN_CLUSTER        = "InCluster"
    CLUSTER_LINK      = "ClusterLink"
    CONTRACT_LINK     = "ContractLink"

CAUSAL_EDGE_TYPES    = frozenset({NKGEdgeType.CAUSAL_LINK.value, NKGEdgeType.ENABLES.value, NKGEdgeType.BLOCKS.value})
EMOTIONAL_EDGE_TYPES = frozenset({NKGEdgeType.EMOTIONAL_ECHO.value, NKGEdgeType.RESONANCE.value})
FORESHADOW_EDGE_TYPES= frozenset({NKGEdgeType.FORESHADOWING.value, NKGEdgeType.PAYOFF.value})
REFERENCE_EDGE_TYPES = frozenset({NKGEdgeType.TEMPORAL_BACK.value, NKGEdgeType.INVOLVES.value,
                                   NKGEdgeType.TRIGGERS_EVENT.value, NKGEdgeType.PART_OF_ARC.value,
                                   NKGEdgeType.EXEMPLIFY_THEME.value})
PROCESS_EDGE_TYPES   = frozenset({NKGEdgeType.STEP_IN_NARRATIVE.value, NKGEdgeType.IN_CLUSTER.value,
                                   NKGEdgeType.CLUSTER_LINK.value, NKGEdgeType.CONTRACT_LINK.value})
ACYCLIC_EDGE_TYPES   = CAUSAL_EDGE_TYPES

class SemanticModelState(Enum):
    WRITE     = "write"
    RECONCILE = "reconcile"
    FROZEN    = "frozen"

class ConflictType(Enum):
    ANTAGONIST = "antagonist"
    ALLY       = "ally"
    RIVAL      = "rival"
    NEUTRAL    = "neutral"
    COMPLEX    = "complex"

@dataclass
class NKGNode:
    node_type:  NKGNodeType
    node_id:    str
    label:      str
    metadata:   Dict[str, Any] = field(default_factory=dict)
    created_at: float          = field(default_factory=time.time)
    dirty:      bool           = False

    def content_hash(self) -> str:
        raw = f"{self.node_type.value}:{self.node_id}:{self.label}"
        return hashlib.sha256(raw.encode()).hexdigest()[:12]

    def to_dict(self) -> Dict[str, Any]:
        return {"node_id": self.node_id, "node_type": self.node_type.value,
                "label": self.label, "metadata": self.metadata}

@dataclass
class SceneNode(NKGNode):
    scene_order:      int   = 0
    tension_value:    float = 0.0
    emotional_vector: Dict[str, float] = field(default_factory=dict)
    last_modified:    float = field(default_factory=time.time)
    def __post_init__(self): self.node_type = NKGNodeType.SCENE

@dataclass
class CharacterNode(NKGNode):
    role:            str           = "unknown"
    knowledge_state: str           = "KNOWS"
    cluster_id:      Optional[str] = None
    def __post_init__(self): self.node_type = NKGNodeType.CHARACTER

@dataclass
class EventNode(NKGNode):
    event_type: str   = "generic"
    impact:     float = 0.5
    def __post_init__(self): self.node_type = NKGNodeType.EVENT

@dataclass
class ForeshadowNode(NKGNode):
    planted_scene:  str   = ""
    payoff_scene:   str   = ""
    reveal_budget:  float = 0.3
    is_candidate:   bool  = False
    def __post_init__(self): self.node_type = NKGNodeType.FORESHADOW

@dataclass
class EpisodeNode(NKGNode):
    episode_index: int = 0
    def __post_init__(self): self.node_type = NKGNodeType.EPISODE

@dataclass
class ArcNode(NKGNode):
    arc_type: str = "main"
    def __post_init__(self): self.node_type = NKGNodeType.ARC

@dataclass
class ThemeNode(NKGNode):
    theme_weight: float = 1.0
    def __post_init__(self): self.node_type = NKGNodeType.THEME

@dataclass
class ConflictClusterNode(NKGNode):
    cluster_id:     str          = ""
    member_ids:     List[str]    = field(default_factory=list)
    conflict_type:  ConflictType = ConflictType.NEUTRAL
    cohesion_score: float        = 0.0
    primary_scene:  str          = ""
    def __post_init__(self): self.node_type = NKGNodeType.CONFLICT_CLUSTER

@dataclass
class NarrativeProcessNode(NKGNode):
    process_id:            str         = ""
    entry_scene:           str         = ""
    resolution_scene:      str         = ""
    steps:                 List[str]   = field(default_factory=list)
    foreshadow_candidates: List[str]   = field(default_factory=list)
    tension_arc:           List[float] = field(default_factory=list)
    def __post_init__(self): self.node_type = NKGNodeType.NARRATIVE_PROCESS

@dataclass
class NKGEdge:
    source:     str
    target:     str
    edge_type:  NKGEdgeType
    weight:     float = 1.0
    confidence: float = 1.0
    metadata:   Dict[str, Any] = field(default_factory=dict)

def make_cluster_id(idx: int) -> str:
    return f"cluster_{idx:04d}"

def make_process_id(idx: int) -> str:
    return f"process_{idx:04d}"


# ── V329/V340 레거시 alias ─────────────────────────────────────
NKGSceneNode      = SceneNode
NKGCharacterNode  = CharacterNode
NKGEventNode      = EventNode
NKGForeshadowNode = ForeshadowNode
NKGEpisodeNode    = EpisodeNode
NKGArcNode        = ArcNode
NKGThemeNode      = ThemeNode

def _sha256_short(text: str) -> str:
    """V329 레거시 호환 — content_hash 보조 함수."""
    import hashlib
    return hashlib.sha256(text.encode()).hexdigest()[:12]
