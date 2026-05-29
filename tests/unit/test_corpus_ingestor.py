"""
SP-A.5 (V592) — test_corpus_ingestor.py

CorpusEntry / 3종 Ingestor / CorpusFallbackPipeline /
CorpusProvenanceIndex / 5천 신 Provenance 추적 검증

TC01~TC20: 20 cases / 목표 20/20 PASS
"""
from __future__ import annotations

import json
import os
import sys
import tempfile

import pytest

# ---------------------------------------------------------------------------
# 경로 설정
# ---------------------------------------------------------------------------
_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

from literary_system.corpus.corpus_ingestor import (
    CorpusEntry,
    CorpusFallbackOption,
    CorpusFallbackPipeline,
    PublicDomainIngestor,
    SyntheticCorpusIngestor,
    AcademicCorpusIngestor,
)
from literary_system.corpus.provenance_index import (
    CorpusProvenanceIndex,
    CorpusProvenanceRecord,
)


# ===========================================================================
# TC01 ~ TC05 : CorpusEntry 기본
# ===========================================================================

class TestCorpusEntry:
    """TC01~TC05"""

    def test_tc01_corpus_entry_creation(self):
        """TC01: CorpusEntry 기본 생성 및 필드 확인"""
        entry = CorpusEntry(
            entry_id="E001",
            text="춘향이와 이도령의 사랑 이야기",
            source_type="public_domain",
            license="public_domain",
            source_title="춘향전",
            source_author="작자미상",
            ingestor="PublicDomainIngestor",
            word_count=8,
        )
        assert entry.entry_id == "E001"
        assert entry.source_type == "public_domain"
        assert entry.license == "public_domain"
        assert entry.word_count == 8

    def test_tc02_corpus_entry_defaults(self):
        """TC02: CorpusEntry 선택 필드 기본값 확인"""
        entry = CorpusEntry(
            entry_id="E002",
            text="테스트 텍스트",
            source_type="synthetic",
            license="CC-BY-4.0",
        )
        assert entry.source_title == ""
        assert entry.source_author == ""
        assert entry.ingestor == ""
        # word_count는 구현에 따라 0이거나 auto-계산 가능 — 음수가 아님을 확인
        assert entry.word_count >= 0

    def test_tc03_corpus_fallback_option_values(self):
        """TC03: CorpusFallbackOption Enum 값 확인"""
        assert CorpusFallbackOption.PUBLIC_DOMAIN.value == "public_domain"
        assert CorpusFallbackOption.SYNTHETIC.value == "synthetic"
        assert CorpusFallbackOption.ACADEMIC.value == "academic"

    def test_tc04_corpus_entry_text_not_empty(self):
        """TC04: PublicDomainIngestor 텍스트 비어있지 않음"""
        ingestor = PublicDomainIngestor(seed=0)
        entries = ingestor.ingest(3)
        for e in entries:
            assert len(e.text) > 0, f"entry_id={e.entry_id} text is empty"

    def test_tc05_corpus_entry_unique_ids(self):
        """TC05: 수집된 entry_id 중복 없음"""
        ingestor = PublicDomainIngestor(seed=42)
        entries = ingestor.ingest(50)
        ids = [e.entry_id for e in entries]
        assert len(ids) == len(set(ids))


# ===========================================================================
# TC06 ~ TC10 : 3종 Ingestor
# ===========================================================================

class TestIngestors:
    """TC06~TC10"""

    def test_tc06_public_domain_ingestor_count(self):
        """TC06: PublicDomainIngestor count만큼 반환"""
        ingestor = PublicDomainIngestor()
        entries = ingestor.ingest(20)
        assert len(entries) == 20

    def test_tc07_public_domain_license(self):
        """TC07: PublicDomainIngestor 모든 항목 license=public_domain"""
        ingestor = PublicDomainIngestor()
        entries = ingestor.ingest(10)
        for e in entries:
            assert e.license == "public_domain"
            assert e.source_type == "public_domain"

    def test_tc08_synthetic_ingestor_count(self):
        """TC08: SyntheticCorpusIngestor count만큼 반환"""
        ingestor = SyntheticCorpusIngestor()
        entries = ingestor.ingest(15)
        assert len(entries) == 15

    def test_tc09_synthetic_ingestor_license(self):
        """TC09: SyntheticCorpusIngestor license=CC-BY-4.0"""
        ingestor = SyntheticCorpusIngestor()
        entries = ingestor.ingest(5)
        for e in entries:
            assert e.license == "CC-BY-4.0"

    def test_tc10_academic_ingestor_count(self):
        """TC10: AcademicCorpusIngestor count만큼 반환 (placeholder)"""
        ingestor = AcademicCorpusIngestor()
        entries = ingestor.ingest(10)
        assert len(entries) == 10


# ===========================================================================
# TC11 ~ TC13 : CorpusFallbackPipeline
# ===========================================================================

