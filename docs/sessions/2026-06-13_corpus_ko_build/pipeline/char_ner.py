# 시리즈 단위 인물 NER (CHAR_NER_PROPOSAL 구현): 화자위치 한정+헤딩제외+접미필터+재등장
import os,glob,json,re
from collections import defaultdict,Counter
SPEAK=re.compile(r'^\s*([가-힣]{2,4})\s*[:：]\s*\S')
TAB  =re.compile(r'^\s*([가-힣]{2,5})(?:\t+|\s{2,})\S')
NAME =re.compile(r'^\s*([가-힣]{2,4})(\s*\([^)]{1,6}\))?\s*$')
STOP=set("그리고 그러나 그래서 하지만 그때 이때 다시 사람 남자 여자 엄마 아빠 순간 갑자기 조용 모두 우리 당신 자막 소리 화면 목소리 내레이션 지금 오늘 내일 자기 자신 마치 정도 동안 향해 잠시 다들 거기 그곳 모습 표정 얼굴 시선 마음 생각 둘이 서로 일동 전체 사이 잠깐 결국 도대체".split())
LOC_SUF=re.compile(r'(실|방|관|집|청|국|소|점|장|원|동|로|길|앞|밖|안|쪽|가|역|항|港)$')
LOCSTOP=set("거실 안방 주방 침실 서재 화장실 욕실 부엌 마당 대문 현관 복도 계단 옥상 베란다 사무실 교실 병실 회의실 대회의실 휴게실 탕비실 작업실 분장실 대기실 응접실 식당 카페 술집 편의점 거리 골목 공원 운동장 옥탑방 노래방 강의실 연구실 응급실 수술실 면회실 취조실 사장실 부장실 팀장실 상무실 회장실 비서실 로비 주차장 실내 실외 전경 외경 내부".split())
HEADWORD=re.compile(r'(낮|밤|아침|저녁|새벽|오후|오전|실내|실외|S\s*#|^#|^\d)')
def series(w):
    if re.match(r'^\d+부$',w): return "신사의품격"
    for p in ["태후","미생","커피프린스","풍문으로들었소","개인의취향","드라마시그널대본","신사의품격","위대한유산","장밋빛인생","적도의남자",
              "두번째프러포즈","개와늑대의시간","넌어느별에서왔니","넌내게반했어","네자매이야기","밤이면밤마다","별순검S1","별순검S2",
              "어느멋진날","여우야뭐하니","역전의여왕","옥탑방고양이","원더풀라이프","트리플","장난스런키스"]:
        if w.startswith(p): return p
    return w  # 영화·단일작은 자기자신
groups=defaultdict(list)
for sf in glob.glob("scenes/*.jsonl"):
    groups[series(os.path.basename(sf)[:-6])].append(sf)
def cast_of(sfs):
    headvoc=Counter(); spk_ep=Counter()
    for sf in sfs:
        epspk=set()
        for L in open(sf,errors='ignore'):
            d=json.loads(L)
            for t in re.findall(r'[가-힣]{2,4}',d.get("heading","")): headvoc[t]+=1
            lines=d["text"].splitlines()
            for i,ln in enumerate(lines):
                m=SPEAK.match(ln) or TAB.match(ln)
                if m and m.group(1) not in STOP: epspk.add(m.group(1)); continue
                nm=NAME.match(ln)
                if nm and nm.group(1) not in STOP and not HEADWORD.search(ln):
                    nxt=next((lines[j].strip() for j in range(i+1,min(i+3,len(lines))) if lines[j].strip()),"")
                    if nxt and not NAME.match(nxt): epspk.add(nm.group(1))
        for c in epspk: spk_ep[c]+=1
    nep=len(sfs); thr=2 if nep>=2 else 1
    cast=[]
    for c,se in spk_ep.most_common():
        if se<thr or c in LOCSTOP: continue
        if LOC_SUF.search(c) and headvoc.get(c,0)>=se: continue   # 장소 접미+헤딩빈도↑ 제외
        if headvoc.get(c,0)>se*2: continue                        # 헤딩에 압도적=장소
        cast.append(c)
    return cast[:15]
nkg=json.load(open("nkg.json"))
fixed=0; before=sum(1 for w in nkg if nkg[w].get('n_characters',0)==0)
for s,sfs in groups.items():
    cast=cast_of(sfs)
    if len(cast)<2: continue
    for sf in sfs:
        w=os.path.basename(sf)[:-6]
        e=nkg.setdefault(w,{})
        if e.get('n_characters',0)==0:
            e['characters']=cast; e['n_characters']=len(cast); e['char_method']='series_ner'; fixed+=1
json.dump(nkg,open("nkg.json","w"),ensure_ascii=False,indent=0)
after=sum(1 for w in nkg if nkg[w].get('n_characters',0)==0)
print(f"NER 보강: NOCHAR {before}→{after} (메운 회차 {fixed})")
for s in ["미생05","역전의여왕05","옥탑방고양이03","궁01","원더풀라이프05"]:
    if s in nkg: print(f"  {s}: {nkg[s].get('characters',[])[:7]}")
