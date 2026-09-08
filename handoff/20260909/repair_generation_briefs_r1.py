#!/usr/bin/env python3
import io, os, json, hashlib, zipfile, pathlib

ROOT=pathlib.Path('/mnt/data/i4h_prospective_work')
PARTS=[ROOT/'db59_parts/db59.part001', ROOT/'db59_parts/db59.part002']
FREEZE=ROOT/'sample_freeze/P07_I4H_PROSPECTIVE_SAMPLE_FREEZE_R1_20260909.json'
OUT=ROOT/'sample_freeze'
RUNTIME_ROOT='seqcard_ko/reinforcement_v1/runtime_scene_projection/'

class SplitReader(io.RawIOBase):
    def __init__(self, paths):
        self.files=[open(p,'rb') for p in paths]
        self.sizes=[os.path.getsize(p) for p in paths]
        self.starts=[]; s=0
        for z in self.sizes: self.starts.append(s); s+=z
        self.total=s; self.pos=0
    def readable(self): return True
    def seekable(self): return True
    def tell(self): return self.pos
    def seek(self, off, whence=io.SEEK_SET):
        if whence==io.SEEK_SET: p=off
        elif whence==io.SEEK_CUR: p=self.pos+off
        elif whence==io.SEEK_END: p=self.total+off
        else: raise ValueError(whence)
        if p<0: raise ValueError('negative seek')
        self.pos=p; return p
    def read(self,n=-1):
        if n is None or n<0: n=self.total-self.pos
        n=min(n,self.total-selfpos) if False else min(n,self.total-self.pos)
        if n<=0: return b''
        out=[]; rem=n
        while rem and self.pos<self.total:
            i=max(i for i,st in enumerate(self.starts) if st<=self.pos)
            local=self.pos-self.starts[i]
            take=min(rem,self.sizes[i]-local)
            self.files[i].seek(local); chunk=self.files[i].read(take)
            if not chunk: break
            out.append(chunk); self.pos+=len(chunk); rem-=len(chunk)
        return b''.join(out)
    def readinto(self,b):
        c=self.read(len(b)); b[:len(c)]=c; return len(c)
    def close(self):
        for f in self.files: f.close()
        super().close()

def cbytes(obj): return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def sha(b): return hashlib.sha256(b).hexdigest()
def replace(value,mapping):
    if isinstance(value,str):
        out=value
        for old,new in sorted(mapping.items(),key=lambda kv:(-len(kv[0]),kv[0])):
            out=out.replace(old,new)
        return out
    if isinstance(value,list): return [replace(x,mapping) for x in value]
    if isinstance(value,dict): return {k:replace(v,mapping) for k,v in value.items()}
    return value

def make_brief(rec, sid, cohort, all_names):
    scene_chars=list(rec.get('characters') or [])
    speaker_map={name:f'P{i+1}' for i,name in enumerate(scene_chars)}
    context_names=sorted(set(all_names)-set(scene_chars))
    context_map={name:f'X{i+1}' for i,name in enumerate(context_names)}
    mapping={**context_map,**speaker_map}
    cs=[]
    for x in rec.get('character_states') or []:
        cs.append({'character':mapping.get(x.get('character'),x.get('character')),
                   'sequence_function':replace(x.get('sequence_function'),mapping),
                   'participation':x.get('participation')})
    infos=[]
    for x in rec.get('info_context') or []:
        infos.append({'subject':replace(x.get('subject'),mapping),'before':replace(x.get('before'),mapping),
                      'after':replace(x.get('after'),mapping),'mode':x.get('mode')})
    pp=[]
    for x in rec.get('plant_payoff_context') or []:
        if isinstance(x,dict): pp.append({'kind':x.get('kind'),'statement':replace(x.get('statement'),mapping)})
    brief={
      'scene_id':sid,'cohort':cohort,'characters':[speaker_map[x] for x in scene_chars],
      'primary_pov':mapping.get(rec.get('primary_pov'),rec.get('primary_pov')),
      'secondary_pov':[mapping.get(x,x) for x in (rec.get('secondary_pov') or [])],
      'character_states':cs,
      'event_context':replace(rec.get('event_context'),mapping),
      'info_context':infos,
      'plant_payoff_context':pp,
      'functional_propositions':replace(rec.get('functional_propositions') or [],mapping),
      'generation_notice':'Derived structural brief only. No source dialogue/prose is supplied. Render a fresh Korean drama scene; do not imitate a known work.'
    }
    return brief,mapping

