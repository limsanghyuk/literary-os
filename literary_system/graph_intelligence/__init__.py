"""literary_system/graph_intelligence — Phase 4 GIG (V526~V529)"""
from literary_system.graph_intelligence.narrative_graph_schema import (
    CharacterNode, DialogueIntentNode, EmotionPressureNode, EventNode,
    MotifNode, NarrativeEdge, NarrativeEdgeType, NarrativeImpactReport,
    NarrativeNode, NarrativeNodeType, RelationshipNode, RevealNode,
    SceneNode, SecretNode, TimeDeltaNode,
)
from literary_system.graph_intelligence.narrative_graph_store import NarrativeGraphStore
from literary_system.graph_intelligence.narrative_graph_indexer import (
    IndexInput, NarrativeGraphIndexer,
)
from literary_system.graph_intelligence.narrative_impact_analyzer import NarrativeImpactAnalyzer
from literary_system.graph_intelligence.scene_change_pre_gate import (
    Gate26Result, SceneChangePreGate,
)
__all__ = [
    "NarrativeNodeType","NarrativeEdgeType","NarrativeNode","NarrativeEdge",
    "NarrativeImpactReport","CharacterNode","SceneNode","EventNode",
    "SecretNode","RevealNode","MotifNode","RelationshipNode",
    "EmotionPressureNode","TimeDeltaNode","DialogueIntentNode",
    "NarrativeGraphStore","IndexInput","NarrativeGraphIndexer",
    "NarrativeImpactAnalyzer","Gate26Result","SceneChangePreGate",
]

# V546 Cleanup — P1~P8 해소 모듈
from .graph_sync_orchestrator import GraphSyncOrchestrator, SyncReport
from .gate_hierarchy_manager import (
    GateHierarchyManager, HierarchyGateResult,
    get_gate_hierarchy_manager,
)
from .llm0_static_gate import LLM0StaticGate, LLM0StaticResult
from .adr_index_generator import ADRIndexGenerator, ADREntry
from .asd.safety_augmented_auto_repair import (
    SafetyAugmentedAutoRepair, SafetyRepairResult, SafetyCheckResult,
)
