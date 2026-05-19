"""V526 — NarrativeGraphSchema: 서사 지식 그래프 노드·엣지 (10+10)"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class NarrativeNodeType(Enum):
    CHARACTER="character"; SCENE="scene"; EVENT="event"; SECRET="secret"
    REVEAL="reveal"; MOTIF="motif"; RELATIONSHIP="relationship"
    EMOTION_PRESSURE="emotion_pressure"; TIME_DELTA="time_delta"; DIALOGUE_INTENT="dialogue_intent"

class NarrativeEdgeType(Enum):
    CAUSES="causes"; KNOWS="knows"; HIDES="hides"; REVEALS="reveals"
    DEPENDS_ON="depends_on"; CONTRADICTS="contradicts"; ESCALATES="escalates"
    RELIEVES="relieves"; FORESHADOWS="foreshadows"; ECHOES="echoes"

@dataclass
class NarrativeNode:
    node_id: str; node_type: NarrativeNodeType; label: str
    meta: Dict[str,Any] = field(default_factory=dict)
    def __hash__(self): return hash(self.node_id)
    def __eq__(self, o): return isinstance(o, NarrativeNode) and self.node_id==o.node_id

@dataclass
class NarrativeCharacterNode(NarrativeNode):
    role: str="supporting"; episode_first: int=1; episode_last: int=1
    def __post_init__(self): self.node_type=NarrativeNodeType.CHARACTER

@dataclass
class NarrativeSceneNode(NarrativeNode):
    episode: int=1; scene_idx: int=0; t_position: float=0.0
    def __post_init__(self): self.node_type=NarrativeNodeType.SCENE

@dataclass
class NarrativeEventNode(NarrativeNode):
    episode: int=1; scene_id: str=""; impact: float=0.5
    def __post_init__(self): self.node_type=NarrativeNodeType.EVENT

@dataclass
class SecretNode(NarrativeNode):
    holder_ids: List[str]=field(default_factory=list); reveal_episode: Optional[int]=None
    def __post_init__(self): self.node_type=NarrativeNodeType.SECRET

@dataclass
class RevealNode(NarrativeNode):
    secret_id: str=""; reveal_episode: int=1; reveal_scene: str=""; audience_only: bool=False
    def __post_init__(self): self.node_type=NarrativeNodeType.REVEAL

@dataclass
class MotifNode(NarrativeNode):
    symbol: str=""; appearances: List[str]=field(default_factory=list)
    def __post_init__(self): self.node_type=NarrativeNodeType.MOTIF

@dataclass
class RelationshipNode(NarrativeNode):
    char_a_id: str=""; char_b_id: str=""; rel_type: str="neutral"; episode: int=1
    def __post_init__(self): self.node_type=NarrativeNodeType.RELATIONSHIP

@dataclass
class EmotionPressureNode(NarrativeNode):
    char_id: str=""; pressure: float=0.5; episode: int=1
    def __post_init__(self): self.node_type=NarrativeNodeType.EMOTION_PRESSURE

@dataclass
class TimeDeltaNode(NarrativeNode):
    from_scene: str=""; to_scene: str=""; delta_days: int=0
    def __post_init__(self): self.node_type=NarrativeNodeType.TIME_DELTA

@dataclass
class DialogueIntentNode(NarrativeNode):
    scene_id: str=""; char_id: str=""; surface_text: str=""; hidden_intent: str=""
    def __post_init__(self): self.node_type=NarrativeNodeType.DIALOGUE_INTENT

@dataclass
class NarrativeEdge:
    edge_id: str; src_id: str; dst_id: str; edge_type: NarrativeEdgeType
    weight: float=1.0; episode: int=1; meta: Dict[str,Any]=field(default_factory=dict)
    def __hash__(self): return hash(self.edge_id)
    def __eq__(self, o): return isinstance(o, NarrativeEdge) and self.edge_id==o.edge_id

@dataclass
class NarrativeImpactReport:
    target_scene_id: str; change_description: str=""
    direct_impact: List[str]=field(default_factory=list)
    indirect_impact: List[str]=field(default_factory=list)
    reveal_impacts: List[str]=field(default_factory=list)
    motif_impacts: List[str]=field(default_factory=list)
    foreshadow_breaks: List[str]=field(default_factory=list)
    risk_score: float=0.0; risk_level: str="low"; decision: str="proceed"; reason: str=""

    def summary(self) -> str:
        return (f"=== NarrativeImpactReport ===\nTarget: {self.target_scene_id}\n"
                f"Risk: {self.risk_level.upper()} ({self.risk_score:.3f})\n"
                f"Decision: {self.decision}\nDirect:{len(self.direct_impact)} "
                f"Indirect:{len(self.indirect_impact)} Reveals:{len(self.reveal_impacts)} "
                f"ForeshadowBreaks:{len(self.foreshadow_breaks)}"
                + (f"\nReason: {self.reason}" if self.reason else ""))

CharacterNode = NarrativeCharacterNode  # V579 backward-compat alias

EventNode = NarrativeEventNode  # V579 backward-compat alias

SceneNode = NarrativeSceneNode  # V579 backward-compat alias
