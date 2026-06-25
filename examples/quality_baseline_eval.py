# -*- coding: utf-8 -*-
import json,subprocess,sys,re
OAI=open('/tmp/.oai').read().strip()
def call(sys_p,usr,mt=700,temp=0.7):
    body=json.dumps({"model":"gpt-4o-mini","temperature":temp,"max_tokens":mt,
      "messages":[{"role":"system","content":sys_p},{"role":"user","content":usr}]})
    r=subprocess.run(['curl','-s','--max-time','40','https://api.openai.com/v1/chat/completions',
      '-H',f'Authorization: Bearer {OAI}','-H','Content-Type: application/json','-d',body],
      capture_output=True,text=True)
    return json.loads(r.stdout)['choices'][0]['message']['content'].strip()
GEN_SYS=("너는 한국 드라마 대본 작가다. 주어진 전제로 1화 오프닝 장면 하나를 한국어 대본체(지문+대사/내레이션)로 써라. "
         "분량 350~600자. 설명이 아니라 보여주기로. 메타설명 없이 장면만.")
PREMISE={
 '시그널':"장기 미제 사건을 쫓는 현재의 프로파일러와 과거의 형사가 우연히 연결되는 범죄 스릴러. 1화 오프닝.",
 '대장금':"조선 궁중을 배경으로 비극적 가족사를 지닌 인물이 등장하는 사극. 1화 오프닝.",
 '미생':"냉혹한 비즈니스 세계에 던져진 주인공을 그리는 직장 드라마. 내레이션 포함 1화 오프닝.",
}
phase=sys.argv[1]
if phase=='gen':
    real=json.load(open('/tmp/real_scenes.json',encoding='utf-8'))
    out={}
    for name in PREMISE:
        if name not in real: continue
        gen=call(GEN_SYS,f"[전제] {PREMISE[name]}")
        out[name]={'real':real[name]['text'],'gen':gen,'work':real[name]['work']}
        print(f"[{name}] 생성 {len(gen)}자")
    json.dump(out,open('/tmp/eval_pairs.json','w',encoding='utf-8'),ensure_ascii=False)
    print("saved eval_pairs.json")

if phase=='judge':
    import random; random.seed(11)
    pairs=json.load(open('/tmp/eval_pairs.json',encoding='utf-8'))
    JS=("너는 드라마 극본 심사위원이다. 두 오프닝 장면 A와 B를 블라인드로 비교해라. "
        "5축(구조/인물/대사/감정/장르적합) 각각 더 나은 쪽(A|B|TIE)과 전체 우세(A|B|TIE)를 판정하고 "
        "각 축 한 줄 근거. 반드시 JSON만: {\"structure\":\"A|B|TIE\",\"character\":..,\"dialogue\":..,"
        "\"emotion\":..,\"genre\":..,\"overall\":..,\"why\":{\"structure\":\"..\",..}}")
    rows=[]
    for name,d in pairs.items():
        flip=random.random()<0.5
        A,B=(d['gen'],d['real']) if not flip else (d['real'],d['gen'])
        genlabel='A' if not flip else 'B'
        usr=f"[장면 A]\n{A[:900]}\n\n[장면 B]\n{B[:900]}"
        try: r=json.loads(re.sub(r'^```json|```$','',call(JS,usr,500,0).strip(),flags=re.M).strip())
        except Exception as e: print(name,"judge err",e); continue
        axes=['structure','character','dialogue','emotion','genre','overall']
        genwins={ax:(r.get(ax)==genlabel) for ax in axes}
        genlose={ax:(r.get(ax) in ('A','B') and r.get(ax)!=genlabel) for ax in axes}
        rows.append({'work':name,'genlabel':genlabel,'verdict':{ax:r.get(ax) for ax in axes},
                     'gen_wins':genwins,'why':r.get('why',{})})
        print(f"\n=== {name} (생성={genlabel}) ===")
        for ax in axes:
            mark='생성승' if genwins[ax] else ('명작승' if genlose[ax] else 'TIE')
            print(f"  {ax}: {r.get(ax)} [{mark}]  - {r.get('why',{}).get(ax,'')[:70]}")
    # aggregate
    import collections
    agg=collections.Counter()
    for ax in ['structure','character','dialogue','emotion','genre','overall']:
        gw=sum(1 for x in rows if x['gen_wins'][ax]); tie=sum(1 for x in rows if x['verdict'][ax]=='TIE')
        ml=len(rows)-gw-tie
        print(f"[{ax}] 생성승 {gw} / TIE {tie} / 명작승 {ml}  (n={len(rows)})")
    json.dump(rows,open('/tmp/eval_verdicts.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print("saved eval_verdicts.json")
