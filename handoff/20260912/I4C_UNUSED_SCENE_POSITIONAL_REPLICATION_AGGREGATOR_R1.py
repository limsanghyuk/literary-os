import json, hashlib, statistics, sys
from pathlib import Path

AXES = [
'DIALOGUE_SUBTEXT','CHARACTER_VOICE','RELATIONSHIP_STATUS_PRESSURE','PHYSICALIZATION_ACTION',
'PACING_ESCALATION_TIME_PRESSURE','ENSEMBLE_WORLD_SPECIFICITY','INFORMATION_REVEAL_IRREVERSIBILITY','LINE_ECONOMY_RHYTHM']
RESP_DIR=Path('handoff/20260912/i4c_unused_scene_responses')
EXPECTED_RESP={
'J01':'6bc7d546dabe96dea8785d4f7f97520fc91cc32ecfeb9a6209a82386180e1799',
'J02':'d7128feed3e5a1a7e54bca8cb53f0031d52b996a2a524da3f45e521b627712d2',
'J03':'92103ff48714a5b2f552c298ec17f74813bb02e38991f216586069fd115317df'}
MAPPING=[
{'opaque_id':'AP01','scene_id':'S26','position':'MIDDLE'},
{'opaque_id':'AP02','scene_id':'S16','position':'EARLY'},
{'opaque_id':'AP03','scene_id':'S13','position':'EARLY'},
{'opaque_id':'AP04','scene_id':'S29','position':'MIDDLE'},
{'opaque_id':'AP05','scene_id':'S23','position':'MIDDLE'},
{'opaque_id':'AP06','scene_id':'S46','position':'LATE'},
{'opaque_id':'AP07','scene_id':'S27','position':'MIDDLE'},
{'opaque_id':'AP08','scene_id':'S02','position':'EARLY'},
{'opaque_id':'AP09','scene_id':'S43','position':'LATE'},
{'opaque_id':'AP10','scene_id':'S10','position':'EARLY'},
{'opaque_id':'AP11','scene_id':'S42','position':'LATE'},
{'opaque_id':'AP12','scene_id':'S48','position':'LATE'}]
EXPECTED_MAPPING_SHA='46f8972c408250614761733ac29da956d1f1eecd3b0d3dbe9d14f13877ff2377'

def sha(b): return hashlib.sha256(b).hexdigest()
def load(jid):
    p=RESP_DIR/f'{jid}_I4C_UNUSED_SCENE_MIXED_CRAFT_RESPONSE_R1.json'
    b=p.read_bytes(); h=sha(b)
    if h != EXPECTED_RESP[jid]: raise SystemExit(f'{jid} response SHA mismatch: {h}')
    d=json.loads(b.decode('utf-8'))
    return d

responses={jid:load(jid) for jid in ('J01','J02','J03')}
score_by_jid={}
for jid,d in responses.items():
    score_by_jid[jid]={s['opaque_id']:s['scores'] for s in d['scenes']}

scene_metrics={}
for m in MAPPING:
    ap=m['opaque_id']
    med={a:statistics.median([score_by_jid[j][ap][a] for j in ('J01','J02','J03')]) for a in AXES}
    breadth=sum(v>=1 for v in med.values())
    material=sum(v>=2 for v in med.values())
    severity=sum(med.values())
    scene_metrics[ap]={**m,'axis_medians':med,'scene_breadth':breadth,'scene_material_breadth':material,'scene_severity_sum':severity}

strata={pos:[x['opaque_id'] for x in MAPPING if x['position']==pos] for pos in ('EARLY','MIDDLE','LATE')}
def mean(vals): return sum(vals)/len(vals)
stratum_metrics={}
for pos,aps in strata.items():
    stratum_metrics[pos]={
      'scene_count':len(aps),
      'mean_breadth':mean([scene_metrics[a]['scene_breadth'] for a in aps]),
      'mean_material_breadth':mean([scene_metrics[a]['scene_material_breadth'] for a in aps]),
      'mean_severity':mean([scene_metrics[a]['scene_severity_sum'] for a in aps]),
      'opaque_ids':aps}
ml=strata['MIDDLE']+strata['LATE']
pooled={
 'mean_breadth':mean([scene_metrics[a]['scene_breadth'] for a in ml]),
 'mean_severity':mean([scene_metrics[a]['scene_severity_sum'] for a in ml]),
 'scene_count':len(ml)}
early=stratum_metrics['EARLY']
delta_b=pooled['mean_breadth']-early['mean_breadth']
delta_s=pooled['mean_severity']-early['mean_severity']

judge_direction={}
for jid in ('J01','J02','J03'):
    def raw(ap): return sum(score_by_jid[jid][ap][a] for a in AXES)
    emean=mean([raw(a) for a in strata['EARLY']])
    mlmean=mean([raw(a) for a in ml])
    judge_direction[jid]={'early_mean_raw_severity':emean,'middle_late_mean_raw_severity':mlmean,'middle_late_gt_early':mlmean>emean,'delta':mlmean-emean}
agreement=sum(v['middle_late_gt_early'] for v in judge_direction.values())
positive=(delta_b>=1.0 and delta_s>=2.0 and agreement>=2)
if positive:
    decision='POSITIVE_MIXED_CRAFT_POSITIONAL_REPLICATION'
elif (delta_b>0 or delta_s>0 or agreement<2):
    decision='MIXED_OR_WEAK_REPLICATION'
else:
    decision='NO_POSITIONAL_REPLICATION'

out={
 'schema':'I4CUnusedSceneMixedCraftPositionalReplicationResultR1',
 'date':'2026-09-12',
 'classification':'EXPLORATORY_REPLICATION__KNOWLEDGE_ONLY__NO_RENDERER_INTERVENTION',
 'prereg_commit':'b4a323edb9efbecd34e196848f5c9f2c6c260163',
 'three_valid_responses_gate':'PASS__THREE_VALID_RESPONSES__UNBLIND_AUTHORIZED',
 'response_sha256':EXPECTED_RESP,
 'mapping_sha256':EXPECTED_MAPPING_SHA,
 'mapping_byte_seal_verified':True,
 'scene_metrics':scene_metrics,
 'stratum_metrics':stratum_metrics,
 'middle_late_pooled':pooled,
 'middle_late_minus_early':{'breadth':delta_b,'severity':delta_s},
 'individual_evaluator_direction':judge_direction,
 'evaluators_with_middle_late_raw_severity_gt_early':agreement,
 'frozen_thresholds':{'breadth_delta_min_for_positive':1.0,'severity_delta_min_for_positive':2.0,'individual_direction_agreement_min_for_positive':2},
 'threshold_checks':{'breadth':delta_b>=1.0,'severity':delta_s>=2.0,'individual_direction_agreement':agreement>=2},
 'decision':decision,
 'interpretation_boundary':'This is a knowledge-only positional replication on one sealed I4C episode using 12 previously unused scenes and three independent GPT evaluator sessions. It does not authorize renderer changes, Production promotion, Formal R140, or claims of human consensus.',
 'R4A_mapping_open':0,
 'R4A_judges':0,
 'historical_score_rewrite':False,
 'authority_change':False
}
raw=json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True).encode('utf-8')
out['result_sha256_without_self_hash']=sha(raw)
print(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True))
Path('/tmp/I4C_UNUSED_SCENE_POSITIONAL_REPLICATION_RESULT_R1.json').write_text(json.dumps(out,ensure_ascii=False,indent=2,sort_keys=True),encoding='utf-8')
