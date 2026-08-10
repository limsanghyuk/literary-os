# -*- coding: utf-8 -*-
"""제거 시험: 상투 꼬리·표제 도입부만 기계적으로 걷어냈을 때 알맹이가 남는가."""
import json,glob,re,os,sys,collections
sys.path.insert(0,'.')
from selfcheck import div,Q
B='/sessions/compassionate-eager-lovelace/mnt/claude/db/seqcard_ko/reinforcement_v1/thick_sequence/'
LEAD=re.compile(r'^\s*[‘\'"“][^’\'"”]{2,60}[’\'"”](?:의|은|는|이|가)?\s*(?:에서|에|장면(?:은|이|에서)?)?\s*')
TAILS=[r'이 장면은 [^.]{0,60}한다\.',r'이 장면의 두 번째 기능은 [^.]{0,120}한다\.',
       r'이 지점은 [^.]{0,80}한다\.',r'[^.]{0,40}(?:필요한|이후) 신뢰 근거를 쌓는다\.',
       r'관계의 거리를 바꿔 이후 선택의 감정 조건을 만든다\.']
TAIL=re.compile('|'.join(TAILS))
for w in ['강남엄마따라잡기','개와늑대의시간','가을동화','너의목소리가들려','101번째프로포즈']:
    R=[json.loads(l) for f in sorted(glob.glob(B+w+'/*.jsonl')) for l in open(f,encoding='utf-8') if l.strip()]
    P=[fp for r in R for s in r.get('scene_notes',[]) for fp in s.get('functional_propositions',[])]
    S=[]
    for p in P:
        t=TAIL.sub('',p); t=LEAD.sub('',t); t=re.sub(r'\s+',' ',t).strip()
        S.append(t)
    kept=[t for t in S if len(t)>=25]
    print('%-10s 명제 %4d | 원본 다양도 %s → 제거후 %s | 잔존(25자+) %d (%.0f%%) | 평균길이 %d→%d'%(
        w,len(P),div(P),div(S),len(kept),100.0*len(kept)/len(P),
        sum(len(x) for x in P)//max(len(P),1),sum(len(x) for x in S)//max(len(S),1)))
