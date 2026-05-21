"""
SP-A.4 (V591) — EquivalenceTester: MOCK↔REAL 5축 검증

MOCK fine-tune 결과와 실제 GPU fine-tune 결과 간의 동등성을 5가지 축으로
검증하여 MOCK fixture가 실제 환경에서도 유효한지 자동으로 감지한다.

5축:
  1. schema_match       — 출력 스키마 일치 (필수 필드 존재)
  2. length_ratio       — 출력 길이 비율 (0.9 ≤ ratio ≤ 1.1)
  3. kl_divergence      — 토큰 분포 KL 발산 (≤ 0.3)
  4. bertscore_f1       — BERTScore F1 유사도 (≥ 0.80, 근사치 사용)
  5. safety_pass        — 안전성 검증 통과 (금칙어 0건)

drift_detected 기준: 전체 골든셋에서 pass_rate < 0.95

LLM-0 원칙: 외부 LLM API 호출 없음. BERTScore는 경량 n-gram 기반 근사치 사용.

ADR-052 참조.
"""
from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 상수 / 임계값
# ---------------------------------------------------------------------------

# 5축 임계값
THRESHOLD_LENGTH_RATIO_MIN: float = 0.9
THRESHOLD_LENGTH_RATIO_MAX: float = 1.1
THRESHOLD_KL_DIVERGENCE_MAX: float = 0.3
THRESHOLD_BERTSCORE_F1_MIN: float = 0.80
DRIFT_PASS_RATE_MIN: float = 0.95  # 이 이하이면 drift_detected=True

# 안전성: 금칙어 패턴 (실명/욕설/PII 대리 패턴)
_SAFETY_FORBIDDEN_PATTERNS: List[str] = [
    r"\b\d{6}-\d{7}\b",          # 주민등록번호 패턴
    r"\b01[0-9]-\d{3,4}-\d{4}\b", # 한국 휴대폰 번호
    r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",  # 이메일
]


# ---------------------------------------------------------------------------
# 데이터 모델
# ---------------------------------------------------------------------------

@dataclass
class EquivalenceAxis:
    """단일 축 검증 결과."""
    name:    str
    passed:  bool
    score:   float          # 정량 점수 (비율, 거리, F1 등)
    threshold: float        # 합격 기준
    detail:  str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name":      self.name,
            "passed":    self.passed,
            "score":     round(self.score, 6),
            "threshold": self.threshold,
            "detail":    self.detail,
        }


@dataclass
class EquivalenceReport:
    """
    단일 샘플 5축 검증 보고서.

    Attributes:
        sample_id:   골든셋 샘플 식별자
        all_passed:  5축 모두 합격 여부
        axes:        각 축별 결과 목록
        mock_output: MOCK 출력 (스냅샷)
        real_output: REAL 출력 (비교 대상)
    """
    sample_id:   str
    all_passed:  bool
    axes:        List[EquivalenceAxis]
    mock_output: Dict[str, Any] = field(default_factory=dict)
    real_output: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "sample_id":  self.sample_id,
            "all_passed": self.all_passed,
            "axes":       [a.to_dict() for a in self.axes],
        }


@dataclass
class EquivalenceDriftReport:
    """
    골든셋 전체 drift 평가 결과.

    Attributes:
        total_samples:  평가한 샘플 수
        passed_samples: 5축 모두 합격한 샘플 수
        pass_rate:      합격률 (passed / total)
        drift_detected: True if pass_rate < DRIFT_PASS_RATE_MIN
        axis_stats:     축별 합격률 집계
        reports:        샘플별 상세 보고서
    """
    total_samples:  int
    passed_samples: int
    pass_rate:      float
    drift_detected: bool
    axis_stats:     Dict[str, float]  # axis_name → pass_rate
    reports:        List[EquivalenceReport]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_samples":  self.total_samples,
            "passed_samples": self.passed_samples,
            "pass_rate":      round(self.pass_rate, 4),
            "drift_detected": self.drift_detected,
            "axis_stats":     {k: round(v, 4) for k, v in self.axis_stats.items()},
            "sample_reports": [r.to_dict() for r in self.reports],
        }


# ---------------------------------------------------------------------------
# 5축 검증 함수
# ---------------------------------------------------------------------------

def _check_schema_match(
    mock_out: Dict[str, Any],
    real_out: Dict[str, Any],
    required_keys: Optional[List[str]] = None,
) -> EquivalenceAxis:
    """
    축 1: schema_match
    MOCK 출력과 REAL 출력이 동일한 최상위 키를 갖는지 검증.
    required_keys 미지정 시 mock_out의 키를 기준으로 사용.
    """
    keys = required_keys or list(mock_out.keys())
    missing = [k for k in keys if k not in real_out]
    passed = len(missing) == 0
    score = 1.0 - len(missing) / max(len(keys), 1)
    return EquivalenceAxis(
        name      = "schema_match",
        passed    = passed,
        score     = score,
        threshold = 1.0,
        detail    = f"missing keys: {missing}" if missing else "all keys present",
    )


