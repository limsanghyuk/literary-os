"""
tests/unit/test_v729_chaos_resilience_gate.py
V729 — G89 Chaos Resilience Gate 테스트 (TC01~TC33, 33개)
ADR-190
"""
import pytest
from unittest.mock import MagicMock, patch


# ── Fixture: 실제 chaos 모듈 ───────────────────────────────────────────────────

@pytest.fixture
def chaos_engine():
    from literary_system.chaos.chaos_engine import ChaosEngine
    return ChaosEngine(enabled=True)

@pytest.fixture
def fault_spec_factory():
    from literary_system.chaos.chaos_engine import FaultSpec, FaultType
    def _make(fid="f-1", ftype=None, target="svc", duration_ms=10):
        return FaultSpec(fid, ftype or FaultType.NETWORK_PARTITION, target, duration_ms=duration_ms)
    return _make


# ── TC01~TC07: CRCheckResult / ChaosResilienceReport ─────────────────────────

class TestDataClasses:
    def test_tc01_cr_check_result_frozen(self):
        from literary_system.gates.chaos_resilience_gate import CRCheckResult
        r = CRCheckResult("CR-1", True, "ok")
        with pytest.raises((AttributeError, TypeError)):
            r.passed = False  # type: ignore

    def test_tc02_report_initial_state(self):
        from literary_system.gates.chaos_resilience_gate import ChaosResilienceReport
        rpt = ChaosResilienceReport()
        assert rpt.gate == "G89"
        assert rpt.total_count == 6
        assert rpt.passed is False

    def test_tc03_report_to_dict_keys(self):
        from literary_system.gates.chaos_resilience_gate import ChaosResilienceReport
        rpt = ChaosResilienceReport()
        d = rpt.to_dict()
        assert "gate" in d and "pass" in d and "passed" in d
        assert "passed_count" in d and "total_count" in d
        assert "checkpoints" in d and "errors" in d

    def test_tc04_report_to_dict_gate_value(self):
        from literary_system.gates.chaos_resilience_gate import ChaosResilienceReport
        d = ChaosResilienceReport().to_dict()
        assert d["gate"] == "G89"

    def test_tc05_cp_helper_passed(self):
        from literary_system.gates.chaos_resilience_gate import _cp
        r = _cp("CR-1", True, "detail")
        assert r.passed is True and r.checkpoint == "CR-1"

    def test_tc06_cp_helper_failed(self):
        from literary_system.gates.chaos_resilience_gate import _cp
        r = _cp("CR-2", False, "error msg")
        assert r.passed is False

    def test_tc07_report_checkpoints_list(self):
        from literary_system.gates.chaos_resilience_gate import ChaosResilienceReport, _cp
        rpt = ChaosResilienceReport()
        rpt.checkpoints.append(_cp("CR-1", True, "ok"))
        assert len(rpt.checkpoints) == 1


# ── TC08~TC14: CR-1 ChaosEngine ───────────────────────────────────────────────

class TestCR1ChaosEngine:
    def test_tc08_engine_register(self, chaos_engine, fault_spec_factory):
        spec = fault_spec_factory()
        chaos_engine.register(spec)
        assert "f-1" in [s.fault_id for s in chaos_engine.list_specs()]

    def test_tc09_engine_activate_deactivate(self, chaos_engine, fault_spec_factory):
        chaos_engine.register(fault_spec_factory("f-2"))
        chaos_engine.activate("f-2")
        assert chaos_engine.is_active("f-2")
        chaos_engine.deactivate("f-2")
        assert not chaos_engine.is_active("f-2")

    def test_tc10_engine_inject_records(self, chaos_engine, fault_spec_factory):
        chaos_engine.register(fault_spec_factory("f-3"))
        chaos_engine.activate("f-3")
        result = chaos_engine.inject("f-3")
        assert result.injected is True
        assert len(chaos_engine.history()) >= 1

    def test_tc11_engine_stats_dict(self, chaos_engine):
        stats = chaos_engine.stats()
        assert isinstance(stats, dict)

    def test_tc12_engine_inject_all_active(self, chaos_engine, fault_spec_factory):
        from literary_system.chaos.chaos_engine import FaultType
        chaos_engine.register(fault_spec_factory("fa1", FaultType.CPU_SPIKE))
        chaos_engine.register(fault_spec_factory("fa2", FaultType.MEMORY_LEAK))
        chaos_engine.activate("fa1")
        chaos_engine.activate("fa2")
        results = chaos_engine.inject_all_active()
        assert len(results) == 2

    def test_tc13_engine_unregister(self, chaos_engine, fault_spec_factory):
        chaos_engine.register(fault_spec_factory("f-un"))
        removed = chaos_engine.unregister("f-un")
        assert removed is True

    def test_tc14_engine_reset_history(self, chaos_engine, fault_spec_factory):
        chaos_engine.register(fault_spec_factory("f-rh"))
        chaos_engine.activate("f-rh")
        chaos_engine.inject("f-rh")
        chaos_engine.reset_history()
        assert len(chaos_engine.history()) == 0


