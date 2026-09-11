from pathlib import Path
import json,re
root=Path('handoff/20260911/i4k5r3_attempt2/control')
files=sorted(root.glob('P07_I4K5R3_A2_CONTROL_SQ*_SC*.txt'))
rows=[]; total=0; ids=[]
for p in files:
    t=p.read_text(encoding='utf-8')
    m=re.search(r'(?m)^S#\d+\.',t)
    e=t.rfind('[END ATTEMPT2')
    if not m or e<0: raise SystemExit('bad segment '+p.name)
    body=t[m.start():e].rstrip('\n')
    scene=[int(x) for x in re.findall(r'(?m)^S#(\d+)\.',body)]
    rows.append({'name':p.name,'body_chars':len(body),'scene_ids':scene})
    total+=len(body); ids.extend(scene)
out={'segment_count':len(files),'body_chars':total,'scene_count':len(ids),'scene_ids_exact_1_50':ids==list(range(1,51)),'segments':rows,'body_ge_35000':total>=35000}
Path('_i4k5r3_a2c').mkdir(exist_ok=True)
Path('_i4k5r3_a2c/metrics.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps(out,ensure_ascii=False))
