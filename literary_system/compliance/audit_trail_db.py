"""
AuditTrailDB v2 — Append-Only + Hash Chain 감사 추적 DB (V466)

ADR-014: Audit Trail Immutability
LLM-0: 외부 LLM 없음.

설계 원칙:
  - Append-only: 기존 레코드 수정/삭제 불가
  - Hash chain: 각 레코드는 이전 레코드의 해시를 포함 (blockchain 스타일)
  - 7년 보존 정책 (PIPA §29 / 상법 §33 준거)
  - 체인 무결성 검증 API
  - 테넌트 격리: 테넌트별 독립 체인
  - 실제 PostgreSQL 연결은 pg_handler 주입으로 교체 가능 (기본: 인메모리)

이벤트 유형:
  - PERSONAL_DATA_ACCESS: 개인정보 조회
  - PERSONAL_DATA_MODIFY: 개인정보 수정
  - PERSONAL_DATA_DELETE: 개인정보 삭제 요청
  - PERSONAL_DATA_EXPORT: 개인정보 내보내기
  - CONSENT_GRANTED: 동의 획득
  - CONSENT_WITHDRAWN: 동의 철회
  - DPO_DECISION: DPO 결재
  - CROSS_BORDER_TRANSFER: 국경 간 이전
  - AI_DECISION: AI 자동화 결정
  - SECURITY_INCIDENT: 보안 사고
  - SYSTEM_CONFIG_CHANGE: 시스템 설정 변경
"""
from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any, Callable

# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class AuditEventType(str, Enum):
    PERSONAL_DATA_ACCESS = "personal_data_access"
    PERSONAL_DATA_MODIFY = "personal_data_modify"
    PERSONAL_DATA_DELETE = "personal_data_delete"
    PERSONAL_DATA_EXPORT = "personal_data_export"
    CONSENT_GRANTED = "consent_granted"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    DPO_DECISION = "dpo_decision"
    CROSS_BORDER_TRANSFER = "cross_border_transfer"
    AI_DECISION = "ai_decision"
    SECURITY_INCIDENT = "security_incident"
    SYSTEM_CONFIG_CHANGE = "system_config_change"
    PII_SCAN = "pii_scan"
    DELETION_CASCADE = "deletion_cascade"
    COMPLIANCE_CHECK = "compliance_check"


class AuditSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class AuditRecord:
    """불변 감사 레코드"""
    record_id: str
    tenant_id: str
    event_type: AuditEventType
    severity: AuditSeverity
    actor: str                      # 행위자 (user_id, system, DPO)
    subject_id: str | None          # 영향받는 정보주체 ID
    resource: str                   # 대상 리소스 (table, endpoint 등)
    action: str                     # 수행 작업 상세
    metadata: dict[str, Any]        # 추가 메타데이터
    timestamp: str
    prev_hash: str                  # 이전 레코드 해시 (체인)
    record_hash: str = ""           # 본 레코드 해시 (자동 계산)
    expires_at: str = ""            # 보존 만료일

    def compute_hash(self) -> str:
        payload = json.dumps({
            "record_id": self.record_id,
            "tenant_id": self.tenant_id,
            "event_type": self.event_type.value,
            "actor": self.actor,
            "subject_id": self.subject_id,
            "resource": self.resource,
            "action": self.action,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
        }, sort_keys=True)
        return hashlib.sha256(payload.encode()).hexdigest()

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "tenant_id": self.tenant_id,
            "event_type": self.event_type.value,
            "severity": self.severity.value,
            "actor": self.actor,
            "subject_id": self.subject_id,
            "resource": self.resource,
            "action": self.action,
            "metadata": self.metadata,
            "timestamp": self.timestamp,
            "prev_hash": self.prev_hash,
            "record_hash": self.record_hash,
            "expires_at": self.expires_at,
        }


@dataclass
class ChainIntegrityReport:
    tenant_id: str
    total_records: int
    valid: bool
    broken_at: str | None       # 체인이 끊어진 record_id
    verified_at: str
    details: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "tenant_id": self.tenant_id,
            "total_records": self.total_records,
            "valid": self.valid,
            "broken_at": self.broken_at,
            "verified_at": self.verified_at,
            "details": self.details,
        }


# ---------------------------------------------------------------------------
# AuditTrailDB v2
# ---------------------------------------------------------------------------

RETENTION_YEARS = 7
GENESIS_HASH = "0" * 64   # 체인의 첫 레코드 prev_hash


