# -*- coding: utf-8 -*-
"""허브 안전판 생성기 — LOS-CT-HUBSAFE-20260805-V1.0

허브 경계 정책: hub_boundary = "No raw scripts, source scripts, or full authored JSONL"
정답표의 evidence 는 설명 산문 + 원문 직접인용이 섞인 문자열이다.
실측(감사 §5): 인용 71건, 평균 15.8자, 최대 47자, 총 1,138자 = 홀드아웃 원문 7,005자의 16.25%,
그리고 1건은 원문 한 행과 완전히 일치한다. 따라서 정본을 그대로 허브에 올리지 않는다.

규칙
  1. evidence·text 안의 작은따옴표 인용 '...' 을 앞 8자 + 말줄임표로 절단.
     행 번호와 설명 산문은 보존한다 — 집 컴퓨터에서 검토가 가능해야 하므로.
  2. 2차 방어: 따옴표 짝이 어긋나 1차를 빠져나간 원문 행을 직접 치환.
  3. 검증 파일의 note 필드는 원문을 인용하므로 통째로 제거. 판정과 5축만 남긴다.
  4. 게이트: 절단 후 원문 orig/*.txt 의 어떤 행과도 완전 일치가 없어야 한다.

사용:  python make_hubsafe.py --root C:\claude
"""
import json, os, re, argparse, hashlib

ap = argparse.ArgumentParser()
ap.add_argument('--root', default=r'C:\claude')
ap.add_argument('--out', default=None)
A = ap.parse_args()
R = A.root
OUT = A.out or os.path.join(R, 'CT_AUDIT_20260805', 'hubsafe')
CT06 = os.path.join(R, 'CT06_run_20260805')
ORIG = os.path.join(R, 'G1_run_20260804', 'orig')
os.makedirs(OUT, exist_ok=True)

TRUNC = 8
ELL = '…'
QUOTE = re.compile(r"'([^']{1,200})'")
stat = {'n': 0, 'cut': 0, 'before': 0, 'after': 0, 'line_hits': 0}


def J(p):
    with open(p, encoding='utf-8') as f:
        return json.load(f)


def W(p, obj):
    s = json.dumps(obj, ensure_ascii=False, indent=2)
    if os.path.exists(p):
        os.remove(p)                      # D-36 회피: 덮어쓰기 금지, 삭제 후 신규 생성
    with open(p, 'w', encoding='utf-8') as f:
        f.write(s)
    J(p)                                  # 파싱 재검증
    return os.path.getsize(p)


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def redact(s):
    def rep(m):
        q = m.group(1)
        stat['n'] += 1
        stat['before'] += len(q)
        if len(q) > TRUNC:
            stat['cut'] += 1
            q = q[:TRUNC] + ELL
        stat['after'] += len(q)
        return "'" + q + "'"
    return QUOTE.sub(rep, s)


# ---------- 0. 원문 행 사전 ----------
SRCLINES = set()
for fn in sorted(os.listdir(ORIG)):
    if fn.endswith('.txt'):
        for ln in open(os.path.join(ORIG, fn), encoding='utf-8'):
            t = ln.strip()
            if len(t) >= 6:
                SRCLINES.add(t)
SRCORDER = sorted(SRCLINES, key=len, reverse=True)   # 긴 행부터


def redact_lines(s):
    """2차 방어 — 따옴표 짝이 어긋나 1차를 빠져나간 원문 행을 직접 잘라낸다."""
    for L in SRCORDER:
        if L in s:
            stat['line_hits'] += 1
            s = s.replace(L, L[:TRUNC] + ELL)
    return s


# ---------- 1. 정답표 허브 안전판 ----------
KEYSRC = os.path.join(CT06, 'CT06_FUNCTION_KEY.json')


def scrub(node):
    """문서 전체의 모든 문자열에 적용한다. elements 뿐 아니라 revision/note 에도
    원문 인용이 섞여 있음이 게이트에서 실측됐다(건빵 s7 conflict, revision items[3])."""
    if isinstance(node, dict):
        return {k: scrub(v) for k, v in node.items()}
    if isinstance(node, list):
        return [scrub(v) for v in node]
    if isinstance(node, str):
        return redact_lines(redact(node))
    return node


