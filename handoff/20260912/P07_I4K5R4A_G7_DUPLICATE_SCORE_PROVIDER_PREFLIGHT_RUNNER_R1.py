from pathlib import Path
import json, os, re, hashlib

root = Path('.')
base = root / 'handoff' / '20260912'
g6 = json.loads((base/'P07_I4K5R4A_G6_MASK_LEAKAGE_PASS_R1_20260912.json').read_text(encoding='utf-8'))
auth = (root/'handoff'/'CURRENT_DEVELOPER_HUB_AUTHORITY.md').read_text(encoding='utf-8')

score_like = []
for p in base.rglob('*'):
    if not p.is_file():
        continue
    n = p.name.upper()
    if 'P07_I4K5R4A' in n and re.search(r'J0[123]', n) and any(k in n for k in ('RESPONSE','SCORE','JUDGE_RESULT')):
        score_like.append(str(p))

mapping_open_hits = []
for p in base.rglob('*'):
    if not p.is_file() or 'P07_I4K5R4A' not in p.name.upper():
        continue
    try:
        t = p.read_text(encoding='utf-8', errors='ignore')
    except Exception:
        continue
    if re.search(r'"mapping_open"\s*:\s*(1|true)', t, re.I) or re.search(r'"opened"\s*:\s*true', t, re.I):
        mapping_open_hits.append(str(p))

checks = {
    'g6_pass': g6.get('status','').startswith('PASS__G6'),
    'masked_packet_internal_sha256': g6['masked_packet_artifact']['internal_packet_sha256'],
    'mapping_internal_sha256_recorded': bool(g6['mapping_secret_artifact'].get('internal_mapping_sha256')),
    'mapping_receipt_opened_false': g6['mapping_secret_artifact'].get('opened') is False,
    'prior_judge_score_files_count': len(score_like),
    'mapping_open_hits_count': len(mapping_open_hits),
    'current_physical_sync_r26': 'SYNC-R26' in auth,
    'current_judges_zero': ('Judges=0' in auth or 'judges=0' in auth or 'judge scores 0' in auth or 'independent judge scores=0' in auth),
    'provider_secret_present': bool(os.environ.get('OPENAI_API_KEY','').strip()),
}
scientific_pass = all([
    checks['g6_pass'], checks['mapping_internal_sha256_recorded'], checks['mapping_receipt_opened_false'],
    checks['prior_judge_score_files_count']==0, checks['mapping_open_hits_count']==0,
    checks['current_physical_sync_r26'], checks['current_judges_zero']
])
out = {
    'schema':'P07I4K5R4AG7DuplicateScoreProviderPreflightR1',
    'date':'2026-09-12',
    'experiment_id':'P07-I4K-5R4A-PSSB-EXPRESSION-HYGIENE-INDEPENDENT-FRESH-CONFIRMATION',
    'checks':checks,
    'score_like_paths':score_like,
    'mapping_open_paths':mapping_open_hits,
    'scientific_preflight_pass':scientific_pass,
    'provider_dispatch_ready': scientific_pass and checks['provider_secret_present'],
    'mapping_open':0,
    'judge_scores':0,
    'status': 'PASS__G7_DUPLICATE_SCORE_AND_PROVENANCE_PREFLIGHT' if scientific_pass else 'HOLD__G7_PREFLIGHT_INTEGRITY_FAILURE',
    'next_legal_action': 'REAL_PROVIDER_CONNECTIVITY_PROBE_THEN_J01_J02_J03' if scientific_pass and checks['provider_secret_present'] else ('PROVIDER_SECRET_REQUIRED_BEFORE_JUDGES' if scientific_pass else 'STOP_AND_REPAIR_G7'),
}
raw=json.dumps(out, ensure_ascii=False, indent=2).encode('utf-8')
out['receipt_sha256']=hashlib.sha256(raw).hexdigest()
Path('/tmp/i4k5r4a_g7_preflight_r1.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(out,ensure_ascii=False,indent=2))
if not scientific_pass:
    raise SystemExit(2)
