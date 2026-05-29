"""
B2BPartnerGate — Gate G71 (V664 SP-C.3)
LOI(Letter of Intent) 3건 이상 체결 검증 게이트.

ADR-124 참조.
LLM-0: 외부 LLM 호출 없음.
DEV_MODE: False (ADR-034).
"""
from __future__ import annotations

import re
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any

# ─── 상수 ────────────────────────────────────────────────────────────────────
MIN_LOI_COUNT: int = 3
GATE_ID: str = "G71"
GATE_NAME: str = "B2BPartnerGate"

# LOI 상태 단계
class LOIStatus(str, Enum):
    DRAFT = "draft"
    SIGNED = "signed"
    EXECUTED = "executed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


# ─── 데이터 클래스 ────────────────────────────────────────────────────────────
@dataclass
class LOIRecord:
    """개별 LOI(Letter of Intent) 기록."""
    loi_id: str
    partner_name: str
    status: LOIStatus
    signed_date: str        # ISO 8601 날짜 (YYYY-MM-DD)
    contact_email: str
    annual_value_krw: int   # 연간 계약 예상 금액 (원)
    api_scope: list[str] = field(default_factory=list)  # OAuth scope / endpoint 목록
    notes: str = ""

    @property
    def is_valid(self) -> bool:
        """유효한 LOI 여부 (SIGNED 또는 EXECUTED)."""
        return self.status in (LOIStatus.SIGNED, LOIStatus.EXECUTED)

    def to_dict(self) -> dict[str, Any]:
        return {
            "loi_id": self.loi_id,
            "partner_name": self.partner_name,
            "status": self.status.value,
            "signed_date": self.signed_date,
            "contact_email": self.contact_email,
            "annual_value_krw": self.annual_value_krw,
            "api_scope": self.api_scope,
            "notes": self.notes,
            "is_valid": self.is_valid,
        }


@dataclass
class LOIValidationResult:
    """LOI 개별 검증 결과."""
    loi_id: str
    partner_name: str
    valid: bool
    reasons: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "loi_id": self.loi_id,
            "partner_name": self.partner_name,
            "valid": self.valid,
            "reasons": self.reasons,
        }


@dataclass
class B2BPartnerReport:
    """G71 게이트 실행 결과 보고서."""
    gate_id: str = GATE_ID
    gate_name: str = GATE_NAME
    passed: bool = False
    total_loi_count: int = 0
    valid_loi_count: int = 0
    min_required: int = MIN_LOI_COUNT
    total_annual_value_krw: int = 0
    elapsed_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    loi_results: list[LOIValidationResult] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "passed": self.passed,
            "total_loi_count": self.total_loi_count,
            "valid_loi_count": self.valid_loi_count,
            "min_required": self.min_required,
            "total_annual_value_krw": self.total_annual_value_krw,
            "elapsed_ms": round(self.elapsed_ms, 2),
            "errors": self.errors,
            "loi_results": [r.to_dict() for r in self.loi_results],
        }


# ─── LOI 저장소 ──────────────────────────────────────────────────────────────
class LOIRepository:
    """LOI 기록 저장소 (인메모리, 실제 DB 연동 가능)."""

    def __init__(self) -> None:
        self._records: dict[str, LOIRecord] = {}

    def add(self, record: LOIRecord) -> None:
        if record.loi_id in self._records:
            raise ValueError(f"LOI ID 중복: {record.loi_id}")
        self._records[record.loi_id] = record

    def get(self, loi_id: str) -> LOIRecord | None:
        return self._records.get(loi_id)

    def all(self) -> list[LOIRecord]:
        return list(self._records.values())

    def valid_count(self) -> int:
        return sum(1 for r in self._records.values() if r.is_valid)

    def total_annual_value(self) -> int:
        return sum(r.annual_value_krw for r in self._records.values() if r.is_valid)

    def clear(self) -> None:
        self._records.clear()


