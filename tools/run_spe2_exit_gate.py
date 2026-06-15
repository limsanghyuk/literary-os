#!/usr/bin/env python3
"""run_spe2_exit_gate.py — SP-E.2 Exit (ADR-221, V761) = Phase E.2 완료 판정."""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from literary_system.critic.spe2_exit import run_spe2_exit


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--json", action="store_true"); a = ap.parse_args()
    r = run_spe2_exit()
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"SP-E2-EXIT ({r['phase']}): {'PASS' if r['passed'] else 'FAIL'} {r['n_pass']}/{r['n_total']}")
        for cp in r["checkpoints"]:
            print(f"  [{'+' if cp['passed'] else 'x'}] {cp['name']}: {cp['detail']}")
    return 0 if r["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
