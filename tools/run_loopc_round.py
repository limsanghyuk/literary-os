"""run_loopc_round.py — loop-C 폐회로 1라운드 CLI (V774).
계획만: python tools/run_loopc_round.py --pairs dpo.jsonl
실측판정: ... --w1 0.63 [--kl 0.05 --r-before 0.7 --r-after 0.72]
"""
import argparse, json, sys
from literary_system.learning.loopc_closure import LoopCClosure
from literary_system.learning.pareto_router import TrainingMode

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True)
    ap.add_argument("--mode", default="LOCAL", choices=["LOCAL","CLOUD","HYBRID","AUTO"])
    ap.add_argument("--base", default="meta-llama/Llama-3.2-3B")
    ap.add_argument("--round", type=int, default=1)
    ap.add_argument("--w1", type=float, default=None, help="학습후 재측정 승률(있으면 수용판정)")
    ap.add_argument("--kl", type=float, default=0.0)
    ap.add_argument("--r-before", type=float, default=None)
    ap.add_argument("--r-after", type=float, default=None)
    ap.add_argument("--target", type=float, default=0.60)
    a = ap.parse_args()
    c = LoopCClosure(mode=TrainingMode[a.mode], target_w=a.target, base_model=a.base)
    rep = c.run_round(a.pairs, round_idx=a.round, measured_w1=a.w1,
                      kl=a.kl, r_before=a.r_before, r_after=a.r_after)
    print(json.dumps(rep.to_dict(), ensure_ascii=False, indent=2))
    print("\n>>", rep.summary)
    return 0 if (rep.gate is None or rep.gate.passed) else 1

if __name__ == "__main__":
    sys.exit(main())
