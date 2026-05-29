"""
test_v664_b2b_partner_gate.py — V664 B2BPartnerGate G71 테스트 (33 TC)

DEV_MODE: False (ADR-034)
LLM-0: 외부 LLM 호출 없음
"""
from __future__ import annotations

import pytest
from literary_system.gates.b2b_partner_gate import (
    B2BPartnerGate,
    B2BPartnerReport,
    LOIRecord,
    LOIRepository,
    LOIStatus,
    LOIValidationResult,
    MIN_LOI_COUNT,
    _make_demo_loi,
    _validate_loi,
    run_g71,
)


# ─── 픽스처 ──────────────────────────────────────────────────────────────────

def _signed_loi(idx: int = 0, loi_id: str = "LOIS-001", partner: str = "PartnerA") -> LOIRecord:
    return LOIRecord(
        loi_id=loi_id,
        partner_name=partner,
        status=LOIStatus.SIGNED,
        signed_date="2026-05-15",
        contact_email=f"partner{idx}@example.com",
        annual_value_krw=100_000_000,
        api_scope=["analyze", "generate"],
    )


def _executed_loi(idx: int = 0) -> LOIRecord:
    return LOIRecord(
        loi_id=f"LOIS-EX-{idx:03d}",
        partner_name=f"ExecutedPartner{idx}",
        status=LOIStatus.EXECUTED,
        signed_date="2026-04-01",
        contact_email=f"exec{idx}@corp.com",
        annual_value_krw=200_000_000,
        api_scope=["repair", "predict"],
    )


def _make_three_valid_lois() -> list[LOIRecord]:
    return [
        _signed_loi(0, "LOIS-001", "PartnerA"),
        _signed_loi(1, "LOIS-002", "PartnerB"),
        _signed_loi(2, "LOIS-003", "PartnerC"),
    ]


# ─── LOIStatus 테스트 ────────────────────────────────────────────────────────

class TestLOIStatus:
    def test_tc01_signed_is_valid_status(self):
        """TC01: SIGNED 상태 LOI는 유효."""
        loi = _signed_loi()
        assert loi.is_valid is True

    def test_tc02_executed_is_valid_status(self):
        """TC02: EXECUTED 상태 LOI는 유효."""
        loi = _executed_loi()
        assert loi.is_valid is True

    def test_tc03_draft_is_invalid(self):
        """TC03: DRAFT 상태 LOI는 무효."""
        loi = _signed_loi()
        loi.status = LOIStatus.DRAFT
        assert loi.is_valid is False

    def test_tc04_expired_is_invalid(self):
        """TC04: EXPIRED 상태 LOI는 무효."""
        loi = _signed_loi()
        loi.status = LOIStatus.EXPIRED
        assert loi.is_valid is False

    def test_tc05_cancelled_is_invalid(self):
        """TC05: CANCELLED 상태 LOI는 무효."""
        loi = _signed_loi()
        loi.status = LOIStatus.CANCELLED
        assert loi.is_valid is False


# ─── LOIRecord 테스트 ────────────────────────────────────────────────────────

class TestLOIRecord:
    def test_tc06_to_dict_keys(self):
        """TC06: to_dict()에 필수 키 포함."""
        loi = _signed_loi()
        d = loi.to_dict()
        for k in ("loi_id", "partner_name", "status", "signed_date", "contact_email",
                  "annual_value_krw", "api_scope", "notes", "is_valid"):
            assert k in d

    def test_tc07_to_dict_status_is_string(self):
        """TC07: to_dict()의 status는 문자열."""
        loi = _signed_loi()
        assert isinstance(loi.to_dict()["status"], str)

    def test_tc08_zero_annual_value_ok(self):
        """TC08: annual_value_krw=0은 허용."""
        loi = _signed_loi()
        loi.annual_value_krw = 0
        result = _validate_loi(loi)
        assert result.valid is True

    def test_tc09_negative_annual_value_invalid(self):
        """TC09: annual_value_krw 음수는 유효성 검사 실패."""
        loi = _signed_loi()
        loi.annual_value_krw = -1
        result = _validate_loi(loi)
        assert result.valid is False
        assert any("음수" in r for r in result.reasons)


