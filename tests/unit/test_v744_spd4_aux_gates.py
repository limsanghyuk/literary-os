"""tests/unit/test_v744_spd4_aux_gates.py

V744: SP-D.4 보조 게이트 3종 단위 테스트 (G92·G93·G94)
ADR-205, ADR-206, ADR-207

합격 기준:
  - G92 PS-1~PS-5: 5/5 PASS
  - G93 SP-1~SP-5: 5/5 PASS
  - G94 OC-1~OC-5: 5/5 PASS
  - 통합 run_spd4_aux_gates(): 15/15 PASS

테스트 설계 원칙:
  LLM-0: 외부 LLM 호출 없음.
  G32: print() 사용 금지.
"""

from __future__ import annotations

import importlib
import sys
from pathlib import Path
from typing import Any, Dict, List

import pytest

# ── 경로 설정 ──────────────────────────────────────────────────────────────
_REPO_ROOT = Path(__file__).resolve().parents[3]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

from literary_system.gates.spd4_aux_gates import (
    API_P99_SLO_MS,
    AGENT_RTT_SLO_MS,
    BACKUP_LATENCY_MS,
    AuxCheckResult,
    AuxGateResult,
    _check_ps1_agent_bus_import,
    _check_ps2_circuit_breaker_states,
    _check_ps3_slo_constants,
    _check_ps4_latency_percentile,
    _check_ps5_backup_latency,
    _check_sp1_zero_trust_import,
    _check_sp2_token_claims,
    _check_sp3_plugin_whitelist,
    _check_sp4_tenant_authority_isolation,
    _check_sp5_audit_log_structure,
    _check_oc1_otel_span,
    _check_oc2_trace_context_roundtrip,
    _check_oc3_prometheus_snapshot,
    _check_oc4_phase_e_manifest_validator,
    _check_oc5_dr_e2e_observability,
    run_g92_performance_slo,
    run_g93_security_posture,
    run_g94_observability_completeness,
    run_spd4_aux_gates,
)


# ═══════════════════════════════════════════════════════════════════════════
# 헬퍼
# ═══════════════════════════════════════════════════════════════════════════

def _assert_check(result: AuxCheckResult, expected_id: str, expected_pass: bool) -> None:
    assert isinstance(result, AuxCheckResult)
    assert result.check_id == expected_id
    assert result.passed == expected_pass, (
        f"{expected_id} expected passed={expected_pass}, got {result.passed}: {result.message}"
    )
    assert isinstance(result.message, str) and result.message


# ═══════════════════════════════════════════════════════════════════════════
# AuxCheckResult / AuxGateResult 데이터클래스 검증
# ═══════════════════════════════════════════════════════════════════════════

class TestAuxDataclasses:
    def test_check_result_to_dict_keys(self) -> None:
        r = AuxCheckResult("PS-1", "desc", True, "ok")
        d = r.to_dict()
        assert set(d.keys()) == {"check_id", "description", "passed", "message"}

    def test_check_result_to_dict_values(self) -> None:
        r = AuxCheckResult("SP-3", "whitelist", False, "missing")
        d = r.to_dict()
        assert d["check_id"] == "SP-3"
        assert d["passed"] is False
        assert d["message"] == "missing"

    def test_gate_result_to_dict_keys(self) -> None:
        gr = AuxGateResult("G92", "Perf SLO", [], False, 5, 0, "FAIL")
        d = gr.to_dict()
        assert set(d.keys()) == {
            "gate", "gate_name", "passed", "passed_count",
            "total_checks", "summary", "checks", "error"
        }

    def test_gate_result_checks_serialized(self) -> None:
        c = AuxCheckResult("OC-1", "span", True, "ok")
        gr = AuxGateResult("G94", "Obs", [c], True, 1, 1, "PASS")
        d = gr.to_dict()
        assert len(d["checks"]) == 1
        assert d["checks"][0]["check_id"] == "OC-1"

    def test_gate_result_error_default_none(self) -> None:
        gr = AuxGateResult("G93", "Security", [], False, 5, 0)
        assert gr.error is None


# ═══════════════════════════════════════════════════════════════════════════
# SLO 상수 검증
# ═══════════════════════════════════════════════════════════════════════════

class TestSloConstants:
    def test_api_p99_threshold(self) -> None:
        assert API_P99_SLO_MS == 200.0

    def test_agent_rtt_threshold(self) -> None:
        assert AGENT_RTT_SLO_MS == 50.0

    def test_backup_latency_threshold(self) -> None:
        assert BACKUP_LATENCY_MS == 100.0

    def test_p99_strictly_greater_rtt(self) -> None:
        assert API_P99_SLO_MS > AGENT_RTT_SLO_MS

    def test_backup_between_rtt_and_p99(self) -> None:
        assert AGENT_RTT_SLO_MS < BACKUP_LATENCY_MS <= API_P99_SLO_MS


# ═══════════════════════════════════════════════════════════════════════════
# G92 — Performance SLO Gate
# ═══════════════════════════════════════════════════════════════════════════

