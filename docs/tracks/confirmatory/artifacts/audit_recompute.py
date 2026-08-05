# -*- coding: utf-8 -*-
"""2026-08-05 자기 감사 — 보고서에 적힌 수치를 원자료에서 다시 산출한다.

이 스크립트는 보고서를 읽지 않는다. 원자료(채점 원본·검증 판정·정답표 JSON)만 읽어
수치를 새로 계산하고, 보고서에 적힌 값(EXPECT 딕셔너리에 하드코딩)과 대조한다.
집 PC에서 그대로 실행해 같은 값이 나오는지 확인할 수 있다.

전제 경로 (기본값은 회사 세션 기준, --root 로 변경 가능)
  <root>/CT03_run_20260805/       CT-03 원자료
  <root>/CT06_run_20260805/       CT-06 정답표·검증
  <root>/G1_run_20260804/orig/    홀드아웃 10씬 원문 (D-38 재산출에만 사용)
"""
import argparse, json, os, re, random, collections, statistics as st, sys

ap = argparse.ArgumentParser()
ap.add_argument('--root', default=r'C:\claude')
A = ap.parse_args()
R = A.root
CT03 = os.path.join(R, 'CT03_run_20260805')
CT06 = os.path.join(R, 'CT06_run_20260805')
ORIG = os.path.join(R, 'G1_run_20260804', 'orig')

SEED, BOOT = 20260805, 20000
DIMS = ['d1', 'd2', 'd3', 'd4', 'd5']
BG, HS = '건빵선생과별사탕_01_', '한성별곡_01_'

results = []          # (항목, 보고값, 실측값, 판정)


def chk(name, expect, got, tol=0.0005):
    if isinstance(expect, float) and isinstance(got, float):
        ok = abs(expect - got) <= tol
    else:
        ok = expect == got
    results.append((name, expect, got, 'OK' if ok else '★불일치'))
    print('  %-46s 보고 %-22s 실측 %-22s %s'
          % (name, expect, got, 'OK' if ok else '★불일치'))


def J(p):
    return json.load(open(p, encoding='utf-8'))


# ==================================================================== CT-03
print('=' * 96)
print('A. CT-03 작법 필적 시험 — 원자료에서 재산출')
print('=' * 96)

sealed = J(os.path.join(CT03, 'CT03_SEALED_MAP.json'))
items = J(os.path.join(CT03, 'items_raw.json'))
LEN = {(r['seq'], r['scene_no']): {v: len(r[v]) for v in 'HAB'} for r in items}

rows = []
for j in range(3):
    sid = 'J%d' % j
    key = {e['qid']: e for e in sealed['scorers'][sid]}
    sc = J(os.path.join(CT03, 'scores', 'CT03_SCORE_%s.json' % sid))
    for x in sc['items']:
        k = dict(key[x['qid']])
        k.update({'scorer': sid, 'verdict': x['verdict'], 'reason': x['reason'],
                  'craft': st.mean([x[d] for d in DIMS])})
        k.update({d: x[d] for d in DIMS})
        k['correct'] = 1 if x['verdict'] == k['truth'] else 0
        rows.append(k)

main = [r for r in rows if not r['is_anchor']]
anchors = [r for r in rows if r['is_anchor']]


def ba(rs):
    o = [r['correct'] for r in rs if r['truth'] == '원작']
    g = [r['correct'] for r in rs if r['truth'] == '생성']
    if not o or not g:
        return float('nan')
    return (st.mean(o) + st.mean(g)) / 2


def boot(rs, fn, n=BOOT, seed=SEED):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        s = [rs[rng.randrange(len(rs))] for _ in range(len(rs))]
        v = fn(s)
        if v == v:
            out.append(v)
    out.sort()
    return out[int(.025 * len(out))], out[int(.975 * len(out))]


print('\n[A1] 앵커 게이트 (PREREG §5)')
for j in range(3):
    sid = 'J%d' % j
    a = [r for r in anchors if r['scorer'] == sid]
    lo = st.mean([r['craft'] for r in a if r['anchor_kind'] == 'LOW'])
    hi = st.mean([r['craft'] for r in a if r['anchor_kind'] == 'HIGH'])
    chk('%s 저품질앵커 (기준<3.0)' % sid, {'J0': 0.20, 'J1': 0.10, 'J2': 0.00}[sid], round(lo, 2))
    chk('%s 고품질앵커 (기준>2.5)' % sid, {'J0': 3.70, 'J1': 3.90, 'J2': 3.80}[sid], round(hi, 2))
    chk('%s 앵커 판별정확도' % sid, 1.00, round(st.mean([r['correct'] for r in a]), 2))
