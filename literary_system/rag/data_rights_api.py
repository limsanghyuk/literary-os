"""
V442 -- DataRightsAPI
Enforces data subject rights (GDPR Art. 17 / CCPA) over the RAG corpus.

Operations:
  right_to_erasure  -- delete all embeddings + BM25 entries for a subject
  right_to_access   -- return all stored data for a subject
  right_to_portability -- export data in portable format
  consent_gate      -- block indexing if consent not granted

Design principle:
  DataRightsAPI wraps QdrantBridge + ProvenanceLedger.
  All mutations are logged to an AuditLog (append-only).
  Subject identity is resolved through a SubjectRegistry.
"""
from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional

from literary_system.rag.retrieval_pipeline import ProvenanceLedger


# ---------------------------------------------------------------------------
# Enums & constants
# ---------------------------------------------------------------------------

class ConsentStatus(str, Enum):
    GRANTED  = "granted"
    DENIED   = "denied"
    PENDING  = "pending"
    REVOKED  = "revoked"


class RightType(str, Enum):
    ERASURE      = "erasure"
    ACCESS       = "access"
    PORTABILITY  = "portability"
    RECTIFICATION = "rectification"


# ---------------------------------------------------------------------------
# SubjectRegistry
# ---------------------------------------------------------------------------

@dataclass
class SubjectRecord:
    subject_id:  str
    email_hash:  str       # SHA-256 of email -- PII never stored raw
    consent:     ConsentStatus = ConsentStatus.PENDING
    doc_ids:     List[str] = field(default_factory=list)
    registered_at: str = ""

    def __post_init__(self):
        if not self.registered_at:
            self.registered_at = datetime.now(timezone.utc).isoformat()


class SubjectRegistry:
    """Maps subjects to their stored document IDs."""

    def __init__(self) -> None:
        self._subjects: Dict[str, SubjectRecord] = {}

    @staticmethod
    def hash_email(email: str) -> str:
        return hashlib.sha256(email.lower().strip().encode()).hexdigest()[:32]

    def register(
        self,
        subject_id: str,
        email: str,
        consent: ConsentStatus = ConsentStatus.PENDING,
    ) -> SubjectRecord:
        email_hash = self.hash_email(email)
        if subject_id in self._subjects:
            raise ValueError("Subject already registered: " + subject_id)
        rec = SubjectRecord(subject_id=subject_id, email_hash=email_hash, consent=consent)
        self._subjects[subject_id] = rec
        return rec

    def get(self, subject_id: str) -> Optional[SubjectRecord]:
        return self._subjects.get(subject_id)

    def set_consent(self, subject_id: str, status: ConsentStatus) -> None:
        rec = self._subjects.get(subject_id)
        if rec is None:
            raise KeyError("Unknown subject: " + subject_id)
        rec.consent = status

    def add_doc(self, subject_id: str, doc_id: str) -> None:
        rec = self._subjects.get(subject_id)
        if rec is None:
            raise KeyError("Unknown subject: " + subject_id)
        if doc_id not in rec.doc_ids:
            rec.doc_ids.append(doc_id)

    def remove_doc(self, subject_id: str, doc_id: str) -> None:
        rec = self._subjects.get(subject_id)
        if rec and doc_id in rec.doc_ids:
            rec.doc_ids.remove(doc_id)

    @property
    def count(self) -> int:
        return len(self._subjects)


# ---------------------------------------------------------------------------
# AuditLog
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class AuditEntry:
    entry_id:   str
    right_type: RightType
    subject_id: str
    timestamp:  str
    doc_ids:    tuple
    status:     str   # "ok" | "denied" | "error"
    reason:     str = ""


class AuditLog:
    """Append-only audit log for data rights operations."""

    def __init__(self) -> None:
        self._entries: List[AuditEntry] = []

    def append(self, entry: AuditEntry) -> None:
        self._entries.append(entry)

    def for_subject(self, subject_id: str) -> List[AuditEntry]:
        return [e for e in self._entries if e.subject_id == subject_id]

    def all_entries(self) -> List[AuditEntry]:
        return list(self._entries)

    @property
    def count(self) -> int:
        return len(self._entries)

    def export(self) -> List[Dict[str, Any]]:
        return [
            {
                "entry_id": e.entry_id,
                "right_type": e.right_type.value,
                "subject_id": e.subject_id,
                "timestamp": e.timestamp,
                "doc_ids": list(e.doc_ids),
                "status": e.status,
                "reason": e.reason,
            }
            for e in self._entries
        ]


