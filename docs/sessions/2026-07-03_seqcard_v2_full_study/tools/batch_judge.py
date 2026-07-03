import json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_full_study_v2_fixed import judge

work, path, run_idx, model, start, end = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4], int(sys.argv[5]), int(sys.argv[6])
K = os.environ["OPENAI_API_KEY"]
recs = [json.loads(l) for l in open(path, encoding='utf-8') if l.strip()]
batch = recs[start:end]
sc = [{"scene_no":r["scene_no"],"heading":r.get("heading",""),"title":r.get("title",""),"intent_gist":r.get("intent_gist","")} for r in batch]
out = judge(sc, work, model, K)
json.dump(out, open(f"{work}.run{run_idx}.batch{start}.json","w"), ensure_ascii=False)
print(f"batch {start}-{end}: {len(out)} labels")
