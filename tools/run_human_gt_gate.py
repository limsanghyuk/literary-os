#!/usr/bin/env python3
"""run_human_gt_gate.py — G_HUMAN_GT_ALIGNMENT 게이트 (ADR-213, V750)
사용법: python tools/run_human_gt_gate.py [--json]
종료코드: 0 PASS / 1 FAIL"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))
from literary_system.validation.human_gt import run_g_human_gt_alignment
from literary_system.validation.human_gt_fixtures import (
    GT_FIXTURE_RECORDS, PANEL_FIXTURE_JUDGMENTS,
)

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    res = run_g_human_gt_alignment(GT_FIXTURE_RECORDS, PANEL_FIXTURE_JUDGMENTS)
    if args.json:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    else:
        print(f"G_HUMAN_GT_ALIGNMENT: {'PASS' if res['passed'] else 'FAIL'}")
        print(f"  α={res['alpha']} (min {res['alpha_min']}) | "
              f"패널일치={res['panel_alignment']} | n={res['n_records']}")
    return 0 if res["passed"] else 1

if __name__ == "__main__":
    sys.exit(main())
