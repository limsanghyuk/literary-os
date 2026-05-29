"""
ModelEvalHarness — 파인튜닝 모델 평가 하네스 (V471)

ADR-009: LLM-as-Judge Calibration
LLM-0: BLEU/ROUGE/Coherence/StyleSimilarity 모두 로컬 계산

평가 지표:
  - BLEU (1~4gram 정밀도, brevity penalty)
  - ROUGE-L (최장 공통 부분 수열 기반)
  - Coherence Score (문장 간 연결성, 규칙 기반)
  - StyleSimilarity (스타일 레이블 일치율)
  - HallucinationRate (Provenance 미일치 비율)
"""
from __future__ import annotations

import math
import re
import uuid
from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class EvalSample:
    sample_id: str
    input_text: str
    reference_text: str
    generated_text: str
    style_label: str = ""
    source_docs: list[str] = field(default_factory=list)  # Provenance

    def to_dict(self) -> dict[str, Any]:
        return {
            "sample_id": self.sample_id,
            "style_label": self.style_label,
            "reference_length": len(self.reference_text),
            "generated_length": len(self.generated_text),
        }


@dataclass
class EvalReport:
    model_id: str
    report_id: str
    bleu_score: float          # 0~1
    rouge_l: float             # 0~1
    coherence_score: float     # 0~1
    style_similarity: float    # 0~1
    hallucination_rate: float  # 0~1 (낮을수록 좋음)
    sample_count: int
    passed: bool               # 전체 기준 통과 여부
    details: dict[str, Any]
    evaluated_at: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "model_id": self.model_id,
            "report_id": self.report_id,
            "bleu_score": self.bleu_score,
            "rouge_l": self.rouge_l,
            "coherence_score": self.coherence_score,
            "style_similarity": self.style_similarity,
            "hallucination_rate": self.hallucination_rate,
            "sample_count": self.sample_count,
            "passed": self.passed,
            "details": self.details,
            "evaluated_at": self.evaluated_at,
        }


# ---------------------------------------------------------------------------
# 내부 계산 함수 (LLM-0)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    """간단한 한국어+영어 토크나이저"""
    # 한자·한글·영문·숫자 단위로 분리
    return re.findall(r'[가-힣]+|[a-zA-Z]+|\d+|[^\s]', text.lower())


def _ngrams(tokens: list[str], n: int) -> list[tuple]:
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


def _bleu(reference: str, hypothesis: str, max_n: int = 4) -> float:
    """BLEU-N (수정 정밀도 기하 평균 + BP)

    effective_n = min(max_n, len(hyp_tokens) - 1) 동적 조정.
    단문(2~4 토큰) 부분 일치 시 고차 n-gram이 구조적 0이 되는
    문제를 방지한다 (ADR-009: 로컬 순수 계산 원칙 유지).
    """
    ref_tokens = _tokenize(reference)
    hyp_tokens = _tokenize(hypothesis)

    if not hyp_tokens:
        return 0.0

    # Brevity Penalty
    bp = math.exp(1 - len(ref_tokens) / len(hyp_tokens)) if len(hyp_tokens) > len(ref_tokens) else 1.0

    # 동적 max_n: range upper = min(max_n+1, len(hyp_tokens))
    # → effective_n_max = len(hyp_tokens) - 1 (단문 고차 n-gram 0 방지)
    precisions = []
    for n in range(1, min(max_n + 1, len(hyp_tokens))):
        ref_ng = Counter(_ngrams(ref_tokens, n))
        hyp_ng = Counter(_ngrams(hyp_tokens, n))
        clipped = sum(min(hyp_ng[ng], ref_ng.get(ng, 0)) for ng in hyp_ng)
        total = max(len(hyp_tokens) - n + 1, 1)
        precisions.append(clipped / total if total > 0 else 0.0)

    if not precisions:
        return 0.0

    # V483 Hotfix: BLEU smoothing — 고차 n-gram 정밀도 0 시 epsilon 치환
    # any(p==0) → return 0 은 단문에서 과도하게 BLEU=0 반환 유발
    # 대신 epsilon(1e-9) smoothing 적용 (Chen & Cherry Method 1 변형)
    _EPS = 1e-9
    smoothed = [p if p > 0 else _EPS for p in precisions]

    log_avg = sum(math.log(p) for p in smoothed) / len(smoothed)
    return round(bp * math.exp(log_avg), 4)


