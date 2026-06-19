"""G_MEMORIZATION — 결정론적 암기/표절 하드게이트 (LLM-0).

목적
----
LLM-1 Critic가 winner=ref(원문)를 학습목표로 삼는 구조에서, 정책이
'원문을 변형해 이기는' 것이 아니라 '원문을 통째로 베껴서 이기는' 보상
해킹(reward hacking)을 차단한다. 생성 초안(candidate)이 레퍼런스(reference)를
축자(verbatim) 복제하거나 근접 중복(near-duplicate)이면 하드 페널티를 부과한다.

설계 원칙 (3인 교차검토 종합)
----------------------------
- COMP: 외부 의존성 0. 순수 char-level 알고리즘. 토크나이저/모델 호출 없음 → LLM-0.
- DATA: 한국어는 형태소 경계가 모호하므로 char 단위가 안전. 단, '비율'만으로는
        긴 텍스트의 부분 표절을 놓친다 → '절대 연속 일치 길이(contiguous run)'를
        독립 신호로 둔다. 25자(≈한국어 15형태소) 연속 일치는 비율과 무관하게 표절.
- DATA: 오탐(고유명사·관용구·인사말) 억제를 위해 hard block은 신호 '동시발화(co-fire)'
        를 요구한다. 단일 약신호는 review로만 표시.
- ARCH: R(구조보상)과 동일하게 '바닥(floor)'으로 동작. 보상에 더하지 않고,
        표절 판정 시 PENALTY로 덮어쓴다(G_NO_ABSOLUTE_REWARD 원칙과 정합).

판정 로직
---------
hard(표절) := (contig_chars >= TAU_CONTIG_CHARS AND lcs_ratio >= TAU_LCS)
           OR (lcs_ratio >= TAU_LCS_HARD)
           OR (ngram_jaccard >= TAU_JACCARD)
review     := hard가 아니면서 약신호 1개 이상 (lcs_ratio >= REVIEW_LCS 등)
pass       := 그 외

스레숄드는 보수적 기본값. 코퍼스 측정 후 ADR로 재보정.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List

# ── 스레숄드 (보수적 기본값; 코퍼스 캘리브레이션 후 ADR 재보정) ──────────────
TAU_CONTIG_CHARS = 25     # 절대 최장 연속 일치 길이(자). ≈한국어 15형태소 = 축자복제
TAU_LCS = 0.35            # LCS/len(candidate) — contig와 동시발화 시 hard
TAU_LCS_HARD = 0.60       # LCS 단독으로도 근접중복 판정하는 상한
TAU_JACCARD = 0.60        # char 5-gram Jaccard 근접중복 상한
NGRAM_N = 5               # char n-gram 크기
MIN_LEN = 30              # 정규화 후 이 미만은 검사 면제(짧은 대사 오탐 방지)
REVIEW_LCS = 0.25         # 단일 약신호 임계 → review
PENALTY = -9.99           # distribution_guard와 동일 페널티 규약


# ── 정규화 & 원자 함수 (한국어 안전: 토큰화 없이 char 시퀀스) ────────────────
def _norm(text: str) -> str:
    """소문자화 + 공백 정규화. 한국어는 대소문자 영향 없으나 라틴 혼용 대비."""
    if not text:
        return ""
    return " ".join(text.split()).lower()


def _lcs_len(a: str, b: str) -> int:
    """최장 공통 부분수열 길이. rolling 1-D DP로 O(len(a)) 메모리."""
    if not a or not b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = [0] * (len(b) + 1)
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            if ca == cb:
                cur[j] = prev[j - 1] + 1
            else:
                cur[j] = prev[j] if prev[j] >= cur[j - 1] else cur[j - 1]
        prev = cur
    return prev[-1]


def _longest_contig(a: str, b: str) -> int:
    """최장 공통 연속 부분문자열(substring) 길이. rolling 1-D DP."""
    if not a or not b:
        return 0
    if len(a) < len(b):
        a, b = b, a
    prev = [0] * (len(b) + 1)
    best = 0
    for ca in a:
        cur = [0] * (len(b) + 1)
        for j, cb in enumerate(b, 1):
            if ca == cb:
                cur[j] = prev[j - 1] + 1
                if cur[j] > best:
                    best = cur[j]
        prev = cur
    return best


def _char_ngrams(text: str, n: int) -> set:
    if len(text) < n:
        return {text} if text else set()
    return {text[i : i + n] for i in range(len(text) - n + 1)}


def _jaccard(a: set, b: set) -> float:
    if not a and not b:
        return 0.0
    inter = len(a & b)
    union = len(a | b)
    return inter / union if union else 0.0


# ── 결과 컨테이너 ────────────────────────────────────────────────────────────
@dataclass
class MemorizationGateResult:
    lcs_ratio: float
    contig_chars: int
    contig_ratio: float
    ngram_jaccard: float
    max_overlap: float          # 모든 비율신호의 max (요약 지표)
    plagiarized: bool
    decision: str               # "reject" | "review" | "pass"
    detail: str
    signals: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "lcs_ratio": round(self.lcs_ratio, 4),
            "contig_chars": self.contig_chars,
            "contig_ratio": round(self.contig_ratio, 4),
            "ngram_jaccard": round(self.ngram_jaccard, 4),
            "max_overlap": round(self.max_overlap, 4),
            "plagiarized": self.plagiarized,
            "decision": self.decision,
            "detail": self.detail,
            "signals": list(self.signals),
        }


# ── 메인 게이트 ──────────────────────────────────────────────────────────────
def g_memorization(
    candidate: str,
    reference: str,
    tau_contig_chars: int = TAU_CONTIG_CHARS,
    tau_lcs: float = TAU_LCS,
    tau_lcs_hard: float = TAU_LCS_HARD,
    tau_jaccard: float = TAU_JACCARD,
    ngram_n: int = NGRAM_N,
    min_len: int = MIN_LEN,
    review_lcs: float = REVIEW_LCS,
) -> MemorizationGateResult:
    """candidate가 reference를 암기/표절했는지 결정론적으로 판정."""
    c = _norm(candidate)
    r = _norm(reference)

    # 너무 짧으면 검사 면제 (짧은 대사·인사말 오탐 방지)
    if len(c) < min_len or len(r) < min_len:
        return MemorizationGateResult(
            lcs_ratio=0.0, contig_chars=0, contig_ratio=0.0,
            ngram_jaccard=0.0, max_overlap=0.0,
            plagiarized=False, decision="pass",
            detail=f"too_short(min_len={min_len}; |c|={len(c)},|r|={len(r)})",
            signals=[],
        )

    lcs = _lcs_len(c, r)
    lcs_ratio = lcs / len(c)
    contig = _longest_contig(c, r)
    contig_ratio = contig / len(c)
    jac = _jaccard(_char_ngrams(c, ngram_n), _char_ngrams(r, ngram_n))
    max_overlap = max(lcs_ratio, contig_ratio, jac)

    signals: List[str] = []
    if contig >= tau_contig_chars:
        signals.append(f"contig>={tau_contig_chars}({contig})")
    if lcs_ratio >= tau_lcs:
        signals.append(f"lcs_ratio>={tau_lcs}({lcs_ratio:.2f})")
    if jac >= tau_jaccard:
        signals.append(f"jaccard>={tau_jaccard}({jac:.2f})")

    # hard 판정: 동시발화 OR 단독 상한 초과
    hard = (
        (contig >= tau_contig_chars and lcs_ratio >= tau_lcs)
        or (lcs_ratio >= tau_lcs_hard)
        or (jac >= tau_jaccard)
    )

    if hard:
        return MemorizationGateResult(
            lcs_ratio=lcs_ratio, contig_chars=contig, contig_ratio=contig_ratio,
            ngram_jaccard=jac, max_overlap=max_overlap,
            plagiarized=True, decision="reject",
            detail="hard_block: " + "; ".join(signals),
            signals=signals,
        )

    # review: 약신호 1개 이상 (단독으로는 hard 못 미침)
    weak = bool(signals) or lcs_ratio >= review_lcs
    if weak:
        wsig = list(signals)
        if lcs_ratio >= review_lcs and not any("lcs_ratio" in s for s in wsig):
            wsig.append(f"lcs_ratio>={review_lcs}({lcs_ratio:.2f})")
        return MemorizationGateResult(
            lcs_ratio=lcs_ratio, contig_chars=contig, contig_ratio=contig_ratio,
            ngram_jaccard=jac, max_overlap=max_overlap,
            plagiarized=False, decision="review",
            detail="single_weak_signal: " + "; ".join(wsig),
            signals=wsig,
        )

    return MemorizationGateResult(
        lcs_ratio=lcs_ratio, contig_chars=contig, contig_ratio=contig_ratio,
        ngram_jaccard=jac, max_overlap=max_overlap,
        plagiarized=False, decision="pass",
        detail="below_all_thresholds",
        signals=[],
    )


def apply_memorization_penalty(reward: float, result: MemorizationGateResult) -> float:
    """표절 판정 시 보상을 PENALTY로 덮어쓴다(바닥 동작). 그 외 원보상 유지."""
    return PENALTY if result.plagiarized else reward
