"""
V324 - DRSEGraphAdapter  (Phase 3)
RelationGraphStore DiGraph → DRSEScorer 입력 변환.

설계 원칙 (P2 외과적 통합, P3 LLM 0회):
  - RGS 내부 변경 없이 그래프 데이터 추출
  - compute_relational_density: 캐릭터 집합 간 엣지 밀도 → DRSEScorer.S 항 보정
  - compute_arc_pressure: 아크 내 긴장 엣지 비율 → DRSEScorer.A 항 보정
  - extract_drse_inputs: DRSEInputBundle 생성
  - RGS 없으면 기본값 반환 (방어적)
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, List, Optional


@dataclass
class DRSEInputBundle:
    """DRSEScorer에 전달되는 그래프 기반 보정 계수."""
    scene_id: str
    relational_density: float = 0.5     # 0.0~1.0, S 항 보정
    arc_pressure: float = 0.5           # 0.0~1.0, A 항 보정
    char_ids: List[str] = field(default_factory=list)
    arc_id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "relational_density": self.relational_density,
            "arc_pressure": self.arc_pressure,
            "char_ids": self.char_ids,
            "arc_id": self.arc_id,
        }


class DRSEGraphAdapter:
    """
    RelationGraphStore → DRSEInputBundle 변환기.
    RGS가 없어도 기본값으로 동작 (방어적 설계).
    """

    # 긴장 엣지 유형 목록
    TENSION_TYPES = {"CONFLICT", "RIVAL", "DISTRUST", "FEAR", "TENSION"}

    def extract_drse_inputs(
        self,
        rgs: Any,
        scene_id: str,
        char_ids: Optional[List[str]] = None,
        arc_id: Optional[str] = None,
    ) -> DRSEInputBundle:
        """그래프에서 씬 관련 정보를 추출하여 DRSEInputBundle 생성."""
        ids = char_ids or []
        density = self.compute_relational_density(rgs, ids)
        pressure = self.compute_arc_pressure(rgs, arc_id)
        return DRSEInputBundle(
            scene_id=scene_id,
            relational_density=density,
            arc_pressure=pressure,
            char_ids=ids,
            arc_id=arc_id,
        )

    def compute_relational_density(
        self,
        rgs: Any,
        char_ids: List[str],
    ) -> float:
        """
        캐릭터 집합 간 엣지 밀도 계산.
        RGS 없으면 0.5 반환.
        """
        if rgs is None or not char_ids:
            return 0.5
        try:
            g = getattr(rgs, "_graph", None)
            if g is None:
                return 0.5
            n = len(char_ids)
            if n < 2:
                return 0.5
            max_edges = n * (n - 1)
            actual = sum(
                1 for u, v in g.edges()
                if u in char_ids and v in char_ids
            )
            return min(1.0, actual / max_edges) if max_edges > 0 else 0.5
        except Exception:
            return 0.5

    def compute_arc_pressure(
        self,
        rgs: Any,
        arc_id: Optional[str],
    ) -> float:
        """
        아크 내 긴장 엣지 비율 계산.
        RGS 없거나 arc_id 없으면 0.5 반환.
        """
        if rgs is None or arc_id is None:
            return 0.5
        try:
            g = getattr(rgs, "_graph", None)
            if g is None:
                return 0.5
            arc_edges = [
                d for _, _, d in g.edges(data=True)
                if d.get("arc_id") == arc_id
            ]
            if not arc_edges:
                return 0.5
            tension = sum(
                1 for d in arc_edges
                if d.get("relation_type", "").upper() in self.TENSION_TYPES
            )
            return tension / len(arc_edges)
        except Exception:
            return 0.5
