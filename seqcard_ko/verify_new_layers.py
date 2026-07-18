# -*- coding: utf-8 -*-
"""신규 계층(Edge/CharacterArc/RelationshipArc/PayoffCandidate) 강한 검증기 — 범용 CLI.
사용법: python3 tools/verify_new_layers.py <work_id>   (예: 비밀의숲, 내이름은김삼순)
repo 루트에서 실행. 키셋락 + 참조무결성 + 반게이밍(텍스트 다양성/미치환변수) + edge_id/candidate_id
전역 고유성까지 전부 검사. ERRORS 0 이어야 PASS."""
import json, glob, re, sys, os
from collections import Counter

if len(sys.argv) < 2:
    print("사용법: python3 verify_new_layers.py <work_id>")
    sys.exit(1)

BASE = "seqcard_ko"  # 허브/로컬 repo 루트 기준 상대경로
work = sys.argv[1]

LOCAL_EDGE_KEYS = {'edge_id','work_id','edge_type','src_episode_no','src_scene_no',
    'tgt_episode_no','tgt_scene_no','gap_episodes','label','confidence','note','by'}
CHARARC_KEYS = {'work_id','character','episode_no','state_label','state_delta',
    'trigger_scene_no','by','evidence'}
RELARC_KEYS = {'work_id','char_a','char_b','episode_no','relation_state',
    'relation_delta','trigger_scene_no','evidence','by'}
PAYOFF_KEYS = {'candidate_id','work_id','episode_no','scene_no','edge_type_guess',
    'description','by'}
CORE_ENUM = {'ESTABLISH','ORACLE','INTRO','BOND','CONFLICT','REVERSAL','LOSS','PUNISH',
    'REVELATION','REUNION','RELIEF','ROMANCE','PERIL','RESCUE','DESIRE','HOOK'}
EDGE_TYPES = {'causal','callback','plant_payoff','subplot_counterpoint'}

errors = []

scene_range = {}
scene_files = sorted(glob.glob(f"{BASE}/authored/{work}_*.seqcard.jsonl"))
if not scene_files:
    print(f"ERROR: {BASE}/authored/{work}_*.seqcard.jsonl 파일이 없습니다. work_id 철자를 확인하세요.")
    sys.exit(1)
for f in scene_files:
    ep = int(re.search(rf"{re.escape(work)}_(\d+)\.seqcard", f).group(1))
    nos = [json.loads(l)['scene_no'] for l in open(f, encoding='utf-8') if l.strip()]
    scene_range[ep] = set(nos)

def jl(f):
    if not os.path.exists(f):
        return []
    return [json.loads(l) for l in open(f, encoding='utf-8') if l.strip()]

def keycheck(f, r, keyset, tag):
    miss = keyset - set(r); extra = set(r) - keyset
    if miss: errors.append(f"{tag} {f} MISSING {miss}")
    if extra: errors.append(f"{tag} {f} EXTRA {extra}")

# --- LocalEdge + cross-episode edges (cross file optional) ---
edge_files = sorted(glob.glob(f"{BASE}/authored_edges/{work}_*.local_edges.jsonl"))
cross_file = f"{BASE}/authored_edges/{work}_cross_episode_edges.jsonl"
if os.path.exists(cross_file):
    edge_files.append(cross_file)

all_edges = []
for f in edge_files:
    for r in jl(f):
        keycheck(f, r, LOCAL_EDGE_KEYS, "EDGE")
        if r.get('edge_type') not in EDGE_TYPES:
            errors.append(f"EDGE {f} bad edge_type {r.get('edge_type')}")
        if r.get('label') not in CORE_ENUM:
            errors.append(f"EDGE {f} bad label {r.get('label')}")
        if r.get('gap_episodes') != r.get('tgt_episode_no',0) - r.get('src_episode_no',0):
            errors.append(f"EDGE {f} gap mismatch {r.get('edge_id')}")
        se, ss = r.get('src_episode_no'), r.get('src_scene_no')
        te, ts = r.get('tgt_episode_no'), r.get('tgt_scene_no')
        if se not in scene_range or ss not in scene_range.get(se, set()):
            errors.append(f"EDGE {f} BAD src ref ep{se} scene{ss} ({r.get('edge_id')})")
        if te not in scene_range or ts not in scene_range.get(te, set()):
            errors.append(f"EDGE {f} BAD tgt ref ep{te} scene{ts} ({r.get('edge_id')})")
        all_edges.append(r)

