"""learning/pairing/length_match.py — I2 길이매칭 게이트.

Round#2 실증: sum-logp는 짧은 쪽을 기계적으로 선호(길이 confound). chosen/rejected의
토큰 수 차이를 강제로 좁혀 길이를 측정에서 중립화한다.
- token |Δ|/max ≤ 5%  : HARD (위반 → 폐기)
- char  |Δ|/max ≤ 8%  : SOFT (위반 → 플래그·카운트, 보존)
"""
from __future__ import annotations
from dataclasses import dataclass

TOKEN_HARD = 0.05
CHAR_SOFT = 0.08


@dataclass(frozen=True)
class LengthMatch:
    token_delta_ratio: float
    char_delta_ratio: float
    token_hard_ok: bool      # True면 채택 가능
    char_soft_ok: bool       # False면 soft 플래그(폐기는 아님)

    @property
    def accept(self) -> bool:
        return self.token_hard_ok


def _ratio(a: int, b: int) -> float:
    m = max(a, b)
    return abs(a - b) / m if m else 0.0


def length_match_decision(chosen_n_tokens: int, rejected_n_tokens: int,
                          chosen_chars: int, rejected_chars: int,
                          token_hard: float = TOKEN_HARD,
                          char_soft: float = CHAR_SOFT) -> LengthMatch:
    tdr = _ratio(int(chosen_n_tokens), int(rejected_n_tokens))
    cdr = _ratio(int(chosen_chars), int(rejected_chars))
    return LengthMatch(
        token_delta_ratio=tdr, char_delta_ratio=cdr,
        token_hard_ok=(tdr <= token_hard),
        char_soft_ok=(cdr <= char_soft),
    )
