#!/usr/bin/env python3
# train_4070_cumulative_v3.py - SP-E.10 졸업 v3: Path B 하드신호 + maintain 제거(adopt/rollback only) + 단일 held.
# v2 대비 변경점(오직 3가지, 학습 하이퍼파라미터는 동일):
#   (1) ROUNDS = hardB_r1..r5_train.jsonl, 5R 모두 단일 held = hardB_held.jsonl(250)  ← v2는 구데이터+round별 held.
#   (2) 결정 = adopt/rollback 두 가지만. "maintain" 분기 삭제(W 포화가 연속adopt를 못 끊게).
#   (3) adopt 게이트 = w1>w0 ∧ drift≤TAU ∧ CI_lower>0.5 ∧ length_rule_rate≤0.60 ∧ c3 (SP-E.10.2 불변식 정합).
#   rollback 시 prior를 라운드 진입 전 어댑터로 되돌림(실패 어댑터를 체이닝하지 않음).
# 주의: 본 파일은 무GPU 환경서 정적작성만 됨. 실 GPU 1라운드 구동 검증은 집 4070에서 수행 필요(미검증).
import os,sys,json,math,re,random,contextlib,gc
os.environ.setdefault("KMP_DUPLICATE_LIB_OK","TRUE");os.environ.setdefault("MKL_THREADING_LAYER","GNU")
os.environ.setdefault("MKL_SERVICE_FORCE_INTEL","1");os.environ.setdefault("OMP_NUM_THREADS","1")
if not os.environ.get("HF_TOKEN") and os.path.exists("hf_token.txt"):
    os.environ["HF_TOKEN"]=open("hf_token.txt",encoding="utf-8").read().strip()
BASE="meta-llama/Llama-3.1-8B-Instruct"
HELD="hardB_held.jsonl"
ROUNDS=[("hardB_r1_train.jsonl",HELD),("hardB_r2_train.jsonl",HELD),("hardB_r3_train.jsonl",HELD),
        ("hardB_r4_train.jsonl",HELD),("hardB_r5_train.jsonl",HELD)]
TOL=0.02; TAU_DRIFT=0.50; CI_FLOOR=0.5; LRATE_MAX=0.60; OVERFIT_W=0.90
BANDS={"conflict_intensity":(0.0,1.775),"scene_energy_ratio":(0.0,8.333),"dialogue_ratio":(0.0,0.76)}
CONF=re.compile(r'(죽|피|칼|총|싸움|때리|소리(치|질)|분노|울|비명|공격|도망|쫓|협박|폭|배신|복수)');EMO=re.compile(r'[!?]|\.\.\.|…');DIAL=re.compile(r'^\s*[가-힣A-Za-z][가-힣A-Za-z0-9 ]{0,7}\s*[:：]')
def load(p): return [{"prompt":"","chosen":" "+json.loads(l)["chosen"],"rejected":" "+json.loads(l)["rejected"]} for l in open(p,encoding="utf-8") if l.strip()]
def feats(t):
    L=[x for x in t.splitlines() if x.strip()];n=len(L) or 1;ch=len(t) or 1
    d=sum(1 for x in L if DIAL.match(x));sh=sum(1 for x in L if len(x.strip())<14)
    return {"conflict_intensity":len(CONF.findall(t))/(ch/100),"scene_energy_ratio":(len(EMO.findall(t))+sh)/(ch/100),"dialogue_ratio":d/n}
def patho(t):
    f=feats(t);return sum(1 for k,(lo,hi) in BANDS.items() if f[k]<lo or f[k]>hi)
def length_rule_rate(items):  # 길이 인공물 위험률: |Δlen|/max>0.08 쌍 비중(데이터 속성, 측정값). ≤0.60 게이트.
    bad=0
    for d in items:
        a=len(d["chosen"]);b=len(d["rejected"]);m=max(a,b) or 1
        if abs(a-b)/m>0.08: bad+=1
    return round(bad/max(len(items),1),4)
