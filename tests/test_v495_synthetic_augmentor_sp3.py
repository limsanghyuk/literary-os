"""
tests/test_v495_synthetic_augmentor_sp3.py
V495: SyntheticAugmentorSP3 단위 테스트

대상:
  - AugmentedRecord — synthetic=True 플래그 (ADR-008), to_dict()
  - AugmentResultSP3 — total_count / success_rate / all_records() / summary()
  - SyntheticAugmentorSP3.augment() — 전략별, target_count, 라운드로빈
  - SyntheticAugmentorSP3.select_candidates() — min_quality 필터
  - 3종 전략 (paraphrase / back_translation / style_transfer)
  - 지원하지 않는 전략 ValueError
  - LLM 어댑터 주입 (Mock)
  - 빈 입력 처리
  - 결정적(seed) 동작
"""

import pytest
from unittest.mock import MagicMock

from literary_system.slm.synthetic_augmentor_sp3 import (
    SyntheticAugmentorSP3,
    AugmentedRecord,
    AugmentResultSP3,
    SUPPORTED_STRATEGIES,
)


# ─────────────────────────────────────────────────────────────────────
# Fixtures / Helpers
# ─────────────────────────────────────────────────────────────────────
def _records(count=5) -> list:
    return [
        {
            "id": f"rec_{i}",
            "text": f"드라마 씬 {i}: 주인공이 등장한다. 이야기가 시작된다. 감정이 복잡하다.",
            "quality_score": 0.8,
            "tier": "A",
        }
        for i in range(count)
    ]


def _augmentor(**kw) -> SyntheticAugmentorSP3:
    defaults = dict(seed=42)
    defaults.update(kw)
    return SyntheticAugmentorSP3(**defaults)


# ─────────────────────────────────────────────────────────────────────
# TestAugmentedRecord
# ─────────────────────────────────────────────────────────────────────
class TestAugmentedRecord:
    def _rec(self) -> AugmentedRecord:
        return AugmentedRecord(
            id="aug_001", text="합성 텍스트", source_id="rec_0",
            strategy="paraphrase",
        )

    def test_synthetic_flag_is_true(self):
        """ADR-008: 합성 데이터에 synthetic=True 의무."""
        rec = self._rec()
        assert rec.synthetic is True

    def test_default_tier_is_b(self):
        rec = self._rec()
        assert rec.tier == "B"

    def test_default_quality_score(self):
        rec = self._rec()
        assert 0.0 <= rec.quality_score <= 1.0

    def test_to_dict_contains_synthetic_true(self):
        d = self._rec().to_dict()
        assert d["synthetic"] is True

    def test_to_dict_contains_required_keys(self):
        d = self._rec().to_dict()
        for key in ("id", "text", "source_id", "strategy", "synthetic",
                    "quality_score", "tier"):
            assert key in d, f"Missing key: {key}"

    def test_to_dict_strategy(self):
        d = self._rec().to_dict()
        assert d["strategy"] == "paraphrase"


# ─────────────────────────────────────────────────────────────────────
# TestAugmentResultSP3
# ─────────────────────────────────────────────────────────────────────
class TestAugmentResultSP3:
    def _result(self, orig_count=3, aug_count=6) -> AugmentResultSP3:
        orig = _records(orig_count)
        augmented = [
            AugmentedRecord(id=f"aug_{i}", text=f"aug {i}", source_id="r0",
                            strategy="paraphrase")
            for i in range(aug_count)
        ]
        return AugmentResultSP3(
            original=orig,
            augmented=augmented,
            strategy_counts={"paraphrase": aug_count},
        )

    def test_total_count(self):
        result = self._result(3, 6)
        assert result.total_count == 9

    def test_success_rate(self):
        result = self._result(3, 6)
        assert abs(result.success_rate - 2.0) < 1e-9

    def test_all_records_length(self):
        result = self._result(3, 6)
        all_r = result.all_records()
        assert len(all_r) == 9

    def test_all_records_are_dicts(self):
        result = self._result(3, 6)
        for r in result.all_records():
            assert isinstance(r, dict)

    def test_summary_contains_counts(self):
        result = self._result(3, 6)
        s = result.summary()
        assert "3" in s   # 원본
        assert "6" in s   # 합성
        assert "9" in s   # 총

    def test_empty_original_success_rate_zero(self):
        result = AugmentResultSP3(original=[], augmented=[], strategy_counts={})
        assert result.success_rate == 0.0


