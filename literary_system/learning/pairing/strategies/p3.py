from .base import BaseStrategy
class P3AntiLLM(BaseStrategy):
    name = "p3"
    description = ("안티-LLM AI-vs-AI 주력 55%. show-don't-tell 기법쌍 = 1순위 강화후보. "
                   "sum 채점 시 8/8 거짓압승 → 길이매칭+per-token 강제 한묶음.")
