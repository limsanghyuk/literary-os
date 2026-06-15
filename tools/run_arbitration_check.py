#!/usr/bin/env python3
"""run_arbitration_check.py — Arbitration Protocol v1 자가검증 (ADR-219, V759)."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from literary_system.critic.arbitration import arbitrate, classify


def run_check() -> dict:
    items = [
        {"pair_id": "p1", "formula_winner": "a", "critic_winner": "a"},                       # agree
        {"pair_id": "p2", "formula_winner": "a", "critic_winner": "b"},                       # pending
        {"pair_id": "p3", "formula_winner": "a", "critic_winner": "b", "human_winner": "b"},  # formula_defect
        {"pair_id": "p4", "formula_winner": "a", "critic_winner": "b", "human_winner": "a"},  # critic_defect
        {"pair_id": "p5", "formula_winner": "a", "critic_winner": "b", "human_winner": "tie"},# genuine_ambiguous
    ]
    res = arbitrate(items)
    expect = {"agree": 1, "pending": 1, "formula_defect": 1, "critic_defect": 1, "genuine_ambiguous": 1}
    ok = res["counts"] == expect and res["disagreement_queue"] == ["p2"]
    return {"protocol": "Arbitration v1", "passed": ok,
            "counts": res["counts"], "queue": res["disagreement_queue"]}


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--json", action="store_true"); a = ap.parse_args()
    r = run_check()
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json
          else f"Arbitration v1: {'PASS' if r['passed'] else 'FAIL'} {r['counts']} 큐={r['queue']}")
    return 0 if r["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
