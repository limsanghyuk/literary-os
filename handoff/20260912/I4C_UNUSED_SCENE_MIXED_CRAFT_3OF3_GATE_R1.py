import json, sys, hashlib
from pathlib import Path
from importlib.util import spec_from_file_location, module_from_spec

HERE=Path(__file__).resolve().parent
vp=HERE/'I4C_UNUSED_SCENE_MIXED_CRAFT_RESPONSE_VALIDATOR_R1.py'
spec=spec_from_file_location('validator',vp); m=module_from_spec(spec); spec.loader.exec_module(m)

EXPECTED=['J01','J02','J03']
if len(sys.argv)!=4:
    raise SystemExit('usage: gate.py J01.json J02.json J03.json')
results=[]
for path,eid in zip(sys.argv[1:],EXPECTED):
    results.append(m.validate_file(path,eid))
errors=[]
if not all(r['valid'] for r in results): errors.append('one_or_more_invalid_responses')
ids=[r['evaluator_id'] for r in results]
if ids!=EXPECTED: errors.append('evaluator_slot_order_or_identity_mismatch')
shas=[r['sha256'] for r in results]
if len(set(shas))!=3: errors.append('duplicate_response_bytes')
out={
 'schema':'I4CUnusedSceneMixedCraftThreeOfThreeGateR1',
 'response_contract_sha256':'1e592b3bc176691d4160f3021d73c8c0063286ed968a6d529d4c5a023e270a9b',
 'blind_packet_sha256':'c5c5dff8e1bf342dc955137e75c89937d6b8d3b9629830aa748d78f2d7935e3d',
 'responses':results,
 'valid_response_count':sum(1 for r in results if r['valid']),
 'mapping_opened':False,
 'mapping_open_authorized': not errors,
 'errors':errors,
 'status':'PASS__THREE_VALID_RESPONSES__UNBLIND_AUTHORIZED' if not errors else 'HOLD__THREE_VALID_RESPONSES_NOT_SEALED'
}
raw=json.dumps(out,ensure_ascii=False,sort_keys=True).encode(); out['receipt_sha256']=hashlib.sha256(raw).hexdigest()
print(json.dumps(out,ensure_ascii=False,indent=2))
raise SystemExit(0 if not errors else 2)
