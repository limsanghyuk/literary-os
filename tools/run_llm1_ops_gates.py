#!/usr/bin/env python3
"""run_llm1_ops_gates.py — G_LLM1_SAFETY + G_LLM1_COST (ADR-218, V758)."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from literary_system.critic.corpus_gate import CorpusGate
from literary_system.critic.llm1_metrics import LLM1Metrics


def run_safety(n_works: int = 205) -> dict:
    return CorpusGate().check(n_works)


def run_cost(metrics: LLM1Metrics | None = None) -> dict:
    return (metrics or LLM1Metrics()).check_budget()


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--json", action="store_true")
    ap.add_argument("--n-works", type=int, default=205); a = ap.parse_args()
    s, c = run_safety(a.n_works), run_cost()
    out = {"G_LLM1_SAFETY": s, "G_LLM1_COST": c, "passed": s["passed"] and c["passed"]}
    if a.json:
        print(json.dumps(out, ensure_ascii=False, indent=2))
    else:
        print(f"G_LLM1_SAFETY: {'PASS' if s['passed'] else 'FAIL'} (works {s['n_works']}≥{s['min']})")
        print(f"G_LLM1_COST: {'PASS' if c['passed'] else 'FAIL'} (${c['total_usd']}≤${c['hard']})")
    return 0 if out["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
