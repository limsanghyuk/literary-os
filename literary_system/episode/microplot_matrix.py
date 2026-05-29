"""MicroPlotMatrix — V392
16화 × K(가변) 미시 플롯 행렬.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from .episode_planner import EpisodePlan


@dataclass
class MicroPlotMatrix:
    """16화 전체의 미시 플롯 계획 행렬."""
    episodes: List[EpisodePlan] = field(default_factory=list)

    @property
    def episode_count(self) -> int:
        return len(self.episodes)

    @property
    def total_microplot_count(self) -> int:
        return sum(ep.microplot_count for ep in self.episodes)

    @property
    def total_scene_budget(self) -> int:
        return sum(ep.total_scene_budget for ep in self.episodes)

    def get_k(self, episode_idx: int) -> int:
        if 0 <= episode_idx < len(self.episodes):
            return self.episodes[episode_idx].microplot_count
        raise IndexError(f"episode_idx {episode_idx} out of range")

    def get_scene_budget(self, episode_idx: int, mp_idx: int) -> int:
        ep = self.episodes[episode_idx]
        if ep.microplot_count == 0:
            return 0
        return ep.total_scene_budget // ep.microplot_count

    def k_curve(self) -> List[int]:
        return [ep.microplot_count for ep in self.episodes]

    def scene_budget_curve(self) -> List[int]:
        return [ep.total_scene_budget for ep in self.episodes]

    def to_csv(self) -> str:
        lines = ["episode_idx,microplot_count,total_scenes,act_position"]
        for ep in self.episodes:
            lines.append(
                f"{ep.episode_idx},{ep.microplot_count},"
                f"{ep.total_scene_budget},{ep.act_position.value}"
            )
        return "\n".join(lines)

    def summary(self) -> dict:
        if not self.episodes:
            return {}
        ks = self.k_curve()
        return {
            "episode_count": self.episode_count,
            "total_microplots": self.total_microplot_count,
            "total_scene_budget": self.total_scene_budget,
            "k_min": min(ks),
            "k_max": max(ks),
            "k_avg": round(sum(ks) / len(ks), 2),
        }

    @classmethod
    def build(cls, plans: List[EpisodePlan]) -> "MicroPlotMatrix":
        return cls(episodes=plans)