# ---------------------------------------------------------------------------
# DataRightsAPI
# ---------------------------------------------------------------------------

class DataRightsAPI:
    """
    GDPR/CCPA data rights enforcement layer.

    Wraps an in-memory document store (simple dict) + SubjectRegistry.
    In production, doc_store would proxy QdrantBridge.
    """

    def __init__(
        self,
        registry: Optional[SubjectRegistry] = None,
        audit_log: Optional[AuditLog] = None,
    ) -> None:
        self._registry = registry or SubjectRegistry()
        self._audit = audit_log or AuditLog()
        self._doc_store: Dict[str, Dict[str, Any]] = {}

    # --- consent gate -------------------------------------------------------

    def consent_gate(self, subject_id: str) -> bool:
        """Return True if subject has granted consent for indexing."""
        rec = self._registry.get(subject_id)
        if rec is None:
            return False
        return rec.consent == ConsentStatus.GRANTED

    def index_document(
        self,
        subject_id: str,
        doc_id: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Index a document only if subject has granted consent.
        Returns True if indexed, False if blocked by consent gate.
        """
        if not self.consent_gate(subject_id):
            return False
        self._doc_store[doc_id] = {"content": content, "subject_id": subject_id, "metadata": metadata or {}}
        self._registry.add_doc(subject_id, doc_id)
        return True

    # --- Right to Erasure (GDPR Art. 17) ------------------------------------

    def right_to_erasure(self, subject_id: str) -> int:
        """
        Delete all documents belonging to subject_id.
        Returns count of deleted documents.
        Logs to AuditLog.
        """
        rec = self._registry.get(subject_id)
        if rec is None:
            self._log(RightType.ERASURE, subject_id, [], "error", "Unknown subject")
            raise KeyError("Unknown subject: " + subject_id)

        deleted = []
        for doc_id in list(rec.doc_ids):
            if doc_id in self._doc_store:
                del self._doc_store[doc_id]
                deleted.append(doc_id)
            self._registry.remove_doc(subject_id, doc_id)

        self._log(RightType.ERASURE, subject_id, deleted, "ok")
        return len(deleted)

    # --- Right to Access ---------------------------------------------------

    def right_to_access(self, subject_id: str) -> List[Dict[str, Any]]:
        """Return all stored data for subject_id."""
        rec = self._registry.get(subject_id)
        if rec is None:
            raise KeyError("Unknown subject: " + subject_id)

        docs = []
        for doc_id in rec.doc_ids:
            entry = self._doc_store.get(doc_id)
            if entry:
                docs.append({"doc_id": doc_id, **entry})

        self._log(RightType.ACCESS, subject_id, [d["doc_id"] for d in docs], "ok")
        return docs

    # --- Right to Portability ----------------------------------------------

    def right_to_portability(self, subject_id: str) -> Dict[str, Any]:
        """Export subject data in portable JSON-serializable format."""
        docs = self.right_to_access(subject_id)
        rec = self._registry.get(subject_id)
        export = {
            "subject_id": subject_id,
            "consent_status": rec.consent.value if rec else "unknown",
            "exported_at": datetime.now(timezone.utc).isoformat(),
            "documents": docs,
        }
        self._log(RightType.PORTABILITY, subject_id, [d["doc_id"] for d in docs], "ok")
        return export

    # --- helpers ------------------------------------------------------------

    def _log(
        self,
        right_type: RightType,
        subject_id: str,
        doc_ids: List[str],
        status: str,
        reason: str = "",
    ) -> None:
        entry = AuditEntry(
            entry_id=str(uuid.uuid4()),
            right_type=right_type,
            subject_id=subject_id,
            timestamp=datetime.now(timezone.utc).isoformat(),
            doc_ids=tuple(doc_ids),
            status=status,
            reason=reason,
        )
        self._audit.append(entry)

    @property
    def registry(self) -> SubjectRegistry:
        return self._registry

    @property
    def audit_log(self) -> AuditLog:
        return self._audit

    @property
    def indexed_doc_count(self) -> int:
        return len(self._doc_store)
