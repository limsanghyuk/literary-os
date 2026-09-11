from __future__ import annotations
import hashlib, json, os, re, secrets, subprocess
from pathlib import Path

FREEZE = '494190b45db7889de94835de59692b110cbe6a8b'
OUT = Path('/tmp/i4k5r4a_g6_mask_r1')
PACKET = OUT / 'masked_packet'
SECRET = OUT / 'mapping_secret'
PACKET.mkdir(parents=True, exist_ok=True)
SECRET.mkdir(parents=True, exist_ok=True)

CONTROL = [
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
TREATMENT = [
'handoff/20260911/i4k5r4a_attempt2/treatment_superseding_r2/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ01_S01_05_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_superseding_r4/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ02_S06_10_R4_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_superseding_r3/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ03_S11_15_R3_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_superseding_r2/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ04_S16_20_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_superseding_r2/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ05_S21_25_R2_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ06_S26_30_R1_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_late_superseding_r4/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ07_S31_35_R4_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_late_superseding_r4/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ08_S36_40_R4_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_late_superseding_r4/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ09_S41_45_R4_20260911.txt',
'handoff/20260911/i4k5r4a_attempt2/treatment_late_superseding_r3/P07_I4K5R4A_ATTEMPT2_TREATMENT_SQ10_S46_50_R3_20260911.txt']

def git_bytes(path:str)->bytes:
    return subprocess.check_output(['git','show',f'{FREEZE}:{path}'])

def strip_to_scene(raw:bytes)->bytes:
    text=raw.decode('utf-8')
    m=re.search(r'(?m)^S#\d+\b', text)
    if not m:
        raise RuntimeError('no scene marker')
    body=text[m.start():].strip().encode('utf-8')
    return body

def sha(b:bytes)->str: return hashlib.sha256(b).hexdigest()

c=[strip_to_scene(git_bytes(p)) for p in CONTROL]
t=[strip_to_scene(git_bytes(p)) for p in TREATMENT]
whole_c=b'\n\n'.join(c)
whole_t=b'\n\n'.join(t)

units=[]
for i in range(10): units.append((f'U{i+1:02d}',c[i],t[i],'corresponding_full_sequence_surface'))
units.append(('U11',whole_c,whole_t,'whole_episode_architecture_continuity_after_full_read'))
units.append(('U12',whole_c,whole_t,'whole_episode_broadcast_surface_craft_after_full_read'))

mapping={'schema':'P07I4K5R4AG6MappingSecretR1','freeze_commit':FREEZE,'units':[]}
manifest={'schema':'P07I4K5R4AG6MaskedPacketManifestR1','experiment_id':'P07-I4K-5R4A-PSSB-EXPRESSION-HYGIENE-INDEPENDENT-FRESH-CONFIRMATION','units':[],'mapping_in_packet':False,'source_paths_in_packet':False,'source_hashes_in_packet':False,'R3_result_in_packet':False,'other_judge_scores_in_packet':False}
for uid,cb,tb,focus in units:
    treatment_is_A=bool(secrets.randbits(1))
    A,B=(tb,cb) if treatment_is_A else (cb,tb)
    # byte-length equalization with semantically inert trailing ASCII spaces
    maxlen=max(len(A),len(B))
    Aeq=A+b' '*(maxlen-len(A)); Beq=B+b' '*(maxlen-len(B))
    (PACKET/f'{uid}_A.txt').write_bytes(Aeq)
    (PACKET/f'{uid}_B.txt').write_bytes(Beq)
    manifest['units'].append({'unit_id':uid,'focus':focus,'A_file':f'{uid}_A.txt','B_file':f'{uid}_B.txt','A_bytes':len(Aeq),'B_bytes':len(Beq),'A_sha256':sha(Aeq),'B_sha256':sha(Beq)})
    mapping['units'].append({'unit_id':uid,'A':'TREATMENT' if treatment_is_A else 'CONTROL','B':'CONTROL' if treatment_is_A else 'TREATMENT','control_source_sha256':sha(cb),'treatment_source_sha256':sha(tb)})

(PACKET/'MASKED_PACKET_MANIFEST.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
(SECRET/'MAPPING_SECRET.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2),encoding='utf-8')

forbidden=[b'CONTROL',b'TREATMENT',b'PSSB',b'i4k5r4a_attempt2',b'control_superseding',b'treatment_superseding',b'treatment_late_superseding']
leaks=[]
for p in sorted(PACKET.glob('U*_*.txt')):
    data=p.read_bytes()
    for tok in forbidden:
        if tok.lower() in data.lower(): leaks.append({'file':p.name,'token':tok.decode()})

equal=all(u['A_bytes']==u['B_bytes'] for u in manifest['units'])
files=sorted(p.name for p in PACKET.iterdir())
expected=['MASKED_PACKET_MANIFEST.json']+[f'U{i:02d}_{arm}.txt' for i in range(1,13) for arm in ('A','B')]
packet_digest=hashlib.sha256(b''.join((PACKET/f).read_bytes() for f in sorted(files))).hexdigest()
mapping_digest=sha((SECRET/'MAPPING_SECRET.json').read_bytes())
audit={'schema':'P07I4K5R4AG6MaskLeakageAuditR1','freeze_commit':FREEZE,'unit_count':12,'A_B_bytes_equalized_all_units':equal,'forbidden_token_hits':leaks,'packet_file_set_exact':files==sorted(expected),'mapping_file_present_in_packet':(PACKET/'MAPPING_SECRET.json').exists(),'packet_sha256':packet_digest,'mapping_secret_sha256':mapping_digest,'mask_leakage_pass': equal and not leaks and files==sorted(expected) and not (PACKET/'MAPPING_SECRET.json').exists(),'mapping_open':False,'judge_scores':0}
(PACKET/'G6_MASK_LEAKAGE_AUDIT.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2),encoding='utf-8')
if not audit['mask_leakage_pass']:
    raise SystemExit(json.dumps(audit,ensure_ascii=False))
print(json.dumps(audit,ensure_ascii=False))
