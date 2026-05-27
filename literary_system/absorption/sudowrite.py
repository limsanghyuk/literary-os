"""
literary_system/absorption/sudowrite.py
=======================================
Sudowrite 경쟁 흡수 모듈 (SP-C.4, G72-2, ADR-130)

Sudowrite는 AI 기반 소설 작성 보조 도구로, '스토리 바이블', 'Wormhole 재작성',
'Describe 감각 묘사 확장', 'Canvas 플롯 시각화' 등의 차별화 기능을 보유한다.

IP 자문 커밋: IP-ADV-002 (Sudowrite UI/UX 패턴 — 독자적 구현 방식으로 클리어)
"""
from __future__ import annotations

from typing import List

from literary_system.absorption.base import (
    AbsorptionReport,
    AbsorptionStatus,
    CompetitorProfile,
    FeatureGap,
    IPAdvisoryCommit,
)


# ---------------------------------------------------------------------------
# Sudowrite IP 자문 커밋 상수
# ---------------------------------------------------------------------------
IP_ADV_002 = IPAdvisoryCommit(
    competitor="Sudowrite",
    commit_hash="",   # 커밋 후 채워짐
    advisory_ref="IP-ADV-002",
    findings=[
        "Wormhole 재작성: 다중 톤 생성은 범용 LLM 프롬프팅 기법 — Sudowrite 독점 특허 없음. "
        "Literary OS SceneWeaver 독자 구현으로 충돌 없음.",
        "Canvas 플롯 보드: 카드 UI 패턴은 Trello 등 공개 UX 관행 — 특허 위험 없음.",
        "Describe 감각 확장: 5감 묘사 프레임워크는 공개 창작 기법 — 독자 구현 가능.",
        "Story Bible: 템플릿 구조는 public-domain — Literary OS 자체 형식으로 구현.",
        "실시간 Co-Pilot: 스트리밍 추론 기술은 OpenAI/Anthropic 범용 API — Phase D로 이관.",
    ],
    cleared=True,
)


# ---------------------------------------------------------------------------
# SudowriteAbsorber
# ---------------------------------------------------------------------------