class TestG92Checks:
    def test_ps1_agent_bus_import(self) -> None:
        result = _check_ps1_agent_bus_import()
        _assert_check(result, "PS-1", True)

    def test_ps1_returns_aux_check_result(self) -> None:
        assert isinstance(_check_ps1_agent_bus_import(), AuxCheckResult)

    def test_ps2_circuit_breaker_states(self) -> None:
        result = _check_ps2_circuit_breaker_states()
        _assert_check(result, "PS-2", True)

    def test_ps2_message_contains_closed(self) -> None:
        result = _check_ps2_circuit_breaker_states()
        assert "CLOSED" in result.message.upper() or "상태" in result.message

    def test_ps3_slo_constants(self) -> None:
        result = _check_ps3_slo_constants()
        _assert_check(result, "PS-3", True)

    def test_ps3_message_contains_ms(self) -> None:
        result = _check_ps3_slo_constants()
        assert "ms" in result.message.lower() or "MS" in result.message

    def test_ps4_latency_percentile(self) -> None:
        result = _check_ps4_latency_percentile()
        _assert_check(result, "PS-4", True)

    def test_ps4_p99_in_range(self) -> None:
        result = _check_ps4_latency_percentile()
        assert result.passed
        # P99 값이 메시지에 포함돼야 함
        assert "P99" in result.message or "p99" in result.message.lower()

    def test_ps5_backup_latency(self) -> None:
        result = _check_ps5_backup_latency()
        _assert_check(result, "PS-5", True)

    def test_ps5_latency_within_slo(self) -> None:
        result = _check_ps5_backup_latency()
        assert result.passed
        assert "ms" in result.message.lower() or "백업" in result.message


class TestG92Gate:
    def test_run_g92_returns_aux_gate_result(self) -> None:
        assert isinstance(run_g92_performance_slo(), AuxGateResult)

    def test_run_g92_gate_id(self) -> None:
        r = run_g92_performance_slo()
        assert r.gate == "G92"

    def test_run_g92_total_checks(self) -> None:
        r = run_g92_performance_slo()
        assert r.total_checks == 5

    def test_run_g92_all_passed(self) -> None:
        r = run_g92_performance_slo()
        assert r.passed is True

    def test_run_g92_passed_count(self) -> None:
        r = run_g92_performance_slo()
        assert r.passed_count == 5

    def test_run_g92_checks_count(self) -> None:
        r = run_g92_performance_slo()
        assert len(r.checks) == 5

    def test_run_g92_check_ids(self) -> None:
        r = run_g92_performance_slo()
        ids = [c.check_id for c in r.checks]
        assert ids == ["PS-1", "PS-2", "PS-3", "PS-4", "PS-5"]


# ═══════════════════════════════════════════════════════════════════════════
# G93 — Security Posture Gate
# ═══════════════════════════════════════════════════════════════════════════

class TestG93Checks:
    def test_sp1_zero_trust_import(self) -> None:
        result = _check_sp1_zero_trust_import()
        _assert_check(result, "SP-1", True)

    def test_sp2_token_claims(self) -> None:
        result = _check_sp2_token_claims()
        _assert_check(result, "SP-2", True)

    def test_sp2_message_has_tenant_id(self) -> None:
        result = _check_sp2_token_claims()
        assert "tenant_id" in result.message

    def test_sp3_plugin_whitelist(self) -> None:
        result = _check_sp3_plugin_whitelist()
        _assert_check(result, "SP-3", True)

    def test_sp4_tenant_authority_isolation(self) -> None:
        result = _check_sp4_tenant_authority_isolation()
        _assert_check(result, "SP-4", True)

    def test_sp4_message_indicates_block(self) -> None:
        result = _check_sp4_tenant_authority_isolation()
        assert "차단" in result.message or "PASS" in result.message

    def test_sp5_audit_log_structure(self) -> None:
        result = _check_sp5_audit_log_structure()
        _assert_check(result, "SP-5", True)


class TestG93Gate:
    def test_run_g93_returns_aux_gate_result(self) -> None:
        assert isinstance(run_g93_security_posture(), AuxGateResult)

    def test_run_g93_gate_id(self) -> None:
        r = run_g93_security_posture()
        assert r.gate == "G93"

    def test_run_g93_total_checks(self) -> None:
        r = run_g93_security_posture()
        assert r.total_checks == 5

    def test_run_g93_all_passed(self) -> None:
        r = run_g93_security_posture()
        assert r.passed is True

    def test_run_g93_passed_count(self) -> None:
        r = run_g93_security_posture()
        assert r.passed_count == 5

    def test_run_g93_check_ids(self) -> None:
        r = run_g93_security_posture()
        ids = [c.check_id for c in r.checks]
        assert ids == ["SP-1", "SP-2", "SP-3", "SP-4", "SP-5"]


# ═══════════════════════════════════════════════════════════════════════════
# G94 — Observability Completeness Gate
# ═══════════════════════════════════════════════════════════════════════════

