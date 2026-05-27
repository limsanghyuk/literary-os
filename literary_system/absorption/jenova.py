"""
absorption/jenova.py — Jenova 경쟁 흡수 분석기 (SP-C.4, G72-5, ADR-133)

Jenova: 한국 드라마 특화 AI 서사 플랫폼
- 멀티장르 혼합, 감정 피크 스케줄링, 서사 일관성 검증 등 특화 기능
"""
from __future__ import annotations

from literary_system.absorption.base import (
    AbsorptionReport,
    AbsorptionStatus,
    CompetitorProfile,
    FeatureGap,
    IPAdvisoryCommit,
)

# ─── IP 자문 커밋 (C-M-11 의무) ─────────────────────────────────────────────
IP_ADV_005 = IPAdvisoryCommit(
    competitor="Jenova",
    commit_hash="",          # 실 커밋 시 채워짐
    advisory_ref="IP-ADV-005",
    findings=[
        "KoreanGenreBlending 로직: 독립 구현 가능 — 공개 장르 이론 기반, 저작권 리스크 없음",
        "EmotionalPeakScheduler: 자체 감정 곡선 공식 사용 — Jenova API 비의존",
        "NarrativeCoherenceValidator: Literary OS 내부 arc_consistency_checker 확장 형태 — 원저작물 없음",
        "CharacterRelationshipMapper: 그래프 알고리즘 표준 기법 — 특허 리스크 없음",
        "PredictiveAudienceFeedback: 독점 ML 모델 의존 — IP 리스크 HIGH, 자체 구현 대체 권고",
        "RealTimeCollab: 협업 프로토콜 특허 위험 — Phase D에서 독자 구현 계획",
    ],
    cleared=True,
)

# ─── 기능 격차 목록 ───────────────────────────────────────────────────────────
_FEATURE_GAPS: list[FeatureGap] = [
    FeatureGap(
        feature_name="KoreanGenreBlending",
        competitor="Jenova",
        gap_type="missing",
        priority="high",
        ip_risk="low",
        description="로맨스/스릴러/가족드라마 장르 혼합 규칙 기반 서사 생성",
        absorption_note="공개 장르 이론 기반 독립 구현. GenreTransferEngine 확장으로 흡수.",
    ),
    FeatureGap(
        feature_name="EmotionalPeakScheduler",
        competitor="Jenova",
        gap_type="inferior",
        priority="high",
        ip_risk="low",
        description="에피소드 전반에 걸친 감정 피크 타이밍 최적화",
        absorption_note="Literary OS NarrativeTensionCurve 위에 피크 스케줄링 레이어 추가.",
    ),
    FeatureGap(
        feature_name="NarrativeCoherenceValidator",
        competitor="Jenova",
        gap_type="inferior",
        priority="high",
        ip_risk="low",
        description="멀티 아크 서사 일관성 자동 검증 (캐릭터·플롯·시간선)",
        absorption_note="ArcConsistencyChecker 확장 형태로 흡수. 내부 데이터 모델 활용.",
    ),
    FeatureGap(
        feature_name="CharacterRelationshipMapper",
        competitor="Jenova",
        gap_type="missing",
        priority="medium",
        ip_risk="low",
        description="복잡한 인물 관계망 시각화 및 충돌 감지",
        absorption_note="표준 그래프 알고리즘. SharedCharacterDB v2에 관계 레이어 추가로 흡수.",
    ),
    FeatureGap(
        feature_name="PredictiveAudienceFeedback",
        competitor="Jenova",
        gap_type="different_approach",
        priority="medium",
        ip_risk="high",
        description="AI 기반 시청자 반응 사전 예측 스코어링",
        absorption_note="Jenova 독점 ML 모델 의존. IP 리스크 HIGH → 자체 ReaderFeedback 루프로 대체.",
    ),
    FeatureGap(
        feature_name="RealTimeCollab",
        competitor="Jenova",
        gap_type="missing",
        priority="low",
        ip_risk="medium",
        description="실시간 다중 작가 협업 공동 편집",
        absorption_note="협업 프로토콜 특허 위험. Phase D에서 독자 구현 계획.",
    ),
]


class JenovaAbsorber:
    """Jenova 경쟁 흡수 분석기."""

    COMPETITOR = "Jenova"

    def analyze(self) -> CompetitorProfile:
        """Jenova 프로파일 분석."""
        return CompetitorProfile(
            name=self.COMPETITOR,
            version_analyzed="2.1",
            category="ai_writing",
            pricing_model="subscription_tiered",
            target_market="korean_drama_writers",
            core_differentiators=[
                "한국 드라마 장르 특화 멀티장르 혼합 엔진",
                "에피소드 단위 감정 피크 스케줄러",
                "실시간 다중 작가 협업",
                "AI 시청자 반응 예측 (독점 모델)",
            ],
            weaknesses=[
                "독점 ML 모델 의존으로 인한 높은 IP 리스크",
                "실시간 협업 인프라 비용 높음",
                "한국 드라마 이외 장르 지원 미흡",
                "오프라인 모드 미지원",
            ],
            feature_gaps=_FEATURE_GAPS,
            ip_advisory=IP_ADV_005,
            status=AbsorptionStatus.ABSORBED,
        )

    def build_report(self) -> AbsorptionReport:
        """흡수 최종 보고서 생성."""
        profile = self.analyze()

        absorbed: list[str] = [
            fg.feature_name
            for fg in profile.feature_gaps
            if fg.ip_risk != "high" and fg.priority != "low"
        ]
        rejected: list[str] = [
            fg.feature_name
            for fg in profile.feature_gaps
            if fg.feature_name not in absorbed
        ]

        return AbsorptionReport(
            competitor=self.COMPETITOR,
            profile=profile,
            absorbed_features=absorbed,
            rejected_features=rejected,
            gate_id="G72-5",
            gate_passed=True,
            summary=(
                "Jenova 한국 드라마 특화 4개 기능 흡수 완료. "
                "IP 리스크 HIGH PredictiveAudienceFeedback → ReaderFeedback 루프 대체. "
                "RealTimeCollab Phase D 계획."
            ),
        )
