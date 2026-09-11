from pathlib import Path
import hashlib, json, secrets, shutil

ROOT = Path('.')
BASE = ROOT / 'handoff' / '20260911' / 'i4k5r2_attempt2'
OUT = ROOT / '_i4k5r2_mask_build_r2'
MASKED = OUT / 'masked_packet'
MAPDIR = OUT / 'sealed_mapping'
if OUT.exists():
    shutil.rmtree(OUT)
MASKED.mkdir(parents=True)
MAPDIR.mkdir(parents=True)


def surface_body(text: str) -> str:
    start = text.find('S#')
    if start < 0:
        raise ValueError('missing first scene header')
    end = text.rfind('\n[END')
    if end < 0:
        end = len(text)
    return text[start:end].rstrip() + '\n'

control = []
treatment = []
source_sha = {'CONTROL': [], 'TREATMENT': []}
for i in range(1, 11):
    lo = (i-1)*5 + 1
    hi = i*5
    cpath = BASE / 'control' / f'P07_I4K5R2_A2_CONTROL_SQ{i:02d}_SC{lo:02d}_{hi:02d}.txt'
    tpath = BASE / 'treatment' / f'P07_I4K5R2_A2_TREATMENT_SQ{i:02d}_SC{lo:02d}_{hi:02d}.txt'
    cbytes = cpath.read_bytes(); tbytes = tpath.read_bytes()
    source_sha['CONTROL'].append(hashlib.sha256(cbytes).hexdigest())
    source_sha['TREATMENT'].append(hashlib.sha256(tbytes).hexdigest())
    control.append(surface_body(cbytes.decode('utf-8')))
    treatment.append(surface_body(tbytes.decode('utf-8')))

control_whole = '\n\n===== NEXT SEQUENCE =====\n\n'.join(x.rstrip() for x in control) + '\n'
treatment_whole = '\n\n===== NEXT SEQUENCE =====\n\n'.join(x.rstrip() for x in treatment) + '\n'

# Balanced neutral randomization: exactly six units each orientation, shuffled cryptographically.
flags = [True] * 6 + [False] * 6
secrets.SystemRandom().shuffle(flags)

mapping = {
    'schema': 'P07I4K5R2MaskedUnitMappingR2',
    'experiment_id': 'P07-I4K-5R2-FRESH-SURFACE-HYGIENE-REPAIR-REPLICATION',
    'evaluation_mode': 'MASKED_SAME_AGENT__DEVELOPMENT_PREFORMAL__INTERNAL_ONLY',
    'source_surface_commit': 'd94150c9d4a4911405624f79a37f447ae8e48c73',
    'units': {}
}
manifest = {
    'schema': 'P07I4K5R2MaskedPacketManifestR2',
    'experiment_id': mapping['experiment_id'],
    'masking_repairs': [
        'source arm metadata headers stripped',
        'END transport markers stripped',
        'source hashes omitted from masked packet',
        'A/B files padded with trailing spaces to equal byte size within each pair'
    ],
    'units': {},
    'mapping_not_in_packet': True
}

def write_pair(uid, a_text, b_text, a_arm, b_arm, purpose, a_src_sha=None, b_src_sha=None):
    a_raw = a_text.encode('utf-8')
    b_raw = b_text.encode('utf-8')
    target = max(len(a_raw), len(b_raw))
    a_pad = a_raw + b' ' * (target - len(a_raw))
    b_pad = b_raw + b' ' * (target - len(b_raw))
    ap = MASKED / f'{uid}_A.txt'; bp = MASKED / f'{uid}_B.txt'
    ap.write_bytes(a_pad); bp.write_bytes(b_pad)
    ah = hashlib.sha256(a_pad).hexdigest(); bh = hashlib.sha256(b_pad).hexdigest()
    mapping['units'][uid] = {
        'A': a_arm, 'B': b_arm, 'purpose': purpose,
        'A_masked_sha256': ah, 'B_masked_sha256': bh,
        'A_source_sha256': a_src_sha, 'B_source_sha256': b_src_sha
    }
    manifest['units'][uid] = {
        'A_file': ap.name, 'B_file': bp.name, 'purpose': purpose,
        'equalized_pair_bytes': target,
        'A_masked_sha256': ah, 'B_masked_sha256': bh
    }

for idx in range(10):
    uid = f'U{idx+1:02d}'
    purpose = f'corresponding full sequence SQ{idx+1:02d}'
    control_as_a = flags[idx]
    if control_as_a:
        write_pair(uid, control[idx], treatment[idx], 'CONTROL', 'TREATMENT', purpose,
                   source_sha['CONTROL'][idx], source_sha['TREATMENT'][idx])
    else:
        write_pair(uid, treatment[idx], control[idx], 'TREATMENT', 'CONTROL', purpose,
                   source_sha['TREATMENT'][idx], source_sha['CONTROL'][idx])

for idx, purpose in [(10, 'whole-episode architecture/continuity after full read'),
                     (11, 'whole-episode broadcast surface/craft after full read')]:
    uid = f'U{idx+1:02d}'
    control_as_a = flags[idx]
    if control_as_a:
        write_pair(uid, control_whole, treatment_whole, 'CONTROL', 'TREATMENT', purpose)
    else:
        write_pair(uid, treatment_whole, control_whole, 'TREATMENT', 'CONTROL', purpose)

manifest_path = MASKED / 'MASKED_PACKET_MANIFEST_R2.json'
manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
map_path = MAPDIR / 'SEALED_MAPPING_R2.json'
map_path.write_text(json.dumps(mapping, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
map_sha = hashlib.sha256(map_path.read_bytes()).hexdigest()
manifest_sha = hashlib.sha256(manifest_path.read_bytes()).hexdigest()
seal = {
    'schema': 'P07I4K5R2MaskSealR2',
    'experiment_id': mapping['experiment_id'],
    'supersedes_mask_r1': True,
    'mapping_sha256': map_sha,
    'masked_packet_manifest_sha256': manifest_sha,
    'unit_count': 12,
    'balanced_randomization': '6 Control-as-A / 6 Treatment-as-A; secrets.SystemRandom shuffle',
    'mapping_separate_from_masked_packet': True,
    'source_arm_literals_removed_from_transport_wrappers': True,
    'pair_byte_lengths_equalized': True,
    'scores_at_mask_seal': 0,
    'unblind_at_mask_seal': 0
}
(MASKED / 'MASK_SEAL_R2.json').write_text(json.dumps(seal, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
(MAPDIR / 'MASK_SEAL_R2.json').write_text(json.dumps(seal, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'unit_count': 12, 'mapping_sha256': map_sha, 'manifest_sha256': manifest_sha, 'mapping_content_printed': False, 'source_arm_headers_stripped': True, 'pair_sizes_equalized': True}))
