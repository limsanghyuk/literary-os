import json,re,hashlib
from pathlib import Path

SEQ=Path('handoff/20260911/P07_I4K5R4A_ATTEMPT2_SHARED_10_SEQUENCE_PLAN_R1_20260911.json')
TM=Path('handoff/20260911/P07_I4K5R4A_ATTEMPT2_TREATMENT_CANONICAL_MANIFEST_R4_20260911.json')
OUT=Path('/tmp/i4k5r4a_frozen_repeated_plan_purpose_compliance_r1.json')

def body(text):
    m=re.search(r'(?m)^S#\d+\.', text)
    if not m: raise RuntimeError('missing scene body')
    return text[m.start():]

def norm(s):
    return re.sub(r'[^0-9A-Za-z가-힣]+','',s).lower()

seq=json.loads(SEQ.read_text(encoding='utf-8'))
man=json.loads(TM.read_text(encoding='utf-8'))
parts=[]
for p in man['canonical_segments']:
    parts.append(body(Path(p).read_text(encoding='utf-8')))
treatment='\n'.join(parts)
nt=norm(treatment)

checks=[]
repeated_copy_count=0
any_copy_count=0
for s in seq['sequences']:
    purpose=s['purpose']
    np=norm(purpose)
    count=nt.count(np) if np else 0
    repeated=max(0,count-1)
    any_copy_count += count
    repeated_copy_count += repeated
    checks.append({
        'sequence':s['id'],
        'purpose':purpose,
        'normalized_chars':len(np),
        'exact_normalized_full_purpose_occurrences_in_treatment':count,
        'repeated_occurrences_beyond_first':repeated
    })

result={
  'schema':'P07I4K5R4AFrozenRepeatedPlanPurposeComplianceR1',
  'date':'2026-09-12',
  'experiment_id':'P07-I4K-5R4A-PSSB-EXPRESSION-HYGIENE-INDEPENDENT-FRESH-CONFIRMATION',
  'surface_state':'FROZEN__NO_MUTATION',
  'treatment_manifest':'handoff/20260911/P07_I4K5R4A_ATTEMPT2_TREATMENT_CANONICAL_MANIFEST_R4_20260911.json',
  'sequence_plan':'handoff/20260911/P07_I4K5R4A_ATTEMPT2_SHARED_10_SEQUENCE_PLAN_R1_20260911.json',
  'inherited_gate':'treatment_repeated_plan_purpose_copy == 0',
  'method':'For each sealed Sequence purpose, remove whitespace/punctuation and count exact full normalized purpose occurrences in the frozen Treatment screenplay body. Gate counts repeated occurrences beyond the first; no fuzzy threshold or post-output quality criterion is introduced.',
  'purpose_checks':checks,
  'full_purpose_copy_occurrences_total':any_copy_count,
  'repeated_plan_purpose_copy':repeated_copy_count,
  'gate_pass':repeated_copy_count==0,
  'quality_score_used':False,
  'surface_mutated':False,
  'mask':0,
  'judge_scores':0,
  'mapping_open':0
}
result['result_sha256']=hashlib.sha256(json.dumps(result,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
OUT.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(result,ensure_ascii=False,indent=2))
