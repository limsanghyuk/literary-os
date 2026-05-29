"""literary_system/prose/ — V370 산문 렌더링 레이어 (Prose Rendering Layer)."""
from literary_system.prose.anti_llm_filter import FilterResult, KoreanAntiLLMFilter
from literary_system.prose.contract import ProseContractViolationError, ProseRenderContract
from literary_system.prose.emotion_behavior import BehaviorText, EmotionToBehaviorRenderer
from literary_system.prose.render_orchestrator import ClosedLoopRenderOrchestratorV2, FinalRenderedProseIR
from literary_system.prose.rhythm_rewriter import KoreanRhythmRewriter, RhythmResult
from literary_system.prose.sensory_anchor import AnchoredSceneIR, SensoryAnchorInjector
from literary_system.prose.style_dna import StyleDNA, StyleDNAProfile
from literary_system.prose.surface_scorer import ReaderSurfaceScorer, SurfaceScore

__all__ = [
    "ProseRenderContract", "ProseContractViolationError",
    "KoreanAntiLLMFilter", "FilterResult",
    "EmotionToBehaviorRenderer", "BehaviorText",
    "SensoryAnchorInjector", "AnchoredSceneIR",
    "KoreanRhythmRewriter", "RhythmResult",
    "ReaderSurfaceScorer", "SurfaceScore",
    "ClosedLoopRenderOrchestratorV2", "FinalRenderedProseIR",
    "StyleDNA", "StyleDNAProfile",
]

from .korean_cadence_planner import CadencePlan, KoreanCadencePlanner

# V11.39.0 ADR-128: node2_extensions/ AntiClicheSubstitutionEngine 연결
try:
    from literary_system.node2_extensions.node2_extensions import (
        AntiClicheSubstitutionEngine,
        EmotionToBehaviorTransformer,
        SubtextPlanner,
    )
except ImportError:
    AntiClicheSubstitutionEngine = None
    EmotionToBehaviorTransformer = None
    SubtextPlanner = None
