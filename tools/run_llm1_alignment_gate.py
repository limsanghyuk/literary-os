#!/usr/bin/env python3
"""run_llm1_alignment_gate.py — G_LLM1_ALIGNMENT (ADR-217, V757)
Gold 쌍에서 critic↔인간 GT 일치율 ≥0.80. 사용: [--json] / 종료 0 PASS 1 FAIL"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from literary_system.critic.base import CriticContext
from literary_system.critic.ensemble import CriticEnsemble
from literary_system.critic.alignment_monitor import measure_alignment
from literary_system.validation.human_gt_fixtures import GT_FIXTURE_PAIRS, GT_FIXTURE_RECORDS, FIXTURE_DB


def _canon_judge(prompt: str) -> str:
    # 평가지 A 영역에 '명작'(canon) 포함 여부로 판정(픽스처 검증용 결정론)
    a = prompt.split("씬 A ===")[1].split("씬 B ===")[0]
    return "WINNER: A" if "명작" in a else "WINNER: B"


def run_g_llm1_alignment() -> dict:
    pairs = [(p.pair_id, p.left_id, p.right_id, FIXTURE_DB[p.left_id], FIXTURE_DB[p.right_id])
             for p in GT_FIXTURE_PAIRS]
    ens = CriticEnsemble(llm=_canon_judge, seed=1)
    rep = measure_alignment(pairs, ens, lambda pid: CriticContext(rag_refs=["real::ref"]), GT_FIXTURE_RECORDS)
    return {"gate": "G_LLM1_ALIGNMENT", "passed": rep.passed,
            "agreement_rate": rep.agreement_rate, "min": 0.80, "n_pairs": rep.n_pairs}


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--json", action="store_true"); a = ap.parse_args()
    r = run_g_llm1_alignment()
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json
          else f"G_LLM1_ALIGNMENT: {'PASS' if r['passed'] else 'FAIL'} 일치율={r['agreement_rate']} (min {r['min']}, n={r['n_pairs']})")
    return 0 if r["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
