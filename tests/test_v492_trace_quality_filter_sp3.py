"""tests/test_v492_trace_quality_filter_sp3.py — TraceQualityFilterSP3 테스트"""
import pytest
from literary_system.slm.trace_quality_filter_sp3 import (
    TraceQualityFilterSP3, SP3Record, SP3FilterResult, DedupReport,
    jaccard_estimate, _minhash, _shingles, _tokenize,
)


def _make_records(n=20, quality=0.8, tier="A", text_prefix="씬"):
    return [{"id": f"r{i}", "text": f"{text_prefix} {i}: 주인공이 등장하여 갈등을 겪는다.",
             "quality_score": quality, "tier": tier, "opt_in": True, "license": "cc-by"}
            for i in range(n)]


# ── SP3Record ────────────────────────────────────────────────────────

class TestSP3Record:
    def test_from_dict_defaults(self):
        r = SP3Record.from_dict({"id": "x", "text": "hello"})
        assert r.quality_score == 1.0
        assert r.tier == "A"
        assert r.opt_in is True

    def test_from_dict_full(self):
        r = SP3Record.from_dict({
            "id": "x", "text": "안녕", "quality_score": 0.9,
            "tier": "B", "opt_in": False, "license": "mit"
        })
        assert r.quality_score == 0.9
        assert r.tier == "B"
        assert not r.opt_in

    def test_to_dict_roundtrip(self):
        r = SP3Record(id="x", text="hi", quality_score=0.7, tier="A", opt_in=True, license="cc-by")
        d = r.to_dict()
        assert d["id"] == "x"
        assert d["text"] == "hi"
        assert d["quality_score"] == 0.7


# ── MinHash 헬퍼 ─────────────────────────────────────────────────────

class TestMinHash:
    def test_identical_texts_jaccard_one(self):
        sig = _minhash(_shingles(_tokenize("주인공이 등장한다 갈등이 고조된다")))
        assert jaccard_estimate(sig, sig) == pytest.approx(1.0)

    def test_different_texts_jaccard_low(self):
        s1 = _minhash(_shingles(_tokenize("주인공이 등장한다")))
        s2 = _minhash(_shingles(_tokenize("전혀 다른 내용의 완전히 새로운 문장")))
        assert jaccard_estimate(s1, s2) < 0.5

    def test_near_duplicate_high_similarity(self):
        s1 = _minhash(_shingles(_tokenize("씬 1: 주인공이 등장하여 갈등을 겪는다")))
        s2 = _minhash(_shingles(_tokenize("씬 1: 주인공이 등장하여 갈등을 겪는다")))  # 동일
        assert jaccard_estimate(s1, s2) > 0.9


# ── TraceQualityFilterSP3 ────────────────────────────────────────────

class TestTraceQualityFilterSP3:
    def test_basic_run_returns_sp3_filter_result(self):
        tqf = TraceQualityFilterSP3()
        result = tqf.run(_make_records(30))
        assert isinstance(result, SP3FilterResult)
        assert result.total_kept > 0

    def test_split_ratios(self):
        tqf = TraceQualityFilterSP3(train_ratio=0.8, val_ratio=0.1, test_ratio=0.1)
        result = tqf.run(_make_records(100))
        total = result.total_kept
        assert total > 0
        # train이 가장 커야 함
        assert len(result.train) >= len(result.val)
        assert len(result.train) >= len(result.test)

    def test_quality_filter_removes_low_quality(self):
        records = _make_records(10, quality=0.8) + _make_records(5, quality=0.1)
        tqf = TraceQualityFilterSP3(min_quality=0.5)
        result = tqf.run(records)
        assert result.quality_removed == 5

    def test_tier_filter_removes_c_tier(self):
        records = _make_records(10, tier="A") + _make_records(5, tier="C")
        tqf = TraceQualityFilterSP3()
        result = tqf.run(records)
        assert result.tier_removed == 5

    def test_opt_in_filter(self):
        records = [{"id": f"r{i}", "text": f"씬 {i}", "quality_score": 0.9,
                    "tier": "A", "opt_in": False, "license": "cc-by"} for i in range(5)]
        tqf = TraceQualityFilterSP3()
        result = tqf.run(records)
        assert result.tier_removed == 5

    def test_dedup_removes_duplicates(self):
        base = {"text": "완전히 동일한 텍스트가 반복된다", "quality_score": 0.9,
                "tier": "A", "opt_in": True, "license": "cc-by"}
        records = [{"id": f"r{i}", **base} for i in range(10)]
        tqf = TraceQualityFilterSP3(dedup_threshold=0.9)
        result = tqf.run(records)
        assert result.dedup_report.removed_count > 0
        assert result.total_kept < 10

    def test_pii_scrubbed_count(self):
        records = [{"id": "p1", "text": "주민번호: 850101-1234567", "quality_score": 0.9,
                    "tier": "A", "opt_in": True, "license": "cc-by"}]
        tqf = TraceQualityFilterSP3(scrub_pii=True)
        result = tqf.run(records)
        assert result.pii_scrubbed >= 1
        if result.train:
            assert "850101-1234567" not in result.train[0].text

    def test_export_jsonl(self):
        tqf = TraceQualityFilterSP3()
        result = tqf.run(_make_records(30))
        jsonl = result.export_jsonl("train")
        lines = [l for l in jsonl.split("\n") if l.strip()]
        assert len(lines) == len(result.train)

    def test_counts_dict(self):
        tqf = TraceQualityFilterSP3()
        result = tqf.run(_make_records(30))
        counts = result.counts()
        assert "train" in counts and "val" in counts and "test" in counts

    def test_summary_string(self):
        tqf = TraceQualityFilterSP3()
        result = tqf.run(_make_records(20))
        s = result.summary()
        assert "SP3FilterResult" in s

    def test_invalid_ratio_raises(self):
        with pytest.raises(AssertionError):
            TraceQualityFilterSP3(train_ratio=0.9, val_ratio=0.1, test_ratio=0.1)

    def test_dedup_report_structure(self):
        tqf = TraceQualityFilterSP3()
        result = tqf.run(_make_records(20))
        dr = result.dedup_report
        assert isinstance(dr, DedupReport)
        assert 0.0 <= dr.removal_rate <= 1.0

    def test_empty_input(self):
        tqf = TraceQualityFilterSP3()
        result = tqf.run([])
        assert result.total_kept == 0
        assert result.quality_removed == 0

    def test_mixed_tiers_stratified(self):
        records = _make_records(10, tier="A") + _make_records(10, tier="B")
        tqf = TraceQualityFilterSP3()
        result = tqf.run(records)
        assert result.total_kept > 0

    def test_no_pii_scrub(self):
        records = [{"id": "p1", "text": "010-1234-5678", "quality_score": 0.9,
                    "tier": "A", "opt_in": True, "license": "cc-by"}]
        tqf = TraceQualityFilterSP3(scrub_pii=False)
        result = tqf.run(records)
        assert result.pii_scrubbed == 0