freeze=json.loads(FREEZE.read_text(encoding='utf-8'))
selected=freeze['selected']
works=sorted({x['source_work_id'] for x in selected})
all_names={w:set() for w in works}
records={}

with zipfile.ZipFile(SplitReader(PARTS)) as z:
    work_files={w:[n for n in z.namelist() if n.startswith(RUNTIME_ROOT+w+'/') and n.endswith('.runtime_scene_projection.jsonl')] for w in works}
    for w,files in work_files.items():
        for name in files:
            with z.open(name) as fh:
                for raw in fh:
                    try: rec=json.loads(raw)
                    except Exception: continue
                    for ch in rec.get('characters') or []:
                        if isinstance(ch,str) and ch.strip(): all_names[w].add(ch.strip())
                    for st in rec.get('character_states') or []:
                        ch=st.get('character') if isinstance(st,dict) else None
                        if isinstance(ch,str) and ch.strip(): all_names[w].add(ch.strip())
    by_path={}
    for item in selected: by_path.setdefault(item['archive_path'],[]).append(item)
    for path,items in by_path.items():
        wanted={i['archive_line_no']:i for i in items}
        with z.open(path) as fh:
            for line_no,raw in enumerate(fh,1):
                if line_no not in wanted: continue
                rec=json.loads(raw)
                rec_sha=sha(cbytes(rec))
                if rec_sha!=wanted[line_no]['record_sha256']:
                    raise SystemExit(f'RECORD_SHA_MISMATCH {wanted[line_no]["scene_id"]}')
                records[wanted[line_no]['scene_id']]=rec

briefs=[]; audit=[]
for item in selected:
    sid=item['scene_id']; w=item['source_work_id']; rec=records[sid]
    brief,mapping=make_brief(rec,sid,item['cohort'],all_names[w])
    text=json.dumps(brief,ensure_ascii=False)
    remaining=sorted([n for n in all_names[w] if n and n in text])
    if remaining:
        raise SystemExit(f'HOLD_DEIDENTIFICATION {sid} remaining={remaining}')
    bsha=sha(cbytes(brief))
    briefs.append(brief)
    audit.append({'scene_id':sid,'known_character_names_in_work':len(all_names[w]),
                  'selected_speakers':len(rec.get('characters') or []),'mapping_entries':len(mapping),
                  'remaining_known_name_hits':0,'brief_sha256':bsha})

payload={'schema':'P07I4HProspectiveGenerationBriefsR2','date':'2026-09-09',
         'parent_sample_freeze_sha256':sha(cbytes(freeze)),
         'amendment':'P07_I4H_PROSPECTIVE_PREREG_AMENDMENT_R1_DEIDENTIFICATION_REPAIR_20260909.json',
         'briefs':briefs,'source_prose_included':False,'status':'GENERATION_INPUT_R2_FROZEN__DEIDENTIFICATION_AUDIT_PASS'}
payload_sha=sha(cbytes(payload)); payload['canonical_payload_sha256']=payload_sha
report={'schema':'P07I4HProspectiveDeidentificationAuditR1','date':'2026-09-09','scenes':audit,
        'scene_count':len(audit),'remaining_known_character_name_hits_total':0,
        'status':'PASS__24_OF_24__NO_KNOWN_WORK_CHARACTER_NAME_HITS__NO_GENERATION'}
report_sha=sha(cbytes(report)); report['canonical_payload_sha256']=report_sha

p=OUT/'P07_I4H_PROSPECTIVE_GENERATION_BRIEFS_R2_20260909.json'
a=OUT/'P07_I4H_PROSPECTIVE_DEIDENTIFICATION_AUDIT_R1_20260909.json'
p.write_text(json.dumps(payload,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
a.write_text(json.dumps(report,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
print(json.dumps({'briefs':str(p),'brief_file_sha256':sha(p.read_bytes()),'payload_sha256':payload_sha,
                  'audit':str(a),'audit_file_sha256':sha(a.read_bytes()),'audit_payload_sha256':report_sha,
                  'scene_count':len(audit),'remaining_hits':0},ensure_ascii=False,indent=2))