# ── TC15~TC19: CR-2 FaultInjector ─────────────────────────────────────────────

class TestCR2FaultInjector:
    def test_tc15_injector_inject_before(self, chaos_engine, fault_spec_factory):
        from literary_system.chaos.fault_injector import FaultInjector
        chaos_engine.register(fault_spec_factory("fi-b"))
        chaos_engine.activate("fi-b")
        injector = FaultInjector(chaos_engine)
        log = []
        injector.inject_before("fi-b", lambda: log.append(1))
        assert log

    def test_tc16_injector_inject_after(self, chaos_engine, fault_spec_factory):
        from literary_system.chaos.fault_injector import FaultInjector
        chaos_engine.register(fault_spec_factory("fi-a"))
        chaos_engine.activate("fi-a")
        injector = FaultInjector(chaos_engine)
        log = []
        injector.inject_after("fi-a", lambda: log.append(1))
        assert log

    def test_tc17_injector_wrap_decorator(self, chaos_engine, fault_spec_factory):
        from literary_system.chaos.fault_injector import FaultInjector, InjectionPoint
        chaos_engine.register(fault_spec_factory("fi-w"))
        chaos_engine.activate("fi-w")
        injector = FaultInjector(chaos_engine)
        @injector.wrap(fault_id="fi-w", point=InjectionPoint.BEFORE)
        def fn(): return 42
        assert fn() == 42

    def test_tc18_injector_records_count(self, chaos_engine, fault_spec_factory):
        from literary_system.chaos.fault_injector import FaultInjector
        chaos_engine.register(fault_spec_factory("fi-r"))
        chaos_engine.activate("fi-r")
        injector = FaultInjector(chaos_engine)
        injector.inject_before("fi-r", lambda: None)
        injector.inject_after("fi-r", lambda: None)
        assert len(injector.records()) == 2

    def test_tc19_injector_injected_count(self, chaos_engine, fault_spec_factory):
        from literary_system.chaos.fault_injector import FaultInjector
        chaos_engine.register(fault_spec_factory("fi-ic"))
        chaos_engine.activate("fi-ic")
        injector = FaultInjector(chaos_engine)
        injector.inject_before("fi-ic", lambda: None)
        assert injector.injected_count() >= 1


# ── TC20~TC23: CR-3 ChaosScenario ────────────────────────────────────────────

class TestCR3ChaosScenario:
    def test_tc20_preset_list_not_empty(self, chaos_engine):
        from literary_system.chaos.chaos_scenario import ChaosScenario
        assert len(ChaosScenario.PRESET_SCENARIOS) > 0

    def test_tc21_from_preset_runs(self, chaos_engine):
        from literary_system.chaos.chaos_scenario import ChaosScenario, ScenarioState
        presets = list(ChaosScenario.PRESET_SCENARIOS.keys())
        scenario = ChaosScenario.from_preset(presets[0], chaos_engine)
        result = scenario.run()
        assert result.state in (ScenarioState.PASSED, ScenarioState.FAILED)

    def test_tc22_unknown_preset_raises(self, chaos_engine):
        from literary_system.chaos.chaos_scenario import ChaosScenario
        with pytest.raises(KeyError):
            ChaosScenario.from_preset("__nonexistent__", chaos_engine)

    def test_tc23_scenario_result_has_state(self, chaos_engine):
        from literary_system.chaos.chaos_scenario import ChaosScenario
        presets = list(ChaosScenario.PRESET_SCENARIOS.keys())
        s = ChaosScenario.from_preset(presets[0], chaos_engine)
        r = s.run()
        assert hasattr(r, "state")


# ── TC24~TC26: CR-4 ChaosCircuitBreaker ──────────────────────────────────────

