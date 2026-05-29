"""
V324 - SceneMetricsCollector  (Phase 2)
씬 실행 결과에서 MAEOrchestrator가 소비하는 객관적 메트릭을 수집.

설계 원칙 (P3 LLM 0회, Gemini MAE 자기참조 결함 해결):
  - 에이전트 가중치에 의존하지 않는 독립적 측정값만 포함
  - DRSEScorer, SpatialConstraintGate, CharacterStateGate, ReaderSimulator 출력에서 파생
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

try:
    from literary_system.trajectory.reader_simulator import ReaderSimulator
    _READER_SIM_AVAILABLE = True
except ImportError:
    _READER_SIM_AVAILABLE = False


@dataclass
class SceneMetrics:
    """씬 품질 메트릭 — MAEOrchestrator 3에이전트의 공통 입력."""
    scene_id: str
    drse_gate_pass_rate: float        # 0.0~1.0 (DRSE AbsoluteGate PASS 비율)
    spatial_violation_count: int      # SpatialConstraintGate 위반 수
    character_state_valid: bool       # CharacterStateGate 검사 통과 여부
    reader_pull: float                # ReaderSimulator.reader_pull
    reader_afterimage: float          # ReaderSimulator.reader_afterimage
    reader_uncertainty: float         # ReaderSimulator.reader_uncertainty
    reader_composite_score: float     # (pull + afterimage - uncertainty) / 3
    relation_consistency: float       # 1 - (모순 엣지 / 전체 엣지)

    @classmethod
    def compute(
        cls,
        scene_id: str,
        drse_gate_pass_rate: float = 1.0,
        spatial_violation_count: int = 0,
        character_state_valid: bool = True,
        reader_pull: float = 0.5,
        reader_afterimage: float = 0.5,
        reader_uncertainty: float = 0.5,
        relation_consistency: float = 1.0,
    ) -> "SceneMetrics":
        """
        개별 측정값으로부터 SceneMetrics 생성.
        reader_composite_score는 자동 계산.
        """
        composite = (reader_pull + reader_afterimage - reader_uncertainty) / 3.0
        return cls(
            scene_id=scene_id,
            drse_gate_pass_rate=drse_gate_pass_rate,
            spatial_violation_count=spatial_violation_count,
            character_state_valid=character_state_valid,
            reader_pull=reader_pull,
            reader_afterimage=reader_afterimage,
            reader_uncertainty=reader_uncertainty,
            reader_composite_score=composite,
            relation_consistency=relation_consistency,
        )

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "drse_gate_pass_rate": self.drse_gate_pass_rate,
            "spatial_violation_count": self.spatial_violation_count,
            "character_state_valid": self.character_state_valid,
            "reader_pull": self.reader_pull,
            "reader_afterimage": self.reader_afterimage,
            "reader_uncertainty": self.reader_uncertainty,
            "reader_composite_score": self.reader_composite_score,
            "relation_consistency": self.relation_consistency,
        }


class SceneMetricsCollector:
    """
    씬 실행 결과 오브젝트를 받아 SceneMetrics로 변환.

    각 게이트/스코어러의 결과를 집계하여 MAEOrchestrator에 공급.
    내부에서 에이전트 가중치를 참조하지 않는다 (Gemini MAE 결함 방지).
    """

    def collect(self, scene_id: str, text: str = "") -> "SceneMetrics":
        """
        V327 P1-2: SGO._collect_metrics() 호환 편의 메서드.
        텍스트 기반 기본 메트릭을 추출하여 SceneMetrics 반환.
        외부 컴포넌트(DRSE, Spatial 등) 없이도 작동.

        Args:
            scene_id: 씬 식별자
            text:     씬 텍스트 (길이·내용 기반 기본 메트릭 계산)

        Returns:
            SceneMetrics (기본값 기반 — 외부 게이트 연결 없음)
        """
        text_len = len(text)
        # 텍스트 길이 기반 reader_pull 추정 (200~2000자 기준)
        reader_pull = min(1.0, max(0.1, text_len / 2000))
        # 문장 다양성 기반 afterimage 추정
        sentences = [s.strip() for s in text.replace(".", "\n").replace("!", "\n").replace("?", "\n").split("\n") if s.strip()]
        afterimage = min(1.0, max(0.3, len(sentences) / 20))
        uncertainty = max(0.0, 0.5 - reader_pull * 0.2)

        return SceneMetrics.compute(
            scene_id               = scene_id,
            drse_gate_pass_rate    = 1.0,
            spatial_violation_count= 0,
            character_state_valid  = True,
            reader_pull            = reader_pull,
            reader_afterimage      = afterimage,
            reader_uncertainty     = uncertainty,
            relation_consistency   = 1.0,
        )

    def collect_from_components(
        self,
        scene_id: str,
        *,
        drse_result: Any = None,
        spatial_result: Any = None,
        char_result: Any = None,
        reader_est: Any = None,
        rgs: Any = None,
    ) -> SceneMetrics:
        """
        각 컴포넌트 결과에서 메트릭을 추출하여 SceneMetrics 반환.

        Args:
            drse_result:    DRSEScorer 결과 (score, gate_passed 등)
            spatial_result: SpatialConstraintGate 결과 (violations 등)
            char_result:    CharacterStateGate 결과 (passed 등)
            reader_est:     ReaderSimulator.estimate() 결과
            rgs:            RelationGraphStore (일관성 계산용)
        """
        # DRSE gate pass rate
        drse_pass = self._extract_drse_pass(drse_result)

        # Spatial violations
        spatial_v = self._extract_spatial_violations(spatial_result)

        # Character state validity
        char_valid = self._extract_char_valid(char_result)

        # Reader metrics
        pull, afterimage, uncertainty = self._extract_reader(reader_est)

        # Relation consistency
        consistency = self._compute_consistency(rgs)

        return SceneMetrics.compute(
            scene_id=scene_id,
            drse_gate_pass_rate=drse_pass,
            spatial_violation_count=spatial_v,
            character_state_valid=char_valid,
            reader_pull=pull,
            reader_afterimage=afterimage,
            reader_uncertainty=uncertainty,
            relation_consistency=consistency,
        )

    # ── 내부 추출 헬퍼 ────────────────────────────────────────────────

    def _extract_drse_pass(self, drse_result: Any) -> float:
        if drse_result is None:
            return 1.0
        # DRSEResult 객체 또는 dict 지원
        if hasattr(drse_result, "gate_pass_rate"):
            return float(drse_result.gate_pass_rate)
        if isinstance(drse_result, dict):
            return float(drse_result.get("gate_pass_rate", 1.0))
        # score 필드 폴백
        if hasattr(drse_result, "score"):
            s = float(drse_result.score)
            return min(1.0, max(0.0, s))
        return 1.0

    def _extract_spatial_violations(self, spatial_result: Any) -> int:
        if spatial_result is None:
            return 0
        if hasattr(spatial_result, "violations"):
            return len(spatial_result.violations)
        if isinstance(spatial_result, dict):
            return int(spatial_result.get("violation_count", 0))
        return 0

    def _extract_char_valid(self, char_result: Any) -> bool:
        if char_result is None:
            return True
        if hasattr(char_result, "passed"):
            return bool(char_result.passed)
        if isinstance(char_result, dict):
            return bool(char_result.get("passed", True))
        return True

    def _extract_reader(self, reader_est: Any) -> tuple[float, float, float]:
        if reader_est is None:
            return 0.5, 0.5, 0.5
        pull = float(getattr(reader_est, "reader_pull", 0.5))
        afterimage = float(getattr(reader_est, "reader_afterimage", 0.5))
        uncertainty = float(getattr(reader_est, "reader_uncertainty", 0.5))
        return pull, afterimage, uncertainty

    def _compute_consistency(self, rgs: Any) -> float:
        """RelationGraphStore에서 관계 일관성 계산. RGS 없으면 1.0."""
        if rgs is None:
            return 1.0
        try:
            # NetworkX DiGraph 기반 RGS
            g = rgs._graph if hasattr(rgs, "_graph") else None
            if g is None:
                return 1.0
            total_edges = g.number_of_edges()
            if total_edges == 0:
                return 1.0
            # 모순 엣지: relation_type="CONTRADICTION" 또는 weight < 0
            contradiction = sum(
                1 for _, _, d in g.edges(data=True)
                if d.get("relation_type") == "CONTRADICTION" or d.get("weight", 0) < 0
            )
            return 1.0 - (contradiction / total_edges)
        except Exception:
            return 1.0

    def collect_batch(
        self,
        scene_texts: Dict[str, str],
        literary_state_before: Optional[Dict[str, float]] = None,
    ) -> Dict[str, "SceneMetrics"]:
        """
        V556: 복수 씬 일괄 수집 — ReaderSimulator.estimate_batch() 직접 사용.

        Parameters
        ----------
        scene_texts : {scene_id: text}
        literary_state_before : 이전 문학 상태 (선택)

        Returns
        -------
        {scene_id: SceneMetrics}
        """
        if not scene_texts:
            return {}

        if _READER_SIM_AVAILABLE:
            sim = ReaderSimulator()
            estimates = sim.estimate_batch(scene_texts, literary_state_before)
            return {
                sid: SceneMetrics.compute(
                    scene_id=sid,
                    reader_pull=est.reader_pull,
                    reader_afterimage=est.reader_afterimage,
                    reader_uncertainty=est.reader_uncertainty,
                )
                for sid, est in estimates.items()
            }
        # fallback: 개별 collect
        return {sid: self.collect(sid, text) for sid, text in scene_texts.items()}

