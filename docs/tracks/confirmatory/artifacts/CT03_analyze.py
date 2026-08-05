# -*- coding: utf-8 -*-
"""CT-03 언블라인딩 + 판정 산출
사전등록 LOS-CT-03-PREREG-V1.0 §5·§6 + 개정 LOS-CT-03-AMD-01
"""
import json, os, random, statistics as st

OUT = os.path.dirname(os.path.abspath(__file__))
SEED = 20260805
B = 20000
DIMS = ['d1', 'd2', 'd3', 'd4', 'd5']

sealed = json.load(open(os.path.join(OUT, 'CT03_SEALED_MAP.json'), encoding='utf-8'))
items = json.load(open(os.path.join(OUT, 'items_raw.json'), encoding='utf-8'))
LEN = {(r['seq'], r['scene_no']): {v: len(r[v]) for v in 'HAB'} for r in items}

rows = []
for j in range(3):
    sid = 'J%d' % j
    key = {e['qid']: e for e in sealed['scorers'][sid]}
    sc = json.load(open(os.path.join(OUT, 'scores', 'CT03_SCORE_%s.json' % sid), encoding='utf-8'))
    for x in sc['items']:
        k = key[x['qid']]
        q = dict(k)
        q.update({'scorer': sid, 'verdict': x['verdict'], 'reason': x['reason'],
                  'craft': st.mean([x[d] for d in DIMS])})
        q.update({d: x[d] for d in DIMS})
        q['correct'] = 1 if x['verdict'] == k['truth'] else 0
        rows.append(q)

# ---------- §5 앵커 보정 게이트 ----------
print('=' * 64)
print('§5 보정 앵커 게이트')
gate = {}
for j in range(3):
    sid = 'J%d' % j
    a = [r for r in rows if r['scorer'] == sid and r['is_anchor']]
    lo = st.mean([r['craft'] for r in a if r['anchor_kind'] == 'LOW'])
    hi = st.mean([r['craft'] for r in a if r['anchor_kind'] == 'HIGH'])
    ok = (lo < 3.0) and (hi > 2.5)
    gate[sid] = ok
    ac = st.mean([r['correct'] for r in a])
    print('  %s  저품질앵커 %.2f (기준 <3.0)  고품질앵커 %.2f (기준 >2.5)  -> %s  | 앵커 판별정확도 %.2f'
          % (sid, lo, hi, 'PASS' if ok else '무효', ac))
valid = [s for s in gate if gate[s]]
print('  유효 채점자:', valid)

main = [r for r in rows if not r['is_anchor'] and r['scorer'] in valid]
print('  본시험 유효 문항 수:', len(main))


def bal_acc(rs):
    o = [r['correct'] for r in rs if r['truth'] == '원작']
    g = [r['correct'] for r in rs if r['truth'] == '생성']
    if not o or not g:
        return float('nan')
    return (st.mean(o) + st.mean(g)) / 2


def boot(rs, fn, n=B, seed=SEED):
    rng = random.Random(seed)
    out = []
    for _ in range(n):
        s = [rs[rng.randrange(len(rs))] for _ in range(len(rs))]
        v = fn(s)
        if v == v:
            out.append(v)
    out.sort()
    return out[int(.025 * len(out))], out[int(.975 * len(out))]


print('=' * 64)
print('§6 1차 종점 — 균형정확도 (AMD-01)')
ba = bal_acc(main); lo, hi = boot(main, bal_acc)
acc = st.mean([r['correct'] for r in main])
print('  단순 정확도 (참고) : %.3f' % acc)
print('  균형정확도 BA      : %.3f   95%% CI [%.3f, %.3f]' % (ba, lo, hi))
print('  원작 문항 정답률   : %.3f (n=%d)' % (
    st.mean([r['correct'] for r in main if r['truth'] == '원작']),
    len([r for r in main if r['truth'] == '원작'])))
print('  생성 문항 정답률   : %.3f (n=%d)' % (
    st.mean([r['correct'] for r in main if r['truth'] == '생성']),
    len([r for r in main if r['truth'] == '생성'])))

