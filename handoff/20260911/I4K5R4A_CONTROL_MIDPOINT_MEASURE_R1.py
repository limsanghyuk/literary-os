from pathlib import Path
import json,re,hashlib
ROOT=Path('.')
base=ROOT/'handoff/20260911/i4k5r4a_attempt1/control'
files=sorted(base.glob('P07_I4K5R4A_CONTROL_SQ0[1-5]_*.txt'))
assert len(files)==5, files
rows=[]; total=0; scene_ids=[]
for p in files:
    text=p.read_text(encoding='utf-8')
    lines=text.splitlines()
    body='\n'.join([ln for ln in lines if not ln.startswith('[P07-') and not ln.startswith('작품:')]).strip()
    n=len(body)
    ids=[int(x) for x in re.findall(r'S#(\d+)\.', text)]
    total += n; scene_ids += ids
    rows.append({'file':str(p),'body_chars':n,'sha256':hashlib.sha256(text.encode()).hexdigest(),'scene_ids':ids})
result={
 'schema':'I4K5R4AControlMidpointMeasureR1',
 'source_commit':'dcd80d12bef0fa47fae53e74c6d5d4e77ad6ad64',
 'segments':len(files),
 'scene_ids':scene_ids,
 'scene_ids_exact_1_25':scene_ids==list(range(1,26)),
 'body_chars_total':total,
 'midpoint_target_min':17500,
 'midpoint_target_pass':total>=17500,
 'simple_linear_projection_10_segments':total*2,
 'projection_above_35000':total*2>=35000,
 'rows':rows,
 'quality_inspection_performed':False
}
out=ROOT/'handoff/20260911/i4k5r4a_control_midpoint_metrics_r1.json'
out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
