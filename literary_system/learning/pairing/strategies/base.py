"""learning/pairing/strategies/base.py — 전략 인터페이스 + 파이프라인 순서 강제.

순서 강제(설계 C3): 후보 생성 → 길이매칭 → E4 게이트. process_candidate가 이 순서를
하드코딩한다. 어떤 전략도 이 순서를 우회할 수 없다.

혼합비 15/55/20/10(P1/P3/P2/P4), 1.3× 과생성(fail-fast 풀).
"""
from __future__ import annotations
import math
import re
import random as _random
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence

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


# ---------------------------------------------------------------------------
# 후보 생성 계층 (V793 포팅 — tools/loop_c_4070_kit/gen_p3.py·gen_p2.py 기반)
#
# 설계 원칙:
#   - 전략은 *선호쌍 생성 로직*(프롬프트 템플릿 + 파싱 + RawPair 조립)만 소유한다.
#   - LLM 호출은 주입된 Generator(prompt->text)로 추상화한다. 프로덕션=실 LLM,
#     테스트=결정론 페이크. → 네트워크/키 없이 단위 테스트 가능(I5 토크나이저 잠금과
#     동일 철학: 외부 비결정성 격리).
#   - 생성된 RawPair는 그대로 process_candidate(길이매칭→E4) 파이프라인에 투입된다.
#     즉 생성 계층은 파이프라인을 우회하지 않는다(설계 C3).
# ---------------------------------------------------------------------------

# Generator: 프롬프트 1개를 받아 모델 응답 텍스트를 돌려주는 호출 가능 객체.
Generator = Callable[[str], str]


def parse_two_version(text: str, marker_a: str, marker_b: str):
    """[A]...[B]... 2버전 응답을 (a_body, b_body)로 분해. 실패 시 (None, None)."""
    m = re.search(re.escape(marker_a) + r"(.*?)" + re.escape(marker_b) + r"(.*)",
                  text, re.S)
    if not m:
        return None, None
    return m.group(1).strip()[:600], m.group(2).strip()[:600]


class TwoVersionStrategy(BaseStrategy):
    """chosen/rejected를 '같은 상황·목표길이'의 두 버전으로 생성하는 LLM 기반 전략.

    P3(show vs tell)·P2(good vs weak)의 공통 골격. 하위 클래스는
    PROMPT_FN / MARKER_A / MARKER_B / SITUATIONS / GENRES 만 정의한다.
    """
    MARKER_A = "[A]"
    MARKER_B = "[B]"
    SITUATIONS: Sequence[str] = ()
    GENRES: Sequence[str] = ()
    MIN_LEN = 150

    def _prompt(self, situ: str, genre: str) -> str:
        raise NotImplementedError

    def generate(self, n: int, *, generator: Generator,
                 rng: Optional[_random.Random] = None,
                 max_attempts_factor: int = 3) -> List[RawPair]:
        """n개 RawPair 생성. chosen=우월버전, rejected=열등버전.

        - generator 예외/단문(<MIN_LEN)/파싱실패는 폐기 후 재시도(fail-fast 풀).
        - 결과 RawPair는 strategy=self.name. ref_text 미설정(E4는 명작 원문 대상이며
          본 합성쌍은 원문 인용이 아니므로 skipped로 정직 기록됨 — base 설계).
        """
        rng = rng or _random.Random()
        out: List[RawPair] = []
        attempts = 0
        cap = max(n * max_attempts_factor, n + 1)
        while len(out) < n and attempts < cap:
            attempts += 1
            situ = rng.choice(self.SITUATIONS) if self.SITUATIONS else ""
            genre = rng.choice(self.GENRES) if self.GENRES else ""
            try:
                text = generator(self._prompt(situ, genre))
            except Exception:
                continue
            a, b = parse_two_version(text, self.MARKER_A, self.MARKER_B)
            if not a or not b or len(a) < self.MIN_LEN or len(b) < self.MIN_LEN:
                continue
            i = len(out)
            out.append(RawPair(
                pair_id=f"{self.name}_{i:04d}", work_id=f"{self.name}_{i:04d}",
                strategy=self.name, chosen_text=a, rejected_text=b,
                genre=genre, meta={"situation": situ}))
        return out
