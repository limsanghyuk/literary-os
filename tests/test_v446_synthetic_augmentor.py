"""
V446 tests -- SyntheticAugmentor
"""
import pytest
from literary_system.slm.synthetic_augmentor import (
    SyntheticAugmentor, AugmentLog, AugmentResult,
    _mock_self_critique, _mock_paraphrase, _mock_style_transfer,
)
from literary_system.trace.trace_dataset_store import (
    TraceDatasetStore, TraceRecord, PromotionTier, make_trace_record,
)
import tempfile


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

_BEFORE = {"SP": 0.4, "RU": 0.3, "ET": 0.2}
_AFTER  = {"SP": 0.5, "RU": 0.4, "ET": 0.3}


def _rec(
    user_prompt="씬 내용",
    render_text="씬 본문 텍스트",
    L_total=0.10,
    scene_id="sc01",
    episode_no=1,
) -> TraceRecord:
    return make_trace_record(
        project_id="test_proj",
        episode_no=episode_no,
        scene_id=scene_id,
        seed_contract={"genre": "drama", "user_prompt": user_prompt},
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


def _candidate_records(n=3):
    """L_total=0.10 → threshold 이하 (CANONICAL)."""
    return [
        _rec(scene_id=f"sc{i:02d}", episode_no=i+1, L_total=0.10)
        for i in range(n)
    ]


def _high_loss_records(n=2):
    """L_total=0.50 → threshold 초과, 증강 제외."""
    return [
        _rec(scene_id=f"hl{i:02d}", episode_no=i+10, L_total=0.50)
        for i in range(n)
    ]


# ---------------------------------------------------------------------------
# TestMockStrategies
# ---------------------------------------------------------------------------

class TestMockStrategies:
    def test_self_critique_appends_tag(self):
        result = _mock_self_critique("그는 슬펐다")
        assert "[증강됨]" in result

    def test_self_critique_replaces_emotion(self):
        result = _mock_self_critique("그는 슬펐다")
        assert "손이 떨렸다" in result

    def test_paraphrase_appends_tag(self):
        result = _mock_paraphrase("그는 걸었다")
        assert "[패러프레이즈]" in result

    def test_paraphrase_replaces_pronoun(self):
        result = _mock_paraphrase("그는 걸었다")
        assert "남자는" in result

    def test_style_transfer_wraps(self):
        result = _mock_style_transfer("씬 내용")
        assert result.startswith("【")
        assert result.endswith("】")


# ---------------------------------------------------------------------------
# TestSyntheticAugmentorInit
# ---------------------------------------------------------------------------

class TestSyntheticAugmentorInit:
    def test_default_strategy(self):
        aug = SyntheticAugmentor()
        assert aug.strategy == "self_critique"

    def test_invalid_strategy_raises(self):
        with pytest.raises(ValueError):
            SyntheticAugmentor(strategy="unknown_strategy")

    def test_custom_threshold(self):
        aug = SyntheticAugmentor(threshold=0.20)
        assert aug.threshold == 0.20

    def test_custom_augment_fn(self):
        fn = lambda text: text + " [custom]"
        aug = SyntheticAugmentor(augment_fn=fn)
        assert aug.augment_fn is fn

    def test_supported_strategies_set(self):
        assert "self_critique" in SyntheticAugmentor.SUPPORTED_STRATEGIES
        assert "paraphrase" in SyntheticAugmentor.SUPPORTED_STRATEGIES
        assert "style_transfer" in SyntheticAugmentor.SUPPORTED_STRATEGIES


# ---------------------------------------------------------------------------
# TestSelectCandidates
# ---------------------------------------------------------------------------

class TestSelectCandidates:
    def test_selects_low_loss(self):
        aug = SyntheticAugmentor(threshold=0.12)
        records = _candidate_records(3) + _high_loss_records(2)
        candidates = aug.select_candidates(records)
        assert len(candidates) == 3

    def test_excludes_high_loss(self):
        aug = SyntheticAugmentor(threshold=0.12)
        records = _high_loss_records(3)
        candidates = aug.select_candidates(records)
        assert len(candidates) == 0

    def test_boundary_included(self):
        aug = SyntheticAugmentor(threshold=0.12)
        rec = _rec(L_total=0.12)
        candidates = aug.select_candidates([rec])
        assert len(candidates) == 1

    def test_boundary_excluded(self):
        aug = SyntheticAugmentor(threshold=0.12)
        rec = _rec(L_total=0.13)
        candidates = aug.select_candidates([rec])
        assert len(candidates) == 0

    def test_empty_input(self):
        aug = SyntheticAugmentor()
        assert aug.select_candidates([]) == []


# ---------------------------------------------------------------------------
# TestAugment
# ---------------------------------------------------------------------------

class TestAugment:
    def test_augment_returns_result(self):
        aug = SyntheticAugmentor()
        records = _candidate_records(2)
        result = aug.augment(records)
        assert isinstance(result, AugmentResult)

    def test_augment_count_matches(self):
        aug = SyntheticAugmentor()
        records = _candidate_records(3)
        result = aug.augment(records)
        assert result.augmented_count == 3
        assert result.source_count == 3

    def test_high_loss_excluded(self):
        aug = SyntheticAugmentor(threshold=0.12)
        records = _high_loss_records(3)
        result = aug.augment(records)
        assert result.augmented_count == 0
        assert result.source_count == 0

    def test_augmented_records_are_candidate_tier(self):
        aug = SyntheticAugmentor()
        records = _candidate_records(2)
        result = aug.augment(records)
        for rec in result.augmented_records:
            assert rec.promotion == PromotionTier.CANDIDATE

    def test_original_unchanged(self):
        aug = SyntheticAugmentor()
        orig = _rec(render_text="원본 씬 텍스트")
        result = aug.augment([orig])
        # Original render_output unchanged
        assert list(orig.render_output.values())[0] == "원본 씬 텍스트"

    def test_augmented_trace_id_differs(self):
        aug = SyntheticAugmentor()
        orig = _rec()
        result = aug.augment([orig])
        assert result.augmented_records[0].trace_id != orig.trace_id

    def test_augmented_trace_id_prefix(self):
        aug = SyntheticAugmentor()
        records = _candidate_records(1)
        result = aug.augment(records)
        assert result.augmented_records[0].trace_id.startswith("aug_")

    def test_quality_improves(self):
        aug = SyntheticAugmentor()
        orig = _rec(L_total=0.10)
        result = aug.augment([orig])
        aug_rec = result.augmented_records[0]
        assert aug_rec.loss_report["L_total"] <= orig.loss_report["L_total"]

    def test_success_rate_all_pass(self):
        aug = SyntheticAugmentor()
        records = _candidate_records(4)
        result = aug.augment(records)
        assert result.success_rate == 1.0

    def test_strategy_override(self):
        aug = SyntheticAugmentor(strategy="self_critique")
        records = _candidate_records(1)
        result = aug.augment(records, strategy="paraphrase")
        assert result.strategy == "paraphrase"
        text = list(result.augmented_records[0].render_output.values())[0]
        assert "[패러프레이즈]" in text

    def test_style_transfer_strategy(self):
        aug = SyntheticAugmentor(strategy="style_transfer")
        records = _candidate_records(1)
        result = aug.augment(records)
        text = list(result.augmented_records[0].render_output.values())[0]
        assert "【" in text

    def test_custom_fn_used(self):
        custom_fn = lambda t: t + " [custom_aug]"
        aug = SyntheticAugmentor(augment_fn=custom_fn)
        records = _candidate_records(1)
        result = aug.augment(records)
        text = list(result.augmented_records[0].render_output.values())[0]
        assert "[custom_aug]" in text


# ---------------------------------------------------------------------------
# TestAugmentLogs
# ---------------------------------------------------------------------------

class TestAugmentLogs:
    def test_logs_created(self):
        aug = SyntheticAugmentor()
        records = _candidate_records(2)
        result = aug.augment(records)
        assert len(result.logs) == 2

    def test_log_fields(self):
        aug = SyntheticAugmentor()
        records = _candidate_records(1)
        result = aug.augment(records)
        log = result.logs[0]
        assert isinstance(log, AugmentLog)
        assert log.success is True
        assert log.strategy == "self_critique"
        assert log.quality_before >= 0
        assert log.quality_after <= log.quality_before

    def test_all_logs_accumulate(self):
        aug = SyntheticAugmentor()
        aug.augment(_candidate_records(2))
        aug.augment(_candidate_records(1))
        assert len(aug.all_logs()) == 3

    def test_all_logs_returns_copy(self):
        aug = SyntheticAugmentor()
        aug.augment(_candidate_records(1))
        logs1 = aug.all_logs()
        logs2 = aug.all_logs()
        assert logs1 is not logs2

    def test_log_to_dict(self):
        aug = SyntheticAugmentor()
        records = _candidate_records(1)
        result = aug.augment(records)
        d = result.logs[0].to_dict()
        assert "aug_id" in d
        assert "source_trace_id" in d
        assert "strategy" in d
        assert "success" in d


# ---------------------------------------------------------------------------
# TestAugmentStats
# ---------------------------------------------------------------------------

class TestAugmentStats:
    def test_stats_keys(self):
        aug = SyntheticAugmentor()
        aug.augment(_candidate_records(2))
        s = aug.stats()
        assert "total_augmented" in s
        assert "total_failed" in s
        assert "strategies_used" in s
        assert "avg_quality_improvement" in s

    def test_stats_counts(self):
        aug = SyntheticAugmentor()
        aug.augment(_candidate_records(3))
        s = aug.stats()
        assert s["total_augmented"] == 3
        assert s["total_failed"] == 0

    def test_strategies_used(self):
        aug = SyntheticAugmentor(strategy="paraphrase")
        aug.augment(_candidate_records(1))
        s = aug.stats()
        assert "paraphrase" in s["strategies_used"]


# ---------------------------------------------------------------------------
# TestAugmentResultSummary
# ---------------------------------------------------------------------------

class TestAugmentResultSummary:
    def test_summary_keys(self):
        aug = SyntheticAugmentor()
        result = aug.augment(_candidate_records(2))
        s = result.summary()
        assert "source_count" in s
        assert "augmented_count" in s
        assert "success_rate" in s
        assert "strategy" in s

    def test_summary_values(self):
        aug = SyntheticAugmentor()
        result = aug.augment(_candidate_records(3))
        s = result.summary()
        assert s["source_count"] == 3
        assert s["augmented_count"] == 3
        assert s["success_rate"] == 1.0

    def test_empty_augment_summary(self):
        aug = SyntheticAugmentor(threshold=0.12)
        result = aug.augment(_high_loss_records(2))
        s = result.summary()
        assert s["source_count"] == 0
        assert s["augmented_count"] == 0
