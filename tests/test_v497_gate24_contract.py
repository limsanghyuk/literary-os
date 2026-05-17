"""
tests/test_v497_gate24_contract.py
V497 Hotfix: Gate24 반환 키 명세 계약 테스트 (G2 수정)

Gate24가 symbols_checked / symbols_passed / count / symbols_verified
모두 반환하는지 검증.
"""
import pytest
from literary_system.gates.gate24_slm_sp3 import run_gate24, _gate_slm_sp3_survival


class TestGate24Contract:
    def test_run_gate24_passes(self):
        result = run_gate24()
        assert result["pass"] is True, f"Gate24 FAIL: {result.get('errors')}"

    def test_gate24_has_symbols_verified(self):
        result = _gate_slm_sp3_survival()
        assert "symbols_verified" in result
        assert isinstance(result["symbols_verified"], list)

    def test_gate24_has_count(self):
        result = _gate_slm_sp3_survival()
        assert "count" in result
        assert isinstance(result["count"], int)
        assert result["count"] >= 30

    def test_gate24_has_symbols_checked(self):
        """G2 수정: symbols_checked 키 존재 확인."""
        result = _gate_slm_sp3_survival()
        assert "symbols_checked" in result, "G2: symbols_checked 키 누락"
        assert result["symbols_checked"] == result["count"]

    def test_gate24_has_symbols_passed(self):
        """G2 수정: symbols_passed 키 존재 확인."""
        result = _gate_slm_sp3_survival()
        assert "symbols_passed" in result, "G2: symbols_passed 키 누락"
        assert result["symbols_passed"] == result["count"]

    def test_gate24_adr008_checks(self):
        result = _gate_slm_sp3_survival()
        assert "adr" in result
        assert len(result["adr"]) == 3, f"ADR-008 항목 수 오류: {result['adr']}"

    def test_gate24_no_errors(self):
        result = _gate_slm_sp3_survival()
        assert result["errors"] == [], f"Gate24 에러: {result['errors']}"
