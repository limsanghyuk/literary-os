from pathlib import Path
import hashlib, json, re, secrets, shutil

BASE=Path('handoff/20260911/i4k5r3_attempt2')
SHARED=Path('handoff/20260911/P07_I4K5R3_ATTEMPT2_SHARED_SCENE_CONTEXT_EXPANSION_R1_20260911.json')
PSSB=Path('handoff/20260911/P07_I4K5R3_ATTEMPT2_TREATMENT_PSSB_BINDING_MAP_R1_20260911.json')
OUT=Path('_i4k5r3_mask_r1')
EXPECT={'CONTROL':'00aee8b3a5a04d296bdbb9cbe189cfa5b9283719f837814a2b3ec7f61e9d62db','TREATMENT':'9064f4f0b14377b8af379f89523a33aa213b47bc4c152e86a10b5797af296cec'}

def H(b): return hashlib.sha256(b).hexdigest()
def body(t):
    m=re.search(r'(?m)^S#\d+\.',t); e=t.rfind('[END ATTEMPT2')
    if not m or e<0: raise RuntimeError('bad source segment')
    return t[m.start():e].rstrip('\n')

def arm_segments(label, pssb=False):
    shared={int(k):v for k,v in json.loads(SHARED.read_text(encoding='utf-8'))['expansions'].items()}
    binds={int(k):v for k,v in json.loads(PSSB.read_text(encoding='utf-8'))['bindings'].items()} if pssb else {}
    src=BASE/('control_final' if label=='CONTROL' else 'treatment_final')
    files=sorted(src.glob('*.txt'))
    if len(files)!=10: raise RuntimeError('segment count')
    out=[]
    for p in files:
        t=p.read_text(encoding='utf-8')
        ms=list(re.finditer(r'(?m)^S#(\d+)\.[^\n]*\n',t))
        for m in reversed(ms):
            sid=int(m.group(1)); pos=m.end()
            if t[pos:pos+1]=='\n': pos+=1
            ins=shared[sid]+'\n\n'
            if pssb: ins+=binds[sid]+'\n\n'
            t=t[:pos]+ins+t[pos:]
        out.append(body(t))
    logical='\n\n'.join(out)
    if H(logical.encode())!=EXPECT[label]: raise RuntimeError(f'frozen hash mismatch {label}')
    return out

def equalize(a,b):
    ab=a.encode('utf-8'); bb=b.encode('utf-8'); n=max(len(ab),len(bb))
    if len(ab)<n: a=a+(' '*(n-len(ab)))
    if len(bb)<n: b=b+(' '*(n-len(bb)))
    assert len(a.encode())==len(b.encode())
    return a,b

if OUT.exists(): shutil.rmtree(OUT)
packet=OUT/'packet'; seal=OUT/'mapping_seal'; packet.mkdir(parents=True); seal.mkdir(parents=True)
C=arm_segments('CONTROL',False); T=arm_segments('TREATMENT',True)
mapping={}; packet_manifest={'schema':'P07I4K5R3MaskPacketR1','units':{},'arm_labels_exposed':False,'source_hashes_exposed':False,'pair_byte_lengths_equal':True}

for i in range(10):
    uid=f'U{i+1:02d}'; flip=secrets.randbits(1)
    A,B=(C[i],T[i]) if flip==0 else (T[i],C[i])
    a=f'[{uid}-A]\n'+A+'\n'; b=f'[{uid}-B]\n'+B+'\n'; a,b=equalize(a,b)
    (packet/f'{uid}_A.txt').write_text(a,encoding='utf-8'); (packet/f'{uid}_B.txt').write_text(b,encoding='utf-8')
    mapping[uid]={'A':'CONTROL' if flip==0 else 'TREATMENT','B':'TREATMENT' if flip==0 else 'CONTROL'}
    packet_manifest['units'][uid]={'focus':'corresponding full sequence surfaces','A_file':f'{uid}_A.txt','B_file':f'{uid}_B.txt','equal_bytes':len(a.encode())}

# Whole-episode pair, one random mapping shared by U11 and U12.
fc='\n\n'.join(C); ft='\n\n'.join(T); flip=secrets.randbits(1)
A,B=(fc,ft) if flip==0 else (ft,fc)
a='[WHOLE-EPISODE-A]\n'+A+'\n'; b='[WHOLE-EPISODE-B]\n'+B+'\n'; a,b=equalize(a,b)
(packet/'WHOLE_A.txt').write_text(a,encoding='utf-8'); (packet/'WHOLE_B.txt').write_text(b,encoding='utf-8')
for uid,focus in [('U11','whole-episode architecture/continuity after full read'),('U12','whole-episode broadcast surface/craft after full read')]:
    mapping[uid]={'A':'CONTROL' if flip==0 else 'TREATMENT','B':'TREATMENT' if flip==0 else 'CONTROL'}
    packet_manifest['units'][uid]={'focus':focus,'A_file':'WHOLE_A.txt','B_file':'WHOLE_B.txt','equal_bytes':len(a.encode())}

(packet/'MASKED_PACKET_MANIFEST.json').write_text(json.dumps(packet_manifest,ensure_ascii=False,indent=2),encoding='utf-8')
mapdoc={'schema':'P07I4K5R3MappingSealR1','nonce':secrets.token_hex(32),'mapping':mapping,'do_not_open_before_score_seal':True}
(seal/'MAPPING_SEAL.json').write_text(json.dumps(mapdoc,ensure_ascii=False,indent=2),encoding='utf-8')
# Audit packet itself for leakage.
joined='\n'.join(p.read_text(encoding='utf-8') for p in packet.glob('*') if p.is_file())
for bad in ['FINAL_CONTROL','FINAL_TREATMENT','__CONTROL__','__TREATMENT__','control_final','treatment_final','00aee8b3','9064f4f0']:
    if bad in joined: raise RuntimeError('mask leak '+bad)
print(json.dumps({'packet_files':len(list(packet.iterdir())),'mapping_units':len(mapping),'leak_check':'PASS'},sort_keys=True))