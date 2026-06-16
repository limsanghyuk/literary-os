import warnings,os; warnings.filterwarnings("ignore"); os.environ["TRANSFORMERS_VERBOSITY"]="error"
import torch; from transformers import AutoModelForCausalLM,AutoTokenizer
from datasets import Dataset; from trl import DPOConfig,DPOTrainer
torch.manual_seed(0)
M="sshleifer/tiny-gpt2"; tok=AutoTokenizer.from_pretrained(M); tok.pad_token=tok.eos_token
prompts=["스릴러 도입:","추격:","대치:","복도:","전화벨:","문이 열리자:","그림자:","마지막 계단:","빗속 골목:","정적:"]
ch=["그는 멈췄다. 숨을 골랐다. 다시 한 걸음.","심장이 뛰었다. 발소리. 침묵.","둘은 마주 섰다. 누구도 움직이지 않았다.","불빛이 깜빡였다. 그는 벽에 붙었다.","손이 떨렸다. 받지 않았다.","차가운 바람. 어둠뿐.","눈이 빛났다. 천천히.","한 칸. 또 한 칸.","빗물이 흘렀다. 그는 기다렸다.","시계만 돌았다."]
rj=["그는 빠르게 걸어가서 문을 열고 들어갔다.","그는 매우 빨리 뛰어서 도망쳤다.","두 사람은 서로 바라보며 이야기했다.","복도에는 불이 켜져 있었다.","전화가 와서 그는 받아서 통화했다.","문을 여니 방은 깨끗했다.","그림자가 있었지만 무섭지 않았다.","계단을 올라 방에 도착했다.","비가 와서 골목이 젖어 있었다.","조용했지만 곧 떠들기 시작했다."]
data=[{"prompt":p,"chosen":" "+c,"rejected":" "+r} for p,c,r in zip(prompts,ch,rj)]
def slp(m,p,c):
    a=tok(p,return_tensors="pt").input_ids; b=tok(p+c,return_tensors="pt").input_ids
    with torch.no_grad(): lg=m(b).logits[:,:-1,:].log_softmax(-1)
    return lg.gather(-1,b[:,1:].unsqueeze(-1)).squeeze(-1)[:,a.shape[1]-1:].sum().item()
def acc(m): return sum(1 for d in data if slp(m,d["prompt"],d["chosen"])>slp(m,d["prompt"],d["rejected"]))/len(data)
def margin(m): return sum(slp(m,d["prompt"],d["chosen"])-slp(m,d["prompt"],d["rejected"]) for d in data)/len(data)
m=AutoModelForCausalLM.from_pretrained(M)
b_acc,b_mar=acc(m),margin(m)
cfg=DPOConfig(output_dir="/tmp/o",per_device_train_batch_size=2,num_train_epochs=15,learning_rate=2e-3,beta=0.1,max_length=64,logging_steps=15,report_to=[],disable_tqdm=True,save_strategy="no",use_cpu=True,seed=0)
tr=DPOTrainer(model=m,ref_model=None,args=cfg,train_dataset=Dataset.from_list(data),processing_class=tok); tr.train()
a_acc,a_mar=acc(tr.model),margin(tr.model)
losses=[round(float(h["loss"]),4) for h in tr.state.log_history if "loss" in h]
last={k:h.get(k) for h in tr.state.log_history for k in ["rewards/margins","rewards/accuracies"] if k in h}
print("=== 진짜 DPO 학습 (Mock 아님 · tiny-gpt2 · CPU · 15ep) ===")
print("DPO 손실 궤적:", losses[0], "→", losses[-1], f"({len(losses)}점, 단조감소={all(losses[i]>=losses[i+1] for i in range(len(losses)-1))})")
print(f"선호정확도(chosen>rejected): {b_acc:.2f} → {a_acc:.2f}")
print(f"평균 로그확률 마진(chosen-rejected): {b_mar:.3f} → {a_mar:.3f}  (Δ {a_mar-b_mar:+.3f})")
print(f"DPO 내부 보상마진(최종): {last.get('rewards/margins')} | 보상정확도: {last.get('rewards/accuracies')}")
