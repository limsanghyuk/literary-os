"""DSRHandler — GDPR/PIPA Data Subject Request 핸들러.

ADR-056: 30-day SLA 추적. PENDING → PROCESSING → COMPLETED/REJECTED/EXPIRED.
"""

from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional

from literary_system.governance.provenance_ledger import LoRAProvenanceLedger

DSR_SLA_DAYS = 30
DSR_SLA_SECONDS = DSR_SLA_DAYS * 86400


class DSRStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETED = "COMPLETED"
    REJECTED = "REJECTED"
    EXPIRED = "EXPIRED"


@dataclass
class DSRRequest:
    """단일 DSR 요청."""

    request_id: str
    subject_id: str
    entry_ids: List[str]
    submitted_at: float
    status: DSRStatus = DSRStatus.PENDING
    deadline: float = field(init=False)
    processed_at: Optional[float] = None
    completed_at: Optional[float] = None
    notes: str = ""

    def __post_init__(self) -> None:
        self.deadline = self.submitted_at + DSR_SLA_SECONDS


class DSRHandler:
    """DSR 수명주기 관리자.

    Usage:
        handler = DSRHandler()
        req = handler.submit("user-1", ["entry-a", "entry-b"])
        handler.process(req.request_id, ledger=ledger)
        handler.complete(req.request_id)
    """

    def __init__(self) -> None:
        self._requests: Dict[str, DSRRequest] = {}

    # ------------------------------------------------------------------
    # CRUD
    # ------------------------------------------------------------------

    def submit(self, subject_id: str, entry_ids: List[str]) -> DSRRequest:
        """새 DSR 제출."""
        req = DSRRequest(
            request_id=str(uuid.uuid4()),
            subject_id=subject_id,
            entry_ids=list(entry_ids),
            submitted_at=time.time(),
        )
        self._requests[req.request_id] = req
        return req

    def process(
        self,
        request_id: str,
        ledger: Optional[LoRAProvenanceLedger] = None,
    ) -> DSRRequest:
        """PROCESSING 상태로 전이. ledger가 주어지면 entry 삭제 마킹."""
        req = self._get(request_id)
        req.status = DSRStatus.PROCESSING
        req.processed_at = time.time()
        if ledger is not None:
            for eid in req.entry_ids:
                ledger.mark_dsr_deleted(eid, request_id)
        return req

    def complete(self, request_id: str, notes: str = "") -> DSRRequest:
        """COMPLETED 상태로 전이."""
        req = self._get(request_id)
        req.status = DSRStatus.COMPLETED
        req.completed_at = time.time()
        if notes:
            req.notes = notes
        return req

    def reject(self, request_id: str, notes: str = "") -> DSRRequest:
        """REJECTED 상태로 전이."""
        req = self._get(request_id)
        req.status = DSRStatus.REJECTED
        req.completed_at = time.time()
        if notes:
            req.notes = notes
        return req

    def overdue_requests(self, now: Optional[float] = None) -> List[DSRRequest]:
        """SLA 기한을 초과한 PENDING/PROCESSING 요청 반환."""
        now = now if now is not None else time.time()
        result = []
        for req in self._requests.values():
            if req.status in (DSRStatus.PENDING, DSRStatus.PROCESSING):
                if now > req.deadline:
                    req.status = DSRStatus.EXPIRED
                    result.append(req)
        return result

    def get(self, request_id: str) -> Optional[DSRRequest]:
        return self._requests.get(request_id)

    def all_requests(self) -> List[DSRRequest]:
        return list(self._requests.values())

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get(self, request_id: str) -> DSRRequest:
        req = self._requests.get(request_id)
        if req is None:
            raise KeyError(f"DSR request not found: {request_id}")
        return req
