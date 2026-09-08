#!/usr/bin/env python3
import io, os, json, hashlib, zipfile, re, pathlib

DB59_SHA='a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9'
SEED=f'P07-I4H-PROSP-CRAFT-R1|DB59={DB59_SHA}'
PARTS=[
 '/mnt/data/i4h_prospective_work/db59_parts/db59.part001',
 '/mnt/data/i4h_prospective_work/db59_parts/db59.part002'
]
OUT=pathlib.Path('/mnt/data/i4h_prospective_work/sample_freeze')
OUT.mkdir(parents=True, exist_ok=True)
POINTER='seqcard_ko/reinforcement_v1/CURRENT_PLANNER_RUNTIME_AUTHORITY_POINTER.json'
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
        n=min(n,self.total-self.pos)
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

def canonical_bytes(obj):
    return json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
def sha_bytes(b): return hashlib.sha256(b).hexdigest()
def rank_for(rec, rec_sha):
    material=f"{SEED}|{rec['work_id']}|{rec['episode_no']}|{rec['scene_no']}|{rec_sha}"
    return hashlib.sha256(material.encode('utf-8')).hexdigest()
def eligible(rec, canonical_works, holds):
    if rec.get('schema')!='DB98_RUNTIME_SCENE_PROJECTION_V1': return False
    if rec.get('work_id') not in canonical_works or rec.get('work_id') in holds: return False
    chars=rec.get('characters') or []
    if not (2<=len(chars)<=5): return False
    if not str(rec.get('event_context') or '').strip(): return False
    if not (rec.get('info_context') or []): return False
    if not (rec.get('functional_propositions') or []): return False
    return True
def is_info_challenge(rec):
    modes={str(x.get('mode','')).upper() for x in (rec.get('info_context') or []) if isinstance(x,dict)}
    opp=any(str(x.get('participation','')).upper()=='OPPOSITION' for x in (rec.get('character_states') or []) if isinstance(x,dict))
    return bool(modes & {'REVEAL','STATE_CHANGE'}) and (opp or len(rec.get('functional_propositions') or [])>=2)
def is_relational(rec):
    if len(rec.get('characters') or [])!=2: return False
    modes={str(x.get('mode','')).upper() for x in (rec.get('info_context') or []) if isinstance(x,dict)}
    if 'STATE_CHANGE' not in modes: return False
    states=[x for x in (rec.get('character_states') or []) if isinstance(x,dict)]
    if any(str(x.get('participation','')).upper()=='OPPOSITION' for x in states): return False
    sec=bool(rec.get('secondary_pov') or [])
    primaries=sum(str(x.get('participation','')).upper()=='PRIMARY' for x in states)>=2
    return sec or primaries

def replace_names(value, mapping):
    if isinstance(value,str):
        out=value
        for old,new in sorted(mapping.items(),key=lambda kv:len(kv[0]),reverse=True):
            out=out.replace(old,new)
        return out
    if isinstance(value,list): return [replace_names(x,mapping) for x in value]
    if isinstance(value,dict): return {k:replace_names(v,mapping) for k,v in value.items()}
    return value

def make_brief(rec, scene_id, cohort):
    chars=rec['characters']; mapping={name:f'P{i+1}' for i,name in enumerate(chars)}
    cs=[]
    for x in rec.get('character_states') or []:
        cs.append({'character':mapping.get(x.get('character'),x.get('character')),
                   'sequence_function':replace_names(x.get('sequence_function'),mapping),
                   'participation':x.get('participation')})
    infos=[]
    for x in rec.get('info_context') or []:
        infos.append({'subject':replace_names(x.get('subject'),mapping),'before':replace_names(x.get('before'),mapping),
                      'after':replace_names(x.get('after'),mapping),'mode':x.get('mode')})
    pp=[]
    for x in rec.get('plant_payoff_context') or []:
        if isinstance(x,dict): pp.append({'kind':x.get('kind'),'statement':replace_names(x.get('statement'),mapping)})
    brief={
      'scene_id':scene_id,'cohort':cohort,'characters':[mapping[x] for x in chars],
      'primary_pov':mapping.get(rec.get('primary_pov'),rec.get('primary_pov')),
      'secondary_pov':[mapping.get(x,x) for x in (rec.get('secondary_pov') or [])],
      'character_states':cs,
      'event_context':replace_names(rec.get('event_context'),mapping),
      'info_context':infos,
      'plant_payoff_context':pp,
      'functional_propositions':replace_names(rec.get('functional_propositions') or [],mapping),
      'generation_notice':'Derived structural brief only. No source dialogue/prose is supplied. Render a fresh Korean drama scene; do not imitate a known work.'
    }
    return brief,mapping

