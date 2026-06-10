# -*- coding: utf-8 -*-
"""Mode 2 실측 — 공식 on 실제 명작 (운수 좋은 날, 현진건 1924, PD)
[사전등록 — 실행 전 고정]
H1 (변별 타당성): 블라인드 주석 후 fitness(원본 씬) > fitness(열화 씬)이 11쌍 중 >=8 (sign test).
   열화 = 동일 사건·인물·길이 유지, 긴장/아이러니/감각 디테일만 제거.
H2 (복선 잔향): 설렁탕 plant 씬(scene1,2)이 payoff 씬(scene11)과의 임베딩 유사도에서
   비-plant 씬 9개 대비 상위 3위 안 (retrieval test).
실패 기준도 사전 고정: H1 <8/11 → fitness 변별력 불충분. H2 plant 미상위 → 잔향 공식 전제 약화.
"""
import sys, json, os, math, time, urllib.request
sys.path.insert(0, "/tmp/hub")
from literary_system.physics.fitness_score import NarrativeFitnessComponents, NarrativeFitnessScore
from literary_system.physics.coefficient_store import PhysicsCoefficientStore

KEY = os.environ["OPENAI_API_KEY"]
def chat(messages, model="gpt-4o-mini", temp=0.0, max_tok=900):
    body = json.dumps({"model": model, "temperature": temp, "max_tokens": max_tok,
                       "messages": messages}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r)["choices"][0]["message"]["content"]

def embed(texts):
    body = json.dumps({"model": "text-embedding-3-small", "input": texts}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/embeddings", data=body,
        headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=120) as r:
        return [d["embedding"] for d in json.load(r)["data"]]

scenes = [s.strip() for s in open("/tmp/mode2/unsu.txt", encoding="utf-8").read().split("###SCENE###")]
N = len(scenes)
print(f"[사전등록 확인] H1: A>B >=8/{N} | H2: plant(s1,s2) in top3 of sim-to-s11 | N={N}", flush=True)

# 1) 열화 생성 (B군) — 체크포인트
CK1="/tmp/mode2/degraded.json"
degraded = json.load(open(CK1)) if os.path.exists(CK1) else []
for i in range(len(degraded), N):
    s = scenes[i]
    out = chat([{"role": "system", "content": "당신은 텍스트 편집기다. 지시만 수행한다."},
        {"role": "user", "content": f"다음 장면을 같은 사건·인물 그대로, 원문과 거의 같은 분량(약 {len(s)}자)으로 다시 써라. 단, 긴장·아이러니·감정 대비·감각적 디테일·대사의 생동감을 모두 제거하고 밋밋한 서술체로 만들어라. 새 사건 추가 금지, 요약 금지.\n\n" + s}], temp=0.3, max_tok=1400)
    degraded.append(out.strip()); json.dump(degraded, open(CK1,"w"))
    print(f"  degraded {i+1}/{N} ({len(out)}c)", flush=True)

# 2) 블라인드 주석 (A/B 무작위 섞기, 조건 비공지)
import random
random.seed(42)
items = [("A", i, scenes[i]) for i in range(N)] + [("B", i, degraded[i]) for i in range(N)]
random.shuffle(items)
RUBRIC = """다음 장면 하나를 읽고 6개 지표를 0.0~1.0로 평가하라. JSON만 출력.
{"conflict_intensity": 갈등의 강도, "scene_energy_ratio": 장면의 에너지 보존(처짐 없이 밀도 유지), "motif_residue_score": 모티프/상징이 잔향을 남기는 정도, "curiosity_gradient": 다음이 궁금해지는 정도, "reader_surface_score": 문장 표면 품질(생동감·구체성), "arc_tension_score": 서사 긴장 기여도}"""
CK2="/tmp/mode2/ann.json"
ann_s = json.load(open(CK2)) if os.path.exists(CK2) else {}
for k, (cond, idx, text) in enumerate(items):
    key = f"{cond}{idx}"
    if key in ann_s: continue
    out = chat([{"role": "system", "content": "당신은 서사 분석가다. JSON만 출력한다."},
        {"role": "user", "content": RUBRIC + "\n\n[장면]\n" + text}], temp=0.0, max_tok=200)
    ann_s[key] = json.loads(out[out.find("{"):out.rfind("}")+1])
    json.dump(ann_s, open(CK2,"w"))
    print(f"  annotated {k+1}/{len(items)}", flush=True)
ann = {(c, i): ann_s[f"{c}{i}"] for c in "AB" for i in range(N)}

# 3) 공식 적용 (V745 실 공식)
fit = NarrativeFitnessScore(PhysicsCoefficientStore())
def F(j): return fit.calculate(NarrativeFitnessComponents(
    conflict_intensity=j["conflict_intensity"], scene_energy_ratio=j["scene_energy_ratio"],
    motif_residue_score=j["motif_residue_score"], curiosity_gradient=j["curiosity_gradient"],
    reader_surface_score=j["reader_surface_score"], arc_tension_score=j["arc_tension_score"]))
wins = 0; rows = []
for i in range(N):
    fa, fb = F(ann[("A", i)]), F(ann[("B", i)])
    wins += fa > fb; rows.append((i+1, fa, fb, fa - fb))
    print(f"  scene{i+1:2d}  원본 {fa:.2f}  열화 {fb:.2f}  Δ{fa-fb:+.2f}")
p = sum(math.comb(N, k) for k in range(wins, N+1)) / 2**N
print(f"\n=== H1 결과: 원본 우위 {wins}/{N} (사전등록 임계 8) | sign-test p={p:.4f} | {'PASS' if wins>=8 else 'FAIL'} ===")

# 4) H2 복선 잔향 (원본 11씬 임베딩, payoff=s11)
embs = embed(scenes)
def cos(a, b):
    num = sum(x*y for x, y in zip(a, b))
    return num / (math.sqrt(sum(x*x for x in a)) * math.sqrt(sum(y*y for y in b)))
sims = sorted(((cos(embs[i], embs[N-1]), i+1) for i in range(N-1)), reverse=True)
rank = {sc: r+1 for r, (s, sc) in enumerate(sims)}
print("sim-to-payoff(s11) 순위:", [(sc, f"{s:.3f}") for s, sc in sims])
h2 = min(rank[1], rank[2]) <= 3
print(f"=== H2 결과: plant 씬(s1 rank {rank[1]}, s2 rank {rank[2]}) | 임계 top3 | {'PASS' if h2 else 'FAIL'} ===")
json.dump({"rows": rows, "wins": wins, "p": p, "h2_ranks": {"s1": rank[1], "s2": rank[2]},
           "sims": [(sc, s) for s, sc in sims]}, open("/tmp/mode2/results.json", "w"))