def _lcs_length(a: list[str], b: list[str]) -> int:
    """최장 공통 부분 수열 길이 (동적 프로그래밍)"""
    m, n = len(a), len(b)
    if m == 0 or n == 0:
        return 0
    # 메모리 절약: 1D DP
    prev = [0] * (n + 1)
    for i in range(1, m + 1):
        curr = [0] * (n + 1)
        for j in range(1, n + 1):
            if a[i-1] == b[j-1]:
                curr[j] = prev[j-1] + 1
            else:
                curr[j] = max(prev[j], curr[j-1])
        prev = curr
    return prev[n]


def _rouge_l(reference: str, hypothesis: str) -> float:
    """ROUGE-L F1"""
    ref_tokens = _tokenize(reference)
    hyp_tokens = _tokenize(hypothesis)
    if not ref_tokens or not hyp_tokens:
        return 0.0
    lcs = _lcs_length(ref_tokens, hyp_tokens)
    precision = lcs / len(hyp_tokens)
    recall = lcs / len(ref_tokens)
    if precision + recall == 0:
        return 0.0
    return round(2 * precision * recall / (precision + recall), 4)


def _coherence(text: str) -> float:
    """
    규칙 기반 문장 연결성 점수.
    - 접속사·연결어 존재 여부
    - 문장 길이 균형
    - 반복 구문 페널티
    """
    sentences = re.split(r'[.!?。]\s*', text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if len(sentences) <= 1:
        return 0.7  # 단문은 기본값

    # 접속사 점수
    connectors = ['그래서', '그런데', '하지만', '그러나', '따라서', '그리고',
                  '또한', '즉', '왜냐하면', '결국', '한편', '반면에', '그렇지만']
    connector_score = min(1.0, sum(
        0.15 for c in connectors if c in text
    ))

    # 문장 길이 균형
    lengths = [len(_tokenize(s)) for s in sentences]
    if len(lengths) < 2:
        length_balance = 0.8
    else:
        avg = sum(lengths) / len(lengths)
        std = math.sqrt(sum((l - avg) ** 2 for l in lengths) / len(lengths))
        cv = std / avg if avg > 0 else 1.0  # 변동계수
        length_balance = max(0.0, 1.0 - cv * 0.3)

    # 반복 페널티
    words = _tokenize(text)
    if len(words) > 0:
        unique_ratio = len(set(words)) / len(words)
        repetition_penalty = unique_ratio
    else:
        repetition_penalty = 0.5

    score = (connector_score * 0.3 + length_balance * 0.4 + repetition_penalty * 0.3)
    return round(min(1.0, score), 4)


def _style_similarity(generated: str, style_label: str) -> float:
    """
    스타일 레이블 기반 유사도 (규칙 기반 키워드 분석).
    실제 서비스에서는 임베딩 기반으로 교체.
    """
    style_keywords: dict[str, list[str]] = {
        "romance": ['사랑', '설레', '마음', '그리움', '두근', '눈물', '행복', '연인', '키스', '포옹'],
        "thriller": ['공포', '긴장', '추격', '살인', '비밀', '음모', '탈출', '위험', '충격', '반전'],
        "sf": ['우주', '로봇', '미래', '기술', '인공지능', '외계', '차원', '양자', '나노', '사이보그'],
        "historical": ['왕', '조선', '고려', '장군', '전쟁', '신라', '백제', '임금', '사대부', '무사'],
        "contemporary": ['현대', '직장', '카페', '스마트폰', '지하철', '아파트', '회사', '인터넷', '유튜브', '배달'],
    }

    keywords = style_keywords.get(style_label, [])
    if not keywords:
        return 0.5

    count = sum(1 for kw in keywords if kw in generated)
    return round(min(1.0, count / len(keywords) * 2), 4)


def _hallucination_rate(generated: str, source_docs: list[str]) -> float:
    """
    Provenance 기반 허상율.
    생성 텍스트 고유 명사가 소스 문서에 없으면 허상으로 간주.
    """
    if not source_docs:
        return 0.1  # 소스 없을 때 기본 낮은 허상율

    # 고유 명사 추출 (대문자 시작 또는 따옴표 내 명사)
    proper_nouns = set(re.findall(r'[A-Z][a-z]+|「([^」]+)」|『([^』]+)』', generated))
    flat_nouns = set()
    for item in proper_nouns:
        if isinstance(item, tuple):
            flat_nouns.update(n for n in item if n)
        else:
            flat_nouns.add(item)

    if not flat_nouns:
        return 0.05  # 고유 명사 없으면 허상율 낮음

    all_source = " ".join(source_docs)
    hallucinated = sum(1 for noun in flat_nouns if noun not in all_source)
    rate = hallucinated / len(flat_nouns)
    return round(rate, 4)


# ---------------------------------------------------------------------------
# ModelEvalHarness
# ---------------------------------------------------------------------------

class ModelEvalHarness:
    """
    ADR-009 파인튜닝 모델 평가 하네스.

    run_eval(model_id, samples) → EvalReport
    - BLEU ≥ 0.15 목표
    - ROUGE-L ≥ 0.20 목표
    - Coherence ≥ 0.60 목표
    - StyleSimilarity ≥ 0.30 목표
    - HallucinationRate ≤ 0.30 목표

    LLM-0: 모든 지표 로컬 규칙 기반 계산.
    """

    # 합격 임계값
    BLEU_THRESHOLD = 0.15
    ROUGE_THRESHOLD = 0.20
    COHERENCE_THRESHOLD = 0.60
    STYLE_SIM_THRESHOLD = 0.30
    HALLUCINATION_THRESHOLD = 0.30  # 낮을수록 좋음

    def __init__(self) -> None:
        self._reports: dict[str, EvalReport] = {}

    def run_eval(
        self,
        model_id: str,
        samples: list[EvalSample],
    ) -> EvalReport:
        """전체 샘플에 대해 평가 지표 계산"""
        if not samples:
            raise ValueError("평가 샘플이 없습니다.")

        bleu_scores = []
        rouge_scores = []
        coherence_scores = []
        style_scores = []
        hallucination_rates = []

        for sample in samples:
            bleu_scores.append(_bleu(sample.reference_text, sample.generated_text))
            rouge_scores.append(_rouge_l(sample.reference_text, sample.generated_text))
            coherence_scores.append(_coherence(sample.generated_text))
            style_scores.append(
                _style_similarity(sample.generated_text, sample.style_label)
                if sample.style_label else 0.5
            )
            hallucination_rates.append(
                _hallucination_rate(sample.generated_text, sample.source_docs)
            )

        def avg(lst: list[float]) -> float:
            return round(sum(lst) / len(lst), 4) if lst else 0.0

        bleu = avg(bleu_scores)
        rouge = avg(rouge_scores)
        coherence = avg(coherence_scores)
        style_sim = avg(style_scores)
        halluc = avg(hallucination_rates)

        passed = (
            bleu >= self.BLEU_THRESHOLD
            and rouge >= self.ROUGE_THRESHOLD
            and coherence >= self.COHERENCE_THRESHOLD
            and style_sim >= self.STYLE_SIM_THRESHOLD
            and halluc <= self.HALLUCINATION_THRESHOLD
        )

        report = EvalReport(
            model_id=model_id,
            report_id=f"eval-{str(uuid.uuid4())[:8]}",
            bleu_score=bleu,
            rouge_l=rouge,
            coherence_score=coherence,
            style_similarity=style_sim,
            hallucination_rate=halluc,
            sample_count=len(samples),
            passed=passed,
            details={
                "thresholds": {
                    "bleu": self.BLEU_THRESHOLD,
                    "rouge_l": self.ROUGE_THRESHOLD,
                    "coherence": self.COHERENCE_THRESHOLD,
                    "style_similarity": self.STYLE_SIM_THRESHOLD,
                    "hallucination_rate": self.HALLUCINATION_THRESHOLD,
                },
                "individual": {
                    "bleu_per_sample": bleu_scores[:5],
                    "rouge_per_sample": rouge_scores[:5],
                },
            },
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )
        self._reports[model_id] = report
        return report

    def get_report(self, model_id: str) -> EvalReport | None:
        return self._reports.get(model_id)

    def compare(self, model_id_a: str, model_id_b: str) -> dict[str, Any]:
        """두 모델 보고서 비교"""
        ra = self._reports.get(model_id_a)
        rb = self._reports.get(model_id_b)
        if ra is None or rb is None:
            raise KeyError("비교 대상 보고서 없음")
        return {
            "model_a": model_id_a,
            "model_b": model_id_b,
            "bleu_delta": round(rb.bleu_score - ra.bleu_score, 4),
            "rouge_delta": round(rb.rouge_l - ra.rouge_l, 4),
            "coherence_delta": round(rb.coherence_score - ra.coherence_score, 4),
            "style_sim_delta": round(rb.style_similarity - ra.style_similarity, 4),
            "hallucination_delta": round(rb.hallucination_rate - ra.hallucination_rate, 4),
            "winner": model_id_b if (
                rb.bleu_score + rb.rouge_l + rb.coherence_score
                > ra.bleu_score + ra.rouge_l + ra.coherence_score
            ) else model_id_a,
        }