def _check_length_ratio(
    mock_out: Dict[str, Any],
    real_out: Dict[str, Any],
    text_key: str = "text",
) -> EquivalenceAxis:
    """
    축 2: length_ratio
    MOCK/REAL 출력 텍스트 길이 비율이 [0.9, 1.1] 범위인지 검증.
    text_key가 없으면 전체 dict repr 길이로 대체.
    """
    mock_text = str(mock_out.get(text_key, mock_out))
    real_text = str(real_out.get(text_key, real_out))
    mock_len  = max(len(mock_text), 1)
    real_len  = max(len(real_text), 1)
    ratio     = real_len / mock_len
    passed    = THRESHOLD_LENGTH_RATIO_MIN <= ratio <= THRESHOLD_LENGTH_RATIO_MAX
    return EquivalenceAxis(
        name      = "length_ratio",
        passed    = passed,
        score     = ratio,
        threshold = THRESHOLD_LENGTH_RATIO_MAX,  # 상한 기준으로 표시
        detail    = f"mock={mock_len}chars real={real_len}chars ratio={ratio:.3f}",
    )


def _token_freq(text: str) -> Dict[str, float]:
    """간단한 단어 빈도 분포 (소문자, 구두점 제거)."""
    words = re.findall(r"[가-힣a-zA-Z0-9]+", text.lower())
    if not words:
        return {"__empty__": 1.0}
    freq: Dict[str, int] = {}
    for w in words:
        freq[w] = freq.get(w, 0) + 1
    total = sum(freq.values())
    return {w: c / total for w, c in freq.items()}


def _kl_divergence(p: Dict[str, float], q: Dict[str, float]) -> float:
    """
    KL(P || Q) 계산. Q에 없는 단어는 스무딩(epsilon=1e-10) 처리.
    결과가 무한대이면 10.0으로 클리핑.
    """
    epsilon = 1e-10
    kl = 0.0
    for word, p_prob in p.items():
        q_prob = q.get(word, epsilon)
        kl += p_prob * math.log(p_prob / q_prob)
    return min(kl, 10.0)


def _check_kl_divergence(
    mock_out: Dict[str, Any],
    real_out: Dict[str, Any],
    text_key: str = "text",
) -> EquivalenceAxis:
    """
    축 3: kl_divergence
    MOCK 출력과 REAL 출력의 토큰 분포 KL 발산이 ≤ 0.3인지 검증.
    """
    mock_text = str(mock_out.get(text_key, mock_out))
    real_text = str(real_out.get(text_key, real_out))
    p = _token_freq(mock_text)
    q = _token_freq(real_text)
    kl = _kl_divergence(p, q)
    passed = kl <= THRESHOLD_KL_DIVERGENCE_MAX
    return EquivalenceAxis(
        name      = "kl_divergence",
        passed    = passed,
        score     = kl,
        threshold = THRESHOLD_KL_DIVERGENCE_MAX,
        detail    = f"KL(mock||real)={kl:.4f} (threshold≤{THRESHOLD_KL_DIVERGENCE_MAX})",
    )


def _ngram_overlap_f1(ref: str, hyp: str, n: int = 2) -> float:
    """
    n-gram 기반 BERTScore F1 근사치.
    LLM-0 원칙: 실제 BERT 모델 없이 n-gram overlap으로 근사.
    """
    def get_ngrams(text: str, n: int) -> Dict[Tuple[str, ...], int]:
        tokens = re.findall(r"[가-힣a-zA-Z0-9]+", text.lower())
        ngrams: Dict[Tuple[str, ...], int] = {}
        for i in range(len(tokens) - n + 1):
            gram = tuple(tokens[i : i + n])
            ngrams[gram] = ngrams.get(gram, 0) + 1
        return ngrams

    ref_grams = get_ngrams(ref, n)
    hyp_grams = get_ngrams(hyp, n)

    if not ref_grams or not hyp_grams:
        # 단어 없음 → 완전 일치로 처리 (빈 문서 케이스)
        return 1.0 if ref == hyp else 0.0

    # overlap count
    overlap = sum(min(ref_grams.get(g, 0), hyp_grams.get(g, 0)) for g in hyp_grams)
    precision = overlap / sum(hyp_grams.values()) if hyp_grams else 0.0
    recall    = overlap / sum(ref_grams.values()) if ref_grams else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return f1


