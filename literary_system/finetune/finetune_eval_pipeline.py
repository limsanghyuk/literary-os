"""
SP-B.1 (V599) — FineTuneEvalPipeline: 파인튜닝 평가 5축 파이프라인

Phase B 본안 보강 B-M-07 / B-M-08:

  Axis-1 BERTScore F1  ≥ 0.85   (n-gram 기반 근사, LLM-0 준수)
  Axis-2 LLM-judge     ≥ 4.0    (0~5 스케일, 스텁 구현 — 실 운영 시 LOSConstitution 연동)
  Axis-3 Style         ≥ 0.80   (drse + prose 스타일 일관성)
  Axis-4 BLEU floor    ≥ 0.30   (smoothing BLEU-4)
  Axis-5 Equivalence   pass_rate ≥ 0.95 (EquivalenceTester 5축)

  Krippendorff α 계산 (B-M-08): 인간 어노테이터 inter-annotator agreement
    - 분기별 1회 + 인간 5명 월 1회 100 샘플 calibration

  전축 PASS → EvalResult.passed = True
  하나라도 FAIL → passed = False

LLM-0 원칙: 외부 LLM API 직접 호출 없음. 모든 지표 경량 근사 구현.
ADR-059 참조.
"""
from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 임계값 상수 (B-M-07)
# ---------------------------------------------------------------------------

THRESHOLD_BERTSCORE_F1: float  = 0.85
THRESHOLD_LLM_JUDGE:    float  = 4.0
THRESHOLD_STYLE:        float  = 0.80
THRESHOLD_BLEU:         float  = 0.30
THRESHOLD_EQUIV_PASS_RATE: float = 0.95

# Krippendorff α 임계값 (B-M-08)
THRESHOLD_KRIPPENDORFF_ALPHA: float = 0.70


# ---------------------------------------------------------------------------
# 경량 BERTScore 근사 (Axis-1)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """간이 토크나이저: 공백·구두점 분리."""
    return re.findall(r"[\w가-힣]+", text.lower())


def _precision_recall_f1(
    hyp_tokens: List[str],
    ref_tokens: List[str],
) -> Tuple[float, float, float]:
    """
    n-gram 겹침 기반 BERTScore 근사.
    실제 BERTScore (bert-score 라이브러리) 대신 LLM-0 준수를 위해
    unigram + bigram 가중 겹침으로 근사 계산.
    """
    if not hyp_tokens or not ref_tokens:
        return 0.0, 0.0, 0.0

    hyp_cnt = Counter(hyp_tokens)
    ref_cnt = Counter(ref_tokens)

    # Precision
    overlap_p = sum(min(hyp_cnt[t], ref_cnt[t]) for t in hyp_cnt)
    precision  = overlap_p / max(len(hyp_tokens), 1)

    # Recall
    overlap_r = sum(min(ref_cnt[t], hyp_cnt[t]) for t in ref_cnt)
    recall    = overlap_r / max(len(ref_tokens), 1)

    # F1
    if precision + recall == 0:
        return 0.0, 0.0, 0.0
    f1 = 2 * precision * recall / (precision + recall)
    return round(precision, 4), round(recall, 4), round(f1, 4)


def compute_bertscore_f1(hypothesis: str, reference: str) -> float:
    """
    경량 BERTScore F1 근사 계산.

    Returns:
        0.0 ~ 1.0 F1 점수
    """
    hyp_tok = _tokenize(hypothesis)
    ref_tok = _tokenize(reference)
    _, _, f1 = _precision_recall_f1(hyp_tok, ref_tok)
    return f1


# ---------------------------------------------------------------------------
# BLEU-4 (Axis-4)
# ---------------------------------------------------------------------------

def _ngram_counts(tokens: List[str], n: int) -> Counter:
    return Counter(tuple(tokens[i: i + n]) for i in range(len(tokens) - n + 1))


