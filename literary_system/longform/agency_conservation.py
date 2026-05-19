"""CharacterAgencyConservation — V394. LLM 0 calls."""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


class AgencyEventType(str, Enum):
    CHOICE = "CHOICE"; REFUSAL = "REFUSAL"; LIE = "LIE"
    CONFESSION = "CONFESSION"; SACRIFICE = "SACRIFICE"; BETRAYAL = "BETRAYAL"
    RESISTANCE = "RESISTANCE"; SILENCE = "SILENCE"; TRADE = "TRADE"
    MISJUDGMENT = "MISJUDGMENT"; RETURN = "RETURN"


@dataclass
class AgencyDelta:
    """단일 장면에서 인물의 agency 변화량."""
    character_id: str
    episode_idx: int
    scene_id: str
    event_type: AgencyEventType
    decision_weight: float = 0.5      # 결정의 중요도
    consequence_weight: float = 0.5   # 결과의 무게
    risk_weight: float = 0.3          # 위험 감수 정도
    irreversibility_weight: float = 0.4
    belief_shift_weight: float = 0.3

    @property
    def score(self) -> float:
        return (self.decision_weight * 0.3
                + self.consequence_weight * 0.25
                + self.risk_weight * 0.2
                + self.irreversibility_weight * 0.15
                + self.belief_shift_weight * 0.1)

    @classmethod
    def passive(cls, character_id: str, episode_idx: int, scene_id: str) -> "AgencyDelta":
        """agency 없는 수동적 장면."""
        return cls(character_id=character_id, episode_idx=episode_idx, scene_id=scene_id,
                   event_type=AgencyEventType.SILENCE,
                   decision_weight=0.0, consequence_weight=0.0,
                   risk_weight=0.0, irreversibility_weight=0.0, belief_shift_weight=0.0)


@dataclass
class AgencyReport:
    character_agency_curves: Dict[str, List[float]] = field(default_factory=dict)
    protagonist_floor_pass: bool = True
    passive_episode_counts: Dict[str, int] = field(default_factory=dict)
    agency_floor_violations: List[str] = field(default_factory=list)
    max_passive_threshold: int = 3

    @property
    def pass_gate(self) -> bool:
        return self.protagonist_floor_pass and len(self.agency_floor_violations) == 0


class AgencyConservationChecker:
    """V394 — 인물 agency 보존 검증기."""

    AGENCY_FLOOR = 0.15          # 에피소드당 최소 agency score
    MAX_PASSIVE_EPISODES = 3     # 주인공이 수동적 에피소드 최대 허용 수

    def check(
        self,
        deltas: List[AgencyDelta],
        protagonist_ids: List[str],
        episode_count: int = 16,
    ) -> AgencyReport:
        # 인물별 에피소드별 누적 agency score
        curves: Dict[str, List[float]] = {}
        for char_id in set(d.character_id for d in deltas):
            ep_scores = [0.0] * episode_count
            for d in deltas:
                if d.character_id == char_id and d.episode_idx < episode_count:
                    ep_scores[d.episode_idx] += d.score
            curves[char_id] = ep_scores

        violations = []
        passive_counts: Dict[str, int] = {}
        protagonist_pass = True

        for pid in protagonist_ids:
            ep_scores = curves.get(pid, [0.0] * episode_count)
            passive_eps = sum(1 for s in ep_scores if s < self.AGENCY_FLOOR)
            passive_counts[pid] = passive_eps
            if passive_eps > self.MAX_PASSIVE_EPISODES:
                violations.append(
                    f"protagonist_passive_episodes: {pid} passive={passive_eps}"
                )
                protagonist_pass = False

        return AgencyReport(
            character_agency_curves=curves,
            protagonist_floor_pass=protagonist_pass,
            passive_episode_counts=passive_counts,
            agency_floor_violations=violations,
            max_passive_threshold=self.MAX_PASSIVE_EPISODES,
        )

    @staticmethod
    def build_synthetic_deltas(
        protagonist_ids: List[str],
        episode_count: int = 16,
        scenes_per_episode: int = 8,
    ) -> List[AgencyDelta]:
        """Synthetic 테스트용 delta 목록 생성."""
        import random
        random.seed(42)
        deltas = []
        event_types = list(AgencyEventType)
        for ep_i in range(episode_count):
            for sc_i in range(scenes_per_episode):
                for pid in protagonist_ids:
                    et = random.choice(event_types)
                    deltas.append(AgencyDelta(
                        character_id=pid,
                        episode_idx=ep_i,
                        scene_id=f"ep{ep_i}_sc{sc_i}",
                        event_type=et,
                        decision_weight=random.uniform(0.3, 0.9),
                        consequence_weight=random.uniform(0.3, 0.9),
                        risk_weight=random.uniform(0.2, 0.7),
                        irreversibility_weight=random.uniform(0.2, 0.7),
                        belief_shift_weight=random.uniform(0.2, 0.7),
                    ))
        return deltas
