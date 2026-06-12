import os,json,re,urllib.request,random,time
KEY=os.environ["GEMINI_API_KEY"]
def call(p,model="gemini-2.5-flash",mt=1400,temp=0.6):
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={KEY}"
    b={"contents":[{"parts":[{"text":p}]}],"generationConfig":{"maxOutputTokens":mt,"temperature":temp,"thinkingConfig":{"thinkingBudget":0}}}
    r=urllib.request.Request(url,data=json.dumps(b).encode(),headers={"content-type":"application/json"})
    time.sleep(2)
    with urllib.request.urlopen(r,timeout=45) as x: d=json.load(x)
    return "".join(pp.get("text","") for pp in d["candidates"][0]["content"]["parts"]).strip()

COND="구한말(1871년 전후), 노비 출신 소년이 신미양요 중 도망쳐 미국 군함에 오르며 조선을 등지는 장면. 인물: 소년(훗날 유진 초이). 톤: 비장·서사적. 거시: 버림받은 자가 떠나며 훗날의 귀환을 예비."
# ① 모델 생성(arm B)
B=call(f"다음 조건으로 한국 시대극 한 장면을 써라(250~400자, 지문+대사). 조건: {COND}")
# ② 레퍼런스 재구성(arm A) — 실제 미스터 션샤인 해당 씬(LLM 지식). *실 검증은 합법 대본집 필요(프록시)
A=call(f"드라마 '미스터 션샤인' 1화의 위 조건에 해당하는 실제 장면을 네 기억대로 재구성하라(250~400자, 지문+대사). 조건: {COND}", mt=1500)
# ③ 다중 에이전트 블라인드 평가 (3 페르소나)
swap=random.random()<0.5
w1,w2=(B,A) if swap else (A,B)   # 작품1이 실제로 뭔지 기록
PERSONAS={"문학평론가":"문학성·주제 밀도·문장","드라마투르그":"극적 구조·인과·긴장·인물","일반시청자":"몰입·감정·다음 궁금"}
votes={}; details={}
for name,crit in PERSONAS.items():
    raw=call(f"""너는 {name}다. 기준={crit}. 동일 조건의 두 시대극 장면을 블라인드 비교하라.
=작품1=\n{w1}\n=작품2=\n{w2}\nJSON만: {{"winner":1또는2,"score1":0~10,"score2":0~10,"why":"한줄"}}""",model="gemini-2.5-flash",mt=500,temp=0.2)
    m=re.search(r"\{.*\}",raw,re.S); j=json.loads(m.group(0))
    lab2arm={1:("B" if swap else "A"),2:("A" if swap else "B")}
    votes[name]=lab2arm[j["winner"]]
    sA=j["score2" if swap else "score1"]; sB=j["score1" if swap else "score2"]
    details[name]={"win":lab2arm[j["winner"]],"A(실제)":sA,"B(생성)":sB,"why":j.get("why","")}
print("조건:",COND[:50],"...")
print("=== 다중 에이전트 블라인드 평가 (A=실제 레퍼런스 / B=모델 생성) ===")
from collections import Counter
print("투표:",dict(Counter(votes.values())))
for n,d in details.items(): print(f"  {n}: 승={d['win']} A실제={d['A(실제)']} B생성={d['B(생성)']} | {d['why'][:40]}")
json.dump({"cond":COND,"A_real":A,"B_gen":B,"votes":votes,"details":details},open("refcheck_sample.json","w"),ensure_ascii=False,indent=1)
