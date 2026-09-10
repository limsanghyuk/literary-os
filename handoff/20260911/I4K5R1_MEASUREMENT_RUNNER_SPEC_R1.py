from pathlib import Path
import hashlib,re,json
ROOT=Path('.')
FILES={
 'CONTROL':ROOT/'handoff/20260911/P07_I4K5R1_CONTROL_WHOLE_EPISODE_PROVISIONAL_R1_20260911.txt',
 'TREATMENT':ROOT/'handoff/20260911/P07_I4K5R1_TREATMENT_WHOLE_EPISODE_PROVISIONAL_R1_20260911.txt'
}
def sha(b): return hashlib.sha256(b).hexdigest()
def body(text):
 s=text.index('S#1.')
 e=text.index('[END PROVISIONAL')
 return text[s:e].rstrip('\n')
def count_occ(s,sub): return s.count(sub)
def sentences(s):
 return [x.strip() for x in re.split(r'(?<=[.!?])\s+|\n+',s) if x.strip()]
rows={}
for arm,p in FILES.items():
 raw=p.read_bytes(); txt=raw.decode('utf-8'); b=body(txt)
 long=[x for x in sentences(b) if len(x)>=40]
 dup={x:long.count(x) for x in set(long) if long.count(x)>1}
 forbidden=['Event Ecology','thread','engine','planner','Treatment','Control']
 rows[arm]={
   'file_sha256':sha(raw),'file_bytes':len(raw),'body_chars':len(b),
   'scene_count':len(re.findall(r'(?m)^S#\d+\.',b)),
   'scene_ids':[int(x) for x in re.findall(r'(?m)^S#(\d+)\.',b)],
   'forbidden_literal_counts':{x:b.count(x) for x in forbidden},
   'CH_id_count':len(re.findall(r'\bCH\d+\b',b)),
   'SQ_id_count':len(re.findall(r'\bSQ\d+\b',b)),
   'exact_long_duplicate_sentence_count':len(dup),
   'exact_long_duplicate_examples':list(dup.items())[:20]
 }
gap=abs(rows['CONTROL']['body_chars']-rows['TREATMENT']['body_chars'])/max(rows['CONTROL']['body_chars'],rows['TREATMENT']['body_chars'])
out={'rows':rows,'relative_body_char_gap':gap}
print('I4K5R1_METRICS_JSON='+json.dumps(out,ensure_ascii=False,sort_keys=True))
