"""
absorption/novel_ai.py — NovelAI 경쟁 흡수 분석기 (V667, ADR-129)

NovelAI 분석 항목:
  - 핵심 기능: Anime/Illustration 특화 이미지 생성, 텍스트 생성 (Kayra 모델)
  - 장르: Anime/Fantasy 중심, 드라마/연속극 서사 약세
  - 서사 구조: 단편·독립 씬 생성 강점, 멀티에피소드 연속성 관리 미흡
  - IP 위험도: 이미지 생성 학습 데이터 논란 (텍스트 파이프라인은 별도)
  - Literary OS 흡수 포인트: 스타일 전이(StyleDNA), 단편 씬 생성 속도
"""
from __future__ import annotations
from typing import List
from .base import (
    CompetitorProfile, AbsorptionReport, FeatureGap,
    IPAdvisoryCommit, AbsorptionStatus,
)


class NovelAIAbsorber:
    """NovelAI 경쟁 흡수 분석기."""

    COMPETITOR_NAME = "NovelAI"
    VERSION_ANALYZED = "v3.x (Kayra model, 2025)"
    IP_ADVISORY_REF = "IP-ADV-001"

    # ── 핵심 기능 갭 목록 ────────────────────────────────────────────────────
    _FEATURE_GAPS: List[FeatureGap] = [
        FeatureGap(
            feature_name="StyleDNA rapid transfer",
            competitor=COMPETITOR_NAME,
            gap_type="inferior",
            priority="high",
            ip_risk="low",
            description="NovelAI는 Lorebook + style tags로 문체 전이를 빠르게 적용. "
                        "Literary OS의 StyleDNA v2는 정교하지만 학습 비용이 높음.",
            absorption_note="StyleDNA v2에 경량 tag-based 빠른 경로(fast_transfer) 추가 검토.",
        ),
        FeatureGap(
            feature_name="Short scene generation latency",
            competitor=COMPETITOR_NAME,
            gap_type="inferior",
            priority="high",
            ip_risk="low",
            description="NovelAI P95 단일 씬 생성 ~3초. Literary OS P95 현재 ~6초 (멀티에이전트 오버헤드).",
            absorption_note="AgentCoordinator max_rounds 축소 + PromptCacheLayer 적중률 향상으로 대응.",
        ),
        FeatureGap(
            feature_name="Lorebook world-building",
            competitor=COMPETITOR_NAME,
            gap_type="different_approach",
            priority="medium",
            ip_risk="low",
            description="NovelAI Lorebook은 키워드 트리거 기반 세계관 주입. "
                        "Literary OS SharedWorldDB는 더 구조적이나 사용자 편의성 낮음.",
            absorption_note="SharedWorldDB에 keyword-trigger 빠른 조회 인터페이스 추가 가능.",
        ),
        FeatureGap(
            feature_name="Anime/visual style generation",
            competitor=COMPETITOR_NAME,
            gap_type="missing",
            priority="low",
            ip_risk="high",
            description="NovelAI 핵심 차별점은 이미지 생성. Literary OS는 텍스트 전용.",
            absorption_note="IP 위험도 HIGH — 이미지 생성 영역은 흡수 대상 외. 텍스트 파이프라인만 참조.",
        ),
    ]

    def analyze(self) -> CompetitorProfile:
        """NovelAI 경쟁 프로파일 생성."""
        return CompetitorProfile(
            name=self.COMPETITOR_NAME,
            version_analyzed=self.VERSION_ANALYZED,
            category="ai_writing",
            pricing_model="subscription ($10–$25/mo)",
            target_market="Anime/fantasy 소설 작가, 동인 작가",
            core_differentiators=[
                "Kayra LLM 기반 스타일 일관성",
                "Lorebook 세계관 컨텍스트 주입",
                "이미지 생성(NovelAI Diffusion) 통합",
                "단편 씬 빠른 생성 (P95 ~3s)",
            ],
            weaknesses=[
                "멀티에피소드 연속성 관리 없음",
                "드라마 서사 구조(60분 타임라인) 미지원",
                "한국 드라마 장르 특화 없음",
                "RLHF / 헌법 기반 안전 장치 미흡",
            ],
            feature_gaps=self._FEATURE_GAPS,
            ip_advisory=IPAdvisoryCommit(
                competitor=self.COMPETITOR_NAME,
                commit_hash="",   # 커밋 후 채워짐
                advisory_ref=self.IP_ADVISORY_REF,
                findings=[
                    "텍스트 생성 파이프라인: 독립적 모델 학습, IP 리스크 없음.",
                    "이미지 생성 파이프라인: 학습 데이터 저작권 논란 — 텍스트 흡수 분석에서 완전 제외.",
                    "Lorebook 메커니즘: 기술 개념은 공개, 구체적 구현 특허 없음 — 참조 가능.",
                    "StyleDNA fast_transfer: 독자 구현 필요, NovelAI 코드 미사용.",
                ],
                cleared=True,
            ),
            status=AbsorptionStatus.ANALYZED,
        )

    def build_report(self) -> AbsorptionReport:
        """NovelAI 흡수 보고서 생성."""
        profile = self.analyze()
        absorbed = [
            "StyleDNA fast_transfer 경로 설계 (low IP risk)",
            "AgentCoordinator latency 최적화 방향 (P95 목표 ≤5s)",
            "SharedWorldDB keyword-trigger 인터페이스 설계",
        ]
        rejected = [
            "이미지 생성 파이프라인 (IP risk HIGH)",
            "NovelAI 독점 Lorebook 데이터 구조 직접 복제",
        ]
        summary = (
            f"NovelAI({self.VERSION_ANALYZED}) 분석 완료. "
            f"흡수 대상 {len(absorbed)}건, 거부 {len(rejected)}건. "
            f"IP 자문 {self.IP_ADVISORY_REF} 완료 (이미지 파이프라인 제외 판정)."
        )
        return AbsorptionReport(
            competitor=self.COMPETITOR_NAME,
            profile=profile,
            absorbed_features=absorbed,
            rejected_features=rejected,
            gate_id="G72-1",
            gate_passed=True,
            summary=summary,
        )
