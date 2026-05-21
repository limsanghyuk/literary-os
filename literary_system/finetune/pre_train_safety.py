"""
SP-B.1 (V599) — PreTrainSafety: 학습 전 데이터 안전성 4축 검사

Phase B 본안 보강 B-M-09:
  Axis-1 PII       — 한국 주민등록번호·전화·이메일·계좌번호 정규식 탐지
  Axis-2 Toxic     — 혐오·욕설·위험 키워드 패턴 탐지
  Axis-3 Copyright — 긴 반복 구절(>50자) verbatim 복제 탐지
  Axis-4 Quality   — 최소 길이·반복 비율·공백 비율 품질 필터

모든 축 PASS → SafetyResult.safe = True
하나라도 FAIL → safe = False + failed_axes 보고

LLM-0 원칙: 외부 LLM API 직접 호출 없음. 순수 정규식/통계 기반.
ADR-059 참조.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------

# Axis-4 Quality 임계값
QUALITY_MIN_CHARS: int   = 50       # 최소 문자 수
QUALITY_MAX_REPEAT_RATIO: float = 0.40  # 반복 구절 비율 상한
QUALITY_MAX_BLANK_RATIO: float  = 0.60  # 공백 비율 상한

# Axis-3 Copyright 임계값
COPYRIGHT_MIN_VERBATIM_LEN: int = 50    # verbatim 구절 최소 길이
COPYRIGHT_MAX_RATIO: float      = 0.30  # 본문 대비 허용 verbatim 비율 상한


# ---------------------------------------------------------------------------
# SafetyAxis 열거
# ---------------------------------------------------------------------------

class SafetyAxis(str, Enum):
    PII       = "pii"
    TOXIC     = "toxic"
    COPYRIGHT = "copyright"
    QUALITY   = "quality"


# ---------------------------------------------------------------------------
# PII 패턴 (Axis-1)
# ---------------------------------------------------------------------------

_PII_PATTERNS: List[Tuple[str, re.Pattern]] = [
    ("rrn",     re.compile(r"\b\d{6}-[1-4]\d{6}\b")),            # 주민등록번호
    ("phone",   re.compile(r"01[016789]-\d{3,4}-\d{4}")),        # 휴대전화
    ("email",   re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")),
    ("account", re.compile(r"\b\d{3,6}-\d{2,6}-\d{4,8}\b")),     # 계좌번호
    ("passport",re.compile(r"\b[A-Z]{1,2}\d{7,9}\b")),            # 여권번호
]


# ---------------------------------------------------------------------------
# Toxic 패턴 (Axis-2)  — 대표 예시 (실 운영 시 전문 리스트로 교체)
# ---------------------------------------------------------------------------

_TOXIC_PATTERNS: List[re.Pattern] = [
    re.compile(r"시[발팔]|씨[발팔]", re.IGNORECASE),
    re.compile(r"개(새끼|세끼)|병(신|쉰)", re.IGNORECASE),
    re.compile(r"(자살|자해)\s*(방법|방식|하는\s*법)", re.IGNORECASE),
    re.compile(r"폭발물\s*제조|총기\s*밀수", re.IGNORECASE),
    re.compile(r"(아동|어린이)\s*(음란|포르노)", re.IGNORECASE),
    re.compile(r"혐오\s*발언|hate\s*speech", re.IGNORECASE),
]


# ---------------------------------------------------------------------------
# 결과 데이터클래스
# ---------------------------------------------------------------------------

@dataclass
class AxisResult:
    """단일 축 검사 결과."""
    axis:    SafetyAxis
    passed:  bool
    score:   float          # 0.0 (위험) ~ 1.0 (안전)
    details: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict:
        return {
            "axis":    self.axis.value,
            "passed":  self.passed,
            "score":   round(self.score, 4),
            "details": self.details,
        }


@dataclass
class SafetyResult:
    """4축 통합 안전성 결과."""
    safe:         bool
    axis_results: List[AxisResult]
    text_length:  int
    failed_axes:  List[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.failed_axes = [
            r.axis.value for r in self.axis_results if not r.passed
        ]

    def to_dict(self) -> Dict:
        return {
            "safe":         self.safe,
            "text_length":  self.text_length,
            "failed_axes":  self.failed_axes,
            "axis_results": [r.to_dict() for r in self.axis_results],
        }


# ---------------------------------------------------------------------------
# 축별 검사 함수
# ---------------------------------------------------------------------------

def _check_pii(text: str) -> AxisResult:
    """Axis-1: PII 탐지 (정규식)."""
    hits: List[str] = []
    for name, pat in _PII_PATTERNS:
        matches = pat.findall(text)
        if matches:
            hits.append(f"{name}:{len(matches)}건")

    passed = len(hits) == 0
    score  = 0.0 if hits else 1.0
    return AxisResult(
        axis=SafetyAxis.PII,
        passed=passed,
        score=score,
        details=hits,
    )


def _check_toxic(text: str) -> AxisResult:
    """Axis-2: 혐오·욕설·위험 키워드 탐지."""
    hits: List[str] = []
    for pat in _TOXIC_PATTERNS:
        m = pat.search(text)
        if m:
            hits.append(f"matched:{m.group()[:20]!r}")

    passed = len(hits) == 0
    score  = 0.0 if hits else 1.0
    return AxisResult(
        axis=SafetyAxis.TOXIC,
        passed=passed,
        score=score,
        details=hits,
    )


def _check_copyright(text: str, reference_corpus: Optional[List[str]] = None) -> AxisResult:
    """
    Axis-3: Verbatim 복제 탐지.

    reference_corpus 미제공 시 → 내부 반복 구절 비율만 검사.
    reference_corpus 제공 시 → 각 참조 텍스트와 대조.
    """
    text_len = max(len(text), 1)
    verbatim_chars = 0
    details: List[str] = []

    corpora = reference_corpus or []

    for ref in corpora:
        # 긴 공통 부분 문자열 탐색 (간소화: 50자 슬라이딩 윈도우)
        for start in range(0, len(ref) - COPYRIGHT_MIN_VERBATIM_LEN, 10):
            snippet = ref[start: start + COPYRIGHT_MIN_VERBATIM_LEN]
            if snippet in text:
                verbatim_chars += COPYRIGHT_MIN_VERBATIM_LEN
                details.append(f"verbatim:{snippet[:20]!r}")
                break  # 해당 참조에서 1건 발견 시 충분

    ratio = verbatim_chars / text_len
    passed = ratio <= COPYRIGHT_MAX_RATIO
    score  = max(0.0, 1.0 - ratio / max(COPYRIGHT_MAX_RATIO, 1e-9))
    score  = min(1.0, score)

    if not details:
        details = ["no_verbatim_match"]

    return AxisResult(
        axis=SafetyAxis.COPYRIGHT,
        passed=passed,
        score=score,
        details=details,
    )


def _check_quality(text: str) -> AxisResult:
    """
    Axis-4: 품질 필터.
    - 최소 문자 수 50
    - 반복 구절 비율 ≤ 0.40
    - 공백 비율 ≤ 0.60
    """
    details: List[str] = []
    issues = 0

    # 최소 길이
    if len(text) < QUALITY_MIN_CHARS:
        details.append(f"too_short:{len(text)}<{QUALITY_MIN_CHARS}")
        issues += 1

    # 공백 비율
    ws_ratio = sum(1 for c in text if unicodedata.category(c) in ("Zs", "Cc")) / max(len(text), 1)
    if ws_ratio > QUALITY_MAX_BLANK_RATIO:
        details.append(f"blank_ratio:{ws_ratio:.2f}>{QUALITY_MAX_BLANK_RATIO}")
        issues += 1

    # 반복 비율 — 4-gram 중복 비율
    words = text.split()
    if len(words) >= 4:
        grams = [" ".join(words[i: i + 4]) for i in range(len(words) - 3)]
        unique = len(set(grams))
        repeat_ratio = 1.0 - unique / max(len(grams), 1)
        if repeat_ratio > QUALITY_MAX_REPEAT_RATIO:
            details.append(f"repeat_ratio:{repeat_ratio:.2f}>{QUALITY_MAX_REPEAT_RATIO}")
            issues += 1
    else:
        repeat_ratio = 0.0

    passed = issues == 0
    score  = max(0.0, 1.0 - issues * 0.34)
    if not details:
        details = ["quality_ok"]

    return AxisResult(
        axis=SafetyAxis.QUALITY,
        passed=passed,
        score=score,
        details=details,
    )


# ---------------------------------------------------------------------------
# PreTrainSafety — 메인 클래스
# ---------------------------------------------------------------------------

class PreTrainSafety:
    """
    학습 데이터 안전성 4축 검사기.

    B-M-09: PII / Toxic / Copyright / Quality 전축 PASS 필수.
    LLM-0: 외부 LLM API 호출 없음.

    Usage:
        checker = PreTrainSafety()
        result = checker.check("씬 텍스트…")
        if not result.safe:
            print(result.failed_axes)
    """

    def __init__(
        self,
        reference_corpus: Optional[List[str]] = None,
    ) -> None:
        """
        Args:
            reference_corpus: Copyright 대조용 참조 텍스트 리스트 (선택)
        """
        self._reference_corpus = reference_corpus or []

    def check(self, text: str) -> SafetyResult:
        """
        단일 텍스트에 대해 4축 안전성 검사를 수행.

        Args:
            text: 검사 대상 텍스트

        Returns:
            SafetyResult (safe=True/False + 축별 상세)
        """
        axis_results = [
            _check_pii(text),
            _check_toxic(text),
            _check_copyright(text, self._reference_corpus),
            _check_quality(text),
        ]
        safe = all(r.passed for r in axis_results)
        return SafetyResult(
            safe=safe,
            axis_results=axis_results,
            text_length=len(text),
        )

    def check_batch(self, texts: List[str]) -> List[SafetyResult]:
        """
        텍스트 배치 일괄 검사.

        Args:
            texts: 검사 대상 텍스트 리스트

        Returns:
            SafetyResult 리스트 (texts 순서와 동일)
        """
        return [self.check(t) for t in texts]

    def filter_safe(self, texts: List[str]) -> Tuple[List[str], List[SafetyResult]]:
        """
        배치 중 safe=True 텍스트만 필터링.

        Returns:
            (safe_texts, all_results)
        """
        results = self.check_batch(texts)
        safe_texts = [t for t, r in zip(texts, results) if r.safe]
        return safe_texts, results

    def summary(self, results: List[SafetyResult]) -> Dict:
        """
        배치 결과 요약 통계.

        Returns:
            dict with total / safe_count / fail_counts_by_axis
        """
        total = len(results)
        safe_count = sum(1 for r in results if r.safe)
        fail_by_axis: Dict[str, int] = {ax.value: 0 for ax in SafetyAxis}
        for r in results:
            for ax in r.failed_axes:
                fail_by_axis[ax] = fail_by_axis.get(ax, 0) + 1
        return {
            "total":          total,
            "safe_count":     safe_count,
            "fail_count":     total - safe_count,
            "pass_rate":      round(safe_count / max(total, 1), 4),
            "fail_by_axis":   fail_by_axis,
        }
