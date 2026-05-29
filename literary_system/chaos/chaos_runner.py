"""
literary_system.chaos.chaos_runner
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V728 — ChaosRunner + AutoRecovery: 자동화 카오스 실행 + 복구 (ADR-189)
G32 준수: print() 금지
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from literary_system.chaos.chaos_engine import ChaosEngine, FaultSpec, FaultType, FaultResult
from literary_system.chaos.chaos_scenario import ChaosScenario, ScenarioResult, ScenarioState


class RecoveryState(str, Enum):
    IDLE       = "idle"
    RECOVERING = "recovering"
    RECOVERED  = "recovered"
    FAILED     = "failed"


@dataclass
class RunnerResult:
    """ChaosRunner 실행 결과."""
    run_id:          str
    scenarios_run:   int = 0
    scenarios_passed: int = 0
    scenarios_failed: int = 0
    recovery_success: int = 0
    recovery_failed:  int = 0
    elapsed_ms:       float = 0.0
    results:          List[ScenarioResult] = field(default_factory=list)

    @property
    def resilience_ratio(self) -> float:
        total = self.scenarios_run
        return self.scenarios_passed / total if total > 0 else 0.0


class AutoRecovery:
    """
    장애 발생 후 자동 복구를 시도하는 컴포넌트.

    Usage::

        recovery = AutoRecovery(max_retries=3, retry_interval_ms=100)
        state = recovery.recover(check_fn=lambda: True, restore_fn=lambda: None)
    """

    def __init__(self, max_retries: int = 3, retry_interval_ms: int = 100) -> None:
        self._max_retries      = max_retries
        self._retry_interval_s = retry_interval_ms / 1000.0
        self._history: List[RecoveryState] = []

    def recover(
        self,
        check_fn: Callable[[], bool],
        restore_fn: Callable[[], None],
    ) -> RecoveryState:
        """
        check_fn이 True를 반환할 때까지 restore_fn을 반복 호출.

        Args:
            check_fn:   시스템이 정상인지 확인 (True=정상)
            restore_fn: 복구 동작 실행

        Returns:
            RecoveryState
        """
        self._history.append(RecoveryState.RECOVERING)
        for attempt in range(self._max_retries):
            try:
                restore_fn()
                time.sleep(self._retry_interval_s)
                if check_fn():
                    self._history.append(RecoveryState.RECOVERED)
                    return RecoveryState.RECOVERED
            except Exception:
                pass
        self._history.append(RecoveryState.FAILED)
        return RecoveryState.FAILED

    @property
    def history(self) -> List[RecoveryState]:
        return list(self._history)

    def last_state(self) -> Optional[RecoveryState]:
        return self._history[-1] if self._history else None


class ChaosRunner:
    """
    복수의 ChaosScenario를 순서대로 실행하고 AutoRecovery를 결합하는 오케스트레이터.

    Usage::

        runner = ChaosRunner(engine, recovery=AutoRecovery())
        runner.add_scenario(scenario1)
        runner.add_scenario(scenario2)
        result = runner.run_all("run-001")
        assert result.resilience_ratio >= 0.8  # ≥ 4/5
    """

    def __init__(
        self,
        engine: ChaosEngine,
        *,
        recovery: Optional[AutoRecovery] = None,
        check_fn: Optional[Callable[[], bool]] = None,
        restore_fn: Optional[Callable[[], None]] = None,
    ) -> None:
        self._engine      = engine
        self._recovery    = recovery or AutoRecovery()
        self._check_fn    = check_fn or (lambda: True)
        self._restore_fn  = restore_fn or (lambda: None)
        self._scenarios:  List[ChaosScenario] = []

    def add_scenario(self, scenario: ChaosScenario) -> "ChaosRunner":
        self._scenarios.append(scenario)
        return self

    def run_all(self, run_id: str = "default") -> RunnerResult:
        """등록된 모든 시나리오를 순서대로 실행하고 복구."""
        result = RunnerResult(run_id=run_id)
        t_start = time.time()

        for scenario in self._scenarios:
            result.scenarios_run += 1
            sr = scenario.run()
            result.results.append(sr)

            if sr.success:
                result.scenarios_passed += 1
                # 복구 시도
                rec_state = self._recovery.recover(
                    check_fn=self._check_fn,
                    restore_fn=self._restore_fn,
                )
                if rec_state == RecoveryState.RECOVERED:
                    result.recovery_success += 1
                else:
                    result.recovery_failed += 1
            else:
                result.scenarios_failed += 1

        result.elapsed_ms = (time.time() - t_start) * 1000
        return result

    def run_preset(
        self,
        preset_name: str,
        target: str = "system",
        run_id: Optional[str] = None,
    ) -> RunnerResult:
        """단일 프리셋 시나리오 실행."""
        scenario = ChaosScenario.from_preset(preset_name, self._engine, target=target)
        self._scenarios = [scenario]
        return self.run_all(run_id or preset_name)

    def stats(self) -> Dict[str, int]:
        return {
            "scenarios": len(self._scenarios),
        }
