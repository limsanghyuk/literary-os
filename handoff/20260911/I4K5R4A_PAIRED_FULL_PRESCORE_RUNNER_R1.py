from pathlib import Path
import json,re,hashlib,collections
SOURCE_COMMIT='27f35eb5b63ca9202d1a6249e82a5dae0dc713dc'
BASE=Path('handoff/20260911/i4k5r4a_attempt1')
CONTROL=[
 BASE/'control_superseding_r2'/'P07_I4K5R4A_CONTROL_SQ01_S01_05_R2_20260911.txt',
 BASE/'control_superseding_r2'/'P07_I4K5R4A_CONTROL_SQ02_S06_10_R2_20260911.txt',
 BASE/'control_superseding_r2'/'P07_I4K5R4A_CONTROL_SQ03_S11_15_R2_20260911.txt',
 BASE/'control_superseding_r2'/'P07_I4K5R4A_CONTROL_SQ04_S16_20_R2_20260911.txt',
 BASE/'control_superseding_r2'/'P07_I4K5R4A_CONTROL_SQ05_S21_25_R2_20260911.txt',
 BASE/'control_superseding_r3'/'P07_I4K5R4A_CONTROL_SQ06_S26_30_R3_20260911.txt',
 BASE/'control_superseding_r3'/'P07_I4K5R4A_CONTROL_SQ07_S31_35_R3_20260911.txt',
 BASE/'control_superseding_r3'/'P07_I4K5R4A_CONTROL_SQ08_S36_40_R3_20260911.txt',
 BASE/'control_superseding_r3'/'P07_I4K5R4A_CONTROL_SQ09_S41_45_R3_20260911.txt',
 BASE/'control_superseding_r3'/'P07_I4K5R4A_CONTROL_SQ10_S46_50_R3_20260911.txt',
]
TREATMENT=[
 BASE/'treatment'/'P07_I4K5R4A_TREATMENT_SQ01_S01_05_R1_20260911.txt',
 BASE/'treatment_superseding_r2'/'P07_I4K5R4A_TREATMENT_SQ02_S06_10_R2_20260911.txt',
 BASE/'treatment_superseding_r2'/'P07_I4K5R4A_TREATMENT_SQ03_S11_15_R2_20260911.txt',
 BASE/'treatment_superseding_r2'/'P07_I4K5R4A_TREATMENT_SQ04_S16_20_R2_20260911.txt',
 BASE/'treatment_superseding_r2'/'P07_I4K5R4A_TREATMENT_SQ05_S21_25_R2_20260911.txt',
 BASE/'treatment'/'P07_I4K5R4A_TREATMENT_SQ06_S26_30_R1_20260911.txt',
 BASE/'treatment'/'P07_I4K5R4A_TREATMENT_SQ07_S31_35_R1_20260911.txt',
 BASE/'treatment'/'P07_I4K5R4A_TREATMENT_SQ08_S36_40_R1_20260911.txt',
 BASE/'treatment'/'P07_I4K5R4A_TREATMENT_SQ09_S41_45_R1_20260911.txt',
 BASE/'treatment'/'P07_I4K5R4A_TREATMENT_SQ10_S46_50_R1_20260911.txt',
]
SPEAKERS={'윤재','해린','지호','선옥','태오','미라','민정','자원봉사자','직원','관리업체 직원','세척 직원'}
META=[r'\bPSSB\b',r'\bCONTROL\b',r'\bTREATMENT\b',r'shared upstream',r'scene plan',r'decision owner',r'future thread',r'\bowner\b',r'\bCH\d+',r'\bSQ\d+']
EMO=[r'불안(?:해한다|한 표정|해 보인다)',r'화난 표정',r'분노(?:한다|한 표정)?',r'슬퍼(?:한다| 보인다)',r'슬픈 표정',r'기뻐(?:한다| 보인다)',r'기쁜 표정',r'당황(?:한다|한 표정|해 보인다)',r'초조(?:해한다|한 표정|해 보인다)',r'긴장(?:한다|한 표정|해 보인다)',r'안도(?:한다|한 표정|해 보인다)',r'걱정(?:한다|스러운 표정|해 보인다)',r'두려워(?:한다| 보인다)',r'무서워한다',r'죄책감',r'속상(?:해한다|한 표정)',r'서운(?:해한다|한 표정)',r'행복(?:해한다|한 표정)',r'감정을 드러낸다',r'감정이 드러난다']
def body(t):
 m=re.search(r'(?m)^S#\d+\.',t)
 if not m: raise ValueError('no scene')
 return t[m.start():]
