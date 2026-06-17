"""
finetune/train_local.py — 로컬 워크스테이션 QLoRA DPO 학습 (V767, ADR-227).

사용자 PC(RTX 4070 등)에서 직접 실행하는 스크립트. 샌드박스/CI에서는 실행 안 함.
무거운 의존(torch/peft/trl/bitsandbytes)은 main 내부에서만 import → 레포 import·테스트는 LLM-0 무부하.

usage:
    python -m literary_system.finetune.train_local \\
        --dataset dpo_pairs.jsonl --base meta-llama/Llama-3.2-3B --out ./lora_out --rank 16

LLM-0: 외부 LLM API 미호출. 로컬 가중치 학습만 수행.
"""
from __future__ import annotations
import argparse, sys


def preflight_or_exit(min_vram_gb: float = 12.0) -> None:
    """학습 전 로컬 사전조건 점검 — 실패 시 클라우드 폴백 안내 후 종료."""
    # _cli_demo: 사용자 PC 콘솔 출력(스크립트 전용, 프로덕션 로깅 아님)
    from literary_system.finetune.gpu_adapter import LocalPreflight
    pf = LocalPreflight(min_vram_gb=min_vram_gb).run()
    print(f"[preflight] {pf.detail}")
    if not pf.ok:
        print("[preflight] 로컬 학습 불가 → RunPod/Lambda 클라우드 사용 권장.", file=sys.stderr)
        sys.exit(2)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="로컬 QLoRA DPO 학습 (4070)")
    ap.add_argument("--dataset", required=True, help="DPO jsonl (prompt/chosen/rejected)")
    ap.add_argument("--base", default="meta-llama/Llama-3.2-3B")
    ap.add_argument("--out", default="./lora_out")
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--epochs", type=float, default=1.0)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--skip-preflight", action="store_true")
    args = ap.parse_args(argv)

    if not args.skip_preflight:
        preflight_or_exit()

    # ── 무거운 의존은 여기서만 import ────────────────────────────
    import torch
    from datasets import load_dataset
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import LoraConfig
    from trl import DPOTrainer, DPOConfig

    torch.manual_seed(args.seed)
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    tok = AutoTokenizer.from_pretrained(args.base)
    if tok.pad_token is None:
        tok.pad_token = tok.eos_token
    model = AutoModelForCausalLM.from_pretrained(args.base, quantization_config=bnb, device_map="auto")
    peft_cfg = LoraConfig(r=args.rank, lora_alpha=args.rank * 2, lora_dropout=0.05,
                          target_modules=["q_proj", "v_proj"], task_type="CAUSAL_LM")
    ds = load_dataset("json", data_files=args.dataset, split="train")
    cfg = DPOConfig(output_dir=args.out, num_train_epochs=args.epochs,
                    per_device_train_batch_size=1, gradient_accumulation_steps=8,
                    learning_rate=5e-5, bf16=True, seed=args.seed, logging_steps=5)
    trainer = DPOTrainer(model=model, args=cfg, train_dataset=ds,
                         processing_class=tok, peft_config=peft_cfg)
    # _cli_demo: 사용자 PC 콘솔 출력(스크립트 전용)
    trainer.train()
    trainer.save_model(args.out)
    print(f"[done] LoRA 어댑터 저장: {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