chk('본시험 유효 문항 수', 72, len(main))
chk('앵커 문항 수', 12, len(anchors))

print('\n[A2] 1차 종점 — 균형정확도')
BA = ba(main)
lo, hi = boot(main, ba)
chk('BA', 0.979, round(BA, 3))
chk('BA 95%CI 하한', 0.947, round(lo, 3))
chk('BA 95%CI 상한', 1.000, round(hi, 3))
chk('단순 정확도', 0.972, round(st.mean([r['correct'] for r in main]), 3))
chk('원작 문항 정답률', 1.000, round(st.mean([r['correct'] for r in main if r['truth'] == '원작']), 3))
chk('원작 문항 n', 24, len([r for r in main if r['truth'] == '원작']))
chk('생성 문항 정답률', 0.958, round(st.mean([r['correct'] for r in main if r['truth'] == '생성']), 3))
chk('생성 문항 n', 48, len([r for r in main if r['truth'] == '생성']))

wrong = [r for r in main if not r['correct']]
chk('오답 건수', 2, len(wrong))
chk('오답 전부 J1인가', True, all(r['scorer'] == 'J1' for r in wrong))
chk('원작→생성 오판 건수', 0, len([r for r in wrong if r['truth'] == '원작']))

for v, nm, e_ba, e_lo, e_hi in [('A', 'H vs A′', 0.979, 0.932, 1.000),
                                ('B', 'H vs B′', 0.979, 0.929, 1.000)]:
    sub = [r for r in main if r['version'] in ('H', v)]
    b2 = ba(sub); l2, h2 = boot(sub, ba)
    chk('%s BA' % nm, e_ba, round(b2, 3))
    chk('%s CI' % nm, (e_lo, e_hi), (round(l2, 3), round(h2, 3)))

print('\n[A3] 공동 1차 종점 — 작법 품질')
M = {v: st.mean([r['craft'] for r in main if r['version'] == v]) for v in 'HAB'}
chk('작법 H 총평균', 2.875, round(M['H'], 3))
chk('작법 A′ 총평균', 2.983, round(M['A'], 3))
chk('작법 B′ 총평균', 2.958, round(M['B'], 3))
gap = M['H'] - max(M['A'], M['B'])
gapfn = lambda rs: (st.mean([r['craft'] for r in rs if r['version'] == 'H'])
                    - max(st.mean([r['craft'] for r in rs if r['version'] == 'A']),
                          st.mean([r['craft'] for r in rs if r['version'] == 'B'])))


def gapsafe(rs):
    try:
        return gapfn(rs)
    except Exception:
        return float('nan')


gl, gh = boot(main, gapsafe)
chk('작법 격차 H−max(A′,B′)', -0.108, round(gap, 3))
chk('격차 95%CI', (-0.581, 0.213), (round(gl, 3), round(gh, 3)))
D = {v: {d: st.mean([r[d] for r in main if r['version'] == v]) for d in DIMS} for v in 'HAB'}
chk('④상투성 부재 격차 (보고 +0.62)', 0.62, round(D['H']['d4'] - max(D['A']['d4'], D['B']['d4']), 2))
chk('②구체성 격차 (보고 −0.42)', -0.42, round(D['H']['d2'] - max(D['A']['d2'], D['B']['d2']), 2))
chk('⑤서브텍스트 격차 (보고 −0.62)', -0.62, round(D['H']['d5'] - max(D['A']['d5'], D['B']['d5']), 2))

print('\n[A4] 판정 재현')
chk('① BA CI 상한 < 0.65', False, hi < 0.65)
chk('② 작법 격차 ≤ 0.5', True, gap <= 0.5)
chk('FAIL 조건 (CI 하한 ≥ 0.65)', True, lo >= 0.65)

