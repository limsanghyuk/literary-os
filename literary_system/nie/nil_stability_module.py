"""
NILStabilityModule — V512
ADR-019: NIL 수렴 안정화 모듈

- 발산 감지  : |Δα| > 0.1 연속 3회 → LR × 0.5
- 진동 감지  : sign 교차 5회/10 epoch → EMA 강화
- 경계 응축  : α ∈ (0.30, 0.80) 내부 경계 접근 시 alarm
- get_effective_lr(): PhysicsRewardBridge / AMW 에서 호출
"""

from __future__ import annotations

import math
from collections import defaultdict, deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional


# ─── 상수 ─────────────────────────────────────────────────────────────────────
ALPHA_MIN: float = 0.30
ALPHA_MAX: float = 0.80

DIVERGE_THRESHOLD: float = 0.10       # |Δα| 임계값
DIVERGE_CONSECUTIVE: int = 3          # 연속 발산 횟수 임계값
LR_DIVERGE_FACTOR: float = 0.50       # 발산 시 LR 감소율

OSCILLATION_SIGN_CROSS: int = 5       # 부호 교차 횟수 임계값
OSCILLATION_WINDOW: int = 10          # epoch 창 크기
LR_OSC_FACTOR: float = 0.70           # 진동 시 LR 감소율

BOUNDARY_INNER_LOW: float = 0.305     # 하한 경계 근접 임계값 (α_min + 0.005)
BOUNDARY_INNER_HIGH: float = 0.795    # 상한 경계 근접 임계값 (α_max - 0.005)

ALARM_MAX_COUNT: int = 5              # 동일 이벤트 반복 alarm 최대 기록 수


# ─── 이벤트 타입 ──────────────────────────────────────────────────────────────
class StabilityEventType(Enum):
    DIVERGENCE = "DIVERGENCE"
    OSCILLATION = "OSCILLATION"
    BOUNDARY_LOW = "BOUNDARY_LOW"
    BOUNDARY_HIGH = "BOUNDARY_HIGH"
    NORMAL = "NORMAL"


@dataclass
class StabilityEvent:
    event_type: StabilityEventType
    dim: str
    alpha: float
    delta: float
    epoch: int
    lr_factor: float = 1.0           # 이 이벤트로 인한 LR 보정 계수

    @property
    def is_alarm(self) -> bool:
        return self.event_type != StabilityEventType.NORMAL


# ─── 차원별 상태 ──────────────────────────────────────────────────────────────
@dataclass
class _DimState:
    consecutive_diverge: int = 0
    delta_history: deque = field(default_factory=lambda: deque(maxlen=OSCILLATION_WINDOW))
    sign_cross_count: int = 0
    last_sign: Optional[int] = None                # +1 or -1
    lr_factor_diverge: float = 1.0                 # 발산 누적 LR 계수
    lr_factor_osc: float = 1.0                     # 진동 누적 LR 계수
    boundary_alarm_count: int = 0
    epoch: int = 0


