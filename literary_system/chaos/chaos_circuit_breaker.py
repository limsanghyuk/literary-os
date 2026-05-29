"""
literary_system.chaos.chaos_circuit_breaker
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V727 — ChaosCircuitBreaker: Chaos + AgentCircuitBreaker 통합 (ADR-188)
G32 준수: print() 금지
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import List, Optional

from literary_system.chaos.chaos_engine import ChaosEngine, FaultSpec, FaultType
from literary_system.agents.circuit_breaker import (
    AgentCircuitBreaker, CircuitBreakerConfig, CircuitState,
)


def _raise_chaos_error() -> None:
    raise RuntimeError("chaos fault injected")


@dataclass
class CircuitChaosRecord:
    """Chaos 주입 + CircuitBreaker 상태 기록."""
    fault_id:     str
    injected:     bool
    state_before: str
    state_after:  str


class ChaosCircuitBreaker:
    """
    Chaos 장애 주입 후 AgentCircuitBreaker 상태 변화를 검증하는 통합 도구.

    Usage::

        config = CircuitBreakerConfig(failure_threshold=3)
        cb = AgentCircuitBreaker("test", config)
        engine = ChaosEngine()
        chaos_cb = ChaosCircuitBreaker(cb, engine)
        chaos_cb.register_fault("crash", FaultType.SERVICE_CRASH, "svc")
        record = chaos_cb.inject_and_fail("crash", n_failures=3)
    """

    def __init__(self, circuit_breaker: AgentCircuitBreaker, engine: ChaosEngine) -> None:
        self._cb      = circuit_breaker
        self._engine  = engine
        self._records: List[CircuitChaosRecord] = []

    def register_fault(
        self,
        fault_id: str,
        fault_type: FaultType,
        target: str,
        *,
        duration_ms: int = 0,
    ) -> None:
        spec = FaultSpec(fault_id, fault_type, target, duration_ms=duration_ms)
        self._engine.register(spec)
        self._engine.activate(fault_id)

    def inject_and_fail(self, fault_id: str, n_failures: int = 1) -> CircuitChaosRecord:
        """장애 주입 후 n_failures번 실패를 CircuitBreaker에 보고."""
        state_before = self._cb.state.value
        result = self._engine.inject(fault_id)
        for _ in range(n_failures):
            try:
                self._cb.call(_raise_chaos_error)
            except Exception:
                pass
        state_after = self._cb.state.value
        record = CircuitChaosRecord(
            fault_id=fault_id,
            injected=result.injected,
            state_before=state_before,
            state_after=state_after,
        )
        self._records.append(record)
        return record

    def reset_circuit(self) -> None:
        self._cb.reset()

    def records(self) -> List[CircuitChaosRecord]:
        return list(self._records)

    def opened_count(self) -> int:
        return sum(1 for r in self._records if r.state_after == CircuitState.OPEN.value)