class TestCR4ChaosCircuitBreaker:
    def test_tc24_cb_open_on_failures(self, chaos_engine):
        from literary_system.chaos.chaos_circuit_breaker import ChaosCircuitBreaker
        from literary_system.chaos.chaos_engine import FaultType
        from literary_system.agents.circuit_breaker import (
            AgentCircuitBreaker, CircuitBreakerConfig, CircuitState,
        )
        config = CircuitBreakerConfig(failure_threshold=2, success_threshold=1, timeout_seconds=0.1)
        cb = AgentCircuitBreaker("cb-1", config)
        chaos_cb = ChaosCircuitBreaker(cb, chaos_engine)
        chaos_cb.register_fault("c-1", FaultType.SERVICE_CRASH, "svc")
        record = chaos_cb.inject_and_fail("c-1", n_failures=2)
        assert record.state_after == CircuitState.OPEN.value

    def test_tc25_cb_opened_count(self, chaos_engine):
        from literary_system.chaos.chaos_circuit_breaker import ChaosCircuitBreaker
        from literary_system.chaos.chaos_engine import FaultType
        from literary_system.agents.circuit_breaker import (
            AgentCircuitBreaker, CircuitBreakerConfig,
        )
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = AgentCircuitBreaker("cb-2", config)
        chaos_cb = ChaosCircuitBreaker(cb, chaos_engine)
        chaos_cb.register_fault("c-2", FaultType.SERVICE_CRASH, "svc")
        chaos_cb.inject_and_fail("c-2", n_failures=2)
        assert chaos_cb.opened_count() >= 1

    def test_tc26_cb_reset(self, chaos_engine):
        from literary_system.chaos.chaos_circuit_breaker import ChaosCircuitBreaker
        from literary_system.chaos.chaos_engine import FaultType
        from literary_system.agents.circuit_breaker import (
            AgentCircuitBreaker, CircuitBreakerConfig, CircuitState,
        )
        config = CircuitBreakerConfig(failure_threshold=2)
        cb = AgentCircuitBreaker("cb-3", config)
        chaos_cb = ChaosCircuitBreaker(cb, chaos_engine)
        chaos_cb.register_fault("c-3", FaultType.SERVICE_CRASH, "svc")
        chaos_cb.inject_and_fail("c-3", n_failures=2)
        chaos_cb.reset_circuit()
        assert cb.state == CircuitState.CLOSED


# ── TC27~TC30: CR-5 ChaosRunner + AutoRecovery ───────────────────────────────

class TestCR5ChaosRunner:
    def test_tc27_runner_run_all(self, chaos_engine):
        from literary_system.chaos.chaos_scenario import ChaosScenario
        from literary_system.chaos.chaos_runner import ChaosRunner, AutoRecovery
        presets = list(ChaosScenario.PRESET_SCENARIOS.keys())
        recovery = AutoRecovery(max_retries=2, retry_interval_ms=5)
        runner = ChaosRunner(chaos_engine, recovery=recovery, check_fn=lambda: True)
        runner.add_scenario(ChaosScenario.from_preset(presets[0], chaos_engine))
        result = runner.run_all("tc27")
        assert result.scenarios_run >= 1

    def test_tc28_resilience_ratio_range(self, chaos_engine):
        from literary_system.chaos.chaos_scenario import ChaosScenario
        from literary_system.chaos.chaos_runner import ChaosRunner, AutoRecovery
        presets = list(ChaosScenario.PRESET_SCENARIOS.keys())
        runner = ChaosRunner(chaos_engine, recovery=AutoRecovery())
        for p in presets[:2]:
            runner.add_scenario(ChaosScenario.from_preset(p, chaos_engine))
        result = runner.run_all("tc28")
        assert 0.0 <= result.resilience_ratio <= 1.0

    def test_tc29_auto_recovery_recovered(self):
        from literary_system.chaos.chaos_runner import AutoRecovery, RecoveryState
        recovery = AutoRecovery(max_retries=3, retry_interval_ms=5)
        state = recovery.recover(check_fn=lambda: True, restore_fn=lambda: None)
        assert state == RecoveryState.RECOVERED

    def test_tc30_auto_recovery_failed(self):
        from literary_system.chaos.chaos_runner import AutoRecovery, RecoveryState
        recovery = AutoRecovery(max_retries=2, retry_interval_ms=1)
        state = recovery.recover(check_fn=lambda: False, restore_fn=lambda: None)
        assert state == RecoveryState.FAILED


# ── TC31~TC33: run_g89_gate() 통합 ───────────────────────────────────────────

class TestRunG89Gate:
    def test_tc31_run_g89_returns_dict(self):
        from literary_system.gates.chaos_resilience_gate import run_g89_gate
        result = run_g89_gate()
        assert isinstance(result, dict)
        assert result["gate"] == "G89"

    def test_tc32_run_g89_has_required_keys(self):
        from literary_system.gates.chaos_resilience_gate import run_g89_gate
        result = run_g89_gate()
        for key in ("gate", "pass", "passed", "passed_count", "total_count", "checkpoints"):
            assert key in result, f"키 없음: {key}"

    def test_tc33_run_g89_six_checkpoints(self):
        from literary_system.gates.chaos_resilience_gate import run_g89_gate
        result = run_g89_gate()
        assert result["total_count"] == 6
        assert len(result["checkpoints"]) == 6
