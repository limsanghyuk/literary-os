"""
critic/llm_critics.py — 실 LLM 축별 Critic 5종 (V754, ADR-215)

CriticInterface(base) 서브클래스. 외부 LLM은 주입형 llm: Callable[[str],str].
블라인드(좌우 무작위) 쌍대 판정. 절대점수 금지(winner a/b/tie). RAG 필수(base에서 강제).
실 LLM은 개발자가 주입(RealOpenAIAdapter/gpt-5/gpt-4o-mini), 테스트는 fake llm.
"""
from __future__ import annotations
import random, re
from typing import Callable, List, Optional, Tuple

from literary_system.critic.base import (
    CriticAxis, CriticContext, CriticInterface, CriticVerdict, aggregate_verdicts,
)

_AXIS_CRITERIA = {
    CriticAxis.STRUCTURE: "극적 구조(도입·전개·전환)와 인과 연결·비트 충실도",
    CriticAxis.CHARACTER: "인물 일관성, 욕망·결함의 표현, 관계의 변화",
    CriticAxis.DIALOGUE: "대사의 자연스러움, 서브텍스트, 화자별 말투 구별",
    CriticAxis.EMOTION: "감정의 흐름과 긴장 곡선, 정서적 울림(카타르시스)",
    CriticAxis.GENRE: "장르 관습·톤의 일치와 장르적 기대 충족",
}


class LLMCritic(CriticInterface):
    """축별 쌍대 LLM critic. llm 미주입 시 _judge 호출에서 오류."""
    DEFAULT_PERSONAS = ("문학평론가", "드라마투르그", "일반시청자")

    def __init__(self, axis: CriticAxis,
                 llm: Optional[Callable[[str], str]] = None,
                 seed: Optional[int] = None,
                 n_judges: int = 1,
                 personas: Optional[tuple] = None) -> None:
        self.axis = axis
        self._llm = llm
        self._rng = random.Random(seed)
        self._n_judges = max(1, int(n_judges))      # V760: 다수 판정자 합의
        self._personas = personas or self.DEFAULT_PERSONAS

    def _build_prompt(self, A: str, B: str, ctx: CriticContext,
                      persona: Optional[str] = None) -> str:
        crit = _AXIS_CRITERIA[self.axis]
        pp = f"너는 '{persona}' 관점의 " if persona else "너는 "
        g = f"\n장르: {ctx.genre}" if ctx.genre else ""
        refs = "\n".join(f"- {r}" for r in ctx.rag_refs[:3])
        return (f"{pp}'{self.axis.value}' 전문 비평가다. 두 드라마 씬 A/B를 "
                f"**{crit}** 기준으로만 비교해 더 우수한 쪽을 고른다.{g}\n"
                f"참고(유사 실제 씬):\n{refs}\n"
                f"분석은 1문장 이내로 짧게. 그리고 **반드시 마지막 줄에 정확히** "
                f"'WINNER: A' 또는 'WINNER: B' 또는 'WINNER: TIE' 만 출력(다른 텍스트 금지).\n\n"
                f"=== 씬 A ===\n{A}\n\n=== 씬 B ===\n{B}\n")

    @staticmethod
    def _parse(resp: str) -> str:
        m = re.search(r"WINNER\s*[:：]\s*(A|B|TIE)", resp or "", re.I)
        if m:
            return {"A": "a", "B": "b", "TIE": "tie"}[m.group(1).upper()]
        m2 = re.search(r"(?:우수|나은|선택|승)[^\n]{0,8}?[:：(]?\s*(A|B)\b", resp or "", re.I)
        return {"A": "a", "B": "b"}[m2.group(1).upper()] if m2 else "tie"

    def _one_vote(self, a_text, b_text, ctx, persona):
        swap = self._rng.random() < 0.5            # 블라인드 좌우 무작위(독립)
        A, B = (b_text, a_text) if swap else (a_text, b_text)
        resp = self._llm(self._build_prompt(A, B, ctx, persona))
        w = self._parse(resp)
        if swap and w in ("a", "b"):               # 역변환
            w = "b" if w == "a" else "a"
        return w, (resp or "").strip()[:120]

    def _judge(self, a_text: str, b_text: str, ctx: CriticContext) -> Tuple[str, str]:
        if self._llm is None:
            raise RuntimeError(f"{type(self).__name__}: LLM 미주입(llm=)")
        if self._n_judges == 1:
            return self._one_vote(a_text, b_text, ctx, None)
        votes, notes = [], []
        for k in range(self._n_judges):            # V760: 다중 페르소나 합의
            persona = self._personas[k % len(self._personas)]
            w, note = self._one_vote(a_text, b_text, ctx, persona)
            votes.append(w); notes.append(f"{persona}:{w}")
        from collections import Counter
        cnt = Counter(votes); top, n = cnt.most_common(1)[0]
        # 동률(예: a==b 표) → tie
        winner = top if list(cnt.values()).count(n) == 1 else "tie"
        return winner, f"합의({self._n_judges}) {';'.join(notes)}"


class StructureCritic(LLMCritic):
    def __init__(self, llm=None, seed=None, n_judges=1, personas=None):
        super().__init__(CriticAxis.STRUCTURE, llm, seed, n_judges, personas)
class CharacterCritic(LLMCritic):
    def __init__(self, llm=None, seed=None, n_judges=1, personas=None):
        super().__init__(CriticAxis.CHARACTER, llm, seed, n_judges, personas)
class DialogueCritic(LLMCritic):
    def __init__(self, llm=None, seed=None, n_judges=1, personas=None):
        super().__init__(CriticAxis.DIALOGUE, llm, seed, n_judges, personas)
class EmotionCritic(LLMCritic):
    def __init__(self, llm=None, seed=None, n_judges=1, personas=None):
        super().__init__(CriticAxis.EMOTION, llm, seed, n_judges, personas)
class GenreCritic(LLMCritic):
    def __init__(self, llm=None, seed=None, n_judges=1, personas=None):
        super().__init__(CriticAxis.GENRE, llm, seed, n_judges, personas)

ALL_CRITICS = [StructureCritic, CharacterCritic, DialogueCritic, EmotionCritic, GenreCritic]


def make_ensemble(llm=None, seed=None, n_judges=1) -> List[LLMCritic]:
    return [LLMCritic(c().axis, llm=llm, seed=seed, n_judges=n_judges) for c in ALL_CRITICS]


def evaluate_all_axes(a_text: str, b_text: str, ctx: CriticContext,
                      llm: Callable[[str], str], a_id: str = "a", b_id: str = "b"):
    """5축 critic 전부 실행 → (verdicts, BT 합의 점수)."""
    verdicts = [c.evaluate(a_text, b_text, ctx) for c in make_ensemble(llm=llm)]
    return verdicts, aggregate_verdicts(verdicts, a_id, b_id)
