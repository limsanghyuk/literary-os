from pathlib import Path
import json,re,hashlib,collections
SOURCE_COMMIT='24ce709fe39f2d236c6f5ed7cd721fa0d846ee59'
ROOT=Path('handoff/20260911/i4k5r4a_attempt1/treatment')
files=sorted(ROOT.glob('P07_I4K5R4A_TREATMENT_SQ0[1-5]*_R1_20260911.txt'))
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
rows=[]; ids=[]; mh=[]; eh=[]; long=[]
for p in files:
 t=p.read_text(encoding='utf-8'); b=body(t); st=stage(b); si=[int(x) for x in re.findall(r'(?m)^S#(\d+)\.',b)]; ids+=si
 for q in META:
  for m in re.finditer(q,b,re.I): mh.append({'file':str(p),'pattern':q,'match':m.group(0)})
 for q in EMO:
  for m in re.finditer(q,st): eh.append({'file':str(p),'pattern':q,'match':m.group(0)})
 long += [x.strip() for x in b.splitlines() if len(x.strip())>=40 and not re.match(r'^S#\d+\.',x.strip())]
 rows.append({'file':str(p),'body_chars':len(b),'sha256':hashlib.sha256(t.encode()).hexdigest(),'scene_ids':si,'per_segment_min_3600_pass':len(b)>=3600})
c=collections.Counter(long); dup=[{'line':k,'count':v} for k,v in c.items() if v>1]
r={'schema':'I4K5R4ATreatmentMidpointPrescoreR1','source_commit':SOURCE_COMMIT,'segments':len(files),'body_chars_total':sum(x['body_chars'] for x in rows),'midpoint_min_18000_pass':sum(x['body_chars'] for x in rows)>=18000,'all_segments_min_3600_pass':all(x['per_segment_min_3600_pass'] for x in rows),'scene_ids_exact_1_25':ids==list(range(1,26)),'meta_leak_hits':mh,'meta_leak_zero':len(mh)==0,'direct_emotion_stage_hits':eh,'direct_emotion_stage_zero':len(eh)==0,'exact_long_duplicate_lines':dup,'exact_long_duplicate_zero':len(dup)==0,'rows':rows,'quality_inspection_performed':False}
Path('i4k5r4a_treatment_midpoint_prescore_r1.json').write_text(json.dumps(r,ensure_ascii=False,indent=2),encoding='utf-8')
if len(files)!=5 or not all([r['midpoint_min_18000_pass'],r['all_segments_min_3600_pass'],r['scene_ids_exact_1_25'],r['meta_leak_zero'],r['direct_emotion_stage_zero'],r['exact_long_duplicate_zero']]): raise SystemExit(2)