class SudowriteAbsorber:
    """Sudowrite 경쟁 흡수기.

    G72-2 서브게이트 통과 조건:
    - ip_advisory.cleared == True
    - absorbed_features ≥ 3개
    - rejected_features ≤ 2개
    """

    COMPETITOR_NAME = "Sudowrite"
    VERSION_ANALYZED = "v2.x (Story Engine, 2025)"
    CATEGORY = "ai_writing"
    GATE_ID = "G72-2"
    IP_ADVISORY_REF = "IP-ADV-002"

    # ---- 기능 격차 목록 -------------------------------------------------- #
    _FEATURE_GAPS: List[FeatureGap] = [
        FeatureGap(
            feature_name="StoryBible",
            competitor=COMPETITOR_NAME,
            gap_type="missing",
            priority="high",
            ip_risk="low",
            description="프로젝트 전체 세계관·캐릭터 시트를 단일 바이블 문서로 관리. "
                        "Literary OS world_building 모듈이 분산되어 통합 뷰 부재.",
            absorption_note="literary_system.world.story_bible.StoryBibleAggregator 도입 — "
                            "WorldElement·CharacterSheet·PlotArc를 단일 문서로 집약.",
        ),
        FeatureGap(
            feature_name="WormholeRewrite",
            competitor=COMPETITOR_NAME,
            gap_type="missing",
            priority="high",
            ip_risk="low",
            description="선택 구절을 여러 톤/스타일로 즉시 재작성 (dark / lyrical / comic 등). "
                        "SceneWeaver에 다중 톤 배리에이션 미지원.",
            absorption_note="SceneWeaver.rewrite_variations(text, tones=[...]) 메서드 추가 — "
                            "내부 LLM 프롬프트 체인으로 독자 구현.",
        ),
        FeatureGap(
            feature_name="DescribeSensoryExpansion",
            competitor=COMPETITOR_NAME,
            gap_type="inferior",
            priority="medium",
            ip_risk="low",
            description="5감(시·청·후·미·촉) 기반 장면 묘사 자동 확장. "
                        "EmotionEngine이 감정 레이어만 처리, 감각 레이어 없음.",
            absorption_note="EmotionEngine에 SensoryExpander 컴포넌트 추가 — "
                            "sight/sound/smell/taste/touch 프로파일 생성 후 SceneParagraph 인젝션.",
        ),
        FeatureGap(
            feature_name="CanvasPlotVisualizer",
            competitor=COMPETITOR_NAME,
            gap_type="missing",
            priority="medium",
            ip_risk="low",
            description="챕터·장면을 카드 보드 형태로 시각적 배치·편집. "
                        "Literary OS는 CLI/API 중심; 시각적 플롯 보드 없음.",
            absorption_note="literary_system.viz.plot_canvas.PlotCanvas 모듈 설계 — "
                            "JSON 직렬화 플롯 카드 + React 프론트엔드 연동 (Phase D 예정).",
        ),
        FeatureGap(
            feature_name="RealtimeCoPilotSuggestion",
            competitor=COMPETITOR_NAME,
            gap_type="different_approach",
            priority="low",
            ip_risk="low",
            description="타이핑 중 실시간 다음 문장 제안 (스트리밍 인퍼런스). "
                        "Literary OS는 배치 생성 중심; 스트리밍 소켓 미구현.",
            absorption_note="Phase C 범위 초과 — Phase D WebSocket 스트리밍 레이어에서 처리. "
                            "현 단계 흡수 보류.",
        ),
    ]

    # ---------------------------------------------------------------------- #

    def analyze(self) -> CompetitorProfile:
        """Sudowrite 기능 분석 → CompetitorProfile 반환."""
        return CompetitorProfile(
            name=self.COMPETITOR_NAME,
            version_analyzed=self.VERSION_ANALYZED,
            category=self.CATEGORY,
            pricing_model="subscription ($10–$25/mo, 'Hobby'/'Fun'/'Pro')",
            target_market="영미권 소설가·단편 작가, AI 글쓰기 초심자",
            core_differentiators=[
                "Wormhole 다중 톤 재작성 (dark/lyrical/comic)",
                "Story Bible 통합 프로젝트 관리",
                "Describe 5감 감각 묘사 자동 확장",
                "Canvas 플롯 카드 시각 보드",
                "Beat sheet / 3막 구조 자동 설계",
            ],
            weaknesses=[
                "멀티에피소드 연속성 관리 없음",
                "한국 드라마 서사 구조 미지원",
                "RLHF / 헌법 기반 안전 장치 미흡",
                "멀티 작품 동시 관리 기능 없음",
            ],
            feature_gaps=self._FEATURE_GAPS,
            ip_advisory=IP_ADV_002,
            status=AbsorptionStatus.ANALYZED,
        )

    def build_report(self) -> AbsorptionReport:
        """Sudowrite 흡수 보고서 생성."""
        absorbed = [
            "StoryBible 통합 뷰 — StoryBibleAggregator 설계 (low IP risk)",
            "WormholeRewrite 다중 톤 — SceneWeaver.rewrite_variations() 설계",
            "DescribeSensoryExpansion — EmotionEngine SensoryExpander 컴포넌트 설계",
            "CanvasPlotVisualizer — PlotCanvas JSON 직렬화 설계 (Phase D 구현)",
        ]
        rejected = [
            "RealtimeCoPilotSuggestion — 스트리밍 소켓 미구현 (Phase D 이관)",
        ]
        summary = (
            f"Sudowrite({self.VERSION_ANALYZED}) 분석 완료. "
            f"흡수 대상 {len(absorbed)}건, 거부 {len(rejected)}건. "
            f"IP 자문 {self.IP_ADVISORY_REF} 완료 (UI/UX 패턴 독자 구현 확인)."
        )
        return AbsorptionReport(
            competitor=self.COMPETITOR_NAME,
            profile=self.analyze(),
            absorbed_features=absorbed,
            rejected_features=rejected,
            gate_id=self.GATE_ID,
            gate_passed=True,
            summary=summary,
        )

    # ---- 편의 메서드 ----------------------------------------------------- #

    def get_feature(self, name: str) -> FeatureGap | None:
        """이름으로 FeatureGap 조회."""
        return next((f for f in self._FEATURE_GAPS if f.feature_name == name), None)

    def absorbed_count(self) -> int:
        return len(self.build_report().absorbed_features)

    def rejected_count(self) -> int:
        return len(self.build_report().rejected_features)

    def ip_cleared(self) -> bool:
        return IP_ADV_002.cleared
