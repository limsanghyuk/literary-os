# -*- coding: utf-8 -*-
import json,subprocess,re
OAI=open('/tmp/.oai').read().strip()
SCN='/sessions/dreamy-affectionate-rubin/mnt/claude/db/corpus_ko/scenes'
def call(sysp,usr,mt=1200):
    body=json.dumps({"model":"gpt-4o-mini","temperature":0.2,"max_tokens":mt,
      "messages":[{"role":"system","content":sysp},{"role":"user","content":usr}]})
    r=subprocess.run(['curl','-s','--max-time','40','https://api.openai.com/v1/chat/completions',
      '-H',f'Authorization: Bearer {OAI}','-H','Content-Type: application/json','-d',body],
      capture_output=True,text=True)
    c=json.loads(r.stdout)['choices'][0]['message']['content']
    return re.sub(r'^```json|```$','',c.strip(),flags=re.M).strip()
rows=[json.loads(l) for l in open(f'{SCN}/대장금_01.jsonl',encoding='utf-8') if l.strip()]
N=14
items=[{"scene_no":r["scene_no"],"본문":re.sub(r'\s+',' ',r["text"])[:420]} for r in rows[:N]]
SYS=("너는 드라마 대본을 씬 단위로 분석하는 스토리 분석가다. 각 씬 본문을 읽고 그 씬의 '설계도'를 만든다. "
     "각 씬마다 JSON: {scene_no, 소제목(그 씬의 핵심 사건/전환을 압축한 6~14자 제목, 장소슬러그 말고 '무슨 일'), "
     "설명(1~2문장: 누가 무엇을 하고 그 결과/정보가 무엇인가), "
     "극적기능(갈등촉발|상승|반전|해소|복선심기|복선회수|관계전환|정보공개|잔향 중 1), "
     "주요인물([이름..])}. 배열만 출력, 군더더기 없이.")
out=call(SYS, json.dumps(items,ensure_ascii=False))
try:
    briefs=json.loads(out)
    for b in briefs:
        print(f"#{b['scene_no']:>2} [{b.get('극적기능','')}] {b.get('소제목','')}")
        print(f"     {b.get('설명','')}  · 인물:{','.join(b.get('주요인물',[]))}")
    json.dump(briefs,open('/tmp/brief_pilot_out.json','w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print(f"\nOK {len(briefs)}씬 brief 생성")
except Exception as e:
    print("parse err",e); print(out[:600])
