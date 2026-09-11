from pathlib import Path
import json, re, hashlib

SOURCE_COMMIT = '4ee0efeeab17759e1273231638c578fd7cabb3a2'
ROOT = Path('handoff/20260911/i4k5r4a_attempt1/control_superseding_r2')
files = sorted(ROOT.glob('P07_I4K5R4A_CONTROL_SQ*_R2_20260911.txt'))
rows=[]
all_ids=[]
for p in files:
    text=p.read_text(encoding='utf-8')
    m=re.search(r'(?m)^S#\d+\.', text)
    if not m:
        raise SystemExit(f'no scene heading: {p}')
    body=text[m.start():]
    ids=[int(x) for x in re.findall(r'(?m)^S#(\d+)\.', body)]
    all_ids.extend(ids)
    rows.append({
        'file':str(p),
        'body_chars':len(body),
        'sha256':hashlib.sha256(text.encode('utf-8')).hexdigest(),
        'scene_ids':ids,
        'per_segment_min_3600_pass':len(body)>=3600,
    })
result={
    'schema':'I4K5R4AControlR2MidpointMeasureR1',
    'source_commit':SOURCE_COMMIT,
    'segments':len(files),
    'scene_ids':all_ids,
    'scene_ids_exact_1_25':all_ids==list(range(1,26)),
    'body_chars_total':sum(r['body_chars'] for r in rows),
    'midpoint_target_min':18000,
    'midpoint_target_pass':sum(r['body_chars'] for r in rows)>=18000,
    'all_segments_min_3600_pass':all(r['per_segment_min_3600_pass'] for r in rows),
    'rows':rows,
    'quality_inspection_performed':False,
}
Path('i4k5r4a_control_r2_midpoint_metrics_r1.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
if len(files)!=5 or not result['scene_ids_exact_1_25'] or not result['midpoint_target_pass'] or not result['all_segments_min_3600_pass']:
    raise SystemExit(2)
