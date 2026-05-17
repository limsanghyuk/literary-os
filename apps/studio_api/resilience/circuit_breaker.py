"""
V420: Circuit Breaker — literary_system 코어 호출 보호.
상태: CLOSED → OPEN → HALF_OPEN → CLOSED
ADR-001: L4 → L2 경계 보호. 실패 시 degraded 응답 반환.
"""
from __future__ import annotations

import time
import threading
from enum import Enum
from typing import Callable, Any


class CBState(Enum):
    CLOSED = "closed"          # 정상: 모든 요청 통과
    OPEN = "open"              # 차단: 즉시 fallback 반환
    HALF_OPEN = "half_open"    # 탐침: 단일 요청으로 복구 여부 확인


class CircuitBreakerOpen(Exception):
    """Circuit이 OPEN 상태일 때 발생 — 호출자는 degraded 응답을 반환해야 함."""


class CircuitBreaker:
    """
    단일 백엔드 서비스에 대한 Circuit Breaker.

    Parameters
    ----------
    name:            식별자 (로깅/OTel용)
    failure_threshold: CLOSED → OPEN 전환 실패 횟수 (기본 5)
    recovery_timeout:  OPEN → HALF_OPEN 대기 시간 초 (기본 30)
    success_threshold: HALF_OPEN → CLOSED 전환 성공 횟수 (기본 2)
    """

    def __init__(
        self,
        name: str,
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        success_threshold: int = 2,
    ) -> None:
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self._state = CBState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time: float = 0.0
        self._lock = threading.Lock()

    # ── 공개 인터페이스 ──────────────────────────────────────

    @property
    def state(self) -> CBState:
        with self._lock:
            return self._evaluate_state()

    def call(self, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """
        fn(*args, **kwargs) 를 Circuit Breaker 보호 하에 실행.
        OPEN 상태이면 CircuitBreakerOpen 을 raise 한다.
        """
        with self._lock:
            state = self._evaluate_state()

            if state == CBState.OPEN:
                raise CircuitBreakerOpen(
                    f"[{self.name}] Circuit OPEN — "
                    f"recovery in {self._remaining_timeout():.1f}s"
                )

        try:
            result = fn(*args, **kwargs)
            self._on_success()
            return result
        except CircuitBreakerOpen:
            raise
        except Exception as exc:
            self._on_failure()
            raise exc

    def reset(self) -> None:
        """강제 CLOSED 리셋 (테스트/운영 복구용)."""
        with self._lock:
            self._state = CBState.CLOSED
            self._failure_count = 0
            self._success_count = 0

    def status(self) -> dict[str, Any]:
        """현재 상태를 딕셔너리로 반환 (OTel / health 엔드포인트용)."""
        with self._lock:
            state = self._evaluate_state()
            return {
                "name": self.name,
                "state": state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_threshold": self.failure_threshold,
                "remaining_timeout_s": (
                    round(self._remaining_timeout(), 1)
                    if state == CBState.OPEN else 0.0
                ),
            }

    # ── 내부 ────────────────────────────────────────────────

    def _evaluate_state(self) -> CBState:
        """락 보유 중에만 호출. OPEN → HALF_OPEN 자동 전환 처리."""
        if self._state == CBState.OPEN:
            if time.monotonic() - self._last_failure_time >= self.recovery_timeout:
                self._state = CBState.HALF_OPEN
                self._success_count = 0
        return self._state

    def _on_success(self) -> None:
        with self._lock:
            if self._state == CBState.HALF_OPEN:
                self._success_count += 1
                if self._success_count >= self.success_threshold:
                    self._state = CBState.CLOSED
                    self._failure_count = 0
            elif self._state == CBState.CLOSED:
                self._failure_count = max(0, self._failure_count - 1)

    def _on_failure(self) -> None:
        with self._lock:
            self._failure_count += 1
            self._last_failure_time = time.monotonic()
            if self._failure_count >= self.failure_threshold:
                self._state = CBState.OPEN
            elif self._state == CBState.HALF_OPEN:
                # HALF_OPEN 중 실패 → 다시 OPEN
                self._state = CBState.OPEN
                self._last_failure_time = time.monotonic()

    def _remaining_timeout(self) -> float:
        elapsed = time.monotonic() - self._last_failure_time
        return max(0.0, self.recovery_timeout - elapsed)


# ── 사전 구성 인스턴스 ────────────────────────────────────────
# literary_system 코어 모듈별 Circuit Breaker
drse_cb = CircuitBreaker("drse_engine", failure_threshold=5, recovery_timeout=30.0)
nkg_cb = CircuitBreaker("nkg_store", failure_threshold=5, recovery_timeout=30.0)
gate_cb = CircuitBreaker("endurance_gate", failure_threshold=3, recovery_timeout=60.0)
voice_cb = CircuitBreaker("voice_manifold", failure_threshold=5, recovery_timeout=30.0)