def compute_bleu4(hypothesis: str, reference: str) -> float:
    """
    BLEU-4 with smoothing (Lin & Och 2004 방식 근사).

    Returns:
        0.0 ~ 1.0 BLEU 점수
    """
    hyp_tok = _tokenize(hypothesis)
    ref_tok = _tokenize(reference)

    if not hyp_tok or not ref_tok:
        return 0.0

    log_sum = 0.0
    for n in range(1, 5):
        if len(hyp_tok) < n:
            log_sum += math.log(1e-10)
            continue
        hyp_cnt = _ngram_counts(hyp_tok, n)
        ref_cnt = _ngram_counts(ref_tok, n)
        clipped = sum(min(c, ref_cnt[ng]) for ng, c in hyp_cnt.items())
        total   = max(sum(hyp_cnt.values()), 1)
        # Add-1 smoothing
        precision_n = (clipped + 1) / (total + 1)
        log_sum += math.log(precision_n)

    # Brevity penalty
    bp = 1.0 if len(hyp_tok) >= len(ref_tok) else math.exp(
        1 - len(ref_tok) / max(len(hyp_tok), 1)
    )
    bleu = bp * math.exp(log_sum / 4)
    return round(min(bleu, 1.0), 4)


# ---------------------------------------------------------------------------
# LLM-judge 스텁 (Axis-2)
# ---------------------------------------------------------------------------

def _stub_llm_judge(text: str) -> float:
    """
    LLM-judge 스텁 (LLM-0 준수용).

    실 운영 시 → LOSConstitution.score_scene() 연동 예정 (V605+).
    현재는 텍스트 길이·다양성·핵심 드라마 키워드로 4.0 이상 달성 여부 근사.

    Returns:
        0.0 ~ 5.0 점수
    """
    tokens = _tokenize(text)
    if len(tokens) < 20:
        return 2.0

    # 다양성 점수 (unique / total)
    diversity = len(set(tokens)) / max(len(tokens), 1)

    # 드라마 관련 키워드 보너스
    drama_kws = ["씬", "대사", "감정", "갈등", "반전", "복선", "대화", "인물", "장면", "행동"]
    kw_hits = sum(1 for kw in drama_kws if kw in text)

    base  = 3.0
    bonus = min(diversity * 1.5 + kw_hits * 0.15, 2.0)
    score = min(base + bonus, 5.0)
    return round(score, 2)


# ---------------------------------------------------------------------------
# Style 점수 근사 (Axis-3)
# ---------------------------------------------------------------------------

def compute_style_score(hypothesis: str, reference: str) -> float:
    """
    스타일 일관성 점수 근사.

    문장 길이 분포 + 어휘 다양성 차이 기반.

    Returns:
        0.0 ~ 1.0
    """
    def _sent_lengths(t: str) -> List[int]:
        sents = re.split(r"[.!?。！？\n]+", t)
        return [len(s.split()) for s in sents if s.strip()]

    hyp_lens = _sent_lengths(hypothesis)
    ref_lens  = _sent_lengths(reference)

    if not hyp_lens or not ref_lens:
        return 0.5

    hyp_mean = sum(hyp_lens) / len(hyp_lens)
    ref_mean  = sum(ref_lens)  / len(ref_lens)

    len_sim = 1.0 - abs(hyp_mean - ref_mean) / max(ref_mean, 1.0)
    len_sim = max(0.0, min(1.0, len_sim))

    # 어휘 다양성 (TTR)
    hyp_ttr = len(set(_tokenize(hypothesis))) / max(len(_tokenize(hypothesis)), 1)
    ref_ttr  = len(set(_tokenize(reference)))  / max(len(_tokenize(reference)),  1)
    ttr_sim  = 1.0 - abs(hyp_ttr - ref_ttr)
    ttr_sim  = max(0.0, min(1.0, ttr_sim))

    score = 0.5 * len_sim + 0.5 * ttr_sim
    return round(score, 4)


# ---------------------------------------------------------------------------
# Krippendorff α (B-M-08)
# ---------------------------------------------------------------------------

