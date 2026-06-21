"""P4 — ties/기타(혼합 10%). 거의 동률인 쌍으로 정책 분포를 매끄럽게(정칙화).

ties는 강한 선호 신호가 아니라 '동률 근방' 샘플이다. per-token 마진이 0 근처여야
정상이며, 큰 마진이 나오면 그 자체가 라벨 잡음 탐지 신호가 된다. 결정론적 약섭동
(공백·문장부호 정규화 수준)으로 chosen≈rejected를 만든다. LLM 불요.
"""
from __future__ import annotations
import random as _random
import re
from typing import List, Optional, Sequence

from .base import BaseStrategy, RawPair

_PUNCT = {"…": "...", "—": "-", "·": " ", "‧": " "}


def _perturb(text: str) -> str:
    """의미 불변 약섭동: 문장부호 정규화 + 이중공백 정리(길이 근접)."""
    out = text
    for k, v in _PUNCT.items():
        out = out.replace(k, v)
    out = re.sub(r"[ \t]{2,}", " ", out)
    return out


class P4Ties(BaseStrategy):
    name = "p4"
    description = ("ties/기타 10%. 동률 근방 쌍으로 분포 정칙화. per-token 마진 "
                   "≈0이 정상 — 큰 마진은 라벨잡음 탐지 신호.")

    def generate(self, n: int, *, sources: Sequence[str],
                 rng: Optional[_random.Random] = None) -> List[RawPair]:
        """원본에서 n개 동률쌍 생성. chosen=원본, rejected=약섭동본, meta.tie=True."""
        rng = rng or _random.Random()
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
            pert = _perturb(src)
            k = len(out)
            out.append(RawPair(
                pair_id=f"p4_{k:04d}", work_id=f"p4_{k:04d}",
                strategy="p4", chosen_text=src, rejected_text=pert,
                meta={"tie": True}))
        return out
