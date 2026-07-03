import sys, json, os, urllib.request

WORK="비밀의숲_01"
BASE="/sessions/upbeat-focused-bohr/mnt/claude/db"
KEY=open("/tmp/.oaikey").read().strip()
MODEL=os.environ.get("R_MODEL","gpt-5")
EFFORT=os.environ.get("R_EFFORT","low")

# load blueprints
bp={}
for l in open(f"{BASE}/seqcard_ko/authored/{WORK}.seqcard.jsonl"):
    d=json.loads(l); bp[d["scene_no"]]=d

target=int(sys.argv[1])
# running continuity: titles of prior scenes 1..target-1
prior=[]
for n in range(1,target):
    if n in bp:
        prior.append(f"S{n}({bp[n].get('core')}): {bp[n]['title']} — {bp[n].get('intent_gist','')[:40]}")
cont="\n".join(prior) if prior else "(없음 - 회차 첫 씬)"

b=bp[target]
SYS=("당신은 한국 드라마 대본을 쓰는 전문 극작가다. 주어진 씬 설계도(SceneBlueprint)만으로 "
     "실제 방송용 씬 산문을 집필한다. 지문과 대사를 포함하되, 원본을 본 적 없이 설계도의 의도만으로 재창작한다. "
     "출력은 한국 드라마 대본 형식(장소/시간 헤딩 후 지문·대사). 군더더기 설명 없이 씬 본문만 출력.")
USER=f"""[연속성 - 이전 씬 흐름]
{cont}

[집필할 씬 설계도]
- 씬번호: {target}
- 장소/시간(heading): {b['heading']}
- 씬 제목(의도 요약): {b['title']}
- 극적 기능(core): {b.get('core')} / {b.get('core2')}
- 연출 톤(skin): {b.get('skin')}
- 씬 의도(intent_gist): {b.get('intent_gist')}

위 설계도만으로 이 씬의 실제 대본 본문을 써라. 분량은 원본 방송 1씬 수준(과도하게 길지 않게)."""

payload={"model":MODEL,"messages":[{"role":"system","content":SYS},{"role":"user","content":USER}],
         "max_completion_tokens":3000,"reasoning_effort":EFFORT}
req=urllib.request.Request("https://api.openai.com/v1/chat/completions",
    data=json.dumps(payload).encode(), headers={"Authorization":f"Bearer {KEY}","Content-Type":"application/json"})
try:
    r=json.loads(urllib.request.urlopen(req,timeout=40).read())
    out=r["choices"][0]["message"]["content"]
except Exception as e:
    out=f"__ERROR__ {e}"
open(f"/sessions/upbeat-focused-bohr/mnt/outputs/vslice/{WORK}.s{target}.gen.txt","w").write(out)
print(f"scene {target}: {len(out)} chars")
