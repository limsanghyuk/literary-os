# -*- coding: utf-8 -*-
"""신규 계층 강한 검증기 v2 (병합설계: 이중 슬롯 + 이중 floor) — 범용 CLI.

v1(verify_new_layers.py)의 모든 검사를 상위집합으로 포함하고, 아래를 추가한다.

  [이중 슬롯]  CharacterArc.state_label / RelationshipArc.relation_state 를
               '쿼리용 닫힌 enum'으로 강제하고, 산문 의미는 신규 필드
               state_headline / relation_headline 로 분리한다.
  [깊이 floor] evidence/note/description 최소 길이(=40자)를 강제한다(Claude 강점).
  [커버리지 floor] 회차당 최소 arc 행수·인물수, 장거리(gap>=5) cross-edge 쿼터,
               plant->payoff 페어링 최소율을 강제한다(GPT 강점).

기존 정본(v1 스키마)은 건드리지 않는다. v2로 저작한 신규 작품에만 이 게이트를 적용.
사용법(repo 루트에서): python3 seqcard_ko/verify_new_layers_v2.py <work_id>
"""
import json, glob, re, sys, os, math
from collections import Counter, defaultdict

if len(sys.argv) < 2:
    print("사용법: python3 verify_new_layers_v2.py <work_id>")
    sys.exit(1)

BASE = "seqcard_ko"
work = sys.argv[1]

# ── 키셋 (v1 + 이중 슬롯 신규 필드) ─────────────────────────────
LOCAL_EDGE_KEYS = {'edge_id','work_id','edge_type','src_episode_no','src_scene_no',
    'tgt_episode_no','tgt_scene_no','gap_episodes','label','confidence','note','by'}
CHARARC_KEYS = {'work_id','character','episode_no','state_label','state_headline',
    'state_delta','trigger_scene_no','by','evidence'}          # +state_headline
RELARC_KEYS = {'work_id','char_a','char_b','episode_no','relation_state','relation_headline',
    'relation_delta','trigger_scene_no','evidence','by'}       # +relation_headline
PAYOFF_KEYS = {'candidate_id','work_id','episode_no','scene_no','edge_type_guess',
    'description','by'}

# 씬 기능(scene function) 어휘 — LocalEdge/CrossEdge label 전용 (v1과 동일)
CORE_ENUM = {'ESTABLISH','ORACLE','INTRO','BOND','CONFLICT','REVERSAL','LOSS','PUNISH',
    'REVELATION','REUNION','RELIEF','ROMANCE','PERIL','RESCUE','DESIRE','HOOK'}

# 인물 상태 궤적 어휘 — CharacterArc.state_label 전용 (코퍼스 실측 기반 신규 정의)
ARC_STATE_ENUM = {'ESTABLISH','DESIRE','BOND','GROWTH','RESOLVE','CONFLICT','REVERSAL',
    'REVELATION','LOSS','FALL','PUNISH','RESCUE','RELIEF','SACRIFICE'}

# 관계 상태 어휘 — RelationshipArc.relation_state 전용 (코퍼스 실측 기반 신규 정의)
REL_STATE_ENUM = {'BOND','ALLIANCE','ROMANCE','DEPENDENCE','RECONCILE','SUSPICION',
    'CONFLICT','RIVALRY','BETRAYAL','DISTANCE','DOMINANCE','DESIRE','LOSS','REUNION'}

EDGE_TYPES = {'causal','callback','plant_payoff','subplot_counterpoint'}
MIN_LEN = 40  # 깊이 floor: 근거 자유서술 최소 길이

errors = []

# ── 씬 인덱스 ──────────────────────────────────────────────────
scene_range = {}
scene_files = sorted(glob.glob(f"{BASE}/authored/{work}_*.seqcard.jsonl"))
if not scene_files:
    print(f"ERROR: {BASE}/authored/{work}_*.seqcard.jsonl 파일이 없습니다. work_id 철자를 확인하세요.")
    sys.exit(1)
for f in scene_files:
    ep = int(re.search(rf"{re.escape(work)}_(\d+)\.seqcard", f).group(1))
    nos = [json.loads(l)['scene_no'] for l in open(f, encoding='utf-8') if l.strip()]
    scene_range[ep] = set(nos)

EPISODES = len(scene_range)
SCENES = sum(len(v) for v in scene_range.values())

def jl(f):
    if not os.path.exists(f):
        return []
    return [json.loads(l) for l in open(f, encoding='utf-8') if l.strip()]

def keycheck(f, r, keyset, tag):
    miss = keyset - set(r); extra = set(r) - keyset
    if miss: errors.append(f"{tag} {f} MISSING {miss}")
    if extra: errors.append(f"{tag} {f} EXTRA {extra}")

def minlen(records, field, label):
    for r in records:
        v = r.get(field, '')
        if not isinstance(v, str) or len(v.strip()) < MIN_LEN:
            errors.append(f"DEPTHFLOOR {label}.{field} < {MIN_LEN}자: {str(r.get(field))[:24]!r} ({r.get('work_id')})")

