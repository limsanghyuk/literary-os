"""P2 — on-policy 품질쌍(혼합 20%). chosen=구체/고유 디테일, rejected=평이/상투.

포팅 출처: tools/loop_c_4070_kit/gen_p2.py. 현 정책 생성물 vs 개선 후보를
'구체성(GOOD) vs 상투(WEAK)' 동상황·동목표길이 2버전으로 합성.
"""
from __future__ import annotations
from .base import TwoVersionStrategy


class P2OnPolicy(TwoVersionStrategy):
    name = "p2"
    description = ("on-policy 20%. 현 정책 생성물 vs 개선 후보. "
                   "구체/고유 디테일(GOOD) vs 평이/상투(WEAK) 동상황·동길이 합성.")
    MARKER_A = "[GOOD]"
    MARKER_B = "[WEAK]"
    SITUATIONS = ("재회", "갈등 폭발", "결심", "비밀 발각", "작별", "추궁",
                  "위로", "사고 직후")
    GENRES = ("스릴러", "멜로", "수사", "가족", "미스터리", "로맨스", "사극",
              "의학", "코미디")
    MIN_LEN = 150

    def _prompt(self, situ: str, genre: str) -> str:
        return (
            "한국 %s 드라마 한 장면을 두 버전으로. 상황=%s.\n"
            "[GOOD] 구체적·고유 디테일(특정 사물/행동/감각/장소 디테일), 상투어 회피, "
            "인물 고유성.\n"
            "[WEAK] 평이·상투(뻔한 표현, 일반적 묘사, 클리셰), 디테일 없음.\n"
            "두 버전 모두 320~360자, 지문+대사. 형식:\n[GOOD]\n<본문>\n[WEAK]\n<본문>"
        ) % (genre, situ)