print('\n[A5] 사전 고정 2차 분석')
rc = J(os.path.join(CT03, 'reason_classification.json'))
cnt = collections.Counter(x['cat'] for x in rc)
chk('근거분류 ⓒ 건수', 15, cnt['c'])
chk('근거분류 ⓓ 건수', 57, cnt['d'])
chk('ⓒ 비율', 20.8, round(100 * cnt['c'] / len(rc), 1))
idx = {(r['scorer'], r['qid']): r for r in main}
cs = [idx[(x['scorer'], x['qid'])] for x in rc if x['cat'] == 'c']
chk('ⓒ 15건 중 H 문항 수', 12, sum(1 for r in cs if r['version'] == 'H'))
ex = [idx[(x['scorer'], x['qid'])] for x in rc if x['cat'] != 'c']
el, eh = boot(ex, ba)
chk('ⓒ 제외 BA', 0.989, round(ba(ex), 3))
chk('ⓒ 제외 CI', (0.964, 1.000), (round(el, 3), round(eh, 3)))
d = sorted(set((r['seq'], r['scene_no']) for r in main),
           key=lambda k: abs(LEN[k]['H'] - (LEN[k]['A'] + LEN[k]['B']) / 2))
half = set(d[:12])
sub = [r for r in main if (r['seq'], r['scene_no']) in half]
l4, h4 = boot(sub, ba)
chk('분량차 하위 12씬 BA', 0.958, round(ba(sub), 3))
chk('분량차 하위 12씬 CI', (0.896, 1.000), (round(l4, 3), round(h4, 3)))
for w, e in [('건빵선생과별사탕_01', 0.958), ('한성별곡_01', 1.000)]:
    chk('%s BA' % w, e, round(ba([r for r in main if r['work'] == w]), 3))
for s, e in [('J0', 1.000), ('J1', 0.938), ('J2', 1.000)]:
    chk('채점자 %s BA' % s, e, round(ba([r for r in main if r['scorer'] == s]), 3))
for w, eh_, ea, eb in [('한성별곡_01', 394, 715, 693)]:
    rs = [r for r in items if r['work'] == w]
    chk('%s 평균 글자수 H/A/B' % w, (eh_, ea, eb),
        tuple(round(st.mean([len(r[v]) for r in rs])) for v in 'HAB'))

# ==================================================================== CT-06
print('\n' + '=' * 96)
print('B. CT-06 기능충실 정답표 — 원자료에서 재산출')
print('=' * 96)

key = J(os.path.join(CT06, 'CT06_FUNCTION_KEY.json'))
S = key['scenes']
els = [(sc, e) for sc, v in S.items() for e in v['elements']]
chk('씬 수', 10, len(S))
chk('총 요소 수', 49, len(els))
diff = collections.Counter(e['difficulty'] for _, e in els)
chk('난이도 low/mid/high', (8, 21, 20), (diff['low'], diff['mid'], diff['high']))
chk('건빵 s7 요소 수', 4, S[BG + 's7']['n_elements'])
chk('n_elements 필드 = 실제 요소 수', True, all(v['n_elements'] == len(v['elements']) for v in S.values()))
chk('범주 중복 0', True, all(len({e['cat'] for e in v['elements']}) == len(v['elements']) for v in S.values()))
chk('문장 중복 0', 0, len(els) - len({e['text'].strip() for _, e in els}))
chk('빈 필드 0', 0, sum(1 for _, e in els for f in ('cat', 'text', 'evidence', 'difficulty')
                       if not str(e.get(f, '')).strip()))
chk('씬당 low ≤ 1', True, all(sum(1 for e in v['elements'] if e['difficulty'] == 'low') <= 1
                             for v in S.values()))
chk('low 8건 전부 goal 범주인가', True, all(e['cat'] == 'goal' for _, e in els if e['difficulty'] == 'low'))
chk('low goal 을 가진 씬 수', 8, sum(1 for v in S.values()
                                 if any(e['difficulty'] == 'low' for e in v['elements'])))


def V(p):
    d = J(os.path.join(CT06, p))
    return d if isinstance(d, list) else d['verdicts']


V0, V1, V2 = V('CT06_KEY_VERIFICATION.json'), V('CT06_KEY_VERIFICATION_v1.1.json'), V('CT06_KEY_VERIFICATION_v1.2.json')
print('\n[B1] 검증 3회 집계')
for nm, v, e in [('1차', V0, (47, 3, 0)), ('2차', V1, (37, 12, 1)), ('3차', V2, (37, 12, 0))]:
    c = collections.Counter(x['verdict'] for x in v)
    chk('%s hold/weak/fail' % nm, e, (c['hold'], c['weak'], c['fail']))
