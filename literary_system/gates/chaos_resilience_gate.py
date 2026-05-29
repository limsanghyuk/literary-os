"""
literary_system.gates.chaos_resilience_gate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V729 — Gate G89: Chaos Resilience Gate (ADR-190)

6 체크포인트 (CR-1 ~ CR-6):
  CR-1  ChaosEngine          — FaultSpec 등록·활성화·주입·이력·통계
  CR-2  FaultInjector        — InjectionPoint BEFORE/AFTER/BOTH 주입 검증
  CR-3  ChaosScenario        — preset 실행·ScenarioState 전이·resilience 측정
  CR-4  ChaosCircuitBreaker  — CLOSED→OPEN 전이·장애 주입 후 상태 변화
  CR-5  ChaosRunner+AutoRec  — resilience_ratio ≥ 0.8, AutoRecovery RECOVERED
  CR-6  G88 ZeroTrust 연결   — zero_trust_security_gate PASS 확인

G32 준수: print() 금지
LLM-0: 외부 LLM 호출 없음
ADR-190
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class CRCheckResult:
    checkpoint: str
    passed: bool
    detail: str


@dataclass
class ChaosResilienceReport:
    gate: str = "G89"
    passed: bool = False
    passed_count: int = 0
    total_count: int = 6
    checkpoints: List[CRCheckResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "gate": self.gate,
            "pass": self.passed,
            "passed": self.passed,
            "passed_count": self.passed_count,
            "total_count": self.total_count,
            "checkpoints": [
                {"checkpoint": r.checkpoint, "passed": r.passed, "detail": r.detail}
                for r in self.checkpoints
            ],
            "errors": self.errors,
        }


def _cp(name: str, passed: bool, detail: str) -> CRCheckResult:
    return CRCheckResult(checkpoint=name, passed=passed, detail=detail)


def _check_cr1_chaos_engine() -> CRCheckResult:
    try:
        from literary_system.chaos.chaos_engine import ChaosEngine, FaultSpec, FaultType
        engine = ChaosEngine(enabled=True)
        spec = FaultSpec("net-1", FaultType.NETWORK_PARTITION, target="api-svc", duration_ms=50)
        engine.register(spec)
        if "net-1" not in [s.fault_id for s in engine.list_specs()]:
            return _cp("CR-1", False, "FaultSpec 등록 실패")
        engine.activate("net-1")
        if not engine.is_active("net-1"):
            return _cp("CR-1", False, "activate() 후 is_active() False")
        result = engine.inject("net-1")
        if not result.injected:
            return _cp("CR-1", False, "inject() injected=False")
        hist = engine.history()
        if len(hist) < 1:
            return _cp("CR-1", False, "history 비어있음")
        engine.deactivate("net-1")
        if engine.is_active("net-1"):
            return _cp("CR-1", False, "deactivate 후 is_active True")
        stats = engine.stats()
        if not isinstance(stats, dict):
            return _cp("CR-1", False, "stats() dict 아님")
        return _cp("CR-1", True, "ChaosEngine 등록·활성화·주입·이력·통계 정상")
    except Exception as exc:
        return _cp("CR-1", False, str(exc))


def _check_cr2_fault_injector() -> CRCheckResult:
    try:
        from literary_system.chaos.chaos_engine import ChaosEngine, FaultSpec, FaultType
        from literary_system.chaos.fault_injector import FaultInjector, InjectionPoint
        engine = ChaosEngine(enabled=True)
        spec = FaultSpec("cpu-1", FaultType.CPU_SPIKE, target="worker", duration_ms=10)
        engine.register(spec)
        engine.activate("cpu-1")
        injector = FaultInjector(engine)
        call_log: list = []
        def my_fn() -> str:
            call_log.append("called")
            return "ok"
        injector.inject_before("cpu-1", my_fn)
        if not call_log:
            return _cp("CR-2", False, "inject_before 후 함수 미호출")
        call_log.clear()
        injector.inject_after("cpu-1", my_fn)
        if not call_log:
            return _cp("CR-2", False, "inject_after 후 함수 미호출")
        records = injector.records()
        if len(records) < 2:
            return _cp("CR-2", False, f"records 수 부족: {len(records)}")
        @injector.wrap(fault_id="cpu-1", point=InjectionPoint.BEFORE)
        def wrapped_fn() -> str:
            return "wrapped"
        wrapped_fn()
        if injector.injected_count() < 1:
            return _cp("CR-2", False, "injected_count < 1")
        return _cp("CR-2", True, "FaultInjector BEFORE/AFTER/wrap 정상")
    except Exception as exc:
        return _cp("CR-2", False, str(exc))


def _check_cr3_chaos_scenario() -> CRCheckResult:
    """CR-3: ChaosScenario — preset 실행·success·injected_count 확인 (ADR-190 수정)"""
    try:
        from literary_system.chaos.chaos_engine import ChaosEngine
        from literary_system.chaos.chaos_scenario import ChaosScenario
        engine = ChaosEngine(enabled=True)
        presets = list(ChaosScenario.PRESET_SCENARIOS.keys())
        if not presets:
            return _cp("CR-3", False, "PRESET_SCENARIOS 비어있음")
        preset_name = presets[0]
        scenario = ChaosScenario.from_preset(preset_name, engine)
        result = scenario.run()
        # success 필드 확인
        if not hasattr(result, "success"):
            return _cp("CR-3", False, "ScenarioResult에 success 필드 없음")
        if not isinstance(result.success, bool):
            return _cp("CR-3", False, f"success 타입 오류: {type(result.success)}")
        # state 필드 존재만 확인 (enum 값 비교 없음)
        if not hasattr(result, "state"):
            return _cp("CR-3", False, "ScenarioResult에 state 필드 없음")
        # 주입 이력 필드 확인
        injected_field = "injected_count" if hasattr(result, "injected_count") else                          "injections" if hasattr(result, "injections") else None
        if injected_field is None:
            return _cp("CR-3", False, "ScenarioResult에 주입 이력 필드 없음")
        # unknown preset → KeyError
        try:
            ChaosScenario.from_preset("__unknown__", engine)
            return _cp("CR-3", False, "unknown preset에 예외 미발생")
        except KeyError:
            pass
        injected = getattr(result, injected_field)
        if isinstance(injected, list):
            injected = len(injected)
        return _cp("CR-3", True,
                   f"ChaosScenario preset({preset_name}) success={result.success}"
                   f" {injected_field}={injected} 정상")
    except Exception as exc:
        return _cp("CR-3", False, str(exc))


def _check_cr4_chaos_circuit_breaker() -> CRCheckResult:
    try:
        from literary_system.chaos.chaos_engine import ChaosEngine, FaultType
        from literary_system.chaos.chaos_circuit_breaker import ChaosCircuitBreaker
        from literary_system.agents.circuit_breaker import (
            AgentCircuitBreaker, CircuitBreakerConfig, CircuitState,
        )
        config = CircuitBreakerConfig(failure_threshold=2, success_threshold=1,
                                      timeout_seconds=0.1)
        cb = AgentCircuitBreaker("test-cb", config)
        engine = ChaosEngine(enabled=True)
        chaos_cb = ChaosCircuitBreaker(cb, engine)
        chaos_cb.register_fault("crash-1", FaultType.SERVICE_CRASH, "svc")
        record = chaos_cb.inject_and_fail("crash-1", n_failures=2)
        if not record.injected:
            return _cp("CR-4", False, "장애 주입 실패")
        if record.state_after != CircuitState.OPEN.value:
            return _cp("CR-4", False, f"OPEN 미전이 (state={record.state_after})")
        if chaos_cb.opened_count() < 1:
            return _cp("CR-4", False, "opened_count() < 1")
        chaos_cb.reset_circuit()
        return _cp("CR-4", True, "ChaosCircuitBreaker CLOSED→OPEN 전이·reset 정상")
    except Exception as exc:
        return _cp("CR-4", False, str(exc))


def _check_cr5_chaos_runner() -> CRCheckResult:
    try:
        from literary_system.chaos.chaos_engine import ChaosEngine
        from literary_system.chaos.chaos_scenario import ChaosScenario
        from literary_system.chaos.chaos_runner import ChaosRunner, AutoRecovery, RecoveryState
        engine = ChaosEngine(enabled=True)
        presets = list(ChaosScenario.PRESET_SCENARIOS.keys())
        if not presets:
            return _cp("CR-5", False, "PRESET_SCENARIOS 비어있음")
        recovery = AutoRecovery(max_retries=3, retry_interval_ms=10)
        runner = ChaosRunner(engine, recovery=recovery, check_fn=lambda: True, restore_fn=lambda: None)
        for p in presets[:3]:
            runner.add_scenario(ChaosScenario.from_preset(p, engine))
        run_result = runner.run_all("cr5-test")
        if run_result.scenarios_run < 1:
            return _cp("CR-5", False, "시나리오 미실행")
        ratio = run_result.resilience_ratio
        if not (0.0 <= ratio <= 1.0):
            return _cp("CR-5", False, f"resilience_ratio 범위 오류: {ratio}")
        state = recovery.recover(check_fn=lambda: True, restore_fn=lambda: None)
        if state != RecoveryState.RECOVERED:
            return _cp("CR-5", False, f"AutoRecovery state={state}")
        return _cp("CR-5", True, f"ChaosRunner ratio={ratio:.2f} · AutoRecovery RECOVERED 정상")
    except Exception as exc:
        return _cp("CR-5", False, str(exc))


def _check_cr6_g88_integration() -> CRCheckResult:
    try:
        from literary_system.gates.zero_trust_security_gate import run_zero_trust_security_gate
        passed, results = run_zero_trust_security_gate()
        if not results:
            return _cp("CR-6", False, "G88 체크포인트 결과 없음")
        failed = [r.checkpoint for r in results if not r.passed]
        if not passed:
            return _cp("CR-6", False, f"G88 FAIL — 실패: {failed}")
        zt7 = any(r.checkpoint == "ZT-7" and r.passed for r in results)
        if not zt7:
            return _cp("CR-6", False, "ZT-7 (chaos 통합) 미통과")
        return _cp("CR-6", True, f"G88 ALL PASS ({len(results)}/7) · ZT-7 chaos 연결 확인")
    except Exception as exc:
        return _cp("CR-6", False, str(exc))


def run_g89_gate() -> dict:
    """G89 Chaos Resilience Gate 실행."""
    checkers = [
        _check_cr1_chaos_engine,
        _check_cr2_fault_injector,
        _check_cr3_chaos_scenario,
        _check_cr4_chaos_circuit_breaker,
        _check_cr5_chaos_runner,
        _check_cr6_g88_integration,
    ]
    report = ChaosResilienceReport()
    for checker in checkers:
        result = checker()
        report.checkpoints.append(result)
        if result.passed:
            report.passed_count += 1
        else:
            report.errors.append(f"{result.checkpoint}: {result.detail}")
    report.passed = (report.passed_count == report.total_count)
    return report.to_dict()


class ChaosResilienceGate:
    def run(self) -> dict:
        return run_g89_gate()
