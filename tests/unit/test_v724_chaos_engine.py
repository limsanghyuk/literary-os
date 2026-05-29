"""V724 — test_v724_chaos_engine.py: ChaosEngine + FaultInjector 33 TC"""
from __future__ import annotations
import pytest, time
from literary_system.chaos.chaos_engine import ChaosEngine, FaultSpec, FaultType, FaultResult
from literary_system.chaos.fault_injector import FaultInjector, InjectionPoint

def make_spec(fid="f1", ft=FaultType.NETWORK_PARTITION, target="svc", duration_ms=0):
    return FaultSpec(fid, ft, target, duration_ms=duration_ms)

# TC01~TC07: FaultSpec
def test_tc01_faultspec_valid():
    s = make_spec()
    assert s.fault_id == "f1" and s.fault_type == FaultType.NETWORK_PARTITION

def test_tc02_faultspec_invalid_intensity():
    with pytest.raises(ValueError): FaultSpec("x", FaultType.CPU_SPIKE, "t", intensity=1.5)

def test_tc03_faultspec_invalid_probability():
    with pytest.raises(ValueError): FaultSpec("x", FaultType.CPU_SPIKE, "t", probability=-0.1)

def test_tc04_faultspec_invalid_duration():
    with pytest.raises(ValueError): FaultSpec("x", FaultType.CPU_SPIKE, "t", duration_ms=-1)

def test_tc05_faultspec_frozen():
    s = make_spec()
    with pytest.raises((AttributeError, TypeError)): s.fault_id = "other"

def test_tc06_fault_type_enum():
    assert FaultType.NETWORK_PARTITION.value == "network_partition"
    assert len(FaultType) == 5

def test_tc07_fault_result_elapsed():
    r = FaultResult("f1", FaultType.CPU_SPIKE, "t", injected=True)
    time.sleep(0.01)
    r.finished_at = time.time()
    assert r.elapsed_ms >= 10

# TC08~TC15: ChaosEngine 등록/활성화
def test_tc08_register_and_list():
    e = ChaosEngine()
    e.register(make_spec("f1")); e.register(make_spec("f2"))
    assert len(e.list_specs()) == 2

def test_tc09_activate_deactivate():
    e = ChaosEngine()
    e.register(make_spec("f1"))
    e.activate("f1")
    assert e.is_active("f1")
    e.deactivate("f1")
    assert not e.is_active("f1")

def test_tc10_activate_unregistered():
    e = ChaosEngine()
    with pytest.raises(KeyError): e.activate("ghost")

def test_tc11_unregister():
    e = ChaosEngine()
    e.register(make_spec("f1"))
    assert e.unregister("f1")
    assert len(e.list_specs()) == 0

def test_tc12_unregister_nonexistent():
    e = ChaosEngine()
    assert not e.unregister("ghost")

def test_tc13_list_active():
    e = ChaosEngine()
    e.register(make_spec("f1")); e.register(make_spec("f2"))
    e.activate("f1")
    assert e.list_active() == ["f1"]

def test_tc14_disabled_engine():
    e = ChaosEngine(enabled=False)
    e.register(make_spec("f1")); e.activate("f1")
    r = e.inject("f1")
    assert not r.injected  # disabled → 주입 안 됨

def test_tc15_inject_unregistered():
    e = ChaosEngine()
    with pytest.raises(KeyError): e.inject("ghost")

# TC16~TC22: ChaosEngine 주입
def test_tc16_inject_active():
    e = ChaosEngine()
    e.register(make_spec("f1")); e.activate("f1")
    r = e.inject("f1")
    assert r.injected

def test_tc17_inject_inactive():
    e = ChaosEngine()
    e.register(make_spec("f1"))  # 활성화 안 함
    r = e.inject("f1")
    assert not r.injected

def test_tc18_inject_with_handler():
    called = []
    e = ChaosEngine()
    e.register_handler(FaultType.CPU_SPIKE, lambda spec: called.append(spec))
    e.register(make_spec("f1", FaultType.CPU_SPIKE)); e.activate("f1")
    e.inject("f1")
    assert len(called) == 1

