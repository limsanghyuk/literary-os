"""
literary_system/longform/fractal_plot_tree.py
V483 — FractalPlotTree 생성기 (max_depth=4)

V393 FractalTopologyValidator가 기존 FractalPlotUnit을 검증한다면,
FractalPlotTreeBuilder는 서사 파라미터로부터 FractalPlotUnit 계층을
재귀적으로 생성한다. max_depth=4 (SERIES→EPISODE→MICROPLOT→SCENE).

LLM-0 원칙: LLM 호출 없음. 순수 수치 계산 + 규칙 기반.

인터페이스:
  FractalPlotTreeBuilder.build(config) → FractalPlotTree
  FractalPlotTree.units_at_depth(d) → List[FractalPlotUnit]
  FractalPlotTree.validate() → FractalReport
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .fractal_topology import (
    FractalPlotUnit,
    FractalReport,
    FractalTopologyValidator,
    FractalUnitType,
)

# ── 설정 ──────────────────────────────────────────────────────────

@dataclass
class FractalTreeConfig:
    """FractalPlotTreeBuilder 입력 설정."""
    total_episodes: int = 16
    microplots_per_episode: int = 4    # K (EpisodePlanner가 계산; 여기선 고정값)
    scenes_per_microplot: int = 5      # 씬/미시플롯 기본값
    max_depth: int = 4                 # SERIES(0)→EPISODE(1)→MP(2)→SCENE(3)
    act_structure: str = "5act"

    # 5막 기준 함수 풀
    PHASE_FUNCS: Dict[str, List[str]] = field(default_factory=lambda: {
        "setup":     ["world_build", "character_establish", "inciting_incident"],
        "pressure":  ["escalation", "complication", "ally_test"],
        "collision": ["confrontation", "crisis", "betrayal"],
        "reversal":  ["twist", "revelation", "sacrifice"],
        "residue":   ["resolution", "aftermath", "open_question"],
    })


# ── 트리 컨테이너 ─────────────────────────────────────────────────

@dataclass
class FractalPlotTree:
    """
    FractalPlotUnit 계층을 담는 컨테이너.
    root: SERIES 루트 단위
    all_units: 평탄화된 전체 유닛 목록
    """
    root: FractalPlotUnit
    all_units: List[FractalPlotUnit] = field(default_factory=list)
    config: Optional[FractalTreeConfig] = None

    def units_at_depth(self, depth: int) -> List[FractalPlotUnit]:
        """특정 깊이의 유닛 목록 반환 (0=SERIES, 1=EPISODE, 2=MP, 3=SCENE)."""
        depth_to_type = {
            0: FractalUnitType.SERIES,
            1: FractalUnitType.EPISODE,
            2: FractalUnitType.MICROPLOT,
            3: FractalUnitType.SCENE,
            4: FractalUnitType.BEAT,
        }
        target = depth_to_type.get(depth)
        if target is None:
            return []
        return [u for u in self.all_units if u.unit_type == target]

    def units_by_type(self, unit_type: FractalUnitType) -> List[FractalPlotUnit]:
        return [u for u in self.all_units if u.unit_type == unit_type]

    def episode_units(self) -> List[FractalPlotUnit]:
        return self.units_at_depth(1)

    def microplot_units(self) -> List[FractalPlotUnit]:
        return self.units_at_depth(2)

    def scene_units(self) -> List[FractalPlotUnit]:
        return self.units_at_depth(3)

    def total_unit_count(self) -> int:
        return len(self.all_units)

    def validate(self) -> FractalReport:
        validator = FractalTopologyValidator()
        return validator.validate(self.all_units)

    def summary(self) -> dict:
        return {
            "total_units": self.total_unit_count(),
            "series_count": len(self.units_at_depth(0)),
            "episode_count": len(self.episode_units()),
            "microplot_count": len(self.microplot_units()),
            "scene_count": len(self.scene_units()),
            "max_depth": self.config.max_depth if self.config else 4,
        }


# ── 빌더 ──────────────────────────────────────────────────────────

class FractalPlotTreeBuilder:
    """
    V483 — 재귀적 FractalPlotTree 생성기.

    알고리즘:
      1. SERIES 루트 생성 (depth=0)
      2. EPISODE 생성 (depth=1, total_episodes개)
      3. 각 EPISODE에 MICROPLOT 생성 (depth=2, K개)
      4. 각 MICROPLOT에 SCENE 생성 (depth=3, scenes_per_mp개)
      (max_depth=4이면 BEAT까지 생성)

    5막 위치는 episode 인덱스로 결정.
    각 유닛의 setup/pressure/collision/reversal/residue는 함수명 문자열로 채움.
    """

    _SERIES_5ACT_PHASES = ["setup", "pressure", "collision", "reversal", "residue"]
    _SERIES_3ACT_PHASES = ["setup", "collision", "residue"]

    def build(self, config: FractalTreeConfig) -> FractalPlotTree:
        all_units: List[FractalPlotUnit] = []

        # SERIES 루트
        series_unit = self._make_series(config)
        all_units.append(series_unit)

        # EPISODE 레이어
        for ep_idx in range(config.total_episodes):
            ep_unit = self._make_episode(ep_idx, config.total_episodes, config, series_unit)
            all_units.append(ep_unit)
            series_unit.child_unit_ids.append(ep_unit.unit_id)

            if config.max_depth < 2:
                continue

            # MICROPLOT 레이어
            for mp_idx in range(config.microplots_per_episode):
                mp_unit = self._make_microplot(ep_idx, mp_idx, config, ep_unit)
                all_units.append(mp_unit)
                ep_unit.child_unit_ids.append(mp_unit.unit_id)

                if config.max_depth < 3:
                    continue

                # SCENE 레이어
                for sc_idx in range(config.scenes_per_microplot):
                    sc_unit = self._make_scene(ep_idx, mp_idx, sc_idx, config, mp_unit)
                    all_units.append(sc_unit)
                    mp_unit.child_unit_ids.append(sc_unit.unit_id)

                    if config.max_depth < 4:
                        continue

                    # BEAT 레이어 (max_depth=4)
                    for bt_idx in range(3):  # 씬당 비트 3개 기본
                        bt_unit = self._make_beat(ep_idx, mp_idx, sc_idx, bt_idx, sc_unit)
                        all_units.append(bt_unit)
                        sc_unit.child_unit_ids.append(bt_unit.unit_id)

        return FractalPlotTree(root=series_unit, all_units=all_units, config=config)

    # ── 팩토리 메서드 ────────────────────────────────────────────

    def _episode_phase(self, ep_idx: int, total: int) -> str:
        """에피소드 위치 → 5막 위상."""
        pos = ep_idx / max(1, total - 1)
        if pos < 0.12:   return "setup"
        if pos < 0.38:   return "pressure"
        if pos < 0.62:   return "collision"
        if pos < 0.85:   return "reversal"
        return "residue"

    def _mp_phase(self, mp_idx: int, total_mp: int) -> str:
        """미시 플롯 내 위치 → 5막 위상."""
        pos = mp_idx / max(1, total_mp - 1)
        if pos < 0.2:  return "setup"
        if pos < 0.4:  return "pressure"
        if pos < 0.7:  return "collision"
        if pos < 0.9:  return "reversal"
        return "residue"

    def _get_func(self, phase: str, idx: int, config: FractalTreeConfig) -> str:
        pool = config.PHASE_FUNCS.get(phase, ["generic"])
        return pool[idx % len(pool)]

    def _make_unit_5phases(
        self,
        unit_id: str,
        unit_type: FractalUnitType,
        dominant_phase: str,
        idx: int,
        config: FractalTreeConfig,
        parent_id: Optional[str],
    ) -> FractalPlotUnit:
        """5개 위상 문자열을 채운 FractalPlotUnit 생성."""
        phases = {}
        for ph in self._SERIES_5ACT_PHASES:
            phases[ph] = self._get_func(ph, idx, config)
        return FractalPlotUnit(
            unit_id=unit_id,
            unit_type=unit_type,
            setup=phases["setup"],
            pressure=phases["pressure"],
            collision=phases["collision"],
            reversal=phases["reversal"],
            residue=phases["residue"],
            parent_unit_id=parent_id,
        )

    def _make_series(self, config: FractalTreeConfig) -> FractalPlotUnit:
        return self._make_unit_5phases(
            unit_id="series_root",
            unit_type=FractalUnitType.SERIES,
            dominant_phase="collision",
            idx=0,
            config=config,
            parent_id=None,
        )

    def _make_episode(
        self, ep_idx: int, total: int, config: FractalTreeConfig, parent: FractalPlotUnit
    ) -> FractalPlotUnit:
        phase = self._episode_phase(ep_idx, total)
        return self._make_unit_5phases(
            unit_id=f"ep_{ep_idx:03d}",
            unit_type=FractalUnitType.EPISODE,
            dominant_phase=phase,
            idx=ep_idx,
            config=config,
            parent_id=parent.unit_id,
        )

    def _make_microplot(
        self, ep_idx: int, mp_idx: int, config: FractalTreeConfig, parent: FractalPlotUnit
    ) -> FractalPlotUnit:
        phase = self._mp_phase(mp_idx, config.microplots_per_episode)
        return self._make_unit_5phases(
            unit_id=f"ep_{ep_idx:03d}_mp_{mp_idx:02d}",
            unit_type=FractalUnitType.MICROPLOT,
            dominant_phase=phase,
            idx=mp_idx,
            config=config,
            parent_id=parent.unit_id,
        )

    def _make_scene(
        self, ep_idx: int, mp_idx: int, sc_idx: int,
        config: FractalTreeConfig, parent: FractalPlotUnit
    ) -> FractalPlotUnit:
        return self._make_unit_5phases(
            unit_id=f"ep_{ep_idx:03d}_mp_{mp_idx:02d}_sc_{sc_idx:02d}",
            unit_type=FractalUnitType.SCENE,
            dominant_phase="collision",
            idx=sc_idx,
            config=config,
            parent_id=parent.unit_id,
        )

    def _make_beat(
        self, ep_idx: int, mp_idx: int, sc_idx: int, bt_idx: int,
        parent: FractalPlotUnit
    ) -> FractalPlotUnit:
        beat_funcs = ["action", "reaction", "decision"]
        func = beat_funcs[bt_idx % 3]
        return FractalPlotUnit(
            unit_id=f"ep_{ep_idx:03d}_mp_{mp_idx:02d}_sc_{sc_idx:02d}_bt_{bt_idx}",
            unit_type=FractalUnitType.BEAT,
            setup=func,
            pressure=func,
            collision=func,
            reversal=func,
            residue=func,
            parent_unit_id=parent.unit_id,
        )
