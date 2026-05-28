"""V704 — AgentCircuitBreaker (SP-D.2) ADR-166: 에이전트 장애 차단기."""
from __future__ import annotations
import time, logging
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitState(Enum):
    CLOSED = "closed"       # 정상: 요청 통과
    OPEN = "open"           # 장애: 요청 차단
    HALF_OPEN = "half_open" # 복구 시도: 1개 통과


@dataclass
class CircuitStats:
    total_calls: int = 0
    success_calls: int = 0
    failure_calls: int = 0
    rejected_calls: int = 0
    state_changes: int = 0

    def failure_rate(self) -> float:
        if self.total_calls == 0:
            return 0.0
        return self.failure_calls / self.total_calls


class CircuitBreakerError(Exception):
    """회로 차단 시 발생."""


@dataclass
class CircuitBreakerConfig:
    failure_threshold: int = 5          # 연속 실패 → OPEN
    success_threshold: int = 2          # HALF_OPEN에서 연속 성공 → CLOSED
    timeout_seconds: float = 30.0       # OPEN 유지 시간 → HALF_OPEN 전환
    min_calls: int = 1                  # 통계 최소 호출 수


class AgentCircuitBreaker:
    """에이전트 호출 회로 차단기.

    ADR-166: CLOSED→OPEN→HALF_OPEN→CLOSED 상태 전이.
    - CLOSED: 정상 동작, 실패 카운팅
    - OPEN: 즉시 CircuitBreakerError 발생 (fast-fail)
    - HALF_OPEN: 테스트 요청 1개 허용, 성공 시 CLOSED 복구
    """

    def __init__(self, name: str = "default",
                 config: Optional[CircuitBreakerConfig] = None) -> None:
        self.name = name
        self._config = config or CircuitBreakerConfig()
        self._state = CircuitState.CLOSED
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_failure_time: Optional[float] = None
        self._stats = CircuitStats()
        self._hooks: Dict[str, List[Callable]] = {}

    # ── 상태 전이 ─────────────────────────────────────────────────────

    @property
    def state(self) -> CircuitState:
        if self._state == CircuitState.OPEN:
            # OPEN → HALF_OPEN 자동 전환
            if (self._last_failure_time is not None and
                    time.time() - self._last_failure_time >= self._config.timeout_seconds):
                self._transition(CircuitState.HALF_OPEN)
        return self._state

    def _transition(self, new_state: CircuitState) -> None:
        if self._state != new_state:
            old = self._state
            self._state = new_state
            self._stats.state_changes += 1
            logger.info("[CB:%s] %s → %s", self.name, old.value, new_state.value)
            self._fire("state_changed", {"from": old, "to": new_state})

    # ── 호출 인터페이스 ───────────────────────────────────────────────

    def call(self, fn: Callable[[], T]) -> T:
        """보호된 함수 호출."""
        current = self.state  # property로 OPEN→HALF_OPEN 자동 체크

        if current == CircuitState.OPEN:
            self._stats.rejected_calls += 1
            raise CircuitBreakerError(
                f"Circuit '{self.name}' is OPEN — request rejected"
            )

        self._stats.total_calls += 1
        try:
            result = fn()
            self._on_success()
            return result
        except CircuitBreakerError:
            raise
        except Exception as exc:
            self._on_failure()
            raise

    def _on_success(self) -> None:
        self._stats.success_calls += 1
        self._consecutive_failures = 0
        if self._state == CircuitState.HALF_OPEN:
            self._consecutive_successes += 1
            if self._consecutive_successes >= self._config.success_threshold:
                self._consecutive_successes = 0
                self._transition(CircuitState.CLOSED)
        self._fire("success", None)

    def _on_failure(self) -> None:
        self._stats.failure_calls += 1
        self._consecutive_failures += 1
        self._last_failure_time = time.time()
        if self._state == CircuitState.HALF_OPEN:
            # 복구 실패 → 다시 OPEN
            self._consecutive_successes = 0
            self._transition(CircuitState.OPEN)
        elif (self._state == CircuitState.CLOSED and
              self._consecutive_failures >= self._config.failure_threshold):
            self._transition(CircuitState.OPEN)
        self._fire("failure", None)

    # ── 수동 제어 ─────────────────────────────────────────────────────

    def reset(self) -> None:
        """강제 CLOSED 복구."""
        self._consecutive_failures = 0
        self._consecutive_successes = 0
        self._last_failure_time = None
        self._transition(CircuitState.CLOSED)

    def trip(self) -> None:
        """강제 OPEN."""
        self._last_failure_time = time.time()
        self._transition(CircuitState.OPEN)

    # ── 훅·조회 ──────────────────────────────────────────────────────

    def on(self, event: str, cb: Callable) -> None:
        self._hooks.setdefault(event, []).append(cb)

    def _fire(self, event: str, payload: Any) -> None:
        for cb in self._hooks.get(event, []):
            try:
                cb(payload)
            except Exception as exc:
                logger.warning("[CB] hook error: %s", exc)

    def stats(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "state": self.state.value,
            "total_calls": self._stats.total_calls,
            "success_calls": self._stats.success_calls,
            "failure_calls": self._stats.failure_calls,
            "rejected_calls": self._stats.rejected_calls,
            "state_changes": self._stats.state_changes,
            "failure_rate": self._stats.failure_rate(),
        }

    def is_closed(self) -> bool:
        return self.state == CircuitState.CLOSED

    def is_open(self) -> bool:
        return self.state == CircuitState.OPEN

    def is_half_open(self) -> bool:
        return self.state == CircuitState.HALF_OPEN


ADR_166 = {
    "id": "ADR-166",
    "title": "AgentCircuitBreaker",
    "status": "accepted",
    "decision": (
        "CLOSED→OPEN→HALF_OPEN→CLOSED 상태 전이. "
        "연속 실패 임계값 초과 시 OPEN(fast-fail). "
        "timeout 후 HALF_OPEN에서 복구 시도."
    ),
    "version": "V704",
}
