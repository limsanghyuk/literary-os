"""run_first_training.py — 4070 첫 학습 원샷 러너 (V771).
계획 출력 → Preflight → DPO 변환 → train_local 실행.
usage: python run_first_training.py --pairs dpo_pairs.jsonl [--base meta-llama/Llama-3.2-3B] [--smoke]
"""
import argparse, json, os, subprocess, sys
from literary_system.learning.first_training_kit import build_training_plan, prepare_dpo, make_smoke_dataset
from literary_system.finetune.gpu_adapter import LocalPreflight

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", required=True, help="개발자 dpo_pairs.jsonl(전체) 또는 스모크 파일")
    ap.add_argument("--base", default="meta-llama/Llama-3.2-3B")
    ap.add_argument("--out", default="./lora_out")
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--smoke", action="store_true", help="합성 스모크 데이터 생성 후 사용")
    ap.add_argument("--plan-only", action="store_true")
    a = ap.parse_args()

    if a.smoke:
        make_smoke_dataset(a.pairs, 4); print(f"[smoke] 합성 4쌍 → {a.pairs}")

    plan = build_training_plan(a.pairs, base_model=a.base, out_dir=a.out, rank=a.rank, epochs=a.epochs)
    print("=== 학습 계획 ===\n" + json.dumps(plan, ensure_ascii=False, indent=2))
    for w in plan["warnings"]: print("  ⚠ " + w)
    if a.plan_only: return 0

    pf = LocalPreflight().run(); print(f"[preflight] {pf.detail}")
    if not pf.ok:
        print("[중단] 로컬 사전조건 미충족 → 클라우드 권장.", file=sys.stderr); return 2

    os.makedirs(a.out, exist_ok=True)
    n = prepare_dpo(a.pairs, plan["dpo_dataset"]); print(f"[prepare] DPO 표준 {n}쌍 → {plan['dpo_dataset']}")
    print(f"[train] 실행: {plan['train_command']}")
    return subprocess.call(plan["train_command"].split())

if __name__ == "__main__":
    raise SystemExit(main())
