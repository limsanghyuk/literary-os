"""
test_v466_audit_trail.py — V466 AuditTrailDB v2 테스트

ADR-014: Audit Trail Immutability
"""
import pytest
from datetime import datetime, timedelta, timezone

from literary_system.compliance.audit_trail_db import (
    AuditTrailDB, AuditRecord, AuditEventType, AuditSeverity,
    ChainIntegrityReport, GENESIS_HASH, RETENTION_YEARS,
)


def _db(**kwargs) -> AuditTrailDB:
    return AuditTrailDB(**kwargs)


def _log(db, tenant="t1", **kwargs):
    defaults = dict(
        tenant_id=tenant,
        event_type=AuditEventType.PERSONAL_DATA_ACCESS,
        actor="user_a",
        resource="users_table",
        action="SELECT",
    )
    defaults.update(kwargs)
    return db.log(**defaults)


class TestAppendOnly:

    def test_log_creates_record(self):
        db = _db()
        rec = _log(db)
        assert rec.record_id
        assert rec.tenant_id == "t1"
        assert rec.record_hash
        assert rec.record_hash != ""

    def test_log_increments_count(self):
        db = _db()
        _log(db)
        _log(db)
        _log(db)
        assert db.count("t1") == 3

    def test_first_record_prev_hash_genesis(self):
        db = _db()
        rec = _log(db)
        assert rec.prev_hash == GENESIS_HASH

    def test_second_record_prev_hash_chained(self):
        db = _db()
        r1 = _log(db)
        r2 = _log(db)
        assert r2.prev_hash == r1.record_hash

    def test_chain_grows_sequentially(self):
        db = _db()
        recs = [_log(db) for _ in range(5)]
        for i in range(1, 5):
            assert recs[i].prev_hash == recs[i-1].record_hash

    def test_retention_7_years(self):
        db = _db()
        rec = _log(db)
        expires = datetime.fromisoformat(rec.expires_at)
        created = datetime.fromisoformat(rec.timestamp)
        delta_days = (expires - created).days
        assert delta_days >= 365 * RETENTION_YEARS - 1  # 윤년 허용

    def test_tenant_isolation(self):
        db = _db()
        _log(db, tenant="t1")
        _log(db, tenant="t1")
        _log(db, tenant="t2")
        assert db.count("t1") == 2
        assert db.count("t2") == 1

    def test_separate_chains_per_tenant(self):
        db = _db()
        r_t1 = _log(db, tenant="t1")
        r_t2 = _log(db, tenant="t2")
        # t1과 t2 체인은 독립
        assert r_t1.prev_hash == GENESIS_HASH
        assert r_t2.prev_hash == GENESIS_HASH


class TestHashChain:

    def test_record_hash_deterministic(self):
        """동일 레코드 → 동일 해시"""
        db = _db()
        rec = _log(db)
        computed = rec.compute_hash()
        assert rec.record_hash == computed

    def test_chain_integrity_valid(self):
        db = _db()
        for _ in range(10):
            _log(db)
        report = db.verify_chain("t1")
        assert report.valid is True
        assert report.broken_at is None
        assert report.total_records == 10

    def test_chain_integrity_tampered_hash(self):
        """레코드 해시 변조 감지"""
        db = _db()
        _log(db)
        r2 = _log(db)
        _log(db)

        # r2의 해시를 변조
        r2.record_hash = "deadbeef" * 8

        report = db.verify_chain("t1")
        assert report.valid is False
        # 3번째 레코드의 prev_hash가 r2의 원본 해시를 기대하는데
        # r2.record_hash가 변조되었으므로 3번째 또는 r2에서 실패
        assert report.broken_at is not None

    def test_chain_integrity_tampered_content(self):
        """레코드 내용 변조 감지"""
        db = _db()
        rec = _log(db)

        # actor 변조
        original_actor = rec.actor
        rec.actor = "ATTACKER"
        # record_hash는 그대로 → compute_hash()와 불일치

        report = db.verify_chain("t1")
        assert report.valid is False
        assert report.broken_at == rec.record_id

    def test_empty_chain_is_valid(self):
        db = _db()
        report = db.verify_chain("empty_tenant")
        assert report.valid is True
        assert report.total_records == 0

    def test_single_record_valid(self):
        db = _db()
        _log(db)
        report = db.verify_chain("t1")
        assert report.valid is True
        assert report.total_records == 1


class TestQuery:

    def test_query_all(self):
        db = _db()
        for _ in range(5):
            _log(db)
        results = db.query("t1")
        assert len(results) == 5

    def test_query_by_event_type(self):
        db = _db()
        _log(db, event_type=AuditEventType.CONSENT_GRANTED)
        _log(db, event_type=AuditEventType.CONSENT_WITHDRAWN)
        _log(db, event_type=AuditEventType.CONSENT_GRANTED)
        results = db.query("t1", event_type=AuditEventType.CONSENT_GRANTED)
        assert len(results) == 2

    def test_query_by_subject_id(self):
        db = _db()
        _log(db, subject_id="user_1")
        _log(db, subject_id="user_2")
        _log(db, subject_id="user_1")
        results = db.query("t1", subject_id="user_1")
        assert len(results) == 2

    def test_query_by_actor(self):
        db = _db()
        _log(db, actor="admin")
        _log(db, actor="user_x")
        results = db.query("t1", actor="admin")
        assert len(results) == 1

    def test_query_by_severity(self):
        db = _db()
        _log(db, severity=AuditSeverity.CRITICAL)
        _log(db, severity=AuditSeverity.INFO)
        _log(db, severity=AuditSeverity.CRITICAL)
        results = db.query("t1", severity=AuditSeverity.CRITICAL)
        assert len(results) == 2

    def test_query_limit(self):
        db = _db()
        for _ in range(10):
            _log(db)
        results = db.query("t1", limit=3)
        assert len(results) == 3

    def test_query_returns_latest_first(self):
        """최신순 반환 확인"""
        db = _db()
        for i in range(5):
            _log(db, action=f"action_{i}")
        results = db.query("t1")
        # reversed 적용되어 가장 최근이 첫 번째
        assert results[0].action == "action_4"

    def test_get_record(self):
        db = _db()
        rec = _log(db)
        fetched = db.get_record("t1", rec.record_id)
        assert fetched is not None
        assert fetched.record_id == rec.record_id

    def test_get_record_not_found(self):
        db = _db()
        assert db.get_record("t1", "nonexistent") is None

    def test_list_tenants(self):
        db = _db()
        _log(db, tenant="t1")
        _log(db, tenant="t2")
        _log(db, tenant="t3")
        tenants = db.list_tenants()
        assert set(tenants) == {"t1", "t2", "t3"}