def stage(b):
 out=[]; ind=False
 for line in b.splitlines():
  s=line.strip()
  if not s: ind=False; continue
  if s in SPEAKERS: ind=True; continue
  if ind: continue
  out.append(line)
 return '\n'.join(out)
def measure(files,arm):
 rows=[]; ids=[]; mh=[]; eh=[]; long=[]; bodies=[]
 for p in files:
  if not p.exists(): raise FileNotFoundError(p)
  t=p.read_text(encoding='utf-8'); b=body(t); st=stage(b); bodies.append(b)
  si=[int(x) for x in re.findall(r'(?m)^S#(\d+)\.',b)]; ids+=si
  for q in META:
   for m in re.finditer(q,b,re.I): mh.append({'file':str(p),'pattern':q,'match':m.group(0)})
  for q in EMO:
   for m in re.finditer(q,st): eh.append({'file':str(p),'pattern':q,'match':m.group(0)})
  long += [x.strip() for x in b.splitlines() if len(x.strip())>=40 and not re.match(r'^S#\d+\.',x.strip())]
  rows.append({'file':str(p),'body_chars':len(b),'sha256':hashlib.sha256(t.encode()).hexdigest(),'scene_ids':si,'per_segment_min_3600_pass':len(b)>=3600})
 c=collections.Counter(long); dup=[{'line':k,'count':v} for k,v in c.items() if v>1]
 logical='\n'.join(bodies).encode('utf-8')
 return {'arm':arm,'segments':len(files),'body_chars_total':sum(x['body_chars'] for x in rows),'all_segments_min_3600_pass':all(x['per_segment_min_3600_pass'] for x in rows),'scene_ids_exact_1_50':ids==list(range(1,51)),'meta_leak_hits':mh,'meta_leak_zero':len(mh)==0,'direct_emotion_stage_hits':eh,'direct_emotion_stage_zero':len(eh)==0,'exact_long_duplicate_lines':dup,'exact_long_duplicate_zero':len(dup)==0,'logical_join_sha256':hashlib.sha256(logical).hexdigest(),'rows':rows}
c=measure(CONTROL,'CONTROL'); t=measure(TREATMENT,'TREATMENT')
gap=abs(t['body_chars_total']-c['body_chars_total'])/c['body_chars_total'] if c['body_chars_total'] else 999
r={'schema':'I4K5R4APairedFullPrescoreR1','source_commit':SOURCE_COMMIT,'control':c,'treatment':t,'control_min_35000_pass':c['body_chars_total']>=35000,'treatment_min_35000_pass':t['body_chars_total']>=35000,'relative_body_char_gap':gap,'relative_body_char_gap_max_0_10_pass':gap<=0.10,'quality_inspection_performed':False,'mask':0,'independent_judge_scores':0,'mapping_open':0}
allpass=(c['segments']==10 and t['segments']==10 and r['control_min_35000_pass'] and r['treatment_min_35000_pass'] and r['relative_body_char_gap_max_0_10_pass'] and c['all_segments_min_3600_pass'] and t['all_segments_min_3600_pass'] and c['scene_ids_exact_1_50'] and t['scene_ids_exact_1_50'] and c['meta_leak_zero'] and t['meta_leak_zero'] and c['direct_emotion_stage_zero'] and t['direct_emotion_stage_zero'] and c['exact_long_duplicate_zero'] and t['exact_long_duplicate_zero'])
r['overall_mechanical_prescore_pass']=allpass
Path('i4k5r4a_paired_full_prescore_r1.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
if not allpass: raise SystemExit(2)
