"""
V720: ZeroTrustAuditLog — 변조 방지 감사 로그 (ADR-181)
=========================================================
ZeroTrustMiddleware 의사결정 이력을 HMAC-SHA256 체인으로 봉인한다.

구조:
  - AuditRecord: timestamp / action / subject / tenant / decision / reason / seq / chain_hash
  - ZeroTrustAuditLog: append / verify_chain / export_records / query

체인 해시: HMAC-SHA256(prev_hash + record_json, secret_key)
seq=0 의 prev_hash = "GENESIS"
"""
from __future__ import annotations

import hashlib
import hmac
import json
import threading
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone
from typing import List, Optional


# ─── 레코드 타입 ─────────────────────────────────────────────────────────────

@dataclass
class AuditRecord_Security:
    """단일 감사 레코드 — 체인 해시 포함."""
    seq: int
    timestamp: str          # ISO 8601 UTC
    action: str             # "PASS" | "DENY" | "REVOKE" | "ISSUE"
    subject: str            # token subject (sub)
    tenant_id: str
    decision: str           # "ALLOW" | "DENY"
    reason: str
    chain_hash: str         # HMAC-SHA256 체인 서명 (hex)
    extra: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "AuditRecord":
        return cls(**d)


# ─── 감사 로그 ───────────────────────────────────────────────────────────────

class ZeroTrustAuditLog:
    """
    HMAC-SHA256 체인 기반 변조 방지 감사 로그.

    Parameters
    ----------
    secret_key : str
        체인 해시 서명 키 (ZeroTrustTokenService 와 동일 키 공유 가능)
    max_records : int
        인메모리 최대 레코드 수 (기본 10,000). 초과 시 가장 오래된 항목 제거.
    """

    GENESIS_HASH = "GENESIS"

    def __init__(self, secret_key: str = "audit-default-key", max_records: int = 10_000):
        self._key = secret_key.encode() if isinstance(secret_key, str) else secret_key
        self._max = max_records
        self._records: List[AuditRecord] = []
        self._eviction_anchor: str = self.GENESIS_HASH   # hash of last evicted record
        self._lock = threading.Lock()

    # ── 내부 해시 계산 ────────────────────────────────────────────────────────

    def _compute_hash(self, prev_hash: str, record_body: dict) -> str:
        """HMAC-SHA256(prev_hash + sorted-JSON-body, key)"""
        payload = prev_hash + json.dumps(record_body, sort_keys=True, ensure_ascii=False)
        return hmac.new(self._key, payload.encode(), hashlib.sha256).hexdigest()

    def _record_body(self, rec: AuditRecord) -> dict:
        """해시 계산용 body (chain_hash 제외)."""
        d = rec.to_dict()
        d.pop("chain_hash", None)
        return d

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def append(
        self,
        action: str,
        subject: str,
        tenant_id: str,
        decision: str,
        reason: str,
        extra: Optional[dict] = None,
    ) -> AuditRecord:
        """
        새 레코드를 체인에 추가한다.

        Returns
        -------
        AuditRecord
            방금 추가된 레코드 (chain_hash 포함).
        """
        with self._lock:
            seq = len(self._records)
            prev_hash = self._records[-1].chain_hash if self._records else self.GENESIS_HASH
            ts = datetime.now(timezone.utc).isoformat()

            # 체인 해시 계산 전 임시 레코드 (hash="" placeholder)
            rec = AuditRecord(
                seq=seq,
                timestamp=ts,
                action=action,
                subject=subject,
                tenant_id=tenant_id,
                decision=decision,
                reason=reason,
                chain_hash="",
                extra=extra or {},
            )
            body = self._record_body(rec)
            rec.chain_hash = self._compute_hash(prev_hash, body)

            if len(self._records) >= self._max:
                evicted = self._records.pop(0)
                self._eviction_anchor = evicted.chain_hash   # 앵커 갱신
            self._records.append(rec)
            return rec

    def verify_chain(self) -> bool:
        """
        전체 체인 무결성 검증.

        앞쪽 레코드가 eviction으로 제거된 경우, _eviction_anchor 를 기준으로 검증한다.

        Returns
        -------
        bool
            True = 변조 없음, False = 변조 감지.
        """
        with self._lock:
            prev_hash = self._eviction_anchor
            for rec in self._records:
                expected = self._compute_hash(prev_hash, self._record_body(rec))
                if not hmac.compare_digest(expected, rec.chain_hash):
                    return False
                prev_hash = rec.chain_hash
            return True

    def export_records(self) -> List[dict]:
        """전체 레코드 dict 리스트 반환 (복사본)."""
        with self._lock:
            return [r.to_dict() for r in self._records]

    def query(
        self,
        subject: Optional[str] = None,
        tenant_id: Optional[str] = None,
        decision: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 100,
    ) -> List[AuditRecord]:
        """
        필터 기반 레코드 조회 (최근 limit 개).

        Parameters
        ----------
        subject : str, optional
        tenant_id : str, optional
        decision : str, optional   "ALLOW" | "DENY"
        action : str, optional     "PASS" | "DENY" | "REVOKE" | "ISSUE"
        limit : int
            최대 반환 건수.
        """
        with self._lock:
            results = []
            for rec in reversed(self._records):
                if subject is not None and rec.subject != subject:
                    continue
                if tenant_id is not None and rec.tenant_id != tenant_id:
                    continue
                if decision is not None and rec.decision != decision:
                    continue
                if action is not None and rec.action != action:
                    continue
                results.append(rec)
                if len(results) >= limit:
                    break
            return results

    @property
    def record_count(self) -> int:
        """현재 저장된 레코드 수."""
        with self._lock:
            return len(self._records)

    def allow_count(self) -> int:
        """ALLOW 결정 수."""
        with self._lock:
            return sum(1 for r in self._records if r.decision == "ALLOW")

    def deny_count(self) -> int:
        """DENY 결정 수."""
        with self._lock:
            return sum(1 for r in self._records if r.decision == "DENY")


# G37 DuplicateZero(ADR-033): 클래스명 전역 고유화 — 외부 import 하위호환 별칭
AuditRecord = AuditRecord_Security