class TestRetentionAndExpiry:

    def test_normal_records_not_expired(self):
        db = _db()
        _log(db)
        expired = db.get_expired_records("t1")
        assert len(expired) == 0

    def test_custom_retention(self):
        db = AuditTrailDB(retention_years=1)
        rec = _log(db)
        expires = datetime.fromisoformat(rec.expires_at)
        created = datetime.fromisoformat(rec.timestamp)
        assert (expires - created).days >= 364

    def test_expired_record_detected(self):
        db = _db()
        rec = _log(db)
        # expires_at을 과거로 조작
        past = (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()
        rec.expires_at = past
        expired = db.get_expired_records("t1")
        assert len(expired) == 1


class TestPGHandler:

    def test_pg_handler_called(self):
        called = []

        def fake_pg(record: AuditRecord) -> None:
            called.append(record.record_id)

        db = AuditTrailDB(pg_handler=fake_pg)
        _log(db)
        _log(db)
        assert len(called) == 2

    def test_pg_handler_failure_doesnt_break_chain(self):
        def failing_pg(record: AuditRecord) -> None:
            raise RuntimeError("DB down")

        db = AuditTrailDB(pg_handler=failing_pg)
        _log(db)
        _log(db)
        assert db.count("t1") == 2
        report = db.verify_chain("t1")
        assert report.valid is True


class TestComplianceReport:

    def test_generate_report(self):
        db = _db()
        _log(db, event_type=AuditEventType.CONSENT_GRANTED, severity=AuditSeverity.INFO)
        _log(db, event_type=AuditEventType.SECURITY_INCIDENT, severity=AuditSeverity.CRITICAL)
        _log(db, event_type=AuditEventType.CONSENT_GRANTED, severity=AuditSeverity.INFO)

        report = db.generate_compliance_report("t1")
        assert report["total_records"] == 3
        assert report["chain_integrity"] is True
        assert report["critical_events_count"] == 1
        assert report["event_breakdown"][AuditEventType.CONSENT_GRANTED.value] == 2

    def test_report_for_empty_tenant(self):
        db = _db()
        report = db.generate_compliance_report("empty")
        assert report["total_records"] == 0
        assert report["chain_integrity"] is True


class TestAuditEventTypes:

    def test_all_event_types_loggable(self):
        db = _db()
        for et in AuditEventType:
            _log(db, event_type=et, tenant="t_all")
        assert db.count("t_all") == len(AuditEventType)

    def test_to_dict_complete(self):
        db = _db()
        rec = _log(db, metadata={"key": "value"})
        d = rec.to_dict()
        for k in ("record_id", "tenant_id", "event_type", "severity",
                  "actor", "resource", "action", "metadata",
                  "timestamp", "prev_hash", "record_hash", "expires_at"):
            assert k in d
        assert d["metadata"]["key"] == "value"


class TestV466Integration:

    def test_full_audit_flow(self):
        """동의 → 데이터 접근 → PII 스캔 → 삭제 → 체인 검증"""
        db = _db()

        db.log("tenant_main", AuditEventType.CONSENT_GRANTED,
               "user_100", "consent_api", "GRANT", subject_id="user_100",
               metadata={"scope": ["analytics", "personalization"]})

        db.log("tenant_main", AuditEventType.PERSONAL_DATA_ACCESS,
               "system", "users_table", "SELECT WHERE user_id=100",
               subject_id="user_100")

        db.log("tenant_main", AuditEventType.PII_SCAN,
               "pii_scanner_v2", "generation_text", "SCAN",
               metadata={"pii_found": False})

        db.log("tenant_main", AuditEventType.PERSONAL_DATA_DELETE,
               "privacy_engine", "all_layers", "CASCADE_DELETE",
               subject_id="user_100", severity=AuditSeverity.WARNING,
               metadata={"certificate": "DEL-CERT-ABCD1234"})

        db.log("tenant_main", AuditEventType.DPO_DECISION,
               "chief_dpo", "pia_review", "CONDITIONALLY_APPROVED",
               metadata={"conditions": ["SCC 체결"]})

        assert db.count("tenant_main") == 5
        report = db.verify_chain("tenant_main")
        assert report.valid is True
        assert report.total_records == 5

        # 삭제 이벤트만 조회
        deletes = db.query("tenant_main", event_type=AuditEventType.PERSONAL_DATA_DELETE)
        assert len(deletes) == 1
        assert deletes[0].subject_id == "user_100"

        compliance = db.generate_compliance_report("tenant_main")
        assert compliance["chain_integrity"] is True
        assert compliance["total_records"] == 5
