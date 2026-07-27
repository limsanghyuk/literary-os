#!/usr/bin/env python3
# E1 — 정렬기 골드셋 캘리브레이션 (DR-2 / AM-4)
# 결정론·LLM-free. 골드셋 = corpus_ko/brief2prose 479쌍 (scene_no가 정답).
# Mode S(블라인드 의미 정렬): 브리프(소제목/설명/인물)만으로 에피소드 씬 중 정답 씬을 찾는다.
# confidence = (top1 유사도, top1-top2 마진). 임계는 본 실측의 P-R로 사전등록.
import json, re, sys, glob, os
from collections import Counter

HEAD_RE = re.compile(r'^[ \t]*[sS]?#\s*(\d+)[\.\s\)]', re.M)

def split_scenes(txt):
    """원문 에피소드 → [(scene_num, start, end, body)] 헤딩 기반 결정론 분할"""
    ms = list(HEAD_RE.finditer(txt))
    scenes = []
    for i, m in enumerate(ms):
        start = m.start()
        end = ms[i+1].start() if i+1 < len(ms) else len(txt)
        scenes.append((int(m.group(1)), start, end, txt[start:end]))
    return scenes

def norm(s):
    return re.sub(r'\s+', '', s)

def bigrams(s):
    s = norm(s)
    return Counter(s[i:i+2] for i in range(len(s)-1))

def sim(a_bg, b_bg):
    inter = sum((a_bg & b_bg).values())
    denom = min(sum(a_bg.values()), sum(b_bg.values())) or 1
    return inter / denom

def parse_brief(prompt):
    f = {}
    for k in ['소제목','설명','극적기능','인물']:
        m = re.search(rf'\[{k}\]\s*([^\[]*)', prompt)
        f[k] = m.group(1).strip() if m else ''
    return f

def align_episode(gold_pairs, txt):
    scenes = split_scenes(txt)
    sc_bg = [(num, bigrams(body)) for num, s, e, body in scenes]
    results = []
    for p in gold_pairs:
        brief = parse_brief(p['prompt'])
        q = brief['소제목'] + ' ' + brief['설명']
        chars = [c.strip() for c in brief['인물'].split(',') if c.strip()]
        q_bg = bigrams(q)
        scored = []
        for num, bg in sc_bg:
            s = sim(q_bg, bg)
            body = next(b for n,st,en,b in scenes if n == num)
            nb = norm(body)
            cboost = sum(0.05 for c in chars if norm(c) and norm(c) in nb)
            scored.append((s + min(cboost, 0.15), num))
        scored.sort(reverse=True)
        top1_s, top1_n = scored[0]
        top2_s = scored[1][0] if len(scored) > 1 else 0.0
        results.append(dict(gold=p['scene_no'], pred=top1_n,
                            conf=round(top1_s,4), margin=round(top1_s-top2_s,4),
                            hit=top1_n == p['scene_no']))
    return results, len(scenes)

def main(gold_dir, txt_dir, out_json):
    all_r, per_work = [], {}
    for gp in sorted(glob.glob(os.path.join(gold_dir, '*.jsonl'))):
        wid = os.path.basename(gp)[:-6]
        tp = os.path.join(txt_dir, wid + '.txt')
        if not os.path.exists(tp): continue
        pairs = [json.loads(l) for l in open(gp, encoding='utf-8')]
        txt = open(tp, encoding='utf-8', errors='ignore').read()
        res, n_scenes = align_episode(pairs, txt)
        hits = sum(r['hit'] for r in res)
        per_work[wid] = dict(pairs=len(pairs), parsed_scenes=n_scenes,
                             top1_acc=round(hits/len(pairs),4))
        all_r += res
    acc = sum(r['hit'] for r in all_r) / len(all_r)
    # 임계 스윕: conf 임계별 (커버리지, 정밀도)
    sweep = []
    for th in [0.1,0.15,0.2,0.25,0.3,0.35,0.4,0.5]:
        kept = [r for r in all_r if r['conf'] >= th]
        if not kept: continue
        sweep.append(dict(th=th, coverage=round(len(kept)/len(all_r),3),
                          precision=round(sum(r['hit'] for r in kept)/len(kept),4)))
    out = dict(schema='E1_ALIGN_CALIBRATION_V1', n=len(all_r),
               top1_acc=round(acc,4), per_work=per_work, threshold_sweep=sweep,
               method='deterministic char-bigram overlap + character-name boost, LLM-free')
    json.dump(out, open(out_json,'w',encoding='utf-8'), ensure_ascii=False, indent=1)
    print(json.dumps(out, ensure_ascii=False, indent=1)[:1500])

CARD_NUM = re.compile(r'^[sS]?#?\s*(\d+)')  # 카드 heading 표기 변형("S#15"/"#15") 흡수 — E1 실측 교정

def align_cards_hybrid(cards, txt, headsim_th=0.5):
    """실전 1차 모드: SceneCard heading 번호+텍스트 검증. E1b 실측 426/426=100%.
    반환: (aligned[(scene_no, src_scene_num, headsim)], fallback_queue[cards])"""
    ms = list(HEAD_RE.finditer(txt))
    scenes = {int(m.group(1)): txt[m.start():txt.find('\n', m.start())] for m in ms}
    aligned, fallback = [], []
    for c in cards:
        m = CARD_NUM.match(c.get('heading', ''))
        n = int(m.group(1)) if m else None
        if n in scenes:
            hs = sim(bigrams(c['heading']), bigrams(scenes[n]))
            if hs >= headsim_th:
                aligned.append((c['scene_no'], n, round(hs, 3)))
                continue
        fallback.append(c)  # 의미 폴백(conf>=0.5 자동/미만 수동큐) 대상
    return aligned, fallback

if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2], sys.argv[3])