# ─── _validate_loi 테스트 ────────────────────────────────────────────────────

class TestValidateLOI:
    def test_tc10_valid_loi_passes(self):
        """TC10: 유효한 LOI는 검증 통과."""
        loi = _signed_loi()
        result = _validate_loi(loi)
        assert result.valid is True
        assert len(result.reasons) == 0

    def test_tc11_missing_loi_id(self):
        """TC11: loi_id 누락 시 실패."""
        loi = _signed_loi()
        loi.loi_id = ""
        result = _validate_loi(loi)
        assert result.valid is False
        assert any("loi_id" in r for r in result.reasons)

    def test_tc12_missing_partner_name(self):
        """TC12: partner_name 누락 시 실패."""
        loi = _signed_loi()
        loi.partner_name = ""
        result = _validate_loi(loi)
        assert result.valid is False

    def test_tc13_invalid_email(self):
        """TC13: 이메일 형식 오류 시 실패."""
        loi = _signed_loi()
        loi.contact_email = "not-an-email"
        result = _validate_loi(loi)
        assert result.valid is False
        assert any("email" in r.lower() for r in result.reasons)

    def test_tc14_invalid_date_format(self):
        """TC14: 날짜 형식 오류 시 실패."""
        loi = _signed_loi()
        loi.signed_date = "15-05-2026"
        result = _validate_loi(loi)
        assert result.valid is False

    def test_tc15_draft_status_invalid(self):
        """TC15: DRAFT 상태 LOI는 검증 실패."""
        loi = _signed_loi()
        loi.status = LOIStatus.DRAFT
        result = _validate_loi(loi)
        assert result.valid is False
        assert any("미승인" in r or "상태" in r for r in result.reasons)

    def test_tc16_validation_result_has_loi_id(self):
        """TC16: 검증 결과에 loi_id 포함."""
        loi = _signed_loi(loi_id="TEST-001")
        result = _validate_loi(loi)
        assert result.loi_id == "TEST-001"


# ─── LOIRepository 테스트 ────────────────────────────────────────────────────

class TestLOIRepository:
    def test_tc17_add_and_all(self):
        """TC17: LOI 추가 및 전체 조회."""
        repo = LOIRepository()
        repo.add(_signed_loi(0, "L-001"))
        repo.add(_signed_loi(1, "L-002"))
        assert len(repo.all()) == 2

    def test_tc18_duplicate_id_raises(self):
        """TC18: 중복 loi_id 추가 시 ValueError."""
        repo = LOIRepository()
        repo.add(_signed_loi(0, "L-001"))
        with pytest.raises(ValueError, match="중복"):
            repo.add(_signed_loi(1, "L-001"))

    def test_tc19_valid_count(self):
        """TC19: valid_count는 SIGNED/EXECUTED만 카운트."""
        repo = LOIRepository()
        repo.add(_signed_loi(0, "L-001"))
        draft = _signed_loi(1, "L-002")
        draft.status = LOIStatus.DRAFT
        repo.add(draft)
        assert repo.valid_count() == 1

    def test_tc20_total_annual_value(self):
        """TC20: 유효 LOI의 총 연간 금액 합산."""
        repo = LOIRepository()
        loi1 = _signed_loi(0, "L-001")
        loi1.annual_value_krw = 100_000_000
        loi2 = _signed_loi(1, "L-002")
        loi2.annual_value_krw = 200_000_000
        repo.add(loi1)
        repo.add(loi2)
        assert repo.total_annual_value() == 300_000_000

    def test_tc21_get_existing(self):
        """TC21: get()으로 개별 LOI 조회."""
        repo = LOIRepository()
        repo.add(_signed_loi(0, "L-001"))
        assert repo.get("L-001") is not None

    def test_tc22_get_nonexistent_returns_none(self):
        """TC22: 없는 ID get() 시 None 반환."""
        repo = LOIRepository()
        assert repo.get("NONE") is None

    def test_tc23_clear_empties_repo(self):
        """TC23: clear() 후 all() 비어있음."""
        repo = LOIRepository()
        repo.add(_signed_loi(0, "L-001"))
        repo.clear()
        assert len(repo.all()) == 0


