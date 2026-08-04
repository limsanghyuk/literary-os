#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
G2CAST 보조측정 — 시퀀스 렌더의 화자 수 / 최다화자 점유 측정
2026-08-05. 원자료 = G1SEQ_run_20260804 (어제 시퀀스층 G1의 렌더 36본 + 원작 12본).
탐색적 측정이며 사전등록 대상이 아님. 판정에 사용하지 않는다.
"""
import os, re, sys, glob, json, collections, random, statistics as st

RUN = sys.argv[1] if len(sys.argv) > 1 else "."
NARR_END = re.compile(r'(한다|된다|있다|없다|이다|린다|온다|간다|든다|난다|본다|든지)$')

def speakers(path):
    raw = open(path, encoding='utf-8', errors='replace').read().splitlines()
    c = collections.Counter()
    for i, line in enumerate(raw):
        s = line.strip()
        if not s:
            continue
        # 1) 콜론형   이름: 대사
        m = re.match(r'^([^:：(（,，.·\-–—]{1,12}?)\s*[:：]\s*\S', s)
        if m:
            c[re.sub(r'\s+', '', m.group(1))] += 1
            continue
        # 2) 단독행형  이름 / 다음 줄에 대사
        if len(s) <= 10 and not re.search(r'[,.?!…"\'()·]', s) and i + 1 < len(raw) and raw[i+1].strip():
            nm = re.sub(r'\s+', '', s)
            if re.match(r'^[가-힣A-Za-z][가-힣A-Za-z0-9]{0,7}$', nm) and not NARR_END.search(nm):
                c[nm] += 1
                continue
        # 3) 공백1개 분리형  이름 대사   (건빵 원작 양식)
        m = re.match(r'^([가-힣][가-힣0-9]{1,4})\s+(\S.*)$', s)
        if m and not NARR_END.search(m.group(1)):
            c[m.group(1)] += 1
            continue
        # 4) 이름+괄호지시형  이름 (지시) 대사
        m = re.match(r'^([가-힣][가-힣0-9 ]{0,7}?)\s*\([^)]{1,40}\)\s*\S', s)
        if m:
            nm = re.sub(r'\s+', '', m.group(1))
            if nm and not NARR_END.search(nm):
                c[nm] += 1
    return c

def merged(path):
    """인물 표기 변형 병합 — 끝 2자 병합키 (2026-07-28 측정함정 규약).
    빈도 2회 미만은 파서 오검출로 보고 절사."""
    c = speakers(path)
    m = collections.Counter()
    for k, v in c.items():
        m[k[-2:] if len(k) > 2 else k] += v
    return collections.Counter({k: v for k, v in m.items() if v >= 2})

def stat(c):
    tot = sum(c.values())
    if tot == 0:
        return 0, 0.0
    return len(c), max(c.values()) / tot

def boot(d, n=20000, seed=20260805):
    random.seed(seed)
    ms = sorted(st.mean(random.choices(d, k=len(d))) for _ in range(n))
    return ms[int(.025 * n)], ms[int(.975 * n)]

rows = []
for op in sorted(glob.glob(os.path.join(RUN, "orig", "*.txt"))):
    seq = os.path.basename(op)[:-4]
    r = {"seq": seq}
    n, sh = stat(merged(op)); r["H"] = (n, sh)
    for cond in ("A", "B", "N"):
        p = os.path.join(RUN, "renders", f"{seq}__{cond}.txt")
        r[cond] = stat(merged(p)) if os.path.exists(p) else (None, None)
    rows.append(r)

print(f"{'시퀀스':<24} {'원작':>12} {'A(씬층)':>12} {'B(+시퀀스)':>12} {'N(불일치)':>12}")
for r in rows:
    def f(k):
        n, sh = r[k]
        return "-" if n is None else f"{n:2d}/{sh*100:4.0f}%"
    print(f"{r['seq']:<24} {f('H'):>12} {f('A'):>12} {f('B'):>12} {f('N'):>12}")

print()
summary = {}
for k in ("H", "A", "B", "N"):
    ns = [r[k][0] for r in rows if r[k][0]]
    ss = [r[k][1] for r in rows if r[k][0]]
    summary[k] = {"n_seq": len(ns), "speakers_mean": round(st.mean(ns), 2),
                  "top_share_mean": round(st.mean(ss), 4)}
    print(f"{k}: 화자수 평균 {st.mean(ns):.2f} · 최다화자 점유 평균 {st.mean(ss)*100:.1f}% (n={len(ns)})")

# 집중도 차 — 부호검정 + 부트스트랩
print()
for cond in ("A", "B", "N"):
    d = [r[cond][1] - r["H"][1] for r in rows if r[cond][0] and r["H"][0]]
    pos = sum(1 for x in d if x > 1e-9); neg = sum(1 for x in d if x < -1e-9)
    tie = len(d) - pos - neg
    lo, hi = boot(d)
    print(f"Δ집중도({cond}−원작) = {st.mean(d)*100:+.1f}%p  CI[{lo*100:+.1f}, {hi*100:+.1f}] "
          f"· 양수 {pos} 음수 {neg} 동점 {tie} (n={len(d)})")
    summary[cond]["delta_share_vs_H"] = round(st.mean(d), 4)
    summary[cond]["delta_ci"] = [round(lo, 4), round(hi, 4)]
    summary[cond]["sign"] = {"pos": pos, "neg": neg, "tie": tie}

json.dump({"rows": [{"seq": r["seq"], **{k: {"speakers": r[k][0], "top_share": r[k][1]}
                                          for k in ("H", "A", "B", "N")}} for r in rows],
           "summary": summary},
          open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "cast_concentration_result.json"), "w", encoding="utf-8"),
          ensure_ascii=False, indent=1)
print("\n결과 저장: cast_concentration_result.json")