def compute_krippendorff_alpha(
    ratings: List[List[float]],
) -> float:
    """
    Krippendorff α 계산 (간격 척도 기준).

    Args:
        ratings: shape [n_annotators][n_items] — 각 어노테이터의 점수 리스트.
                 결측값은 None으로 표시.

    Returns:
        α 값 (-1.0 ~ 1.0). 0.70 이상이면 acceptable agreement (B-M-08).
    """
    # 전치: items × annotators
    n_annotators = len(ratings)
    if n_annotators < 2:
        return 1.0  # 단독 어노테이터 → 완전 일치로 간주

    n_items = max(len(r) for r in ratings)

    # 유효 쌍 수집
    obs_disagreement = 0.0
    obs_count = 0

    all_values: List[float] = []
    for ann_ratings in ratings:
        for v in ann_ratings:
            if v is not None:
                all_values.append(v)

    if not all_values:
        return 0.0

    # Expected disagreement (전체 분포 기반)
    n_all = len(all_values)
    exp_disagreement = 0.0
    for i in range(n_all):
        for j in range(i + 1, n_all):
            exp_disagreement += (all_values[i] - all_values[j]) ** 2
    if n_all > 1:
        exp_disagreement = exp_disagreement / (n_all * (n_all - 1) / 2)

    # Observed disagreement (동일 아이템 어노테이터 쌍)
    for item_idx in range(n_items):
        item_vals = []
        for ann_ratings in ratings:
            if item_idx < len(ann_ratings) and ann_ratings[item_idx] is not None:
                item_vals.append(ann_ratings[item_idx])
        n_k = len(item_vals)
        if n_k < 2:
            continue
        for i in range(n_k):
            for j in range(i + 1, n_k):
                obs_disagreement += (item_vals[i] - item_vals[j]) ** 2
                obs_count += 1

    if obs_count == 0 or exp_disagreement == 0:
        return 1.0

    obs_avg = obs_disagreement / obs_count
    alpha   = 1.0 - obs_avg / exp_disagreement
    return round(max(-1.0, min(1.0, alpha)), 4)


# ---------------------------------------------------------------------------
# EquivalenceTester 래퍼 (Axis-5)
# ---------------------------------------------------------------------------

def _equiv_pass_rate(hypothesis: str, reference: str) -> float:
    """
    EquivalenceTester 5축 pass_rate 근사.
    실 운영: EquivalenceTester.run_golden_set() 연동.
    현재: BERTScore F1 기반 단순 근사.
    """
    f1 = compute_bertscore_f1(hypothesis, reference)
    # F1 0.85 이상이면 전체 pass_rate 0.95 이상으로 근사
    return min(1.0, f1 / 0.85 * 0.95) if f1 < 0.85 else 0.95 + (f1 - 0.85) * 0.33


# ---------------------------------------------------------------------------
# 결과 데이터클래스
# ---------------------------------------------------------------------------

@dataclass
class EvalAxisResult:
    """단일 평가 축 결과."""
    axis:      str
    score:     float
    threshold: float
    passed:    bool

    def to_dict(self) -> Dict:
        return {
            "axis":      self.axis,
            "score":     round(self.score, 4),
            "threshold": self.threshold,
            "passed":    self.passed,
        }


@dataclass
class EvalResult:
    """5축 통합 평가 결과."""
    passed:       bool
    axis_results: List[EvalAxisResult]
    failed_axes:  List[str] = field(default_factory=list)
    alpha:        Optional[float] = None   # Krippendorff α (제공 시)

    def __post_init__(self) -> None:
        self.failed_axes = [r.axis for r in self.axis_results if not r.passed]

    def to_dict(self) -> Dict:
        d: Dict[str, Any] = {
            "passed":       self.passed,
            "failed_axes":  self.failed_axes,
            "axis_results": [r.to_dict() for r in self.axis_results],
        }
        if self.alpha is not None:
            d["krippendorff_alpha"] = self.alpha
        return d


# ---------------------------------------------------------------------------
# FineTuneEvalPipeline — 메인 클래스
# ---------------------------------------------------------------------------

