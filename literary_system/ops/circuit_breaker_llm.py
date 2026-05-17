"""
literary_system/ops/circuit_breaker_llm.py
V475 — LLM 어댑터 전용 CircuitBreaker (ADR-015, Phase 3 v2)

3상태 자동기계:
  CLOSED  → 정상 운전
  OPEN    → 차단 (recovery_timeout 후 HALF_OPEN 전환)
  HALF_OPEN → 프로브 시도, 성공 시 CLOSED / 실패 시 OPEN

설계 결정 (v2):
  - 기본 recovery_timeout = 60s
  - LLM 외부 의존 시 llm_recovery_timeout = 120s
  - fail_rate_threshold = 0.5 (50% 실패율)
  - min_calls = 5 (통계 최소 샘플)

LLM-0 준수: 순수 상태 머신, 외부 의존 없음
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, List, Optional, TypeVar

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED    = auto()   # 정상
    OPEN      = auto()   # 차단
    HALF_OPEN = auto()   # 프로브


@dataclass
class CircuitBreakerEvent:
    timestamp: float
    state_from: CircuitState
    state_to:   CircuitState
    reason:     str


class CircuitBreakerOpenError(Exception):
    """Circuit이 OPEN 상태일 때 호출 시 발생."""
    pass


class CircuitBreaker:
    """
    LLM 어댑터 전용 3상태 CircuitBreaker.

    사용 예:
        cb = CircuitBreaker(name="claude")
        result = cb.call(lambda: adapter.predict(ctx))
    """

    def __init__(
        self,
        name: str = "default",
        fail_rate_threshold: float = 0.5,
        min_calls: int = 5,
        recovery_timeout_s: float = 60.0,
        llm_recovery_timeout_s: float = 120.0,
        is_llm_dependent: bool = False,
        clock_fn: Optional[Callable[[], float]] = None,
    ) -> None:
        self.name = name
        self.fail_rate_threshold   = fail_rate_threshold
        self.min_calls             = min_calls
        self.recovery_timeout_s    = recovery_timeout_s
        self.llm_recovery_timeout_s = llm_recovery_timeout_s
        self.is_llm_dependent      = is_llm_dependent
        self._clock                = clock_fn or time.time

        self._state        = CircuitState.CLOSED
        self._call_count   = 0
        self._fail_count   = 0
        self._open_time: Optional[float] = None
        self._history: List[CircuitBreakerEvent] = []
        self._lock = threading.Lock()

    # ── 상태 조회 ────────────────────────────────────────────

    def get_state(self) -> CircuitState:
        with self._lock:
            self._maybe_transition_to_half_open()
            return self._state

    def get_state_name(self) -> str:
        return self.get_state().name

    def fail_rate(self) -> float:
        with self._lock:
            if self._call_count == 0:
                return 0.0
            return self._fail_count / self._call_count

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "name":        self.name,
                "state":       self._state.name,
                "call_count":  self._call_count,
                "fail_count":  self._fail_count,
                "fail_rate":   round(self._fail_count / max(self._call_count, 1), 4),
                "events":      len(self._history),
            }

    # ── 호출 진입점 ──────────────────────────────────────────

    def call(self, fn: Callable[[], T]) -> T:
        """
        fn을 Circuit 보호 하에 실행.
        OPEN 상태이면 CircuitBreakerOpenError 발생.
        """
        with self._lock:
            self._maybe_transition_to_half_open()
            state = self._state

        if state == CircuitState.OPEN:
            raise CircuitBreakerOpenError(
                f"CircuitBreaker '{self.name}' OPEN — 호출 차단"
            )

        try:
            result = fn()
            self._on_success()
            return result
        except CircuitBreakerOpenError:
            raise
        except Exception as exc:
            self._on_failure()
            raise

    # ── 내부 상태 전환 ───────────────────────────────────────

    def _maybe_transition_to_half_open(self) -> None:
        """OPEN → HALF_OPEN 전환 확인 (lock 보유 상태에서 호출)."""
        if self._state != CircuitState.OPEN:
            return
        timeout = (
            self.llm_recovery_timeout_s
            if self.is_llm_dependent
            else self.recovery_timeout_s
        )
        if self._open_time is not None and \
                (self._clock() - self._open_time) >= timeout:
            self._transition(CircuitState.HALF_OPEN, "recovery_timeout")

    def _on_success(self) -> None:
        with self._lock:
            self._call_count += 1
            if self._state == CircuitState.HALF_OPEN:
                self._transition(CircuitState.CLOSED, "probe_success")
                self._reset_counters()

    def _on_failure(self) -> None:
        with self._lock:
            self._call_count += 1
            self._fail_count += 1
            if self._state == CircuitState.HALF_OPEN:
                self._transition(CircuitState.OPEN, "probe_failure")
                self._open_time = self._clock()
            elif self._state == CircuitState.CLOSED:
                if self._call_count >= self.min_calls and \
                        self._fail_count / self._call_count >= self.fail_rate_threshold:
                    self._transition(CircuitState.OPEN, "fail_rate_exceeded")
                    self._open_time = self._clock()

    def _transition(self, to: CircuitState, reason: str) -> None:
        evt = CircuitBreakerEvent(
            timestamp=self._clock(),
            state_from=self._state,
            state_to=to,
            reason=reason,
        )
        self._history.append(evt)
        self._state = to

    def _reset_counters(self) -> None:
        self._call_count = 0
        self._fail_count = 0
        self._open_time  = None

    # ── 수동 제어 ────────────────────────────────────────────

    def force_open(self) -> None:
        with self._lock:
            self._transition(CircuitState.OPEN, "force_open")
            self._open_time = self._clock()

    def force_close(self) -> None:
        with self._lock:
            self._transition(CircuitState.CLOSED, "force_close")
            self._reset_counters()

    def reset(self) -> None:
        """완전 초기화."""
        with self._lock:
            self._state      = CircuitState.CLOSED
            self._call_count = 0
            self._fail_count = 0
            self._open_time  = None
            self._history.clear()

    def event_history(self) -> List[CircuitBreakerEvent]:
        with self._lock:
            return list(self._history)
