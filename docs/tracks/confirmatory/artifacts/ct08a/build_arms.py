# -*- coding: utf-8 -*-
"""CT-08A 5팔 렌더 입력 생성 — LOS-CT08A-BUILD-V2.0 (앵커 단위 = 시퀀스)
등화: B = 그 시퀀스 member 씬의 사람 씬카드 전부. T계열 = 그 시퀀스 후판 레코드 전부.
패딩 없음. I-cut = 삭제된 명제와 15자 연속 일치 문장 제거."""
import json, glob, os, re, collections, hashlib
BASE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.join(BASE, '..')
OUT = os.path.join(BASE, 'render_inputs'); os.makedirs(OUT, exist_ok=True)
for f in glob.glob(os.path.join(OUT, '*')): os.remove(f)

anchors = json.load(open(os.path.join(BASE, 'ANCHORS.json'), encoding='utf-8'))
thick = {}
for f in sorted(glob.glob(os.path.join(ROOT, 'db/seqcard_ko/reinforcement_v1/thick_sequence/가을동화/*.jsonl'))):
    for l in open(f, encoding='utf-8'):
        r = json.loads(l); thick[r['seq_id']] = r
cards = collections.defaultdict(dict)
for ep in range(1, 17):
    for l in open(os.path.join(ROOT, 'db/seqcard_ko/authored/가을동화_%02d.seqcard.jsonl' % ep), encoding='utf-8'):
        c = json.loads(l); cards[ep][c['scene_no']] = c

SPLIT = re.compile(r'(?<=다\.)\s*|(?<=[.!?])\s+')
def sents(t): return [s.strip() for s in SPLIT.split(t or '') if len(s.strip()) > 5]
def hit15(sent, removed):
    for p in removed:
        for i in range(max(len(p) - 14, 0)):
            if p[i:i + 15] in sent: return True
    return False

def render_thick(cast, event, info, pp, notes):
    L = ['## 인물']
    for c in cast: L.append('- %s (%s): %s' % (c['character'], c['participation'], c['desire_or_function']))
    L.append('\n## 사건\n' + (event or '(없음)'))
    L.append('\n## 정보 이동')
    for i in info: L.append('- %s [%s] 씬%s: "%s" → "%s"' % (i['subject'], i['mode'], i.get('scene_nos'), i['before'], i['after']))
    L.append('\n## 심기/거두기')
    for p in pp: L.append('- [%s] %s 씬%s: %s' % (p.get('kind',''), p.get('thread_id',''), p.get('scene_nos'), p.get('text') or p.get('summary','')))
    if notes:
        L.append('\n## 씬별 메모')
        for s in notes:
            L.append('- 씬%d' % s['scene_no'])
            for q in s['functional_propositions']: L.append('  · ' + q)
    return '\n'.join(L)

st = collections.Counter(); man = []
for k, a in enumerate(anchors):
    r = thick[a['seq_id']]
    removed = [q for s in r['scene_notes'] for q in s['functional_propositions']]
    # I-cut
    ncast = []
    for c in r['cast']:
        ss = sents(c['desire_or_function']); keep = [s for s in ss if not hit15(s, removed)]
        st['cast_t'] += len(ss); st['cast_c'] += len(ss) - len(keep)
        ncast.append(dict(c, desire_or_function=' '.join(keep) if keep else '(기술 없음)'))
    es = sents(r['event']); ekeep = [s for s in es if not hit15(s, removed)]
    st['ev_t'] += len(es); st['ev_c'] += len(es) - len(ekeep)
    tn = thick[anchors[(k + 7) % len(anchors)]['seq_id']]

    B = '\n\n'.join('## 씬 %d — %s\n헤딩: %s\n의도: %s\ncore: %s / %s\n표층: %s' % (
        n, cards[a['episode']][n].get('title',''), cards[a['episode']][n].get('heading',''),
        cards[a['episode']][n].get('intent_gist',''), cards[a['episode']][n].get('core',''),
        cards[a['episode']][n].get('core2',''), cards[a['episode']][n].get('skin',''))
        for n in a['scenes'] if n in cards[a['episode']])

    arms = {
      'B':   B,
      'T5':  render_thick(r['cast'], r['event'], r['info_shift'], r['plant_payoff'], r['scene_notes']),
      'T-F': render_thick(r['cast'], r['event'], r['info_shift'], r['plant_payoff'], []),
      'T-I': render_thick(ncast, ' '.join(ekeep), r['info_shift'], r['plant_payoff'], []),
      'TN':  render_thick(tn['cast'], tn['event'], tn['info_shift'], tn['plant_payoff'], tn['scene_notes']),
    }
    for arm, body in arms.items():
        fn = '%s_%s.input.md' % (a['anchor_id'], arm)
        open(os.path.join(OUT, fn), 'w', encoding='utf-8').write(body)
        man.append(dict(anchor_id=a['anchor_id'], seq_id=a['seq_id'], arm=arm, file=fn,
                        chars=len(body), sha256=hashlib.sha256(body.encode('utf-8')).hexdigest()))
json.dump(man, open(os.path.join(BASE, 'ARM_INPUTS.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('생성 %d본' % len(man))
print('I-cut 제거량: cast 문장 %d/%d (%.1f%%) · event 문장 %d/%d (%.1f%%)' % (
    st['cast_c'], st['cast_t'], 100*st['cast_c']/st['cast_t'], st['ev_c'], st['ev_t'], 100*st['ev_c']/st['ev_t']))
by = collections.defaultdict(list)
for m in man: by[m['arm']].append(m['chars'])
print('\n팔별 입력 길이(자) 평균/최소/최대')
for arm in ['B','T5','T-F','T-I','TN']:
    v = by[arm]; print('  %-4s %6.0f / %5d / %5d' % (arm, sum(v)/len(v), min(v), max(v)))