class TestG94Checks:
    def test_oc1_otel_span(self) -> None:
        result = _check_oc1_otel_span()
        _assert_check(result, "OC-1", True)

    def test_oc1_message_mentions_span(self) -> None:
        result = _check_oc1_otel_span()
        assert "스팬" in result.message or "span" in result.message.lower()

    def test_oc2_trace_context_roundtrip(self) -> None:
        result = _check_oc2_trace_context_roundtrip()
        _assert_check(result, "OC-2", True)

    def test_oc2_message_has_traceparent(self) -> None:
        result = _check_oc2_trace_context_roundtrip()
        assert "traceparent" in result.message

    def test_oc3_prometheus_snapshot(self) -> None:
        result = _check_oc3_prometheus_snapshot()
        _assert_check(result, "OC-3", True)

    def test_oc4_phase_e_manifest_validator(self) -> None:
        result = _check_oc4_phase_e_manifest_validator()
        _assert_check(result, "OC-4", True)

    def test_oc4_message_mentions_deploy(self) -> None:
        result = _check_oc4_phase_e_manifest_validator()
        # OC-4는 deploy/ 패키지 연결을 검증
        assert "deploy" in result.message.lower() or "8/8" in result.message

    def test_oc5_dr_e2e_observability(self) -> None:
        result = _check_oc5_dr_e2e_observability()
        _assert_check(result, "OC-5", True)

    def test_oc5_message_has_backup_restore(self) -> None:
        result = _check_oc5_dr_e2e_observability()
        # backup 또는 restore 키워드 포함
        assert ("backup" in result.message.lower()
                or "restore" in result.message.lower()
                or "DR" in result.message)


class TestG94Gate:
    def test_run_g94_returns_aux_gate_result(self) -> None:
        assert isinstance(run_g94_observability_completeness(), AuxGateResult)

    def test_run_g94_gate_id(self) -> None:
        r = run_g94_observability_completeness()
        assert r.gate == "G94"

    def test_run_g94_total_checks(self) -> None:
        r = run_g94_observability_completeness()
        assert r.total_checks == 5

    def test_run_g94_all_passed(self) -> None:
        r = run_g94_observability_completeness()
        assert r.passed is True

    def test_run_g94_passed_count(self) -> None:
        r = run_g94_observability_completeness()
        assert r.passed_count == 5

    def test_run_g94_check_ids(self) -> None:
        r = run_g94_observability_completeness()
        ids = [c.check_id for c in r.checks]
        assert ids == ["OC-1", "OC-2", "OC-3", "OC-4", "OC-5"]


# ═══════════════════════════════════════════════════════════════════════════
# 통합: run_spd4_aux_gates()
# ═══════════════════════════════════════════════════════════════════════════

class TestRunSpd4AuxGates:
    """run_spd4_aux_gates() 통합 결과 검증."""

    @pytest.fixture(scope="class")
    def result(self) -> Dict[str, Any]:
        return run_spd4_aux_gates()

    def test_returns_dict(self, result: Dict[str, Any]) -> None:
        assert isinstance(result, dict)

    def test_version_field(self, result: Dict[str, Any]) -> None:
        assert result.get("version") == "V744"

    def test_gates_key_exists(self, result: Dict[str, Any]) -> None:
        assert "gates" in result

    def test_gates_has_three_gates(self, result: Dict[str, Any]) -> None:
        assert set(result["gates"].keys()) == {"G92", "G93", "G94"}

    def test_all_passed_true(self, result: Dict[str, Any]) -> None:
        assert result["all_passed"] is True

    def test_total_checks_fifteen(self, result: Dict[str, Any]) -> None:
        assert result["total_checks"] == 15

    def test_total_passed_fifteen(self, result: Dict[str, Any]) -> None:
        assert result["total_passed"] == 15

    def test_summary_contains_pass(self, result: Dict[str, Any]) -> None:
        assert "PASS" in result["summary"]

    def test_summary_contains_15_15(self, result: Dict[str, Any]) -> None:
        assert "15/15" in result["summary"]

    def test_g92_passed(self, result: Dict[str, Any]) -> None:
        assert result["gates"]["G92"]["passed"] is True

    def test_g93_passed(self, result: Dict[str, Any]) -> None:
        assert result["gates"]["G93"]["passed"] is True

    def test_g94_passed(self, result: Dict[str, Any]) -> None:
        assert result["gates"]["G94"]["passed"] is True

    def test_g92_five_checks(self, result: Dict[str, Any]) -> None:
        assert result["gates"]["G92"]["passed_count"] == 5

    def test_g93_five_checks(self, result: Dict[str, Any]) -> None:
        assert result["gates"]["G93"]["passed_count"] == 5

    def test_g94_five_checks(self, result: Dict[str, Any]) -> None:
        assert result["gates"]["G94"]["passed_count"] == 5

    def test_each_check_has_required_fields(self, result: Dict[str, Any]) -> None:
        required = {"check_id", "description", "passed", "message"}
        for gate_key, gate_data in result["gates"].items():
            for c in gate_data["checks"]:
                assert set(c.keys()) >= required, (
                    f"{gate_key} check missing keys: {required - set(c.keys())}"
                )

    def test_no_failed_checks(self, result: Dict[str, Any]) -> None:
        for gate_key, gate_data in result["gates"].items():
            for c in gate_data["checks"]:
                assert c["passed"] is True, (
                    f"{c['check_id']} FAILED: {c['message']}"
                )
