"""ProvenanceLedger — sha256 blockchain-lite chain for LoRA dataset entries.

ADR-056: 각 레코드는 entry_id, content_hash, prev_hash, created_at 을
sha256 해시로 연결. append-only. DSR 삭제 마킹 지원.
"""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import List, Optional


class ProvenanceChainError(Exception):
    """체인 무결성 위반 시 발생."""


@dataclass
class LedgerEntry:
    """단일 출처 레코드."""

    entry_id: str
    content_hash: str
    prev_hash: str
    created_at: float
    record_id: str = ""
    dsr_deleted: bool = False
    dsr_request_id: Optional[str] = None

    def __post_init__(self) -> None:
        if not self.record_id:
            self.record_id = self._compute_id()

    def _compute_id(self) -> str:
        payload = f"{self.entry_id}:{self.content_hash}:{self.prev_hash}:{self.created_at}"
        return hashlib.sha256(payload.encode()).hexdigest()


class LoRAProvenanceLedger:
    """sha256 체인 출처 원장.

    Usage:
        ledger = LoRAProvenanceLedger()
        ledger.append("entry-1", "abc123")
        ledger.verify()  # True
    """

    GENESIS_HASH = "0" * 64

    def __init__(self) -> None:
        self._records: List[LedgerEntry] = []

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def append(self, entry_id: str, content_hash: str) -> ProvenanceRecord:
        """새 레코드를 체인에 추가."""
        prev_hash = self._records[-1].record_id if self._records else self.GENESIS_HASH
        record = LedgerEntry(
            entry_id=entry_id,
            content_hash=content_hash,
            prev_hash=prev_hash,
            created_at=time.time(),
        )
        self._records.append(record)
        return record

    def mark_dsr_deleted(self, entry_id: str, request_id: str) -> bool:
        """entry_id 에 해당하는 레코드를 DSR 삭제 마킹."""
        for rec in self._records:
            if rec.entry_id == entry_id and not rec.dsr_deleted:
                rec.dsr_deleted = True
                rec.dsr_request_id = request_id
                return True
        return False

    def active_records(self) -> List[LedgerEntry]:
        """DSR 삭제되지 않은 레코드 목록."""
        return [r for r in self._records if not r.dsr_deleted]

    def verify(self) -> bool:
        """체인 무결성 검증. 문제 시 ProvenanceChainError 발생."""
        expected_prev = self.GENESIS_HASH
        for rec in self._records:
            if rec.prev_hash != expected_prev:
                raise ProvenanceChainError(
                    f"Chain broken at {rec.record_id}: "
                    f"expected prev={expected_prev}, got={rec.prev_hash}"
                )
            computed = rec._compute_id()
            if computed != rec.record_id:
                raise ProvenanceChainError(
                    f"Record ID mismatch at {rec.entry_id}: "
                    f"expected={computed}, stored={rec.record_id}"
                )
            expected_prev = rec.record_id
        return True

    def __len__(self) -> int:
        return len(self._records)

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def save(self, path: Path) -> None:
        """JSONL 파일로 저장."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as fh:
            for rec in self._records:
                fh.write(json.dumps(asdict(rec)) + "\n")

    @classmethod
    def load(cls, path: Path) -> LoRAProvenanceLedger:
        """JSONL 파일에서 로드."""
        ledger = cls()
        path = Path(path)
        if not path.exists():
            return ledger
        with path.open("r", encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                data = json.loads(line)
                rec = LedgerEntry(**data)
                ledger._records.append(rec)
        return ledger
