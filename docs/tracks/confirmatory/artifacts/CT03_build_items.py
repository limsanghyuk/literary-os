# -*- coding: utf-8 -*-
"""CT-03 문항 생성기 (v2) — 표기 정규화 + 씬 추출
사전등록: LOS-CT-03-PREREG-V1.0 §3
"""
import json, re, os, unicodedata
from collections import defaultdict

RUN = '/sessions/compassionate-eager-lovelace/mnt/claude/G1SEQ_run_20260804'
OUT = '/sessions/compassionate-eager-lovelace/mnt/claude/CT03_run_20260805'
VOCAB = json.load(open(os.path.join(OUT,'speaker_vocab.json')))

HEAD = re.compile(r'^[ \t]*(\d+)[.．][ \t]*(.*)$')
MEMO = ['제외','나눠줌','깔아주세요','으로 가요','로 가요','캐스팅','배우','분장','촬영','편집',
        '대사는','붙여주세요','빼주세요','참고바랍']
EPMARK = re.compile(r'^\s*\(?\s*\d+\s*회\s*(ENDING|엔딩|끝)\s*\)?\.?\s*$')
PAGE   = re.compile(r'^\s*(-\s*\d+\s*-|[Pp]\.\s*\d+|\d+\s*/\s*\d+)\s*$')

def sq(x): return re.sub(r'\s+','',x)

LOG = defaultdict(int)
DETAIL = []

def split_scenes(path):
    """씬 번호 -> (heading, body lines)"""
    lines = open(path, encoding='utf-8').read().split('\n')
    scenes = {}; cur=None; buf=[]; head=None
    for ln in lines:
        m = HEAD.match(ln)
        if m and len(m.group(1))<=3:
            if cur is not None: scenes[cur]=(head, buf)
            cur=int(m.group(1)); head=m.group(2).strip(); buf=[]
        else:
            if cur is not None: buf.append(ln)
    if cur is not None: scenes[cur]=(head, buf)
    return scenes

