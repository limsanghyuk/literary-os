import os,re,json,glob,time
ROOT="/sessions/upbeat-focused-bohr/mnt/literary/corpus_ko"
TXT=ROOT+"/txt"; SCN=ROOT+"/scenes"; CHK=ROOT+"/chunks"
os.makedirs(SCN,exist_ok=True); os.makedirs(CHK,exist_ok=True)

NUM=[("S#n",re.compile(r'^\s*S\s*#\s*(\d{1,3})')),
     ("#n",re.compile(r'^\s*#\s*(\d{1,3})\b')),
     ("씬n",re.compile(r'^\s*씬\s*(\d{1,3})')),
     ("n.",re.compile(r'^\s*(\d{1,3})\s*\.(?!\d)')),
     ("n)",re.compile(r'^\s*(\d{1,3})\s*\)'))]
TIME=r'(낮|밤|아침|저녁|새벽|오후|오전|일몰|정오|해질|황혼|심야|동틀)'
INOUT=r'(실내|실외|내부|외부|INT|EXT|인서트|insert)'
slug=re.compile(r'^\s{0,8}.{0,42}('+TIME+r'|'+INOUT+r')\s*[.)\]]?\s*$')
slug_slash=re.compile(r'^\s{0,8}.{2,40}\s*/\s*.{0,15}('+TIME+r'|'+INOUT+r'|아침|저녁)')
prolog=re.compile(r'^\s*(프롤로그|에필로그|prologue|epilogue|타이틀|엔딩)\b',re.I)

def clean(t):
    t=t.replace('\x00','')
    return t

def split_numbered(lines,rx):
    idx=[]
    for i,L in enumerate(lines):
        m=rx.match(L)
        if m and len(L.strip())<=50:
            idx.append((i,int(m.group(1))))
    return idx

def split_slug(lines):
    idx=[]
    for i,L in enumerate(lines):
        s=L.strip()
        if not s: continue
        if prolog.match(s) or (len(s)<=42 and (slug.match(L) or slug_slash.match(L)) and len(s)>=3):
            idx.append((i,len(idx)+1))
    return idx

def build_scenes(text):
    lines=[l.rstrip() for l in text.splitlines()]
    # choose best numbered
    best=None;bc=4
    for name,rx in NUM:
        ix=split_numbered(lines,rx)
        if len(ix)>bc: bc=len(ix);best=(name,ix)
    method=None;cuts=None
    # 슬러그 후보도 미리 계산해 번호방식과 씬수 비교(허위 번호헤딩이 강슬러그를 이기는 버그 방지)
    slug_ix=split_slug(lines)
    if best and not (len(slug_ix)>=15 and len(slug_ix) > len(best[1])*2):
        method="num:"+best[0]; cuts=best[1]
    elif len(slug_ix)>=5:
        method="slug"; cuts=slug_ix
        if len(cuts)>220:
            HEAD=re.compile(r'(낮|밤|아침|저녁|새벽|오후|오전|일몰|심야|실내|실외|내부|외부|/|\s-\s)')
            ref=[(i,n) for (i,n) in cuts if HEAD.search(lines[i]) or len(lines[i].strip())<=14]
            if len(ref)>=5: cuts=ref; method+="+slug"
    else:
        ix=split_slug(lines)
        if len(ix)>=5: method="slug"; cuts=ix
    scenes=[]
    if cuts:
        for k,(i,_) in enumerate(cuts):
            j=cuts[k+1][0] if k+1<len(cuts) else len(lines)
            head=lines[i].strip()
            body="\n".join(lines[i+1:j]).strip()
            txt=(head+"\n"+body).strip()
            if len(txt)<5: continue
            scenes.append({"scene_no":k+1,"heading":head[:120],"text":txt})
    else:
        # fallback sliding pseudo-scenes ~ 28 non-empty lines
        method="fallback_block"
        buf=[];cnt=0;sn=0
        for L in lines:
            buf.append(L)
            if L.strip(): cnt+=1
            if cnt>=28:
                sn+=1; t="\n".join(buf).strip()
                if t: scenes.append({"scene_no":sn,"heading":"[block %d]"%sn,"text":t})
                buf=[];cnt=0
        if buf:
            t="\n".join(buf).strip()
            if len(t)>30: sn+=1; scenes.append({"scene_no":sn,"heading":"[block %d]"%sn,"text":t})
    return method,scenes

def sliding(text,size=1000,ov=200):
    text=re.sub(r'\n{3,}','\n\n',text)
    out=[];i=0;n=len(text);k=0
    while i<n:
        seg=text[i:i+size]
        if seg.strip(): out.append({"chunk_no":k,"text":seg.strip()}); k+=1
        i+=size-ov
    return out

files=sorted(f for f in os.listdir(TXT) if f.endswith('.txt') and os.path.getsize(TXT+"/"+f)>200)
stats={}
START=time.time()
for f in files:
    wid=f[:-4]
    text=clean(open(TXT+"/"+f,errors='ignore').read())
    method,scenes=build_scenes(text)
    # scene chunks (sub-split long scenes >1500)
    schunks=[]
    for s in scenes:
        if len(s["text"])<=1500: schunks.append({"work_id":wid,"scene_no":s["scene_no"],"heading":s["heading"],"text":s["text"]})
        else:
            for p,sub in enumerate(sliding(s["text"],1400,150)):
                schunks.append({"work_id":wid,"scene_no":s["scene_no"],"part":p,"heading":s["heading"],"text":sub["text"]})
    with open(SCN+"/"+wid+".jsonl","w") as o:
        for s in scenes: o.write(json.dumps({"work_id":wid,**s,"method":method},ensure_ascii=False)+"\n")
    with open(CHK+"/"+wid+".jsonl","w") as o:
        for c in schunks: o.write(json.dumps(c,ensure_ascii=False)+"\n")
        for c in sliding(text): o.write(json.dumps({"work_id":wid,"kind":"slide",**c},ensure_ascii=False)+"\n")
    stats[wid]=(method,len(scenes))
json.dump(stats,open(ROOT+"/parse_stats.json","w"),ensure_ascii=False,indent=0)
from collections import Counter
mc=Counter(m.split(':')[0] for m,_ in stats.values())
print("parsed files:",len(stats),"| methods:",dict(mc))
import statistics
sc=[n for _,n in stats.values()]
print("scenes/file min/med/max: %d/%d/%d  total scenes:%d"%(min(sc),int(statistics.median(sc)),max(sc),sum(sc)))
print("low(<8 scenes):",[w for w,(m,n) in stats.items() if n<8][:20])
print("elapsed %.1fs"%(time.time()-START))
