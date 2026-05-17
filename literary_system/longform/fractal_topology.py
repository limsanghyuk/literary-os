"""FractalTopology — V393
시리즈~비트 모든 단위에 setup→pressure→collision→reversal→residue 구조 적용.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class FractalUnitType(str, Enum):
    SERIES = "SERIES"
    EPISODE = "EPISODE"
    MICROPLOT = "MICROPLOT"
    SCENE = "SCENE"
    BEAT = "BEAT"


@dataclass
class FractalPlotUnit:
    unit_id: str
    unit_type: FractalUnitType
    setup: str = ""
    pressure: str = ""
    collision: str = ""
    reversal: str = ""
    residue: str = ""
    parent_unit_id: Optional[str] = None
    child_unit_ids: List[str] = field(default_factory=list)

    @property
    def filled_phases(self) -> int:
        return sum(1 for p in [self.setup, self.pressure, self.collision,
                                self.reversal, self.residue] if p.strip())

    def is_complete(self) -> bool:
        return self.filled_phases == 5

    def is_orphan(self) -> bool:
        return (self.unit_type != FractalUnitType.SERIES
                and self.parent_unit_id is None)


@dataclass
class FractalReport:
    orphan_microplot_count: int
    episode_function_coverage: float          # 0~1
    incomplete_unit_count: int
    total_units: int
    fractal_depth_distribution: Dict[str, int] = field(default_factory=dict)
    violations: List[str] = field(default_factory=list)

    @property
    def pass_gate(self) -> bool:
        return (self.orphan_microplot_count == 0
                and self.episode_function_coverage >= 1.0
                and len(self.violations) == 0)


class FractalTopologyValidator:
    """V393 — LLM 0 calls."""

    def validate(self, units: List[FractalPlotUnit]) -> FractalReport:
        orphan_count = 0
        incomplete = 0
        violations = []
        depth_dist: Dict[str, int] = {}

        id_set = {u.unit_id for u in units}
        episode_units = [u for u in units if u.unit_type == FractalUnitType.EPISODE]
        microplot_units = [u for u in units if u.unit_type == FractalUnitType.MICROPLOT]

        for u in units:
            # 깊이 분포
            t = u.unit_type.value
            depth_dist[t] = depth_dist.get(t, 0) + 1

            # 고아 미시 플롯 검사
            if u.unit_type == FractalUnitType.MICROPLOT and u.is_orphan():
                orphan_count += 1
                violations.append(f"orphan_microplot: {u.unit_id}")

            # 부모 참조 유효성
            if u.parent_unit_id and u.parent_unit_id not in id_set:
                violations.append(f"dangling_parent_ref: {u.unit_id} -> {u.parent_unit_id}")

            # 미완성 유닛
            if not u.is_complete():
                incomplete += 1

        # 에피소드 커버리지: 각 에피소드가 최소 1개 미시 플롯 자식 보유?
        covered = 0
        for ep in episode_units:
            has_child = any(
                mp.parent_unit_id == ep.unit_id for mp in microplot_units
            )
            if has_child:
                covered += 1
            else:
                violations.append(f"episode_no_microplot: {ep.unit_id}")

        coverage = covered / max(1, len(episode_units))

        return FractalReport(
            orphan_microplot_count=orphan_count,
            episode_function_coverage=coverage,
            incomplete_unit_count=incomplete,
            total_units=len(units),
            fractal_depth_distribution=depth_dist,
            violations=violations,
        )

    @staticmethod
    def build_synthetic(episode_count: int = 16) -> List[FractalPlotUnit]:
        """Synthetic corpus용 FractalPlotUnit 트리 생성."""
        units: List[FractalPlotUnit] = []
        series_id = "S_001"
        units.append(FractalPlotUnit(
            unit_id=series_id, unit_type=FractalUnitType.SERIES,
            setup="주인공 등장", pressure="시련 시작", collision="정점 충돌",
            reversal="반전", residue="새로운 세계"
        ))
        for ep_i in range(episode_count):
            ep_id = f"E_{ep_i+1:02d}"
            units.append(FractalPlotUnit(
                unit_id=ep_id, unit_type=FractalUnitType.EPISODE,
                parent_unit_id=series_id,
                setup=f"Ep{ep_i+1} setup", pressure=f"Ep{ep_i+1} pressure",
                collision=f"Ep{ep_i+1} collision", reversal=f"Ep{ep_i+1} reversal",
                residue=f"Ep{ep_i+1} residue"
            ))
            # 에피소드당 3~5개 미시 플롯
            mp_count = 3 + (ep_i % 3)
            for mp_i in range(mp_count):
                mp_id = f"MP_{ep_i+1:02d}_{mp_i+1:02d}"
                units.append(FractalPlotUnit(
                    unit_id=mp_id, unit_type=FractalUnitType.MICROPLOT,
                    parent_unit_id=ep_id,
                    setup="setup", pressure="pressure",
                    collision="collision", reversal="reversal", residue="residue"
                ))
        return units
