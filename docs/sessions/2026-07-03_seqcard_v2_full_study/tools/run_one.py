#!/usr/bin/env python3
import json, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from run_full_study_v2_fixed import judge

def main():
    work, path, run_idx, model = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]
    K = os.environ["OPENAI_API_KEY"]
    sc = [{"scene_no":r["scene_no"],"heading":r.get("heading",""),"title":r.get("title",""),"intent_gist":r.get("intent_gist","")}
          for r in (json.loads(l) for l in open(path, encoding='utf-8') if l.strip())]
    try:
        out = judge(sc, work, model, K)
        json.dump(out, open(f"{work}.run{run_idx}.json","w"), ensure_ascii=False)
        print(f"{work} run{run_idx}: OK {len(out)} labels")
    except Exception as e:
        print(f"{work} run{run_idx}: FAIL {repr(e)}")
        raise

if __name__=="__main__": main()
