"""
critic/base.py — Critic 추상 인터페이스 + 5축 정의 (V753, ADR-214)

D-E2-4 확정 5축:
  STRUCTURE 구조 · CHARACTER 인물 · DIALOGUE 대사 · EMOTION 감정 · GENRE 장르
원칙(LLM-1):
  - 쌍대 판정만 (winner ∈ {a,b,tie}) — 절대 점수 금지 (G_NO_ABSOLUTE_REWARD).
  - RAG 컨텍스트 필수 (G_LLM1_RAG): rag_refs 없는 호출 거부.
  - base는 추상(외부 LLM 미호출). 실 LLM critic은 V754~ 서브클래스에서 주입.
"""
from __future__ import annotations
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Tuple

from literary_system.validation.pairwise import bt_scores  # critic 합의=쌍대 BT 집계(결선)


class CriticAxis(str, Enum):
    STRUCTURE = "structure"   # 기승전결·인과·비트 충실
    CHARACTER = "character"   # 인물 일관성·욕망/결함·관계 변화
    DIALOGUE = "dialogue"     # 대사 자연성·서브텍스트·화자 구별
    EMOTION = "emotion"       # 감정 흐름·긴장·카타르시스
    GENRE = "genre"           # 장르 관습·톤·기대 충족


AXIS_DESC = {
    CriticAxis.STRUCTURE: "기승전결·인과 연결·비트 충실도",
    CriticAxis.CHARACTER: "인물 일관성·욕망/결함 표현·관계 변화",
    CriticAxis.DIALOGUE: "대사 자연성·서브텍스트·화자 구별",
    CriticAxis.EMOTION: "감정 흐름·긴장 곡선·카타르시스",
    CriticAxis.GENRE: "장르 관습·톤 일치·기대 충족",
}

_WINNERS = ("a", "b", "tie")


@dataclass(frozen=True)
class CriticContext:
    """critic 호출 컨텍스트. rag_refs 필수(G_LLM1_RAG)."""
    rag_refs: List[str]
    genre: Optional[str] = None
    targets: Optional[dict] = None

    def __post_init__(self) -> None:
        if not self.rag_refs:
            raise ValueError("critic 호출에 RAG 컨텍스트 필수 (G_LLM1_RAG)")


@dataclass(frozen=True)
class CriticVerdict:
    """단일 critic의 쌍대 판정 (절대점수 없음)."""
    axis: str
    winner: str            # "a" | "b" | "tie"
    rationale: str
    critic_id: str

    def __post_init__(self) -> None:
        if self.winner not in _WINNERS:
            raise ValueError(f"winner는 {_WINNERS} (절대점수 금지): {self.winner}")


class CriticInterface(ABC):
    """축별 쌍대 critic 추상. 서브클래스가 _judge(LLM)를 구현."""
    axis: CriticAxis = CriticAxis.STRUCTURE

    @abstractmethod
    def _judge(self, a_text: str, b_text: str, ctx: CriticContext) -> Tuple[str, str]:
        """반환: (winner ∈ {a,b,tie}, rationale). 실 LLM 호출은 여기서."""
        ...

    def evaluate(self, a_text: str, b_text: str, ctx: CriticContext) -> CriticVerdict:
        if not isinstance(ctx, CriticContext) or not ctx.rag_refs:
            raise ValueError("RAG 컨텍스트 필수 (G_LLM1_RAG)")
        winner, rationale = self._judge(a_text, b_text, ctx)
        return CriticVerdict(axis=self.axis.value, winner=winner,
                             rationale=rationale, critic_id=type(self).__name__)


class MockCritic(CriticInterface):
    """테스트용 결정론 critic (LLM 미호출). 더 긴 텍스트를 a/b 우세로 판정."""
    def __init__(self, axis: CriticAxis = CriticAxis.STRUCTURE) -> None:
        self.axis = axis

    def _judge(self, a_text: str, b_text: str, ctx: CriticContext) -> Tuple[str, str]:
        if len(a_text) == len(b_text):
            return "tie", "동일 길이(mock)"
        w = "a" if len(a_text) > len(b_text) else "b"
        return w, f"{self.axis.value}: 더 충실한 쪽(mock)"


def aggregate_verdicts(verdicts: Sequence[CriticVerdict],
                       a_id: str, b_id: str) -> Dict[str, float]:
    """여러 축 critic verdict → pairwise BT 점수로 합의 집계 (validation.pairwise 재사용).

    절대점수 금지 원칙 유지: 각 verdict는 a/b/tie 쌍대 판정이고, BT로만 종합한다.
    """
    judgments = []
    for v in verdicts:
        if v.winner == "tie":
            continue
        judgments.append({"left_id": a_id, "right_id": b_id,
                          "winner": "left" if v.winner == "a" else "right"})
    return bt_scores(judgments) if judgments else {}
