# 시리즈 단위 인물 NER 프로토타입: 화자위치 한정 + 장소(헤딩)어휘 제외 + 회차 재등장
import os,glob,json,re
from collections import defaultdict,Counter
SPEAK=re.compile(r'^\s*([가-힣]{2,4})\s*[:：]\s*\S')      # 이름: 대사
TAB  =re.compile(r'^\s*([가-힣]{2,5})(?:\t+|\s{2,})\S')   # 이름<tab>대사
NAME =re.compile(r'^\s*([가-힣]{2,4})(\s*\([^)]{1,6}\))?\s*$')  # 단독행 이름(다음행 대사 조건)
STOP=set("그리고 그러나 그래서 하지만 그때 이때 다시 사람 남자 여자 엄마 아빠 순간 갑자기 조용 모두 우리 당신 자막 소리 화면 목소리 내레이션 지금 오늘 내일 자기 자신 마치 정도 동안 향해 잠시 다들 거기 그곳".split())
def series(w):
    if re.match(r'^\d+부$',w): return "신사의품격"
    for p in ["태후","신사의품격","위대한유산","장밋빛인생","적도의남자","두번째프러포즈","알게될거야","강적들","귀여운여인",
              "개와늑대의시간","궁","넌어느별에서왔니","넌내게반했어","네자매이야기","밤이면밤마다","별순검S1","별순검S2",
              "어느멋진날","여우야뭐하니","역전의여왕","옥탑방고양이","원더풀라이프","트리플","장난스런키스"]:
        if w.startswith(p): return p
    return None
groups=defaultdict(list)
for sf in glob.glob("scenes/*.jsonl"):
    w=os.path.basename(sf)[:-6]; s=series(w)
    if s: groups[s].append(sf)
def analyze(series_name,sfs):
    head_vocab=Counter()      # 헤딩(슬러그) 토큰 = 장소 후보
    speaker_ep=Counter()      # 화자 등장 회차수
    for sf in sfs:
        ep_speakers=set()
        for L in open(sf,errors='ignore'):
            d=json.loads(L)
            # 헤딩 토큰 수집(장소)
            for t in re.findall(r'[가-힣]{2,4}',d.get("heading","")): head_vocab[t]+=1
            lines=d["text"].splitlines()
            for i,ln in enumerate(lines):
                m=SPEAK.match(ln) or TAB.match(ln)
                if m and m.group(1) not in STOP: ep_speakers.add(m.group(1)); continue
                nm=NAME.match(ln)
                if nm and nm.group(1) not in STOP:
                    nxt=next((lines[j].strip() for j in range(i+1,min(i+3,len(lines))) if lines[j].strip()),"")
                    if nxt and not NAME.match(nxt): ep_speakers.add(nm.group(1))
        for c in ep_speakers: speaker_ep[c]+=1
    nep=len(sfs)
    # 캐스트: 화자로 ≥2회차 등장 AND 헤딩(장소)빈도가 화자빈도보다 낮음
    cast=[]
    for c,se in speaker_ep.most_common():
        if se>=2 and head_vocab.get(c,0) <= se:   # 장소어휘 제외
            cast.append((c,se))
    return cast[:15]
print("=== 시리즈 단위 인물 NER 프로토타입 (장소누출 제거 검증) ===")
for s in ["궁","역전의여왕","옥탑방고양이","별순검S1","원더풀라이프","개와늑대의시간"]:
    if s in groups:
        cast=analyze(s,groups[s])
        print(f"  {s:10}({len(groups[s])}ep): {[c for c,_ in cast[:8]]}")
