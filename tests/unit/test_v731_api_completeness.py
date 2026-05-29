"""V731 — G86 API Completeness Gate 테스트 (50 TC)."""
import sys
import os
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from literary_system.gates.api_completeness_gate import (
    ApiCompletenessGate,
    GateCheckResult,
    ADR_193,
)


# ── 픽스처 ────────────────────────────────────────────────────────────────────

@pytest.fixture
def gate():
    return ApiCompletenessGate()


# ── TC01~TC06: Gate 기본 실행 ──────────────────────────────────────────────────

def test_tc01_gate_id(gate):
    assert gate.GATE_ID == "G86"

def test_tc02_gate_run_returns_tuple(gate):
    result = gate.run()
    assert isinstance(result, tuple)
    assert len(result) == 2

def test_tc03_gate_run_pass_is_bool(gate):
    passed, _ = gate.run()
    assert isinstance(passed, bool)

def test_tc04_gate_run_results_is_list(gate):
    _, results = gate.run()
    assert isinstance(results, list)

def test_tc05_gate_run_six_checks(gate):
    _, results = gate.run()
    assert len(results) == 6

def test_tc06_gate_overall_pass(gate):
    passed, results = gate.run()
    assert passed == all(r.passed for r in results)


# ── TC07~TC12: GateCheckResult 구조 ───────────────────────────────────────────

def test_tc07_check_result_has_check_id(gate):
    _, results = gate.run()
    for r in results:
        assert hasattr(r, "check_id")
        assert isinstance(r.check_id, str)

def test_tc08_check_result_has_description(gate):
    _, results = gate.run()
    for r in results:
        assert hasattr(r, "description")
        assert len(r.description) > 0

def test_tc09_check_result_has_passed(gate):
    _, results = gate.run()
    for r in results:
        assert hasattr(r, "passed")
        assert isinstance(r.passed, bool)

def test_tc10_check_result_has_message(gate):
    _, results = gate.run()
    for r in results:
        assert hasattr(r, "message")
        assert isinstance(r.message, str)

def test_tc11_check_result_to_dict(gate):
    _, results = gate.run()
    for r in results:
        d = r.to_dict()
        assert "check_id" in d
        assert "description" in d
        assert "passed" in d
        assert "message" in d

def test_tc12_check_result_to_dict_types(gate):
    _, results = gate.run()
    d = results[0].to_dict()
    assert isinstance(d["check_id"], str)
    assert isinstance(d["passed"], bool)


# ── TC13~TC18: A1 ~ A6 체크포인트 ID ──────────────────────────────────────────

def test_tc13_a1_check_id(gate):
    _, results = gate.run()
    ids = [r.check_id for r in results]
    assert "A1" in ids

def test_tc14_a2_check_id(gate):
    _, results = gate.run()
    ids = [r.check_id for r in results]
    assert "A2" in ids

def test_tc15_a3_check_id(gate):
    _, results = gate.run()
    ids = [r.check_id for r in results]
    assert "A3" in ids

def test_tc16_a4_check_id(gate):
    _, results = gate.run()
    ids = [r.check_id for r in results]
    assert "A4" in ids

def test_tc17_a5_check_id(gate):
    _, results = gate.run()
    ids = [r.check_id for r in results]
    assert "A5" in ids

def test_tc18_a6_check_id(gate):
    _, results = gate.run()
    ids = [r.check_id for r in results]
    assert "A6" in ids


# ── TC19~TC24: A1~A6 각 PASS ──────────────────────────────────────────────────

def _get_result(gate, check_id):
    _, results = gate.run()
    return next(r for r in results if r.check_id == check_id)

def test_tc19_a1_pass(gate):
    assert _get_result(gate, "A1").passed is True

def test_tc20_a2_pass(gate):
    assert _get_result(gate, "A2").passed is True

def test_tc21_a3_pass(gate):
    assert _get_result(gate, "A3").passed is True

def test_tc22_a4_pass(gate):
    assert _get_result(gate, "A4").passed is True

def test_tc23_a5_pass(gate):
    assert _get_result(gate, "A5").passed is True

def test_tc24_a6_pass(gate):
    assert _get_result(gate, "A6").passed is True


# ── TC25~TC30: 각 체크 메서드 직접 호출 ───────────────────────────────────────

def test_tc25_check_a1_direct(gate):
    result = gate._check_a1()
    assert isinstance(result, GateCheckResult)

