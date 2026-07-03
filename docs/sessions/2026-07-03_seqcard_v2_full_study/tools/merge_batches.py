#!/usr/bin/env python3
"""batch_judge.py로 나온 <work>.run{N}.batch{start}.json 조각들을 <work>.run{N}.json으로 병합.
사용: python merge_batches.py <work> <run_idx> <start1> <start2> ...
예:   python merge_batches.py 밀회_01 3 0 35 70
"""
import json, sys

work, run_idx = sys.argv[1], sys.argv[2]
starts = [int(x) for x in sys.argv[3:]]
out = []
for s in starts:
    out += json.load(open(f"{work}.run{run_idx}.batch{s}.json", encoding='utf-8'))
out.sort(key=lambda x: x["scene_no"])
json.dump(out, open(f"{work}.run{run_idx}.json","w"), ensure_ascii=False)
print(len(out), "병합 완료 →", f"{work}.run{run_idx}.json")
