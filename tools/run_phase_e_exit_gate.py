"""run_phase_e_exit_gate.py — E.5 Phase E LLM-1 전이 Exit (V766)."""
import sys
from literary_system.learning.phase_e_exit import run_phase_e_exit
if __name__ == "__main__":
    r = run_phase_e_exit()
    mark = "PASS" if r["passed"] else "FAIL"
    print(f"[{mark}] {r['gate']} — {r['phase']} ({r['n_pass']}/{r['n_total']})")
    for c in r["checkpoints"]:
        print(f"  {'OK' if c['passed'] else 'XX'} {c['name']}: {c['detail']}")
    print(f"  note: {r['note']}")
    sys.exit(0 if r["passed"] else 1)