# ─── NILStabilityModule ───────────────────────────────────────────────────────
class NILStabilityModule:
    """NIL 수렴 안정화 감지·제어 모듈 (V512, ADR-019)."""

    def __init__(self) -> None:
        self._states: Dict[str, _DimState] = defaultdict(_DimState)
        self._module_lr_scaling: Dict[str, float] = {}  # module → 종합 LR 계수
        self._events: List[StabilityEvent] = []

    # ── 외부 진입점 ──────────────────────────────────────────────────────────
    def update(self, dim: str, alpha_new: float, alpha_old: float) -> StabilityEvent:
        """
        α 변화를 기록하고 안정성 이벤트를 반환한다.
        AMW.update() 내부에서 매 α 갱신 시 호출.
        """
        state = self._states[dim]
        state.epoch += 1
        delta = alpha_new - alpha_old

        event = self._check_all(dim, state, alpha_new, delta)
        self._update_lr_scaling(dim, state)
        self._events.append(event)
        return event

    def get_effective_lr(self, module: str, base_lr: float) -> float:
        """
        PhysicsRewardBridge / AMW 가 호출 → 조정된 유효 LR 반환.
        module 에 해당하는 종합 계수를 곱한다.
        """
        factor = self._module_lr_scaling.get(module, 1.0)
        return base_lr * factor

    def set_module_lr_factor(self, module: str, factor: float) -> None:
        """외부(AgentCalibrator 등)에서 특정 모듈 LR 계수를 직접 설정."""
        self._module_lr_scaling[module] = max(0.05, min(factor, 1.0))

    def get_dim_lr_factor(self, dim: str) -> float:
        """AMW 가 차원별 LR 계수를 직접 조회할 때 사용."""
        state = self._states[dim]
        return state.lr_factor_diverge * state.lr_factor_osc

    def check_boundary(self, dim: str, alpha: float) -> Optional[StabilityEvent]:
        """
        경계 근접 여부만 독립 점검 (update()와 별도로 호출 가능).
        α 가 경계에 접근하면 BOUNDARY_LOW / BOUNDARY_HIGH 이벤트 반환.
        """
        state = self._states[dim]
        if alpha <= BOUNDARY_INNER_LOW:
            return self._make_boundary_event(dim, state, alpha, 0.0, StabilityEventType.BOUNDARY_LOW)
        if alpha >= BOUNDARY_INNER_HIGH:
            return self._make_boundary_event(dim, state, alpha, 0.0, StabilityEventType.BOUNDARY_HIGH)
        return None

    def reset_dim(self, dim: str) -> None:
        """특정 차원 상태 리셋 (MetaLearner 재시작 시 사용)."""
        self._states[dim] = _DimState()

    def reset_all(self) -> None:
        """전체 상태 리셋."""
        self._states.clear()
        self._module_lr_scaling.clear()
        self._events.clear()

    @property
    def events(self) -> List[StabilityEvent]:
        return list(self._events)

    def alarm_events(self) -> List[StabilityEvent]:
        return [e for e in self._events if e.is_alarm]

    # ── 내부 헬퍼 ────────────────────────────────────────────────────────────
    def _check_all(
        self, dim: str, state: _DimState, alpha: float, delta: float
    ) -> StabilityEvent:
        """발산 → 진동 → 경계 순으로 점검. 가장 중요한 이벤트 하나를 반환."""
        # 1) 발산 감지
        if self._check_divergence(state, delta):
            factor = state.lr_factor_diverge
            return StabilityEvent(
                StabilityEventType.DIVERGENCE, dim, alpha, delta, state.epoch, factor
            )
        # 2) 진동 감지
        if self._check_oscillation(state, delta):
            factor = state.lr_factor_osc
            return StabilityEvent(
                StabilityEventType.OSCILLATION, dim, alpha, delta, state.epoch, factor
            )
        # 3) 경계 응축 alarm
        boundary_evt = self.check_boundary(dim, alpha)
        if boundary_evt is not None:
            return boundary_evt
        # 4) 정상
        return StabilityEvent(StabilityEventType.NORMAL, dim, alpha, delta, state.epoch, 1.0)

    def _check_divergence(self, state: _DimState, delta: float) -> bool:
        """
        |Δα| > DIVERGE_THRESHOLD 연속 DIVERGE_CONSECUTIVE 회 → LR × 0.5.
        조건 충족 시 state.lr_factor_diverge 를 감소시키고 True 반환.
        """
        if abs(delta) > DIVERGE_THRESHOLD:
            state.consecutive_diverge += 1
        else:
            state.consecutive_diverge = 0

        if state.consecutive_diverge >= DIVERGE_CONSECUTIVE:
            state.lr_factor_diverge *= LR_DIVERGE_FACTOR
            state.lr_factor_diverge = max(state.lr_factor_diverge, 0.05)
            state.consecutive_diverge = 0          # 카운터 리셋(재발 감지)
            return True
        return False

    def _check_oscillation(self, state: _DimState, delta: float) -> bool:
        """
        sign(Δα) 교차가 OSCILLATION_SIGN_CROSS 회 / OSCILLATION_WINDOW epoch
        → EMA 강화(LR × 0.7). True 반환.
        """
        if delta == 0.0:
            state.delta_history.append(0)
            return False

        cur_sign = 1 if delta > 0 else -1
        if state.last_sign is not None and cur_sign != state.last_sign:
            state.sign_cross_count += 1
        state.last_sign = cur_sign
        state.delta_history.append(cur_sign)

        # 현재 창 내 sign 교차 수 재계산
        crosses_in_window = sum(
            1 for i in range(1, len(state.delta_history))
            if state.delta_history[i] != state.delta_history[i - 1]
            and state.delta_history[i] != 0 and state.delta_history[i - 1] != 0
        )

        if crosses_in_window >= OSCILLATION_SIGN_CROSS:
            state.lr_factor_osc *= LR_OSC_FACTOR
            state.lr_factor_osc = max(state.lr_factor_osc, 0.10)
            state.sign_cross_count = 0
            return True
        return False

    def _make_boundary_event(
        self,
        dim: str,
        state: _DimState,
        alpha: float,
        delta: float,
        evt_type: StabilityEventType,
    ) -> StabilityEvent:
        state.boundary_alarm_count = min(
            state.boundary_alarm_count + 1, ALARM_MAX_COUNT
        )
        return StabilityEvent(evt_type, dim, alpha, delta, state.epoch, 1.0)

    def _update_lr_scaling(self, dim: str, state: _DimState) -> None:
        """
        차원별 LR 계수를 종합해 module_lr_scaling["amw"] 에 반영.
        PhysicsRewardBridge 는 "physics" 키를 사용하므로 amw 와 별개.
        """
        combined = state.lr_factor_diverge * state.lr_factor_osc
        self._module_lr_scaling[f"amw_{dim}"] = combined
        # 전체 AMW 모듈 기준: 모든 차원 중 최솟값
        all_factors = [
            s.lr_factor_diverge * s.lr_factor_osc
            for s in self._states.values()
        ]
        if all_factors:
            self._module_lr_scaling["amw"] = min(all_factors)
