"""
V599 — PreTrainSafety + FineTuneEvalPipeline + LongContextStrategy 단위 테스트 (12 TC)

TC-A1~A4: PreTrainSafety 4축 검사
TC-B1~B4: FineTuneEvalPipeline 5축 평가 + Krippendorff α
TC-C1~C3: LongContextStrategy 청킹
TC-D1:    batch 처리 + filter_safe
"""
from __future__ import annotations

import math

import pytest

from literary_system.finetune.pre_train_safety import (
    PreTrainSafety,
    SafetyAxis,
    SafetyResult,
    _check_pii,
    _check_toxic,
    _check_copyright,
    _check_quality,
    QUALITY_MIN_CHARS,
)
from literary_system.finetune.finetune_eval_pipeline import (
    FineTuneEvalPipeline,
    compute_bertscore_f1,
    compute_bleu4,
    compute_style_score,
    compute_krippendorff_alpha,
    THRESHOLD_BERTSCORE_F1,
    THRESHOLD_BLEU,
    THRESHOLD_KRIPPENDORFF_ALPHA,
)
from literary_system.finetune.long_context_strategy import (
    LongContextStrategy,
    CHUNK_SIZE_TOKENS,
    OVERLAP_TOKENS,
    CHARS_PER_TOKEN,
)


# ===========================================================================
# TC-A: PreTrainSafety
# ===========================================================================

class TestPreTrainSafety:
    """TC-A1~A4: 4축 안전성 검사."""

    def test_a1_clean_text_passes_all_axes(self):
        """TC-A1: 안전한 드라마 씬 텍스트는 4축 전부 PASS해야 한다."""
        text = (
            "주인공이 창문 너머로 빗줄기를 바라보며 깊은 한숨을 내쉬었다. "
            "그의 눈 속에는 오래된 슬픔이 고여 있었다. "
            "오늘이 지나면 모든 것이 달라지리라는 예감이 들었다. "
            "그는 천천히 문 쪽으로 걸어갔다."
        )
        checker = PreTrainSafety()
        result  = checker.check(text)

        assert result.safe is True
        assert result.failed_axes == []
        assert result.text_length == len(text)

    def test_a2_pii_text_fails(self):
        """TC-A2: 주민등록번호 포함 텍스트는 PII 축 FAIL해야 한다."""
        text = "등록번호: 900101-1234567 이고 연락처는 010-1234-5678입니다."
        result = _check_pii(text)

        assert result.axis == SafetyAxis.PII
        assert result.passed is False
        assert result.score == 0.0
        assert any("rrn" in d or "phone" in d for d in result.details)

    def test_a3_toxic_text_fails(self):
        """TC-A3: 혐오 키워드 포함 텍스트는 Toxic 축 FAIL해야 한다."""
        text = "자살 방법을 검색하며 절망에 빠진 장면이 있다."
        result = _check_toxic(text)

        assert result.axis == SafetyAxis.TOXIC
        assert result.passed is False
        assert result.score == 0.0

    def test_a4_quality_too_short_fails(self):
        """TC-A4: 50자 미만 텍스트는 Quality 축 FAIL해야 한다."""
        short_text = "짧은 텍스트."
        assert len(short_text) < QUALITY_MIN_CHARS

        result = _check_quality(short_text)

        assert result.axis == SafetyAxis.QUALITY
        assert result.passed is False
        assert any("too_short" in d for d in result.details)

    def test_a4b_repetitive_text_fails_quality(self):
        """TC-A4b: 반복 비율 초과 텍스트는 Quality 축 FAIL해야 한다."""
        # 동일 구절 반복
        repeated = ("가나다라 마바사아 " * 20).strip()
        result = _check_quality(repeated)

        assert result.axis == SafetyAxis.QUALITY
        assert result.passed is False
        assert any("repeat_ratio" in d for d in result.details)

    def test_a_integrated_pii_in_batch(self):
        """TC-A(통합): 배치 처리 시 PII 포함 텍스트가 필터링되어야 한다."""
        clean = (
            "두 사람은 서로를 바라보며 오랜 침묵을 나눴다. "
            "말보다 더 많은 것을 전하는 눈빛이었다. "
            "그 순간만은 세상의 모든 소음이 멎은 것 같았다."
        )
        pii   = "주민번호 900101-1234567 포함 텍스트입니다."
        checker = PreTrainSafety()

        safe_texts, results = checker.filter_safe([clean, pii])

        assert len(safe_texts) == 1
        assert safe_texts[0] == clean
        summary = checker.summary(results)
        assert summary["safe_count"] == 1
        assert summary["fail_by_axis"]["pii"] == 1


# ===========================================================================
# TC-B: FineTuneEvalPipeline
# ===========================================================================