def _check_bertscore_f1(
    mock_out: Dict[str, Any],
    real_out: Dict[str, Any],
    text_key: str = "text",
) -> EquivalenceAxis:
    """
    축 4: bertscore_f1
    n-gram 기반 BERTScore F1 근사치가 ≥ 0.80인지 검증.
    LLM-0: 외부 BERT 모델 호출 없음.
    """
    mock_text = str(mock_out.get(text_key, mock_out))
    real_text = str(real_out.get(text_key, real_out))
    # unigram(n=1)과 bigram(n=2) 평균
    f1_uni = _ngram_overlap_f1(mock_text, real_text, n=1)
    f1_bi  = _ngram_overlap_f1(mock_text, real_text, n=2)
    f1     = (f1_uni + f1_bi) / 2.0
    passed = f1 >= THRESHOLD_BERTSCORE_F1_MIN
    return EquivalenceAxis(
        name      = "bertscore_f1",
        passed    = passed,
        score     = f1,
        threshold = THRESHOLD_BERTSCORE_F1_MIN,
        detail    = f"n-gram approx F1={f1:.4f} (uni={f1_uni:.3f} bi={f1_bi:.3f})",
    )


def _check_safety_pass(real_out: Dict[str, Any], text_key: str = "text") -> EquivalenceAxis:
    """
    축 5: safety_pass
    REAL 출력에 금칙어 패턴(PII/욕설)이 없는지 검증.
    """
    real_text = str(real_out.get(text_key, real_out))
    violations: List[str] = []
    for pattern in _SAFETY_FORBIDDEN_PATTERNS:
        matches = re.findall(pattern, real_text)
        if matches:
            violations.extend(matches[:3])  # 최대 3개만 기록
    passed = len(violations) == 0
    score  = 0.0 if violations else 1.0
    return EquivalenceAxis(
        name      = "safety_pass",
        passed    = passed,
        score     = score,
        threshold = 1.0,
        detail    = f"violations: {violations}" if violations else "no violations",
    )


# ---------------------------------------------------------------------------
# EquivalenceTester
# ---------------------------------------------------------------------------

class EquivalenceTester:
    """
    MOCK↔REAL fine-tune 출력 동등성 5축 검증기.

    Usage::

        tester = EquivalenceTester()
        report = tester.compare(
            sample_id  = "golden_001",
            mock_output = {"text": "조선 시대 기생 춘향은..."},
            real_output = {"text": "조선 시대 기생 춘향이는..."},
        )
        assert report.all_passed

        drift = tester.run_golden_set()
        assert not drift.drift_detected
    """

    def __init__(
        self,
        text_key:          str            = "text",
        required_keys:     Optional[List[str]] = None,
        golden_set:        Optional[List[Dict[str, Any]]] = None,
        drift_threshold:   float          = DRIFT_PASS_RATE_MIN,
    ) -> None:
        self._text_key        = text_key
        self._required_keys   = required_keys
        self._golden_set      = golden_set or _build_default_golden_set()
        self._drift_threshold = drift_threshold

    # ── 핵심 API ────────────────────────────────────────────────

    def compare(
        self,
        sample_id:   str,
        mock_output: Dict[str, Any],
        real_output: Dict[str, Any],
    ) -> EquivalenceReport:
        """단일 샘플 5축 검증."""
        axes = [
            _check_schema_match(mock_output, real_output, self._required_keys),
            _check_length_ratio(mock_output, real_output, self._text_key),
            _check_kl_divergence(mock_output, real_output, self._text_key),
            _check_bertscore_f1(mock_output, real_output, self._text_key),
            _check_safety_pass(real_output, self._text_key),
        ]
        all_passed = all(a.passed for a in axes)
        return EquivalenceReport(
            sample_id   = sample_id,
            all_passed  = all_passed,
            axes        = axes,
            mock_output = mock_output,
            real_output = real_output,
        )

    def run_golden_set(
        self,
        real_outputs: Optional[List[Dict[str, Any]]] = None,
    ) -> EquivalenceDriftReport:
        """
        골든셋 전체 실행.

        Args:
            real_outputs: 실제 GPU 출력 목록. None이면 mock_output을 real로 사용
                          (self-consistency 검증 — 항상 PASS해야 함).

        Returns:
            EquivalenceDriftReport — drift_detected=True if pass_rate < DRIFT_PASS_RATE_MIN
        """
        reports: List[EquivalenceReport] = []
        for i, sample in enumerate(self._golden_set):
            mock_out = sample.get("mock_output", sample)
            real_out = (
                real_outputs[i]
                if real_outputs and i < len(real_outputs)
                else sample.get("real_output", mock_out)
            )
            sid    = sample.get("id", f"golden_{i:03d}")
            report = self.compare(sid, mock_out, real_out)
            reports.append(report)

        total   = len(reports)
        passed  = sum(1 for r in reports if r.all_passed)
        rate    = passed / total if total > 0 else 0.0

        # 축별 합격률
        axis_names = ["schema_match", "length_ratio", "kl_divergence", "bertscore_f1", "safety_pass"]
        axis_stats: Dict[str, float] = {}
        for ax_name in axis_names:
            ax_passed = sum(
                1 for r in reports
                for a in r.axes
                if a.name == ax_name and a.passed
            )
            axis_stats[ax_name] = ax_passed / total if total > 0 else 0.0

        return EquivalenceDriftReport(
            total_samples  = total,
            passed_samples = passed,
            pass_rate      = rate,
            drift_detected = rate < self._drift_threshold,
            axis_stats     = axis_stats,
            reports        = reports,
        )

    def update_golden_set(self, new_samples: List[Dict[str, Any]]) -> None:
        """드리프트 감지 후 골든셋 갱신 (MOCK fixture 자동 갱신용)."""
        self._golden_set = new_samples

    @property
    def golden_set_size(self) -> int:
        return len(self._golden_set)


