"""
literary_system/absorption/nolan_ai.py
=======================================
NolanAI 경쟁 흡수 모듈 (SP-C.4, G72-4, ADR-132)

NolanAI는 영화·TV 대본(screenplay) 전문 AI 작성 도구로,
'Final Draft 호환 포맷', 'Scene Heading 자동완성', 'Character Voice Consistency',
'Beat Board 시각화', 'Production Breakdown' 등의 차별 기능을 보유한다.

Literary OS가 한국 드라마(방송 대본) 생성 영역에서 직접 경쟁하는 플레이어이므로
대본 포맷 및 씬 헤더 자동화 기능이 특히 흡수 가치가 높다.

IP 자문 커밋: IP-ADV-004 (NolanAI 대본 포맷 특허 — 독립 구현으로 클리어)
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
# NolanAI IP 자문 커밋 상수
# ---------------------------------------------------------------------------
IP_ADV_004 = IPAdvisoryCommit(
    competitor="NolanAI",
    commit_hash="",   # 커밋 후 채워짐
    advisory_ref="IP-ADV-004",
    findings=[
        "Final Draft 호환 포맷(.fdx): 파일 포맷 스펙은 Final Draft Inc. 소유이나 "
        "Literary OS는 자체 KoreanDrama 포맷 사용 — 직접 복제 없음.",
        "Scene Heading 자동완성: INT./EXT. 키워드 감지는 공개 대본 규칙 — 특허 없음. "
        "Literary OS 독자 SceneHeadingParser 구현 가능.",
        "Character Voice Consistency: LLM 기반 대화 스타일 일관성 검사는 범용 기법 — "
        "Literary OS CharacterVoiceChecker 독자 구현.",
        "Beat Board 시각화: 카드 기반 플롯 보드는 공개 UX 패턴 — 위험 없음.",
        "Production Breakdown: 촬영 스케줄·캐스팅 시트 자동 생성은 "
        "공개 제작 관리 방법론 — 특허 없음.",
        "진단: 한국 방송 대본 서식(KBS/MBC/tvN 스타일) 기반 독자 구현 시 전혀 충돌 없음.",
    ],
    cleared=True,
)


# ---------------------------------------------------------------------------
# NolanAIAbsorber
# ---------------------------------------------------------------------------

class NolanAIAbsorber:
    """NolanAI 경쟁 흡수기.

    G72-4 서브게이트 통과 조건:
    - ip_advisory.cleared == True
    - absorbed_features ≥ 3개
    - rejected_features ≤ 2개
    """

    COMPETITOR_NAME = "NolanAI"
    VERSION_ANALYZED = "v1.x (2025)"
    CATEGORY = "ai_writing"
    GATE_ID = "G72-4"
    IP_ADVISORY_REF = "IP-ADV-004"

    # ---- 기능 격차 목록 -------------------------------------------------- #
    _FEATURE_GAPS: List[FeatureGap] = [
        FeatureGap(
            feature_name="ScriptFormatEngine",
            competitor=COMPETITOR_NAME,
            gap_type="missing",
            priority="high",
            ip_risk="low",
            description="Final Draft / Fountain 표준 대본 포맷 자동 적용 "
                        "(INT/EXT 씬 헤딩, 액션라인, 다이얼로그 블록). "
                        "Literary OS SceneWeaver가 산문형 텍스트 생성 중심이며 "
                        "표준 대본 포맷 출력 없음.",
            absorption_note="literary_system.prose.script_formatter.ScriptFormatEngine 신설 — "
                            "KoreanDrama 방송 대본 포맷(KBS/MBC/tvN 스타일) 우선 지원. "
                            "씬헤딩(S#)/지문/대사 블록 자동 렌더링.",
        ),
        FeatureGap(
            feature_name="SceneHeadingAutocomplete",
            competitor=COMPETITOR_NAME,
            gap_type="missing",
            priority="high",
            ip_risk="low",
            description="씬 번호·장소·시간대 자동완성 (S#001 낮/밤, INT/EXT). "
                        "Literary OS FractalPlotTree가 씬 메타데이터를 비정형으로 처리.",
            absorption_note="FractalPlotTree.SceneNode에 structured_heading 필드 추가 — "
                            "scene_number / location / time_of_day 타입 안전 편집.",
        ),
        FeatureGap(
            feature_name="CharacterVoiceConsistency",
            competitor=COMPETITOR_NAME,
            gap_type="inferior",
            priority="high",
            ip_risk="low",
            description="각 캐릭터의 어휘·말투·어조를 추적해 에피소드 간 일관성 검증. "
                        "Literary OS ArcConsistencyChecker가 서사 아크만 검사, "
                        "대사 스타일 레이어 없음.",
            absorption_note="ArcConsistencyChecker에 CharacterVoiceChecker 서브모듈 추가 — "
                            "캐릭터별 어휘 빈도·문장 패턴 임베딩 비교, 이탈 경고.",
        ),
        FeatureGap(
            feature_name="BeatBoardVisualization",
            competitor=COMPETITOR_NAME,
            gap_type="missing",
            priority="medium",
            ip_risk="low",
            description="씬·비트를 드래그 앤 드롭 카드로 시각적 배치·재정렬. "
                        "Literary OS CLI/API 중심; 시각 보드 미구현.",
            absorption_note="Novelcrafter 흡수 CanvasPlotVisualizer와 통합 — "
                            "PlotCanvas에 script_beat 카드 타입 추가 (Phase D 구현).",
        ),
        FeatureGap(
            feature_name="ProductionBreakdown",
            competitor=COMPETITOR_NAME,
            gap_type="missing",
            priority="medium",
            ip_risk="low",
            description="씬 분석으로 캐스팅 시트·소품 목록·촬영 장소 자동 추출. "
                        "Literary OS는 제작 정보 레이어 없음.",
            absorption_note="literary_system.production.breakdown.ProductionBreakdown 신설 — "
                            "SceneDraftOutput에서 캐릭터명·소품·장소 엔티티 추출 후 보고서 생성.",
        ),
        FeatureGap(
            feature_name="FinalDraftExport",
            competitor=COMPETITOR_NAME,
            gap_type="missing",
            priority="low",
            ip_risk="medium",
            description="Final Draft(.fdx) 포맷 직접 내보내기. "
                        "Literary OS ManuscriptExporter가 .txt/.md/.docx만 지원.",
            absorption_note="Final Draft .fdx 포맷은 독점 스펙 — 직접 지원 대신 "
                            "Fountain(.fountain) 오픈 포맷 지원으로 대체. "
                            "ManuscriptExporter에 FountainExporter 추가.",
        ),
    ]

    # ---------------------------------------------------------------------- #

    def analyze(self) -> CompetitorProfile:
        """NolanAI 기능 분석 → CompetitorProfile 반환."""
        return CompetitorProfile(
            name=self.COMPETITOR_NAME,
            version_analyzed=self.VERSION_ANALYZED,
            category=self.CATEGORY,
            pricing_model="구독 ($20–$40/mo, Pro/Studio)",
            target_market="영화 각본가, TV 드라마 작가, 독립 제작사",
            core_differentiators=[
                "표준 대본 포맷(Final Draft/Fountain) 자동 적용",
                "씬 헤딩 자동완성 (INT/EXT + 시간대)",
                "캐릭터 보이스 일관성 추적",
                "비트 보드 드래그 앤 드롭",
                "제작 분석(프로덕션 브레이크다운)",
            ],
            weaknesses=[
                "한국 드라마 방송 대본 포맷 미지원",
                "AI 서사 기억(NKG) 없음",
                "멀티 테넌트 / 엔터프라이즈 기능 없음",
                "RLHF / 헌법 기반 안전 장치 미흡",
            ],
            feature_gaps=self._FEATURE_GAPS,
            ip_advisory=IP_ADV_004,
            status=AbsorptionStatus.ANALYZED,
        )

    def build_report(self) -> AbsorptionReport:
        """NolanAI 흡수 보고서 생성."""
        absorbed = [
            "ScriptFormatEngine — KoreanDrama 방송 대본 포맷 렌더러 설계",
            "SceneHeadingAutocomplete — FractalPlotTree SceneNode structured_heading 설계",
            "CharacterVoiceConsistency — ArcConsistencyChecker CharacterVoiceChecker 설계",
            "BeatBoardVisualization — PlotCanvas script_beat 카드 타입 (Phase D)",
            "ProductionBreakdown — production.breakdown.ProductionBreakdown 설계",
        ]
        rejected = [
            "FinalDraftExport (.fdx) — 독점 포맷 대신 Fountain 오픈 포맷으로 대체",
        ]
        summary = (
            f"NolanAI({self.VERSION_ANALYZED}) 분석 완료. "
            f"흡수 대상 {len(absorbed)}건, 거부 {len(rejected)}건. "
            f"IP 자문 {self.IP_ADVISORY_REF} 완료 (.fdx 대신 Fountain 포맷 채택)."
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
        return next((f for f in self._FEATURE_GAPS if f.feature_name == name), None)

    def absorbed_count(self) -> int:
        return len(self.build_report().absorbed_features)

    def rejected_count(self) -> int:
        return len(self.build_report().rejected_features)

    def ip_cleared(self) -> bool:
        return IP_ADV_004.cleared
