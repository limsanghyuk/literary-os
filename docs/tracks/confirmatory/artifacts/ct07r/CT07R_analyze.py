# -*- coding: utf-8 -*-
"""CT-07R 판정 재계산기 — LOS-CT07R-ANALYZE-V1.0

입력 (전부 허브에 있음)
  scores/scorer1.json, scorer2.json, scorer3.json   채점자 3인 요소 판정 벡터
  BLIND_MAP.json                                    render_id -> work/episode/scene_no/arm
  element_labels.json                               AMD-01 §3.4 범주 라벨

출력
  사전등록 §7 4조건 판정, 앵커별 원점수, AMD-01 S1/S2/S3 민감도, 채점자 일치도

사용:  python CT07R_analyze.py --run C:\\claude\\CT07R_run_20260807

집 컴퓨터에서 이 스크립트만 돌리면 RESULT.json 의 모든 수치가 재현된다.
정답표 원문·렌더 원문 없이도 재계산이 성립하도록 설계했다 — 채점은 이미 끝났고
채점 결과(요소별 0/1)만 있으면 판정 산술은 닫힌다.
"""
import json, os, glob, argparse, itertools, collections

ap = argparse.ArgumentParser()
ap.add_argument('--run', default=r'C:\claude\CT07R_run_20260807')
A = ap.parse_args()
R = A.run

SCALE = 5.0          # 정답표 내장 scoring = 5.0 * matched / n_elements
N_ELEM = 5
ARMS = ['A', 'B', 'T', 'TN']

bm = {b['render_id']: b for b in json.load(open(os.path.join(R, 'BLIND_MAP.json'), encoding='utf-8'))}
raters = [json.load(open(p, encoding='utf-8'))
          for p in sorted(glob.glob(os.path.join(R, 'scores', 'scorer*.json')))]
E = collections.defaultdict(list)
for s in raters:
    for r in s['results']:
        E[r['render_id']].append(r['E'])


def scene_key(b):
    return f"{b['work']}_{b['episode']:02d}_s{b['scene_no']}"


def mean(v):
    return sum(v) / len(v)


def score(rid, idxs=None):
    """3인 평균 점수. idxs 를 주면 그 요소 부분집합으로 재정규화한다."""
    ix = idxs if idxs is not None else list(range(N_ELEM))
    return mean([SCALE * sum(e[i] for i in ix) / len(ix) for e in E[rid]])


def block(anchors, idx_of=None, label=''):
    """anchors = [(work, ep, scene_no), ...]"""
    keep = {(a['work'], a['episode'], a['scene_no']) for a in anchors} \
        if isinstance(anchors[0], dict) else set(anchors)
    m = {}
    for arm in ARMS:
        vals = []
        for rid, b in bm.items():
            if b['arm'] != arm:
                continue
            if (b['work'], b['episode'], b['scene_no']) not in keep:
                continue
            ix = idx_of(scene_key(b)) if idx_of else None
            if ix is not None and not ix:
                continue
            vals.append(score(rid, ix))
        m[arm] = mean(vals)
    ba = m['B'] - m['A']
    return dict(label=label, **m, BA=ba,
                rT=(m['T'] - m['A']) / ba if ba else float('nan'),
                DN=m['T'] - m['TN'])


ANCH = sorted({(b['work'], b['episode'], b['scene_no']) for b in bm.values()})
WORKS = sorted({a[0] for a in ANCH})

print('=' * 78)
print('CT-07R 판정 재계산   앵커 {}건 · 렌더 {}본 · 채점자 {}인'.format(
    len(ANCH), len(bm), len(raters)))
print('=' * 78)

# ---------- 1차 판정 ----------
blocks = [block(ANCH, label='전체')] + \
         [block([a for a in ANCH if a[0] == w], label=w) for w in WORKS]
print('\n[팔별 평균 0-5]')
print('{:16s}{:>7}{:>7}{:>7}{:>7}{:>8}{:>8}{:>8}'.format(
    '', 'A', 'B', 'T', 'TN', 'B-A', 'r_T', 'D_N'))
for b in blocks:
    print('{:16s}{A:7.3f}{B:7.3f}{T:7.3f}{TN:7.3f}{BA:8.3f}{rT:8.3f}{DN:8.3f}'.format(
        b['label'], **b))

