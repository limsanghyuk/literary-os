# -*- coding: utf-8 -*-
"""CT-07R 사후 분석 — 정답표 원 5범주 분해 + 렌더 40본 개별 점수.

봉인 이후에 추가된 스크립트다. 사전지정 분석이 아니며 판정을 바꾸지 않는다.
봉인된 RESULT.json / CT07R_analyze.py 는 건드리지 않는다.

    python3 CT07R_posthoc_cat5.py --run .
"""
import argparse, collections, io, json, os
from statistics import mean

CATS = ['character', 'goal', 'conflict', 'info', 'link']
LABS = ['씬내부', '배치관계']


def load(run):
    j = lambda p: json.load(io.open(os.path.join(run, p), encoding='utf-8'))
    blind = {b['render_id']: b for b in j('BLIND_MAP.json')}
    lab = {(r['scene'], r['idx']): r for r in j('element_labels.json')}
    E = collections.defaultdict(list)
    for i in (1, 2, 3):
        for r in j('scores/scorer%d.json' % i)['results']:
            E[r['render_id']].append(r['E'])
    return blind, lab, E


def scene_key(b):
    return "%s_%02d_s%d" % (b['work'], b['episode'], b['scene_no'])


def decompose(blind, lab, E, keyfn, keys):
    out = {}
    for k in keys:
        arm = collections.defaultdict(list)
        for rid, b in blind.items():
            s = scene_key(b)
            ix = [i for i in range(5) if keyfn(lab[(s, i)]) == k]
            if not ix:
                continue
            for e in E[rid]:
                arm[b['arm']].append(5.0 * sum(e[i] for i in ix) / len(ix))
        m = {a: mean(v) for a, v in arm.items()}
        out[k] = dict(n=len(arm['T']) // 3, A=m['A'], B=m['B'], T=m['T'], TN=m['TN'],
                      r_T=(m['T'] - m['A']) / (m['B'] - m['A']), D_N=m['T'] - m['TN'])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--run', default='.')
    ap.add_argument('--json', default=None)
    a = ap.parse_args()
    blind, lab, E = load(a.run)

    c5 = decompose(blind, lab, E, lambda r: r['cat'], CATS)
    c2 = decompose(blind, lab, E, lambda r: r['label'], LABS)

    for title, tbl in ((u'원 5범주 (사후)', c5), (u'2부류 (AMD-01 §3.4 사전지정, 대조용)', c2)):
        print(u'\n== %s ==' % title)
        print(u'%-10s %3s %7s %7s %7s %7s %8s %8s' % ('cat', 'n', 'A', 'B', 'T', 'TN', 'r_T', 'D_N'))
        for k, v in tbl.items():
            print(u'%-10s %3d %7.3f %7.3f %7.3f %7.3f %8.3f %8.3f'
                  % (k, v['n'], v['A'], v['B'], v['T'], v['TN'], v['r_T'], v['D_N']))

    print(u'\n== 렌더 40본 개별 점수 (요소 5개 중 성립 수) ==')
    print(u'%-5s %-14s %3s %5s %3s %4s %4s %4s %7s' % ('id', 'work', 'ep', 'scene', 'arm', 's1', 's2', 's3', 'mean'))
    rows = []
    for rid in sorted(blind, key=lambda x: int(x[1:])):
        b = blind[rid]
        sc = [sum(e) for e in E[rid]]
        rows.append(dict(render_id=rid, work=b['work'], episode=b['episode'],
                         scene_no=b['scene_no'], arm=b['arm'], scores=sc, mean=mean(sc)))
        print(u'%-5s %-14s %3d %5d %3s %4d %4d %4d %7.2f'
              % (rid, b['work'], b['episode'], b['scene_no'], b['arm'], sc[0], sc[1], sc[2], mean(sc)))

    if a.json:
        json.dump({'prespecified': False, 'by_cat5': c5, 'by_label2': c2, 'renders': rows},
                  io.open(a.json, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
