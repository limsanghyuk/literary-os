"""longform/ — V393~V398
8개 장편 이론 모듈. 모두 결정론적 (LLM 호출 0회).
"""
from .fractal_topology import (
    FractalUnitType, FractalPlotUnit, FractalReport, FractalTopologyValidator
)
from .load_balancing import (
    EpisodeLoad, LoadBalanceReport, DramaticLoadBalancer
)
from .agency_conservation import (
    AgencyEventType, AgencyDelta, AgencyReport, AgencyConservationChecker
)
from .payoff_debt import (
    DebtType, DebtPriority, DebtStatus, PayoffDebt, PayoffDebtLedger
)
from .scene_necessity import (
    SceneFunctionType, NecessityResult, NecessityReport, SceneNecessityChecker
)
from .dialogue_pragmatics import (
    DialogueProfile, DialogueForce, DialogueReport, DialoguePragmaticsEngine
)
from .voice_manifold import (
    VoiceVector, DriftType, DriftResult, VoiceDriftReport, VoiceManifold, StyleGenome
)
from .attention_economy import (
    SceneAttentionValue, FatigueReport, NarrativeAttentionEconomy
)

__all__ = [
    "FractalUnitType","FractalPlotUnit","FractalReport","FractalTopologyValidator",
    "EpisodeLoad","LoadBalanceReport","DramaticLoadBalancer",
    "AgencyEventType","AgencyDelta","AgencyReport","AgencyConservationChecker",
    "DebtType","DebtPriority","DebtStatus","PayoffDebt","PayoffDebtLedger",
    "SceneFunctionType","NecessityResult","NecessityReport","SceneNecessityChecker",
    "DialogueProfile","DialogueForce","DialogueReport","DialoguePragmaticsEngine",
    "VoiceVector","DriftType","DriftResult","VoiceDriftReport","VoiceManifold","StyleGenome",
    "SceneAttentionValue","FatigueReport","NarrativeAttentionEconomy",
]
