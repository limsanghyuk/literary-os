import sys, json, os, urllib.request
WORK="비밀의숲_01"
BASE="/sessions/upbeat-focused-bohr/mnt/claude/db"
KEY=open("/tmp/.oaikey").read().strip()
MODEL=os.environ.get("R_MODEL","gpt-5")
EFFORT=os.environ.get("R_EFFORT","low")
bp={}
for l in open(f"{BASE}/seqcard_ko/authored/{WORK}.seqcard.jsonl"):
    d=json.loads(l); bp[d["scene_no"]]=d
orig={}
for l in open(f"{BASE}/corpus_ko/scenes/{WORK}.jsonl"):
    d=json.loads(l); orig[d["scene_no"]]=len(d.get("text",""))
target=int(sys.argv[1])
tgt=orig.get(target,300); lo=int(tgt*0.8); hi=int(tgt*1.3)
TENS={"INTRO":"차분한 관찰, 인물 각인","ESTABLISH":"정보 제시, 낮은 긴장","BOND":"관계 형성, 온기","CONFLICT":"대립·마찰 상승","REVELATION":"폭로·전환의 충격","LOSS":"상실·하강","ORACLE":"불길한 예고","PERIL":"위기·위협 고조","DESIRE":"욕망·추동","HOOK":"다음을 끄는 미끼","RELIEF":"이완·안도"}
b=bp[target]; tens=TENS.get(b.get("core"),"장면 목적에 맞는 긴장")
prior=[]
for n in range(1,target):
    if n in bp: prior.append(f"S{n}({bp[n].get('core')}): {bp[n]['title']} — {bp[n].get('intent_gist','')[:40]}")
cont="\n".join(prior) if prior else "(없음 - 회차 첫 씬)"
SYS=("당신은 한국 드라마 대본을 쓰는 전문 극작가다. 주어진 씬 설계도(SceneBlueprint)만으로 실제 방송용 씬 산문을 집필한다. 지문과 대사를 포함하되, 원본을 본 적 없이 설계도의 의도만으로 재창작한다. 출력은 한국 드라마 대본 형식(장소/시간 헤딩 후 지문·대사). 군더더기 설명 없이 씬 본문만 출력.")
USER=f"""[연속성 - 이전 씬 흐름]
{cont}

[집필할 씬 설계도]
- 씬번호: {target}
- 장소/시간(heading): {b['heading']}
- 씬 제목(의도 요약): {b['title']}
- 극적 기능(core): {b.get('core')} / {b.get('core2')}
- 연출 톤(skin): {b.get('skin')}
- 씬 의도/목적(intent_gist): {b.get('intent_gist')}

[렌더러 제약(renderer_prompt_constraints) - 반드시 준수]
- 목표 분량: 한국어 {tgt}자 내외 (허용범위 {lo}~{hi}자). 방영 60분에서 이 씬에 배정된 분량. 초과 금지.
- 긴장 역할(tension): {tens}. 이 톤/긴장 유지, 과잉 연출·설명 지문 금지.
- 지문/대사 배분: 방송대본 지문은 간결·함축적. 인물 심리를 장황히 서술 말고 행동·대사로 드러내라.
- 이 한 씬의 목적만 달성하고 끝내라. 앞뒤 이야기를 새로 발명 말 것.

위 설계도와 제약만으로 이 씬 대본 본문을 목표 분량 내에서 써라."""
payload={"model":MODEL,"messages":[{"role":"system","content":SYS},{"role":"user","content":USER}],"max_completion_tokens":3000,"reasoning_effort":EFFORT}
req=urllib.request.Request("https://api.openai.com/v1/chat/completions",data=json.dumps(payload).encode(),headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
try:
    r=json.loads(urllib.request.urlopen(req,timeout=40).read()); out=r["choices"][0]["message"]["content"]
except Exception as e:
    out=f"__ERROR__ {e}"
open(f"/sessions/upbeat-focused-bohr/mnt/outputs/vslice/{WORK}.s{target}.con.txt","w").write(out)
print(f"scene {target}: target={tgt} range={lo}-{hi} -> out={len(out)} chars")
