import json,re
from pathlib import Path
from collections import Counter
SOURCE_COMMIT='d264f9c247e53437e59f4d8ad6db9568d91494d2'
FILES=[
'handoff/20260911/i4k5r4a_attempt2/control_superseding_r2/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ01_S01_05_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control_superseding_r2/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ02_S06_10_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control_superseding_r2/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ03_S11_15_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control_superseding_r2/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ04_S16_20_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control_superseding_r2/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ05_S21_25_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ06_S26_30_R1_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ07_S31_35_R1_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ08_S36_40_R1_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ09_S41_45_R1_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ10_S46_50_R1_20260911.txt']
META=['PSSB','shared upstream','future_adoption','decision_owner','scene plan','TREATMENT','owner','future thread']
EMO=['불안해','불안한','화가 난','화난','분노','슬퍼','슬픈','기뻐','기쁜','안도하','안도한','초조해','초조한','긴장하','긴장한','당황하','당황한','두려워','두려운','걱정스러운','절망','행복해','행복한']
def body(t):
 m=re.search(r'(?m)^S#\d+\.',t)
 if not m: raise SystemExit('missing scene heading')
 return t[m.start():]
segments=[]; ids=[]; meta=[]; emo=[]; iid=[]; lines=[]
for p in FILES:
 b=body(Path(p).read_text(encoding='utf-8')); si=[int(x) for x in re.findall(r'(?m)^S#(\d+)\.',b)]; ids+=si
 for tok in META:
  if tok.lower() in b.lower(): meta.append({'file':p,'token':tok})
 for pat in EMO:
  if pat in b: emo.append({'file':p,'pattern':pat})
 for hit in re.findall(r'\b(?:CH|SQ)\d+\b',b): iid.append({'file':p,'token':hit})
 for line in b.splitlines():
  s=line.strip()
  if len(s)>=40 and not re.match(r'^S#\d+\.',s): lines.append(s)
 segments.append({'file':p,'body_chars':len(b),'scene_ids':si})
dups=[{'line':k,'count':v} for k,v in Counter(lines).items() if v>1]
total=sum(x['body_chars'] for x in segments)
r={'schema':'P07I4K5R4AAttempt2ControlFullGateMetricsR1','source_commit':SOURCE_COMMIT,'segments':segments,'body_chars_total':total,'body_chars_min_35000_pass':total>=35000,'all_segments_min_3600_pass':all(x['body_chars']>=3600 for x in segments),'scene_ids':ids,'scene_ids_exact_1_50':ids==list(range(1,51)),'meta_leak_hits':meta,'meta_leak_zero':not meta,'CH_SQ_id_hits':iid,'CH_SQ_id_zero':not iid,'direct_emotion_pattern_hits':emo,'direct_emotion_pattern_zero':not emo,'exact_long_duplicate_lines':dups,'exact_long_duplicate_zero':not dups,'quality_inspection_performed':False}
r['full_gate_pass']=all([r['body_chars_min_35000_pass'],r['all_segments_min_3600_pass'],r['scene_ids_exact_1_50'],r['meta_leak_zero'],r['CH_SQ_id_zero'],r['direct_emotion_pattern_zero'],r['exact_long_duplicate_zero']])
Path('/tmp/i4k5r4a_attempt2_control_full_gate_metrics.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(r,ensure_ascii=False,indent=2))