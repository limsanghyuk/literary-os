"""
V720: ZeroTrustAuditLog 단위 테스트 (33 TC)
============================================
ADR-181: HMAC-SHA256 체인 기반 변조 방지 감사 로그
"""
import pytest, time, threading, json, hmac, hashlib
from literary_system.security.zero_trust_audit_log import ZeroTrustAuditLog, AuditRecord


# ── Fixture ──────────────────────────────────────────────────────────────────

@pytest.fixture
def log():
    return ZeroTrustAuditLog(secret_key="test-secret-key")


def _append(log, n=5):
    for i in range(n):
        log.append(
            action="PASS", subject=f"user-{i}", tenant_id="t1",
            decision="ALLOW", reason="valid token",
        )


# ── TC01~05: 기본 추가 ────────────────────────────────────────────────────────

def test_tc01_append_returns_audit_record(log):
    rec = log.append("PASS", "alice", "t1", "ALLOW", "ok")
    assert isinstance(rec, AuditRecord)

def test_tc02_record_count_increments(log):
    assert log.record_count == 0
    _append(log, 3)
    assert log.record_count == 3

def test_tc03_seq_starts_at_zero(log):
    rec = log.append("PASS", "alice", "t1", "ALLOW", "ok")
    assert rec.seq == 0

def test_tc04_seq_increments(log):
    _append(log, 3)
    records = log.export_records()
    seqs = [r["seq"] for r in records]
    assert seqs == [0, 1, 2]

def test_tc05_chain_hash_not_empty(log):
    rec = log.append("PASS", "alice", "t1", "ALLOW", "ok")
    assert len(rec.chain_hash) == 64   # SHA256 hex = 64 chars


# ── TC06~10: 체인 무결성 ──────────────────────────────────────────────────────

def test_tc06_verify_chain_empty_log(log):
    assert log.verify_chain() is True

def test_tc07_verify_chain_single_record(log):
    log.append("PASS", "alice", "t1", "ALLOW", "ok")
    assert log.verify_chain() is True

def test_tc08_verify_chain_multiple_records(log):
    _append(log, 10)
    assert log.verify_chain() is True

def test_tc09_tamper_detection_hash_altered(log):
    _append(log, 3)
    log._records[1].chain_hash = "0" * 64   # 변조
    assert log.verify_chain() is False

def test_tc10_tamper_detection_body_altered(log):
    _append(log, 3)
    log._records[1].subject = "HACKED"      # 본문 변조
    assert log.verify_chain() is False


# ── TC11~15: 첫 레코드 genesis ────────────────────────────────────────────────

def test_tc11_first_record_uses_genesis(log):
    rec = log.append("PASS", "alice", "t1", "ALLOW", "ok")
    # genesis_hash + body → hash(rec) 직접 계산
    body = {k: v for k, v in rec.to_dict().items() if k != "chain_hash"}
    payload = ZeroTrustAuditLog.GENESIS_HASH + json.dumps(body, sort_keys=True)
    expected = hmac.new(b"test-secret-key", payload.encode(), hashlib.sha256).hexdigest()
    assert rec.chain_hash == expected

def test_tc12_second_record_uses_prev_hash(log):
    r0 = log.append("PASS", "alice", "t1", "ALLOW", "ok")
    r1 = log.append("DENY", "bob", "t2", "DENY", "expired")
    body1 = {k: v for k, v in r1.to_dict().items() if k != "chain_hash"}
    payload = r0.chain_hash + json.dumps(body1, sort_keys=True)
    expected = hmac.new(b"test-secret-key", payload.encode(), hashlib.sha256).hexdigest()
    assert r1.chain_hash == expected

def test_tc13_different_key_different_hash():
    log_a = ZeroTrustAuditLog(secret_key="key-a")
    log_b = ZeroTrustAuditLog(secret_key="key-b")
    log_a.append("PASS", "alice", "t1", "ALLOW", "ok")
    log_b.append("PASS", "alice", "t1", "ALLOW", "ok")
    assert log_a._records[0].chain_hash != log_b._records[0].chain_hash

def test_tc14_genesis_constant():
    assert ZeroTrustAuditLog.GENESIS_HASH == "GENESIS"

def test_tc15_chain_hash_is_hex_sha256(log):
    rec = log.append("PASS", "u", "t", "ALLOW", "r")
    int(rec.chain_hash, 16)   # must be valid hex
    assert len(rec.chain_hash) == 64


# ── TC16~20: export / query ───────────────────────────────────────────────────

def test_tc16_export_records_is_list_of_dicts(log):
    _append(log, 3)
    exported = log.export_records()
    assert isinstance(exported, list)
    assert all(isinstance(r, dict) for r in exported)

