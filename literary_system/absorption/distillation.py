"""
absorption/distillation.py — 경쟁 흡수 증류 파이프라인 (SP-C.4, ADR-134)

G72 전체 흡수 결과를 Literary OS 내부 기능 명세로 증류(Distillation)하여
실행 가능한 Feature 로드맵으로 변환한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional


class DistillationPhase(str, Enum):
    IMMEDIATE = "immediate"   # 현재 스프린트 내 구현
    NEXT      = "next"        # 다음 서브페이즈 (V673~)
    DEFERRED  = "deferred"    # Phase D 이후


@dataclass
class DistilledFeature:
    """흡수 기능에서 증류된 Literary OS 내부 Feature 명세."""
    feature_id: str                 # 예: "DF-001"
    source_competitor: str
    source_feature: str
    internal_module: str            # 매핑 대상 내부 모듈/클래스
    distillation_phase: DistillationPhase
    rationale: str = ""
    implementation_hint: str = ""


@dataclass
class DistillationReport:
    """전체 증류 결과 보고서."""
    source_gate: str = "G72"
    distilled_features: List[DistilledFeature] = field(default_factory=list)
    deferred_count: int = 0
    immediate_count: int = 0
    next_count: int = 0
    export_ready: bool = False

    def to_dict(self) -> Dict:
        return {
            "source_gate": self.source_gate,
            "total": len(self.distilled_features),
            "immediate": self.immediate_count,
            "next": self.next_count,
            "deferred": self.deferred_count,
            "export_ready": self.export_ready,
            "features": [
                {
                    "id": f.feature_id,
                    "competitor": f.source_competitor,
                    "source": f.source_feature,
                    "module": f.internal_module,
                    "phase": f.distillation_phase.value,
                }
                for f in self.distilled_features
            ],
        }


# ── 증류 정의 ─────────────────────────────────────────────────────────────────
_DISTILLED_FEATURES: List[DistilledFeature] = [
    # NovelAI (G72-1)
    DistilledFeature("DF-001", "NovelAI",      "StoryBible",               "literary_system.nkg.graph_store",            DistillationPhase.IMMEDIATE, "NKG 확장으로 스토리 바이블 노드 추가"),
    DistilledFeature("DF-002", "NovelAI",      "ProseStyleSelector",       "literary_system.prose.style_dna",            DistillationPhase.IMMEDIATE, "StyleDNA에 장르별 프리셋 추가"),
    DistilledFeature("DF-003", "NovelAI",      "ModuleBasedPlotBuilder",   "literary_system.episode.episode_planner",    DistillationPhase.IMMEDIATE, "EpisodePlanner 모듈 기반 플롯 빌더 확장"),
    DistilledFeature("DF-004", "NovelAI",      "MemoryTokenOptimizer",     "literary_system.rag.semantic_cache_layer",   DistillationPhase.NEXT,      "SemanticCacheLayer TTL 최적화"),
    # Sudowrite (G72-2)
    DistilledFeature("DF-005", "Sudowrite",    "StoryBibleEnhanced",       "literary_system.nkg.graph_store",            DistillationPhase.IMMEDIATE, "스토리 바이블 강화 레이어"),
    DistilledFeature("DF-006", "Sudowrite",    "WormholeRewrite",          "literary_system.prose.prose_rewriter",       DistillationPhase.IMMEDIATE, "문맥 보존 재작성 엔진"),
    DistilledFeature("DF-007", "Sudowrite",    "DescribeSensoryExpansion", "literary_system.prose.sensory_expander",     DistillationPhase.IMMEDIATE, "오감 묘사 확장기"),
    DistilledFeature("DF-008", "Sudowrite",    "CanvasPlotVisualizer",     "literary_system.narrative.narrative_graph",  DistillationPhase.NEXT,      "플롯 시각화 NarrativeGraph 확장"),
    # Novelcrafter (G72-3)
    DistilledFeature("DF-009", "Novelcrafter", "CodexWorldDB",             "literary_system.shared_world_db_v2",         DistillationPhase.IMMEDIATE, "SharedWorldDB v2 코덱스 확장"),
    DistilledFeature("DF-010", "Novelcrafter", "SceneLevelOutline",        "literary_system.episode.episode_planner",    DistillationPhase.IMMEDIATE, "씬 단위 아웃라인 생성"),
    DistilledFeature("DF-011", "Novelcrafter", "ChapterBeatSheet",         "literary_system.episode.episode_planner",    DistillationPhase.IMMEDIATE, "챕터 비트 시트"),
    DistilledFeature("DF-012", "Novelcrafter", "AIDraftGenerate",          "literary_system.generation.scene_gen",       DistillationPhase.IMMEDIATE, "AI 드래프트 생성 파이프라인 통합"),
    DistilledFeature("DF-013", "Novelcrafter", "SeriesManagement",         "literary_system.multi_work.multi_work_core", DistillationPhase.NEXT,      "MultiWorkCore 시리즈 관리 확장"),
    # NolanAI (G72-4)
    DistilledFeature("DF-014", "NolanAI",      "ScriptFormatEngine",       "literary_system.prose.script_formatter",     DistillationPhase.IMMEDIATE, "한국 드라마 스크립트 포맷 엔진"),
    DistilledFeature("DF-015", "NolanAI",      "SceneHeadingAutocomplete", "literary_system.prose.script_formatter",     DistillationPhase.IMMEDIATE, "씬 헤딩 자동완성"),
    DistilledFeature("DF-016", "NolanAI",      "CharacterVoiceConsistency","literary_system.shared_character_db_v2",     DistillationPhase.IMMEDIATE, "캐릭터 목소리 일관성 검증"),
    DistilledFeature("DF-017", "NolanAI",      "BeatBoardVisualization",   "literary_system.narrative.narrative_graph",  DistillationPhase.NEXT,      "비트 보드 시각화 Phase D"),
    DistilledFeature("DF-018", "NolanAI",      "ProductionBreakdown",      "literary_system.prose.production_breakdown", DistillationPhase.IMMEDIATE, "제작 분해 모듈"),
    # Jenova (G72-5)
    DistilledFeature("DF-019", "Jenova",       "KoreanGenreBlending",      "literary_system.genre_transfer",             DistillationPhase.IMMEDIATE, "GenreTransferEngine 멀티장르 혼합"),
    DistilledFeature("DF-020", "Jenova",       "EmotionalPeakScheduler",   "literary_system.narrative.tension_curve",    DistillationPhase.IMMEDIATE, "NarrativeTensionCurve 피크 스케줄러"),
    DistilledFeature("DF-021", "Jenova",       "NarrativeCoherenceValidator","literary_system.asd.arc_consistency",      DistillationPhase.IMMEDIATE, "ArcConsistencyChecker 확장"),
    DistilledFeature("DF-022", "Jenova",       "CharacterRelationshipMapper","literary_system.shared_character_db_v2",   DistillationPhase.NEXT,      "SharedCharacterDB v2 관계 레이어"),
]


class DistillationExportPipeline:
    """G72 전체 흡수 결과 증류 파이프라인."""

    def __init__(self, features: Optional[List[DistilledFeature]] = None):
        self._features = features if features is not None else _DISTILLED_FEATURES

    def run(self) -> DistillationReport:
        """증류 실행 — 22개 absorbed feature → DistilledFeature 목록 생성."""
        immediate = [f for f in self._features if f.distillation_phase == DistillationPhase.IMMEDIATE]
        next_phase = [f for f in self._features if f.distillation_phase == DistillationPhase.NEXT]
        deferred   = [f for f in self._features if f.distillation_phase == DistillationPhase.DEFERRED]

        return DistillationReport(
            source_gate="G72",
            distilled_features=list(self._features),
            immediate_count=len(immediate),
            next_count=len(next_phase),
            deferred_count=len(deferred),
            export_ready=True,
        )

    def export_roadmap(self) -> List[Dict]:
        """IMMEDIATE 우선순위로 정렬된 실행 가능 로드맵 반환."""
        report = self.run()
        phase_order = {
            DistillationPhase.IMMEDIATE: 0,
            DistillationPhase.NEXT: 1,
            DistillationPhase.DEFERRED: 2,
        }
        sorted_features = sorted(
            report.distilled_features,
            key=lambda f: phase_order[f.distillation_phase],
        )
        return [
            {
                "id": f.feature_id,
                "competitor": f.source_competitor,
                "feature": f.source_feature,
                "module": f.internal_module,
                "phase": f.distillation_phase.value,
                "rationale": f.rationale,
            }
            for f in sorted_features
        ]
