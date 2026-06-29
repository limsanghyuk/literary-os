# -*- coding: utf-8 -*-
"""씬 분할 결함 스캐너 + 재파서 (verbatim 비커밋 — 로컬 db에서만 실행).
결함 신호: 저장 씬수 << 헤딩 최대번호 + 갭. 거짓양성=최대#>200(연도/타임코드).
복구: 원본 txt를 올바른 마커로 재파싱(예: 천만번사랑해 = 소문자 's#N.').
"""
import glob,re,os,json
def scan(scenes_dir):
    hn=re.compile(r'"heading"\s*:\s*"\s*[Ss]?#?\s*(\d+)')
    rep=[]
    from collections import defaultdict
    works=defaultdict(list)
    for f in glob.glob(f'{scenes_dir}/*.jsonl'):
        m=re.match(r'^(.*?)_(\d+)$',os.path.basename(f)[:-6])
        if m: works[m.group(1)].append(f)
    for w,fs in works.items():
        if len(fs)<8: continue
        for f in fs:
            nums=[int(x.group(1)) for x in (hn.search(l) for l in open(f,encoding='utf-8')) if x]
            if len(nums)<2: continue
            mx=max(nums); 
            if mx>200: continue
            gaps=(mx-min(nums)+1)-len(set(nums))
            if gaps>=10 and gaps/(mx-min(nums)+1)>=0.15:
                rep.append((os.path.basename(f)[:-6],len(nums),mx,gaps))
    return rep
def refix(txt_glob, out_dir, marker):
    SP=re.compile(marker)
    os.makedirs(out_dir,exist_ok=True); done=[]
    for f in sorted(glob.glob(txt_glob)):
        ep=os.path.basename(f)[:-4]; t=open(f,encoding='utf-8',errors='ignore').read()
        P=list(SP.finditer(t))
        if len(P)<2: continue
        scs=[]
        for i,m in enumerate(P):
            s=m.start(); e=P[i+1].start() if i+1<len(P) else len(t)
            b=t[s:e].strip()
            if len(b)>=10: scs.append((m.group(1),b))
        with open(f'{out_dir}/{ep}.jsonl','w',encoding='utf-8') as fo:
            for k,(no,b) in enumerate(scs,1):
                fo.write(json.dumps({'work_id':ep,'scene_no':k,'orig_no':no,'text':b,'method':'refix'},ensure_ascii=False)+'\n')
        done.append((ep,len(scs)))
    return done
if __name__=='__main__':
    import sys
    base=sys.argv[1] if len(sys.argv)>1 else '.'
    for r in sorted(scan(f'{base}/scenes'),key=lambda x:-x[3])[:30]: print(r)
