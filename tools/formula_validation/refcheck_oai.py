import os,json,re,urllib.request,random,time
KEY=os.environ["OPENAI_API_KEY"]
def chat(prompt,model="gpt-4o-mini",mt=900,temp=0.7):
    body={"model":model,"max_tokens":mt,"temperature":temp,"messages":[{"role":"user","content":prompt}]}
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=json.dumps(body).encode(),
        headers={"content-type":"application/json","Authorization":f"Bearer {KEY}"})
    for a in range(3):
        try:
            with urllib.request.urlopen(r,timeout=50) as x: d=json.load(x)
            return d["choices"][0]["message"]["content"].strip()
        except Exception as e:
            if a==2: raise
            time.sleep(4)
COND="구한말(1871 신미양요 전후), 노비 출신 소년이 전란 중 도망쳐 미국 군함에 오르며 조선을 등지는 장면. 인물: 소년(훗날 유진 초이). 톤: 비장·서사적. 거시: 버림받은 자가 떠나며 훗날의 귀환을 예비."
B=chat(f"다음 조건으로 한국 시대극 한 장면을 써라(250~400자, 지문+대사, 대사 원문 창작). 조건: {COND}")
A=chat(f"드라마 '미스터 션샤인' 1화에서 위 조건에 해당하는 실제 장면을 네 지식대로 재구성하라(250~400자, 지문+대사). 조건: {COND}",mt=1000)
swap=random.random()<0.5
w1,w2=(B,A) if swap else (A,B)
PER={"문학평론가":"문학성·주제밀도·문장의 격","드라마투르그":"극적 구조·인과·긴장·인물 동기","일반시청자":"몰입·감정·다음이 궁금한가"}
votes={};det={}
for name,crit in PER.items():
    raw=chat(f"""너는 {name}다. 평가기준={crit}. 동일 조건으로 쓴 두 시대극 장면을 블라인드로 비교하라.
[작품1]
{w1}
[작품2]
{w2}
JSON만 출력: {{"winner":1또는2,"score1":0~10,"score2":0~10,"why":"한 문장"}}""",model="gpt-4o",mt=400,temp=0.2)
    m=re.search(r"\{.*\}",raw,re.S); j=json.loads(m.group(0))
    l2a={1:("B" if swap else "A"),2:("A" if swap else "B")}
    votes[name]=l2a[j["winner"]]
    det[name]={"win":l2a[j["winner"]],"A_real":j["score2" if swap else "score1"],"B_gen":j["score1" if swap else "score2"],"why":j.get("why","")}
    time.sleep(1)
from collections import Counter
print("조건:",COND[:46],"...")
print("=== 다중에이전트 블라인드 비교 (A=실제 레퍼런스 / B=모델 생성) ===")
print("투표 집계:",dict(Counter(votes.values())))
for n,d in det.items(): print(f"  {n:8s}: 승={d['win']}  A(실제)={d['A_real']} B(생성)={d['B_gen']} | {d['why'][:46]}")
json.dump({"cond":COND,"A_real":A,"B_gen":B,"votes":votes,"detail":det},open("refcheck_sample.json","w"),ensure_ascii=False,indent=1)
print("\n[B 생성 앞부분]",B[:120])
print("[A 실제 앞부분]",A[:120])