# ─── B2BPartnerGate 테스트 ──────────────────────────────────────────────────

class TestB2BPartnerGate:
    def test_tc24_three_valid_lois_pass(self):
        """TC24: 유효 LOI 3건으로 G71 통과."""
        gate = B2BPartnerGate()
        for loi in _make_three_valid_lois():
            gate.register_loi(loi)
        report = gate.run()
        assert report.passed is True

    def test_tc25_two_valid_lois_fail(self):
        """TC25: 유효 LOI 2건으로 G71 실패."""
        gate = B2BPartnerGate()
        gate.register_loi(_signed_loi(0, "L-001"))
        gate.register_loi(_signed_loi(1, "L-002"))
        report = gate.run()
        assert report.passed is False

    def test_tc26_zero_lois_fail(self):
        """TC26: LOI 0건으로 G71 실패."""
        gate = B2BPartnerGate()
        report = gate.run()
        assert report.passed is False
        assert report.valid_loi_count == 0

    def test_tc27_executed_lois_pass(self):
        """TC27: EXECUTED 상태 LOI 3건으로 G71 통과."""
        gate = B2BPartnerGate()
        for i in range(3):
            gate.register_loi(_executed_loi(i))
        report = gate.run()
        assert report.passed is True

    def test_tc28_mixed_status_counts_correctly(self):
        """TC28: SIGNED+EXECUTED 혼합 3건 통과, DRAFT 포함 시 실패."""
        gate = B2BPartnerGate()
        gate.register_loi(_signed_loi(0, "L-001"))
        gate.register_loi(_executed_loi(1))
        draft = _signed_loi(2, "L-DRAFT")
        draft.status = LOIStatus.DRAFT
        gate.register_loi(draft)
        report = gate.run()
        # draft는 검증 실패 → passed False
        assert report.passed is False

    def test_tc29_report_fields(self):
        """TC29: 보고서에 필수 필드 포함."""
        gate = B2BPartnerGate()
        for loi in _make_three_valid_lois():
            gate.register_loi(loi)
        report = gate.run()
        d = report.to_dict()
        for k in ("gate_id", "gate_name", "passed", "valid_loi_count",
                  "total_loi_count", "total_annual_value_krw", "elapsed_ms",
                  "errors", "loi_results"):
            assert k in d

    def test_tc30_gate_id_is_g71(self):
        """TC30: gate_id는 G71."""
        gate = B2BPartnerGate()
        report = gate.run()
        assert report.gate_id == "G71"

    def test_tc31_annual_value_summed(self):
        """TC31: 총 연간 금액이 집계됨."""
        gate = B2BPartnerGate()
        for i, loi in enumerate(_make_three_valid_lois()):
            loi.annual_value_krw = 100_000_000 * (i + 1)
            gate.register_loi(loi)
        report = gate.run()
        assert report.total_annual_value_krw == 600_000_000

    def test_tc32_summary_method(self):
        """TC32: summary() 메서드 결과 구조 확인."""
        gate = B2BPartnerGate()
        for loi in _make_three_valid_lois():
            gate.register_loi(loi)
        s = gate.summary()
        assert s["valid"] == 3
        assert s["ready"] is True
        assert "total_annual_value_krw" in s


# ─── run_g71 편의 함수 테스트 ────────────────────────────────────────────────

class TestRunG71:
    def test_tc33_run_g71_demo_passes(self):
        """TC33: run_g71() 데모 3건 자동 등록 → G71 PASS."""
        result = run_g71()
        assert result["passed"] is True
        assert result["valid_loi_count"] >= MIN_LOI_COUNT
        assert result["gate_id"] == "G71"
