"""
literary_system.chaos.chaos_scenario
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V726 — ChaosScenario: 시나리오 기반 장애 주입 (ADR-187)

5종 시나리오:
  NETWORK_PARTITION, MEMORY_PRESSURE, CPU_SPIKE, DISK_FULL, SERVICE_CRASH

G32 준수: print() 금지
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from literary_system.chaos.chaos_engine import ChaosEngine, FaultSpec, FaultType, FaultResult


class ScenarioState(str, Enum):
    IDLE    = "idle"
    RUNNING = "running"
    DONE    = "done"
    FAILED  = "failed"


@dataclass
class ScenarioResult:
    """시나리오 실행 결과."""
    scenario_id: str
    state:       ScenarioState
    injections:  List[FaultResult] = field(default_factory=list)
    error:       Optional[str] = None
    started_at:  float = field(default_factory=time.time)
    finished_at: Optional[float] = None

    @property
    def success(self) -> bool:
        return self.state == ScenarioState.DONE

    @property
    def injected_count(self) -> int:
        return sum(1 for r in self.injections if r.injected)


class ChaosScenario:
    """
    미리 정의된 복합 장애 시나리오 실행기.

    Usage::

        scenario = ChaosScenario("partition-test", engine)
        scenario.add_fault(FaultSpec("net", FaultType.NETWORK_PARTITION, "api", duration_ms=0))
        result = scenario.run()
        assert result.success
    """

    PRESET_SCENARIOS: Dict[str, List[FaultType]] = {
        "network_partition":  [FaultType.NETWORK_PARTITION],
        "memory_pressure":    [FaultType.MEMORY_PRESSURE],
        "cpu_spike":          [FaultType.CPU_SPIKE],
        "disk_full":          [FaultType.DISK_FULL],
        "service_crash":      [FaultType.SERVICE_CRASH],
        "cascade_failure":    [FaultType.NETWORK_PARTITION, FaultType.SERVICE_CRASH],
        "resource_exhaustion":[FaultType.MEMORY_PRESSURE, FaultType.CPU_SPIKE, FaultType.DISK_FULL],
    }

    def __init__(
        self,
        scenario_id: str,
        engine: ChaosEngine,
        *,
        on_complete: Optional[Callable[[ScenarioResult], None]] = None,
    ) -> None:
        self.scenario_id = scenario_id
        self._engine     = engine
        self._faults:    List[FaultSpec] = []
        self._on_complete = on_complete
        self._last_result: Optional[ScenarioResult] = None

    def add_fault(self, spec: FaultSpec) -> "ChaosScenario":
        """장애 사양 추가 (체이닝 가능)."""
        self._faults.append(spec)
        return self

    def run(self) -> ScenarioResult:
        """등록된 모든 장애를 순서대로 주입."""
        result = ScenarioResult(
            scenario_id=self.scenario_id,
            state=ScenarioState.RUNNING,
        )
        try:
            for spec in self._faults:
                if spec.fault_id not in [s.fault_id for s in self._engine.list_specs()]:
                    self._engine.register(spec)
                self._engine.activate(spec.fault_id)
                inject_result = self._engine.inject(spec.fault_id)
                result.injections.append(inject_result)
                self._engine.deactivate(spec.fault_id)
            result.state = ScenarioState.DONE
        except Exception as exc:
            result.state = ScenarioState.FAILED
            result.error = str(exc)
        finally:
            result.finished_at = time.time()

        self._last_result = result
        if self._on_complete:
            self._on_complete(result)
        return result

    @classmethod
    def from_preset(
        cls,
        preset_name: str,
        engine: ChaosEngine,
        target: str = "system",
    ) -> "ChaosScenario":
        """사전 정의된 시나리오로부터 생성."""
        if preset_name not in cls.PRESET_SCENARIOS:
            raise KeyError(f"Unknown preset: {preset_name!r}. Available: {list(cls.PRESET_SCENARIOS)}")
        scenario = cls(preset_name, engine)
        for i, ft in enumerate(cls.PRESET_SCENARIOS[preset_name]):
            spec = FaultSpec(
                fault_id=f"{preset_name}-{i}",
                fault_type=ft,
                target=target,
                duration_ms=0,
            )
            scenario.add_fault(spec)
        return scenario

    @property
    def last_result(self) -> Optional[ScenarioResult]:
        return self._last_result
