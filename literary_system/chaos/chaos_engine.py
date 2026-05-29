"""
literary_system.chaos.chaos_engine
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V724 — ChaosEngine: 장애 주입 엔진 (ADR-185).

설계:
  - FaultSpec: 주입할 장애 사양 (불변 dataclass)
  - FaultType: 장애 유형 Enum (5종)
  - FaultResult: 주입 결과 DTO
  - ChaosEngine: 장애 등록/활성화/비활성화/실행
  - G32 준수: print() 금지
"""
from __future__ import annotations

import sys
import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional


# ── 장애 유형 ─────────────────────────────────────────────────────────────────

class FaultType(str, Enum):
    NETWORK_PARTITION = "network_partition"   # 네트워크 단절
    MEMORY_PRESSURE   = "memory_pressure"     # 메모리 압박
    CPU_SPIKE         = "cpu_spike"           # CPU 스파이크
    DISK_FULL         = "disk_full"           # 디스크 포화
    SERVICE_CRASH     = "service_crash"       # 서비스 강제 종료


# ── 장애 사양 ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class FaultSpec:
    """주입할 장애 사양 (불변)."""
    fault_id:    str
    fault_type:  FaultType
    target:      str           # 대상 서비스/컴포넌트 이름
    intensity:   float = 1.0   # 0.0~1.0 (강도)
    duration_ms: int   = 1000  # 지속 시간 (밀리초)
    probability: float = 1.0   # 주입 확률 0.0~1.0

    def __post_init__(self) -> None:
        if not (0.0 <= self.intensity <= 1.0):
            raise ValueError(f"intensity must be in [0.0, 1.0], got {self.intensity}")
        if not (0.0 <= self.probability <= 1.0):
            raise ValueError(f"probability must be in [0.0, 1.0], got {self.probability}")
        if self.duration_ms < 0:
            raise ValueError(f"duration_ms must be >= 0, got {self.duration_ms}")


# ── 주입 결과 ─────────────────────────────────────────────────────────────────

@dataclass
class FaultResult:
    """장애 주입 실행 결과."""
    fault_id:    str
    fault_type:  FaultType
    target:      str
    injected:    bool          # 실제 주입 여부 (확률로 스킵될 수 있음)
    started_at:  float = field(default_factory=time.time)
    finished_at: Optional[float] = None
    error:       Optional[str]  = None

    @property
    def elapsed_ms(self) -> float:
        end = self.finished_at or time.time()
        return (end - self.started_at) * 1000


# ── 장애 엔진 ─────────────────────────────────────────────────────────────────

class ChaosEngine:
    """
    장애 주입 엔진.

    Usage::

        engine = ChaosEngine()
        spec = FaultSpec("net-1", FaultType.NETWORK_PARTITION, target="api-server",
                         intensity=0.8, duration_ms=500)
        engine.register(spec)
        engine.activate("net-1")
        result = engine.inject("net-1")
    """

    def __init__(self, *, enabled: bool = True) -> None:
        self._enabled = enabled
        self._specs: Dict[str, FaultSpec]   = {}
        self._active: Dict[str, bool]       = {}
        self._history: List[FaultResult]    = []
        self._handlers: Dict[FaultType, Callable[[FaultSpec], None]] = {}
        self._lock = threading.Lock()

    # ── 등록 ────────────────────────────────────────────────────────────────

    def register(self, spec: FaultSpec) -> None:
        with self._lock:
            self._specs[spec.fault_id] = spec
            self._active[spec.fault_id] = False

    def unregister(self, fault_id: str) -> bool:
        with self._lock:
            if fault_id in self._specs:
                del self._specs[fault_id]
                del self._active[fault_id]
                return True
            return False

    def activate(self, fault_id: str) -> None:
        with self._lock:
            if fault_id not in self._specs:
                raise KeyError(f"Fault '{fault_id}' not registered")
            self._active[fault_id] = True

    def deactivate(self, fault_id: str) -> None:
        with self._lock:
            if fault_id in self._active:
                self._active[fault_id] = False

    def is_active(self, fault_id: str) -> bool:
        return self._active.get(fault_id, False)

    # ── 핸들러 ────────────────────────────────────────────────────────────

    def register_handler(
        self,
        fault_type: FaultType,
        handler: Callable[[FaultSpec], None],
    ) -> None:
        """특정 FaultType에 대한 실행 핸들러 등록."""
        self._handlers[fault_type] = handler

    # ── 주입 ──────────────────────────────────────────────────────────────

    def inject(self, fault_id: str) -> FaultResult:
        """
        등록된 장애를 주입한다.
        probability < 1.0이면 일부 주입을 스킵한다.
        """
        import random
        with self._lock:
            spec = self._specs.get(fault_id)
            if spec is None:
                raise KeyError(f"Fault '{fault_id}' not registered")
            active = self._active.get(fault_id, False)

        result = FaultResult(
            fault_id=fault_id,
            fault_type=spec.fault_type,
            target=spec.target,
            injected=False,
        )

        if not self._enabled or not active:
            result.finished_at = time.time()
            self._history.append(result)
            return result

        # 확률 검사
        if random.random() > spec.probability:
            result.finished_at = time.time()
            self._history.append(result)
            return result

        # 핸들러 실행
        try:
            handler = self._handlers.get(spec.fault_type)
            if handler:
                handler(spec)
            else:
                time.sleep(spec.duration_ms / 1000.0)
            result.injected = True
        except Exception as exc:
            result.error = str(exc)
        finally:
            result.finished_at = time.time()

        self._history.append(result)
        return result

    def inject_all_active(self) -> List[FaultResult]:
        """활성화된 모든 장애를 주입."""
        active_ids = [fid for fid, on in self._active.items() if on]
        return [self.inject(fid) for fid in active_ids]

    # ── 조회 ──────────────────────────────────────────────────────────────

    def list_specs(self) -> List[FaultSpec]:
        return list(self._specs.values())

    def list_active(self) -> List[str]:
        return [fid for fid, on in self._active.items() if on]

    def history(self) -> List[FaultResult]:
        return list(self._history)

    def stats(self) -> Dict[str, int]:
        return {
            "registered": len(self._specs),
            "active":     len(self.list_active()),
            "injected":   sum(1 for r in self._history if r.injected),
            "skipped":    sum(1 for r in self._history if not r.injected),
            "errors":     sum(1 for r in self._history if r.error),
        }

    def reset_history(self) -> None:
        self._history.clear()
