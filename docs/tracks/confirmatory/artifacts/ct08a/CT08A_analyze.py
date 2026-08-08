#!/usr/bin/env python3
"""CT-08A 재계산 — 허브 clone 만으로 닫힌다(원문·정답표 정본 불요).

사용: python CT08A_analyze.py --run docs/tracks/confirmatory/artifacts/ct08a
출력: 팔별 평균 · 3개 Δ + 부트스트랩 CI + McNemar 정확검정 · 무효조건 5종 · 일치도(전체/비자명)
"""
import argparse, json, math, random, itertools, re
from pathlib import Path

ARMS = ['B', 'T5', 'T-F', 'T-I', 'TN']


def load_scores(run: Path):
    S = {}
    for f in sorted((run / 'scores').glob('*.json')):
        if f.name.startswith('_'):
            continue
        d = json.loads(f.read_text(encoding='utf-8'))
        sc = d.get('scorer') or d.get('scorer_id')
        sc = 'S' + re.search(r'\d', str(sc)).group(0)
        S.setdefault(sc, {}).update(d['scores'])
    return S


def mcnemar(b, c):
    """이항 정확검정 양측."""
    n = b + c
    if n == 0:
        return 1.0
    k = min(b, c)
    p = sum(math.comb(n, i) for i in range(0, k + 1)) / 2 ** n * 2
    return min(1.0, p)


def boot_ci(d, B=20000, seed=7):
    rnd = random.Random(seed)
    n = len(d)
    m = sorted(sum(rnd.choice(d) for _ in range(n)) / n for _ in range(B))
    return m[int(.025 * B)], m[int(.975 * B)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', required=True)
    a = ap.parse_args()
    run = Path(a.run)

    S = load_scores(run)
    bm = json.loads((run / 'BLIND_MAP.json').read_text(encoding='utf-8'))['map']
    ids = sorted(bm)
    n_el = len(next(iter(S['S1'].values())))

    # 다수결
    maj = {r: [1 if sum(S[s][r][i] for s in S) >= 2 else 0 for i in range(n_el)] for r in ids}

    D = {}
    for r in ids:
        m = bm[r]
        D.setdefault(m['arm'], {})[m['anchor_id']] = maj[r]

    def sc(v):
        return 5.0 * sum(v) / n_el

    anchors = sorted(D['B'])
    print('앵커', len(anchors), '· 요소', n_el, '· 렌더', len(ids))
    means = {arm: sum(sc(D[arm][x]) for x in anchors) / len(anchors) for arm in ARMS}
    for arm in ARMS:
        print(f'  {arm:5s} {means[arm]:.3f}')

    print('\n[Δ]')
    for name, hi, lo in [('Δ_true  T5-(T-I)', 'T5', 'T-I'),
                         ('Δ_FI  (T-F)-(T-I)', 'T-F', 'T-I'),
                         ('Δ_app  T5-(T-F)', 'T5', 'T-F'),
                         ('B-T5 (교락, 판정 아님)', 'B', 'T5')]:
        d = [sc(D[hi][x]) - sc(D[lo][x]) for x in anchors]
        b = sum(1 for x in anchors for i in range(n_el) if D[hi][x][i] and not D[lo][x][i])
        c = sum(1 for x in anchors for i in range(n_el) if D[lo][x][i] and not D[hi][x][i])
        ci = boot_ci(d)
        print(f'  {name:24s} {sum(d)/len(d):+.3f} CI[{ci[0]:+.3f},{ci[1]:+.3f}] '
              f'McNemar b={b} c={c} p={mcnemar(b,c):.3g}')

    # 일치도 — 전체 / 비자명(3인 중 1명이라도 1)
    ag = tot = nag = ntot = 0
    pair = {}
    for r in ids:
        for k in range(n_el):
            vs = [S[s][r][k] for s in sorted(S)]
            for (i, x), (j, y) in itertools.combinations(list(enumerate(vs)), 2):
                key = f'S{i+1}-S{j+1}'
                p = pair.setdefault(key, [0, 0])
                p[1] += 1
                p[0] += (x == y)
                tot += 1
                ag += (x == y)
                if any(vs):
                    ntot += 1
                    nag += (x == y)
    print('\n[채점자 일치도]')
    for k, (a_, t_) in sorted(pair.items()):
        print(f'  {k} {a_/t_:.4f}')
    print(f'  전체 {ag/tot:.4f} · 비자명 {nag/ntot:.4f} (비자명 항목 {ntot//3}/{tot//3})')
    print('\n※ 사전등록 §8-2 무효조건 2 = 쌍별 일치도 ≥0.90. 미달 시 판정 무효.')


if __name__ == '__main__':
    main()
