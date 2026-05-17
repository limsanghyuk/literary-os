"""DramaticLoadBalancing — V393. LLM 0 calls."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass
class EpisodeLoad:
    episode_idx: int
    reveal_load: float = 0.0
    emotional_load: float = 0.0
    conflict_load: float = 0.0
    relationship_load: float = 0.0
    motif_load: float = 0.0
    exposition_load: float = 0.0
    agency_load: float = 0.0
    attention_load: float = 0.0

    @property
    def total_load(self) -> float:
        return (self.reveal_load + self.emotional_load + self.conflict_load
                + self.relationship_load + self.motif_load + self.exposition_load
                + self.agency_load + self.attention_load)

    @property
    def is_overloaded(self) -> bool:
        return self.total_load > 5.5

    @property
    def is_underloaded(self) -> bool:
        return self.total_load < 1.5


@dataclass
class LoadBalanceReport:
    episode_loads: List[EpisodeLoad] = field(default_factory=list)
    overloaded_episodes: List[int] = field(default_factory=list)
    underloaded_episodes: List[int] = field(default_factory=list)
    mid_season_sag_risk: float = 0.0
    finale_overload_risk: float = 0.0
    load_curve: List[float] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def pass_gate(self) -> bool:
        # Korean drama climax arcs ALLOW up to 50% episodes to be high-load.
        # finale_overload_risk = fin_avg / OVERLOAD_THRESHOLD; < 0.8 means finale
        # average load is within 80% of the overload ceiling (structurally sound).
        n = max(1, len(self.episode_loads))
        overload_ratio = len(self.overloaded_episodes) / n
        return (overload_ratio <= 0.50
                and self.mid_season_sag_risk < 0.4
                and self.finale_overload_risk < 0.8)


class DramaticLoadBalancer:
    """V393 — 에피소드 하중 분석기."""

    OVERLOAD_THRESHOLD = 5.5
    UNDERLOAD_THRESHOLD = 1.5

    def analyze(self, episode_loads: List[EpisodeLoad]) -> LoadBalanceReport:
        if not episode_loads:
            return LoadBalanceReport()

        overloaded = [ep.episode_idx for ep in episode_loads if ep.is_overloaded]
        underloaded = [ep.episode_idx for ep in episode_loads if ep.is_underloaded]
        load_curve = [ep.total_load for ep in episode_loads]
        warnings = []

        # mid-season sag: 중반부(40~60%) 평균이 전체 평균보다 크게 낮음
        n = len(load_curve)
        mid_start = int(n * 0.4)
        mid_end = int(n * 0.6) + 1
        mid_loads = load_curve[mid_start:mid_end]
        overall_avg = sum(load_curve) / n
        mid_avg = sum(mid_loads) / max(1, len(mid_loads))
        mid_sag_risk = max(0.0, (overall_avg - mid_avg) / max(0.01, overall_avg))

        # finale overload: 마지막 20% 평균
        fin_start = int(n * 0.8)
        fin_loads = load_curve[fin_start:]
        fin_avg = sum(fin_loads) / max(1, len(fin_loads))
        finale_overload_risk = min(1.0, fin_avg / max(0.01, self.OVERLOAD_THRESHOLD))

        if overloaded:
            warnings.append(f"overloaded_episodes={overloaded}")
        if underloaded:
            warnings.append(f"underloaded_episodes={underloaded}")
        if mid_sag_risk > 0.3:
            warnings.append(f"mid_season_sag_risk={mid_sag_risk:.2f}")

        return LoadBalanceReport(
            episode_loads=episode_loads,
            overloaded_episodes=overloaded,
            underloaded_episodes=underloaded,
            mid_season_sag_risk=round(mid_sag_risk, 4),
            finale_overload_risk=round(finale_overload_risk, 4),
            load_curve=load_curve,
            warnings=warnings,
        )

    @staticmethod
    def compute_load(
        episode_idx: int,
        microplot_count: int,
        act_position_str: str,
        conflict_density: float = 0.5,
        reveal_density: float = 0.5,
    ) -> EpisodeLoad:
        """단일 에피소드 하중 계산."""
        base = {
            "SETUP": [0.2, 0.3, 0.2, 0.3, 0.4, 0.5, 0.2, 0.3],
            "PRESSURE": [0.4, 0.5, 0.4, 0.4, 0.5, 0.3, 0.4, 0.5],
            "COLLISION": [0.7, 0.8, 0.8, 0.5, 0.6, 0.2, 0.7, 0.8],
            "REVERSAL": [0.6, 0.7, 0.6, 0.6, 0.7, 0.2, 0.6, 0.7],
            "RESIDUE": [0.3, 0.5, 0.3, 0.4, 0.5, 0.3, 0.4, 0.4],
        }.get(act_position_str, [0.5]*8)

        scale = 1.0 + 0.1 * (microplot_count - 4)
        loads = [min(1.0, v * scale) for v in base]
        loads[0] = min(1.0, loads[0] * (0.5 + reveal_density))
        loads[2] = min(1.0, loads[2] * (0.5 + conflict_density))

        return EpisodeLoad(
            episode_idx=episode_idx,
            reveal_load=loads[0], emotional_load=loads[1],
            conflict_load=loads[2], relationship_load=loads[3],
            motif_load=loads[4], exposition_load=loads[5],
            agency_load=loads[6], attention_load=loads[7],
        )