key = scrub(J(KEYSRC))
key['_hubsafe'] = {
    'doc_id': 'LOS-CT06-KEY-V1.2-HUBSAFE',
    'derived_from': 'CT06_FUNCTION_KEY.json',
    'source_sha256': sha(KEYSRC),
    'rule': 'evidence·text 안의 작은따옴표 직접인용을 앞 8자 + 말줄임표로 절단. 행 번호·설명 산문·판정 조건·난이도·범주는 원본과 동일.',
    'why': '허브 경계 정책(원문 대본 커밋 금지). 정본 인용 71건 총 1,138자 = 홀드아웃 원문 7,005자의 16.25%, 1건은 원문 한 행과 완전 일치.',
    'note': '★채점 집행에는 이 파일을 쓰지 말 것. 집행 정본은 로컬 C:\\claude\\CT06_run_20260805\\CT06_FUNCTION_KEY.json (sha = source_sha256) 이다.',
}
b1 = W(os.path.join(OUT, 'CT06_FUNCTION_KEY_v1.2.hubsafe.json'), key)

# ---------- 2. 검증 파일 tally-only ----------
AXES = ['scene_placement', 'factual_match', 'function_scale', 'independence', 'evidence_lines']
made = []
for src, dst in [('CT06_KEY_VERIFICATION.json', 'CT06_KEY_VERIFICATION_r1.tally.json'),
                 ('CT06_KEY_VERIFICATION_v1.1.json', 'CT06_KEY_VERIFICATION_r2.tally.json'),
                 ('CT06_KEY_VERIFICATION_v1.2.json', 'CT06_KEY_VERIFICATION_r3.tally.json')]:
    p = os.path.join(CT06, src)
    d = J(p)
    vs = d if isinstance(d, list) else d['verdicts']
    rows, tally = [], {}
    for v in vs:
        r = {'scene': v.get('scene'), 'category': v.get('category'), 'verdict': v.get('verdict')}
        for ax in AXES:
            if ax in v:
                r[ax] = v[ax]
        rows.append(r)
        tally[v.get('verdict')] = tally.get(v.get('verdict'), 0) + 1
    obj = {
        'doc_id': dst.replace('.json', '').replace('.', '_').upper(),
        'derived_from': src, 'source_sha256': sha(p),
        'rule': 'note 필드 제거(원문 인용 포함). 판정 + 5축 + 씬·범주 키만 보존.',
        'n': len(rows), 'tally': tally, 'verdicts': rows,
    }
    made.append((dst, W(os.path.join(OUT, dst), obj), len(rows), tally))

# ---------- 3. 게이트 ----------
hits = []
for fn in sorted(os.listdir(OUT)):
    txt = open(os.path.join(OUT, fn), encoding='utf-8').read()
    for L in SRCLINES:
        if L in txt:
            hits.append((fn, L))

print('=' * 66)
print('허브 안전판 생성 — LOS-CT-HUBSAFE-20260805-V1.0')
print('=' * 66)
print('정답표 안전판   : {:,} B   (정본 {:,} B)'.format(b1, os.path.getsize(KEYSRC)))
print('  인용 절단     : 총 {}건 중 {}건 절단  {:,}자 -> {:,}자 ({:.1%} 잔존)'.format(
    stat['n'], stat['cut'], stat['before'], stat['after'],
    stat['after'] / max(stat['before'], 1)))
print('  2차 방어 적중 : {}건 (따옴표 짝 어긋남으로 1차를 빠져나간 원문 행)'.format(stat['line_hits']))
for dst, b, n, t in made:
    print('{:42s} {:>7,} B  n={}  {}'.format(dst, b, n, t))
print('원문 6자 이상 행 후보 : {}행'.format(len(SRCLINES)))
print('★게이트 — 절단 후 원문 행 완전일치 : {}건  -> {}'.format(
    len(hits), 'PASS' if not hits else '★FAIL ' + repr(hits[:5])))
print('=' * 66)
