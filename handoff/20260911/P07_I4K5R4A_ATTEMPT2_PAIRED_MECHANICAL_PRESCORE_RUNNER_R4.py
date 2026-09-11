import json,re
from pathlib import Path
from collections import Counter
CONTROL=json.loads(Path('handoff/20260911/P07_I4K5R4A_ATTEMPT2_CONTROL_CANONICAL_MANIFEST_R2_20260911.json').read_text(encoding='utf-8'))['canonical_segments']
TREATMENT=json.loads(Path('handoff/20260911/P07_I4K5R4A_ATTEMPT2_TREATMENT_CANONICAL_MANIFEST_R4_20260911.json').read_text(encoding='utf-8'))['canonical_segments']
META=['PSSB','shared upstream','future_adoption','decision_owner','scene plan','CONTROL','owner','future thread']
EMO=['불안해','불안한','화가 난','화난','분노','슬퍼','슬픈','기뻐','기쁜','안도하','안도한','초조해','초조한','긴장하','긴장한','당황하','당황한','두려워','두려운','걱정스러운','절망','행복해','행복한']
def body(t):
 m=re.search(r'(?m)^S#\d+\.',t); assert m; return t[m.start():]
def arm(files):
 seg=[];ids=[];meta=[];emo=[];iid=[];lines=[]
 for p in files:
  b=body(Path(p).read_text(encoding='utf-8')); si=[int(x) for x in re.findall(r'(?m)^S#(\d+)\.',b)];ids+=si
  meta += [{'file':p,'token':x} for x in META if x.lower() in b.lower()]
  emo += [{'file':p,'pattern':x} for x in EMO if x in b]
  iid += [{'file':p,'token':x} for x in re.findall(r'\b(?:CH|SQ)\d+\b',b)]
  lines += [s for s in map(str.strip,b.splitlines()) if len(s)>=40 and not re.match(r'^S#\d+\.',s)]
  seg.append({'file':p,'body_chars':len(b),'scene_ids':si})
 d=[{'line':k,'count':v} for k,v in Counter(lines).items() if v>1]
 total=sum(x['body_chars'] for x in seg)
 return {'segments':seg,'body_chars_total':total,'all_segments_min_3600_pass':all(x['body_chars']>=3600 for x in seg),'scene_ids_exact_1_50':ids==list(range(1,51)),'meta_leak_hits':meta,'meta_leak_zero':not meta,'CH_SQ_id_hits':iid,'CH_SQ_id_zero':not iid,'direct_emotion_pattern_hits':emo,'direct_emotion_pattern_zero':not emo,'exact_long_duplicate_lines':d,'exact_long_duplicate_zero':not d}
c=arm(CONTROL); t=arm(TREATMENT); gap=abs(c['body_chars_total']-t['body_chars_total'])/max(c['body_chars_total'],t['body_chars_total'])
r={'schema':'P07I4K5R4AAttempt2PairedMechanicalPrescoreR4','control':c,'treatment':t,'relative_gap':gap,'control_min_35000_pass':c['body_chars_total']>=35000,'treatment_min_35000_pass':t['body_chars_total']>=35000,'relative_gap_max_0_10_pass':gap<=0.10,'quality_inspection_performed':False}
r['mechanical_prescore_pass']=all([r['control_min_35000_pass'],r['treatment_min_35000_pass'],r['relative_gap_max_0_10_pass'],c['all_segments_min_3600_pass'],t['all_segments_min_3600_pass'],c['scene_ids_exact_1_50'],t['scene_ids_exact_1_50'],c['meta_leak_zero'],t['meta_leak_zero'],c['CH_SQ_id_zero'],t['CH_SQ_id_zero'],c['direct_emotion_pattern_zero'],t['direct_emotion_pattern_zero'],c['exact_long_duplicate_zero'],t['exact_long_duplicate_zero']])
Path('/tmp/i4k5r4a_attempt2_paired_mechanical_prescore_r4.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(r,ensure_ascii=False,indent=2))