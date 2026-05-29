"""EpisodePlanner — V392
K값(미시 플롯 수)을 동적으로 계산하는 에피소드 플래너.
LLM 호출 0회. 9개 변수의 결정론적 함수.

K = f(episode_position, act_position, target_runtime, reveal_budget,
       character_density, conflict_density, emotional_momentum,
       scene_energy_required, curiosity_gradient)
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import List

from .episode_state import ActPosition, EpisodeState, MicroPlotSlot, NarrativeStateTensor, SeriesConfig


@dataclass
class EpisodePlan:
    """EpisodePlanner.plan()의 출력."""
    episode_idx: int
    microplot_count: int               # K
    total_scene_budget: int
    act_position: ActPosition
    reveal_budget_per_slot: float
    emotional_targets: List[float]
    conflict_weights: List[float]
    slot_functions: List[str]
    planning_trace: List[str] = field(default_factory=list)

    def to_episode_state(self) -> EpisodeState:
        slots = [
            MicroPlotSlot(
                slot_idx=i,
                scene_budget=max(3, self.total_scene_budget // self.microplot_count),
                reveal_budget=self.reveal_budget_per_slot,
                emotional_target=self.emotional_targets[i],
                conflict_weight=self.conflict_weights[i],
                act_function=self.slot_functions[i],
            )
            for i in range(self.microplot_count)
        ]
        return EpisodeState(
            episode_idx=self.episode_idx,
            act_position=self.act_position,
            microplot_slots=slots,
        )


class EpisodePlanner:
    """에피소드 플래너.

    K = base_K × position_multiplier × runtime_factor
        × reveal_factor × density_factor
    범위: K ∈ [2, 8]

    씬 예산: K × scenes_per_microplot (3~8)
    """

    # K 계산 상수
    BASE_K = 4
    K_MIN = 2
    K_MAX = 8
    BASE_SCENES_PER_MICROPLOT = 5

    def plan(
        self,
        series_config: SeriesConfig,
        episode_idx: int,
        narrative_state: NarrativeStateTensor,
    ) -> EpisodePlan:
        trace = []
        n = series_config.total_episodes
        pos = episode_idx / max(1, n - 1)  # 0.0 ~ 1.0

        act_pos = self._determine_act_position(pos, series_config.act_structure)
        trace.append(f"act_position={act_pos.value} pos={pos:.2f}")

        K = self._compute_k(
            episode_position=pos,
            act_position=act_pos,
            target_runtime=series_config.runtime_minutes,
            reveal_budget=narrative_state.remaining_reveal_budget,
            character_density=len(narrative_state.active_characters),
            conflict_density=narrative_state.conflict_pressure,
            emotional_momentum=narrative_state.avg_emotional_momentum,
            scene_energy_req=narrative_state.scene_energy_required,
            curiosity_gradient=narrative_state.avg_curiosity_gradient,
        )
        trace.append(f"K={K}")

        scenes_per_mp = self._compute_scenes_per_mp(act_pos, series_config.runtime_minutes)
        total_scenes = K * scenes_per_mp
        trace.append(f"scenes_per_mp={scenes_per_mp} total_scenes={total_scenes}")

        reveal_per_slot = self._compute_reveal_budget(pos, narrative_state, K)
        emotional_targets = self._compute_emotional_targets(K, act_pos, pos)
        conflict_weights = self._compute_conflict_weights(K, act_pos)
        slot_functions = self._assign_slot_functions(K, act_pos, pos, n)

        return EpisodePlan(
            episode_idx=episode_idx,
            microplot_count=K,
            total_scene_budget=total_scenes,
            act_position=act_pos,
            reveal_budget_per_slot=reveal_per_slot,
            emotional_targets=emotional_targets,
            conflict_weights=conflict_weights,
            slot_functions=slot_functions,
            planning_trace=trace,
        )

    # ── 내부 계산 ──────────────────────────────────────────────

    def _determine_act_position(self, pos: float, structure: str) -> ActPosition:
        if structure == "5act":
            if pos < 0.12:   return ActPosition.SETUP
            if pos < 0.38:   return ActPosition.PRESSURE
            if pos < 0.62:   return ActPosition.COLLISION
            if pos < 0.85:   return ActPosition.REVERSAL
            return ActPosition.RESIDUE
        else:  # 3act
            if pos < 0.25:   return ActPosition.SETUP
            if pos < 0.75:   return ActPosition.COLLISION
            return ActPosition.RESIDUE

    def _compute_k(
        self,
        episode_position: float,
        act_position: ActPosition,
        target_runtime: int,
        reveal_budget: float,
        character_density: int,
        conflict_density: float,
        emotional_momentum: float,
        scene_energy_req: float,
        curiosity_gradient: float,
    ) -> int:
        k = float(self.BASE_K)

        # 1. 막(Act) 위치별 기본 조정
        act_mult = {
            ActPosition.SETUP: 0.8,
            ActPosition.PRESSURE: 1.0,
            ActPosition.COLLISION: 1.3,
            ActPosition.REVERSAL: 1.2,
            ActPosition.RESIDUE: 0.9,
        }[act_position]
        k *= act_mult

        # 2. 런타임 팩터 (60분 기준)
        runtime_factor = math.sqrt(target_runtime / 60.0)
        k *= runtime_factor

        # 3. reveal budget 여유가 많을수록 미시 플롯 수 증가
        k *= (0.8 + 0.4 * reveal_budget)

        # 4. 인물 밀도 (3~10인 기준)
        density_norm = min(1.0, max(0.0, (character_density - 2) / 8.0))
        k *= (0.9 + 0.2 * density_norm)

        # 5. 갈등 강도 높을수록 미시 플롯 세분화
        k *= (0.9 + 0.2 * conflict_density)

        # 6. 감정 모멘텀 높을수록 약간 증가
        k *= (0.95 + 0.1 * emotional_momentum)

        raw_k = int(round(k))
        return max(self.K_MIN, min(self.K_MAX, raw_k))

    def _compute_scenes_per_mp(self, act: ActPosition, runtime: int) -> int:
        base = max(3, round(self.BASE_SCENES_PER_MICROPLOT * runtime / 60))
        mult = {
            ActPosition.SETUP: 0.8,
            ActPosition.PRESSURE: 1.0,
            ActPosition.COLLISION: 1.2,
            ActPosition.REVERSAL: 1.1,
            ActPosition.RESIDUE: 0.9,
        }[act]
        return max(3, int(round(base * mult)))

    def _compute_reveal_budget(
        self, pos: float, state: NarrativeStateTensor, K: int
    ) -> float:
        remaining = state.remaining_reveal_budget
        episodes_left = max(1, state.total_episodes - state.current_episode_idx)
        per_episode = remaining / episodes_left
        per_slot = per_episode / K
        return round(max(0.01, min(0.3, per_slot)), 4)

    def _compute_emotional_targets(
        self, K: int, act: ActPosition, pos: float
    ) -> list:
        base_map = {
            ActPosition.SETUP: 0.3,
            ActPosition.PRESSURE: 0.5,
            ActPosition.COLLISION: 0.75,
            ActPosition.REVERSAL: 0.85,
            ActPosition.RESIDUE: 0.6,
        }
        base = base_map[act]
        return [round(base + 0.05 * (i - K // 2) / max(1, K), 3) for i in range(K)]

    def _compute_conflict_weights(self, K: int, act: ActPosition) -> list:
        base_map = {
            ActPosition.SETUP: 0.2,
            ActPosition.PRESSURE: 0.4,
            ActPosition.COLLISION: 0.7,
            ActPosition.REVERSAL: 0.65,
            ActPosition.RESIDUE: 0.35,
        }
        base = base_map[act]
        step = 0.05 / max(1, K)
        return [round(min(1.0, base + step * i), 3) for i in range(K)]

    def _assign_slot_functions(
        self, K: int, act: ActPosition, pos: float, total_episodes: int
    ) -> list:
        func_pools = {
            ActPosition.SETUP: ["introduction", "world_build", "inciting_incident", "character_establish"],
            ActPosition.PRESSURE: ["escalation", "complication", "ally_test", "reveal_partial"],
            ActPosition.COLLISION: ["confrontation", "crisis", "betrayal", "peak_conflict"],
            ActPosition.REVERSAL: ["twist", "revelation", "sacrifice", "regroup"],
            ActPosition.RESIDUE: ["resolution", "aftermath", "new_normal", "open_question"],
        }
        pool = func_pools[act]
        # 마지막 화 특수 처리
        if pos > 0.9:
            pool = ["final_confrontation", "resolution", "aftermath", "closure"]
        return [pool[i % len(pool)] for i in range(K)]
