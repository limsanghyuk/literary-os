#!/usr/bin/env python3
# train_4070_p0.py - SP-E.9 clean per-token DPO round. chosen=coherent, rejected=causality-broken (length-matched).
# Primary metric = per-token win rate (sum reported only for contrast). Emits held logp ledger. ASCII-safe.
import argparse, json, os, sys
os.environ.setdefault("KMP_DUPLICATE_LIB_OK","TRUE"); os.environ.setdefault("MKL_THREADING_LAYER","GNU")
os.environ.setdefault("MKL_SERVICE_FORCE_INTEL","1"); os.environ.setdefault("OMP_NUM_THREADS","1")
if not os.environ.get("HF_TOKEN") and os.path.exists("hf_token.txt"):
    os.environ["HF_TOKEN"]=open("hf_token.txt",encoding="utf-8").read().strip()

def load(path):
    out=[]
    for l in open(path,encoding="utf-8"):
        l=l.strip()
        if not l: continue
        d=json.loads(l)
        out.append({"prompt":"", "chosen":" "+d["chosen"], "rejected":" "+d["rejected"]})
    return out

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--train",default="p0_train.jsonl"); ap.add_argument("--held",default="p0_held.jsonl")
    ap.add_argument("--base",default="meta-llama/Llama-3.1-8B-Instruct"); ap.add_argument("--out",default="./lora_p0")
    ap.add_argument("--rank",type=int,default=16); ap.add_argument("--epochs",type=float,default=2.0)
    ap.add_argument("--tau",type=float,default=0.50)
    a=ap.parse_args()
    print("[start] base=%s train=%s held=%s"%(a.base,a.train,a.held),flush=True)
    import importlib.util
    miss=[p for p in ["torch","transformers","datasets","trl","peft"] if importlib.util.find_spec(p) is None]
    if miss: print("[STOP] missing",miss,flush=True); sys.exit(2)
    import torch
    print("[preflight] GPU=%s | %s"%(torch.cuda.is_available(), torch.cuda.get_device_name(0) if torch.cuda.is_available() else "none"),flush=True)
    train=load(a.train); held=load(a.held)
    print("[data] train %d | held %d"%(len(train),len(held)),flush=True)
    import traceback
    try:
        print("[1/6] libs...",flush=True)
        from datasets import Dataset
        from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig
        from peft import LoraConfig, prepare_model_for_kbit_training
        from trl import DPOConfig, DPOTrainer
        torch.manual_seed(0)
        print("[2/6] model 4bit...",flush=True)
        tok=AutoTokenizer.from_pretrained(a.base)
        if tok.pad_token is None: tok.pad_token=tok.eos_token
        bnb=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_compute_dtype=torch.bfloat16,bnb_4bit_use_double_quant=True)
        model=AutoModelForCausalLM.from_pretrained(a.base,quantization_config=bnb,device_map="auto")
        model.config.use_cache=False; model=prepare_model_for_kbit_training(model,use_gradient_checkpointing=True)
        def score(m,p,c):
            ip=tok(p,return_tensors="pt").input_ids.to(m.device) if p else None
            ipc=tok(p+c,return_tensors="pt",truncation=True,max_length=384).input_ids.to(m.device)
            st=ip.shape[1]-1 if ip is not None else 0
            with torch.no_grad(): lg=m(ipc).logits[:,:-1,:].log_softmax(-1)
            sp=lg.gather(-1,ipc[:,1:].unsqueeze(-1)).squeeze(-1)[:,st:].sum().item()
            return sp, int(max(ipc.shape[1]-1-st,1))
        def measure(m,items):
            sw=ptw=ptm=0.0; led=[]
            for d in items:
                cs,cn=score(m,d["prompt"],d["chosen"]); rs,rn=score(m,d["prompt"],d["rejected"])
                sw+=1.0 if cs>rs else 0.0
                cpt,rpt=cs/cn,rs/rn
                ptw+=1.0 if cpt>rpt else 0.0; ptm+=(cpt-rpt)
                led.append({"chosen":{"sumlogp":cs,"n_tokens":cn},"rejected":{"sumlogp":rs,"n_tokens":rn}})
            n=len(items); return sw/n, ptw/n, ptm/n, led
        def kl(m,items):
            import contextlib; tot=0.0;k=0
            for d in items[:40]:
                ids=tok(d["chosen"],return_tensors="pt",truncation=True,max_length=320).input_ids.to(m.device)
                with torch.no_grad():
                    lp=m(ids).logits[0].log_softmax(-1)
                    with m.disable_adapter(): lr=m(ids).logits[0].log_softmax(-1)
                    tot+=(lp.exp()*(lp-lr)).sum(-1).mean().item(); k+=1
            return tot/max(k,1)
        print("[3/6] HELD W0 (before)...",flush=True)
        s0,p0,m0,_=measure(model,held); print("    sum W0=%.3f | per-token W0=%.3f | pt-margin %.4f"%(s0,p0,m0),flush=True)
        peft=LoraConfig(r=a.rank,lora_alpha=a.rank*2,lora_dropout=0.05,target_modules=["q_proj","k_proj","v_proj","o_proj"],task_type="CAUSAL_LM")
        cfg=DPOConfig(output_dir=a.out,per_device_train_batch_size=1,gradient_accumulation_steps=8,num_train_epochs=a.epochs,
                      learning_rate=5e-5,beta=0.1,max_length=384,bf16=True,gradient_checkpointing=True,logging_steps=10,save_strategy="no",report_to=[])
        print("[4/6] train DPO on %d..."%len(train),flush=True)
        tr=DPOTrainer(model=model,args=cfg,train_dataset=Dataset.from_list(train),processing_class=tok,peft_config=peft)
        tr.train(); tr.save_model(a.out)
        print("[5/6] HELD W1 (after)...",flush=True)
        s1,p1,m1,led1=measure(tr.model,held)
        print("[6/6] KL...",flush=True); klv=kl(tr.model,held)
        json.dump(led1,open("logp_p0_held_W1.jsonl","w"))
        dWpt=p1-p0
        print("",flush=True); print("===== SP-E.9 clean per-token round (length-matched P1) =====",flush=True)
        print("  HELD sum        W0->W1 : %.3f -> %.3f (dW_sum %+.3f)"%(s0,s1,s1-s0),flush=True)
        print("  HELD per-token  W0->W1 : %.3f -> %.3f (dW_pt %+.3f)"%(p0,p1,dWpt),flush=True)
        print("  HELD pt-margin  M0->M1 : %.4f -> %.4f (dM_pt %+.4f)"%(m0,m1,m1-m0),flush=True)
        print("  KL/token (policy||ref) : %.4f  (tau %.2f)"%(klv,a.tau),flush=True)
        c1=dWpt>0; c2=klv<=a.tau
        print("",flush=True)
        print("G_LOOPC_WINRATE(per-token): [%s] dW_pt>0  [%s] KL<=tau  [N/A] structural(c3)"%("PASS" if c1 else "FAIL","PASS" if c2 else "FAIL"),flush=True)
        print("VERDICT: "+("ADOPT-candidate (clean per-token dW>0!) — Round#2 길이착시 극복"if(c1 and c2)else"ROLLBACK (clean per-token dW<=0)"),flush=True)
        led={"ts":__import__("time").strftime("%Y-%m-%dT%H:%M:%S"),"strategy":"p1_causality_lenmatched",
             "train_n":len(train),"held_n":len(held),"sum_W0":round(s0,4),"sum_W1":round(s1,4),
             "pt_W0":round(p0,4),"pt_W1":round(p1,4),"dW_pt":round(dWpt,4),"KL":round(klv,4),"verdict":"ADOPT-candidate" if(c1 and c2)else"ROLLBACK"}
        open("rounds_ledger.jsonl","a",encoding="utf-8").write(json.dumps(led,ensure_ascii=False)+"\n")
        print("** Send this block to Claude. ledger appended. **",flush=True)
    except Exception:
        print("[ERROR] paste below:",flush=True); traceback.print_exc(); sys.exit(1)

if __name__=="__main__": main()
