# -*- coding: utf-8 -*-
"""CT-08A 앵커 결정론적 선정 — LOS-CT08A-SELECT-V2.0 (앵커 단위 = 시퀀스)
V1.0(씬 단위)은 절단 등화 하에서 I-cut 제거량이 8.5%에 그쳐 T-F/T-I 대조가 성립하지 않았다.
후판은 시퀀스 단위 산출물이므로 앵커도 시퀀스로 올린다. 난수 없음."""
import json, glob, collections, os
BASE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(BASE, '..')
recs = []
for f in sorted(glob.glob(os.path.join(ROOT, 'db/seqcard_ko/reinforcement_v1/thick_sequence/가을동화/*.jsonl'))):
    for l in open(f, encoding='utf-8'): recs.append(json.loads(l))

pool = [r for r in recs if len(r['info_shift']) >= 1 and len(r['plant_payoff']) >= 1
        and 4 <= len(r['member_scene_nos']) <= 10]
pool.sort(key=lambda r: (r['episode_no'], r['seq_index']))
LONG_EPS = {6, 8, 11, 13, 14}

def pick(c, k, cap=2):
    out, per, seen = [], collections.Counter(), set()
    order = [c[round(i * (len(c) - 1) / max(k - 1, 1))] for i in range(k)] if k > 1 else c[:1]
    for x in list(order) + c:
        if len(out) >= k: break
        if x['seq_id'] in seen or per[x['episode_no']] >= cap: continue
        seen.add(x['seq_id']); per[x['episode_no']] += 1; out.append(x)
    return out[:k]

sel = pick([r for r in pool if r['episode_no'] in LONG_EPS], 8) + \
      pick([r for r in pool if r['episode_no'] not in LONG_EPS], 16)
sel.sort(key=lambda r: (r['episode_no'], r['seq_index']))
rows = []
for i, r in enumerate(sel, 1):
    rows.append(dict(anchor_id='A%02d' % i, seq_id=r['seq_id'], episode=r['episode_no'],
                     seq_index=r['seq_index'], scenes=r['member_scene_nos'],
                     n_scene=len(r['member_scene_nos']),
                     n_prop=sum(len(s['functional_propositions']) for s in r['scene_notes']),
                     n_cast=len(r['cast']), n_info=len(r['info_shift']), n_pp=len(r['plant_payoff']),
                     stratum='LONG' if r['episode_no'] in LONG_EPS else 'SHORT'))
print('모집단 %d시퀀스 → 선정 %d (LONG %d · SHORT %d)' % (
    len(pool), len(rows), sum(x['stratum'] == 'LONG' for x in rows), sum(x['stratum'] == 'SHORT' for x in rows)))
print('회차분포', dict(sorted(collections.Counter(x['episode'] for x in rows).items())))
print('씬 총 %d · 명제 총 %d' % (sum(x['n_scene'] for x in rows), sum(x['n_prop'] for x in rows)))
for x in rows:
    print('  %s %-18s EP%02d q%d  씬%2d 명제%2d cast%d info%d pp%d [%s]' % (
        x['anchor_id'], x['seq_id'], x['episode'], x['seq_index'], x['n_scene'],
        x['n_prop'], x['n_cast'], x['n_info'], x['n_pp'], x['stratum']))
json.dump(rows, open(os.path.join(BASE, 'ANCHORS.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
