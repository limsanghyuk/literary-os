#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cast Layer v3 / Tier 1 — advisory_bridge 전수 부트스트랩 (LLM 미사용, 결정론)

입력  : authored_chararc/<work>_NN.chararc.jsonl  (인물명 원천)
        original_extracted/<work>/*.txt           (표면형 출현 증거)
출력  : advisory_bridge/<work>.bridge.jsonl       (EntityBridgeRecord 정확 9키)

v2 대비 변경 — 표면형 증거 반영:
  대본은 작품마다 인물을 부르는 표기가 다르다. 비밀의숲 원문은 '황시목' 7회 대
  '시목' 313회, '한여진' 0회 대 '여진' 81회로 이름만 쓴다. v2 명부는 정식 성명만
  담고 있어 씬 배치 재현율이 14.7%까지 떨어졌다.
  → 정식명의 접미 변형 중 (a) 원문 출현 3회 이상이고 (b) 같은 작품 내 다른 인물과
    충돌하지 않는 것만 aliases에 편입한다. 충돌형은 정밀도를 파괴하므로 버린다
    (일괄 확장 시 돌아온일지매 정밀도 0.550→0.408 실측).
"""
import json, os, re, sys, glob, collections

ROOT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/work87/seqcard_ko/seqcard_ko"
OUT  = sys.argv[2] if len(sys.argv) > 2 else "/tmp/cl3/out/advisory_bridge"
MIN_OCC = 3

SPLIT = re.compile(r"[/()（）\[\]]")
WS = re.compile(r"\s+")
def norm(n):
    """괄호·슬래시 이후 절단 + 내부 공백 제거.
    공백을 남기면 '독고 철'과 '독고철'이 다른 인물로 갈라진다(쩐의전쟁 실측 grain 중복)."""
    return WS.sub("", SPLIT.split(str(n))[0]).strip()

def mergekey(n):
    """표기 변형 병합키 — 끝 2자. 이은찬/고은찬/은찬 → '은찬'."""
    n = norm(n)
    return n[-2:] if len(n) >= 2 else n

def variants(s):
    """성 제거 접미 변형 후보."""
    out = set()
    if len(s) >= 3: out.add(s[1:])
    if len(s) >= 4: out.add(s[2:])
    return {v for v in out if len(v) >= 2 and v != s}

def slug(s):
    return re.sub(r"\s+", "", str(s))

def work_of(fn):
    return os.path.basename(fn).rsplit("_", 1)[0]

def main():
    os.makedirs(OUT, exist_ok=True)
    # 1) CharacterArc에서 작품별 인물명 수집
    raw = collections.defaultdict(collections.Counter)
    for fp in sorted(glob.glob(os.path.join(ROOT, "authored_chararc", "*.chararc.jsonl"))):
        w = work_of(fp.replace(".chararc.jsonl", ""))
        for line in open(fp, encoding="utf-8"):
            line = line.strip()
            if not line: continue
            try: r = json.loads(line)
            except Exception: continue
            nm = r.get("character_name") or r.get("character") or r.get("name")
            if nm: raw[w][norm(nm)] += 1

    stat = dict(works=0, raw_names=0, records=0, merged=0, conflicts=0,
                alias_added=0, alias_rejected_ambiguous=0, alias_rejected_absent=0,
                works_without_text=0)

    for w, names in sorted(raw.items()):
        stat["works"] += 1
        stat["raw_names"] += len(names)
        # 2) 표기 변형 병합
        groups = collections.defaultdict(list)
        for n, c in names.items():
            groups[mergekey(n)].append((n, c))
        entries = []
        for mk, members in groups.items():
            members.sort(key=lambda x: (-x[1], -len(x[0])))
            canonical = members[0][0]
            aliases = sorted({m for m, _ in members[1:]})
            if len(members) > 1: stat["merged"] += 1
            firsts = {m[0][0] for m in members if m[0]}
            status = "CONFLICT" if len(firsts) > 1 else "PROVISIONAL"
            if status == "CONFLICT": stat["conflicts"] += 1
            entries.append([canonical, aliases, status])

        # 3) 원문 증거로 접미 변형 검증
        txts = sorted(glob.glob(os.path.join(ROOT, "original_extracted", w, "*.txt")))
        full = ""
        for t in txts:
            try: full += open(t, encoding="utf-8", errors="ignore").read()
            except Exception: pass
        if not full: stat["works_without_text"] += 1

        # 3a) 후보 수집 + 모호성 판정 (한 변형이 2인 이상에 걸리면 폐기)
        cand = collections.defaultdict(set)   # variant -> {canonical,...}
        for canonical, aliases, _ in entries:
            for base in [canonical] + list(aliases):
                for v in variants(base):
                    cand[v].add(canonical)
        for canonical, aliases, _ in entries:
            add = set()
            for base in [canonical] + list(aliases):
                for v in variants(base):
                    if len(cand[v]) > 1:
                        stat["alias_rejected_ambiguous"] += 1; continue
                    if full and full.count(v) < MIN_OCC:
                        stat["alias_rejected_absent"] += 1; continue
                    if not full:
                        stat["alias_rejected_absent"] += 1; continue
                    add.add(v)
            add -= {canonical} | set(aliases)
            if add:
                aliases.extend(sorted(add)); stat["alias_added"] += len(add)

        # 4) EntityBridgeRecord 정확 9키 기록
        path = os.path.join(OUT, f"{w}.bridge.jsonl")
        with open(path, "w", encoding="utf-8") as fh:
            for canonical, aliases, status in sorted(entries):
                rec = {
                    "work_id": w,
                    "character_key": f"{slug(w)}:{slug(canonical)}",
                    "canonical_name": canonical,
                    "aliases": sorted(set(aliases)),
                    "entity_id": None,
                    "mapping_status": status,
                    "source_registry_ref": None,
                    "source_registry_sha": None,
                    "by": "derived_bootstrap_v3",
                }
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
                stat["records"] += 1

    stat["conflict_rate"] = round(stat["conflicts"] / max(stat["records"], 1), 4)
    print(json.dumps(stat, ensure_ascii=False))

if __name__ == "__main__":
    main()