chk('3차 요소 수', 49, len(V2))
chk('3차 씬배치 전건 ok', True, all(x.get('scene_placement') == 'ok' for x in V2))

print('\n[B2] weak 비율 (★보고서 §4 기재값과 대조)')
for nm, v, e in [('1차', V0, 0.06), ('2차', V1, 0.26), ('3차', V2, 0.24)]:
    c = collections.Counter(x['verdict'] for x in v)
    chk('%s weak 비율 (weak만)' % nm, e, round(c['weak'] / len(v), 3))
    print('       └ 참고: (weak+fail)/n = %.3f' % ((c['weak'] + c['fail']) / len(v)))

print('\n[B3] 개정 라운드 통과율')
# v1.1 에서 문장이 바뀐 9요소 = 개정이력 R2a·R2b·R3a·R3b·R3c·R3d(=R4b)·R3e·R4a·R4c
E11 = {(HS + 's1', 'conflict'), (HS + 's27', 'character'), (BG + 's7', 'conflict'),
       (BG + 's7', 'link'), (BG + 's15', 'link'), (HS + 's1', 'goal'),
       (HS + 's27', 'link'), (BG + 's15', 'conflict'), (HS + 's57', 'goal')}
p12 = J(os.path.join(CT06, 'CT06_KEY_v1.2_PATCH.json'))
E12 = {(e['scene'], e['cat']) for e in p12['edits']}
chk('v1.1 문장변경 요소 수', 9, len(E11))
chk('v1.2 개정 요소 수', 14, len(E12))
chk('v1.2 삭제 요소 수', 1, len(p12.get('drops', [])))

d0 = {(x['scene'], x['cat']): x['verdict'] for x in V0}
d1 = {(x['scene'], x['cat']): x['verdict'] for x in V1}
d2 = {(x['scene'], x['cat']): x['verdict'] for x in V2}
# R1 씬키 오배치 교환 — v1.0 의 s15/s19 블록은 v1.1 에서 서로 맞바뀌었다.
# '문장이 바뀌지 않은 요소'를 비교하려면 v1.0 판정을 교환된 키로 재정렬해야 한다.
swap = {BG + 's15': BG + 's19', BG + 's19': BG + 's15'}
d0r = {(swap.get(s, s), c): v for (s, c), v in d0.items()}

for lab, cur, prev, ed, e_ed, e_un in [('v1.1', d1, d0r, E11, (3, 9), (34, 41)),
                                       ('v1.2', d2, d1, E12, (11, 14), (26, 35))]:
    E = [k for k in cur if k in ed]
    U = [k for k in cur if k not in ed and k in prev]
    h = lambda K: sum(1 for k in K if cur[k] == 'hold')
    chk('%s 개정요소 통과' % lab, e_ed, (h(E), len(E)))
    chk('%s 미개정요소 통과' % lab, e_un, (h(U), len(U)))

print('\n[B4] ★D-37 검증자 단방향 표류 (문장 미변경 요소만)')
for lab, a, b, ed, e_n, e_same, e_agree, e_down in [
        ('1차→2차', d0r, d1, E11, 41, 34, 0.829, 7),
        ('2차→3차', d1, d2, E12, 35, 26, 0.743, 9)]:
    K = [k for k in b if k in a and k not in ed]
    same = sum(1 for k in K if a[k] == b[k])
    dis = [(k, a[k], b[k]) for k in K if a[k] != b[k]]
    dn = sum(1 for _, x, y in dis if x == 'hold' and y == 'weak')
    up = sum(1 for _, x, y in dis if x == 'weak' and y == 'hold')
    chk('%s 비교 대상 수' % lab, e_n, len(K))
    chk('%s 일치 건수' % lab, e_same, same)
    chk('%s 일치율' % lab, e_agree, round(same / len(K), 3))
    chk('%s hold→weak' % lab, e_down, dn)
    chk('%s weak→hold (역방향)' % lab, 0, up)
    chk('%s 그 외 방향' % lab, 0, len(dis) - dn - up)
