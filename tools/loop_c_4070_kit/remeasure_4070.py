#!/usr/bin/env python3
# remeasure_4070.py - 저장된 LoRA 어댑터로 held logp ledger 방출 + per-token 재측정 (학습 없음, 측정만).
# W0=어댑터 끔(base), W1=어댑터 켬. ref-win(=모델이 명작을 draft보다 위로 랭크) 비율을 sum vs per-token 비교.
import os, sys, json
os.environ.setdefault("KMP_DUPLICATE_LIB_OK", "TRUE"); os.environ.setdefault("MKL_THREADING_LAYER", "GNU")
os.environ.setdefault("MKL_SERVICE_FORCE_INTEL", "1"); os.environ.setdefault("OMP_NUM_THREADS", "1")
if not os.environ.get("HF_TOKEN") and os.path.exists("hf_token.txt"):
    os.environ["HF_TOKEN"] = open("hf_token.txt", encoding="utf-8").read().strip()

HELD = sys.argv[1] if len(sys.argv) > 1 else "pairs_held.jsonl"
BASE = "meta-llama/Llama-3.1-8B-Instruct"
ADAPTER = "./lora_out_4070"

def load_pairs(path):
    out = []
    for line in open(path, encoding="utf-8"):
        line = line.strip()
        if not line: continue
        d = json.loads(line)
        out.append({"prompt": "[%s %s] " % (d.get("genre",""), d.get("func","")),
                    "ref": " " + d["ref"], "draft": " " + d["draft"]})  # ref=chosen, draft=rejected
    return out

def per_token(side): return side["sumlogp"] / max(int(side["n_tokens"]), 1)
def ref_winrate(rows, scheme):
    s = 0.0
    for r in rows:
        d, f = r["draft"], r["ref"]
        da, ra = (d["sumlogp"], f["sumlogp"]) if scheme == "sum" else (per_token(d), per_token(f))
        if abs(da - ra) <= 1e-9: s += 0.5
        elif ra > da: s += 1.0                      # ref 승 = 모델이 명작 선호
    return round(s / len(rows), 4)
def margin_pt(rows):
    return round(sum(per_token(r["ref"]) - per_token(r["draft"]) for r in rows) / len(rows), 4)

print("[start] remeasure (no training). HELD=%s" % HELD, flush=True)
import traceback
try:
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
    from peft import PeftModel
    import contextlib
    data = load_pairs(HELD); print("[data] held %d pairs" % len(data), flush=True)
    tok = AutoTokenizer.from_pretrained(BASE)
    if tok.pad_token is None: tok.pad_token = tok.eos_token
    bnb = BitsAndBytesConfig(load_in_4bit=True, bnb_4bit_quant_type="nf4",
                             bnb_4bit_compute_dtype=torch.bfloat16, bnb_4bit_use_double_quant=True)
    print("[load] base 4bit + adapter...", flush=True)
    base = AutoModelForCausalLM.from_pretrained(BASE, quantization_config=bnb, device_map="auto")
    model = PeftModel.from_pretrained(base, ADAPTER); model.eval()

    def score(p, c):
        ip = tok(p, return_tensors="pt").input_ids.to(model.device)
        ipc = tok(p + c, return_tensors="pt", truncation=True, max_length=384).input_ids.to(model.device)
        n = int(max(ipc.shape[1] - ip.shape[1], 1))
        with torch.no_grad():
            lg = model(ipc).logits[:, :-1, :].log_softmax(-1)
        sp = lg.gather(-1, ipc[:, 1:].unsqueeze(-1)).squeeze(-1)[:, ip.shape[1]-1:].sum().item()
        return {"sumlogp": sp, "n_tokens": n}

    def ledger(adapter_on):
        rows = []
        cm = contextlib.nullcontext() if adapter_on else model.disable_adapter()
        with cm:
            for d in data:
                rows.append({"ref": score(d["prompt"], d["ref"]), "draft": score(d["prompt"], d["draft"])})
        return rows

    print("[measure] W0 (adapter OFF = base)...", flush=True); L0 = ledger(False)
    print("[measure] W1 (adapter ON = trained)...", flush=True); L1 = ledger(True)
    json.dump(L0, open("logp_held_W0.jsonl", "w")); json.dump(L1, open("logp_held_W1.jsonl", "w"))
    W0s, W0p = ref_winrate(L0, "sum"), ref_winrate(L0, "pertoken")
    W1s, W1p = ref_winrate(L1, "sum"), ref_winrate(L1, "pertoken")
    print("\n===== per-token RE-MEASUREMENT (ref-win = model prefers masterpiece) =====", flush=True)
    print("  sum (length-biased, Round#2): W0=%.3f -> W1=%.3f  (dW_sum %+.3f)" % (W0s, W1s, W1s-W0s), flush=True)
    print("  per-token (length-normalized): W0=%.3f -> W1=%.3f  (dW_pt %+.3f)" % (W0p, W1p, W1p-W0p), flush=True)
    print("  per-token margin(ref-draft) : M0=%+.4f -> M1=%+.4f  (dM_pt %+.4f)" % (margin_pt(L0), margin_pt(L1), margin_pt(L1)-margin_pt(L0)), flush=True)
    print("\nVERDICT: " + ("REAL learning (per-token dW>0)" if (W1p-W0p) > 0 else "LENGTH ARTIFACT (per-token dW<=0)"), flush=True)
except Exception:
    print("[ERROR] paste below to Claude:", flush=True); traceback.print_exc(); sys.exit(1)
