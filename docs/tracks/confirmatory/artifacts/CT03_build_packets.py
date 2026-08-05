# -*- coding: utf-8 -*-
"""CT-03 채점 패킷 생성 (사전등록 LOS-CT-03-PREREG-V1.0 §4·§5)

라틴방격: 씬 i(0..23) × 채점자 j(0..2) -> 판본 VERS[(i+j)%3], VERS=['H','A','B']
  - 각 채점자는 24개 씬을 각각 1개 판본으로만 본다.
  - 3인을 합치면 24씬 × 3판본 = 72문항이 정확히 1회씩 제시된다.
패킷 = 24문항 + 보정앵커 4건 = 28. 제시순서 무작위(seed 20260805), 문항ID 무작위.
정답 매핑은 CT03_SEALED_MAP.json 에 봉인한다. 채점 완료 전 열람 금지.
"""
import json, os, random, hashlib

OUT = os.path.dirname(os.path.abspath(__file__))
SEED = 20260805
VERS = ['H', 'A', 'B']

items = json.load(open(os.path.join(OUT, 'items_raw.json'), encoding='utf-8'))
anchors = json.load(open(os.path.join(OUT, 'anchors.json'), encoding='utf-8'))

# 씬 정본 순서 (작품·시퀀스·씬번호) — 결정론
items.sort(key=lambda r: (r['work'], r['seq'], r['scene_no']))
assert len(items) == 24, len(items)

rng = random.Random(SEED)

# 문항ID 풀: 무작위 4자리 영숫자, 충돌 없음
pool = set()
while len(pool) < 3 * 28:
    pool.add(''.join(rng.choice('ABCDEFGHJKLMNPQRSTUVWXYZ23456789') for _ in range(4)))
pool = sorted(pool)
rng.shuffle(pool)
pool = iter(pool)

sealed = {'seed': SEED, 'latin_square': '(i+j)%3, VERS=[H,A,B]', 'scorers': {}}
os.makedirs(os.path.join(OUT, 'packets'), exist_ok=True)

for j in range(3):
    entries = []
    for i, r in enumerate(items):
        v = VERS[(i + j) % 3]
        entries.append({
            'qid': next(pool), 'is_anchor': False,
            'work': r['work'], 'seq': r['seq'], 'scene_no': r['scene_no'],
            'version': v, 'truth': '원작' if v == 'H' else '생성',
            'text': r[v],
        })
    for a in anchors:
        entries.append({
            'qid': next(pool), 'is_anchor': True, 'anchor_id': a['aid'],
            'anchor_kind': a['kind'], 'src': a['src'],
            'version': 'ANCHOR',
            'truth': '원작' if a['kind'] == 'HIGH' else '생성',
            'text': a['text'],
        })
    rng.shuffle(entries)

    sealed['scorers']['J%d' % j] = [
        {k: e[k] for k in e if k != 'text'} for e in entries
    ]

    lines = []
    lines.append('# CT-03 작법 필적 시험 — 채점자 J%d 문항지\n' % j)
    lines.append('문서 ID: LOS-CT-03-PACKET-J%d · 사전등록 LOS-CT-03-PREREG-V1.0\n' % j)
    lines.append('총 %d문항. 순서대로 채점한다. 문항 간 되돌아가 수정하지 않는다.\n' % len(entries))
    lines.append('각 문항마다 아래 두 가지를 모두 기록한다.\n')
    lines.append('1. **판별** — 이 씬은 사람이 쓴 방영 대본의 원작인가, 기계가 생성한 것인가. '
                 '`원작` / `생성` 둘 중 하나를 반드시 고른다(중립·유보 없음). '
                 '그리고 **그렇게 판단한 근거를 한 줄로** 적는다.\n')
    lines.append('2. **작법 품질** — 아래 5개 항목을 각각 0~5 정수로 매긴다.\n')
    lines.append('   - ① 대사의 인물별 개성 — 화자를 지우고 읽어도 누가 말했는지 구분되는가\n'
                 '   - ② 행동·소품의 구체성 — 그 장면에만 있는 물건·동작이 있는가\n'
                 '   - ③ 장면 목적의 달성 — 이 씬이 무엇을 하려 했고 그것을 해냈는가\n'
                 '   - ④ 상투성 부재 (**역채점**: 상투적일수록 낮게) \n'
                 '   - ⑤ 서브텍스트 — 말해지지 않은 것이 작동하는가\n')
    lines.append('\n표기 규격은 모든 문항에서 동일하게 맞춰져 있다. '
                 '헤딩은 `## 장소, 시간`, 대사는 `화자<탭>대사`, 블록 사이는 한 줄이다. '
                 '**표기 형식은 판단 근거가 되지 못한다.**\n')
    lines.append('\n---\n')
    for n, e in enumerate(entries, 1):
        lines.append('\n## 문항 %02d  [%s]\n' % (n, e['qid']))
        lines.append('```\n' + e['text'] + '\n```\n')
        lines.append('- 판별: ( 원작 / 생성 )\n- 판별 근거 한 줄:\n'
                     '- ①___ ②___ ③___ ④___ ⑤___\n')
        lines.append('\n---\n')
    open(os.path.join(OUT, 'packets', 'CT03_PACKET_J%d.md' % j), 'w',
         encoding='utf-8').write(''.join(lines))

json.dump(sealed, open(os.path.join(OUT, 'CT03_SEALED_MAP.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)

# 검증
h = hashlib.sha256(open(os.path.join(OUT, 'CT03_SEALED_MAP.json'), 'rb').read()).hexdigest()
cover = {}
for j in range(3):
    for e in sealed['scorers']['J%d' % j]:
        if e['is_anchor']:
            continue
        cover.setdefault((e['seq'], e['scene_no']), []).append(e['version'])
bad = {k: v for k, v in cover.items() if sorted(v) != ['A', 'B', 'H']}
print('씬수', len(cover), '커버리지 위반', len(bad))
print('패킷당 문항', [len(sealed['scorers']['J%d' % j]) for j in range(3)])
print('SEALED_MAP sha256', h[:16])