# R1 재정렬을 하지 않으면 값이 달라진다는 사실 자체를 기록
K = [k for k in d1 if k in d0 and k not in E11]
print('       └ 참고: R1 씬키 재정렬 없이 비교하면 1차→2차 일치율 = %.3f (재정렬 시 0.829)'
      % (sum(1 for k in K if d0[k] == d1[k]) / len(K)))

print('\n[B5] ★D-38 결함수 vs 씬 길이 상관 — 검증 라운드별로 재산출')
if os.path.isdir(ORIG):
    scenes = [BG + s for s in ['s1', 's7', 's10', 's15', 's19']] + \
             [HS + s for s in ['s1', 's14', 's27', 's42', 's57']]
    size = {}
    for s in scenes:
        b = open(os.path.join(ORIG, s + '.txt'), 'rb').read()
        size[s] = (len(b), len([l for l in b.decode('utf-8').split('\n') if l.strip()]))

    def pear(x, y):
        mx, my = st.mean(x), st.mean(y)
        num = sum((a - mx) * (b - my) for a, b in zip(x, y))
        den = (sum((a - mx) ** 2 for a in x) * sum((b - my) ** 2 for b in y)) ** .5
        return num / den

    def defects(v, remap=False):
        c = collections.Counter()
        for x in v:
            if x['verdict'] in ('weak', 'fail'):
                s = swap.get(x['scene'], x['scene']) if remap else x['scene']
                c[s] += 1
        return c
    for nm, v, rm in [('1차(v1.0)', V0, True), ('2차(v1.1)', V1, False), ('3차(v1.2)', V2, False)]:
        dd = defects(v, rm)
        y = [dd.get(s, 0) for s in scenes]
        rb = pear([size[s][0] for s in scenes], y)
        rl = pear([size[s][1] for s in scenes], y)
        print('  %-10s 결함수 vs 바이트 r = %+.3f   vs 유효행 r = %+.3f   (n=10)' % (nm, rb, rl))
    dd = defects(V1)
    chk('D-38 보고값 r=−0.52 는 2차 기준인가', -0.52, round(pear([size[s][0] for s in scenes],
                                                       [dd.get(s, 0) for s in scenes]), 2))
    z = [s for s in scenes if dd.get(s, 0) == 0]
    chk('2차 결함0 씬 바이트', (1172, 1580, 3548), tuple(sorted(size[s][0] for s in z)))
    sh = sorted(scenes, key=lambda s: size[s][0])[:4]
    chk('최단 4씬 바이트', (677, 861, 882, 1029), tuple(sorted(size[s][0] for s in sh)))
    chk('최단 4씬 전부 결함 ≥ 2 (2차)', True, all(dd.get(s, 0) >= 2 for s in sh))
else:
    print('  (원문 폴더 없음 — D-38 재산출 생략: %s)' % ORIG)

print('\n[B6] evidence 인용 길이 — 허브 경계 점검용')
q = [(sc, e['cat'], t.strip()) for sc, e in els
     for t in re.findall(r"['\"‘“]([^'\"’”]{2,200})['\"’”]", e['evidence'])]
ln = [len(t) for _, _, t in q]
print('  인용 %d개  평균 %.1f자  최장 %d자  20자 초과 %d개  30자 초과 %d개'
      % (len(q), st.mean(ln), max(ln), sum(1 for x in ln if x > 20), sum(1 for x in ln if x > 30)))
print('  ★보고서 §7 은 "15자 내외 인용" 이라 기재 — 평균은 맞으나 상한이 아니다(최장 %d자).' % max(ln))
if os.path.isdir(ORIG):
    full = 0
    for sc, c, t in q:
        L = [l.strip() for l in open(os.path.join(ORIG, sc + '.txt'), encoding='utf-8').read().split('\n')]
        if t in L:
            full += 1
    print('  원문 전행과 완전일치하는 인용: %d개' % full)

print('\n' + '=' * 96)
bad = [r for r in results if r[3] != 'OK']
print('감사 대조 %d항목 — OK %d / ★불일치 %d' % (len(results), len(results) - len(bad), len(bad)))
for r in bad:
    print('  ★ %s : 보고 %s vs 실측 %s' % (r[0], r[1], r[2]))
print('=' * 96)
sys.exit(0)
