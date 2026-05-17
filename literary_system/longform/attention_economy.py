"""NarrativeAttentionEconomy — V398. LLM 0 calls.
독자 집중력을 제한 자원으로 모델링.
AttentionValue = rewards - costs.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class SceneAttentionValue:
    """단일 장면의 집중력 가치."""
    scene_id: str
    emotional_reward: float = 0.0
    curiosity_reward: float = 0.0
    payoff_reward: float = 0.0
    agency_reward: float = 0.0
    cognitive_load: float = 0.0
    confusion_cost: float = 0.0
    repetition_cost: float = 0.0

    @property
    def net_value(self) -> float:
        rewards = (self.emotional_reward + self.curiosity_reward
                   + self.payoff_reward + self.agency_reward)
        costs = self.cognitive_load + self.confusion_cost + self.repetition_cost
        return rewards - costs

    @property
    def is_draining(self) -> bool:
        return self.net_value < -0.2


@dataclass
class FatigueReport:
    episode_attention_values: List[float] = field(default_factory=list)
    mid_season_fatigue_risk: float = 0.0
    finale_fatigue_risk: float = 0.0
    low_reward_high_cost_scenes: List[str] = field(default_factory=list)
    episode_ending_hook_strengths: List[float] = field(default_factory=list)
    cognitive_overload_warnings: List[str] = field(default_factory=list)

    @property
    def pass_gate(self) -> bool:
        return (self.mid_season_fatigue_risk < 0.4
                and self.finale_fatigue_risk < 0.3)


class NarrativeAttentionEconomy:
    """V398 — 독자 집중력 경제 모델."""

    MID_SEASON_START = 0.4
    MID_SEASON_END = 0.65
    FINALE_START = 0.8

    def analyze(
        self,
        scene_values: List[SceneAttentionValue],
        episode_count: int = 16,
    ) -> FatigueReport:
        if not scene_values:
            return FatigueReport()

        # 에피소드별 평균 집중력
        n_scenes = len(scene_values)
        scenes_per_ep = max(1, n_scenes // episode_count)
        ep_values: List[float] = []
        for i in range(episode_count):
            start = i * scenes_per_ep
            end = start + scenes_per_ep
            chunk = scene_values[start:end]
            avg_val = sum(s.net_value for s in chunk) / max(1, len(chunk))
            ep_values.append(round(avg_val, 4))

        n = len(ep_values)
        mid_s = int(n * self.MID_SEASON_START)
        mid_e = int(n * self.MID_SEASON_END) + 1
        fin_s = int(n * self.FINALE_START)

        mid_vals = ep_values[mid_s:mid_e]
        fin_vals = ep_values[fin_s:]
        overall_avg = sum(ep_values) / n

        # 피로 리스크: 평균보다 낮은 구간
        mid_avg = sum(mid_vals) / max(1, len(mid_vals))
        fin_avg = sum(fin_vals) / max(1, len(fin_vals))

        mid_risk = max(0.0, min(1.0, (0.0 - mid_avg) / 0.5 + 0.3))
        fin_risk = max(0.0, min(1.0, (0.0 - fin_avg) / 0.5 + 0.2))

        # 저보상 고비용 장면
        draining = [s.scene_id for s in scene_values if s.is_draining]

        # 에피소드 엔딩 훅 강도: 각 에피소드 마지막 씬의 curiosity_reward
        hook_strengths = []
        for i in range(episode_count):
            end_idx = min((i+1) * scenes_per_ep - 1, n_scenes - 1)
            hook_strengths.append(scene_values[end_idx].curiosity_reward)

        cog_warnings = [
            s.scene_id for s in scene_values if s.cognitive_load > 0.7
        ]

        return FatigueReport(
            episode_attention_values=ep_values,
            mid_season_fatigue_risk=round(mid_risk, 4),
            finale_fatigue_risk=round(fin_risk, 4),
            low_reward_high_cost_scenes=draining,
            episode_ending_hook_strengths=hook_strengths,
            cognitive_overload_warnings=cog_warnings,
        )

    @staticmethod
    def build_synthetic_scenes(
        episode_count: int = 16, scenes_per_ep: int = 8
    ) -> List[SceneAttentionValue]:
        import random
        random.seed(55)
        scenes = []
        for ep_i in range(episode_count):
            pos = ep_i / max(1, episode_count - 1)
            for sc_i in range(scenes_per_ep):
                # 후반부로 갈수록 보상 증가
                base_reward = 0.3 + 0.4 * pos
                scenes.append(SceneAttentionValue(
                    scene_id=f"ep{ep_i}_sc{sc_i}",
                    emotional_reward=random.uniform(base_reward * 0.8, base_reward * 1.2),
                    curiosity_reward=random.uniform(0.2, 0.6),
                    payoff_reward=random.uniform(0.0, 0.3),
                    agency_reward=random.uniform(0.1, 0.4),
                    cognitive_load=random.uniform(0.1, 0.3),
                    confusion_cost=random.uniform(0.0, 0.15),
                    repetition_cost=random.uniform(0.0, 0.1),
                ))
        return scenes
