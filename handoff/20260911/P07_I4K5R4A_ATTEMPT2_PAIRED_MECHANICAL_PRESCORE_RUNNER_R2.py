import json,re
from pathlib import Path
from collections import Counter
CONTROL=[
'handoff/20260911/i4k5r4a_attempt2/control_superseding_r2/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ01_S01_05_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control_superseding_r2/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ02_S06_10_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control_superseding_r2/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ03_S11_15_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control_superseding_r2/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ04_S16_20_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control_superseding_r2/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ05_S21_25_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ06_S26_30_R1_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control_superseding_r2/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ07_S31_35_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control_superseding_r2/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ08_S36_40_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ09_S41_45_R1_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/control/P07_I4K5R4A_ATTEMPT2_CONTROL_SQ10_S46_50_R1_20260911.txt']
TREATMENT=[
'handoff/20260911/i4k5r4a_attempt2/treatment_superseding_r2/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ01_S01_05_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_superseding_r4/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ02_S06_10_R4_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_superseding_r3/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ03_S11_15_R3_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_superseding_r2/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ04_S16_20_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_superseding_r2/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ05_S21_25_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ06_S26_30_R1_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_late_superseding_r2/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ07_S31_35_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_late_superseding_r2/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ08_S36_40_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_late_superseding_r2/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ09_S41_45_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_late_superseding_r2/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ10_S46_50_R2_20260911.txt']
META=['PSSB','shared upstream','future_adoption','decision_owner','scene plan','CONTROL','owner','future thread']
EMO=['불안해','불안한','화가 난','화난','분노','슬퍼','슬픈','기뻐','기쁜','안도하','안도한','초조해','초조한','긴장하','긴장한','당황하','당황한','두려워','두려운','걱정스러운','절망','행복해','행복한']
def body(t):
 m=re.search(r'(?m)^S#\d+\.',t)
 if not m: raise RuntimeError('missing scene heading')
 return t[m.start():]
def arm(files):
 seg=[];ids=[];meta=[];emo=[];iid=[];lines=[]
 for p in files:
  b=body(Path(p).read_text(encoding='utf-8')); si=[int(x) for x in re.findall(r'(?m)^S#(\d+)\.',b)];ids+=si
  for tok in META:
   if tok.lower() in b.lower():meta.append({'file':p,'token':tok})
  for pat in EMO:
   if pat in b:emo.append({'file':p,'pattern':pat})
  for hit in re.findall(r'\b(?:CH|SQ)\d+\b',b):iid.append({'file':p,'token':hit})
  for line in b.splitlines():
   s=line.strip()
   if len(s)>=40 and not re.match(r'^S#\d+\.',s):lines.append(s)
  seg.append({'file':p,'body_chars':len(b),'scene_ids':si})
 dups=[{'line':k,'count':v} for k,v in Counter(lines).items() if v>1]
 total=sum(x['body_chars'] for x in seg)
 return {'segments':seg,'body_chars_total':total,'all_segments_min_3600_pass':all(x['body_chars']>=3600 for x in seg),'scene_ids':ids,'scene_ids_exact_1_50':ids==list(range(1,51)),'meta_leak_hits':meta,'meta_leak_zero':not meta,'CH_SQ_id_hits':iid,'CH_SQ_id_zero':not iid,'direct_emotion_pattern_hits':emo,'direct_emotion_pattern_zero':not emo,'exact_long_duplicate_lines':dups,'exact_long_duplicate_zero':not dups}
c=arm(CONTROL);t=arm(TREATMENT);gap=abs(c['body_chars_total']-t['body_chars_total'])/max(c['body_chars_total'],t['body_chars_total'])
r={'schema':'P07I4K5R4AAttempt2PairedMechanicalPrescoreR2','control':c,'treatment':t,'relative_gap':gap,'control_min_35000_pass':c['body_chars_total']>=35000,'treatment_min_35000_pass':t['body_chars_total']>=35000,'relative_gap_max_0_10_pass':gap<=0.10,'quality_inspection_performed':False}
r['mechanical_prescore_pass']=all([r['control_min_35000_pass'],r['treatment_min_35000_pass'],r['relative_gap_max_0_10_pass'],c['all_segments_min_3600_pass'],t['all_segments_min_3600_pass'],c['scene_ids_exact_1_50'],t['scene_ids_exact_1_50'],c['meta_leak_zero'],t['meta_leak_zero'],c['CH_SQ_id_zero'],t['CH_SQ_id_zero'],c['direct_emotion_pattern_zero'],t['direct_emotion_pattern_zero'],c['exact_long_duplicate_zero'],t['exact_long_duplicate_zero']])
Path('/tmp/i4k5r4a_attempt2_paired_mechanical_prescore_r2.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(r,ensure_ascii=False,indent=2))