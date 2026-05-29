"""
absorption/base.py — 경쟁 흡수 공통 데이터 모델 (SP-C.4 C-M-11)
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class AbsorptionStatus(str, Enum):
    PENDING   = "pending"
    ANALYZED  = "analyzed"
    ABSORBED  = "absorbed"
    REJECTED  = "rejected"


@dataclass
class FeatureGap:
    """경쟁사 기능 중 Literary OS에 없거나 열등한 항목."""
    feature_name: str
    competitor: str
    gap_type: str           # "missing" | "inferior" | "different_approach"
    priority: str           # "high" | "medium" | "low"
    ip_risk: str            # "high" | "medium" | "low"
    description: str = ""
    absorption_note: str = ""


@dataclass
class IPAdvisoryCommit:
    """IP 자문 커밋 기록 — C-M-11 의무 사항."""
    competitor: str
    commit_hash: str        # git commit hash (실제 commit 시 채워짐)
    advisory_ref: str       # 자문 번호 (예: "IP-ADV-001")
    findings: List[str] = field(default_factory=list)
    cleared: bool = False   # IP 법무 검토 완료 여부


@dataclass
class CompetitorProfile:
    """경쟁사 분석 프로파일."""
    name: str
    version_analyzed: str
    category: str           # "ai_writing" | "screenplay" | "narrative"
    pricing_model: str
    target_market: str
    core_differentiators: List[str] = field(default_factory=list)
    weaknesses: List[str] = field(default_factory=list)
    feature_gaps: List[FeatureGap] = field(default_factory=list)
    ip_advisory: Optional[IPAdvisoryCommit] = None
    status: AbsorptionStatus = AbsorptionStatus.PENDING


@dataclass
class AbsorptionReport:
    """경쟁 흡수 분석 최종 보고서."""
    competitor: str
    profile: CompetitorProfile
    absorbed_features: List[str] = field(default_factory=list)
    rejected_features: List[str] = field(default_factory=list)
    gate_id: str = ""
    gate_passed: bool = False
    summary: str = ""

    def passed(self) -> bool:
        return self.gate_passed and self.profile.ip_advisory is not None
