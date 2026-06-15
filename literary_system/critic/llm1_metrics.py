"""critic/llm1_metrics.py — LLM-1 비용·호출 추적 + G_LLM1_COST (V758, ADR-218)."""
from __future__ import annotations
import time
from dataclasses import dataclass, field
from typing import List, Tuple

COST_HARD_USD: float = 50.0      # 월 hard
COST_SOFT_USD: float = 30.0      # 월 soft
# (input, output) per 1M tokens
_PRICES = {
    "gpt-4o-mini": (0.15, 0.60), "gpt-4o": (2.5, 10.0),
    "gpt-5": (1.25, 10.0), "gpt-5-mini": (0.25, 2.0), "gpt-5-chat-latest": (1.25, 10.0),
}


@dataclass(frozen=True)
class CallRecord:
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float
    ts: float = field(default_factory=time.time)


class LLM1Metrics:
    """critic LLM 호출 비용/횟수 누적. 5축 측정의 '비용'·'호출률' 원천."""
    def __init__(self) -> None:
        self._calls: List[CallRecord] = []

    def record(self, model: str, tokens_in: int, tokens_out: int) -> float:
        pi, po = _PRICES.get(model, (0.15, 0.60))
        cost = tokens_in * pi / 1e6 + tokens_out * po / 1e6
        self._calls.append(CallRecord(model, tokens_in, tokens_out, round(cost, 6)))
        return cost

    @property
    def total_cost(self) -> float:
        return round(sum(c.cost_usd for c in self._calls), 6)

    @property
    def n_calls(self) -> int:
        return len(self._calls)

    def check_budget(self) -> dict:
        t = self.total_cost
        return {"gate": "G_LLM1_COST", "passed": t <= COST_HARD_USD,
                "total_usd": t, "hard": COST_HARD_USD, "soft": COST_SOFT_USD,
                "within_soft": t <= COST_SOFT_USD, "n_calls": self.n_calls}
