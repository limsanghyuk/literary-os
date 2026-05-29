"""V726~V728 — ChaosScenario + ChaosCircuitBreaker + ChaosRunner 33 TC"""
from __future__ import annotations
import pytest
from literary_system.chaos.chaos_engine import ChaosEngine, FaultSpec, FaultType
from literary_system.chaos.chaos_scenario import ChaosScenario, ScenarioResult, ScenarioState
from literary_system.chaos.chaos_circuit_breaker import ChaosCircuitBreaker, CircuitChaosRecord
from literary_system.chaos.chaos_runner import ChaosRunner, AutoRecovery, RecoveryState, RunnerResult
from literary_system.agents.circuit_breaker import AgentCircuitBreaker, CircuitBreakerConfig, CircuitState

def make_engine(): return ChaosEngine()
def make_spec(fid="f1", ft=FaultType.NETWORK_PARTITION, dur=0):
    return FaultSpec(fid, ft, "svc", duration_ms=dur)

# ── V726 ChaosScenario (TC01~TC11) ────────────────────────────────────────────

def test_tc01_scenario_run_success():
    e = make_engine()
    s = ChaosScenario("sc1", e)
    s.add_fault(make_spec("f1"))
    r = s.run()
    assert r.success and r.state == ScenarioState.DONE

def test_tc02_scenario_injected_count():
    e = make_engine()
    s = ChaosScenario("sc2", e)
    s.add_fault(make_spec("f1")); s.add_fault(make_spec("f2", FaultType.CPU_SPIKE))
    r = s.run()
    assert r.injected_count == 2

def test_tc03_scenario_chaining():
    e = make_engine()
    s = ChaosScenario("sc3", e)
    result = s.add_fault(make_spec("f1")).add_fault(make_spec("f2", FaultType.DISK_FULL))
    assert result is s  # 체이닝 반환

def test_tc04_scenario_preset_network():
    e = make_engine()
    s = ChaosScenario.from_preset("network_partition", e, target="api")
    r = s.run()
    assert r.success

def test_tc05_scenario_preset_cascade():
    e = make_engine()
    s = ChaosScenario.from_preset("cascade_failure", e)
    r = s.run()
    assert r.success and r.injected_count >= 2

def test_tc06_scenario_preset_resource():
    e = make_engine()
    s = ChaosScenario.from_preset("resource_exhaustion", e)
    r = s.run()
    assert r.injected_count == 3

def test_tc07_scenario_all_presets():
    expected = {"network_partition","memory_pressure","cpu_spike","disk_full","service_crash","cascade_failure","resource_exhaustion"}
    assert set(ChaosScenario.PRESET_SCENARIOS.keys()) == expected

def test_tc08_scenario_invalid_preset():
    e = make_engine()
    with pytest.raises(KeyError): ChaosScenario.from_preset("invalid_preset", e)

def test_tc09_scenario_on_complete_hook():
    e = make_engine()
    called = []
    s = ChaosScenario("sc9", e, on_complete=lambda r: called.append(r))
    s.add_fault(make_spec("f1"))
    s.run()
    assert len(called) == 1 and isinstance(called[0], ScenarioResult)

def test_tc10_scenario_last_result():
    e = make_engine()
    s = ChaosScenario("sc10", e)
    s.add_fault(make_spec("f1"))
    assert s.last_result is None
    s.run()
    assert s.last_result is not None

def test_tc11_scenario_elapsed():
    e = make_engine()
    s = ChaosScenario("sc11", e)
    s.add_fault(make_spec("f1"))
    r = s.run()
    assert r.finished_at is not None and r.finished_at >= r.started_at

# ── V727 ChaosCircuitBreaker (TC12~TC22) ─────────────────────────────────────

def test_tc12_cb_opens_after_failures():
    config = CircuitBreakerConfig(failure_threshold=3)
    cb = AgentCircuitBreaker("test", config)
    e = make_engine()
    chaos_cb = ChaosCircuitBreaker(cb, e)
    chaos_cb.register_fault("f1", FaultType.SERVICE_CRASH, "svc")
    record = chaos_cb.inject_and_fail("f1", n_failures=3)
    assert record.state_after == CircuitState.OPEN.value

def test_tc13_cb_state_before_closed():
    config = CircuitBreakerConfig(failure_threshold=5)
    cb = AgentCircuitBreaker("test", config)
    e = make_engine()
    chaos_cb = ChaosCircuitBreaker(cb, e)
    chaos_cb.register_fault("f1", FaultType.CPU_SPIKE, "svc")
    record = chaos_cb.inject_and_fail("f1", n_failures=1)
    assert record.state_before == CircuitState.CLOSED.value

def test_tc14_cb_injected_true():
    config = CircuitBreakerConfig(failure_threshold=3)
    cb = AgentCircuitBreaker("test", config)
    e = make_engine()
    chaos_cb = ChaosCircuitBreaker(cb, e)
    chaos_cb.register_fault("f1", FaultType.MEMORY_PRESSURE, "svc")
    record = chaos_cb.inject_and_fail("f1", n_failures=3)
    assert record.injected

def test_tc15_cb_reset():
    config = CircuitBreakerConfig(failure_threshold=3)
    cb = AgentCircuitBreaker("test", config)
    e = make_engine()
    chaos_cb = ChaosCircuitBreaker(cb, e)
    chaos_cb.register_fault("f1", FaultType.DISK_FULL, "svc")
    chaos_cb.inject_and_fail("f1", n_failures=3)
    assert cb.state == CircuitState.OPEN
    chaos_cb.reset_circuit()
    assert cb.state == CircuitState.CLOSED

