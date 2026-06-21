"""P3 — 안티-LLM AI-vs-AI 주력(혼합 55%). chosen=show, rejected=tell.

포팅 출처: tools/loop_c_4070_kit/gen_p3.py. show-don't-tell 기법쌍이 1순위
강화후보. sum 채점 시 8/8 거짓압승(길이 인공물) → 길이매칭+per-token 강제.
"""
from __future__ import annotations
from .base import TwoVersionStrategy


class P3AntiLLM(TwoVersionStrategy):
    name = "p3"
    description = ("안티-LLM AI-vs-AI 주력 55%. show-don't-tell 기법쌍 = 1순위 강화후보. "
                   "sum 채점 시 8/8 거짓압승 → 길이매칭+per-token 강제 한묶음.")
    MARKER_A = "[SHOW]"
    MARKER_B = "[TELL]"
    SITUATIONS = ("재회", "배신 발각", "이별 직전", "비밀 누설", "대치", "고백",
                  "상실", "추격 후 정적")
    GENRES = ("스릴러", "멜로", "수사", "가족", "미스터리", "로맨스", "사극", "의학")
    FUNCTIONS = ("도입", "상승", "위기", "절정", "전환", "해소")
    MIN_LEN = 150

    def _prompt(self, situ: str, genre: str) -> str:
        return (
            "한국 %s 드라마 한 장면을 두 가지 버전으로 써라. 상황=%s.\n"
            "[SHOW] 보여주기(show, don't tell): 지문·행동·정적·감각으로 감정을 "
            "'드러내되 명시하지 마라'. 감정단어 금지.\n"
            "[TELL] 말하기(tell): 같은 상황을 평이하게, 감정을 직접 서술하고 설명조로.\n"
            "두 버전 모두 320~360자. 형식:\n[SHOW]\n<본문>\n[TELL]\n<본문>"
        ) % (genre, situ)
