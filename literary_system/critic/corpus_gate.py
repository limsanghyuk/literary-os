"""critic/corpus_gate.py — G_LLM1_SAFETY (V758, ADR-218): 코퍼스<50편 시 critic 차단."""
from __future__ import annotations
from dataclasses import dataclass

MIN_CORPUS_WORKS: int = 50


@dataclass(frozen=True)
class CorpusGate:
    min_works: int = MIN_CORPUS_WORKS

    def is_critic_allowed(self, n_works: int) -> bool:
        return n_works >= self.min_works

    def check(self, n_works: int) -> dict:
        ok = n_works >= self.min_works
        return {"gate": "G_LLM1_SAFETY", "passed": ok, "n_works": n_works,
                "min": self.min_works, "critic_allowed": ok}