class AuditTrailDB:
    """
    Append-Only Hash Chain 감사 추적 DB.

    - 레코드 삽입만 허용 (수정/삭제 금지)
    - 테넌트별 독립 체인 유지
    - pg_handler 주입 시 PostgreSQL 연결 (기본: 인메모리)
    - 7년 보존 후 만료 마킹 (실제 삭제는 법무 검토 후 별도 실행)

    LLM-0: 외부 LLM 없음.
    """

    def __init__(
        self,
        pg_handler: Callable[[AuditRecord], None] | None = None,
        retention_years: int = RETENTION_YEARS,
    ) -> None:
        self._chains: dict[str, list[AuditRecord]] = {}   # tenant_id → records
        self._pg_handler = pg_handler
        self._retention_years = retention_years

    # ------------------------------------------------------------------
    # 레코드 추가 (Append-only)
    # ------------------------------------------------------------------

    def log(
        self,
        tenant_id: str,
        event_type: AuditEventType,
        actor: str,
        resource: str,
        action: str,
        subject_id: str | None = None,
        severity: AuditSeverity = AuditSeverity.INFO,
        metadata: dict[str, Any] | None = None,
    ) -> AuditRecord:
        """감사 이벤트 기록 (append-only)"""
        chain = self._chains.setdefault(tenant_id, [])
        prev_hash = chain[-1].record_hash if chain else GENESIS_HASH

        now = datetime.now(timezone.utc)
        expires_at = (now + timedelta(days=365 * self._retention_years)).isoformat()

        record = AuditRecord(
            record_id=str(uuid.uuid4()),
            tenant_id=tenant_id,
            event_type=event_type,
            severity=severity,
            actor=actor,
            subject_id=subject_id,
            resource=resource,
            action=action,
            metadata=metadata or {},
            timestamp=now.isoformat(),
            prev_hash=prev_hash,
            expires_at=expires_at,
        )
        record.record_hash = record.compute_hash()

        # 인메모리 저장
        chain.append(record)

        # PostgreSQL 핸들러 (주입된 경우)
        if self._pg_handler:
            try:
                self._pg_handler(record)
            except Exception:
                pass  # DB 실패해도 인메모리 체인은 유지

        return record

    # ------------------------------------------------------------------
    # 체인 무결성 검증
    # ------------------------------------------------------------------

    def verify_chain(self, tenant_id: str) -> ChainIntegrityReport:
        """테넌트 체인 전체 해시 검증"""
        chain = self._chains.get(tenant_id, [])
        now = datetime.now(timezone.utc).isoformat()

        if not chain:
            return ChainIntegrityReport(
                tenant_id=tenant_id,
                total_records=0,
                valid=True,
                broken_at=None,
                verified_at=now,
                details="체인 비어 있음 — OK",
            )

        prev = GENESIS_HASH
        for record in chain:
            # prev_hash 연결 확인
            if record.prev_hash != prev:
                return ChainIntegrityReport(
                    tenant_id=tenant_id,
                    total_records=len(chain),
                    valid=False,
                    broken_at=record.record_id,
                    verified_at=now,
                    details=f"체인 단절: {record.record_id} prev_hash 불일치",
                )
            # 레코드 자체 해시 검증
            expected = record.compute_hash()
            if record.record_hash != expected:
                return ChainIntegrityReport(
                    tenant_id=tenant_id,
                    total_records=len(chain),
                    valid=False,
                    broken_at=record.record_id,
                    verified_at=now,
                    details=f"레코드 변조 감지: {record.record_id}",
                )
            prev = record.record_hash

        return ChainIntegrityReport(
            tenant_id=tenant_id,
            total_records=len(chain),
            valid=True,
            broken_at=None,
            verified_at=now,
            details=f"체인 무결성 확인 완료 ({len(chain)}개 레코드)",
        )

    # ------------------------------------------------------------------
    # 조회
    # ------------------------------------------------------------------

    def query(
        self,
        tenant_id: str,
        event_type: AuditEventType | None = None,
        subject_id: str | None = None,
        actor: str | None = None,
        since: str | None = None,
        until: str | None = None,
        severity: AuditSeverity | None = None,
        limit: int = 100,
    ) -> list[AuditRecord]:
        """감사 레코드 조회 (필터 조합)"""
        chain = self._chains.get(tenant_id, [])
        results: list[AuditRecord] = []

        for record in reversed(chain):   # 최신순
            if event_type and record.event_type != event_type:
                continue
            if subject_id and record.subject_id != subject_id:
                continue
            if actor and record.actor != actor:
                continue
            if severity and record.severity != severity:
                continue
            if since and record.timestamp < since:
                continue
            if until and record.timestamp > until:
                continue
            results.append(record)
            if len(results) >= limit:
                break

        return results

    def get_record(self, tenant_id: str, record_id: str) -> AuditRecord | None:
        for r in self._chains.get(tenant_id, []):
            if r.record_id == record_id:
                return r
        return None

    def count(self, tenant_id: str) -> int:
        return len(self._chains.get(tenant_id, []))

    def list_tenants(self) -> list[str]:
        return list(self._chains.keys())

    def get_expired_records(self, tenant_id: str) -> list[AuditRecord]:
        """만료된 레코드 목록 (실제 삭제는 법무 승인 후 별도)"""
        now = datetime.now(timezone.utc).isoformat()
        return [
            r for r in self._chains.get(tenant_id, [])
            if r.expires_at and r.expires_at <= now
        ]

    # ------------------------------------------------------------------
    # 규정 준수 보고서
    # ------------------------------------------------------------------

    def generate_compliance_report(self, tenant_id: str) -> dict[str, Any]:
        """GDPR/PIPA 준수 현황 요약"""
        chain = self._chains.get(tenant_id, [])
        integrity = self.verify_chain(tenant_id)

        event_counts: dict[str, int] = {}
        critical_events: list[str] = []

        for record in chain:
            event_counts[record.event_type.value] = event_counts.get(record.event_type.value, 0) + 1
            if record.severity == AuditSeverity.CRITICAL:
                critical_events.append(record.record_id)

        return {
            "tenant_id": tenant_id,
            "total_records": len(chain),
            "chain_integrity": integrity.valid,
            "event_breakdown": event_counts,
            "critical_events_count": len(critical_events),
            "critical_event_ids": critical_events[:10],  # 최대 10개
            "retention_years": self._retention_years,
            "generated_at": datetime.now(timezone.utc).isoformat(),
        }