with zipfile.ZipFile(SplitReader(PARTS)) as z:
    pointer=json.loads(z.read(POINTER))
    manifest_name='seqcard_ko/reinforcement_v1/'+pointer['manifest']
    manifest=json.loads(z.read(manifest_name))
    canonical=set(manifest['canonical_works']); holds=set(pointer.get('source_hold_works') or [])
    runtime_files=[n for n in z.namelist() if n.startswith(RUNTIME_ROOT) and n.endswith('.runtime_scene_projection.jsonl')]
    top={work:{'NATURAL':None,'INFO_CHALLENGE':None,'RELATIONAL_SUBTEXT':None} for work in canonical}
    counts={'records_seen':0,'eligible':0,'info':0,'relational':0}
    for name in runtime_files:
        work=name[len(RUNTIME_ROOT):].split('/',1)[0]
        if work not in canonical or work in holds: continue
        with z.open(name) as fh:
            for line_no,raw in enumerate(fh,1):
                counts['records_seen']+=1
                try: rec=json.loads(raw)
                except Exception: continue
                if not eligible(rec,canonical,holds): continue
                counts['eligible']+=1
                rec_sha=sha_bytes(canonical_bytes(rec)); rank=rank_for(rec,rec_sha)
                cand={'rank':rank,'record_sha256':rec_sha,'archive_path':name,'line_no':line_no,'record':rec}
                def keep(kind):
                    cur=top[work][kind]
                    if cur is None or rank<cur['rank']: top[work][kind]=cand
                keep('NATURAL')
                if is_info_challenge(rec): counts['info']+=1; keep('INFO_CHALLENGE')
                if is_relational(rec): counts['relational']+=1; keep('RELATIONAL_SUBTEXT')

    selected=[]; used=set()
    def take(kind,n):
        pool=[]
        for work,d in top.items():
            if work in used: continue
            c=d[kind]
            if c: pool.append((c['rank'],work,c))
        pool.sort(key=lambda t:t[0])
        if len(pool)<n: raise SystemExit(f'HOLD_SAMPLE_POWER {kind}: {len(pool)}<{n}')
        for _,work,c in pool[:n]:
            used.add(work); selected.append((kind,work,c))
    take('NATURAL',16); take('INFO_CHALLENGE',4); take('RELATIONAL_SUBTEXT',4)

    freezes=[]; briefs=[]
    for idx,(cohort,work,c) in enumerate(selected,1):
        sid=f'P{idx:02d}'
        brief,mapping=make_brief(c['record'],sid,cohort)
        brief_sha=sha_bytes(canonical_bytes(brief))
        freezes.append({'scene_id':sid,'cohort':cohort,'source_work_id':work,'episode_no':c['record']['episode_no'],
                        'scene_no':c['record']['scene_no'],'archive_path':c['archive_path'],'archive_line_no':c['line_no'],
                        'record_sha256':c['record_sha256'],'rank_sha256':c['rank'],'brief_sha256':brief_sha,
                        'character_alias_mapping_sha256':sha_bytes(canonical_bytes(mapping))})
        briefs.append(brief)

    freeze={'schema':'P07I4HProspectiveCraftSampleFreezeR1','date':'2026-09-09','db59_sha256':DB59_SHA,
            'planner_runtime_pointer_schema':pointer.get('schema'),'planner_runtime_authority_id':pointer.get('current_authority_id'),
            'planner_runtime_manifest':pointer.get('manifest'),'canonical_works':len(canonical),'source_holds':sorted(holds),
            'selection_seed':SEED,'counts':counts,'selected':freezes,
            'status':'SAMPLE_FROZEN__24_OF_24__NO_GENERATION__NO_EVALUATION'}
    briefs_payload={'schema':'P07I4HProspectiveGenerationBriefsR1','date':'2026-09-09','briefs':briefs,
                    'source_prose_included':False,'status':'GENERATION_INPUT_FROZEN'}
    freeze_bytes=canonical_bytes(freeze); brief_bytes=canonical_bytes(briefs_payload)
    freeze['canonical_payload_sha256']=sha_bytes(freeze_bytes); briefs_payload['canonical_payload_sha256']=sha_bytes(brief_bytes)
    (OUT/'P07_I4H_PROSPECTIVE_SAMPLE_FREEZE_R1_20260909.json').write_text(json.dumps(freeze,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    (OUT/'P07_I4H_PROSPECTIVE_GENERATION_BRIEFS_R1_20260909.json').write_text(json.dumps(briefs_payload,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    print(json.dumps({'counts':counts,'selected':[(x['scene_id'],x['cohort'],x['source_work_id'],x['episode_no'],x['scene_no'],x['rank_sha256'][:12]) for x in freezes]},ensure_ascii=False,indent=2))