# edge_id must be globally unique across the whole work
ids = [e['edge_id'] for e in all_edges]
dup_ids = [k for k,v in Counter(ids).items() if v>1]
if dup_ids: errors.append(f"EDGE duplicate edge_id: {dup_ids}")

# dedicated cross-episode file: every record must actually span episodes
if os.path.exists(cross_file):
    for e in jl(cross_file):
        if e['gap_episodes'] == 0:
            errors.append(f"CROSS-EDGE {e['edge_id']} has gap_episodes=0 (should span episodes)")

# --- CharacterArc ---
chararc_files = sorted(glob.glob(f"{BASE}/authored_chararc/{work}_*.chararc.jsonl"))
all_chararc = []
for f in chararc_files:
    for r in jl(f):
        keycheck(f, r, CHARARC_KEYS, "CHARARC")
        ep, sn = r.get('episode_no'), r.get('trigger_scene_no')
        if ep not in scene_range or sn not in scene_range.get(ep, set()):
            errors.append(f"CHARARC {f} BAD trigger ref ep{ep} scene{sn}")
        all_chararc.append(r)

# --- RelationshipArc ---
relarc_files = sorted(glob.glob(f"{BASE}/authored_relarc/{work}_*.relarc.jsonl"))
all_relarc = []
for f in relarc_files:
    for r in jl(f):
        keycheck(f, r, RELARC_KEYS, "RELARC")
        ep, sn = r.get('episode_no'), r.get('trigger_scene_no')
        if ep not in scene_range or sn not in scene_range.get(ep, set()):
            errors.append(f"RELARC {f} BAD trigger ref ep{ep} scene{sn}")
        all_relarc.append(r)

# --- PayoffCandidate ---
payoff_files = sorted(glob.glob(f"{BASE}/authored_edges/{work}_*.payoff_candidates.jsonl"))
all_payoff = []
for f in payoff_files:
    for r in jl(f):
        keycheck(f, r, PAYOFF_KEYS, "PAYOFF")
        if r.get('edge_type_guess') not in {'plant_payoff','callback','subplot_counterpoint','resolved_here'}:
            errors.append(f"PAYOFF {f} bad edge_type_guess {r.get('edge_type_guess')}")
        ep, sn = r.get('episode_no'), r.get('scene_no')
        if ep not in scene_range or sn not in scene_range.get(ep, set()):
            errors.append(f"PAYOFF {f} BAD scene ref ep{ep} scene{sn}")
        all_payoff.append(r)

cids = [p['candidate_id'] for p in all_payoff]
dup_cids = [k for k,v in Counter(cids).items() if v>1]
if dup_cids: errors.append(f"PAYOFF duplicate candidate_id: {dup_cids}")

# --- anti-gaming: text diversity + no unresolved template vars ---
def diversity(records, field, label, threshold=0.15):
    texts = [r.get(field,'') for r in records]
    c = Counter(texts)
    total = len(texts)
    if not total:
        return
    top = c.most_common(1)[0]
    ratio = top[1]/total
    if ratio > threshold:
        errors.append(f"ANTIGAME {label}.{field}: top repeated text {top[1]}/{total} ({ratio:.1%}) >= threshold — possible templating")

placeholder_pat = re.compile(r'\{[a-zA-Z_]+\}')
def placeholder_check(records, label):
    hits = 0
    for r in records:
        for v in r.values():
            if isinstance(v,str) and placeholder_pat.search(v):
                hits += 1
    if hits:
        errors.append(f"ANTIGAME {label}: {hits} unresolved template placeholders found")

print(f"=== {work} 신규계층 검증 ===")
print(f"LocalEdge+CrossEdge: {len(all_edges)} records ({len(edge_files)} files)")
print(f"CharacterArc: {len(all_chararc)} records")
print(f"RelationshipArc: {len(all_relarc)} records")
print(f"PayoffCandidate: {len(all_payoff)} records")
print()

diversity(all_edges, 'note', 'EDGE')
diversity(all_chararc, 'evidence', 'CHARARC')
diversity(all_relarc, 'evidence', 'RELARC')
diversity(all_payoff, 'description', 'PAYOFF')
placeholder_check(all_edges + all_chararc + all_relarc + all_payoff, 'ALL')

print(f"ERRORS: {len(errors)}")
for e in errors:
    print(" -", e)

if not errors:
    print()
    print(f"ERRORS 0 — [{work}] 신규계층 강한게이트 ALL PASS")
