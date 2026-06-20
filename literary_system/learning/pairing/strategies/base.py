"""learning/pairing/strategies/base.py — 전략 인터페이스 + 파이프라인 순서 강제.

순서 강제(설계 C3): 후보 생성 → 길이매칭 → E4 게이트. process_candidate가 이 순서를
하드코딩한다. 어떤 전략도 이 순서를 우회할 수 없다.

혼합비 15/55/20/10(P1/P3/P2/P4), 1.3× 과생성(fail-fast 풀).
"""
from __future__ import annotations
import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from literary_system.learning.memorization_gate import g_memorization
from ..length_match import length_match_decision, LengthMatch
from ..tokenizer import Tokenizer

MIX: Dict[str, float] = {"p1": 0.15, "p3": 0.55, "p2": 0.20, "p4": 0.10}
OVERGEN = 1.3


@dataclass
class RawPair:
    pair_id: str
    work_id: str
    strategy: str
    chosen_text: str
    rejected_text: str
    ref_text: str = ""           # 명작 원문(E4 검사용 입력 — 산출물엔 미포함)
    genre: str = ""
    meta: Dict = field(default_factory=dict)


@dataclass(frozen=True)
class PairVerdict:
    pair_id: str
    work_id: str
    strategy: str
    accept: bool
    drop_reason: Optional[str]      # None | "length" | "e4_reject"
    length: LengthMatch
    e4_decision: str                # pass | review | reject | (skipped)
    chosen_n_tokens: int
    rejected_n_tokens: int
    soft_flag: bool                 # char soft 위반(보존하되 카운트)


def allocate(target_n: int, mix: Dict[str, float] = MIX,
             overgen: float = OVERGEN) -> Dict[str, int]:
    """전략별 생성 쿼터(과생성 포함). 합이 target_n*overgen 이상이 되도록 ceil."""
    pool = math.ceil(target_n * overgen)
    return {k: math.ceil(pool * v) for k, v in mix.items()}


def process_candidate(raw: RawPair, tokenizer: Tokenizer) -> PairVerdict:
    """순서 강제: (1) 길이매칭 → (2) E4 게이트. 둘 다 통과해야 accept."""
    cn = len(tokenizer.tokenize(raw.chosen_text))
    rn = len(tokenizer.tokenize(raw.rejected_text))
    lm = length_match_decision(cn, rn, len(raw.chosen_text), len(raw.rejected_text))

    if not lm.accept:
        return PairVerdict(raw.pair_id, raw.work_id, raw.strategy, False,
                           "length", lm, "skipped", cn, rn,
                           soft_flag=not lm.char_soft_ok)

    # E4는 길이매칭 후 실행(매칭이 텍스트를 바꾸므로 사후 — 설계 C2/C3)
    # ref_text 없으면 E4 검사 불가 → 정직하게 "skipped"로 기록(거짓 "pass" 금지).
    # 감사 가능성을 위해 report.e4_breakdown에 집계된다.
    e4 = "skipped"
    if raw.ref_text:
        res = g_memorization(candidate=raw.chosen_text, reference=raw.ref_text)
        e4 = res.decision
    if e4 == "reject":
        return PairVerdict(raw.pair_id, raw.work_id, raw.strategy, False,
                           "e4_reject", lm, e4, cn, rn,
                           soft_flag=not lm.char_soft_ok)

    return PairVerdict(raw.pair_id, raw.work_id, raw.strategy, True,
                       None, lm, e4, cn, rn, soft_flag=not lm.char_soft_ok)


class BaseStrategy:
    name = "base"
    description = ""

    def describe(self) -> str:
        return f"{self.name}: {self.description}"
