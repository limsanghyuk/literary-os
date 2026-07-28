#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cast Layer v3 / Tier 3 — pov_char 규약 정규화 전수 (LLM 미사용, 결정론)

원장 SequenceBlueprint 18키는 손대지 않는다. 사이드카로만 산출한다.
출력: advisory_pov/<work>_NN.pov.jsonl
  {work_id, work_id_series, seq_id, pov_char_legacy, pov_char, resolved, unresolved_surface, flags}

규약 v3:
  pov_char : str -> list[str]
  값 도메인: EntityBridge.character_key
  POV 없음 = []   (누락/공란은 [] + POV-0 플래그)
  4인 이상 = WARN (POV-3)  — 시퀀스 시점이 그만큼 분산되면 시퀀스 분할이 의심된다
  LEGACY_POV : 표면형을 명부에 붙이지 못한 경우 원문자열 보존 + WARN
"""
import json, os, re, sys, glob, collections

ROOT   = sys.argv[1] if len(sys.argv) > 1 else "/tmp/work87/seqcard_ko/seqcard_ko"
BRIDGE = sys.argv[2] if len(sys.argv) > 2 else "/tmp/cl3/out/advisory_bridge"
OUT    = sys.argv[3] if len(sys.argv) > 3 else "/tmp/cl3/out/advisory_pov"

SEPS = re.compile(r"[·/,、+&]|\s+및\s+|\s+와\s+|\s+과\s+")
WS   = re.compile(r"\s+")

def split_pov(v):
    if v is None: return []
    if isinstance(v, list): return [WS.sub("", str(x)) for x in v if str(x).strip()]
    return [WS.sub("", p) for p in SEPS.split(str(v)) if p.strip()]

def series_of(work_ep):
    return work_ep.rsplit("_", 1)[0]

def load_surface(bdir):
    """work -> surface(공백제거) -> character_key. 긴 표면형 우선."""
    m = collections.defaultdict(dict)
    for fp in glob.glob(os.path.join(bdir, "*.bridge.jsonl")):
        for l in open(fp, encoding="utf-8"):
            r = json.loads(l)
            for s in [r["canonical_name"]] + list(r.get("aliases") or []):
                s = WS.sub("", str(s))
                if len(s) >= 2: m[r["work_id"]][s] = r["character_key"]
    return m

# 인물명이 아닌 POV 표기 — 앙상블/총칭. 명부 조인 대상이 아니므로 별도 분류한다.
NON_PERSON = {"전체","앙상블","다수","군중","주인공","동료","없음","해당없음","N/A","다인물","전인물"}

def resolve(surface_map, token):
    if token in surface_map: return surface_map[token]
    # 부분 포함 역조회 — '검사황시목' 같은 직함 결합 표기 구제
    hits = [k for s, k in surface_map.items() if s in token]
    return hits[0] if len(hits) == 1 else None

def main():
    os.makedirs(OUT, exist_ok=True)
    SM = load_surface(BRIDGE)
    st = collections.Counter()
    per_work = collections.defaultdict(lambda: collections.Counter())
    for fp in sorted(glob.glob(os.path.join(ROOT, "authored_seq", "*.seqblueprint.jsonl"))):
        ep = os.path.basename(fp).replace(".seqblueprint.jsonl", "")
        ser = series_of(ep)
        sm = SM.get(ser, {})
        out = []
        for l in open(fp, encoding="utf-8"):
            l = l.strip()
            if not l: continue
            r = json.loads(l); st["sequences"] += 1
            legacy = r.get("pov_char")
            if not isinstance(legacy, list): st["legacy_str"] += 1
            toks = split_pov(legacy)
            keys, unres, flags = [], [], []
            if not toks:
                flags.append("POV-0"); st["blank"] += 1
            for t in toks:
                k = resolve(sm, t)
                if k:
                    if k not in keys: keys.append(k)
                elif t in NON_PERSON:
                    flags.append("POV-ENSEMBLE"); st["ensemble"] += 1
                else:
                    unres.append(t); flags.append("LEGACY_POV")
            if len(toks) > 1: st["multi_pov"] += 1
            if len(keys) >= 4: flags.append("POV-3"); st["over3_warn"] += 1
            st["tokens"] += len(toks); st["resolved_tokens"] += len(toks) - len(unres)
            st["unresolved_tokens"] += len(unres)
            per_work[ser]["tok"] += len(toks); per_work[ser]["res"] += len(toks) - len(unres)
            out.append({
                "work_id": ep, "work_id_series": ser, "seq_id": r.get("seq_id"),
                "pov_char_legacy": legacy, "pov_char": keys,
                "resolved": len(unres) == 0 and bool(keys),
                "unresolved_surface": unres, "flags": sorted(set(flags)),
            })
        with open(os.path.join(OUT, f"{ep}.pov.jsonl"), "w", encoding="utf-8") as fh:
            for o in out: fh.write(json.dumps(o, ensure_ascii=False) + "\n")

    st["match_rate"] = round(st["resolved_tokens"] / max(st["tokens"], 1), 4)
    unreliable = sorted(w for w, c in per_work.items() if c["tok"] and c["res"] / c["tok"] < 0.5)
    res = dict(st); res["works"] = len(per_work); res["unreliable_works"] = unreliable
    res["unreliable_n"] = len(unreliable)
    print(json.dumps(res, ensure_ascii=False))

if __name__ == "__main__":
    main()
