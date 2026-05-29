"""
literary_system/episode/episode_structure_calculator.py
V482 — EpisodeStructureCalculator

60분 한국 드라마 1화 구조를 분(minute) 단위로 계산.
EpisodePlanner(K값)와 FractalTopology를 결합하여 씬별 타임스탬프 배출.

LLM-0 원칙: generate() 호출 없음. 순수 수치 계산.

한국 드라마 60분 관례:
  - 콜드 오픈(Cold Open): 2~4분
  - 본편 3막 구조: ~54분
  - 예고편(Preview): 1~2분

인터페이스:
  EpisodeStructureCalculator.calculate(config) → EpisodeStructure
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from .episode_planner import EpisodePlan, EpisodePlanner
from .episode_state import ActPosition, NarrativeStateTensor, SeriesConfig

# ── 씬 타입 ─────────────────────────────────────────────────────

class SceneRole(str, Enum):
    COLD_OPEN    = "cold_open"       # 콜드 오픈 (훅)
    SETUP        = "setup"           # 도입
    RISING       = "rising"          # 상승
    CLIMAX       = "climax"          # 클라이맥스
    RESOLUTION   = "resolution"      # 해소
    DENOUEMENT   = "denouement"      # 결말 여운
    PREVIEW      = "preview"         # 예고편


# ── 데이터 모델 ──────────────────────────────────────────────────

@dataclass
class SceneSlot:
    """개별 씬 타임슬롯."""
    scene_idx: int
    microplot_idx: int              # 속한 미시 플롯 인덱스
    start_min: float                # 시작 분
    end_min: float                  # 종료 분
    duration_min: float             # 지속 시간(분)
    role: SceneRole
    act_position: ActPosition
    reveal_budget: float            # 해당 씬의 reveal 예산
    emotional_target: float         # 감정 목표 (0~1)
    conflict_weight: float          # 갈등 강도 (0~1)
    slot_function: str              # "introduction", "confrontation" 등
    is_critical: bool = False       # 클라이맥스·반전 씬 여부

    @property
    def duration_sec(self) -> float:
        return self.duration_min * 60.0

    def to_dict(self) -> dict:
        return {
            "scene_idx": self.scene_idx,
            "microplot_idx": self.microplot_idx,
            "start_min": round(self.start_min, 2),
            "end_min": round(self.end_min, 2),
            "duration_min": round(self.duration_min, 2),
            "role": self.role.value,
            "act_position": self.act_position.value,
            "slot_function": self.slot_function,
            "reveal_budget": self.reveal_budget,
            "emotional_target": self.emotional_target,
            "conflict_weight": self.conflict_weight,
            "is_critical": self.is_critical,
        }


@dataclass
class ActSegment:
    """막(Act) 단위 세그먼트."""
    act_position: ActPosition
    start_min: float
    end_min: float
    scene_count: int
    microplot_count: int

    @property
    def duration_min(self) -> float:
        return self.end_min - self.start_min


@dataclass
class EpisodeStructure:
    """
    EpisodeStructureCalculator.calculate()의 최종 출력.

    60분 1화 완성 구조 — 씬 슬롯 배열 + 막별 세그먼트 + 요약 통계
    """
    episode_idx: int
    runtime_min: float
    microplot_count: int           # K
    total_scene_count: int
    cold_open_min: float
    preview_min: float
    main_content_min: float

    scenes: List[SceneSlot] = field(default_factory=list)
    acts: List[ActSegment] = field(default_factory=list)
    plan: Optional[EpisodePlan] = None

    # 통계
    avg_scene_duration_min: float = 0.0
    critical_scene_count: int = 0
    reveal_budget_total: float = 0.0

    @property
    def pass_60min_constraint(self) -> bool:
        """총 런타임이 허용 범위(55~65분) 내에 있는지."""
        return 55.0 <= self.runtime_min <= 65.0

    @property
    def scene_count_by_act(self) -> Dict[str, int]:
        counts: Dict[str, int] = {}
        for sc in self.scenes:
            key = sc.act_position.value
            counts[key] = counts.get(key, 0) + 1
        return counts

    def to_dict(self) -> dict:
        return {
            "episode_idx": self.episode_idx,
            "runtime_min": self.runtime_min,
            "microplot_count": self.microplot_count,
            "total_scene_count": self.total_scene_count,
            "cold_open_min": self.cold_open_min,
            "preview_min": self.preview_min,
            "main_content_min": self.main_content_min,
            "avg_scene_duration_min": self.avg_scene_duration_min,
            "critical_scene_count": self.critical_scene_count,
            "reveal_budget_total": round(self.reveal_budget_total, 4),
            "pass_60min_constraint": self.pass_60min_constraint,
            "scene_count_by_act": self.scene_count_by_act,
            "acts": [
                {
                    "act_position": a.act_position.value,
                    "start_min": round(a.start_min, 2),
                    "end_min": round(a.end_min, 2),
                    "duration_min": round(a.duration_min, 2),
                    "scene_count": a.scene_count,
                }
                for a in self.acts
            ],
            "scenes": [sc.to_dict() for sc in self.scenes],
        }


# ── 설정 ─────────────────────────────────────────────────────────

@dataclass
class EpisodeStructureConfig:
    """EpisodeStructureCalculator 입력 설정."""
    episode_idx: int = 0
    total_episodes: int = 16
    runtime_min: float = 60.0
    act_structure: str = "5act"         # "5act" | "3act"

    # 콜드 오픈 / 예고편 길이
    cold_open_min: float = 3.0          # 한국 드라마 관례: 2~4분
    preview_min: float = 1.5            # 예고편: 1~2분

    # 씬 길이 파라미터 (분)
    min_scene_min: float = 2.0
    max_scene_min: float = 8.0
    target_scene_min: float = 4.0      # 기본 씬 목표 길이

    # NarrativeStateTensor 기본값 (외부 주입 가능)
    initial_narrative_state: Optional[NarrativeStateTensor] = None

    def make_series_config(self) -> SeriesConfig:
        return SeriesConfig(
            title=f"Episode{self.episode_idx:02d}",
            total_episodes=self.total_episodes,
            runtime_minutes=int(self.runtime_min),
            act_structure=self.act_structure,
        )

    def make_narrative_state(self) -> NarrativeStateTensor:
        if self.initial_narrative_state is not None:
            return self.initial_narrative_state
        # 기본값: 중간 상태 (에피소드 위치 반영)
        pos = self.episode_idx / max(1, self.total_episodes - 1)
        # remaining_reveal_budget = total - used (property)
        # → used_reveal_budget = total * (1 - desired_remaining)
        desired_remaining = max(0.05, 1.0 - pos * 0.85)
        used = 1.0 - desired_remaining
        state = NarrativeStateTensor(
            total_episodes=self.total_episodes,
            total_reveal_budget=1.0,
            used_reveal_budget=used,
            active_characters=["A", "B", "C"],          # 기본 3인
            conflict_pressure=0.3 + 0.4 * pos,
            avg_emotional_momentum=0.4 + 0.3 * pos,
            scene_energy_required=0.5,
            avg_curiosity_gradient=0.5 + 0.2 * pos,
        )
        # current_episode_idx = len(episodes) → episode_idx개의 더미 에피소드 추가
        from literary_system.episode.episode_state import ActPosition, EpisodeState
        for i in range(self.episode_idx):
            state.episodes.append(EpisodeState(
                episode_idx=i,
                act_position=ActPosition.SETUP,
                microplot_slots=[],
            ))
        return state


# ── 메인 계산기 ──────────────────────────────────────────────────

class EpisodeStructureCalculator:
    """
    V482 — 60분 한국 드라마 에피소드 구조 계산기.

    1. EpisodePlanner로 K(미시 플롯 수) 산출
    2. 60분 타임라인을 콜드 오픈 + 본편(K 미시 플롯) + 예고편으로 분할
    3. 각 미시 플롯을 씬 슬롯 배열로 전개
    4. EpisodeStructure 반환

    LLM-0 원칙: LLM generate() 호출 없음.
    """

    # 막별 시간 비율 (5막 기준, 합산 1.0)
    ACT_TIME_RATIOS_5ACT: Dict[str, float] = {
        "SETUP":     0.15,
        "PRESSURE":  0.25,
        "COLLISION": 0.30,
        "REVERSAL":  0.20,
        "RESIDUE":   0.10,
    }

    # 3막 비율
    ACT_TIME_RATIOS_3ACT: Dict[str, float] = {
        "SETUP":     0.25,
        "COLLISION": 0.50,
        "RESIDUE":   0.25,
    }

    # 막→SceneRole 매핑
    ACT_TO_ROLE: Dict[str, SceneRole] = {
        "SETUP":     SceneRole.SETUP,
        "PRESSURE":  SceneRole.RISING,
        "COLLISION": SceneRole.CLIMAX,
        "REVERSAL":  SceneRole.RESOLUTION,
        "RESIDUE":   SceneRole.DENOUEMENT,
    }

    def __init__(self, planner: Optional[EpisodePlanner] = None) -> None:
        self._planner = planner or EpisodePlanner()

    def calculate(self, config: EpisodeStructureConfig) -> EpisodeStructure:
        """60분 에피소드 구조 계산."""
        series_config = config.make_series_config()
        narrative_state = config.make_narrative_state()

        # Step 1: EpisodePlanner로 K + 막 정보 산출
        plan = self._planner.plan(series_config, config.episode_idx, narrative_state)

        # Step 2: 타임라인 분배
        main_content_min = (
            config.runtime_min - config.cold_open_min - config.preview_min
        )
        main_content_min = max(10.0, main_content_min)  # 최소 10분 보장

        # Step 3: 막별 시간 분배
        act_ratios = (
            self.ACT_TIME_RATIOS_5ACT
            if config.act_structure == "5act"
            else self.ACT_TIME_RATIOS_3ACT
        )

        # Step 4: 씬 슬롯 생성
        scenes: List[SceneSlot] = []
        acts: List[ActSegment] = []
        scene_idx = 0

        # 콜드 오픈 씬
        cold_scene = SceneSlot(
            scene_idx=scene_idx,
            microplot_idx=-1,
            start_min=0.0,
            end_min=config.cold_open_min,
            duration_min=config.cold_open_min,
            role=SceneRole.COLD_OPEN,
            act_position=ActPosition.SETUP,
            reveal_budget=plan.reveal_budget_per_slot * 0.5,
            emotional_target=plan.emotional_targets[0] if plan.emotional_targets else 0.3,
            conflict_weight=0.1,
            slot_function="hook",
            is_critical=True,
        )
        scenes.append(cold_scene)
        scene_idx += 1

        # 본편 막별 씬 배치
        current_min = config.cold_open_min
        act_positions = self._get_act_positions(config.act_structure)

        for act_idx, act_pos_val in enumerate(act_positions):
            act_ratio = act_ratios.get(act_pos_val, 0.2)
            act_duration = main_content_min * act_ratio
            act_start = current_min

            # 이 막에 속하는 미시 플롯 수
            mp_in_act = self._microplots_in_act(act_pos_val, plan, len(act_positions))
            if mp_in_act == 0:
                current_min += act_duration
                continue

            time_per_mp = act_duration / mp_in_act
            act_scene_count = 0

            for mp_offset in range(mp_in_act):
                mp_idx = sum(
                    self._microplots_in_act(act_positions[i], plan, len(act_positions))
                    for i in range(act_idx)
                ) + mp_offset

                mp_start = current_min
                mp_end = current_min + time_per_mp

                # 씬 수 계산
                scenes_in_mp = max(1, round(time_per_mp / config.target_scene_min))
                scene_dur = time_per_mp / scenes_in_mp

                # 씬 길이 클램프
                scene_dur = max(config.min_scene_min, min(config.max_scene_min, scene_dur))

                # 씬 생성
                act_position_enum = ActPosition(act_pos_val)
                role = self.ACT_TO_ROLE.get(act_pos_val, SceneRole.SETUP)

                # 막 내 감정/갈등 값 가져오기
                et = plan.emotional_targets[mp_idx % len(plan.emotional_targets)] if plan.emotional_targets else 0.5
                cw = plan.conflict_weights[mp_idx % len(plan.conflict_weights)] if plan.conflict_weights else 0.5
                sf = plan.slot_functions[mp_idx % len(plan.slot_functions)] if plan.slot_functions else "generic"

                for sc_offset in range(scenes_in_mp):
                    sc_start = current_min + sc_offset * scene_dur
                    sc_end = min(sc_start + scene_dur, mp_end)
                    is_critical = (
                        act_pos_val in ("COLLISION", "REVERSAL")
                        and sc_offset == scenes_in_mp - 1
                    )
                    scenes.append(SceneSlot(
                        scene_idx=scene_idx,
                        microplot_idx=mp_idx,
                        start_min=sc_start,
                        end_min=sc_end,
                        duration_min=sc_end - sc_start,
                        role=role,
                        act_position=act_position_enum,
                        reveal_budget=plan.reveal_budget_per_slot,
                        emotional_target=et,
                        conflict_weight=cw,
                        slot_function=sf,
                        is_critical=is_critical,
                    ))
                    scene_idx += 1
                    act_scene_count += 1

                current_min = mp_end

            acts.append(ActSegment(
                act_position=ActPosition(act_pos_val),
                start_min=act_start,
                end_min=current_min,
                scene_count=act_scene_count,
                microplot_count=mp_in_act,
            ))

        # 예고편 씬
        preview_start = current_min
        preview_end = preview_start + config.preview_min
        scenes.append(SceneSlot(
            scene_idx=scene_idx,
            microplot_idx=-2,
            start_min=preview_start,
            end_min=preview_end,
            duration_min=config.preview_min,
            role=SceneRole.PREVIEW,
            act_position=ActPosition.RESIDUE,
            reveal_budget=0.0,
            emotional_target=0.0,
            conflict_weight=0.0,
            slot_function="preview",
            is_critical=False,
        ))

        # 통계
        main_scenes = [s for s in scenes if s.role not in (SceneRole.COLD_OPEN, SceneRole.PREVIEW)]
        avg_dur = (
            sum(s.duration_min for s in main_scenes) / len(main_scenes)
            if main_scenes else 0.0
        )
        critical_count = sum(1 for s in scenes if s.is_critical)
        reveal_total = sum(s.reveal_budget for s in main_scenes)

        total_runtime = preview_end if scenes else config.runtime_min

        return EpisodeStructure(
            episode_idx=config.episode_idx,
            runtime_min=round(total_runtime, 2),
            microplot_count=plan.microplot_count,
            total_scene_count=len(scenes),
            cold_open_min=config.cold_open_min,
            preview_min=config.preview_min,
            main_content_min=round(main_content_min, 2),
            scenes=scenes,
            acts=acts,
            plan=plan,
            avg_scene_duration_min=round(avg_dur, 3),
            critical_scene_count=critical_count,
            reveal_budget_total=round(reveal_total, 4),
        )

    # ── 내부 헬퍼 ────────────────────────────────────────────────

    def _get_act_positions(self, act_structure: str) -> List[str]:
        if act_structure == "5act":
            return ["SETUP", "PRESSURE", "COLLISION", "REVERSAL", "RESIDUE"]
        return ["SETUP", "COLLISION", "RESIDUE"]

    def _microplots_in_act(
        self, act_pos_val: str, plan: EpisodePlan, n_acts: int
    ) -> int:
        """막별 미시 플롯 수 분배 (plan.microplot_count를 비율로 분할)."""
        K = plan.microplot_count
        # 비율 맵 (5막 기준)
        weight_5 = {
            "SETUP": 0.15, "PRESSURE": 0.25, "COLLISION": 0.30,
            "REVERSAL": 0.20, "RESIDUE": 0.10,
        }
        weight_3 = {"SETUP": 0.25, "COLLISION": 0.50, "RESIDUE": 0.25}
        weights = weight_5 if n_acts == 5 else weight_3
        w = weights.get(act_pos_val, 1.0 / n_acts)
        return max(1, round(K * w))
