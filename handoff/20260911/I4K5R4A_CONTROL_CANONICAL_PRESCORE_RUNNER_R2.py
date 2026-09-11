from pathlib import Path
import json, re, hashlib, collections
SOURCE_COMMIT='c27d403a4366f1b2bdf69bd8a83eb58c0a7e879a'
MANIFEST=Path('handoff/20260911/P07_I4K5R4A_ATTEMPT1_CONTROL_CANONICAL_MANIFEST_R1_20260911.json')
paths=[Path(p) for p in json.loads(MANIFEST.read_text(encoding='utf-8'))['segments']]
SPEAKERS={'윤재','해린','지호','선옥','태오','미라','민정','자원봉사자','직원','관리업체 직원','세척 직원'}
META_PATTERNS=[r'\bPSSB\b',r'\bCONTROL\b',r'\bTREATMENT\b',r'shared upstream',r'scene plan',r'decision owner',r'future thread',r'\bowner\b',r'\bCH\d+',r'\bSQ\d+']
DIRECT_EMOTION_PATTERNS=[r'불안(?:해한다|한 표정|해 보인다)',r'화난 표정',r'분노(?:한다|한 표정)?',r'슬퍼(?:한다| 보인다)',r'슬픈 표정',r'기뻐(?:한다| 보인다)',r'기쁜 표정',r'당황(?:한다|한 표정|해 보인다)',r'초조(?:해한다|한 표정|해 보인다)',r'긴장(?:한다|한 표정|해 보인다)',r'안도(?:한다|한 표정|해 보인다)',r'걱정(?:한다|스러운 표정|해 보인다)',r'두려워(?:한다| 보인다)',r'무서워한다',r'죄책감',r'속상(?:해한다|한 표정)',r'서운(?:해한다|한 표정)',r'행복(?:해한다|한 표정)',r'감정을 드러낸다',r'감정이 드러난다']
def body_of(text):
 m=re.search(r'(?m)^S#\d+\.',text)
 if not m: raise ValueError('no scene heading')
 return text[m.start():]
def stage_lines(body):
 lines=body.splitlines(); out=[]; in_dialog=False
 for line in lines:
  s=line.strip()
  if not s: in_dialog=False; continue
  if s in SPEAKERS: in_dialog=True; continue
  if in_dialog: continue
  out.append(line)
 return out
rows=[]; ids=[]; meta=[]; emotion=[]; all_lines=[]
for p in paths:
 text=p.read_text(encoding='utf-8'); body=body_of(text)
 scene_ids=[int(x) for x in re.findall(r'(?m)^S#(\d+)\.',body)]; ids+=scene_ids
 stage='\n'.join(stage_lines(body))
 for pat in META_PATTERNS:
  for m in re.finditer(pat,body,re.I): meta.append({'file':str(p),'pattern':pat,'match':m.group(0)})
 for pat in DIRECT_EMOTION_PATTERNS:
  for m in re.finditer(pat,stage): emotion.append({'file':str(p),'pattern':pat,'match':m.group(0)})
 lines=[ln.strip() for ln in body.splitlines() if len(ln.strip())>=40 and not re.match(r'^S#\d+\.',ln.strip())]; all_lines += lines
 rows.append({'file':str(p),'body_chars':len(body),'sha256':hashlib.sha256(text.encode()).hexdigest(),'scene_ids':scene_ids,'per_segment_min_3600_pass':len(body)>=3600})
counts=collections.Counter(all_lines); dups=[{'line':k,'count':v} for k,v in counts.items() if v>1]
result={'schema':'I4K5R4AControlCanonicalPrescoreR2','source_commit':SOURCE_COMMIT,'segments':len(paths),'body_chars_total':sum(r['body_chars'] for r in rows),'body_chars_min_35000_pass':sum(r['body_chars'] for r in rows)>=35000,'all_segments_min_3600_pass':all(r['per_segment_min_3600_pass'] for r in rows),'scene_ids':ids,'scene_ids_exact_1_50':ids==list(range(1,51)),'meta_leak_hits':meta,'meta_leak_zero':len(meta)==0,'direct_emotion_stage_hits':emotion,'direct_emotion_stage_zero':len(emotion)==0,'exact_long_duplicate_lines':dups,'exact_long_duplicate_zero':len(dups)==0,'rows':rows,'quality_inspection_performed':False}
Path('i4k5r4a_control_canonical_prescore_r2.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
if len(paths)!=10 or not all([result['body_chars_min_35000_pass'],result['all_segments_min_3600_pass'],result['scene_ids_exact_1_50'],result['meta_leak_zero'],result['direct_emotion_stage_zero'],result['exact_long_duplicate_zero']]): raise SystemExit(2)
