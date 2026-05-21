"""ADR-050 | V589 | L1 — BackendHealthMonitor: DB 백엔드 가용성 모니터.

SP-A.2:
- AvailabilityState: FULL / PARTIAL_DEGRADED / CRITICAL / OFFLINE
- 30초 ping 간격 + Circuit Breaker per backend
- QueryInterface 폴백 로직 지원 (T1~T4 시나리오)

LLM-0 원칙: 외부 LLM 호출 없음.
"""
from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional

from literary_system.db.schema_registry import BackendType

logger = logging.getLogger(__name__)


class AvailabilityState(str, Enum):
    FULL             = "FULL"
    PARTIAL_DEGRADED = "PARTIAL_DEGRADED"
    CRITICAL         = "CRITICAL"
    OFFLINE          = "OFFLINE"


class BackendCircuitState(str, Enum):
    CLOSED    = "CLOSED"
    OPEN      = "OPEN"
    HALF_OPEN = "HALF_OPEN"


@dataclass
class BackendHealthRecord:
    backend: BackendType
    circuit_state: BackendCircuitState = BackendCircuitState.CLOSED
    consecutive_failures: int = 0
    total_checks: int = 0
    total_failures: int = 0
    last_check_time: float = 0.0
    last_failure_time: float = 0.0
    last_error: str = ""
    failure_threshold: int = 3
    recovery_timeout_sec: float = 60.0

    def is_available(self) -> bool:
        return self.circuit_state in (BackendCircuitState.CLOSED, BackendCircuitState.HALF_OPEN)

    def record_success(self) -> None:
        self.total_checks += 1
        self.consecutive_failures = 0
        self.circuit_state = BackendCircuitState.CLOSED
        self.last_check_time = time.monotonic()

    def record_failure(self, error: str = "") -> None:
        self.total_checks += 1
        self.total_failures += 1
        self.consecutive_failures += 1
        self.last_failure_time = time.monotonic()
        self.last_check_time = time.monotonic()
        self.last_error = error
        if self.consecutive_failures >= self.failure_threshold:
            if self.circuit_state != BackendCircuitState.OPEN:
                logger.warning(
                    "BackendHealthMonitor: %s Circuit OPEN (연속 %d회 실패)",
                    self.backend.value, self.consecutive_failures,
                )
            self.circuit_state = BackendCircuitState.OPEN

    def try_recover(self) -> bool:
        if self.circuit_state == BackendCircuitState.OPEN:
            elapsed = time.monotonic() - self.last_failure_time
            if elapsed >= self.recovery_timeout_sec:
                self.circuit_state = BackendCircuitState.HALF_OPEN
                logger.info(
                    "BackendHealthMonitor: %s Circuit HALF_OPEN (%.1fs 경과)",
                    self.backend.value, elapsed,
                )
                return True
        return False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "backend": self.backend.value,
            "circuit_state": self.circuit_state.value,
            "consecutive_failures": self.consecutive_failures,
            "total_checks": self.total_checks,
            "total_failures": self.total_failures,
            "last_error": self.last_error,
            "available": self.is_available(),
        }


class BackendHealthMonitor:
    """DB 백엔드 가용성 모니터 (ADR-050).

    - ping_interval_sec (기본 30s) 간격으로 연결 상태 캐시
    - backend 별 Circuit Breaker: 3회 연속 실패 → OPEN → 60s 후 HALF_OPEN
    - overall_state() → AvailabilityState
    - get_available_backends() → 쿼리 가능 BackendType 목록
    """

    PING_INTERVAL_SEC: float = 30.0

    def __init__(
        self,
        ping_interval_sec: float = PING_INTERVAL_SEC,
        failure_threshold: int = 3,
        recovery_timeout_sec: float = 60.0,
    ) -> None:
        self._ping_interval = ping_interval_sec
        self._failure_threshold = failure_threshold
        self._recovery_timeout = recovery_timeout_sec
        self._records: Dict[BackendType, BackendHealthRecord] = {}
        self._ping_funcs: Dict[BackendType, Callable[[], bool]] = {}
        logger.debug(
            "BackendHealthMonitor 초기화 — ping=%.0fs threshold=%d recovery=%.0fs",
            self._ping_interval, self._failure_threshold, self._recovery_timeout,
        )

    def register(
        self,
        backend: BackendType,
        ping_fn: Optional[Callable[[], bool]] = None,
    ) -> None:
        self._records[backend] = BackendHealthRecord(
            backend=backend,
            failure_threshold=self._failure_threshold,
            recovery_timeout_sec=self._recovery_timeout,
        )
        self._ping_funcs[backend] = ping_fn or (lambda: True)
        logger.debug("BackendHealthMonitor: %s 등록", backend.value)

    def unregister(self, backend: BackendType) -> None:
        self._records.pop(backend, None)
        self._ping_funcs.pop(backend, None)

    def registered_backends(self) -> List[BackendType]:
        return list(self._records.keys())

    def check(self, backend: BackendType) -> BackendCircuitState:
        if backend not in self._records:
            return BackendCircuitState.OPEN
        rec = self._records[backend]
        rec.try_recover()
        now = time.monotonic()
        if (now - rec.last_check_time) < self._ping_interval and rec.total_checks > 0:
            return rec.circuit_state
        try:
            ok = self._ping_funcs[backend]()
            if ok:
                rec.record_success()
            else:
                rec.record_failure("ping returned False")
        except Exception as exc:
            rec.record_failure(str(exc))
            logger.warning("BackendHealthMonitor.check(%s) 예외: %s", backend.value, exc)
        return rec.circuit_state

    def check_all(self) -> Dict[BackendType, BackendCircuitState]:
        return {b: self.check(b) for b in self._records}

    def get_available_backends(self) -> List[BackendType]:
        result = []
        for backend, rec in self._records.items():
            rec.try_recover()
            if rec.is_available():
                result.append(backend)
        return result

    def overall_state(self) -> AvailabilityState:
        if not self._records:
            return AvailabilityState.OFFLINE
        total = len(self._records)
        available = len(self.get_available_backends())
        if available == total:
            return AvailabilityState.FULL
        elif available >= 2:
            return AvailabilityState.PARTIAL_DEGRADED
        elif available == 1:
            return AvailabilityState.CRITICAL
        else:
            return AvailabilityState.OFFLINE

    def health_report(self) -> Dict[str, Any]:
        state = self.overall_state()
        return {
            "overall_state": state.value,
            "available_backends": [b.value for b in self.get_available_backends()],
            "total_backends": len(self._records),
            "backends": {
                b.value: rec.to_dict()
                for b, rec in self._records.items()
            },
        }

    def force_open(self, backend: BackendType) -> None:
        """테스트용: Circuit 강제 OPEN."""
        if backend in self._records:
            rec = self._records[backend]
            rec.circuit_state = BackendCircuitState.OPEN
            rec.consecutive_failures = self._failure_threshold
            rec.last_failure_time = time.monotonic()

    def force_closed(self, backend: BackendType) -> None:
        """테스트용: Circuit 강제 CLOSED."""
        if backend in self._records:
            rec = self._records[backend]
            rec.circuit_state = BackendCircuitState.CLOSED
            rec.consecutive_failures = 0
