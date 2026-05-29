"""EpisodeState — V391
에피소드 상태 텐서의 단일 에피소드 슬라이스.
T[episode][scene][character][dimension]에서 episode 레이어를 담당한다.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class ActPosition(str, Enum):
    SETUP = "SETUP"
    PRESSURE = "PRESSURE"
    COLLISION = "COLLISION"
    REVERSAL = "REVERSAL"
    RESIDUE = "RESIDUE"


@dataclass
class MicroPlotSlot:
    """미시 플롯 슬롯 — EpisodePlan이 K개 생성."""
    slot_idx: int
    scene_budget: int          # 이 미시 플롯이 소비할 씬 수
    reveal_budget: float       # 0~1, 공개 예산
    emotional_target: float    # 0~1, 감정 목표치
    conflict_weight: float     # 0~1
    act_function: str          # 이 슬롯이 서사에서 수행하는 기능
    filled: bool = False       # FullSceneOrchestrator가 채우면 True


@dataclass
class CharacterEpisodeState:
    """에피소드 내 단일 인물 상태."""
    character_id: str
    belief_state: Dict[str, float] = field(default_factory=dict)
    emotional_level: float = 0.5
    goal_progress: float = 0.0
    agency_delta_sum: float = 0.0
    active: bool = True


@dataclass
class EpisodeState:
    """단일 에피소드의 완전한 상태.
    NarrativeStateTensor의 episode 축 슬라이스.
    """
    episode_idx: int                                # 0-based
    act_position: ActPosition
    microplot_slots: List[MicroPlotSlot] = field(default_factory=list)
    character_states: Dict[str, CharacterEpisodeState] = field(default_factory=dict)
    open_debt_ids: List[str] = field(default_factory=list)
    paid_debt_ids: List[str] = field(default_factory=list)
    energy_budget: float = 1.0
    curiosity_target: float = 0.6
    episode_hook_strength: float = 0.5
    completed: bool = False
    execution_trace: List[str] = field(default_factory=list)

    @property
    def microplot_count(self) -> int:
        return len(self.microplot_slots)

    @property
    def total_scene_budget(self) -> int:
        return sum(s.scene_budget for s in self.microplot_slots)

    def add_trace(self, msg: str) -> None:
        self.execution_trace.append(f"[Ep{self.episode_idx:02d}] {msg}")

    def mark_slot_filled(self, slot_idx: int) -> None:
        for s in self.microplot_slots:
            if s.slot_idx == slot_idx:
                s.filled = True
                break

    def all_slots_filled(self) -> bool:
        return all(s.filled for s in self.microplot_slots)


@dataclass
class NarrativeStateTensor:
    """16화 전체 서사 상태 텐서.
    T[episode][scene][character][dimension]의 에피소드 축.
    """
    total_episodes: int
    episodes: List[EpisodeState] = field(default_factory=list)

    # 시리즈 전체 누적 지표
    total_reveal_budget: float = 1.0
    used_reveal_budget: float = 0.0
    active_characters: List[str] = field(default_factory=list)
    conflict_pressure: float = 0.5
    avg_emotional_momentum: float = 0.5
    scene_energy_required: float = 0.6
    avg_curiosity_gradient: float = 0.6

    @property
    def remaining_reveal_budget(self) -> float:
        return max(0.0, self.total_reveal_budget - self.used_reveal_budget)

    @property
    def current_episode_idx(self) -> int:
        return len(self.episodes)

    def push_episode(self, ep: EpisodeState) -> None:
        self.episodes.append(ep)

    def update_from_episode(self, ep: EpisodeState) -> None:
        """에피소드 완료 후 텐서 전역 지표 갱신."""
        reveal_used = sum(s.reveal_budget for s in ep.microplot_slots)
        self.used_reveal_budget += reveal_used * 0.1  # 스케일 조정
        if ep.character_states:
            emotions = [c.emotional_level for c in ep.character_states.values()]
            self.avg_emotional_momentum = sum(emotions) / len(emotions)


@dataclass
class SeriesConfig:
    """시리즈 전체 설정."""
    title: str
    total_episodes: int = 16            # 16화 또는 24화
    runtime_minutes: int = 60           # 화당 분량
    genre: str = "korean_drama"
    protagonist_ids: List[str] = field(default_factory=list)
    target_audience: str = "general"
    act_structure: str = "5act"         # 5act or 3act
    reveal_strategy: str = "gradual"    # gradual / twist_heavy / character_driven
