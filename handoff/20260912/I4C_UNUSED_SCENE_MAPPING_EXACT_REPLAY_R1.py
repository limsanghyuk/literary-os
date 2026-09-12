import random, json, hashlib, sys
EXPECTED='46f8972c408250614761733ac29da956d1f1eecd3b0d3dbe9d14f13877ff2377'
selected={
 'EARLY':['S02','S10','S13','S16'],
 'MIDDLE':['S23','S26','S27','S29'],
 'LATE':['S42','S43','S46','S48'],
}
flat=[(sid,pos) for pos in ('EARLY','MIDDLE','LATE') for sid in selected[pos]]
rng2=random.Random(202609120305); rng2.shuffle(flat)
mapping=[{'opaque_id':f'AP{i:02d}','scene_id':sid,'position':pos} for i,(sid,pos) in enumerate(flat,1)]
map_obj={
 'schema':'I4CUnusedSceneMixedCraftAnnotationReplicationMappingR1',
 'seed_select':202609120304,
 'seed_packet_order':202609120305,
 'selected_by_stratum':selected,
 'mapping':mapping,
}
map_bytes=json.dumps(map_obj,ensure_ascii=False,sort_keys=True,indent=2).encode('utf-8')
actual=hashlib.sha256(map_bytes).hexdigest()
out={
 'schema':'I4CUnusedSceneMappingExactReplayReceiptR1',
 'expected_sha256':EXPECTED,
 'actual_sha256':actual,
 'bytes':len(map_bytes),
 'byte_seal_match':actual==EXPECTED,
 'mapping':mapping,
 'R4A_mapping_open':0,
 'status':'PASS__EXACT_MAPPING_BYTE_SEAL_REPRODUCED' if actual==EXPECTED else 'HOLD__EXACT_MAPPING_BYTE_SEAL_MISMATCH',
}
print(json.dumps(out,ensure_ascii=False,indent=2))
open('/tmp/I4C_UNUSED_SCENE_MAPPING_EXACT_REPLAY_RECEIPT_R1.json','w',encoding='utf-8').write(json.dumps(out,ensure_ascii=False,indent=2))
open('/tmp/I4C_UNUSED_SCENE_MIXED_CRAFT_MAPPING_SECRET_REPLAY_R1.json','wb').write(map_bytes)
if actual!=EXPECTED: sys.exit(2)