print('-' * 64)
print('  분해 (보조, 검정 없음)')
for v, nm in [('A', 'H vs A′ 맨프롬프트'), ('B', 'H vs B′ SeqCard')]:
    sub = [r for r in main if r['version'] in ('H', v)]
    b2 = bal_acc(sub); l2, h2 = boot(sub, bal_acc)
    print('    %-20s BA %.3f  CI [%.3f, %.3f]' % (nm, b2, l2, h2))

print('=' * 64)
print('§6 공동 1차 종점 — 작법 품질')
means = {}
for v in 'HAB':
    rs = [r for r in main if r['version'] == v]
    means[v] = st.mean([r['craft'] for r in rs])
    per = {d: st.mean([r[d] for r in rs]) for d in DIMS}
    print('  %s  총평균 %.3f (n=%d)  | ' % (v, means[v], len(rs))
          + ' '.join('%s %.2f' % (d, per[d]) for d in DIMS))
gap = means['H'] - max(means['A'], means['B'])


def gapfn(rs):
    try:
        h = st.mean([r['craft'] for r in rs if r['version'] == 'H'])
        a = st.mean([r['craft'] for r in rs if r['version'] == 'A'])
        b = st.mean([r['craft'] for r in rs if r['version'] == 'B'])
        return h - max(a, b)
    except Exception:
        return float('nan')


gl, gh = boot(main, gapfn)
print('  격차 H − max(A′,B′) = %.3f   95%% CI [%.3f, %.3f]   (기준 ≤ 0.5)' % (gap, gl, gh))

print('=' * 64)
print('판정')
c1 = hi < 0.65
c2 = gap <= 0.5
print('  ① BA 95%% CI 상한 %.3f < 0.65 ?  %s' % (hi, 'YES' if c1 else 'NO'))
print('  ② 작법 격차 %.3f ≤ 0.5 ?        %s' % (gap, 'YES' if c2 else 'NO'))
verdict = 'PASS (구분 불가 · 작법 필적)' if (c1 and c2) else \
          ('FAIL' if (lo >= 0.65 or gap > 0.5) else '★보류')
print('  => %s' % verdict)

print('=' * 64)
print('2차 분석 (NORM-V1.0 §3에서 사전 고정)')
# (3) 작품별
for w in sorted(set(r['work'] for r in main)):
    sub = [r for r in main if r['work'] == w]
    b3 = bal_acc(sub); l3, h3 = boot(sub, bal_acc)
    cm = {v: st.mean([r['craft'] for r in sub if r['version'] == v]) for v in 'HAB'}
    print('  %-20s BA %.3f CI[%.3f,%.3f] | 작법 H %.2f A′ %.2f B′ %.2f'
          % (w, b3, l3, h3, cm['H'], cm['A'], cm['B']))
# (2) 분량 정합 민감도
d = sorted(set((r['seq'], r['scene_no']) for r in main),
           key=lambda k: abs(LEN[k]['H'] - (LEN[k]['A'] + LEN[k]['B']) / 2))
half = set(d[:12])
sub = [r for r in main if (r['seq'], r['scene_no']) in half]
b4 = bal_acc(sub); l4, h4 = boot(sub, bal_acc)
print('  분량차 하위 12씬만  BA %.3f CI[%.3f,%.3f]  (전체 %.3f)' % (b4, l4, h4, ba))
# (1) 근거 분류는 별도 분류자가 수행 -> 원자료만 덤프
json.dump([{k: r[k] for k in ('scorer', 'qid', 'reason')} for r in main],
          open(os.path.join(OUT, 'reasons_for_classification.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

json.dump(rows, open(os.path.join(OUT, 'RESULT_rows.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
json.dump({'gate': gate, 'BA': ba, 'BA_CI': [lo, hi], 'acc': acc,
           'craft': means, 'gap': gap, 'gap_CI': [gl, gh], 'verdict': verdict},
          open(os.path.join(OUT, 'RESULT_summary.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
