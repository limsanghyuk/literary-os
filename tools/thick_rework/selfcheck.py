# -*- coding: utf-8 -*-
"""
LOS-DEPTH-SELFCHECK-V0.1  (2026-08-10)
후판(thick_sequence) 1개 작품의 '깊이'를 제출 전에 스스로 채점한다.

사용법:
    python selfcheck.py <작품 thick_sequence 폴더> [stock300.json]
    예) python selfcheck.py ./thick_sequence/경성스캔들 ./stock300.json

주판정(합격/불합격을 가르는 유일한 항): 다양도@813 >= 0.748
  - 이 축만이 2026-08-10 열화 대조 2AFC(H 22/24, p=0.00002)로 방향이 검증되었다.
보조 진단(합격 여부를 바꾸지 않는다. '무엇이 왜 얕은지'를 국소화하는 용도):
  정형문% <=6 · 상투피복% <=20 · cast재기술% <=20 · 회수재기술% <=20 ·
  명제표제인용% <=25 · 회수보유% >=70 · 정보보유% >=70 · event/cast/info 다양도 >=0.70
"""
import json,glob,re,random,collections,sys,os
import statistics as st

Q=re.compile(r'[‘’\'"“”「『][^‘’\'"“”」』]{0,80}[’‘\'"“”」』]')
LINE={'div':0.748,'tmpl':6.0,'cov':20.0,'cast_re':20.0,'pp_re':20.0,'q_prop':25.0,
      'pp':70.0,'ip':70.0,'field':0.70}

def load(d):
    R=[]
    for f in sorted(glob.glob(os.path.join(d,'*.jsonl'))):
        for L in open(f,encoding='utf-8'):
            L=L.strip()
            if L: R.append(json.loads(L))
    return R

def div(texts,N=813,reps=30,seed=7):
    w=[]
    for p in texts: w+=[x for x in re.split(r'\s+',Q.sub('',p or '')) if x]
    if len(w)<N: return None
    rnd=random.Random(seed)
    return round(st.mean(len(set(rnd.sample(w,N)))/N for _ in range(reps)),3)

def skel(p): return re.sub(r'\d+','<D>',Q.sub('<Q>',p))

def tmpl(P):
    c=collections.Counter(skel(p) for p in P)
    return round(100.0*sum(1 for p in P if c[skel(p)]>=2)/max(len(P),1),1)

def cov(P,STOCK):
    h=t=0
    for p in P:
        ws=[x for x in re.split(r'\s+',Q.sub('<Q>',p)) if x]
        gs=[' '.join(ws[i:i+5]) for i in range(len(ws)-4)]
        if not gs: continue
        t+=1
        if any(x in STOCK for x in gs): h+=1
    return round(100.0*h/max(t,1),1)

def ng(s,n=12):
    s=re.sub(r'\s+','',s or '')
    return set(s[i:i+n] for i in range(len(s)-n+1))

def restate(texts_by_rec,events):
    """상위필드(event) 문장을 하위필드가 그대로 되받아 쓴 비율"""
    n=c=0
    for ts,ev in zip(texts_by_rec,events):
        E=ng(ev)
        for t in ts:
            n+=1; g=ng(t)
            if g and len(g&E)/len(g)>=0.30: c+=1
    return round(100.0*c/max(n,1),1)

def report(d,stockpath='stock300.json'):
    R=load(d)
    if not R: print('레코드 0건:',d); return
    STOCK=set(json.load(open(stockpath,encoding='utf-8')))
    P=[fp for r in R for s in r.get('scene_notes',[]) for fp in s.get('functional_propositions',[])]
    events=[r.get('event','') or '' for r in R]
    m={}
    m['seq']=len(R); m['props']=len(P)
    m['div']=div(P); m['tmpl']=tmpl(P); m['cov']=cov(P,STOCK)
    m['d_event']=div(events)
    m['d_cast']=div([c.get('desire_or_function','') for r in R for c in r.get('cast',[])])
    inf=[(s.get('before','') or '')+' '+(s.get('after','') or '') for r in R for s in r.get('info_shift',[])]
    m['d_info']=div(inf) if inf else None
    m['cast_re']=restate([[c.get('desire_or_function','') for c in r.get('cast',[])] for r in R],events)
    m['pp_re']=restate([[str(p.get('statement','')) for p in r.get('plant_payoff',[])] for r in R],events)
    m['prop_re']=restate([[fp for s in r.get('scene_notes',[]) for fp in s.get('functional_propositions',[])] for r in R],events)
    m['q_prop']=round(100.0*sum(1 for p in P if Q.search(p))/max(len(P),1),1)
    m['pp']=round(100.0*sum(1 for r in R if r.get('plant_payoff'))/len(R),1)
    m['ip']=round(100.0*sum(1 for r in R if r.get('info_shift'))/len(R),1)

    print('== %s : 시퀀스 %d · 명제 %d =='%(os.path.basename(d.rstrip('/')),m['seq'],m['props']))
    ok = (m['div'] is not None and m['div']>=LINE['div'])
    print('  [주판정 · 검증된 축]')
    print('    다양도@813   %7s  >= %s   %s'%(m['div'],LINE['div'],'합격' if ok else '**불합격**'))
    print('  [보조 진단 · 결정력 없음. 무엇을 고칠지 국소화하는 용도]')
    aux=[('정형문%',m['tmpl'],'<=',LINE['tmpl']),
         ('상투피복%',m['cov'],'<=',LINE['cov']),
         ('cast재기술%',m['cast_re'],'<=',LINE['cast_re']),
         ('회수재기술%',m['pp_re'],'<=',LINE['pp_re']),
         ('명제재기술%',m['prop_re'],'<=',LINE['q_prop']),
         ('명제표제인용%',m['q_prop'],'<=',LINE['q_prop']),
         ('회수보유%',m['pp'],'>=',LINE['pp']),
         ('정보보유%',m['ip'],'>=',LINE['ip']),
         ('event다양도',m['d_event'],'>=',LINE['field']),
         ('cast다양도',m['d_cast'],'>=',LINE['field']),
         ('info다양도',m['d_info'],'>=',LINE['field'])]
    flags=[]
    for name,v,op,th in aux:
        if v is None: print('    %-14s      -   (표본부족)'%name); continue
        g=(v>=th) if op=='>=' else (v<=th)
        if not g: flags.append(name)
        print('    %-14s %7s  %s %-6s  %s'%(name,v,op,th,'ok' if g else 'FLAG'))
    print('  판정: %s   / 보조 FLAG %d항%s'%('합격' if ok else '불합격',len(flags),
          (' ('+', '.join(flags)+')') if flags else ''))
    return m

if __name__=='__main__':
    d=sys.argv[1]
    sp=sys.argv[2] if len(sys.argv)>2 else os.path.join(os.path.dirname(os.path.abspath(__file__)),'stock300.json')
    report(d,sp)
