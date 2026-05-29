"""
DPO Workflow — Data Protection Officer 결재 워크플로우 (V463)

ADR-011: GDPR/PIPA Dual Compliance
LLM-0: 외부 LLM 없음. 상태 머신 기반.

DPO 승인이 필요한 PIA/처리 활동에 대해:
  - 요청 생성 → DPO 검토 → 승인/반려 → 조건부 승인
  - 30일 내 무응답 시 자동 에스컬레이션
  - 감사 로그 자동 기록
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any


class DPOStatus(str, Enum):
    PENDING = "pending"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    CONDITIONALLY_APPROVED = "conditionally_approved"
    REJECTED = "rejected"
    ESCALATED = "escalated"     # 30일 초과 무응답


class DPORequestType(str, Enum):
    PIA_REVIEW = "pia_review"                    # PIA 검토 요청
    CROSS_BORDER_TRANSFER = "cross_border_transfer"
    NEW_PROCESSING_ACTIVITY = "new_processing_activity"
    VENDOR_DPA = "vendor_dpa"                    # 처리 위탁 계약
    SUBJECT_REQUEST = "subject_request"          # 정보주체 권리 요청


@dataclass
class DPORequest:
    request_id: str
    tenant_id: str
    request_type: DPORequestType
    title: str
    description: str
    related_pia_id: str | None
    requester: str
    status: DPOStatus
    created_at: str
    deadline_at: str            # 기본 30일
    reviewed_at: str | None = None
    reviewer: str | None = None
    decision_notes: str | None = None
    conditions: list[str] = field(default_factory=list)
    audit_trail: list[dict] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "request_type": self.request_type.value,
            "title": self.title,
            "description": self.description,
            "related_pia_id": self.related_pia_id,
            "requester": self.requester,
            "status": self.status.value,
            "created_at": self.created_at,
            "deadline_at": self.deadline_at,
            "reviewed_at": self.reviewed_at,
            "reviewer": self.reviewer,
            "decision_notes": self.decision_notes,
            "conditions": self.conditions,
            "audit_trail": self.audit_trail,
        }


class DPOWorkflow:
    """
    DPO 결재 워크플로우 관리자.

    상태 전이:
      PENDING → UNDER_REVIEW → APPROVED / CONDITIONALLY_APPROVED / REJECTED
      PENDING (30일 경과) → ESCALATED
    """

    REVIEW_DEADLINE_DAYS = 30

    def __init__(self) -> None:
        self._requests: dict[str, DPORequest] = {}

    # ------------------------------------------------------------------
    def create_request(
        self,
        tenant_id: str,
        request_type: DPORequestType,
        title: str,
        description: str,
        requester: str,
        related_pia_id: str | None = None,
    ) -> DPORequest:
        now = datetime.now(timezone.utc)
        deadline = now + timedelta(days=self.REVIEW_DEADLINE_DAYS)
        request_id = str(uuid.uuid4())

        req = DPORequest(
            request_id=request_id,
            tenant_id=tenant_id,
            request_type=request_type,
            title=title,
            description=description,
            related_pia_id=related_pia_id,
            requester=requester,
            status=DPOStatus.PENDING,
            created_at=now.isoformat(),
            deadline_at=deadline.isoformat(),
        )
        req.audit_trail.append(self._log_event("CREATED", requester, "요청 생성"))
        self._requests[request_id] = req
        return req

    # ------------------------------------------------------------------
    def start_review(self, request_id: str, reviewer: str) -> DPORequest:
        req = self._get_or_raise(request_id)
        if req.status not in (DPOStatus.PENDING, DPOStatus.ESCALATED):
            raise ValueError(f"Cannot start review on status={req.status}")
        req.status = DPOStatus.UNDER_REVIEW
        req.reviewer = reviewer
        req.audit_trail.append(self._log_event("REVIEW_STARTED", reviewer, "검토 시작"))
        return req

    def approve(self, request_id: str, reviewer: str, notes: str = "") -> DPORequest:
        req = self._get_or_raise(request_id)
        self._assert_under_review(req)
        req.status = DPOStatus.APPROVED
        req.reviewed_at = datetime.now(timezone.utc).isoformat()
        req.reviewer = reviewer
        req.decision_notes = notes
        req.audit_trail.append(self._log_event("APPROVED", reviewer, notes or "승인"))
        return req

    def approve_with_conditions(
        self, request_id: str, reviewer: str, conditions: list[str], notes: str = ""
    ) -> DPORequest:
        req = self._get_or_raise(request_id)
        self._assert_under_review(req)
        req.status = DPOStatus.CONDITIONALLY_APPROVED
        req.reviewed_at = datetime.now(timezone.utc).isoformat()
        req.reviewer = reviewer
        req.decision_notes = notes
        req.conditions = conditions
        req.audit_trail.append(
            self._log_event("CONDITIONALLY_APPROVED", reviewer,
                            f"조건부 승인: {'; '.join(conditions)}")
        )
        return req

    def reject(self, request_id: str, reviewer: str, notes: str) -> DPORequest:
        req = self._get_or_raise(request_id)
        self._assert_under_review(req)
        req.status = DPOStatus.REJECTED
        req.reviewed_at = datetime.now(timezone.utc).isoformat()
        req.reviewer = reviewer
        req.decision_notes = notes
        req.audit_trail.append(self._log_event("REJECTED", reviewer, notes))
        return req

    # ------------------------------------------------------------------
    def check_escalations(self) -> list[DPORequest]:
        """30일 초과 PENDING 요청을 ESCALATED로 전환"""
        now = datetime.now(timezone.utc)
        escalated: list[DPORequest] = []
        for req in self._requests.values():
            if req.status == DPOStatus.PENDING:
                deadline = datetime.fromisoformat(req.deadline_at)
                if now > deadline:
                    req.status = DPOStatus.ESCALATED
                    req.audit_trail.append(
                        self._log_event("ESCALATED", "SYSTEM", "30일 기한 초과 자동 에스컬레이션")
                    )
                    escalated.append(req)
        return escalated

    # ------------------------------------------------------------------
    def get_request(self, request_id: str) -> DPORequest | None:
        return self._requests.get(request_id)

    def list_by_tenant(self, tenant_id: str) -> list[DPORequest]:
        return [r for r in self._requests.values() if r.tenant_id == tenant_id]

    def list_pending(self) -> list[DPORequest]:
        return [r for r in self._requests.values()
                if r.status in (DPOStatus.PENDING, DPOStatus.UNDER_REVIEW, DPOStatus.ESCALATED)]

    # ------------------------------------------------------------------
    def _get_or_raise(self, request_id: str) -> DPORequest:
        req = self._requests.get(request_id)
        if req is None:
            raise KeyError(f"DPORequest not found: {request_id}")
        return req

    @staticmethod
    def _assert_under_review(req: DPORequest) -> None:
        if req.status != DPOStatus.UNDER_REVIEW:
            raise ValueError(f"Request must be UNDER_REVIEW, got {req.status}")

    @staticmethod
    def _log_event(event: str, actor: str, detail: str) -> dict:
        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event,
            "actor": actor,
            "detail": detail,
        }