# ---------------------------------------------------------------------------
# 기본 골든셋 20개 (한국 드라마/소설 장면 요약 예시)
# ---------------------------------------------------------------------------

def _build_default_golden_set() -> List[Dict[str, Any]]:
    """
    기본 골든셋 20개 — 한국 드라마/소설 장면 요약 텍스트.
    mock_output과 real_output이 동일(self-consistency) → 항상 5축 PASS.
    """
    scenes = [
        "조선 시대 기생 춘향은 이도령과 사랑에 빠졌으나 신분의 차이로 인해 고난을 겪는다.",
        "가야금 선율이 울려 퍼지는 달빛 아래 두 사람은 처음으로 눈을 마주쳤다.",
        "장마철 빗속에서 그녀는 우산도 없이 골목을 달렸다. 뒤에서 그가 불렀다.",
        "어머니는 된장찌개를 끓이며 딸의 귀가를 기다렸다. 시계 바늘만 돌아갔다.",
        "첫눈이 내리는 날 그는 오래된 편지를 꺼냈다. 잉크가 번진 자리에 그리움이 있었다.",
        "해질 무렵 강가에서 두 노인은 바둑돌을 하나씩 놓았다. 말은 필요 없었다.",
        "도시로 올라온 지 삼 년, 그녀는 처음으로 고향 사투리를 부끄럽게 생각했다.",
        "병실 창문으로 봄볕이 들어왔다. 의사는 검사 결과를 오래 들여다봤다.",
        "졸업식 날 아버지는 끝까지 눈물을 참았다. 집에 돌아와서야 혼자 울었다.",
        "시장 골목 떡볶이 집에서 그들은 우연히 다시 만났다. 십오 년 만이었다.",
        "새벽 세 시, 그는 아직도 원고지를 메우고 있었다. 마감은 여덟 시간 후였다.",
        "꽃밭 한가운데 할머니가 쪼그리고 앉아 잡초를 뽑았다. 손은 여전히 빠르고 능숙했다.",
        "회사 옥상에서 그녀는 도시를 내려다봤다. 사직서를 접어 주머니에 넣었다.",
        "밤 열차가 터널을 통과할 때 그들은 처음으로 손을 잡았다. 어둠이 도와줬다.",
        "오래된 사진 한 장이 책 사이에서 떨어졌다. 젊은 날의 부모님이 웃고 있었다.",
        "막내가 처음으로 걸음마를 떼던 날, 온 가족이 숨을 죽이고 지켜봤다.",
        "고시원 좁은 방에서 그는 법전을 펼쳤다. 열두 번째 도전이 시작되었다.",
        "폭설이 내린 아침, 이장은 홀로 제설을 시작했다. 누가 시킨 것도 아니었다.",
        "편의점 알바를 마치고 나온 그녀의 귀에 아직도 계산기 소리가 울렸다.",
        "마지막 회 방영이 끝나자 시청자 게시판에 글이 쏟아졌다. 모두 같은 말을 했다.",
    ]
    golden = []
    for i, scene in enumerate(scenes):
        output = {"text": scene, "scene_id": f"sc_{i:03d}", "word_count": len(scene.split())}
        golden.append({
            "id":          f"golden_{i:03d}",
            "mock_output": output,
            "real_output": output,  # self-consistency: 동일 출력
        })
    return golden