def normalize(head, body, work, tag):
    voc = set(VOCAB[work])
    out=[]
    i=0
    n=len(body)
    # --- N2: 헤딩 인접 괄호 블록(제작메모) 제거 ---
    # 본문 선두의 괄호블록 검사
    while i<n and body[i].strip()=='' : out.append(''); i+=1
    if i<n and body[i].lstrip().startswith('('):
        j=i; depth=0; blk=[]
        while j<n:
            blk.append(body[j]); depth += body[j].count('(')-body[j].count(')')
            if depth<=0: break
            j+=1
        txt='\n'.join(blk)
        if any(k in txt for k in MEMO):
            LOG['N2_removed']+=1; DETAIL.append((tag,'N2_removed',txt[:120]))
            i=j+1
        else:
            LOG['N2_preserved']+=1; DETAIL.append((tag,'N2_preserved',txt[:80]))
    res=[]
    while i<n:
        ln=body[i]
        # --- N3: 회차/페이지 표기 ---
        if EPMARK.match(ln) or PAGE.match(ln):
            LOG['N3.'+tag[-1]]+=1; i+=1; continue
        res.append(ln); i+=1
    body=res

    # --- N5: 타이포그래피 ---
    tmp=[]
    for ln in body:
        o=ln
        ln=ln.replace('　',' ')
        ln=re.sub(r'[ \t]+',' ',ln).strip()
        if ln!=o.strip(): LOG['N5.'+tag[-1]]+=1
        tmp.append(ln)
    body=tmp

    # --- N6: 이름 단독행 병합 (확장: 다음 비어있지않은 행 일반) ---
    tmp=[]; i=0; n=len(body)
    while i<n:
        ln=body[i]; s=ln.strip()
        if s and sq(s) in voc and len(sq(s))<=8:
            j=i+1
            while j<n and body[j].strip()=='' : j+=1
            if j<n:
                tmp.append(s+'\t'+body[j].strip())
                LOG['N6.'+tag[-1]]+=1
                i=j+1; continue
        tmp.append(ln); i+=1
    body=tmp

    # --- N1c: 콜론 화자표기 -> 탭 (원작 고유 관습 = 출처 단서) ---
    tmp=[]
    for ln in body:
        m=re.match(r'^([^\t]{1,14}?)[ ]*:[ ]*(\S.*)$', ln)
        if m and 1<=len(sq(m.group(1)))<=8 and sq(m.group(1)) in voc:
            tmp.append(sq(m.group(1))+'\t'+m.group(2).strip()); LOG['N1c.'+tag[-1]]+=1
        elif m:
            nm=m.group(1).strip()
            core=re.sub(r'\((?:E|F|F\.?O|O\.?S|N)\)','',nm).strip()
            if 1<=len(sq(core))<=10 and not re.search(r'[.!?…,\u3002]', core):
                tmp.append(sq(core)+'\t'+m.group(2).strip()); LOG['N1c2.'+tag[-1]]+=1
                DETAIL.append((tag,'N1c2',nm))
            else:
                tmp.append(ln)
        else:
            tmp.append(ln)
    body=tmp

    # --- N7: 성명 -> 약칭 (꼬리가 vocab에 있을 때만) ---
    tmp=[]
    full=[v for v in voc if len(v)==3]
    mapping={}
    for f in full:
        if f[1:] in voc: mapping[f]=f[1:]
    for ln in body:
        o=ln
        for f,s in mapping.items():
            if f in ln: ln=ln.replace(f,s)
        if ln!=o: LOG['N7.'+tag[-1]]+=1
        tmp.append(ln)
    body=tmp

    # --- N9: 화면밖/효과 표기 통일 (이름E / 이름(E) / 이름 E -> 이름(E)) ---
    tmp=[]
    for ln in body:
        o=ln
        ln=re.sub(r'(?<=[가-힣0-9])[ ]?\(?(E|F|N|O\.?S|F\.?O)\)?(?=[\t ])', lambda m:'(%s)'%m.group(1), ln)
        if ln!=o: LOG['N9.'+tag[-1]]+=1
        tmp.append(ln)
    body=tmp

    # --- N8: 공백행 균일화 (모든 판본 동일 규격: 비어있지 않은 행 사이 1행) ---
    nonb=[x for x in body if x.strip()]
    LOG['N8']+= 1 if len(nonb)!=len(body) or True else 0
    txt='\n\n'.join(nonb).strip()
    return '## '+re.sub(r'^\d+[.．]\s*','',head).strip()+'\n\n'+txt

def main():
    h=json.load(open(os.path.join(RUN,'holdout_raw.json')))
    items=[]
    for work in h:
        for seq in h[work]['pick']:
            mem=sorted(h[work]['seqs'][seq]['member_scene_nos'])
            picks=[mem[0], mem[len(mem)//2]]
            O=split_scenes(os.path.join(RUN,'orig',seq+'.txt'))
            R={v:split_scenes(os.path.join(RUN,'renders',seq+'__%s.txt'%v)) for v in 'AB'}
            # 오프셋 (건빵 번호 어긋남)
            off = sorted(O)[0]-sorted(R['A'])[0]
            for p in picks:
                rec={'work':work,'seq':seq,'scene_no':p,'off':off}
                hd,bd = O[p+off]
                rec['H']=normalize(hd,bd,work,f'{seq}#{p}/H')
                for v in 'AB':
                    hd,bd = R[v][p]
                    rec[v]=normalize(hd,bd,work,f'{seq}#{p}/{v}')
                items.append(rec)
    json.dump(items, open(os.path.join(OUT,'items_raw.json'),'w'), ensure_ascii=False, indent=1)
    json.dump({'counts':dict(LOG),'detail':DETAIL}, open(os.path.join(OUT,'normalization_log.json'),'w'), ensure_ascii=False, indent=1)
    print('items',len(items))
    print(dict(LOG))
    # 검증: 잔여 콜론행
    import statistics
    for v in 'HAB':
        resid=0; lens=[]
        for r in items:
            lens.append(len(r[v]))
            for ln in r[v].split('\n'):
                m=re.match(r'^([^\t]{1,14}?)[ ]*:[ ]*\S', ln)
                if m: resid+=1
        print(v,'잔여콜론행',resid,'평균길이',round(statistics.mean(lens)))

main()
