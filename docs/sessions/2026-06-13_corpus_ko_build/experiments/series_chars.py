# 시리즈 단위 인물 추출 — 드라마 회차를 시리즈로 묶어 재등장 인물 산출 후 각 회차에 부여
import os,glob,json,re
from collections import defaultdict,Counter
from mecab import MeCab
m=MeCab()
nkg=json.load(open("nkg.json"))
SPEAK=re.compile(r'^\s*([가-힣]{2,4})\s*[:：]')
NAMELINE=re.compile(r'^\s*([가-힣]{2,4})(\s*\([^)]{1,6}\))?\s*$')
TABCUE=re.compile(r'^\s*([가-힣]{2,5})(\t+|\s{2,})\S')
STOP=set("그리고 그러나 그래서 하지만 그때 이때 다시 사람 남자 여자 엄마 아빠 순간 갑자기 조용 모두 우리 당신 자막 소리 화면 목소리 내레이션 지금 오늘 내일 여기 저기 자기 자신 마치 정도 동안 향해".split())
HEAD=re.compile(r'(낮|밤|아침|저녁|새벽|오후|오전|실내|실외|S\s*#|^#|^\d)')
# 시리즈 매핑
SER={"신사의품격":"신사의품격","태후":"태양의후예","위대한유산":"위대한유산","장밋빛인생":"장밋빛인생","적도의남자":"적도의남자",
"두번째프러포즈":"두번째프러포즈","알게될거야":"알게될거야","강적들":"강적들","귀여운여인":"귀여운여인","개와늑대의시간":"개와늑대의시간",
"궁":"궁","넌어느별에서왔니":"넌어느별","넌내게반했어":"넌내게반했어","네자매이야기":"네자매이야기","밤이면밤마다":"밤이면밤마다",
"별순검S1":"별순검S1","별순검S2":"별순검S2","어느멋진날":"어느멋진날","여우야뭐하니":"여우야뭐하니","역전의여왕":"역전의여왕",
"옥탑방고양이":"옥탑방고양이","원더풀라이프":"원더풀라이프","트리플":"트리플","장난스런키스":"장난스런키스"}
def series(w):
    if re.match(r'^\d+부$',w): return "신사의품격"
    for p,s in SER.items():
        if w.startswith(p): return s
    return None
groups=defaultdict(list)
for sf in glob.glob("scenes/*.jsonl"):
    w=os.path.basename(sf)[:-6]; s=series(w)
    if s: groups[s].append((w,sf))
def cues(text):
    out=set()
    for ln in text.splitlines():
        for rx in (SPEAK,TABCUE):
            mm=rx.match(ln)
            if mm and mm.group(1) not in STOP and not HEAD.search(ln): out.add(mm.group(1))
        nm=NAMELINE.match(ln)
        if nm and nm.group(1) not in STOP: out.add(nm.group(1))
    return out
fixed=0
for s,eps in groups.items():
    epcount=Counter()  # 이름 -> 등장 회차 수
    for w,sf in eps:
        epchars=set()
        for L in open(sf,errors='ignore'):
            epchars|=cues(json.loads(L)["text"])
        for c in epchars: epcount[c]+=1
    # 시리즈 전체에서 ≥2 회차 등장 = 실제 캐스트
    cast=[c for c,n in epcount.most_common() if n>=2][:15]
    if len(cast)<2: continue
    for w,sf in eps:
        if nkg.get(w,{}).get("n_characters",0)==0:
            nkg.setdefault(w,{})["characters"]=cast; nkg[w]["n_characters"]=len(cast); nkg[w]["char_method"]="series"; fixed+=1
json.dump(nkg,open("nkg.json","w"),ensure_ascii=False,indent=0)
print("시리즈 단위로 인물 부여한 회차:",fixed)
print("남은 NOCHAR:",sum(1 for w in nkg if nkg[w].get('n_characters',0)==0))
# 샘플
for s in ["궁01","역전의여왕05","옥탑방고양이03","별순검S1_10" if "별순검S1_10" in nkg else "별순검S110"]:
    if s in nkg: print(f"  {s}: {nkg[s].get('characters',[])[:6]}")