def test_tc19_inject_all_active():
    e = ChaosEngine()
    for i in range(3):
        s = FaultSpec(f"f{i}", FaultType.MEMORY_PRESSURE, "t", duration_ms=0)
        e.register(s); e.activate(f"f{i}")
    results = e.inject_all_active()
    assert len(results) == 3
    assert all(r.injected for r in results)

def test_tc20_history_grows():
    e = ChaosEngine()
    e.register(make_spec("f1")); e.activate("f1")
    e.inject("f1"); e.inject("f1")
    assert len(e.history()) >= 2

def test_tc21_stats():
    e = ChaosEngine()
    e.register(make_spec("f1")); e.activate("f1")
    e.inject("f1")
    s = e.stats()
    assert s["registered"] == 1 and s["active"] == 1 and s["injected"] >= 1

def test_tc22_reset_history():
    e = ChaosEngine()
    e.register(make_spec("f1")); e.activate("f1")
    e.inject("f1")
    e.reset_history()
    assert len(e.history()) == 0

# TC23~TC28: FaultInjector
def test_tc23_injector_inject_before():
    e = ChaosEngine(); e.register(make_spec("f1")); e.activate("f1")
    inj = FaultInjector(e)
    result = inj.inject_before("f1", lambda: "ok")
    assert result == "ok"

def test_tc24_injector_inject_after():
    e = ChaosEngine(); e.register(make_spec("f1")); e.activate("f1")
    inj = FaultInjector(e)
    result = inj.inject_after("f1", lambda: "ok")
    assert result == "ok"

def test_tc25_injector_wrap_before():
    e = ChaosEngine(); e.register(make_spec("f1")); e.activate("f1")
    inj = FaultInjector(e)
    @inj.wrap("f1", InjectionPoint.BEFORE)
    def my_fn(): return 42
    assert my_fn() == 42
    assert inj.injected_count() >= 1

def test_tc26_injector_wrap_both():
    e = ChaosEngine(); e.register(make_spec("f1")); e.activate("f1")
    inj = FaultInjector(e)
    @inj.wrap("f1", InjectionPoint.BOTH)
    def my_fn(): return "x"
    my_fn()
    assert len(inj.records()) >= 2

def test_tc27_injector_records():
    e = ChaosEngine(); e.register(make_spec("f1")); e.activate("f1")
    inj = FaultInjector(e)
    inj.inject_before("f1", lambda: None)
    recs = inj.records()
    assert len(recs) >= 1

def test_tc28_injection_point_enum():
    assert InjectionPoint.BEFORE.value == "before"
    assert InjectionPoint.AFTER.value == "after"
    assert InjectionPoint.BOTH.value == "both"

# TC29~TC33: import 및 구조 검증
def test_tc29_all_fault_types():
    expected = {"network_partition","memory_pressure","cpu_spike","disk_full","service_crash"}
    actual = {ft.value for ft in FaultType}
    assert actual == expected

def test_tc30_chaos_package_import():
    from literary_system.chaos import ChaosEngine, FaultSpec, FaultType, FaultResult, FaultInjector, InjectionPoint
    assert all([ChaosEngine, FaultSpec, FaultType, FaultResult, FaultInjector, InjectionPoint])

def test_tc31_g32_no_print():
    import literary_system.chaos.chaos_engine as m
    src = open(m.__file__, encoding="utf-8").read()
    lines = [l for l in src.splitlines() if l.strip().startswith("print(")]
    assert len(lines) == 0

def test_tc32_faultresult_no_error():
    r = FaultResult("f1", FaultType.DISK_FULL, "t", injected=True)
    assert r.error is None

def test_tc33_probability_zero_no_inject():
    import random
    e = ChaosEngine()
    s = FaultSpec("f1", FaultType.CPU_SPIKE, "t", probability=0.0)
    e.register(s); e.activate("f1")
    results = [e.inject("f1") for _ in range(10)]
    assert all(not r.injected for r in results)
