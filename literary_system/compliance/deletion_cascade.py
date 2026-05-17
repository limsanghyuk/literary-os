"""
DeletionCascade — GDPR/PIPA 삭제 요청 카스케이드 실행기 (V463)

ADR-011: GDPR/PIPA Dual Compliance
LLM-0: 외부 LLM 없음. 삭제 그래프 순회 기반.

GDPR Art.17 '잊혀질 권리' / PIPA §36 삭제 요청:
  - 요청 접수 → 대상 식별 → 카스케이드 삭제 → 익명화 → 감사 기록
  - 30일 내 처리 완료 의무
  - 법적 보존 의무 데이터는 삭제 대신 격리(quarantine)
  - 삭제 완료 증명서 발급

카스케이드 순서:
  1. 세션/토큰
  2. 개인화 데이터 (preference, history)
  3. 콘텐츠 데이터 (manuscripts, generations)
  4. RAG 인덱스 벡터
  5. 빌링 기록 (법적 보존 → 격리)
  6. 감사 로그 (법적 보존 → 격리)
  7. 테넌트 계정
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable


class DeletionStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    PARTIALLY_COMPLETED = "partially_completed"   # 일부 격리
    FAILED = "failed"


class DeletionScope(str, Enum):
    FULL = "full"               # 전체 삭제 (계정 탈퇴)
    DATA_ONLY = "data_only"     # 개인정보만 삭제 (계정 유지)
    SPECIFIC = "specific"       # 특정 데이터 삭제


@dataclass
class DeletionTarget:
    """삭제 대상 단위"""
    layer: str                  # 레이어명 (sessions, preferences, ...)
    record_count: int
    deleted: int = 0
    quarantined: int = 0        # 법적 보존으로 격리
    error: str | None = None

    @property
    def status(self) -> str:
        if self.error:
            return "error"
        # Bug-Fix: previous condition `quarantined>0 AND deleted < record_count-quarantined`
        # was False when deleted=0 and quarantined=record_count (all records legally held).
        # That caused status="ok" even though records were quarantined not deleted.
        # Fix: quarantined>0 alone is sufficient for "partial".
        if self.quarantined > 0:
            return "partial"
        return "ok"


@dataclass
class DeletionRequest:
    request_id: str
    tenant_id: str
    subject_id: str             # 정보주체 ID
    scope: DeletionScope
    reason: str
    status: DeletionStatus
    created_at: str
    deadline_at: str            # 30일 기한
    completed_at: str | None = None
    targets: list[DeletionTarget] = field(default_factory=list)
    certificate_id: str | None = None
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": self.request_id,
            "tenant_id": self.tenant_id,
            "subject_id": self.subject_id,
            "scope": self.scope.value,
            "reason": self.reason,
            "status": self.status.value,
            "created_at": self.created_at,
            "deadline_at": self.deadline_at,
            "completed_at": self.completed_at,
            "targets": [
                {
                    "layer": t.layer,
                    "record_count": t.record_count,
                    "deleted": t.deleted,
                    "quarantined": t.quarantined,
                    "status": t.status,
                    "error": t.error,
                }
                for t in self.targets
            ],
            "certificate_id": self.certificate_id,
            "notes": self.notes,
        }


# ---------------------------------------------------------------------------
# DeletionCascade
# ---------------------------------------------------------------------------

# 카스케이드 레이어 순서 (의존성 역순 — 외곽부터)
_CASCADE_LAYERS = [
    "sessions",
    "preferences",
    "generation_history",
    "manuscripts",
    "rag_index",
    "billing_records",       # → quarantine (법적 5년 보존)
    "audit_logs",            # → quarantine (법적 7년 보존)
    "tenant_account",
]

# 법적 보존 의무 레이어 (삭제 대신 격리)
_LEGAL_HOLD_LAYERS = {"billing_records", "audit_logs"}


class DeletionCascade:
    """
    GDPR Art.17 / PIPA §36 삭제 카스케이드 실행기.

    실제 DB 삭제는 layer_handlers를 주입하여 연결.
    핸들러 미주입 시 시뮬레이션 모드(dry_run) 동작.
    """

    DEADLINE_DAYS = 30

    def __init__(
        self,
        layer_handlers: dict[str, Callable[[str, str], int]] | None = None,
        dry_run: bool = False,
    ) -> None:
        """
        layer_handlers: {layer_name: handler(tenant_id, subject_id) → deleted_count}
        dry_run: True면 실제 삭제 없이 시뮬레이션
        """
        self._handlers = layer_handlers or {}
        self._dry_run = dry_run
        self._requests: dict[str, DeletionRequest] = {}

    # ------------------------------------------------------------------
    def create_request(
        self,
        tenant_id: str,
        subject_id: str,
        scope: DeletionScope,
        reason: str,
    ) -> DeletionRequest:
        now = datetime.now(timezone.utc)
        req = DeletionRequest(
            request_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            subject_id=subject_id,
            scope=scope,
            reason=reason,
            status=DeletionStatus.PENDING,
            created_at=now.isoformat(),
            deadline_at=(now + timedelta(days=self.DEADLINE_DAYS)).isoformat(),
        )
        self._requests[req.request_id] = req
        return req

    # ------------------------------------------------------------------
    def execute(self, request_id: str) -> DeletionRequest:
        """카스케이드 삭제 실행"""
        req = self._get_or_raise(request_id)
        if req.status not in (DeletionStatus.PENDING, DeletionStatus.FAILED):
            raise ValueError(f"Cannot execute deletion in status={req.status}")

        req.status = DeletionStatus.IN_PROGRESS
        req.targets.clear()

        layers = self._select_layers(req.scope)
        has_error = False
        has_quarantine = False

        for layer in layers:
            target = self._process_layer(req.tenant_id, req.subject_id, layer)
            req.targets.append(target)
            if target.error:
                has_error = True
            if target.quarantined > 0:
                has_quarantine = True

        now = datetime.now(timezone.utc).isoformat()
        req.completed_at = now

        if has_error:
            req.status = DeletionStatus.FAILED
        elif has_quarantine:
            req.status = DeletionStatus.PARTIALLY_COMPLETED
            req.certificate_id = self._issue_certificate(req)
            req.notes = "일부 데이터는 법적 보존 의무로 격리되었습니다."
        else:
            req.status = DeletionStatus.COMPLETED
            req.certificate_id = self._issue_certificate(req)

        return req

    # ------------------------------------------------------------------
    def _process_layer(
        self, tenant_id: str, subject_id: str, layer: str
    ) -> DeletionTarget:
        is_legal_hold = layer in _LEGAL_HOLD_LAYERS

        if self._dry_run:
            # 시뮬레이션: 레코드 수 추정
            simulated = {"sessions": 12, "preferences": 5, "generation_history": 87,
                         "manuscripts": 23, "rag_index": 154, "billing_records": 36,
                         "audit_logs": 210, "tenant_account": 1}.get(layer, 10)
            if is_legal_hold:
                return DeletionTarget(layer=layer, record_count=simulated,
                                      deleted=0, quarantined=simulated)
            return DeletionTarget(layer=layer, record_count=simulated,
                                  deleted=simulated, quarantined=0)

        handler = self._handlers.get(layer)
        if handler is None:
            # 핸들러 없음 → 건너뜀 (경고)
            return DeletionTarget(layer=layer, record_count=0,
                                  deleted=0, error="핸들러 미등록 — 건너뜀")

        try:
            count = handler(tenant_id, subject_id)
            if is_legal_hold:
                return DeletionTarget(layer=layer, record_count=count,
                                      deleted=0, quarantined=count)
            return DeletionTarget(layer=layer, record_count=count,
                                  deleted=count, quarantined=0)
        except Exception as e:
            return DeletionTarget(layer=layer, record_count=0,
                                  error=str(e))

    # ------------------------------------------------------------------
    @staticmethod
    def _select_layers(scope: DeletionScope) -> list[str]:
        if scope == DeletionScope.FULL:
            return _CASCADE_LAYERS
        elif scope == DeletionScope.DATA_ONLY:
            return [l for l in _CASCADE_LAYERS if l != "tenant_account"]
        else:  # SPECIFIC — 모든 레이어 순회 (핸들러 있는 것만 처리)
            return _CASCADE_LAYERS

    @staticmethod
    def _issue_certificate(req: DeletionRequest) -> str:
        """삭제 완료 증명서 ID 발급"""
        return f"DEL-CERT-{req.request_id[:8].upper()}"

    # ------------------------------------------------------------------
    def get_request(self, request_id: str) -> DeletionRequest | None:
        return self._requests.get(request_id)

    def list_by_tenant(self, tenant_id: str) -> list[DeletionRequest]:
        return [r for r in self._requests.values() if r.tenant_id == tenant_id]

    def overdue_requests(self) -> list[DeletionRequest]:
        """30일 기한 초과 미완료 요청"""
        now = datetime.now(timezone.utc)
        result: list[DeletionRequest] = []
        for req in self._requests.values():
            if req.status in (DeletionStatus.PENDING, DeletionStatus.IN_PROGRESS, DeletionStatus.FAILED):
                deadline = datetime.fromisoformat(req.deadline_at)
                if now > deadline:
                    result.append(req)
        return result

    def _get_or_raise(self, request_id: str) -> DeletionRequest:
        req = self._requests.get(request_id)
        if req is None:
            raise KeyError(f"DeletionRequest not found: {request_id}")
        return req
