"""
V442 tests -- DataRightsAPI (GDPR/CCPA)
"""
import pytest
from literary_system.rag.data_rights_api import (
    ConsentStatus, RightType, SubjectRecord, SubjectRegistry,
    AuditEntry, AuditLog, DataRightsAPI,
)


# ---------------------------------------------------------------------------
# TestConsentStatus
# ---------------------------------------------------------------------------

class TestConsentStatus:
    def test_values(self):
        assert ConsentStatus.GRANTED.value == "granted"
        assert ConsentStatus.DENIED.value == "denied"
        assert ConsentStatus.REVOKED.value == "revoked"


# ---------------------------------------------------------------------------
# TestSubjectRegistry
# ---------------------------------------------------------------------------

class TestSubjectRegistry:
    def test_register(self):
        r = SubjectRegistry()
        rec = r.register("s1", "user@example.com")
        assert rec.subject_id == "s1"
        assert rec.email_hash  # not empty

    def test_duplicate_raises(self):
        r = SubjectRegistry()
        r.register("s1", "a@b.com")
        with pytest.raises(ValueError):
            r.register("s1", "a@b.com")

    def test_hash_email_consistent(self):
        h1 = SubjectRegistry.hash_email("User@Example.COM")
        h2 = SubjectRegistry.hash_email("user@example.com")
        assert h1 == h2

    def test_set_consent(self):
        r = SubjectRegistry()
        r.register("s1", "a@b.com")
        r.set_consent("s1", ConsentStatus.GRANTED)
        assert r.get("s1").consent == ConsentStatus.GRANTED

    def test_set_consent_unknown_raises(self):
        r = SubjectRegistry()
        with pytest.raises(KeyError):
            r.set_consent("unknown", ConsentStatus.GRANTED)

    def test_add_and_remove_doc(self):
        r = SubjectRegistry()
        r.register("s1", "a@b.com")
        r.add_doc("s1", "doc1")
        assert "doc1" in r.get("s1").doc_ids
        r.remove_doc("s1", "doc1")
        assert "doc1" not in r.get("s1").doc_ids

    def test_get_missing_returns_none(self):
        r = SubjectRegistry()
        assert r.get("nonexistent") is None

    def test_count(self):
        r = SubjectRegistry()
        r.register("s1", "a@b.com")
        r.register("s2", "b@c.com")
        assert r.count == 2


# ---------------------------------------------------------------------------
# TestAuditLog
# ---------------------------------------------------------------------------

class TestAuditLog:
    def _make_entry(self, subject_id="s1"):
        import uuid
        from datetime import datetime, timezone
        return AuditEntry(
            entry_id=str(uuid.uuid4()),
            right_type=RightType.ERASURE,
            subject_id=subject_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            doc_ids=("d1", "d2"),
            status="ok",
        )

    def test_append_and_count(self):
        log = AuditLog()
        log.append(self._make_entry())
        assert log.count == 1

    def test_for_subject(self):
        log = AuditLog()
        log.append(self._make_entry("s1"))
        log.append(self._make_entry("s2"))
        assert len(log.for_subject("s1")) == 1

    def test_export(self):
        log = AuditLog()
        log.append(self._make_entry())
        exported = log.export()
        assert len(exported) == 1
        assert "entry_id" in exported[0]
        assert "right_type" in exported[0]


# ---------------------------------------------------------------------------
# TestDataRightsAPI
# ---------------------------------------------------------------------------

class TestDataRightsAPI:
    def _setup(self):
        api = DataRightsAPI()
        api.registry.register("s1", "alice@example.com", consent=ConsentStatus.GRANTED)
        return api

    def test_consent_gate_granted(self):
        api = self._setup()
        assert api.consent_gate("s1") is True

    def test_consent_gate_denied(self):
        api = DataRightsAPI()
        api.registry.register("s1", "a@b.com", consent=ConsentStatus.DENIED)
        assert api.consent_gate("s1") is False

    def test_consent_gate_unknown(self):
        api = DataRightsAPI()
        assert api.consent_gate("nobody") is False

    def test_index_document_with_consent(self):
        api = self._setup()
        ok = api.index_document("s1", "doc1", "some text")
        assert ok is True
        assert api.indexed_doc_count == 1

    def test_index_document_without_consent(self):
        api = DataRightsAPI()
        api.registry.register("s2", "b@b.com", consent=ConsentStatus.DENIED)
        ok = api.index_document("s2", "doc1", "text")
        assert ok is False
        assert api.indexed_doc_count == 0

    def test_right_to_erasure(self):
        api = self._setup()
        api.index_document("s1", "doc1", "text")
        api.index_document("s1", "doc2", "more text")
        deleted = api.right_to_erasure("s1")
        assert deleted == 2
        assert api.indexed_doc_count == 0

    def test_erasure_unknown_subject_raises(self):
        api = DataRightsAPI()
        with pytest.raises(KeyError):
            api.right_to_erasure("nobody")

    def test_erasure_logged(self):
        api = self._setup()
        api.index_document("s1", "doc1", "text")
        api.right_to_erasure("s1")
        logs = api.audit_log.for_subject("s1")
        assert any(e.right_type == RightType.ERASURE for e in logs)

    def test_right_to_access(self):
        api = self._setup()
        api.index_document("s1", "doc1", "hello world")
        docs = api.right_to_access("s1")
        assert len(docs) == 1
        assert docs[0]["doc_id"] == "doc1"

    def test_access_logged(self):
        api = self._setup()
        api.right_to_access("s1")
        logs = api.audit_log.for_subject("s1")
        assert any(e.right_type == RightType.ACCESS for e in logs)

    def test_right_to_portability(self):
        api = self._setup()
        api.index_document("s1", "doc1", "content")
        export = api.right_to_portability("s1")
        assert "subject_id" in export
        assert "documents" in export
        assert "exported_at" in export
        assert export["consent_status"] == "granted"

    def test_revoke_consent_blocks_future_index(self):
        api = self._setup()
        api.registry.set_consent("s1", ConsentStatus.REVOKED)
        ok = api.index_document("s1", "doc_new", "text")
        assert ok is False