ov = blocks[0]
c1 = ov['BA'] >= 0.5
c2 = ov['rT'] >= 0.70
c3 = all(b['rT'] > 0.30 for b in blocks[1:])
c4 = all(b['DN'] > 0 for b in blocks)
print('\n[사전등록 §7 조건]')
print('  1 배치 유효성  B-A>=0.5      : {:.3f}  -> {}'.format(ov['BA'], 'PASS' if c1 else 'FAIL'))
print('  2 상대위치     r_T>=0.70     : {:.3f}  -> {}'.format(ov['rT'], 'PASS' if c2 else 'FAIL'))
print('  3 작품별       r_T>0.30      : {}  -> {}'.format(
    ', '.join('{:.3f}'.format(b['rT']) for b in blocks[1:]), 'PASS' if c3 else 'FAIL'))
print('  4 음성대조     TN<T          : {}  -> {}'.format(
    ', '.join('{:+.3f}'.format(b['DN']) for b in blocks), 'PASS' if c4 else 'FAIL'))
verdict = 'PASS' if all([c1, c2, c3, c4]) else 'FAIL'
print('\n>>> 판정: {}   ({})'.format(
    verdict, '강한 재현' if ov['rT'] >= 1.0 else '강한 재현 아님 — r_T < 1.0'))

# ---------- 앵커별 원점수 ----------
print('\n[앵커별 원점수 3인 평균]')
print('{:22s}{:>7}{:>7}{:>7}{:>7}'.format('앵커', *ARMS))
for a in ANCH:
    row = {}
    for rid, b in bm.items():
        if (b['work'], b['episode'], b['scene_no']) == a:
            row[b['arm']] = score(rid)
    print('{:22s}{:7.2f}{:7.2f}{:7.2f}{:7.2f}'.format(
        '{}_{:02d}_s{}'.format(*a), *[row[x] for x in ARMS]))

# ---------- S2 leave-one-out ----------
loo = [(a, block([x for x in ANCH if x != a])) for a in ANCH]
rs = [b['rT'] for _, b in loo]
print('\n[AMD-01 §3.3  민감도 S2 leave-one-out]')
print('  r_T  min {:.3f} (제외 {})   max {:.3f} (제외 {})'.format(
    min(rs), '{}_{:02d}_s{}'.format(*loo[rs.index(min(rs))][0]),
    max(rs), '{}_{:02d}_s{}'.format(*loo[rs.index(max(rs))][0])))
print('  D_N  min {:+.3f}   max {:+.3f}'.format(
    min(b['DN'] for _, b in loo), max(b['DN'] for _, b in loo)))
print('  FRAGILE 병기 필요: {}'.format('예' if min(rs) < 0.70 else '아니오 (최소 >= 0.70)'))

# ---------- S3 범주 분해 ----------
lp = os.path.join(R, 'element_labels.json')
if os.path.exists(lp):
    lab = {(r['scene'], r['idx']): r['label'] for r in json.load(open(lp, encoding='utf-8'))}
    print('\n[AMD-01 §3.4  민감도 S3 범주 분해]')
    print('{:16s}{:>5}{:>7}{:>7}{:>7}{:>7}{:>8}{:>8}'.format(
        '', 'n', 'A', 'B', 'T', 'TN', 'r_T', 'D_N'))
    for cat in ('씬내부', '배치관계'):
        n = sum(1 for k, v in lab.items() if v == cat)
        b = block(ANCH, idx_of=lambda sk, c=cat: [i for i in range(N_ELEM)
                                                  if lab.get((sk, i)) == c], label=cat)
        print('{:16s}{:5d}{A:7.3f}{B:7.3f}{T:7.3f}{TN:7.3f}{rT:8.3f}{DN:8.3f}'.format(
            b['label'], n, **b))

# ---------- 채점자 일치도 ----------
tot = agree = 0
for rid, vs in E.items():
    for i in range(N_ELEM):
        col = [v[i] for v in vs]
        for x, y in itertools.combinations(col, 2):
            tot += 1
            agree += (x == y)
print('\n[채점자 일치도]  요소 단위 쌍별 {}/{} = {:.1%}'.format(agree, tot, agree / tot))
print('  채점자별 총점(만점 {}): {}'.format(
    len(bm) * SCALE,
    ', '.join(str(sum(SCALE * sum(r['E']) / N_ELEM for r in s['results'])) for s in raters)))
print('=' * 78)