# ─────────────────────────────────────────────────────────────────────
# TestSupportedStrategies
# ─────────────────────────────────────────────────────────────────────
class TestSupportedStrategies:
    def test_three_strategies_defined(self):
        assert len(SUPPORTED_STRATEGIES) == 3

    def test_paraphrase_in_strategies(self):
        assert "paraphrase" in SUPPORTED_STRATEGIES

    def test_back_translation_in_strategies(self):
        assert "back_translation" in SUPPORTED_STRATEGIES

    def test_style_transfer_in_strategies(self):
        assert "style_transfer" in SUPPORTED_STRATEGIES

    def test_unknown_strategy_raises(self):
        with pytest.raises(ValueError, match="지원하지 않는 전략"):
            SyntheticAugmentorSP3(strategies=["nonexistent"])


# ─────────────────────────────────────────────────────────────────────
# TestAugmentBasic
# ─────────────────────────────────────────────────────────────────────
class TestAugmentBasic:
    def test_augment_returns_augment_result(self):
        aug = _augmentor()
        result = aug.augment(_records(3))
        assert isinstance(result, AugmentResultSP3)

    def test_augment_empty_input_returns_empty(self):
        aug = _augmentor()
        result = aug.augment([])
        assert result.total_count == 0
        assert result.augmented == []
        assert result.original == []

    def test_augment_default_all_strategies(self):
        aug = _augmentor()
        records = _records(2)
        result = aug.augment(records)
        # 기본: 원본 × 전략 수 = 2 × 3 = 6
        assert len(result.augmented) == 6

    def test_augment_synthetic_flag_all_augmented(self):
        aug = _augmentor()
        result = aug.augment(_records(2))
        for rec in result.augmented:
            assert rec.synthetic is True

    def test_augment_source_id_linked(self):
        aug = _augmentor()
        records = [{"id": "orig_0", "text": "원본 텍스트", "quality_score": 0.8, "tier": "A"}]
        result = aug.augment(records)
        for rec in result.augmented:
            assert rec.source_id == "orig_0"

    def test_augment_all_records_includes_originals(self):
        aug = _augmentor()
        records = _records(3)
        result = aug.augment(records)
        all_r = result.all_records()
        # 원본 3개 + 합성 포함
        assert len(all_r) >= 3


# ─────────────────────────────────────────────────────────────────────
# TestAugmentSingleStrategy
# ─────────────────────────────────────────────────────────────────────
class TestAugmentSingleStrategy:
    @pytest.mark.parametrize("strategy", SUPPORTED_STRATEGIES)
    def test_single_strategy_generates_correct_count(self, strategy):
        aug = _augmentor()
        records = _records(4)
        result = aug.augment(records, strategy=strategy)
        # strategy 지정 시: 원본 × 1
        assert len(result.augmented) == 4

    @pytest.mark.parametrize("strategy", SUPPORTED_STRATEGIES)
    def test_single_strategy_label_correct(self, strategy):
        aug = _augmentor()
        result = aug.augment(_records(2), strategy=strategy)
        for rec in result.augmented:
            assert rec.strategy == strategy

    def test_paraphrase_changes_text(self):
        aug = _augmentor(seed=42)
        records = [{"id": "r0", "text": "주인공이 등장한다 이야기 갈등 사랑", "quality_score": 0.8, "tier": "A"}]
        result = aug.augment(records, strategy="paraphrase")
        # 반드시 변형되지 않을 수도 있지만 반환값은 문자열이어야 함
        assert isinstance(result.augmented[0].text, str)
        assert len(result.augmented[0].text) > 0

    def test_back_translation_returns_string(self):
        aug = _augmentor()
        records = [{"id": "r0", "text": "주인공이 등장한다. 이야기가 시작됩니다. 감정이 복잡하다.", "quality_score": 0.8, "tier": "A"}]
        result = aug.augment(records, strategy="back_translation")
        assert isinstance(result.augmented[0].text, str)

    def test_style_transfer_returns_string(self):
        aug = _augmentor()
        records = [{"id": "r0", "text": "이야기가 시작하였다. 주인공이 하겠습니다.", "quality_score": 0.8, "tier": "A"}]
        result = aug.augment(records, strategy="style_transfer")
        assert isinstance(result.augmented[0].text, str)


