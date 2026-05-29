"""
CrossBorderTransferAPI — 국경 간 개인정보 이전 제어 (V463)

ADR-011: GDPR/PIPA Dual Compliance
ADR-016: DataResidencyRouter 전단 게이트
LLM-0: 외부 LLM 없음. 국가·적정성 결정 테이블 기반.

GDPR Chapter V / PIPA §28의2:
  - EU 적정성 결정 국가: 이전 허용
  - SCC 체결 국가: 이전 허용 (조건부)
  - 그 외: 명시적 동의 + DPO 승인 필요
  - 금지 국가(제재 대상): 이전 거부

한국 PIPA:
  - 제3국 이전 시 정보주체 동의 또는 계약 이행 근거
  - 이전 기록 3년 보존
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class TransferBasis(str, Enum):
    ADEQUACY_DECISION = "adequacy_decision"   # EU 적정성 결정
    SCC = "scc"                               # 표준계약조항
    BCR = "bcr"                               # 구속력 있는 기업 규칙
    EXPLICIT_CONSENT = "explicit_consent"     # 명시적 동의
    CONTRACT = "contract"                     # 계약 이행
    VITAL_INTEREST = "vital_interest"
    DENIED = "denied"                         # 이전 거부


class TransferDecision(str, Enum):
    ALLOWED = "allowed"
    ALLOWED_WITH_SAFEGUARDS = "allowed_with_safeguards"
    REQUIRES_DPO = "requires_dpo"
    DENIED = "denied"


@dataclass
class TransferRequest:
    request_id: str
    tenant_id: str
    source_region: str      # KR, EU, US
    target_country: str     # ISO 3166-1 alpha-2
    data_categories: list[str]
    purpose: str
    recipient: str
    estimated_records: int
    basis: TransferBasis
    decision: TransferDecision
    safeguards: list[str]
    created_at: str
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "source_region": self.source_region,
            "target_country": self.target_country,
            "data_categories": self.data_categories,
            "purpose": self.purpose,
            "recipient": self.recipient,
            "estimated_records": self.estimated_records,
            "basis": self.basis.value,
            "decision": self.decision.value,
            "safeguards": self.safeguards,
            "created_at": self.created_at,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# 국가별 이전 정책 테이블 (LLM-0 — 정적 테이블)
# ---------------------------------------------------------------------------

# EU 회원국 목록 — 내부 이전은 GDPR 영역 내부이므로 추가 조치 불필요
# Bug-Fix: `source == target` check failed for EU region codes ("EU" != "DE").
# Added _EU_MEMBER_STATES to handle EU→EU_member transfers correctly.
_EU_MEMBER_STATES = {
    "AT", "BE", "BG", "CY", "CZ", "DE", "DK", "EE", "ES", "FI",
    "FR", "GR", "HR", "HU", "IE", "IT", "LT", "LU", "LV", "MT",
    "NL", "PL", "PT", "RO", "SE", "SI", "SK",
}

# EU 적정성 결정 국가 목록 (GDPR Article 45)
_EU_ADEQUACY_COUNTRIES = {
    "AD", "AR", "CA", "FO", "GG", "IL", "IM", "JP", "JE",
    "NZ", "CH", "UY", "UK", "KR",   # 한국 2021년 적정성 결정 획득
}

# SCC로 이전 가능한 주요 국가 (일반적 허용)
_SCC_ELIGIBLE_COUNTRIES = {
    "US", "AU", "SG", "IN", "BR", "MX", "ZA", "TH", "PH",
}

# 이전 금지 국가 (제재·특별 규정)
_PROHIBITED_COUNTRIES = {
    "KP", "IR", "SY", "CU",   # OFAC 제재 대상 예시
}

# 한국 → 제3국 이전 시 SCC 필요 국가
_KR_THIRD_COUNTRY_SCC = {
    "US", "AU", "SG", "JP", "CN", "DE", "FR", "GB",
}


class CrossBorderTransferAPI:
    """
    국경 간 개인정보 이전 요청 평가 및 기록 관리.

    evaluate_transfer() → TransferRequest (결정 포함)
    transfer 기록은 3년 보존 (PIPA §28의2).
    """

    def __init__(self) -> None:
        self._transfers: dict[str, TransferRequest] = {}

    # ------------------------------------------------------------------
    def evaluate_transfer(
        self,
        tenant_id: str,
        source_region: str,
        target_country: str,
        data_categories: list[str],
        purpose: str,
        recipient: str,
        estimated_records: int = 0,
    ) -> TransferRequest:
        """이전 요청 평가 → TransferRequest(결정 포함) 반환"""
        basis, decision, safeguards, notes = self._evaluate(
            source_region, target_country, data_categories
        )

        req = TransferRequest(
            request_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            source_region=source_region,
            target_country=target_country,
            data_categories=data_categories,
            purpose=purpose,
            recipient=recipient,
            estimated_records=estimated_records,
            basis=basis,
            decision=decision,
            safeguards=safeguards,
            created_at=datetime.now(timezone.utc).isoformat(),
            notes=notes,
        )
        self._transfers[req.request_id] = req
        return req

    # ------------------------------------------------------------------
    def _evaluate(
        self, source: str, target: str, categories: list[str]
    ) -> tuple[TransferBasis, TransferDecision, list[str], str]:
        """규칙 기반 이전 결정 (LLM-0)"""
        safeguards: list[str] = []

        # 1. 금지 국가
        if target in _PROHIBITED_COUNTRIES:
            return (
                TransferBasis.DENIED,
                TransferDecision.DENIED,
                [],
                f"{target}: 제재 대상 국가 — 이전 금지",
            )

        # 2. 동일 국가/지역 이전 또는 EU 내부 이전
        # Bug-Fix: EU member state transfers (source="EU", target="DE") were not caught
        # because source=="EU" != target=="DE". Added _EU_MEMBER_STATES check.
        if (source == target
                or (source == "EU" and target in _EU_ADEQUACY_COUNTRIES)
                or (source == "EU" and target in _EU_MEMBER_STATES)):
            return (
                TransferBasis.ADEQUACY_DECISION,
                TransferDecision.ALLOWED,
                [],
                "EU 적정성 결정 국가 — 추가 조치 불필요",
            )

        # 3. 민감 데이터 포함 여부
        sensitive = any(c in ("sensitive", "health", "biometric", "children") for c in categories)

        # 4. EU 소스 → SCC 가능 국가
        if source == "EU" and target in _SCC_ELIGIBLE_COUNTRIES:
            safeguards = ["SCC 체결 필수", "데이터 처리 위탁 계약(DPA) 체결"]
            if sensitive:
                safeguards.append("민감정보 별도 동의 확보")
                return (
                    TransferBasis.SCC,
                    TransferDecision.REQUIRES_DPO,
                    safeguards,
                    "민감정보 포함 SCC 이전 — DPO 승인 필요",
                )
            return (
                TransferBasis.SCC,
                TransferDecision.ALLOWED_WITH_SAFEGUARDS,
                safeguards,
                "SCC 체결 조건 하에 이전 허용",
            )

        # 5. KR 소스 → 제3국
        if source == "KR":
            if target in _KR_THIRD_COUNTRY_SCC:
                safeguards = ["표준계약조항(SCC) 체결", "이전 내역 3년 보존"]
                if sensitive:
                    safeguards.append("정보주체 명시적 동의 추가 확보")
                    return (
                        TransferBasis.SCC,
                        TransferDecision.REQUIRES_DPO,
                        safeguards,
                        "PIPA §28의2: 민감정보 제3국 이전 — DPO 승인",
                    )
                return (
                    TransferBasis.SCC,
                    TransferDecision.ALLOWED_WITH_SAFEGUARDS,
                    safeguards,
                    "PIPA §28의2: SCC 조건부 이전 허용",
                )

        # 6. 그 외 — 명시적 동의 + DPO
        safeguards = ["정보주체 명시적 동의", "DPO 사전 승인", "이전 기록 유지"]
        return (
            TransferBasis.EXPLICIT_CONSENT,
            TransferDecision.REQUIRES_DPO,
            safeguards,
            f"비표준 국가({target}) 이전 — DPO 승인 및 명시적 동의 필수",
        )

    # ------------------------------------------------------------------
    def get_transfer(self, request_id: str) -> TransferRequest | None:
        return self._transfers.get(request_id)

    def list_by_tenant(self, tenant_id: str) -> list[TransferRequest]:
        return [t for t in self._transfers.values() if t.tenant_id == tenant_id]

    def list_denied(self) -> list[TransferRequest]:
        return [t for t in self._transfers.values() if t.decision == TransferDecision.DENIED]

    def list_requires_dpo(self) -> list[TransferRequest]:
        return [t for t in self._transfers.values() if t.decision == TransferDecision.REQUIRES_DPO]
