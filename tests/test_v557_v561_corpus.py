"""
tests/test_v557_v561_corpus.py
Phase 6 Stage B SP2 — ExternalCorpusBridge 통합 테스트 (V557~V561)

TestCorpusIngestor    (7 tests) — V557
TestCorpusValidator   (7 tests) — V558
TestBGEM3Embedder     (7 tests) — V559
TestCIMBootstrap      (7 tests) — V560
TestGate30Integration (5 tests) — V561
"""
import pytest


# ─── V557: CorpusIngestor ────────────────────────────────────────────────────
class TestCorpusIngestor:
    def setup_method(self):
        from literary_system.corpus import CorpusIngestor
        self.ingestor = CorpusIngestor(seed=42)

    def test_ingest_target_count(self):
        report = self.ingestor.ingest(target=100)
        assert report.total_ingested == 100

    def test_entries_have_required_fields(self):
        self.ingestor.ingest(target=10)
        for e in self.ingestor.entries():
            assert e.scene_id
            assert e.genre
            assert e.content
            assert len(e.characters) == 2

    def test_synthetic_source_labeled(self):
        self.ingestor.ingest(target=20)
        assert all(e.source == "synthetic" for e in self.ingestor.entries())

    def test_genres_variety(self):
        self.ingestor.ingest(target=200)
        genres = {e.genre for e in self.ingestor.entries()}
        assert len(genres) >= 3

    def test_by_genre_filter(self):
        self.ingestor.ingest(target=200)
        from literary_system.corpus.corpus_ingestor import GENRES
        g = GENRES[0]
        subset = self.ingestor.by_genre(g)
        assert all(e.genre == g for e in subset)

    def test_sample(self):
        self.ingestor.ingest(target=50)
        s = self.ingestor.sample(k=10)
        assert len(s) == 10

    def test_ingest_report_target_reached(self):
        report = self.ingestor.ingest(target=10_000)
        assert report.target_reached is True
        assert report.total_ingested == 10_000


# ─── V558: CorpusValidator ───────────────────────────────────────────────────
class TestCorpusValidator:
    def setup_method(self):
        from literary_system.corpus import CorpusIngestor, CorpusValidator
        ingestor = CorpusIngestor(seed=7)
        ingestor.ingest(target=50)
        self.entries = ingestor.entries()
        self.validator = CorpusValidator()

    def test_validate_batch_structure(self):
        _, report = self.validator.validate_batch(self.entries)
        assert report.total == 50
        assert report.passed + report.failed_license + report.failed_pii + report.failed_quality == 50

    def test_valid_entries_returned(self):
        passed, report = self.validator.validate_batch(self.entries)
        assert len(passed) == report.passed

    def test_license_check_blocks_invalid(self):
        from literary_system.corpus.corpus_ingestor import ScenarioEntry
        bad = ScenarioEntry("x", "t", "멜로", ["a", "b"], "내용 충분히 길게 작성한 테스트 씬 입니다 확인용", license="UNKNOWN")
        result, _ = self.validator.validate_entry(bad)
        from literary_system.corpus.corpus_validator import ValidationResult
        assert result == ValidationResult.FAIL_LICENSE

    def test_pii_masking_phone(self):
        from literary_system.corpus.corpus_ingestor import ScenarioEntry
        entry = ScenarioEntry("p1", "t", "멜로", ["a", "b"], "연락처는 010-1234-5678 입니다 오늘도 잘 부탁드립니다", license="CC-BY-4.0")
        result, masked = self.validator.validate_entry(entry)
        from literary_system.corpus.corpus_validator import ValidationResult
        assert result == ValidationResult.FAIL_PII
        assert "010-1234-5678" not in masked.content
        assert "MASKED" in masked.content

    def test_pii_masking_email(self):
        from literary_system.corpus.corpus_ingestor import ScenarioEntry
        entry = ScenarioEntry("e1", "t", "멜로", ["a", "b"], "이메일은 test@example.com 로 보내주세요 감사합니다", license="CC-BY-4.0")
        result, masked = self.validator.validate_entry(entry)
        from literary_system.corpus.corpus_validator import ValidationResult
        assert result == ValidationResult.FAIL_PII
        assert "test@example.com" not in masked.content

    def test_quality_filter_too_short(self):
        from literary_system.corpus.corpus_ingestor import ScenarioEntry
        entry = ScenarioEntry("q1", "t", "멜로", ["a", "b"], "너무 짧음", license="CC-BY-4.0")
        result, _ = self.validator.validate_entry(entry)
        from literary_system.corpus.corpus_validator import ValidationResult
        assert result == ValidationResult.FAIL_QUALITY

    def test_pass_rate_positive(self):
        _, report = self.validator.validate_batch(self.entries)
        assert report.pass_rate > 0.0