# ─────────────────────────────────────────────────────────────────────
# TestAugmentTargetCount
# ─────────────────────────────────────────────────────────────────────
class TestAugmentTargetCount:
    def test_target_count_generates_correct_augmented_count(self):
        aug = _augmentor()
        records = _records(5)
        result = aug.augment(records, target_count=15)
        # augmented = target_count - len(records) = 10
        assert len(result.augmented) == 10

    def test_target_count_equal_to_original_no_augmentation(self):
        aug = _augmentor()
        records = _records(5)
        result = aug.augment(records, target_count=5)
        assert len(result.augmented) == 0

    def test_target_count_less_than_original_no_augmentation(self):
        aug = _augmentor()
        records = _records(5)
        result = aug.augment(records, target_count=3)
        assert len(result.augmented) == 0

    def test_target_count_with_single_strategy(self):
        aug = _augmentor()
        records = _records(3)
        result = aug.augment(records, strategy="paraphrase", target_count=10)
        assert len(result.augmented) == 7

    def test_target_count_all_synthetic_flagged(self):
        aug = _augmentor()
        result = aug.augment(_records(3), target_count=10)
        for rec in result.augmented:
            assert rec.synthetic is True

    def test_strategy_counts_populated(self):
        aug = _augmentor()
        result = aug.augment(_records(3), target_count=10)
        total = sum(result.strategy_counts.values())
        assert total == len(result.augmented)


# ─────────────────────────────────────────────────────────────────────
# TestSelectCandidates
# ─────────────────────────────────────────────────────────────────────
class TestSelectCandidates:
    def _records_with_quality(self) -> list:
        return [
            {"id": "r0", "text": "텍스트 A", "quality_score": 0.9, "tier": "A"},
            {"id": "r1", "text": "텍스트 B", "quality_score": 0.5, "tier": "B"},
            {"id": "r2", "text": "텍스트 C", "quality_score": 0.3, "tier": "C"},
            {"id": "r3", "text": "텍스트 D", "quality_score": 0.7, "tier": "A"},
        ]

    def test_select_candidates_min_quality_filter(self):
        aug = _augmentor()
        candidates = aug.select_candidates(self._records_with_quality(), min_quality=0.6)
        # 0.9, 0.7 만 통과
        assert len(candidates) == 2

    def test_select_candidates_max_count_limit(self):
        aug = _augmentor()
        candidates = aug.select_candidates(self._records_with_quality(),
                                            min_quality=0.0, max_count=2)
        assert len(candidates) <= 2

    def test_select_candidates_all_pass_low_threshold(self):
        aug = _augmentor()
        candidates = aug.select_candidates(self._records_with_quality(), min_quality=0.0)
        assert len(candidates) == 4

    def test_select_candidates_none_pass_high_threshold(self):
        aug = _augmentor()
        candidates = aug.select_candidates(self._records_with_quality(), min_quality=1.0)
        assert len(candidates) == 0

    def test_select_candidates_empty_input(self):
        aug = _augmentor()
        candidates = aug.select_candidates([], min_quality=0.5)
        assert candidates == []


# ─────────────────────────────────────────────────────────────────────
# TestLLMAdapterInjection
# ─────────────────────────────────────────────────────────────────────
class TestLLMAdapterInjection:
    def test_llm_adapter_called_on_augment(self):
        mock_adapter = MagicMock()
        mock_resp = MagicMock()
        mock_resp.text = "LLM 생성 텍스트"
        mock_adapter.call.return_value = mock_resp

        aug = SyntheticAugmentorSP3(strategies=["paraphrase"], llm_adapter=mock_adapter, seed=42)
        records = [{"id": "r0", "text": "원본", "quality_score": 0.8, "tier": "A"}]
        result = aug.augment(records, strategy="paraphrase")

        mock_adapter.call.assert_called_once()
        assert result.augmented[0].text == "LLM 생성 텍스트"

    def test_llm_adapter_fallback_on_exception(self):
        mock_adapter = MagicMock()
        mock_adapter.call.side_effect = RuntimeError("LLM 오류")

        aug = SyntheticAugmentorSP3(strategies=["paraphrase"], llm_adapter=mock_adapter, seed=42)
        records = [{"id": "r0", "text": "원본 텍스트 주인공 이야기", "quality_score": 0.8, "tier": "A"}]
        # 예외 시 Mock으로 폴백 — 오류 없이 완료되어야 함
        result = aug.augment(records, strategy="paraphrase")
        assert isinstance(result.augmented[0].text, str)
        assert len(result.augmented[0].text) > 0


# ─────────────────────────────────────────────────────────────────────
# TestDeterminism
# ─────────────────────────────────────────────────────────────────────
class TestDeterminism:
    def test_same_seed_produces_same_output(self):
        records = _records(3)
        aug1 = SyntheticAugmentorSP3(strategies=["paraphrase"], seed=123)
        aug2 = SyntheticAugmentorSP3(strategies=["paraphrase"], seed=123)
        result1 = aug1.augment(records, strategy="paraphrase")
        result2 = aug2.augment(records, strategy="paraphrase")
        texts1 = [r.text for r in result1.augmented]
        texts2 = [r.text for r in result2.augmented]
        assert texts1 == texts2

    def test_supported_strategies_property(self):
        aug = _augmentor()
        assert aug.supported_strategies == SUPPORTED_STRATEGIES
