"""run_e4ext_exit_gate.py — E.4 확장 Exit (V778)."""
import sys
from literary_system.learning.e4ext_exit import run_e4ext_exit
if __name__ == "__main__":
    r = run_e4ext_exit()
    print(f"[{'PASS' if r['passed'] else 'FAIL'}] {r['gate']} — {r['phase']} ({r['n_pass']}/{r['n_total']})")
    for c in r["checkpoints"]:
        print(f"  {'OK' if c['passed'] else 'XX'} {c['name']}: {c['detail']}")
    print(f"  note: {r['note']}")
    sys.exit(0 if r["passed"] else 1)