# ─── V559: BGEM3Embedder ─────────────────────────────────────────────────────
class TestBGEM3Embedder:
    def setup_method(self):
        from literary_system.corpus import BGEM3Embedder
        self.embedder = BGEM3Embedder()

    def test_embed_returns_1024_dim(self):
        vec = self.embedder.embed("테스트 텍스트")
        assert len(vec) == 1024

    def test_embed_deterministic(self):
        v1 = self.embedder.embed("같은 텍스트")
        v2 = self.embedder.embed("같은 텍스트")
        assert v1 == v2

    def test_different_texts_different_vectors(self):
        v1 = self.embedder.embed("텍스트 A 내용")
        v2 = self.embedder.embed("텍스트 B 다른 내용")
        assert v1 != v2

    def test_add_entries_and_count(self):
        from literary_system.corpus import CorpusIngestor
        ingestor = CorpusIngestor(seed=0)
        ingestor.ingest(target=5)
        self.embedder.add_entries(ingestor.entries())
        assert self.embedder.index_info()["size"] == 5

    def test_index_info_structure(self):
        info = self.embedder.index_info()
        assert "size" in info
        assert "dim" in info
        assert info["dim"] == 1024

    def test_search_returns_results(self):
        from literary_system.corpus import CorpusIngestor
        ingestor = CorpusIngestor(seed=1)
        ingestor.ingest(target=10)
        self.embedder.add_entries(ingestor.entries())
        results = self.embedder.search("카페에서 만남", top_k=3)
        assert len(results) <= 3
        assert len(results) > 0

    def test_search_score_in_range(self):
        from literary_system.corpus import CorpusIngestor
        ingestor = CorpusIngestor(seed=2)
        ingestor.ingest(target=5)
        self.embedder.add_entries(ingestor.entries())
        results = self.embedder.search("진실 고백", top_k=5)
        for r in results:
            assert -1.01 <= r.score <= 1.01


# ─── V560: CIMBootstrap ──────────────────────────────────────────────────────
class TestCIMBootstrap:
    def setup_method(self):
        from literary_system.corpus import CorpusIngestor, CIMBootstrap
        ingestor = CorpusIngestor(seed=3)
        ingestor.ingest(target=100)
        self.entries = ingestor.entries()
        self.bootstrap = CIMBootstrap(decay=0.95)

    def test_fit_returns_report(self):
        from literary_system.corpus import BootstrapReport
        report = self.bootstrap.fit(self.entries)
        assert isinstance(report, BootstrapReport)
        assert report.total_scenes == 100

    def test_known_characters_populated(self):
        report = self.bootstrap.fit(self.entries)
        assert report.unique_characters > 0

    def test_warm_start_weights_structure(self):
        self.bootstrap.fit(self.entries)
        chars = ["이민준", "박지수", "김도현"]
        weights = self.bootstrap.warm_start_weights(chars)
        assert set(weights.keys()) == set(chars)
        for c in chars:
            assert set(weights[c].keys()) == set(chars)

    def test_warm_start_weights_range(self):
        self.bootstrap.fit(self.entries)
        chars = ["이민준", "박지수"]
        weights = self.bootstrap.warm_start_weights(chars)
        for a in chars:
            for b in chars:
                assert 0.0 <= weights[a][b] <= 1.0

    def test_diagonal_is_one(self):
        self.bootstrap.fit(self.entries)
        chars = ["이민준", "박지수", "김도현"]
        weights = self.bootstrap.warm_start_weights(chars)
        for c in chars:
            assert weights[c][c] == 1.0

    def test_warm_start_matrix_shape(self):
        self.bootstrap.fit(self.entries)
        chars = ["이민준", "박지수", "김도현"]
        mat = self.bootstrap.warm_start_matrix(chars)
        assert len(mat) == 3
        assert all(len(row) == 3 for row in mat)

    def test_top_pairs_sorted(self):
        report = self.bootstrap.fit(self.entries)
        if len(report.top_pairs) >= 2:
            counts = [p[2] for p in report.top_pairs]
            assert counts == sorted(counts, reverse=True)


# ─── V561: Gate30 통합 ───────────────────────────────────────────────────────
class TestGate30Integration:
    def test_gate30_function_exists(self):
        from literary_system.gates import release_gate
        assert hasattr(release_gate, "_gate_corpus_quality_g30")

    def test_gate30_passes(self):
        from literary_system.gates.release_gate import _gate_corpus_quality_g30
        result = _gate_corpus_quality_g30()
        assert result["pass"] is True, f"Gate30 FAIL: {result.get('error', '')}"

    def test_gate_count_is_29_or_more(self):
        from literary_system.gates.release_gate import GATES
        assert len(GATES) >= 29  # L1(22) + Gate25~30(6) + LLM0_static(1) = 29

    def test_release_gate_version(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["version"] in ("V561", "V571")

    def test_corpus_pipeline_end_to_end(self):
        """CorpusIngestor → Validator → BGEM3Embedder → CIMBootstrap 파이프라인."""
        from literary_system.corpus import (
            CorpusIngestor, CorpusValidator, BGEM3Embedder, CIMBootstrap
        )
        ingestor = CorpusIngestor(seed=99)
        report = ingestor.ingest(target=30)
        assert report.total_ingested == 30

        validator = CorpusValidator()
        passed, v_report = validator.validate_batch(ingestor.entries())
        assert v_report.pass_rate > 0.0

        embedder = BGEM3Embedder()
        embedder.add_entries(passed)
        results = embedder.search("운명 교차로", top_k=3)
        assert len(results) > 0

        bootstrap = CIMBootstrap()
        b_report = bootstrap.fit(ingestor.entries())
        assert b_report.unique_characters > 0
