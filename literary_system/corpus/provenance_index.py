"""
SP-A.5 (V592) — CorpusProvenanceIndex: 코퍼스 Provenance 추적 원장

5천 신 이상의 CorpusEntry에 대해 출처·라이선스·해시를 100% 추적.
기존 rag/retrieval_pipeline.py의 ProvenanceRecord와 별개 — 코퍼스 전용.

ADR-053 참조.
LLM-0 준수: 외부 LLM 호출 없음.
"""
from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional

if TYPE_CHECKING:
    from literary_system.corpus.corpus_ingestor import CorpusEntry


# ---------------------------------------------------------------------------
# CorpusProvenanceRecord
# ---------------------------------------------------------------------------

@dataclass
class CorpusProvenanceRecord:
    """
    단일 코퍼스 항목의 Provenance 기록.
    (기존 rag/retrieval_pipeline.py ProvenanceRecord와 별개 — 코퍼스 전용)

    Attributes:
        entry_id:    CorpusEntry.entry_id
        source_type: CorpusFallbackOption.value ("public_domain" / "synthetic" / "academic")
        license:     라이선스 식별자 (e.g. "public_domain", "CC-BY-4.0")
        source_title:  작품명
        source_author: 작가명
        sha256:      텍스트 SHA-256 해시 (무결성 검증)
        ingested_at: 수집 시각 (ISO8601 UTC)
        word_count:  단어 수
    """
    entry_id:      str
    source_type:   str
    license:       str
    source_title:  str  = ""
    source_author: str  = ""
    sha256:        str  = ""
    ingested_at:   str  = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat()
    )
    word_count:    int  = 0

    def to_dict(self) -> dict:
        return {
            "entry_id":      self.entry_id,
            "source_type":   self.source_type,
            "license":       self.license,
            "source_title":  self.source_title,
            "source_author": self.source_author,
            "sha256":        self.sha256,
            "ingested_at":   self.ingested_at,
            "word_count":    self.word_count,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "CorpusProvenanceRecord":
        return cls(**{k: d.get(k, "") for k in (
            "entry_id", "source_type", "license",
            "source_title", "source_author", "sha256", "ingested_at",
        )}, word_count=int(d.get("word_count", 0)))


# ---------------------------------------------------------------------------
# CorpusProvenanceIndex
# ---------------------------------------------------------------------------

class CorpusProvenanceIndex:
    """
    코퍼스 Provenance 원장.

    모든 CorpusEntry에 대해 출처·라이선스·해시를 100% 추적.
    JSONL 형식으로 영속화 / 복원 가능.

    Usage::

        index = CorpusProvenanceIndex()
        for entry in entries:
            index.register(entry)

        coverage = index.coverage(entries)  # 1.0 이어야 함
        index.to_jsonl("/data/provenance.jsonl")
    """

    def __init__(self) -> None:
        self._records: Dict[str, CorpusProvenanceRecord] = {}

    # ── 핵심 API ─────────────────────────────────────────────

    def register(self, entry: "CorpusEntry") -> CorpusProvenanceRecord:
        """CorpusEntry를 Provenance 원장에 등록."""
        sha256 = hashlib.sha256(entry.text.encode("utf-8")).hexdigest()
        rec = CorpusProvenanceRecord(
            entry_id      = entry.entry_id,
            source_type   = entry.source_type,
            license       = entry.license,
            source_title  = getattr(entry, "source_title", ""),
            source_author = getattr(entry, "source_author", ""),
            sha256        = sha256,
            word_count    = entry.word_count,
        )
        self._records[entry.entry_id] = rec
        return rec

    def register_batch(self, entries: List["CorpusEntry"]) -> int:
        """다수 CorpusEntry 일괄 등록. 등록된 수 반환."""
        for entry in entries:
            self.register(entry)
        return len(entries)

    def lookup(self, entry_id: str) -> Optional[CorpusProvenanceRecord]:
        """entry_id로 Provenance 기록 조회."""
        return self._records.get(entry_id)

    def coverage(self, entries: List["CorpusEntry"]) -> float:
        """
        주어진 entries 중 Provenance가 등록된 비율 (0.0~1.0).
        ADR-053 완료 조건: coverage == 1.0 (100%)
        """
        if not entries:
            return 0.0
        tracked = sum(1 for e in entries if e.entry_id in self._records)
        return tracked / len(entries)

    def size(self) -> int:
        """등록된 Provenance 레코드 수."""
        return len(self._records)

    def has_license_violation(self, forbidden_licenses: Optional[List[str]] = None) -> List[str]:
        """
        허용되지 않은 라이선스 보유 entry_id 목록 반환.
        기본 금지 라이선스: ["unknown", "proprietary", "all_rights_reserved"]
        """
        forbidden = forbidden_licenses or ["unknown", "proprietary", "all_rights_reserved"]
        return [
            rec.entry_id
            for rec in self._records.values()
            if rec.license.lower() in forbidden
        ]

    def summary(self) -> dict:
        """원장 요약 통계."""
        by_source: dict = {}
        by_license: dict = {}
        total_words = 0
        for rec in self._records.values():
            by_source[rec.source_type]  = by_source.get(rec.source_type, 0) + 1
            by_license[rec.license]     = by_license.get(rec.license, 0) + 1
            total_words += rec.word_count
        return {
            "total_records": len(self._records),
            "total_words":   total_words,
            "by_source":     by_source,
            "by_license":    by_license,
        }

    # ── 영속화 ────────────────────────────────────────────────

    def to_jsonl(self, path: str) -> int:
        """
        Provenance 레코드를 JSONL 파일로 저장.
        Returns: 저장된 레코드 수.
        """
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            for rec in self._records.values():
                f.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")
        return len(self._records)

    @classmethod
    def from_jsonl(cls, path: str) -> "CorpusProvenanceIndex":
        """JSONL 파일에서 ProvenanceIndex 복원."""
        index = cls()
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                d   = json.loads(line)
                rec = CorpusProvenanceRecord.from_dict(d)
                index._records[rec.entry_id] = rec
        return index