def test_tc17_export_contains_all_fields(log):
    log.append("PASS", "alice", "t1", "ALLOW", "ok")
    r = log.export_records()[0]
    for key in ["seq", "timestamp", "action", "subject", "tenant_id",
                "decision", "reason", "chain_hash"]:
        assert key in r

def test_tc18_query_by_subject(log):
    log.append("PASS", "alice", "t1", "ALLOW", "ok")
    log.append("DENY", "bob", "t1", "DENY", "expired")
    results = log.query(subject="alice")
    assert all(r.subject == "alice" for r in results)
    assert len(results) == 1

def test_tc19_query_by_tenant_id(log):
    log.append("PASS", "alice", "t-alpha", "ALLOW", "ok")
    log.append("PASS", "bob", "t-beta", "ALLOW", "ok")
    results = log.query(tenant_id="t-alpha")
    assert len(results) == 1

def test_tc20_query_by_decision(log):
    log.append("PASS", "alice", "t1", "ALLOW", "ok")
    log.append("DENY", "bob", "t1", "DENY", "expired")
    log.append("PASS", "carol", "t1", "ALLOW", "ok")
    deny = log.query(decision="DENY")
    assert len(deny) == 1 and deny[0].decision == "DENY"


# ── TC21~25: 카운터 / limit ───────────────────────────────────────────────────

def test_tc21_allow_count(log):
    log.append("PASS", "a", "t", "ALLOW", "ok")
    log.append("DENY", "b", "t", "DENY", "exp")
    log.append("PASS", "c", "t", "ALLOW", "ok")
    assert log.allow_count() == 2

def test_tc22_deny_count(log):
    log.append("DENY", "b", "t", "DENY", "exp")
    log.append("DENY", "c", "t", "DENY", "inv")
    assert log.deny_count() == 2

def test_tc23_query_limit(log):
    _append(log, 20)
    results = log.query(limit=5)
    assert len(results) <= 5

def test_tc24_query_returns_most_recent_first(log):
    _append(log, 10)
    results = log.query(limit=3)
    assert results[0].seq > results[1].seq > results[2].seq

def test_tc25_query_by_action(log):
    log.append("ISSUE", "svc", "t", "ALLOW", "issued")
    log.append("PASS", "user", "t", "ALLOW", "ok")
    results = log.query(action="ISSUE")
    assert len(results) == 1


# ── TC26~30: 최대 레코드 / max_records ────────────────────────────────────────

def test_tc26_max_records_evicts_oldest():
    log = ZeroTrustAuditLog(secret_key="k", max_records=5)
    for i in range(7):
        log.append("PASS", f"u{i}", "t", "ALLOW", "ok")
    assert log.record_count == 5

def test_tc27_after_eviction_chain_starts_fresh():
    """max_records 초과 후 새 체인도 verify_chain PASS."""
    log = ZeroTrustAuditLog(secret_key="k", max_records=3)
    for i in range(5):
        log.append("PASS", f"u{i}", "t", "ALLOW", "ok")
    # 체인 검증은 현재 in-memory 레코드 기준이므로 PASS
    assert log.verify_chain() is True

def test_tc28_record_count_bounded(log):
    log2 = ZeroTrustAuditLog(secret_key="k", max_records=10)
    for _ in range(15):
        log2.append("PASS", "u", "t", "ALLOW", "ok")
    assert log2.record_count == 10

def test_tc29_extra_field_stored(log):
    log.append("PASS", "u", "t", "ALLOW", "ok", extra={"ip": "1.2.3.4"})
    r = log.export_records()[0]
    assert r["extra"]["ip"] == "1.2.3.4"

def test_tc30_timestamp_is_iso_utc(log):
    rec = log.append("PASS", "u", "t", "ALLOW", "ok")
    # Must parse as ISO and contain 'T'
    from datetime import datetime
    dt = datetime.fromisoformat(rec.timestamp.replace("Z", "+00:00"))
    assert dt.tzinfo is not None


# ── TC31~33: 스레드 안전 / 직렬화 ────────────────────────────────────────────

def test_tc31_thread_safe_append():
    log = ZeroTrustAuditLog(secret_key="k")
    threads = [
        threading.Thread(target=lambda: log.append("PASS", "u", "t", "ALLOW", "ok"))
        for _ in range(50)
    ]
    [t.start() for t in threads]
    [t.join() for t in threads]
    assert log.record_count == 50
    assert log.verify_chain() is True

def test_tc32_record_from_dict_roundtrip(log):
    rec = log.append("DENY", "bob", "tenant-x", "DENY", "expired")
    d = rec.to_dict()
    restored = AuditRecord.from_dict(d)
    assert restored.chain_hash == rec.chain_hash
    assert restored.seq == rec.seq

def test_tc33_verify_chain_after_query_unchanged(log):
    _append(log, 5)
    _ = log.query(limit=3)     # query should not mutate chain
    assert log.verify_chain() is True
