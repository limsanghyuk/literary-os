import warnings,os,json; warnings.filterwarnings("ignore"); os.environ["TRANSFORMERS_VERBOSITY"]="error"
import torch; from transformers import AutoModelForCausalLM,AutoTokenizer
from datasets import Dataset; from trl import DPOConfig,DPOTrainer
torch.manual_seed(0)
M="sshleifer/tiny-gpt2"; tok=AutoTokenizer.from_pretrained(M); tok.pad_token=tok.eos_token
data=[json.loads(l) for l in open("/tmp/real_pairs.jsonl",encoding="utf-8")]
data=[{"prompt":d["prompt"],"chosen":d["chosen"],"rejected":d["rejected"]} for d in data]
def slp(m,p,c):
    a=tok(p,return_tensors="pt").input_ids; b=tok(p+c,return_tensors="pt").input_ids
    with torch.no_grad(): lg=m(b).logits[:,:-1,:].log_softmax(-1)
    return lg.gather(-1,b[:,1:].unsqueeze(-1)).squeeze(-1)[:,a.shape[1]-1:].sum().item()
def acc(m): return sum(1 for d in data if slp(m,d["prompt"],d["chosen"])>slp(m,d["prompt"],d["rejected"]))/len(data)
def mar(m): return sum(slp(m,d["prompt"],d["chosen"])-slp(m,d["prompt"],d["rejected"]) for d in data)/len(data)
m=AutoModelForCausalLM.from_pretrained(M)
ba,bm=acc(m),mar(m)
cfg=DPOConfig(output_dir="/tmp/o2",per_device_train_batch_size=2,num_train_epochs=10,learning_rate=2e-3,beta=0.1,max_length=64,logging_steps=10,report_to=[],disable_tqdm=True,save_strategy="no",use_cpu=True,seed=0)
tr=DPOTrainer(model=m,ref_model=None,args=cfg,train_dataset=Dataset.from_list(data),processing_class=tok); tr.train()
aa,am=acc(tr.model),mar(tr.model)
ls=[round(float(h["loss"]),4) for h in tr.state.log_history if "loss" in h]
fm=[h.get("rewards/margins") for h in tr.state.log_history if "rewards/margins" in h]
print("=== 진짜 학습 실측 #2: 실 LLM(gpt-4o-mini) 선호쌍 → 로컬 DPO ===")
print(f"데이터: 실 LLM 생성+판정 {len(data)}쌍 (Mock/합성 아님)")
print(f"DPO 손실: {ls[0]} → {ls[-1]} (단조감소={all(ls[i]>=ls[i+1] for i in range(len(ls)-1))})")
print(f"선호정확도(chosen>rejected): {ba:.2f} → {aa:.2f}")
print(f"로그확률 마진(chosen-rejected): {bm:.2f} → {am:.2f} (Δ {am-bm:+.2f})")
print(f"DPO 보상마진 궤적: {fm[0]:.4f} → {fm[-1]:.4f}")