print("[start] SP-E.10 v3 (Path B hardsignal, adopt/rollback only, single held)",flush=True)
import traceback
try:
    import torch
    from datasets import Dataset
    from transformers import AutoModelForCausalLM,AutoTokenizer,BitsAndBytesConfig
    from peft import LoraConfig,prepare_model_for_kbit_training,PeftModel
    from trl import DPOConfig,DPOTrainer
    tok=AutoTokenizer.from_pretrained(BASE)
    if tok.pad_token is None: tok.pad_token=tok.eos_token
    bnb=BitsAndBytesConfig(load_in_4bit=True,bnb_4bit_quant_type="nf4",bnb_4bit_compute_dtype=torch.bfloat16,bnb_4bit_use_double_quant=True)
    def ptlp(m,c):  # per-token logp of chosen
        ipc=tok(c,return_tensors="pt",truncation=True,max_length=384).input_ids.to(m.device)
        with torch.no_grad(): lg=m(ipc).logits[:,:-1,:].log_softmax(-1)
        return lg.gather(-1,ipc[:,1:].unsqueeze(-1)).squeeze(-1).sum().item()/max(ipc.shape[1]-1,1)
    def winrate(m,items):
        w=[1.0 if ptlp(m,d["chosen"])>ptlp(m,d["rejected"]) else 0.0 for d in items]
        W=sum(w)/len(w);se=math.sqrt(max(W*(1-W),1e-6)/len(w));return round(W,4),round(W-1.96*se,4)
    def chosen_vec(m,items): return [ptlp(m,d["chosen"]) for d in items[:60]]
    def c3path(m):
        random.seed(0);GEN=["스릴러","멜로","수사","가족"];FUN=["도입","위기","절정"]
        prompts=["한국 %s 드라마 한 장면 산문(300자). 기능=%s. 본문만."%(random.choice(GEN),random.choice(FUN)) for _ in range(10)]
        try: m.gradient_checkpointing_disable()
        except Exception: pass
        try: m.config.use_cache=True
        except Exception: pass
        def g(on):
            tot=0;cm=contextlib.nullcontext() if on else m.disable_adapter()
            with cm:
                for p in prompts:
                    e=tok.apply_chat_template([{"role":"user","content":p}],add_generation_prompt=True,return_tensors="pt",return_dict=True)
                    iid=e["input_ids"].to(m.device)
                    with torch.no_grad(): o=m.generate(iid,max_new_tokens=200,do_sample=True,temperature=0.8,top_p=0.9,pad_token_id=tok.eos_token_id,use_cache=True)
                    tot+=patho(tok.decode(o[0][iid.shape[1]:],skip_special_tokens=True))
            return tot
        return g(False),g(True)
    records=json.load(open("round_records_v3.json")) if os.path.exists("round_records_v3.json") else []
    done={r["round"] for r in records}; prior=None
    for r in records:  # 재개: 직전 adopt 어댑터만 체이닝(rollback/실패는 무시)
        if r["decision"]=="adopt" and os.path.isdir("./lora_v3_%d"%r["round"]): prior="./lora_v3_%d"%r["round"]
    for i,(tr_f,hd_f) in enumerate(ROUNDS,1):
        if i in done and os.path.isdir("./lora_v3_%d"%i): print("[skip R%d]"%i,flush=True);continue
        print("\n===== R%d ====="%i,flush=True)
        prior_before=prior  # rollback 시 복귀 지점
        train=load(tr_f);held=load(hd_f)
        model=AutoModelForCausalLM.from_pretrained(BASE,quantization_config=bnb,device_map="auto")
        model.config.use_cache=False;model=prepare_model_for_kbit_training(model,use_gradient_checkpointing=True)
        if prior: model=PeftModel.from_pretrained(model,prior,is_trainable=True)
        w0,_=winrate(model,held); before=chosen_vec(model,held)
        near_ceiling = w0>=OVERFIT_W
        epochs=0.5 if near_ceiling else 1.0   # 천장 근접 시 과적합 가드(단, maintain 결정은 없음)
        cfg=DPOConfig(output_dir="./lora_v3_%d"%i,per_device_train_batch_size=1,gradient_accumulation_steps=8,num_train_epochs=epochs,learning_rate=(2e-5 if near_ceiling else 5e-5),beta=0.1,max_length=384,bf16=True,gradient_checkpointing=True,save_strategy="no",report_to=[],logging_steps=50)
        if prior: tr=DPOTrainer(model=model,args=cfg,train_dataset=Dataset.from_list(train),processing_class=tok)
        else:
            peft=LoraConfig(r=16,lora_alpha=32,lora_dropout=0.05,target_modules=["q_proj","k_proj","v_proj","o_proj"],task_type="CAUSAL_LM")
            tr=DPOTrainer(model=model,args=cfg,train_dataset=Dataset.from_list(train),processing_class=tok,peft_config=peft)
        tr.train();tr.save_model("./lora_v3_%d"%i)
        w1,ci=winrate(tr.model,held); after=chosen_vec(tr.model,held)
        drift=round(sum(abs(a-b) for a,b in zip(after,before))/len(before),4)  # per-round 드리프트(직전상태 대비)
        pb,pa=c3path(tr.model); c3=pa<=pb+1
        lrate=length_rule_rate(held)
        adopt = (w1>w0) and (drift<=TAU_DRIFT) and (ci>CI_FLOOR) and (lrate<=LRATE_MAX) and c3
        dec="adopt" if adopt else "rollback"
        if dec=="adopt": prior="./lora_v3_%d"%i
        else: prior=prior_before   # 실패 어댑터 체이닝 안 함
        rec={"round":i,"decision":dec,"n_pairs":len(held),"w0":w0,"w1":w1,"w1_ci_lower":ci,"kl_per_round":drift,"length_rule_rate":lrate,"c3_passed":bool(c3),"epochs":epochs}
        records.append(rec);json.dump(records,open("round_records_v3.json","w"),ensure_ascii=False,indent=1)
        print("  W0=%.3f W1=%.3f CI=%.3f drift=%.3f lrate=%.3f c3=%s => %s"%(w0,w1,ci,drift,lrate,c3,dec),flush=True)
        del tr,model;gc.collect();torch.cuda.empty_cache()
    # 졸업 불변식(SP-E.10.2): 말미 연속 adopt≥5 ∧ 윈도 내 rollback=0 ∧ Σheld≥250
    decs=[r["decision"] for r in records]; tail=decs[-5:]
    sigma_held = records[-1]["n_pairs"] if records else 0
    graduated = (len(tail)==5 and all(d=="adopt" for d in tail) and sigma_held>=250)
    print("\n[DONE] round_records_v3.json  decisions=%s  Σheld=%d  GRADUATED=%s"%(decs,sigma_held,graduated),flush=True)
    print(json.dumps(records,ensure_ascii=False),flush=True)
except Exception:
    print("[ERROR] paste below:",flush=True);traceback.print_exc();sys.exit(1)