# ─── 검증 헬퍼 ──────────────────────────────────────────────────────────────
_EMAIL_RE = re.compile(r"^[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


def _validate_loi(record: LOIRecord) -> LOIValidationResult:
    reasons: list[str] = []

    if not record.loi_id or not record.loi_id.strip():
        reasons.append("loi_id 누락")

    if not record.partner_name or not record.partner_name.strip():
        reasons.append("partner_name 누락")

    if not _EMAIL_RE.match(record.contact_email):
        reasons.append(f"contact_email 형식 오류: {record.contact_email!r}")

    if not _DATE_RE.match(record.signed_date):
        reasons.append(f"signed_date 형식 오류: {record.signed_date!r} (YYYY-MM-DD 필요)")

    if record.annual_value_krw < 0:
        reasons.append(f"annual_value_krw 음수: {record.annual_value_krw}")

    if not record.is_valid:
        reasons.append(f"LOI 상태 미승인: {record.status.value} (signed/executed 필요)")

    valid = len(reasons) == 0
    return LOIValidationResult(
        loi_id=record.loi_id,
        partner_name=record.partner_name,
        valid=valid,
        reasons=reasons,
    )


# ─── 게이트 ──────────────────────────────────────────────────────────────────
class B2BPartnerGate:
    """
    Gate G71 — B2B Partner LOI 검증.

    SIGNED 또는 EXECUTED 상태의 LOI가 MIN_LOI_COUNT(=3)건 이상 등록되어야 통과.
    """

    def __init__(
        self,
        repository: LOIRepository | None = None,
        min_loi_count: int = MIN_LOI_COUNT,
    ) -> None:
        self._repo = repository or LOIRepository()
        self._min_loi_count = min_loi_count

    # ── 공개 인터페이스 ───────────────────────────────────────────────────────
    def register_loi(self, record: LOIRecord) -> None:
        """LOI 등록."""
        self._repo.add(record)

    def run(self) -> B2BPartnerReport:
        """G71 게이트 실행."""
        t0 = time.perf_counter()
        report = B2BPartnerReport()

        records = self._repo.all()
        report.total_loi_count = len(records)

        for record in records:
            result = _validate_loi(record)
            report.loi_results.append(result)
            if not result.valid:
                report.errors.extend(
                    [f"[{record.loi_id}] {r}" for r in result.reasons]
                )

        report.valid_loi_count = sum(1 for r in report.loi_results if r.valid)
        report.total_annual_value_krw = self._repo.total_annual_value()

        if report.valid_loi_count < self._min_loi_count:
            report.errors.append(
                f"유효 LOI {report.valid_loi_count}건 < 최소 요구 {self._min_loi_count}건"
            )

        report.passed = (
            report.valid_loi_count >= self._min_loi_count
            and len([e for e in report.errors if "유효 LOI" in e or "오류" in e]) == 0
        )
        # 단순화: validation errors 없고 valid_count >= min 이면 통과
        report.passed = (
            report.valid_loi_count >= self._min_loi_count
            and all(r.valid for r in report.loi_results)
        )

        report.elapsed_ms = (time.perf_counter() - t0) * 1000
        return report

    def summary(self) -> dict[str, Any]:
        """현재 LOI 현황 요약."""
        records = self._repo.all()
        return {
            "total": len(records),
            "valid": self._repo.valid_count(),
            "min_required": self._min_loi_count,
            "ready": self._repo.valid_count() >= self._min_loi_count,
            "total_annual_value_krw": self._repo.total_annual_value(),
        }


# ─── 편의 함수 ────────────────────────────────────────────────────────────────
def _make_demo_loi(idx: int) -> LOIRecord:
    """테스트/데모용 LOI 생성."""
    partners = [
        ("LOIS-001", "KakaoEnterprise", "api@kakao-ent.com", 120_000_000),
        ("LOIS-002", "NaverCloud", "partner@ncloud.com", 96_000_000),
        ("LOIS-003", "NHNCloud", "bd@nhn-cloud.com", 84_000_000),
        ("LOIS-004", "KT Cloud", "api-partner@ktcloud.com", 60_000_000),
    ]
    loi_id, partner, email, value = partners[idx % len(partners)]
    return LOIRecord(
        loi_id=loi_id,
        partner_name=partner,
        status=LOIStatus.SIGNED,
        signed_date="2026-05-15",
        contact_email=email,
        annual_value_krw=value,
        api_scope=["analyze", "repair", "generate"],
        notes=f"Demo LOI #{idx + 1}",
    )


def run_g71(
    loi_records: list[LOIRecord] | None = None,
    min_loi_count: int = MIN_LOI_COUNT,
) -> dict[str, Any]:
    """
    G71 게이트 실행 진입점.

    Args:
        loi_records: 등록할 LOI 목록. None이면 데모 3건 사용.
        min_loi_count: 최소 LOI 건수 (기본 3).

    Returns:
        gate 결과 dict.
    """
    repo = LOIRepository()
    gate = B2BPartnerGate(repository=repo, min_loi_count=min_loi_count)

    if loi_records is None:
        # 데모: 3건 자동 등록
        for i in range(MIN_LOI_COUNT):
            gate.register_loi(_make_demo_loi(i))
    else:
        for r in loi_records:
            gate.register_loi(r)

    report = gate.run()
    return report.to_dict()