class TestFineTuneEvalPipeline:
    """TC-B1~B4: 5축 평가 + Krippendorff α."""

    def _drama_text(self, length: int = 200) -> str:
        """테스트용 드라마 씬 텍스트 생성."""
        base = (
            "주인공이 방 안으로 들어서며 조용히 문을 닫았다. "
            "그의 시선이 창밖으로 향하며 갈등의 감정이 고조되었다. "
            "대사: '이제 돌아갈 수 없어.' 인물의 반전이 드러나는 씬이었다."
        )
        result = (base * (length // len(base) + 2))[:length]
        return result

    def test_b1_identical_texts_high_scores(self):
        """TC-B1: 동일 텍스트 hypothesis=reference이면 BERTScore ≈ 1.0, BLEU ≈ 1.0이어야 한다."""
        text = self._drama_text(300)
        bs   = compute_bertscore_f1(text, text)
        bleu = compute_bleu4(text, text)

        assert bs   >= 0.99
        assert bleu >= 0.99

    def test_b2_different_texts_lower_scores(self):
        """TC-B2: 전혀 다른 텍스트는 BERTScore < 0.85, BLEU < 0.30이어야 한다."""
        hyp = "안녕하세요 반갑습니다 오늘 날씨가 참 좋네요."
        ref = "양자 컴퓨터 알고리즘의 오류 보정 방식을 설명한다."

        bs   = compute_bertscore_f1(hyp, ref)
        bleu = compute_bleu4(hyp, ref)

        assert bs   < THRESHOLD_BERTSCORE_F1
        assert bleu < THRESHOLD_BLEU

    def test_b3_eval_pipeline_passes_similar(self):
        """TC-B3: 유사 텍스트 쌍은 EvalPipeline PASS해야 한다."""
        ref  = self._drama_text(300)
        # hypothesis = reference 와 동일 (완벽한 재현)
        hyp  = ref

        pipeline = FineTuneEvalPipeline()
        result   = pipeline.evaluate(hyp, ref)

        # BERTScore, BLEU, Equiv는 동일 텍스트이므로 PASS
        axis_map = {r.axis: r for r in result.axis_results}
        assert axis_map["bertscore_f1"].passed is True
        assert axis_map["bleu4"].passed         is True
        assert axis_map["equiv_rate"].passed     is True

    def test_b4_krippendorff_perfect_agreement(self):
        """TC-B4: 모든 어노테이터가 동일 점수 부여 시 α = 1.0이어야 한다."""
        # 3명 어노테이터, 5개 아이템, 모두 동일 점수
        ratings = [
            [4.0, 3.5, 4.5, 4.0, 5.0],
            [4.0, 3.5, 4.5, 4.0, 5.0],
            [4.0, 3.5, 4.5, 4.0, 5.0],
        ]
        alpha = compute_krippendorff_alpha(ratings)
        assert alpha == 1.0

    def test_b4b_krippendorff_disagreement_low(self):
        """TC-B4b: 어노테이터 불일치 시 α < 0.70이어야 한다."""
        # 완전 불일치: 홀수 아이템은 1.0, 짝수는 5.0 (반대 패턴)
        ratings = [
            [1.0, 5.0, 1.0, 5.0, 1.0],
            [5.0, 1.0, 5.0, 1.0, 5.0],
        ]
        alpha = compute_krippendorff_alpha(ratings)
        assert alpha < THRESHOLD_KRIPPENDORFF_ALPHA

    def test_b_aggregate_stats(self):
        """TC-B(통합): aggregate() 결과가 올바른 통계를 반환해야 한다."""
        ref = self._drama_text(300)
        pipeline = FineTuneEvalPipeline()
        pairs = [(ref, ref), (ref, ref)]  # 동일 쌍 2개

        results   = pipeline.evaluate_batch(pairs)
        aggregate = pipeline.aggregate(results)

        assert aggregate["total"] == 2
        assert "pass_rate" in aggregate
        assert "axis_means" in aggregate


# ===========================================================================
# TC-C: LongContextStrategy
# ===========================================================================

class TestLongContextStrategy:
    """TC-C1~C3: 청킹 전략."""

    def test_c1_short_text_single_chunk(self):
        """TC-C1: 청크 크기 미만 텍스트는 청크 1개여야 한다."""
        strategy = LongContextStrategy()
        text     = "가나다라 마바사아 " * 100   # ≈ 1000 chars, 훨씬 작음
        result   = strategy.chunk(text)

        assert result.chunk_count == 1
        assert result.chunks[0].start_char == 0
        assert result.chunks[0].end_char   == len(text)

    def test_c2_long_text_multiple_chunks(self):
        """TC-C2: 청크 크기 초과 텍스트는 2개 이상 청크로 분할되어야 한다."""
        strategy = LongContextStrategy()
        # CHUNK_SIZE_CHARS + 약간 = 반드시 2청크 이상
        chunk_chars = strategy.chunk_size_chars
        text = "드라마 씬 텍스트 내용입니다. " * (chunk_chars // 20 + 50)
        result = strategy.chunk(text)

        assert result.chunk_count >= 2
        # 각 청크의 token_count 검증
        for chunk in result.chunks:
            assert chunk.token_count > 0

    def test_c3_nkg_context_injection(self):
        """TC-C3: nkg_contexts 제공 시 청크에 NKG 컨텍스트가 주입되어야 한다."""
        strategy    = LongContextStrategy()
        text        = "드라마 씬 텍스트입니다. " * 100
        nkg_contexts = ["인물 A: 갈등 관계. 복선: 3화 반전."]

        result = strategy.chunk(text, nkg_contexts=nkg_contexts)

        # 모든 청크에 NKG 컨텍스트가 있어야 함
        for chunk in result.chunks:
            assert chunk.nkg_context == nkg_contexts[0]
            assert "[NKG_CONTEXT]" in chunk.prompt_text

    def test_c3b_overlap_configuration(self):
        """TC-C3b: overlap_tokens >= chunk_size_tokens이면 ValueError가 발생해야 한다."""
        with pytest.raises(ValueError, match="overlap_tokens"):
            LongContextStrategy(chunk_size_tokens=1000, overlap_tokens=1000)

    def test_c_summary_stats(self):
        """TC-C(통합): summary()가 올바른 통계를 반환해야 한다."""
        strategy = LongContextStrategy()
        text     = "내용 " * 500  # 작은 텍스트
        result   = strategy.chunk(text)
        summary  = strategy.summary(result)

        assert "chunk_count" in summary
        assert "total_chars"  in summary
        assert summary["chunk_count"] == result.chunk_count
        assert summary["chunk_size_tokens_config"] == CHUNK_SIZE_TOKENS
        assert summary["overlap_tokens_config"]    == OVERLAP_TOKENS