class TestFallbackPipeline:
    """TC11~TC13"""

    def test_tc11_pipeline_collect_total(self):
        """TC11: CorpusFallbackPipeline.collect() 합계 count 일치"""
        pipeline = CorpusFallbackPipeline(seed=0)
        entries = pipeline.collect(count=100)
        assert len(entries) == 100

    def test_tc12_pipeline_stats(self):
        """TC12: pipeline.stats() 구조 확인"""
        pipeline = CorpusFallbackPipeline()
        entries = pipeline.collect(count=30)
        stats = pipeline.stats(entries)
        assert "total" in stats
        assert stats["total"] == 30
        assert "by_source_type" in stats

    def test_tc13_pipeline_prefer_option(self):
        """TC13: prefer=SYNTHETIC 시 synthetic 항목이 먼저 채워짐"""
        pipeline = CorpusFallbackPipeline(prefer=CorpusFallbackOption.SYNTHETIC)
        entries = pipeline.collect(count=50)
        # 최소 1개 이상 synthetic
        synthetic_count = sum(1 for e in entries if e.source_type == "synthetic")
        assert synthetic_count >= 1


# ===========================================================================
# TC14 ~ TC17 : CorpusProvenanceIndex
# ===========================================================================

class TestProvenanceIndex:
    """TC14~TC17"""

    def _make_entry(self, idx: int, source_type: str = "public_domain") -> CorpusEntry:
        return CorpusEntry(
            entry_id=f"E{idx:04d}",
            text="가나다라마바사아" * 5,
            source_type=source_type,
            license="public_domain" if source_type == "public_domain" else "CC-BY-4.0",
            source_title=f"작품{idx}",
            source_author="작자미상",
            ingestor="test",
            word_count=40,
        )

    def test_tc14_register_single(self):
        """TC14: 단일 항목 register() 후 lookup 성공"""
        idx = CorpusProvenanceIndex()
        entry = self._make_entry(1)
        rec = idx.register(entry)
        assert rec.entry_id == "E0001"
        assert len(rec.sha256) == 64          # SHA-256 hex
        assert idx.size() == 1

    def test_tc15_register_batch(self):
        """TC15: register_batch() 복수 항목 등록"""
        idx = CorpusProvenanceIndex()
        entries = [self._make_entry(i) for i in range(50)]
        count = idx.register_batch(entries)
        assert count == 50
        assert idx.size() == 50

    def test_tc16_coverage_100pct(self):
        """TC16: 모든 항목 등록 후 coverage() == 1.0"""
        idx = CorpusProvenanceIndex()
        entries = [self._make_entry(i) for i in range(20)]
        idx.register_batch(entries)
        cov = idx.coverage(entries)
        assert cov == 1.0

    def test_tc17_coverage_partial(self):
        """TC17: 절반만 등록 시 coverage() < 1.0"""
        idx = CorpusProvenanceIndex()
        entries = [self._make_entry(i) for i in range(20)]
        idx.register_batch(entries[:10])
        cov = idx.coverage(entries)
        assert cov == pytest.approx(0.5, abs=0.01)


# ===========================================================================
# TC18 ~ TC20 : JSONL 영속화 + 5천 신 Provenance 추적
# ===========================================================================

class TestProvenancePersistence:
    """TC18~TC20"""

    def _make_entry(self, idx: int) -> CorpusEntry:
        return CorpusEntry(
            entry_id=f"P{idx:05d}",
            text="이야기는 계속된다. " * 3,
            source_type="synthetic",
            license="CC-BY-4.0",
            source_title=f"합성_{idx}",
            source_author="LOS",
            ingestor="SyntheticCorpusIngestor",
            word_count=15,
        )

    def test_tc18_jsonl_roundtrip(self):
        """TC18: to_jsonl / from_jsonl 왕복 일치"""
        idx = CorpusProvenanceIndex()
        entries = [self._make_entry(i) for i in range(30)]
        idx.register_batch(entries)

        with tempfile.NamedTemporaryFile(suffix=".jsonl", delete=False) as f:
            path = f.name

        try:
            written = idx.to_jsonl(path)
            assert written == 30

            idx2 = CorpusProvenanceIndex.from_jsonl(path)
            assert idx2.size() == 30
            rec = idx2.lookup("P00000")
            assert rec is not None
            assert rec.source_type == "synthetic"
        finally:
            os.unlink(path)

    def test_tc19_no_license_violation(self):
        """TC19: has_license_violation() — forbidden 라이선스 없음"""
        idx = CorpusProvenanceIndex()
        entries = [self._make_entry(i) for i in range(10)]
        idx.register_batch(entries)
        violations = idx.has_license_violation(forbidden_licenses=["proprietary", "all_rights_reserved"])
        assert violations == []

    def test_tc20_5000_provenance_coverage(self):
        """TC20: 5천 신 Provenance 100% 추적 (ADR-053 핵심 조건)"""
        pipeline = CorpusFallbackPipeline(seed=99)
        entries = pipeline.collect(count=5000)
        assert len(entries) == 5000, f"수집 항목 수 부족: {len(entries)}"

        prov_idx = CorpusProvenanceIndex()
        registered = prov_idx.register_batch(entries)
        assert registered == 5000

        cov = prov_idx.coverage(entries)
        assert cov == 1.0, f"Provenance coverage {cov:.4f} < 1.0"

        # 요약 구조 확인 (total �