def test_tc26_check_a2_direct(gate):
    result = gate._check_a2()
    assert isinstance(result, GateCheckResult)

def test_tc27_check_a3_direct(gate):
    result = gate._check_a3()
    assert isinstance(result, GateCheckResult)

def test_tc28_check_a4_direct(gate):
    result = gate._check_a4()
    assert isinstance(result, GateCheckResult)

def test_tc29_check_a5_direct(gate):
    result = gate._check_a5()
    assert isinstance(result, GateCheckResult)

def test_tc30_check_a6_direct(gate):
    result = gate._check_a6()
    assert isinstance(result, GateCheckResult)


# ── TC31~TC36: GateCheckResult 생성자 ────────────────────────────────────────

def test_tc31_gate_check_result_init():
    r = GateCheckResult("X1", "test desc", True, "msg")
    assert r.check_id == "X1"
    assert r.description == "test desc"
    assert r.passed is True
    assert r.message == "msg"

def test_tc32_gate_check_result_default_message():
    r = GateCheckResult("X1", "desc", False)
    assert r.message == ""

def test_tc33_gate_check_result_to_dict_keys():
    r = GateCheckResult("A1", "desc", True, "ok")
    d = r.to_dict()
    assert set(d.keys()) == {"check_id", "description", "passed", "message"}

def test_tc34_gate_check_result_passed_false():
    r = GateCheckResult("X1", "desc", False, "fail")
    assert r.passed is False

def test_tc35_gate_check_result_to_dict_passed_bool():
    r = GateCheckResult("A1", "desc", True, "msg")
    assert r.to_dict()["passed"] is True

def test_tc36_gate_check_result_to_dict_message():
    r = GateCheckResult("A1", "desc", True, "hello")
    assert r.to_dict()["message"] == "hello"


# ── TC37~TC42: ADR-193 메타데이터 ────────────────────────────────────────────

def test_tc37_adr_193_exists():
    assert ADR_193 is not None

def test_tc38_adr_193_id():
    assert ADR_193["id"] == "ADR-193"

def test_tc39_adr_193_status():
    assert ADR_193["status"] == "accepted"

def test_tc40_adr_193_version():
    assert ADR_193["version"] == "V731"

def test_tc41_adr_193_has_title():
    assert "title" in ADR_193
    assert len(ADR_193["title"]) > 0

def test_tc42_adr_193_has_decision():
    assert "decision" in ADR_193
    assert "G86" in ADR_193["decision"]


# ── TC43~TC50: release_gate.py GATES 등록 확인 ───────────────────────────────

def test_tc43_g86_in_gates():
    from literary_system.gates.release_gate import GATES
    ids = [g[0] for g in GATES]
    assert "api_completeness_g86" in ids

def test_tc44_g86_gate_name():
    from literary_system.gates.release_gate import GATES
    entry = next(g for g in GATES if g[0] == "api_completeness_g86")
    assert "G86" in entry[1]

def test_tc45_g86_position_after_g85():
    from literary_system.gates.release_gate import GATES
    ids = [g[0] for g in GATES]
    g85_idx = ids.index("agent_workflow_g85")
    g86_idx = ids.index("api_completeness_g86")
    assert g86_idx == g85_idx + 1

def test_tc46_g86_position_before_g87():
    from literary_system.gates.release_gate import GATES
    ids = [g[0] for g in GATES]
    g86_idx = ids.index("api_completeness_g86")
    g87_idx = ids.index("plugin_registry_g87")
    assert g87_idx == g86_idx + 1

def test_tc47_gates_total_91():
    from literary_system.gates.release_gate import GATES
    assert len(GATES) == 91

def test_tc48_g86_callable():
    from literary_system.gates.release_gate import GATES
    entry = next(g for g in GATES if g[0] == "api_completeness_g86")
    fn = entry[2]
    assert callable(fn)

def test_tc49_g86_fn_returns_dict():
    from literary_system.gates.release_gate import GATES
    entry = next(g for g in GATES if g[0] == "api_completeness_g86")
    result = entry[2]()
    assert isinstance(result, dict)
    assert "pass" in result

def test_tc50_g86_fn_pass_true():
    from literary_system.gates.release_gate import GATES
    entry = next(g for g in GATES if g[0] == "api_completeness_g86")
    result = entry[2]()
    assert result["pass"] is True
