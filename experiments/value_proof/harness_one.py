import os, json, re, time, urllib.request, random, sys
KEY=os.environ["GEMINI_API_KEY"]; M="gemini-2.5-flash"
def call(prompt,mt=750,temp=0.8):
    url=f"https://generativelanguage.googleapis.com/v1beta/models/{M}:generateContent?key={KEY}"
    body={"contents":[{"parts":[{"text":prompt}]}],"generationConfig":{"maxOutputTokens":mt,"temperature":temp,"thinkingConfig":{"thinkingBudget":0}}}
    req=urllib.request.Request(url,data=json.dumps(body).encode(),headers={"content-type":"application/json"})
    with urllib.request.urlopen(req,timeout=35) as r: d=json.load(r)
    c=d.get("candidates",[])
    if not c: return ""
    return "".join(p.get("text","") for p in c[0].get("content",{}).get("parts",[])).strip()
SCENES=[
 {"id":"S1","logline":"이혼 직전의 부부가 비 오는 주차장에서 마지막 대화를 나눈다.","chars":["서연(38, 변호사, 자존심 강함)","민호(40, 건축가, 회피형)"],"prior":"두 사람은 3년간 냉전. 오늘 조정 서류에 서명하기로 함.","goal":"서연이 진짜 원하는 말을 끝내 못 하고 돌아선다(미완의 감정).","arc":"억눌린 분노 → 흔들림 → 체념","conflict":"서명 vs 마지막 만류","motif":"꺼지지 않는 자동차 헤드라이트"},
 {"id":"S2","logline":"재벌가 막내가 비밀리에 운영하던 포장마차가 형에게 발각된다.","chars":["도윤(29, 재벌 막내, 이중생활)","태강(35, 후계자 형, 원칙주의)"],"prior":"도윤은 가업을 거부하고 밤마다 포장마차를 운영.","goal":"태강이 분노 대신 뜻밖의 질문을 던지며 균열을 드러낸다.","arc":"적발의 긴장 → 충돌 → 예상 밖 공감의 틈","conflict":"가문의 의무 vs 개인의 삶","motif":"식어가는 어묵 국물"},
 {"id":"S3","logline":"형사가 용의자가 자신의 옛 은인임을 심문 도중 깨닫는다.","chars":["강력계 형사 준(45)","용의자 윤씨(67, 과거의 은인)"],"prior":"준은 고아 시절 윤씨에게 도움을 받았으나 기억이 흐릿하다.","goal":"준이 직업적 의무와 사적 부채 사이에서 질문을 멈춘다.","arc":"기계적 심문 → 인식의 충격 → 흔들리는 침묵","conflict":"법 집행 vs 개인적 빚","motif":"낡은 손목시계"},
 {"id":"S4","logline":"아이돌 연습생이 데뷔 무대 직전 무대공포로 무너진다.","chars":["연습생 하늘(19)","매니저 박실장(50, 무뚝뚝)"],"prior":"하늘은 7년 연습생. 마지막 기회.","goal":"박실장이 위로 대신 단 한 문장으로 하늘을 일으킨다.","arc":"공황 → 바닥 → 작은 불씨","conflict":"두려움 vs 마지막 기회","motif":"식은 도시락"}]
def pA(s): return f"다음 상황으로 한국 드라마 한 장면을 써라.\n상황: {s['logline']}\n분량: 250~400자, 지문+대사 형식."
def pB(s): return f"""너는 서사 구조 엔진의 가이드를 받는 드라마 작가다. 아래 구조 제약을 모두 충족하라.
[상황] {s['logline']}
[인물(상태 일관성)] {' / '.join(s['chars'])}
[직전 상태(연속성)] {s['prior']}
[인과 목표] {s['goal']}
[감정 아크(이 곡선)] {s['arc']}
[중심 갈등] {s['conflict']}
[모티프(물리적 등장·2회 이상 변주)] {s['motif']}
[공식 가이드] 갈등은 압축적으로, 에너지는 도입↓·중반↑·말미 잔류, 모티프 잔향 적재, 마지막 문장은 다음을 궁금하게.
[헌법] 인물·직전상태 모순 금지, 인과 목표 충족, 설명조 금지·보여주기.
분량: 250~400자, 지문+대사. 모든 구조 제약 반영해 한 장면을 써라."""
JT="""동일 상황으로 쓴 두 드라마 장면이다. 어느 쪽이 더 좋은 드라마 씬인가. 기준: 인물 일관성·인과·감정곡선·모티프·몰입.
[상황] {lg}
=== 작품 1 ===
{w1}
=== 작품 2 ===
{w2}
JSON만: {{"winner":1또는2,"s1":{{"consistency":1-5,"causality":1-5,"character":1-5,"emotion":1-5,"immersion":1-5}},"s2":{{...동일...}},"reason":"한문장"}}"""
idx=int(sys.argv[1]); s=SCENES[idx]
a=call(pA(s)); b=call(pB(s),mt=820)
random.seed(100+idx); swap=random.random()<0.5
w1,w2=(b,a) if swap else (a,b)
raw=call(JT.format(lg=s["logline"],w1=w1,w2=w2),mt=600,temp=0.2)
if not re.search(r"\{.*\}",raw,re.S): print("JUDGE_RAW>>>",raw[:300]); import sys; sys.exit(2)
m=re.search(r"\{.*\}",raw,re.S); j=json.loads(m.group(0))
l2a={1:("B" if swap else "A"),2:("A" if swap else "B")}
win=l2a[j["winner"]]
sa=j["s2" if swap else "s1"]; sb=j["s1" if swap else "s2"]
rec={"id":s["id"],"A":a,"B":b,"len_A":len(a),"len_B":len(b),"winner":win,"score_A":sa,"score_B":sb,"reason":j.get("reason","")}
open("results.jsonl","a").write(json.dumps(rec,ensure_ascii=False)+"\n")
print(f"[{s['id']}] winner={win}  lenA={len(a)} lenB={len(b)}  scoreA={sum(sa.values())} scoreB={sum(sb.values())}")
