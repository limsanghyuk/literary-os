#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
measure_subplot_ratio.py  (no-GPU, deterministic)
Test claim: supporting characters (protagonist affiliation groups:
workplace/family) carry >=~40% of each episode as parallel subplots.

Speaker extraction: corpus has no speaker field. Screenplay convention puts
the BARE character name as a line-leading speaker tag, followed by space/paren
or end-of-line. We take leading Korean tokens of 2-4 chars in that shape,
keep those with freq>=MIN and not in a narration stoplist. Frequency ranking
surfaces real names (name+josa narration variants fall below threshold).
main = top-K by line count; supporting = remainder.
"""
import json, os, re, sys, statistics
from collections import Counter, defaultdict

CORPUS = "/sessions/upbeat-focused-bohr/mnt/claude/db/corpus_ko"
SCENES = os.path.join(CORPUS, "scenes")
OUT    = "/sessions/upbeat-focused-bohr/mnt/outputs/subplot_ratio_results.json"

MIN_SPEAKER_HITS = 5
MAIN_K           = 4

STOP = set("""그 그때 그런 그러나 그리고 그래서 다시 다음 이때 이윽고 잠시 곧 문득 한편 순간
또 또한 결국 마침 어느 모든 두 세 네 한 저 이 그저 막 늘 자꾸 점점 그녀 그는 그들
이미 아직 벌써 방금 이내 동시 일동 모두 사람 사람들 두사람 세사람 화면 카메라 인서트 자막 시간 장면
밤 낮 아침 저녁 새벽 오후 오전 햇살 바람 거리 골목 표정 미소 웃음 눈물 목소리 소리 침묵 정적
하고 하며 하다 하던 그제 이제 저제 여자 남자 모두들 여기 저기 거기""".split())

NAME_RE = re.compile(r'^([가-힣]{2,4})(?=[\s(]|$)')

def lead_token(line):
    line = line.strip()
    if not line: return None
    m = NAME_RE.match(line)
    return m.group(1) if m else None

def group_works():
    src = json.load(open(os.path.join(CORPUS, "sources.json")))
    filmset = {s['id'] for s in src if s.get('media') == 'film'}
    works = defaultdict(list)
    for f in os.listdir(SCENES):
        if not f.endswith('.jsonl'): continue
        n = f[:-6]
        m = re.match(r'^(.*?)[_]?(\d{1,3})$', n)
        if m and m.group(1): works[m.group(1)].append((int(m.group(2)), f))
        else: works[n].append((-1, f))
    out = []
    for base, eps in works.items():
        eps.sort()
        is_film = (len(eps) == 1) and (base in filmset)
        kind = 'film' if is_film else ('drama' if len(eps) > 1 else 'single')
        out.append((base, kind, eps))
    return out

JOSA = set("이 가 은 는 을 를 와 과 도 의 에 야 아 께 한 만 랑")
def normalize_hits(hits):
    """Merge name+josa tokens into their bare-name prefix when the prefix is
    itself a frequent leader (collapses 영달/영달이/영달과 -> 영달)."""
    freq = hits
    remap = {}
    for t in list(hits):
        if len(t) >= 3 and t[-1] in JOSA:
            base = t[:-1]
            if freq.get(base, 0) >= MIN_SPEAKER_HITS:
                remap[t] = base
    if not remap:
        return hits
    merged = Counter()
    for t, c in hits.items():
        merged[remap.get(t, t)] += c
    return merged

def speakers_for_work(eps):
    hits = Counter()
    for _, f in eps:
        for line in open(os.path.join(SCENES, f)):
            for ln in json.loads(line).get('text','').split('\n')[1:]:
                t = lead_token(ln)
                if t: hits[t]+=1
    hits = normalize_hits(hits)
    return {t:c for t,c in hits.items() if c>=MIN_SPEAKER_HITS and t not in STOP}

def measure_work(base, kind, eps):
    sp = speakers_for_work(eps)
    if len(sp) < 3: return None
    ranked = sorted(sp, key=lambda t:-sp[t])
    mk4=set(ranked[:MAIN_K]); mk2=set(ranked[:2])
    per_ep=[]
    for epnum,f in eps:
        dlg=s4=s2=ssc=pss4=0
        for line in open(os.path.join(SCENES,f)):
            sm4=ss=sm2=0
            for ln in json.loads(line).get('text','').split('\n')[1:]:
                t=lead_token(ln)
                if t and len(t)>=3 and t[-1] in JOSA and t[:-1] in sp: t=t[:-1]
                if not t or t not in sp: continue
                dlg+=1
                if t in mk4: sm4+=1
                else: s4+=1; ss+=1
                if t in mk2: sm2+=1
                else: s2+=1
            if sm4+ss>0:
                ssc+=1
                if ss>0 and sm4==0: pss4+=1
        if dlg<20: continue
        per_ep.append({"ep":epnum,"dlg_total":dlg,
            "sub_share_k4":round(s4/dlg,4),"sub_share_k2":round(s2/dlg,4),
            "pure_sub_scene_share_k4":round(pss4/ssc,4) if ssc else 0})
    if not per_ep: return None
    mean=lambda k:round(statistics.mean(e[k] for e in per_ep),4)
    return {"work":base,"kind":kind,"n_episodes_measured":len(per_ep),
        "n_speakers":len(sp),"main_cast_k4":ranked[:MAIN_K],
        "supporting_count":len(sp)-MAIN_K,
        "mean_sub_share_k4":mean("sub_share_k4"),
        "mean_sub_share_k2":mean("sub_share_k2"),
        "mean_pure_sub_scene_share_k4":mean("pure_sub_scene_share_k4"),
        "per_ep":per_ep}

def main():
    results=[]
    for base,kind,eps in group_works():
        if kind=='single': continue
        try: r=measure_work(base,kind,eps)
        except Exception: r=None
        if r: results.append(r)
    json.dump(results,open(OUT,"w"),ensure_ascii=False,indent=1)
    def summ(kind):
        rs=[r for r in results if r['kind']==kind]
        if not rs: print(f"\n{kind}: none"); return
        s4=[r['mean_sub_share_k4'] for r in rs]; s2=[r['mean_sub_share_k2'] for r in rs]
        ps=[r['mean_pure_sub_scene_share_k4'] for r in rs]
        ge40=sum(1 for x in s4 if x>=0.40); ge40_2=sum(1 for x in s2 if x>=0.40)
        print(f"\n=== {kind.upper()}  (N={len(rs)}) ===")
        print(f"  supporting dialogue share, main=top4: mean={statistics.mean(s4):.3f} median={statistics.median(s4):.3f} min={min(s4):.3f} max={max(s4):.3f}")
        print(f"  supporting dialogue share, main=top2: mean={statistics.mean(s2):.3f} median={statistics.median(s2):.3f}")
        print(f"  pure-subplot scene share (no top4):   mean={statistics.mean(ps):.3f} median={statistics.median(ps):.3f}")
        print(f"  works >=40% (top4): {ge40}/{len(rs)}={ge40/len(rs)*100:.0f}%   >=40% (top2): {ge40_2}/{len(rs)}={ge40_2/len(rs)*100:.0f}%")
    print("\n"+"="*70); summ('drama'); summ('film')
    print("\n=== OVERALL ===")
    print(f"  works measured: {len(results)}  (drama={sum(1 for r in results if r['kind']=='drama')}, film={sum(1 for r in results if r['kind']=='film')})")
    print(f"  JSON -> {OUT}")

if __name__=="__main__": main()
