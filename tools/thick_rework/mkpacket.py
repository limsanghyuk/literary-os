# -*- coding: utf-8 -*-
"""회차별 작업 패킷 생성. 좌표(seq_id·member_scene_nos·evidence_refs)는 원본에서 그대로 복제한다."""
import json,glob,re,os,sys,collections
DB='/sessions/compassionate-eager-lovelace/mnt/claude/db/seqcard_ko'
B=DB+'/reinforcement_v1/thick_sequence/'
OUT='/sessions/compassionate-eager-lovelace/mnt/claude/rework'
RX=re.compile(r'(.+):L(\d+)-L(\d+)$')
def src(ref):
    m=RX.match(ref)
    if not m: return None
    return m.group(1),int(m.group(2)),int(m.group(3))
def slice_(path,a,b,cache={}):
    if path not in cache:
        cache[path]=open(os.path.join(DB,path),encoding='utf-8',errors='replace').read().split('\n')
    L=cache[path]
    return '\n'.join(L[a-1:b])
for w in sys.argv[1:]:
    files=sorted(glob.glob(B+w+'/*.jsonl'))
    os.makedirs(OUT+'/'+w+'/packets',exist_ok=True)
    os.makedirs(OUT+'/'+w+'/out',exist_ok=True)
    tot=0
    for f in files:
        R=[json.loads(l) for l in open(f,encoding='utf-8') if l.strip()]
        if not R: continue
        ep=R[0]['episode_no']; base=os.path.basename(f)
        pk={'work_id':w,'episode_no':ep,'source_file':None,'sequences':[]}
        for r in R:
            s=[e for e in (r.get('evidence_refs') or []) if e.get('kind')=='SOURCE']
            p,a,b=src(s[0]['ref']) if s else (None,None,None)
            pk['source_file']=p
            scenes=[]
            for sn in r.get('scene_notes',[]):
                ss=[e for e in (sn.get('evidence_refs') or []) if e.get('kind')=='SOURCE']
                sp,sa,sb=src(ss[0]['ref']) if ss else (p,a,b)
                scenes.append({'scene_no':sn['scene_no'],'n_props':len(sn.get('functional_propositions',[])),
                               'source':'L%d-L%d'%(sa,sb),'text':slice_(sp,sa,sb)})
            pk['sequences'].append({
              'seq_id':r['seq_id'],'seq_index':r['seq_index'],
              'member_scene_nos':r['member_scene_nos'],
              'source':'L%d-L%d'%(a,b),
              'characters':[c['character'] for c in r.get('cast',[])],
              'participation':{c['character']:c.get('participation') for c in r.get('cast',[])},
              'info_subjects':[i.get('subject') for i in r.get('info_shift',[])],
              'info_modes':[i.get('mode') for i in r.get('info_shift',[])],
              'plant':[{'kind':pp.get('kind'),'thread_id':pp.get('thread_id')} for pp in r.get('plant_payoff',[])],
              'scenes':scenes,
              '_fixed':{k:r[k] for k in ('schema','work_id','episode_no','source_hashes','by') if k in r},
              '_refs':{'top':r.get('evidence_refs'),
                       'cast':[c.get('evidence_refs') for c in r.get('cast',[])],
                       'info':[i.get('evidence_refs') for i in r.get('info_shift',[])],
                       'info_scene_nos':[i.get('scene_nos') for i in r.get('info_shift',[])],
                       'plant':[pp.get('evidence_refs') for pp in r.get('plant_payoff',[])],
                       'plant_scene_nos':[pp.get('scene_nos') for pp in r.get('plant_payoff',[])],
                       'plant_existing':[pp.get('existing_refs') for pp in r.get('plant_payoff',[])],
                       'scene':[sn.get('evidence_refs') for sn in r.get('scene_notes',[])]}})
            tot+=1
        json.dump(pk,open('%s/%s/packets/%s'%(OUT,w,base.replace('.jsonl','.packet.json')),'w',encoding='utf-8'),ensure_ascii=False,indent=1)
    print(w,'회차',len(files),'시퀀스',tot)
