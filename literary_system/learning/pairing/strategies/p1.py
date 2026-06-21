"""P1 — 등급화 열화쌍(혼합 15%). chosen=원본, rejected=결정론적 열화본.

설계: 열화 4축 중 '텍스트 단축' 축은 길이교란(V788 회귀)을 재유입하므로 기본
비활성. 길이중립 3축(break_causality·flatten_affect·generic_swap)을 가중 적용해
per-token 신호가 '길이'가 아니라 '인과·정동·구체성'을 향하게 한다. 단축 축을 쓸
경우 meta.length_axis=True로 표식하고 process_candidate의 길이매칭이 사후 차단한다.

LLM 불요(결정론) — 원본 텍스트(sources)만 있으면 동작. 단위 테스트 친화적.
"""
from __future__ import annotations
import random as _random
import re
from typing import Dict, List, Optional, Sequence

from .base import BaseStrategy, RawPair

# 길이중립 열화 사전 -------------------------------------------------------
# break_causality: 인과 접속을 끊되 글자수는 보존(동일 길이 토큰으로 치환).
_CAUSAL = {
    "그래서": "그리고", "때문에": "관련해", "왜냐하면": "그런데도",
    "따라서": "그러나", "그러므로": "그렇지만", "덕분에": "와중에",
}
# flatten_affect: 생생한 정동 동사 → 평이 동사(글자수 근접).
_AFFECT = {
    "흐느꼈다": "말했다", "절규했다": "외쳤다", "떨렸다": "있었다",
    "북받쳤다": "올라왔다", "타올랐다": "생겼다", "사무쳤다": "남았다",
    "오열했다": "울었다", "치밀었다": "들었다",
}
# generic_swap: 구체 명사 → 일반 명사.
_GENERIC = {
    "손목시계": "물건", "골목길": "거리", "빗방울": "비", "담뱃불": "불빛",
    "찻잔": "잔", "편지지": "종이", "운동화": "신발", "유리창": "창문",
}
_AXES = ("break_causality", "flatten_affect", "generic_swap")


def _apply(text: str, table: Dict[str, str]) -> str:
    for k, v in table.items():
        text = text.replace(k, v)
    return text


def degrade(text: str, axes: Sequence[str]) -> str:
    """길이중립 축을 순서대로 적용한 열화본."""
    out = text
    if "break_causality" in axes:
        out = _apply(out, _CAUSAL)
    if "flatten_affect" in axes:
        out = _apply(out, _AFFECT)
    if "generic_swap" in axes:
        out = _apply(out, _GENERIC)
    return out


class P1GradedDegradation(BaseStrategy):
    name = "p1"
    description = ("등급화 열화쌍 15%. 열화 4축 중 텍스트 단축 축은 길이매칭+"
                   "break_causality(길이중립) 가중으로 V788 길이교란 재유입 차단.")
    AXES = _AXES

    def generate(self, n: int, *, sources: Sequence[str],
                 rng: Optional[_random.Random] = None,
                 axes: Optional[Sequence[str]] = None) -> List[RawPair]:
        """원본 sources에서 n개 열화쌍 생성. chosen=원본, rejected=열화본.

        - 길이중립 축만 사용(기본 전축). 열화가 원본과 동일(치환 0건)하면 폐기.
        - 길이는 본질적으로 보존되나, process_candidate가 토큰 5%/문자 8% 게이트로
          최종 판정한다(생성 계층은 파이프라인을 우회하지 않음).
        """
        rng = rng or _random.Random()
        axes = tuple(axes) if axes else self.AXES
        out: List[RawPair] = []
        if not sources:
            return out
        i = 0
        attempts = 0
        cap = max(n * 3, n + 1)
        while len(out) < n and attempts < cap:
            attempts += 1
            src = sources[i % len(sources)]
            i += 1
            if not src or len(src) < 80:
                continue
            deg = degrade(src, axes)
            if deg == src:           # 치환 0 → 열화 실패, 폐기
                continue
            k = len(out)
            out.append(RawPair(
                pair_id=f"p1_{k:04d}", work_id=f"p1_{k:04d}",
                strategy="p1", chosen_text=src, rejected_text=deg,
                meta={"axes": list(axes), "length_axis": False}))
        return out
