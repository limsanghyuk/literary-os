import json
rows=[json.loads(l) for l in open("results.jsonl")]
axes=["consistency","causality","character","emotion","immersion"]
wins={"A":0,"B":0}; tA=[];tB=[];lA=[];lB=[]
pa={"A":{k:[] for k in axes},"B":{k:[] for k in axes}}
for r in rows:
    wins[r["winner"]]+=1
    tA.append(sum(r["score_A"].values())); tB.append(sum(r["score_B"].values()))
    lA.append(r["len_A"]); lB.append(r["len_B"])
    for k in axes: pa["A"][k].append(r["score_A"][k]); pa["B"][k].append(r["score_B"][k])
m=lambda x: round(sum(x)/len(x),2) if x else 0
print("N=",len(rows)," wins A(순수)=%d B(구조)=%d"%(wins["A"],wins["B"]))
print("총점평균 A=%.1f B=%.1f  길이평균 A=%d B=%d"%(m(tA),m(tB),m(lA),m(lB)))
for k in axes: print("  %-12s A=%.2f B=%.2f"%(k,m(pa["A"][k]),m(pa["B"][k])))
