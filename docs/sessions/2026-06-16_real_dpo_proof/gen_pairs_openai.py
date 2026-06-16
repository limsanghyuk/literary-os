"""gen_pairs_openai.py — 실 LLM(gpt-4o-mini) 후보 생성+판정 → 선호쌍 (LLM-1 critic 실측).
키는 환경변수 OPENAI_API_KEY 에서 읽음(파일에 비밀 미포함). 출력: real_llm_pairs.jsonl
usage: OPENAI_API_KEY=... python gen_pairs_openai.py
"""
import os, re, json
from openai import OpenAI
cli = OpenAI(api_key=os.environ["OPENAI_API_KEY"]); MODEL = "gpt-4o-mini"
seeds = ["한밤 골목 추격의 시작","엘리베이터에 갇힌 두 사람","배신을 알게 된 순간",
         "병실 앞 복도에서의 대치","폭우 속 옥상 대화","마지막 통화"]
pairs = []
for s in seeds:
    g = cli.chat.completions.create(model=MODEL, temperature=1.0, max_tokens=200, messages=[
        {"role":"system","content":"너는 한국 드라마 작가다. 상황의 도입 2~3문장을 두 버전으로: A=긴장·여백 문체, B=평이·설명체. 'A: ...\\nB: ...'"},
        {"role":"user","content":s}])
    txt = g.choices[0].message.content
    ma = re.search(r"A[:：]\s*(.+?)(?:\nB[:：]|$)", txt, re.S); mb = re.search(r"B[:：]\s*(.+)", txt, re.S)
    if not (ma and mb): continue
    A, B = ma.group(1).strip()[:200], mb.group(1).strip()[:200]
    j = cli.chat.completions.create(model=MODEL, temperature=0, max_tokens=5, messages=[
        {"role":"system","content":"더 우수한(긴장·문학성·몰입) 쪽만 A 또는 B로 답하라."},
        {"role":"user","content":f"상황:{s}\nA: {A}\nB: {B}"}])
    w = j.choices[0].message.content.strip().upper()[:1]
    chosen, rejected = (A, B) if w == "A" else (B, A)
    pairs.append({"prompt": s+":", "chosen": " "+chosen, "rejected": " "+rejected, "judge": w})
with open("real_llm_pairs.jsonl","w",encoding="utf-8") as f:
    for p in pairs: f.write(json.dumps(p, ensure_ascii=False)+"\n")
print(f"실 LLM 선호쌍 {len(pairs)}건 저장")
