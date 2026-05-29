"""
literary_system.chaos.fault_injector
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V724 — FaultInjector: 타겟 함수에 장애를 주입하는 데코레이터/컨텍스트 (ADR-185).

G32 준수: print() 금지
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, TypeVar

from literary_system.chaos.chaos_engine import ChaosEngine, FaultSpec, FaultType

F = TypeVar("F", bound=Callable[..., Any])


class InjectionPoint(str, Enum):
    BEFORE = "before"   # 함수 실행 전 주입
    AFTER  = "after"    # 함수 실행 후 주입
    BOTH   = "both"     # 전후 모두


@dataclass
class InjectorRecord:
    """주입 이력."""
    target_fn: str
    point:     InjectionPoint
    fault_id:  str
    injected:  bool
    ts:        float = field(default_factory=time.time)


class FaultInjector:
    """
    특정 함수 호출 전후에 장애를 주입하는 인젝터.

    Usage::

        engine = ChaosEngine()
        spec = FaultSpec("crash-1", FaultType.SERVICE_CRASH, "svc", duration_ms=100)
        engine.register(spec); engine.activate("crash-1")

        injector = FaultInjector(engine)

        @injector.wrap(fault_id="crash-1", point=InjectionPoint.BEFORE)
        def my_service_call():
            return "result"

        my_service_call()   # 호출 전 장애 주입됨
    """

    def __init__(self, engine: ChaosEngine) -> None:
        self._engine = engine
        self._records: List[InjectorRecord] = []

    def wrap(
        self,
        fault_id: str,
        point: InjectionPoint = InjectionPoint.BEFORE,
    ) -> Callable[[F], F]:
        """데코레이터: 함수를 장애 주입 래퍼로 감싼다."""
        def decorator(fn: F) -> F:
            def wrapper(*args: Any, **kwargs: Any) -> Any:
                if point in (InjectionPoint.BEFORE, InjectionPoint.BOTH):
                    result = self._engine.inject(fault_id)
                    self._records.append(InjectorRecord(
                        target_fn=fn.__name__,
                        point=InjectionPoint.BEFORE,
                        fault_id=fault_id,
                        injected=result.injected,
                    ))
                ret = fn(*args, **kwargs)
                if point in (InjectionPoint.AFTER, InjectionPoint.BOTH):
                    result = self._engine.inject(fault_id)
                    self._records.append(InjectorRecord(
                        target_fn=fn.__name__,
                        point=InjectionPoint.AFTER,
                        fault_id=fault_id,
                        injected=result.injected,
                    ))
                return ret
            return wrapper  # type: ignore
        return decorator

    def inject_before(self, fault_id: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """함수 실행 전 장애 주입 후 함수 호출."""
        result = self._engine.inject(fault_id)
        self._records.append(InjectorRecord(
            target_fn=fn.__name__,
            point=InjectionPoint.BEFORE,
            fault_id=fault_id,
            injected=result.injected,
        ))
        return fn(*args, **kwargs)

    def inject_after(self, fault_id: str, fn: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """함수 실행 후 장애 주입."""
        ret = fn(*args, **kwargs)
        result = self._engine.inject(fault_id)
        self._records.append(InjectorRecord(
            target_fn=fn.__name__,
            point=InjectionPoint.AFTER,
            fault_id=fault_id,
            injected=result.injected,
        ))
        return ret

    def records(self) -> List[InjectorRecord]:
        return list(self._records)

    def injected_count(self) -> int:
        return sum(1 for r in self._records if r.injected)
