import json, sys, hashlib
from pathlib import Path

REQ_IDS=[f'AP{i:02d}' for i in range(1,13)]
AXES=[
'DIALOGUE_SUBTEXT','CHARACTER_VOICE','RELATIONSHIP_STATUS_PRESSURE','PHYSICALIZATION_ACTION',
'PACING_ESCALATION_TIME_PRESSURE','ENSEMBLE_WORLD_SPECIFICITY','INFORMATION_REVEAL_IRREVERSIBILITY','LINE_ECONOMY_RHYTHM']

def sha256_path(p):
    h=hashlib.sha256()
    with open(p,'rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):
            h.update(b)
    return h.hexdigest()

def validate_obj(obj, expected_evaluator_id=None):
    errors=[]
    if not isinstance(obj,dict): return ['response_root_not_object']
    eid=obj.get('evaluator_id')
    if not isinstance(eid,str) or not eid.strip(): errors.append('missing_evaluator_id')
    if expected_evaluator_id and eid != expected_evaluator_id: errors.append('evaluator_id_mismatch')
    if not isinstance(obj.get('provider_or_human'),str) or not obj.get('provider_or_human','').strip(): errors.append('missing_provider_or_human')
    if not isinstance(obj.get('model_config_or_human_metadata'),str) or not obj.get('model_config_or_human_metadata','').strip(): errors.append('missing_model_config_or_human_metadata')
    if obj.get('independence_attestation') is not True: errors.append('independence_attestation_not_true')
    scenes=obj.get('scenes')
    if not isinstance(scenes,list):
        errors.append('scenes_not_list'); return errors
    ids=[x.get('opaque_id') for x in scenes if isinstance(x,dict)]
    if len(scenes)!=12: errors.append('scene_count_not_12')
    if sorted(ids)!=REQ_IDS: errors.append('opaque_id_set_mismatch_or_duplicate')
    for i,s in enumerate(scenes):
        if not isinstance(s,dict): errors.append(f'scene_{i}_not_object'); continue
        oid=s.get('opaque_id','?')
        scores=s.get('scores')
        if not isinstance(scores,dict): errors.append(f'{oid}_scores_not_object'); continue
        if set(scores)!=set(AXES): errors.append(f'{oid}_axis_set_mismatch')
        for a in AXES:
            v=scores.get(a)
            if type(v) is not int or v not in (0,1,2): errors.append(f'{oid}_{a}_invalid')
        note=s.get('evidence_note')
        if not isinstance(note,str) or not note.strip(): errors.append(f'{oid}_missing_evidence_note')
    return errors

def validate_file(path, expected_evaluator_id=None):
    p=Path(path)
    obj=json.loads(p.read_text(encoding='utf-8'))
    errors=validate_obj(obj,expected_evaluator_id)
    return {'path':str(p),'sha256':sha256_path(p),'evaluator_id':obj.get('evaluator_id'),'valid':not errors,'errors':errors}

if __name__=='__main__':
    if len(sys.argv)<2:
        raise SystemExit('usage: validator.py RESPONSE.json [EXPECTED_EVALUATOR_ID]')
    out=validate_file(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None)
    print(json.dumps(out,ensure_ascii=False,indent=2))
    raise SystemExit(0 if out['valid'] else 2)