class FineTuneEvalPipeline:
    """
    파인튜닝 산출물 5축 자동 평가 파이프라인.

    B-M-07 임계값:
        BERTScore F1 ≥ 0.85
        LLM-judge   ≥ 4.0
        Style       ≥ 0.80
        BLEU-4      ≥ 0.30
        Equiv rate  ≥ 0.95

    Usage:
        pipeline = FineTuneEvalPipeline()
        result = pipeline.evaluate(hypothesis="모델 출력", reference="참조 텍스트")
        if result.passed:
            # PASS → ArtifactStage.VALIDATED 진급 허용
            ...
    """

    def __init__(
        self,
        bertscore_threshold: float = THRESHOLD_BERTSCORE_F1,
        llm_judge_threshold: float = THRESHOLD_LLM_JUDGE,
        style_threshold:     float = THRESHOLD_STYLE,
        bleu_threshold:      float = THRESHOLD_BLEU,
        equiv_threshold:     float = THRESHOLD_EQUIV_PASS_RATE,
    ) -> None:
        self.bertscore_threshold = bertscore_threshold
        self.llm_judge_threshold = llm_judge_threshold
        self.style_threshold     = style_threshold
        self.bleu_threshold      = bleu_threshold
        self.equiv_threshold     = equiv_threshold

    def evaluate(
        self,
        hypothesis: str,
        reference: str,
        annotator_ratings: Optional[List[List[float]]] = None,
    ) -> EvalResult:
        """
        단일 (hypothesis, reference) 쌍 5축 평가.

        Args:
            hypothesis:         모델 생성 텍스트
            reference:          참조(정답) 텍스트
            annotator_ratings:  Krippendorff α 계산용 인간 평가 리스트 (선택)

        Returns:
            EvalResult
        """
        bs_f1   = compute_bertscore_f1(hypothesis, reference)
        judge   = _stub_llm_judge(hypothesis)
        style   = compute_style_score(hypothesis, reference)
        bleu    = compute_bleu4(hypothesis, reference)
        eq_rate = _equiv_pass_rate(hypothesis, reference)

        axis_results = [
            EvalAxisResult("bertscore_f1",   bs_f1,   self.bertscore_threshold, bs_f1   >= self.bertscore_threshold),
            EvalAxisResult("llm_judge",      judge,   self.llm_judge_threshold, judge   >= self.llm_judge_threshold),
            EvalAxisResult("style",          style,   self.style_threshold,     style   >= self.style_threshold),
            EvalAxisResult("bleu4",          bleu,    self.bleu_threshold,      bleu    >= self.bleu_threshold),
            EvalAxisResult("equiv_rate",     eq_rate, self.equiv_threshold,     eq_rate >= self.equiv_threshold),
        ]

        passed = all(r.passed for r in axis_results)

        alpha: Optional[float] = None
        if annotator_ratings:
            alpha = compute_krippendorff_alpha(annotator_ratings)

        return EvalResult(
            passed=passed,
            axis_results=axis_results,
            alpha=alpha,
        )

    def evaluate_batch(
        self,
        pairs: List[Tuple[str, str]],
    ) -> List[EvalResult]:
        """
        (hypothesis, reference) 쌍 배치 평가.

        Returns:
            EvalResult 리스트
        """
        return [self.evaluate(h, r) for h, r in pairs]

    def aggregate(self, results: List[EvalResult]) -> Dict:
        """
        배치 결과 집계 통계.

        Returns:
            dict with pass_rate + 축별 평균 점수
        """
        total     = len(results)
        pass_cnt  = sum(1 for r in results if r.passed)
        axis_sums: Dict[str, float] = {}
        for r in results:
            for ar in r.axis_results:
                axis_sums.setdefault(ar.axis, 0.0)
                axis_sums[ar.axis] += ar.score

        return {
            "total":      total,
            "pass_count": pass_cnt,
            "pass_rate":  round(pass_cnt / max(total, 1), 4),
            "axis_means": {
                k: round(v / max(total, 1), 4)
                for k, v in axis_sums.items()
            },
        }
