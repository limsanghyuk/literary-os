#!/usr/bin/env python3
# train_4070.py v3 - QLoRA DPO with HELD-OUT dW + KL proxy (G_LOOPC_WINRATE-ready). ASCII-safe.
import argparse, json, os, sys


def preflight():
    import importlib.util
    miss = [p for p in ["torch", "transformers", "datasets", "trl", "peft"]
            if importlib.util.find_spec(p) is None]
    if miss:
        print("[STOP] missing packages: {}".format(miss), flush=True); sys.exit(2)
    import torch
    gpu = torch.cuda.is_available()
    name = torch.cuda.get_device_name(0) if gpu else "none"
    vram = round(torch.cuda.get_device_properties(0).total_memory / 1024**3, 1) if gpu else 0
    print("[preflight] GPU={} | {} | VRAM={}GB".format(gpu, name, vram), flush=True)
    if not gpu:
        print("[STOP] no CUDA GPU", flush=True); sys.exit(2)


def load_pairs(path):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line:
            continue
        d = json.loads(line)
        draft, ref, w = d["draft"], d["ref"], d.get("winner", "ref")
        chosen, rejected = (draft, ref) if w == "draft" else (ref, draft)
        out.append({"prompt": "[%s %s] " % (d.get("genre", ""), d.get("func", "")),
                    "chosen": " " + chosen, "rejected": " " + rejected})
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--train", default="pairs_train.jsonl")
    ap.add_argument("--held", default="pairs_held.jsonl")
    ap.add_argument("--base", default="meta-llama/Llama-3.1-8B-Instruct")
    ap.add_argument("--out", default="./lora_out_4070")
    ap.add_argument("--rank", type=int, default=16)
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--tau", type=float, default=0.50)   # KL/token guard
    a = ap.parse_args()
    print("[start] base={} train={} held={}".format(a.base, a.train, a.held), flush=True)
    preflight()
    train = load_pairs(a.train)
    held = load_pairs(a.held) if os.path.exists(a.held) else train
    print("[data] train {} pairs | held {} pairs".format(len(train), len(held)), flush=True)

    import traceback
    try:
        print("[1/6] loading libraries...", flush=True)
        import torch
        from datasets import Dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import LoraConfig, prepare_model_for_kbit_training
        from trl import DPOConfig, DPOTrainer
        torch.manual_seed(0)

        print("[2/6] loading model (4bit)...", flush=True)
        tok = AutoTokenizer.from_pretrained(a.base)
        if tok.pad_token is None:
            tok.pad_token = tok.eos_token
        bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                                 bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
        model = AutoModelForCausalLM.from_pretrained(a.base, quantization_config=bnb, device_map="auto")
        model.config.use_cache = False
        model = prepare_model_for_kbit_training(model, use_gradient_checkpointing=True)

        def slp(m, p, c):
            ip = tok(p, return_tensors="pt").input_ids.to(m.device)
            ipc = tok(p + c, return_tensors="pt", truncation=True, max_length=384).input_ids.to(m.device)
            with torch.no_grad():
                lg = m(ipc).logits[:, :-1, :].log_softmax(-1)
            return lg.gather(-1, ipc[:, 1:].unsqueeze(-1)).squeeze(-1)[:, ip.shape[1]-1:].sum().item()

        def measure(m, items):
            wins, marg = 0, 0.0
            for d in items:
                sc = slp(m, d["prompt"], d["chosen"]); sr = slp(m, d["prompt"], d["rejected"])
                wins += 1 if sc > sr else 0; marg += (sc - sr)
            return wins / len(items), marg / len(items)

        def kl_proxy(m, items):
            # mean per-token KL(policy||reference) on held chosen text; reference = adapter disabled
            import torch
            tot, n = 0.0, 0
            for d in items[:40]:
                ids = tok(d["prompt"] + d["chosen"], return_tensors="pt", truncation=True, max_length=320).input_ids.to(m.device)
                with torch.no_grad():
                    lp = m(ids).logits[0].log_softmax(-1)
                    with m.disable_adapter():
                        lr = m(ids).logits[0].log_softmax(-1)
                    kl = (lp.exp() * (lp - lr)).sum(-1).mean().item()
                tot += kl; n += 1
            return tot / max(n, 1)

        print("[3/6] measuring W0/M0 on HELD (before)...", flush=True)
        before_acc, before_mrg = measure(model, held)
        print("    HELD W0(acc)={:.3f} | M0(margin)={:+.2f}".format(before_acc, before_mrg), flush=True)

        peft_cfg = LoraConfig(r=a.rank, lora_alpha=a.rank * 2, lora_dropout=0.05,
                              target_modules=["q_proj", "k_proj", "v_proj", "o_proj"], task_type="CAUSAL_LM")
        cfg = DPOConfig(output_dir=a.out, per_device_train_batch_size=1, gradient_accumulation_steps=8,
                        num_train_epochs=a.epochs, learning_rate=5e-5, beta=0.1, max_length=384,
                        bf16=True, gradient_checkpointing=True, logging_steps=10, save_strategy="no", report_to=[])

        print("[4/6] training (QLoRA DPO on {} pairs)...".format(len(train)), flush=True)
        tr = DPOTrainer(model=model, args=cfg, train_dataset=Dataset.from_list(train),
                        processing_class=tok, peft_config=peft_cfg)
        tr.train(); tr.save_model(a.out)

        print("[5/6] measuring W1/M1 on HELD (after)...", flush=True)
        after_acc, after_mrg = measure(tr.model, held)

        print("[6/6] measuring KL proxy on HELD...", flush=True)
        kl = kl_proxy(tr.model, held)

        dW = after_acc - before_acc; dM = after_mrg - before_mrg
        print("", flush=True)
        print("===== 4070 real QLoRA DPO - HELD-OUT result =====", flush=True)
        print("model {} | train {} | held {}".format(a.base, len(train), len(held)), flush=True)
        print("  HELD abs-pref-acc  W0->W1 : {:.3f} -> {:.3f}  (dW {:+.3f})".format(before_acc, after_acc, dW), flush=True)
        print("  HELD reward-margin M0->M1 : {:+.2f} -> {:+.2f}  (dM {:+.2f})".format(before_mrg, after_mrg, dM), flush=True)
        print("  KL/token (policy||ref)    : {:.4f}   (tau guard = {:.2f})".format(kl, a.tau), flush=True)
        print("LoRA adapter saved: {}".format(a.out), flush=True)
        c1 = dW > 0
        c2 = kl <= a.tau
        print("", flush=True)
        print("G_LOOPC_WINRATE (held):", flush=True)
        print("  [{}] dW>0  (held generalization)".format("PASS" if c1 else "FAIL"), flush=True)
        print("  [{}] KL<=tau  (no reward-hacking drift)".format("PASS" if c2 else "FAIL"), flush=True)
        print("  [N/A] structural non-regression (run in literary_system gate)", flush=True)
        print("VERDICT: " + ("ADOPT-candidate (dW>0 & KL ok) -> run structural gate" if (c1 and c2)
                             else "ROLLBACK (held dW<=0 or KL drift)"), flush=True)
        print("** Send this whole block to Claude. **", flush=True)
        import time as _t
        ledger = {"ts": _t.strftime("%Y-%m-%dT%H:%M:%S"), "base": a.base,
                  "train_n": len(train), "held_n": len(held),
                  "W0": round(before_acc, 4), "W1": round(after_acc, 4), "dW": round(dW, 4),
                  "M0": round(before_mrg, 2), "M1": round(after_mrg, 2), "dM": round(dM, 2),
                  "KL": round(kl, 4), "tau": a.tau, "adapter": os.path.abspath(a.out),
                  "verdict": "ADOPT-candidate" if (c1 and c2) else "ROLLBACK"}
        with open("rounds_ledger.jsonl", "a", encoding="utf-8") as _L:
            _L.write(json.dumps(ledger, ensure_ascii=False) + "\n")
        print("[ledger] round appended -> rounds_ledger.jsonl", flush=True)
    except Exception:
        print("", flush=True)
        print("[ERROR] paste the FULL message below to Claude:", flush=True)
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