def test_tc16_cb_records():
    config = CircuitBreakerConfig(failure_threshold=3)
    cb = AgentCircuitBreaker("test", config)
    e = make_engine()
    chaos_cb = ChaosCircuitBreaker(cb, e)
    chaos_cb.register_fault("f1", FaultType.NETWORK_PARTITION, "svc")
    chaos_cb.inject_and_fail("f1", n_failures=3)
    assert len(chaos_cb.records()) == 1

def test_tc17_cb_opened_count():
    config = CircuitBreakerConfig(failure_threshold=3)
    cb = AgentCircuitBreaker("test", config)
    e = make_engine()
    chaos_cb = ChaosCircuitBreaker(cb, e)
    chaos_cb.register_fault("f1", FaultType.SERVICE_CRASH, "svc")
    chaos_cb.inject_and_fail("f1", n_failures=3)
    assert chaos_cb.opened_count() == 1

def test_tc18_circuit_chaos_record_dataclass():
    r = CircuitChaosRecord("f1", True, "closed", "open")
    assert r.fault_id == "f1" and r.injected

def test_tc19_cb_partial_failures_stay_closed():
    config = CircuitBreakerConfig(failure_threshold=5)
    cb = AgentCircuitBreaker("test", config)
    e = make_engine()
    chaos_cb = ChaosCircuitBreaker(cb, e)
    chaos_cb.register_fault("f1", FaultType.CPU_SPIKE, "svc")
    record = chaos_cb.inject_and_fail("f1", n_failures=2)
    assert record.state_after == CircuitState.CLOSED.value

def test_tc20_g32_chaos_circuit_breaker():
    import literary_system.chaos.chaos_circuit_breaker as m
    src = open(m.__file__, encoding="utf-8").read()
    assert not any(l.strip().startswith("print(") for l in src.splitlines())

def test_tc21_no_circular_chaos_to_agents():
    import literary_system.chaos.chaos_engine as m
    src = open(m.__file__, encoding="utf-8").read()
    assert "from literary_system.agents" not in src

def test_tc22_circuit_state_enum():
    assert CircuitState.OPEN.value in ("open", "OPEN")
    assert CircuitState.CLOSED.value in ("closed", "CLOSED")

# ── V728 ChaosRunner + AutoRecovery (TC23~TC33) ───────────────────────────────

def test_tc23_auto_recovery_success():
    rec = AutoRecovery(max_retries=3, retry_interval_ms=0)
    state = rec.recover(check_fn=lambda: True, restore_fn=lambda: None)
    assert state == RecoveryState.RECOVERED

def test_tc24_auto_recovery_fail():
    rec = AutoRecovery(max_retries=2, retry_interval_ms=0)
    state = rec.recover(check_fn=lambda: False, restore_fn=lambda: None)
    assert state == RecoveryState.FAILED

def test_tc25_auto_recovery_history():
    rec = AutoRecovery(max_retries=3, retry_interval_ms=0)
    rec.recover(check_fn=lambda: True, restore_fn=lambda: None)
    hist = rec.history
    assert RecoveryState.RECOVERING in hist
    assert RecoveryState.RECOVERED in hist

def test_tc26_auto_recovery_last_state():
    rec = AutoRecovery(max_retries=3, retry_interval_ms=0)
    rec.recover(check_fn=lambda: True, restore_fn=lambda: None)
    assert rec.last_state() == RecoveryState.RECOVERED  # property

def test_tc27_runner_run_all():
    e = make_engine()
    runner = ChaosRunner(e, recovery=AutoRecovery(retry_interval_ms=0),
                         check_fn=lambda: True, restore_fn=lambda: None)
    s1 = ChaosScenario.from_preset("network_partition", e)
    s2 = ChaosScenario.from_preset("cpu_spike", e)
    runner.add_scenario(s1).add_scenario(s2)
    result = runner.run_all("r1")
    assert result.scenarios_run == 2
    assert result.scenarios_passed == 2

def test_tc28_runner_resilience_ratio():
    e = make_engine()
    runner = ChaosRunner(e, recovery=AutoRecovery(retry_interval_ms=0),
                         check_fn=lambda: True)
    for pn in ["network_partition","cpu_spike","disk_full","memory_pressure","service_crash"]:
        runner.add_scenario(ChaosScenario.from_preset(pn, e))
    result = runner.run_all("r2")
    assert result.resilience_ratio >= 0.8

def test_tc29_runner_run_preset():
    e = make_engine()
    runner = ChaosRunner(e, recovery=AutoRecovery(retry_interval_ms=0),
                         check_fn=lambda: True)
    result = runner.run_preset("service_crash", target="api", run_id="r3")
    assert result.scenarios_run == 1

def test_tc30_runner_result_dataclass():
    rr = RunnerResult(run_id="x")
    assert rr.run_id == "x"
    assert rr.resilience_ratio == 0.0

def test_tc31_recovery_state_enum():
    assert RecoveryState.RECOVERED.value == "recovered"
    assert RecoveryState.FAILED.value == "failed"

def test_tc32_runner_elapsed():
    e = make_engine()
    runner = ChaosRunner(e, recovery=AutoRecovery(retry_interval_ms=0),
                         check_fn=lambda: True)
    runner.add_scenario(ChaosScenario.from_preset("cpu_spike", e))
    result = runner.run_all("r4")
    assert result.elapsed_ms >= 0

def test_tc33_chaos_full_import():
    from literary_system.chaos import (
        ChaosEngine, FaultSpec, FaultType, FaultResult,
        FaultInjector, InjectionPoint,
        ChaosScenario, ScenarioResult, ScenarioState,
        ChaosCircuitBreaker, CircuitChaosRecord,
        ChaosRunner, AutoRecovery, RunnerResult, RecoveryState,
    )
    assert all([ChaosEngine, FaultSpec, ChaosScenario, ChaosRunner])
