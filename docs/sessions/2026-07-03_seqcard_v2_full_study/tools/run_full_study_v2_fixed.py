#!/usr/bin/env python3
"""SeqCard v2 본연구 러너 스켈레톤 (집 이어작업용).
결정2: 상위 판정모델 + 3세션(=3 독립 판정 실행) 다수결.
파일럿(run: gpt_one.py)의 확장판. 실행 전 /tmp/.gptenv 또는 환경변수 OPENAI_API_KEY 필요.

사용:
  export OPENAI_API_KEY=...            # 또는 .gptenv
  python run_full_study.py <work_id> <seqcard.jsonl> [--model gpt-4.1] [--runs 3]

동작:
  1) heading+intent_gist만 판정자에게 제시(블라인드).
  2) v2.1 스키마(episode_role 6 / tension_role 앵커 / scene_blocks_need review-only)로 라벨.
  3) --runs N회 독립 판정 → 씬·필드별 다수결 + 합의도(동률=쟁점) 산출.
  4) 클로드 원본 라벨(<work>.newfields.jsonl)과 대조 → PABAK/κ 층화(analyze.py 재사용).
출력: <work>.majority.jsonl, <work>.contested.jsonl
"""
import json, os, sys, urllib.request, collections, argparse

SYS_V21 = """당신은 한국 드라마 극작 구조 분석가입니다. 각 씬(heading+intent_gist)을 회차 아크 맥락에서 독립 라벨링. 연속 점수 금지.
- episode_role ∈ {opening,setup,development,complication,climax,resolution}  # v2.1 6분류
- tension_role ∈ {build,peak,release,bridge}  # build=직전대비 상승, peak=국소정점, release=하강/이완, bridge=긴장무관 연결
- hook_flag(bool) 막/회차말 클리프행어
- continuity_break(bool) 직전 씬과 서사 급단절
- scene_blocks_need(bool)+need_ref  # want추구가 명시된 need에 비용발생시 true, need 미명시면 false
각 씬 reason(8단어 이내). 반드시 순수 json 형식으로만 출력하라. 출력 {"labels":[{scene_no,episode_role,tension_role,hook_flag,continuity_break,scene_blocks_need,need_ref,reason}...]}"""

def key():
    k=os.environ.get("OPENAI_API_KEY")
    if not k and os.path.exists("/tmp/.gptenv"):
        for l in open("/tmp/.gptenv"):
            if l.startswith("OPENAI_API_KEY="): k=l.split("=",1)[1].strip()
    assert k,"no OPENAI_API_KEY"; return k

def judge(scenes, work, model, K):
    u=f"작품:{work}. {len(scenes)}개 씬 전체를 읽고 라벨.\n\n"
    for s in scenes: u+=f'[씬 {s["scene_no"]}] {s["heading"]} | {s.get("title","")}\n요약:{s["intent_gist"]}\n\n'
    body=json.dumps({"model":model,"temperature":0.4,"response_format":{"type":"json_object"},
        "messages":[{"role":"system","content":SYS_V21},{"role":"user","content":u}]}).encode()
    r=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=body,
        headers={"Authorization":f"Bearer {K}","Content-Type":"application/json"})
    return json.loads(json.load(urllib.request.urlopen(r,timeout=300))["choices"][0]["message"]["content"])["labels"]

def main():
    ap=argparse.ArgumentParser(); ap.add_argument("work"); ap.add_argument("path")
    ap.add_argument("--model",default="gpt-4.1"); ap.add_argument("--runs",type=int,default=3)
    a=ap.parse_args(); K=key()
    sc=[{"scene_no":r["scene_no"],"heading":r.get("heading",""),"title":r.get("title",""),"intent_gist":r.get("intent_gist","")}
        for r in (json.loads(l) for l in open(a.path))]
    runs=[{x["scene_no"]:x for x in judge(sc,a.work,a.model,K)} for _ in range(a.runs)]  # 주의: 대형 회차는 배치 분할 필요(파일럿의 33씬 분할 참고)
    FIELDS=["episode_role","tension_role","hook_flag","continuity_break","scene_blocks_need"]
    maj=[]; contested=[]
    for s in sorted(runs[0]):
        rec={"scene_no":s}; dis=[]
        for f in FIELDS:
            votes=[r[s].get(f) for r in runs if s in r]
            c=collections.Counter(map(str,votes)); top,n=c.most_common(1)[0]
            rec[f]=top; rec[f+"_agree"]=n/len(votes)
            if n<len(votes): dis.append(f)
        rec["contested_fields"]=dis; maj.append(rec)
        if dis: contested.append({"scene_no":s,"fields":dis})
    json.dump(maj,open(f"{a.work}.majority.jsonl","w"),ensure_ascii=False)
    json.dump(contested,open(f"{a.work}.contested.jsonl","w"),ensure_ascii=False)
    print(f"{a.work}: {len(maj)}씬 다수결, 쟁점 {len(contested)}씬. → analyze.py로 클로드 원본과 층화 대조.")

if __name__=="__main__": main()