# ── LocalEdge + CrossEdge ─────────────────────────────────────
edge_files = sorted(glob.glob(f"{BASE}/authored_edges/{work}_*.local_edges.jsonl"))
cross_file = f"{BASE}/authored_edges/{work}_cross_episode_edges.jsonl"
if os.path.exists(cross_file):
    edge_files.append(cross_file)

all_edges = []; edges_per_ep = defaultdict(int)
for f in edge_files:
    for r in jl(f):
        keycheck(f, r, LOCAL_EDGE_KEYS, "EDGE")
        if r.get('edge_type') not in EDGE_TYPES:
            errors.append(f"EDGE {f} bad edge_type {r.get('edge_type')}")
        if r.get('label') not in CORE_ENUM:
            errors.append(f"EDGE {f} bad label {r.get('label')} (CORE_ENUM 전용)")
        if r.get('gap_episodes') != r.get('tgt_episode_no',0) - r.get('src_episode_no',0):
            errors.append(f"EDGE {f} gap mismatch {r.get('edge_id')}")
        se, ss = r.get('src_episode_no'), r.get('src_scene_no')
        te, ts = r.get('tgt_episode_no'), r.get('tgt_scene_no')
        if se not in scene_range or ss not in scene_range.get(se, set()):
            errors.append(f"EDGE {f} BAD src ref ep{se} scene{ss} ({r.get('edge_id')})")
        if te not in scene_range or ts not in scene_range.get(te, set()):
            errors.append(f"EDGE {f} BAD tgt ref ep{te} scene{ts} ({r.get('edge_id')})")
        if f != cross_file:
            edges_per_ep[se] += 1
        all_edges.append(r)

ids = [e['edge_id'] for e in all_edges]
dup_ids = [k for k,v in Counter(ids).items() if v>1]
if dup_ids: errors.append(f"EDGE duplicate edge_id: {dup_ids}")

cross_edges = jl(cross_file) if os.path.exists(cross_file) else []
for e in cross_edges:
    if e['gap_episodes'] == 0:
        errors.append(f"CROSS-EDGE {e['edge_id']} has gap_episodes=0 (should span episodes)")

# ── CharacterArc (이중 슬롯) ──────────────────────────────────
chararc_files = sorted(glob.glob(f"{BASE}/authored_chararc/{work}_*.chararc.jsonl"))
all_chararc = []; ch_per_ep = defaultdict(list)
for f in chararc_files:
    for r in jl(f):
        keycheck(f, r, CHARARC_KEYS, "CHARARC")
        if r.get('state_label') not in ARC_STATE_ENUM:
            errors.append(f"CHARARC {f} bad state_label {r.get('state_label')!r} (ARC_STATE_ENUM 전용)")
        hl = r.get('state_headline','')
        if not isinstance(hl,str) or len(hl.strip()) < 8:
            errors.append(f"CHARARC {f} state_headline 너무 짧음/누락: {hl!r}")
        if isinstance(hl,str) and hl.strip() == str(r.get('state_label')).strip():
            errors.append(f"CHARARC {f} state_headline == state_label (산문 슬롯이 enum 복사): {hl!r}")
        ep, sn = r.get('episode_no'), r.get('trigger_scene_no')
        if ep not in scene_range or sn not in scene_range.get(ep, set()):
            errors.append(f"CHARARC {f} BAD trigger ref ep{ep} scene{sn}")
        all_chararc.append(r); ch_per_ep[ep].append(r)

# ── RelationshipArc (이중 슬롯) ───────────────────────────────
relarc_files = sorted(glob.glob(f"{BASE}/authored_relarc/{work}_*.relarc.jsonl"))
all_relarc = []; rel_per_ep = defaultdict(list)
for f in relarc_files:
    for r in jl(f):
        keycheck(f, r, RELARC_KEYS, "RELARC")
        if r.get('relation_state') not in REL_STATE_ENUM:
            errors.append(f"RELARC {f} bad relation_state {r.get('relation_state')!r} (REL_STATE_ENUM 전용)")
        hl = r.get('relation_headline','')
        if not isinstance(hl,str) or len(hl.strip()) < 8:
            errors.append(f"RELARC {f} relation_headline 너무 짧음/누락: {hl!r}")
        if isinstance(hl,str) and hl.strip() == str(r.get('relation_state')).strip():
            errors.append(f"RELARC {f} relation_headline == relation_state: {hl!r}")
        ep, sn = r.get('episode_no'), r.get('trigger_scene_no')
        if ep not in scene_range or sn not in scene_range.get(ep, set()):
            errors.append(f"RELARC {f} BAD trigger ref ep{ep} scene{sn}")
        all_relarc.append(r); rel_per_ep[ep].append(r)

# ── PayoffCandidate ───────────────────────────────────────────
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

