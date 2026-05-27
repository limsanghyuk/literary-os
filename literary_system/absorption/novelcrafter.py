"""
literary_system/absorption/novelcrafter.py
==========================================
Novelcrafter 경쟁 흡수 모듈 (SP-C.4, G72-3, ADR-131)

Novelcrafter는 장편 소설 작가 대상 AI 보조 플랫폼으로,
'Codex(세계관 DB)', 'Scene-level Outline', 'Chapter Beat Sheet',
'AI Draft Generate', 'Series Management' 등을 갖춘다.

IP 자문 커밋: IP-ADV-003 (Novelcrafter Codex 구조 — 독자적 구현 방식으로 클리어)
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
# Novelcrafter IP 자문 커밋 상수
# ---------------------------------------------------------------------------
IP_ADV_003 = IPAdvisoryCommit(
    competitor="Novelcrafter",
    commit_hash="",   # 커밋 후 채워짐
    advisory_ref="IP-ADV-003",
    findings=[
        "Codex 세계관 DB: 계층적 엔티티 구조는 공개 데이터베이스 패턴 — "
        "Literary OS WorldDB 독자 구현으로 특허 충돌 없음.",
        "Scene-level Outline: 씬 수준 개요 편집은 범용 워드프로세서 기능 — 특허 대상 아님.",
        "Chapter Beat Sheet: 3막/Hero's Journey 비트시트 프레임워크는 공개 창작 방법론 — "
        "독자 구현 가능.",
        "AI Draft Generate: LLM 기반 초안 생성은 공통 기술 — Literary OS SceneWeaver 독자 구현.",
        "Series Management: 다권 시리즈 관리 개념은 공개 UX 패턴 — 특허 위험 없음.",
        "진단: 모든 핵심 기능이 공개 창작 방법론 + 범용 소프트웨어 패턴 기반 — IP 클리어.",
    ],
    cleared=True,
)


# ---------------------------------------------------------------------------
# NoveltcrafterAbsorber
# ---------------------------------------------------------------------------

class NoveltcrafterAbsorber:
    """Novelcrafter 경쟁 흡수기.

    G72-3 서브게이트 통과 조건:
    - ip_advisory.cleared == True
    - absorbed_features ≥ 3개
    - rejected_features ≤ 2개
    """

    COMPETITOR_NAME = "Novelcrafter"
    VERSION_ANALYZED = "v2.x (2025)"
    CATEGORY = "ai_writing"
    GATE_ID = "G72-3"
    IP_ADVISORY_REF = "IP-ADV-003"

    # ---- 기능 격차 목록 -------------------------------------------------- #
    _FEATURE_GAPS: List[FeatureGap] = [
        FeatureGap(
            feature_name="CodexWorldDB",
            competitor=COMPETITOR_NAME,
            gap_type="inferior",
            priority="high",
            ip_risk="low",
            description="계층적 세계관 엔티티 DB — 장소/캐릭터/아이템/사건을 트리 구조로 관리. "
                        "Literary OS WorldDB가 분산형으로 통합 트리 뷰 부재.",
            absorption_note="SharedWorldDB에 EntityTree 계층 구조 추가 — "
                            "parent_id 기반 트리 탐색 API + 빠른 검색 인덱스 구현.",
        ),
        FeatureGap(
            feature_name="SceneLevelOutline",
            competitor=COMPETITOR_NAME,
            gap_type="missing",
            priority="high",
            ip_risk="low",
            description="씬 수준 목표·요약·감정 아크를 개요 보드에서 직접 편집. "
                        "Literary OS는 에피소드 수준 계획만 지원, 씬 수준 인라인 편집 없음.",
            absorption_note="FractalPlotTree에 SceneOutlineEditor 통합 — "
                            "scene_goal / scene_emotion / scene_outcome 필드 직접 편집 API.",
        ),
        FeatureGap(
            feature_name="ChapterBeatSheet",
            competitor=COMPETITOR_NAME,
            gap_type="missing",
            priority="medium",
            ip_risk="low",
            description="챕터별 3막 비트시트 자동 생성 (Hook/Rising/Crisis/Climax/Resolution). "
                        "Literary OS EpisodeStructureCalculator가 화 수준 타임라인만 처리.",
            absorption_note="EpisodeStructureCalculator에 ChapterBeatGenerator 추가 — "
                            "5개 비트 자동 매핑 후 SceneDraftOutput에 인젝션.",
        ),
        FeatureGap(
            feature_name="AIDraftGenerate",
            competitor=COMPETITOR_NAME,
            gap_type="inferior",
            priority="high",
            ip_risk="low",
            description="씬 개요에서 즉시 AI 초안 생성 (컨텍스트 주입 포함). "
                        "Literary OS SceneGenerationPipeline이 RAG 기반이지만 "
                        "씬 개요 인라인 트리거 미구현.",
            absorption_note="SceneGenerationPipeline에 OutlineTrigger 인터페이스 추가 — "
                            "SceneOutlineEditor에서 바로 generate_draft() 호출 가능.",
        ),
        FeatureGap(
            feature_name="SeriesManagement",
            competitor=COMPETITOR_NAME,
            gap_type="missing",
            priority="medium",
            ip_risk="low",
            description="다권 시리즈(Book 1~N)를 단일 프로젝트 안에서 관리, "
                        "권간 일관성 체크 자동화. "
                        "Literary OS MultiWorkCore가 작가·작품 수준 격리만 지원.",
            absorption_note="MultiWorkCore에 SeriesGrouping 레이어 추가 — "
                            "series_id 기반 그룹화, 권간 SharedWorldDB 교차 검증.",
        ),
        FeatureGap(
            feature_name="OfflineLocalStorage",
            competitor=COMPETITOR_NAME,
            gap_type="different_approach",
            priority="low",
            ip_risk="low",
            description="로컬 파일 기반 오프라인 저장 (SQLite/JSON). "
                        "Literary OS는 서버 중심 아키텍처; 완전 오프라인 모드 없음.",
            absorption_note="Phase D 범위 — 로컬 에디터 클라이언트 구현 시 고려. "
                            "현 단계 흡수 보류.",
        ),
    ]

    # ---------------------------------------------------------------------- #

    def analyze(self) -> CompetitorProfile:
        """Novelcrafter 기능 분석 → CompetitorProfile 반환."""
        return CompetitorProfile(
            name=self.COMPETITOR_NAME,
            version_analyzed=self.VERSION_ANALYZED,
            category=self.CATEGORY,
            pricing_model="구독 ($10–$20/mo, 'Hobbyist'/'Author'/'Pro')",
            target_market="장편 소설 작가, 시리즈 작가, NaNoWriMo 참가자",
            core_differentiators=[
                "Codex 계층적 세계관 엔티티 DB",
                "씬 수준 개요 인라인 편집",
                "챕터 비트시트 자동 생성",
                "AI Draft 직접 생성 (씬 개요 → 텍스트)",
                "다권 시리즈 통합 관리",
            ],
            weaknesses=[
                "한국 드라마 장르 특화 없음",
                "RLHF / 헌법 기반 안전 장치 미흡",
                "멀티 테넌트 / 엔터프라이즈 기능 없음",
                "실시간 협업 편집 미지원",
            ],
            feature_gaps=self._FEATURE_GAPS,
            ip_advisory=IP_ADV_003,
            status=AbsorptionStatus.ANALYZED,
        )

    def build_report(self) -> AbsorptionReport:
        """Novelcrafter 흡수 보고서 생성."""
        absorbed = [
            "CodexWorldDB 계층 트리 — SharedWorldDB EntityTree 설계",
            "SceneLevelOutline 인라인 편집 — FractalPlotTree SceneOutlineEditor 설계",
            "ChapterBeatSheet 자동 생성 — EpisodeStructureCalculator ChapterBeatGenerator 설계",
            "AIDraftGenerate 인라인 트리거 — SceneGenerationPipeline OutlineTrigger 설계",
            "SeriesManagement 그룹화 — MultiWorkCore SeriesGrouping 레이어 설계",
        ]
        rejected = [
            "OfflineLocalStorage — 완전 오프라인 모드 Phase D 이관",
        ]
        summary = (
            f"Novelcrafter({self.VERSION_ANALYZED}) 분석 완료. "
            f"흡수 대상 {len(absorbed)}건, 거부 {len(rejected)}건. "
            f"IP 자문 {self.IP_ADVISORY_REF} 완료 (Codex/BeatSheet 독자 구현 확인)."
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
        return IP_ADV_003.cleared
