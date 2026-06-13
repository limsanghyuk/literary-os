import os,glob,json,re
from collections import defaultdict,Counter
ROOT="/sessions/upbeat-focused-bohr/mnt/literary/corpus_ko"; SCN=ROOT+"/scenes"
SPEAK=re.compile(r'^\s*([가-힣]{2,4})\s*[:：]')   # dialogue cue: 이름:
STOP={"그리고","그러나","그래서","하지만","그때","이때","다시","사람","남자","여자","엄마","아빠","순간","갑자기","조용","모두","우리","당신","자막","소리","화면","목소리","내레이션"}
graph={"works":[],"nodes_scene":0,"edges_next":0,"characters":0,"edges_char_scene":0}
allnodes=[]; alledges=[]; charstats={}
for sf in sorted(glob.glob(SCN+"/*.jsonl")):
    w=os.path.basename(sf)[:-6]
    scenes=[json.loads(L) for L in open(sf,errors='ignore')]
    spk=defaultdict(set)
    NAMELINE=re.compile(r'^\s*([가-힣]{2,4})(\s*\([^)]{1,6}\))?\s*$')
    HEAD=re.compile(r'(낮|밤|아침|저녁|새벽|오후|오전|실내|실외|S\s*#|^#|^\d)')
    for s in scenes:
        sn=s["scene_no"]; L=s["text"].splitlines()
        for i,ln in enumerate(L):
            m=SPEAK.match(ln)
            if m and m.group(1) not in STOP: spk[m.group(1)].add(sn); continue
            tm=re.match(r'^\s*([가-힣]{2,5})(\t+|\s{2,})\S',ln)
            if tm and tm.group(1) not in STOP and not HEAD.search(ln): spk[tm.group(1)].add(sn); continue
            nm=NAMELINE.match(ln)
            if nm:
                cand=nm.group(1)
                if cand in STOP or HEAD.search(ln): continue
                nxt=next((L[j].strip() for j in range(i+1,min(i+3,len(L))) if L[j].strip()),"")
                if nxt and len(nxt)>=2 and not NAMELINE.match(nxt): spk[cand].add(sn)
    # keep characters appearing in >=3 scenes (filters noise)
    chars={c:sc for c,sc in spk.items() if len(sc)>=3}
    # NEXT edges
    for i in range(len(scenes)-1):
        alledges.append({"w":w,"type":"NEXT","s":scenes[i]["scene_no"],"t":scenes[i+1]["scene_no"]})
    graph["edges_next"]+=max(0,len(scenes)-1)
    graph["nodes_scene"]+=len(scenes)
    # char->scene edges + co-occurrence
    cs_edges=sum(len(v) for v in chars.values())
    graph["edges_char_scene"]+=cs_edges; graph["characters"]+=len(chars)
    cooc=Counter()
    scene_chars=defaultdict(list)
    for c,sset in chars.items():
        for sn in sset: scene_chars[sn].append(c)
    for sn,cl in scene_chars.items():
        for a in range(len(cl)):
            for b in range(a+1,len(cl)):
                cooc[tuple(sorted((cl[a],cl[b])))]+=1
    charstats[w]={"n_scenes":len(scenes),"characters":sorted(chars,key=lambda c:-len(chars[c]))[:12],
                  "n_characters":len(chars),
                  "top_pairs":[{"pair":list(p),"co":n} for p,n in cooc.most_common(8)]}
    graph["works"].append(w)
json.dump(charstats,open(ROOT+"/nkg.json","w"),ensure_ascii=False,indent=0)
json.dump(graph,open(ROOT+"/nkg_summary.json","w"),ensure_ascii=False,indent=1)
print("works:",len(charstats),"scene_nodes:",graph["nodes_scene"],"NEXT:",graph["edges_next"],
      "chars:",graph["characters"],"char-scene edges:",graph["edges_char_scene"])
# sample
for w in ["올드보이","기생충" if os.path.exists(SCN+"/기생충.jsonl") else "마더","곡성"]:
    if w in charstats: print(f"  {w}: chars={charstats[w]['characters'][:6]} pairs={[ (p['pair'],p['co']) for p in charstats[w]['top_pairs'][:3]]}")
