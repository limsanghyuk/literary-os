from pathlib import Path
import hashlib, json, secrets, shutil

ROOT = Path('.')
BASE = ROOT / 'handoff' / '20260911' / 'i4k5r2_attempt2'
OUT = ROOT / '_i4k5r2_mask_build'
MASKED = OUT / 'masked_packet'
MAPDIR = OUT / 'sealed_mapping'
if OUT.exists():
    shutil.rmtree(OUT)
MASKED.mkdir(parents=True)
MAPDIR.mkdir(parents=True)

control = []
treatment = []
for i in range(1, 11):
    lo = (i-1)*5 + 1
    hi = i*5
    c = BASE / 'control' / f'P07_I4K5R2_A2_CONTROL_SQ{i:02d}_SC{lo:02d}_{hi:02d}.txt'
    t = BASE / 'treatment' / f'P07_I4K5R2_A2_TREATMENT_SQ{i:02d}_SC{lo:02d}_{hi:02d}.txt'
    control.append(c.read_text(encoding='utf-8'))
    treatment.append(t.read_text(encoding='utf-8'))

control_whole = '\n\n===== NEXT SEQUENCE =====\n\n'.join(control)
treatment_whole = '\n\n===== NEXT SEQUENCE =====\n\n'.join(treatment)

# Balanced neutral randomization: six units have Control as A, six have Treatment as A.
flags = [True] * 6 + [False] * 6
secrets.SystemRandom().shuffle(flags)

mapping = {
    'schema': 'P07I4K5R2MaskedUnitMappingR1',
    'experiment_id': 'P07-I4K-5R2-FRESH-SURFACE-HYGIENE-REPAIR-REPLICATION',
    'evaluation_mode': 'MASKED_SAME_AGENT__DEVELOPMENT_PREFORMAL__INTERNAL_ONLY',
    'source_surface_commit': 'd94150c9d4a4911405624f79a37f447ae8e48c73',
    'units': {}
}
manifest = {
    'schema': 'P07I4K5R2MaskedPacketManifestR1',
    'experiment_id': mapping['experiment_id'],
    'units': {},
    'mapping_not_in_packet': True
}

def write_unit(uid, a_text, b_text, a_arm, b_arm, purpose):
    ap = MASKED / f'{uid}_A.txt'
    bp = MASKED / f'{uid}_B.txt'
    ap.write_text(a_text, encoding='utf-8')
    bp.write_text(b_text, encoding='utf-8')
    ah = hashlib.sha256(ap.read_bytes()).hexdigest()
    bh = hashlib.sha256(bp.read_bytes()).hexdigest()
    mapping['units'][uid] = {'A': a_arm, 'B': b_arm, 'purpose': purpose, 'A_sha256': ah, 'B_sha256': bh}
    manifest['units'][uid] = {'A_file': ap.name, 'B_file': bp.name, 'purpose': purpose, 'A_sha256': ah, 'B_sha256': bh}

for idx in range(10):
    uid = f'U{idx+1:02d}'
    control_as_a = flags[idx]
    if control_as_a:
        write_unit(uid, control[idx], treatment[idx], 'CONTROL', 'TREATMENT', f'corresponding full sequence SQ{idx+1:02d}')
    else:
        write_unit(uid, treatment[idx], control[idx], 'TREATMENT', 'CONTROL', f'corresponding full sequence SQ{idx+1:02d}')

for idx, purpose in [(10, 'whole-episode architecture/continuity after full read'), (11, 'whole-episode broadcast surface/craft after full read')]:
    uid = f'U{idx+1:02d}'
    control_as_a = flags[idx]
    if control_as_a:
        write_unit(uid, control_whole, treatment_whole, 'CONTROL', 'TREATMENT', purpose)
    else:
        write_unit(uid, treatment_whole, control_whole, 'TREATMENT', 'CONTROL', purpose)

manifest_path = MASKED / 'MASKED_PACKET_MANIFEST_R1.json'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
map_path = MAPDIR / 'SEALED_MAPPING_R1.json'
map_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
map_sha = hashlib.sha256(map_path.read_bytes()).hexdigest()
manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
seal = {
    'schema': 'P07I4K5R2MaskSealR1',
    'experiment_id': mapping['experiment_id'],
    'mapping_sha256': map_sha,
    'masked_packet_manifest_sha256': manifest_sha,
    'unit_count': 12,
    'balanced_randomization': '6 Control-as-A / 6 Treatment-as-A, assignment shuffled with secrets.SystemRandom',
    'mapping_separate_from_masked_packet': True,
    'scores_at_mask_seal': 0,
    'unblind_at_mask_seal': 0
}
(MASKED / 'MASK_SEAL_R1.json').write_text(json.dumps(seal, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(MAPDIR / 'MASK_SEAL_R1.json').write_text(json.dumps(seal, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'unit_count': 12, 'mapping_sha256': map_sha, 'manifest_sha256': manifest_sha, 'mapping_content_printed': False}))
