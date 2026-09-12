import random, json, hashlib

SEED = 202609120305
EXPECTED_SHA = '46f8972c408250614761733ac29da956d1f1eecd3b0d3dbe9d14f13877ff2377'
selected_by_stratum = {
    'EARLY':['S02','S10','S13','S16'],
    'MIDDLE':['S23','S26','S27','S29'],
    'LATE':['S42','S43','S46','S48'],
}
ordered = selected_by_stratum['EARLY'] + selected_by_stratum['MIDDLE'] + selected_by_stratum['LATE']
shuffled = list(ordered)
random.Random(SEED).shuffle(shuffled)
scene_to_stratum = {s:k for k,v in selected_by_stratum.items() for s in v}
mapping = [
    {'opaque_id': f'AP{i:02d}', 'scene_id': scene, 'stratum': scene_to_stratum[scene]}
    for i,scene in enumerate(shuffled, 1)
]

def sha(b): return hashlib.sha256(b).hexdigest()

def variants():
    bases = {
      'list': mapping,
      'dict': {x['opaque_id']: x['scene_id'] for x in mapping},
      'mapping_only': {'mapping': mapping},
      'seed_mapping': {'packet_order_seed':SEED,'mapping':mapping},
      'schema_mapping': {'schema':'I4CUnusedSceneMixedCraftAnnotationMappingR1','date':'2026-09-12','packet_order_seed':SEED,'mapping':mapping},
      'schema_mapping_r2': {'schema':'I4CUnusedSceneMixedCraftAnnotationMappingR2','date':'2026-09-12','packet_order_seed':SEED,'mapping':mapping},
      'selected_mapping': {'packet_order_seed':SEED,'selected_by_stratum':selected_by_stratum,'mapping':mapping},
      'full_guess': {'schema':'I4CUnusedSceneMixedCraftAnnotationMappingR1','date':'2026-09-12','selection_seed':202609120304,'packet_order_seed':SEED,'selected_by_stratum':selected_by_stratum,'mapping':mapping},
    }
    out=[]
    for name,obj in bases.items():
      encodings=[
        ('compact', json.dumps(obj,ensure_ascii=False,separators=(',',':')).encode()),
        ('compact_sort', json.dumps(obj,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()),
        ('indent2', json.dumps(obj,ensure_ascii=False,indent=2).encode()),
        ('indent2_sort', json.dumps(obj,ensure_ascii=False,indent=2,sort_keys=True).encode()),
      ]
      for style,b in encodings:
        for nl in (False,True):
          bb=b+(b'\n' if nl else b'')
          out.append({'name':f'{name}:{style}:nl{int(nl)}','sha256':sha(bb),'match':sha(bb)==EXPECTED_SHA,'bytes':len(bb)})
    return out

candidates=variants()
out={
 'schema':'I4CUnusedSceneMappingRegenDiagnosticR1',
 'date':'2026-09-12',
 'selection_seed':202609120304,
 'packet_order_seed':SEED,
 'selected_by_stratum':selected_by_stratum,
 'semantic_mapping':mapping,
 'expected_sealed_mapping_sha256':EXPECTED_SHA,
 'candidate_serialization_match':[x for x in candidates if x['match']],
 'candidate_count':len(candidates),
 'candidate_serializations':candidates,
 'mapping_open_scope':'I4C_REPLICATION_ONLY',
 'R4A_mapping_open':0,
}
print(json.dumps(out,ensure_ascii=False,indent=2))