# ── 반게이밍: 텍스트 다양성 + 미치환 변수 (v1) ────────────────
def diversity(records, field, label, threshold=0.15):
    texts = [r.get(field,'') for r in records]
    c = Counter(texts); total = len(texts)
    if not total: return
    top = c.most_common(1)[0]; ratio = top[1]/total
    if ratio > threshold:
        errors.append(f"ANTIGAME {label}.{field}: top repeated {top[1]}/{total} ({ratio:.1%}) >= {threshold:.0%}")

placeholder_pat = re.compile(r'\{[a-zA-Z_]+\}')
def placeholder_check(records, label):
    hits = sum(1 for r in records for v in r.values()
               if isinstance(v,str) and placeholder_pat.search(v))
    if hits:
        errors.append(f"ANTIGAME {label}: {hits} unresolved template placeholders")

# ── 커버리지 floor (GPT 강점 흡수) ────────────────────────────
def coverage_floors():
    ch_total_floor = max(4*EPISODES, math.ceil(0.12*SCENES))
    if len(all_chararc) < ch_total_floor:
        errors.append(f"COVFLOOR CharArc 총 {len(all_chararc)} < floor {ch_total_floor} (=max(4*ep, ceil(0.12*S)))")
    for ep in scene_range:
        rows = ch_per_ep.get(ep, [])
        if len(rows) < 4:
            errors.append(f"COVFLOOR CharArc ep{ep} 행 {len(rows)} < 4")
        elif len({r.get('character') for r in rows}) < 3:
            errors.append(f"COVFLOOR CharArc ep{ep} 인물수 {len({r.get('character') for r in rows})} < 3")
    rel_total_floor = max(3*EPISODES, math.ceil(0.09*SCENES))
    if len(all_relarc) < rel_total_floor:
        errors.append(f"COVFLOOR RelArc 총 {len(all_relarc)} < floor {rel_total_floor} (=max(3*ep, ceil(0.09*S)))")
    for ep in scene_range:
        if len(rel_per_ep.get(ep, [])) < 3:
            errors.append(f"COVFLOOR RelArc ep{ep} 행 {len(rel_per_ep.get(ep, []))} < 3")
    for ep in scene_range:
        if edges_per_ep.get(ep, 0) < 8:
            errors.append(f"COVFLOOR LocalEdge ep{ep} {edges_per_ep.get(ep,0)} < 8")
    # 장거리 cross-edge 쿼터
    if EPISODES >= 4:
        cross_total_floor = math.ceil(0.75*EPISODES)
        if len(cross_edges) < cross_total_floor:
            errors.append(f"COVFLOOR CrossEdge 총 {len(cross_edges)} < floor {cross_total_floor} (=ceil(0.75*ep))")
        longrange = sum(1 for e in cross_edges if e.get('gap_episodes',0) >= 5)
        lr_floor = max(3, math.ceil(EPISODES/6))
        if longrange < lr_floor:
            errors.append(f"COVFLOOR 장거리(gap>=5) CrossEdge {longrange} < floor {lr_floor}")
    # plant -> payoff 페어링 최소율
    plants = sum(1 for p in all_payoff if p.get('edge_type_guess')=='plant_payoff')
    paid = sum(1 for e in cross_edges if e.get('edge_type')=='plant_payoff')
    if plants > 0:
        pair_floor = math.ceil(0.3*plants)
        if paid < pair_floor:
            errors.append(f"COVFLOOR plant_payoff 회수 {paid} < floor {pair_floor} (=ceil(0.3*{plants} plants))")

# ── 실행 ──────────────────────────────────────────────────────
print(f"=== {work} 신규계층 검증 v2 (eps={EPISODES}, scenes={SCENES}) ===")
print(f"LocalEdge+CrossEdge: {len(all_edges)} records ({len(edge_files)} files)  cross={len(cross_edges)}")
print(f"CharacterArc: {len(all_chararc)} records")
print(f"RelationshipArc: {len(all_relarc)} records")
print(f"PayoffCandidate: {len(all_payoff)} records")
print()

# 깊이 floor
minlen(all_edges, 'note', 'EDGE')
minlen(all_chararc, 'evidence', 'CHARARC')
minlen(all_relarc, 'evidence', 'RELARC')
minlen(all_payoff, 'description', 'PAYOFF')
# 다양성 + 산문 헤드라인 다양성
diversity(all_edges, 'note', 'EDGE')
diversity(all_chararc, 'evidence', 'CHARARC')
diversity(all_chararc, 'state_headline', 'CHARARC')
diversity(all_relarc, 'evidence', 'RELARC')
diversity(all_relarc, 'relation_headline', 'RELARC')
diversity(all_payoff, 'description', 'PAYOFF')
placeholder_check(all_edges + all_chararc + all_relarc + all_payoff, 'ALL')
coverage_floors()

print(f"ERRORS: {len(errors)}")
for e in errors:
    print(" -", e)
if not errors:
    print()
    print(f"ERRORS 0 — [{work}] 신규계층 v2 강한게이트 ALL PASS")
