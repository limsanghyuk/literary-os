#!/usr/bin/env python3
"""run_one.py로 만든 <work>.run{1,2,3}.json (배치분할 시 <work>.run{N}.batch{start}.json 먼저 merge_batches.py로 병합)을
다수결+합의도로 집계해 <work>.majority.jsonl / <work>.contested.jsonl 생성.
사용: python merge_majority.py <work> [--runs 3]
"""
import json, collections, argparse

FIELDS = ["episode_role","tension_role","hook_flag","continuity_break","scene_blocks_need"]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("work"); ap.add_argument("--runs", type=int, default=3)
    a = ap.parse_args()
    runs = [{x["scene_no"]: x for x in json.load(open(f"{a.work}.run{i}.json", encoding='utf-8'))} for i in range(1, a.runs+1)]
    maj, contested = [], []
    for s in sorted(runs[0].keys()):
        rec = {"scene_no": s}; dis = []
        for f in FIELDS:
            votes = [r[s].get(f) for r in runs if s in r]
            c = collections.Counter(map(str, votes)); top, n = c.most_common(1)[0]
            if top in ("True","False"): top = (top == "True")
            rec[f] = top; rec[f+"_agree"] = n/len(votes)
            if n < len(votes): dis.append(f)
        rec["contested_fields"] = dis; maj.append(rec)
        if dis: contested.append({"scene_no": s, "fields": dis})
    with open(f"{a.work}.majority.jsonl","w",encoding='utf-8') as f:
        for r in maj: f.write(json.dumps(r, ensure_ascii=False)+"\n")
    with open(f"{a.work}.contested.jsonl","w",encoding='utf-8') as f:
        for r in contested: f.write(json.dumps(r, ensure_ascii=False)+"\n")
    print(f"{a.work}: {len(maj)}씬 다수결, GPT 3-run 내부 쟁점 {len(contested)}씬")

if __name__=="__main__": main()
