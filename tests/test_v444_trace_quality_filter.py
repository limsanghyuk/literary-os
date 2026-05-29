"""
V444 tests -- TraceQualityFilter (PromotionTier + MinHash dedup + stratified split)
"""
import tempfile
import pytest
from literary_system.slm.trace_quality_filter import (
    TraceQualityFilter, minhash_signature, jaccard_estimate,
    DedupStats, SplitResult, FilterResult,
    NUM_HASHES, SHINGLE_K,
)
from literary_system.trace.trace_dataset_store import (
    TraceDatasetStore, TraceRecord, PromotionTier, make_trace_record,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_BEFORE = {"SP": 0.4, "RU": 0.3, "ET": 0.2}
_AFTER  = {"SP": 0.5, "RU": 0.4, "ET": 0.3}


def _rec(
    user_prompt="씬 내용",
    render_text="씬 본문 텍스트",
    L_total=0.10,
    genre="drama",
    scene_id="sc01",
    episode_no=1,
) -> TraceRecord:
    return make_trace_record(
        project_id="test_proj",
        episode_no=episode_no,
        scene_id=scene_id,
        seed_contract={"genre": genre, "user_prompt": user_prompt},
        style_dna_profile="압박형",
        macroarc_intent="갈등 심화",
        literary_state_before=_BEFORE,
        literary_state_after=_AFTER,
        render_output={scene_id: render_text},
        loss_report={"L_total": L_total},
        reader_estimate={"reader_pull": 0.60, "ai_smell_score": 0.10},
        trajectory_deviation=0.05,
        critic_findings=[],
        repair_applied=False,
        hitl_recommended=False,
        knowledge_pressure=0.3,
    )


def _archive_rec(scene_id="arc01", episode_no=99) -> TraceRecord:
    """L_total=0.99 → ARCHIVE 티어."""
    return _rec(render_text="archived scene", L_total=0.99, scene_id=scene_id, episode_no=episode_no)


def _candidate_rec(scene_id="cand01", episode_no=2) -> TraceRecord:
    """L_total=0.15 → CANDIDATE 티어."""
    return _rec(render_text="candidate scene content", L_total=0.15, scene_id=scene_id, episode_no=episode_no)


def _canonical_rec(scene_id="can01", render_text="canonical scene content", episode_no=1, genre="drama") -> TraceRecord:
    """L_total=0.10 → CANONICAL 티어."""
    return _rec(render_text=render_text, L_total=0.10, scene_id=scene_id, episode_no=episode_no, genre=genre)


# ---------------------------------------------------------------------------
# TestMinHash
# ---------------------------------------------------------------------------

class TestMinHash:
    def test_identical_texts_jaccard_one(self):
        text = "동일한 텍스트 내용입니다"
        s1 = minhash_signature(text)
        s2 = minhash_signature(text)
        assert jaccard_estimate(s1, s2) == 1.0

    def test_different_texts_low_jaccard(self):
        s1 = minhash_signature("완전히 다른 첫 번째 문서 내용")
        s2 = minhash_signature("totally different second document here")
        assert jaccard_estimate(s1, s2) < 0.3

    def test_near_duplicate_high_jaccard(self):
        base = "오늘 날씨가 매우 맑고 화창합니다 산책하기 좋은 날입니다"
        near = "오늘 날씨가 매우 맑고 화창합니다 산책하기 좋은 날입니다 정말"
        s1 = minhash_signature(base)
        s2 = minhash_signature(near)
        assert jaccard_estimate(s1, s2) > 0.5

    def test_signature_length(self):
        sig = minhash_signature("테스트")
        assert len(sig) == NUM_HASHES

    def test_empty_text(self):
        sig = minhash_signature("")
        assert len(sig) == NUM_HASHES
        assert all(v == 0 for v in sig)

    def test_symmetric(self):
        s1 = minhash_signature("가나다라")
        s2 = minhash_signature("마바사아")
        assert jaccard_estimate(s1, s2) == jaccard_estimate(s2, s1)


# ---------------------------------------------------------------------------
# TestFilterByTier
# ---------------------------------------------------------------------------

class TestFilterByTier:
    def test_canonical_passes(self):
        f = TraceQualityFilter()
        r = _canonical_rec()
        kept, removed = f.filter_by_tier([r])
        assert len(kept) == 1
        assert removed == 0

    def test_archive_removed(self):
        f = TraceQualityFilter()
        r = _archive_rec()
        kept, removed = f.filter_by_tier([r])
        assert len(kept) == 0
        assert removed == 1

    def test_custom_tier_list(self):
        f = TraceQualityFilter(allowed_tiers=[PromotionTier.CANONICAL])
        canonical = _canonical_rec()
        candidate = _candidate_rec()
        kept, removed = f.filter_by_tier([canonical, candidate])
        assert len(kept) == 1
        assert kept[0].trace_id == canonical.trace_id

    def test_mixed_tiers(self):
        f = TraceQualityFilter()
        records = [
            _canonical_rec(scene_id="c1"),
            _candidate_rec(scene_id="c2"),
            _archive_rec(scene_id="c3"),
        ]
        kept, removed = f.filter_by_tier(records)
        assert len(kept) == 2
        assert removed == 1

    def test_empty_input(self):
        f = TraceQualityFilter()
        kept, removed = f.filter_by_tier([])
        assert kept == []
        assert removed == 0


# ---------------------------------------------------------------------------
# TestDeduplicate
# ---------------------------------------------------------------------------

class TestDeduplicate:
    def test_no_duplicates(self):
        f = TraceQualityFilter()
        records = [
            _canonical_rec(scene_id="a", render_text="완전히 다른 첫 번째 씬 내용입니다"),
            _canonical_rec(scene_id="b", render_text="totally different second scene here"),
        ]
        unique, stats = f.deduplicate(records)
        assert len(unique) == 2
        assert stats.removed_count == 0

    def test_exact_duplicates_removed(self):
        f = TraceQualityFilter(dedup_threshold=0.85)
        text = "동일한 텍스트 내용이 두 번 등장합니다 완전히 같은 내용입니다"
        records = [
            _canonical_rec(scene_id="x", render_text=text),
            _canonical_rec(scene_id="y", render_text=text),
        ]
        unique, stats = f.deduplicate(records)
        assert len(unique) == 1
        assert stats.removed_count == 1

    def test_dedup_stats_structure(self):
        f = TraceQualityFilter()
        records = [_canonical_rec(scene_id=f"s{i}") for i in range(3)]
        _, stats = f.deduplicate(records)
        assert isinstance(stats, DedupStats)
        assert stats.original_count == 3
        assert stats.kept_count + stats.removed_count == 3

    def test_dedup_stats_summary(self):
        f = TraceQualityFilter()
        records = [_canonical_rec(scene_id=f"r{i}") for i in range(2)]
        _, stats = f.deduplicate(records)
        summary = stats.summary()
        assert "dedup" in summary
        assert "threshold" in summary

    def test_removal_rate(self):
        f = TraceQualityFilter(dedup_threshold=0.85)
        text = "완전히 동일한 내용의 씬 텍스트입니다 아주 긴 내용"
        records = [_canonical_rec(scene_id=f"dup{i}", render_text=text) for i in range(4)]
        unique, stats = f.deduplicate(records)
        assert stats.removal_rate > 0


# ---------------------------------------------------------------------------
# TestStratifiedSplit
# ---------------------------------------------------------------------------

class TestStratifiedSplit:
    def test_ratio_sum_validation(self):
        with pytest.raises(ValueError):
            TraceQualityFilter(train_ratio=0.8, val_ratio=0.1, test_ratio=0.2)

    def test_split_covers_all_records(self):
        f = TraceQualityFilter()
        records = [_canonical_rec(scene_id=f"sc{i}", episode_no=i+1) for i in range(10)]
        result = f.stratified_split(records)
        assert result.total == 10

    def test_split_result_structure(self):
        f = TraceQualityFilter()
        records = [_canonical_rec(scene_id=f"sc{i}", episode_no=i+1) for i in range(9)]
        result = f.stratified_split(records)
        assert isinstance(result, SplitResult)
        assert isinstance(result.train, list)
        assert isinstance(result.val, list)
        assert isinstance(result.test, list)

    def test_split_ratios_approximate(self):
        f = TraceQualityFilter(train_ratio=0.8, val_ratio=0.1, test_ratio=0.1)
        records = [
            _canonical_rec(scene_id=f"sc{i}", episode_no=i+1, genre="drama")
            for i in range(30)
        ]
        result = f.stratified_split(records)
        # 허용 오차: ±15%
        train_ratio = len(result.train) / result.total
        assert 0.6 <= train_ratio <= 0.95

    def test_split_summary(self):
        f = TraceQualityFilter()
        records = [_canonical_rec(scene_id=f"sc{i}", episode_no=i+1) for i in range(6)]
        result = f.stratified_split(records)
        summary = result.summary()
        assert "total" in summary
        assert "counts" in summary
        assert "ratios" in summary

    def test_reproducible_with_seed(self):
        records = [
            _canonical_rec(scene_id=f"s{i}", episode_no=i+1) for i in range(12)
        ]
        f1 = TraceQualityFilter(random_seed=42)
        f2 = TraceQualityFilter(random_seed=42)
        r1 = f1.stratified_split(records)
        r2 = f2.stratified_split(records)
        assert [r.trace_id for r in r1.train] == [r.trace_id for r in r2.train]

    def test_stratified_by_genre(self):
        """여러 장르에서 레코드를 뽑아 각 split에 모든 장르 포함."""
        records = []
        genres = ["drama", "thriller", "romance"]
        for g in genres:
            for i in range(6):
                records.append(_rec(
                    genre=g,
                    scene_id=f"{g}_{i}",
                    episode_no=i+1,
                    render_text=f"{g} 장르 씬 {i} 내용입니다",
                ))
        f = TraceQualityFilter()
        result = f.stratified_split(records)
        train_genres = {r.seed_contract["genre"] for r in result.train}
        assert len(train_genres) >= 2  # 대부분의 장르 포함


# ---------------------------------------------------------------------------
# TestRunPipeline
# ---------------------------------------------------------------------------

class TestRunPipeline:
    def test_run_returns_filter_result(self):
        f = TraceQualityFilter()
        records = [_canonical_rec(scene_id=f"r{i}", episode_no=i+1) for i in range(5)]
        result = f.run(records)
        assert isinstance(result, FilterResult)

    def test_run_filters_archive(self):
        f = TraceQualityFilter()
        records = [
            _canonical_rec(scene_id="c1", episode_no=1),
            _archive_rec(scene_id="a1"),
        ]
        result = f.run(records)
        assert result.tier_filtered == 1

    def test_run_summary(self):
        f = TraceQualityFilter()
        records = [_canonical_rec(scene_id=f"r{i}", episode_no=i+1) for i in range(4)]
        result = f.run(records)
        s = result.summary()
        assert "tier_filtered" in s
        assert "dedup" in s
        assert "split" in s

    def test_run_total_records(self):
        f = TraceQualityFilter()
        records = [_canonical_rec(scene_id=f"r{i}", episode_no=i+1) for i in range(9)]
        result = f.run(records)
        assert result.split.total <= 9

    def test_run_with_pii_scrub(self):
        f = TraceQualityFilter()
        records = [
            _rec(
                render_text="씬 내용 010-1234-5678 포함",
                scene_id="pii01",
            )
        ]
        result = f.run(records, scrub_pii=True)
        # PII 있는 레코드 스크럽 확인
        assert result.pii_scrubbed >= 1
        # render_output에 원본 전화번호 없어야 함
        all_text = " ".join(
            v
            for r in result.split.train + result.split.val + result.split.test
            for v in r.render_output.values()
        )
        assert "010-1234-5678" not in all_text
