"""
Literary OS V460 -- TenantAuditLog

PostgreSQL append-only + hash chain (ADR-011 / ADR-021 기반).

설계 원칙:
  - LLM-0: db_fn 주입으로 실 DB 호출 격리
  - append-only: 기존 레코드 수정/삭제 불가
  - hash chain: 각 레코드가 이전 레코드의 해시를 포함
  - 무결성 검증: verify_chain() 으로 변조 감지
"""
from __future__ import annotations

import hashlib
import json
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional

# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class TenantAuditEventType(str, Enum):
    # 테넌트 생명주기
    TENANT_CREATED   = "TENANT_CREATED"
    TENANT_SUSPENDED = "TENANT_SUSPENDED"
    TENANT_RESTORED  = "TENANT_RESTORED"
    TENANT_DELETED   = "TENANT_DELETED"
    # KMS
    KMS_KEY_PROVISIONED = "KMS_KEY_PROVISIONED"
    KMS_KEY_ROTATED     = "KMS_KEY_ROTATED"
    # 결제
    BILLING_CHARGED  = "BILLING_CHARGED"
    BILLING_REFUNDED = "BILLING_REFUNDED"
    # 할당량
    QUOTA_EXCEEDED   = "QUOTA_EXCEEDED"
    QUOTA_RESET      = "QUOTA_RESET"
    # 접근 제어
    ACCESS_GRANTED   = "ACCESS_GRANTED"
    ACCESS_DENIED    = "ACCESS_DENIED"
    # 설정 변경
    CONFIG_CHANGED   = "CONFIG_CHANGED"
    # DR
    DR_SNAPSHOT_TAKEN  = "DR_SNAPSHOT_TAKEN"
    DR_RESTORE_STARTED = "DR_RESTORE_STARTED"
    DR_RESTORE_DONE    = "DR_RESTORE_DONE"


# ---------------------------------------------------------------------------
# 감사 레코드 (불변)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TenantAuditRecord:
    """불변 감사 레코드 (hash chain 노드)."""
    record_id:  str
    tenant_id:  str
    event_type: AuditEventType
    actor:      str              # 행위자 (user_id / system / scheduler)
    description: str
    payload:    dict             # 이벤트 세부 데이터
    created_at: datetime
    prev_hash:  str              # 이전 레코드 해시 (첫 레코드는 "GENESIS")
    record_hash: str             # 이 레코드의 SHA-256

    @classmethod
    def compute_hash(
        cls,
        record_id:   str,
        tenant_id:   str,
        event_type:  str,
        actor:       str,
        description: str,
        payload:     dict,
        created_at:  str,
        prev_hash:   str,
    ) -> str:
        blob = json.dumps({
            "record_id":   record_id,
            "tenant_id":   tenant_id,
            "event_type":  event_type,
            "actor":       actor,
            "description": description,
            "payload":     payload,
            "created_at":  created_at,
            "prev_hash":   prev_hash,
        }, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {
            "record_id":   self.record_id,
            "tenant_id":   self.tenant_id,
            "event_type":  self.event_type.value,
            "actor":       self.actor,
            "description": self.description,
            "created_at":  self.created_at.isoformat(),
            "prev_hash":   self.prev_hash,
            "record_hash": self.record_hash,
        }


# ---------------------------------------------------------------------------
# TenantAuditLog
# ---------------------------------------------------------------------------

class TenantAuditLog:
    """
    Append-only hash-chain 감사 로그.

    LLM-0: db_fn(record: dict) -> None 주입으로 실 PostgreSQL 호출 격리.
    테스트 환경에서는 in-memory 저장.
    """

    GENESIS_HASH = "0" * 64

    def __init__(self, db_fn: Optional[Callable[[dict], None]] = None):
        self._db_fn = db_fn  # None = in-memory only
        self._records: List[AuditRecord] = []
        self._lock = threading.Lock()
        # 테넌트별 마지막 해시 (hash chain 연결용)
        self._last_hash: Dict[str, str] = {}

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def append(
        self,
        tenant_id:   str,
        event_type:  AuditEventType,
        actor:       str,
        description: str,
        payload:     Optional[dict] = None,
    ) -> AuditRecord:
        """감사 레코드 추가 (append-only)."""
        with self._lock:
            prev_hash  = self._last_hash.get(tenant_id, self.GENESIS_HASH)
            record_id  = f"AUD-{uuid.uuid4().hex[:12].upper()}"
            created_at = datetime.now(timezone.utc)
            ts_str     = created_at.isoformat()
            pl         = payload or {}

            record_hash = AuditRecord.compute_hash(
                record_id=record_id,
                tenant_id=tenant_id,
                event_type=event_type.value,
                actor=actor,
                description=description,
                payload=pl,
                created_at=ts_str,
                prev_hash=prev_hash,
            )

            rec = AuditRecord(
                record_id=record_id,
                tenant_id=tenant_id,
                event_type=event_type,
                actor=actor,
                description=description,
                payload=pl,
                created_at=created_at,
                prev_hash=prev_hash,
                record_hash=record_hash,
            )
            self._records.append(rec)
            self._last_hash[tenant_id] = record_hash

            if self._db_fn:
                try:
                    self._db_fn(rec.to_dict())
                except Exception:
                    pass  # DB 실패는 감사 체인 자체를 막지 않음

            return rec

    def get_records(
        self,
        tenant_id:  str,
        event_type: Optional[AuditEventType] = None,
        limit:      int = 100,
    ) -> List[AuditRecord]:
        """테넌트 감사 레코드 조회."""
        with self._lock:
            recs = [r for r in self._records if r.tenant_id == tenant_id]
        if event_type:
            recs = [r for r in recs if r.event_type == event_type]
        return recs[-limit:]

    def verify_chain(self, tenant_id: str) -> dict:
        """
        hash chain 무결성 검증.

        Returns:
            {"valid": bool, "checked": int, "broken_at": Optional[str]}
        """
        with self._lock:
            recs = [r for r in self._records if r.tenant_id == tenant_id]

        if not recs:
            return {"valid": True, "checked": 0, "broken_at": None}

        prev_hash = self.GENESIS_HASH
        for rec in recs:
            if rec.prev_hash != prev_hash:
                return {
                    "valid": False,
                    "checked": recs.index(rec),
                    "broken_at": rec.record_id,
                }
            expected = AuditRecord.compute_hash(
                record_id=rec.record_id,
                tenant_id=rec.tenant_id,
                event_type=rec.event_type.value,
                actor=rec.actor,
                description=rec.description,
                payload=rec.payload,
                created_at=rec.created_at.isoformat(),
                prev_hash=rec.prev_hash,
            )
            if expected != rec.record_hash:
                return {
                    "valid": False,
                    "checked": recs.index(rec),
                    "broken_at": rec.record_id,
                }
            prev_hash = rec.record_hash

        return {"valid": True, "checked": len(recs), "broken_at": None}

    def count(self, tenant_id: Optional[str] = None) -> int:
        with self._lock:
            if tenant_id:
                return sum(1 for r in self._records if r.tenant_id == tenant_id)
            return len(self._records)

AuditEventType = TenantAuditEventType  # V579 backward-compat alias

AuditRecord = TenantAuditRecord  # V579 backward-compat alias
