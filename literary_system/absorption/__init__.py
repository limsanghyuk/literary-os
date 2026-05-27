"""
literary_system.absorption
SP-C.4 경쟁 흡수 패키지 — NovelAI·Sudowrite·Novelcrafter·NolanAI·Jenova 분석
"""
from .base import CompetitorProfile, AbsorptionReport, FeatureGap, IPAdvisoryCommit
from .novel_ai import NovelAIAbsorber
from .sudowrite import SudowriteAbsorber

__all__ = [
    "CompetitorProfile", "AbsorptionReport", "FeatureGap", "IPAdvisoryCommit",
    "NovelAIAbsorber",
    "SudowriteAbsorber",
]
