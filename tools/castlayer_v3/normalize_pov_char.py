#!/usr/bin/env python3
"""Cast Layer v3 — Tier3 pov_char 소급 정규화 진단기 (무LLM)

SequenceBlueprint.pov_char 를 v3 규약(list[str], EntityBridge.character_key 참조)으로
분해·조인하고, 결정론으로 고칠 수 없는 잔여를 격리 대상으로 보고한다.

v3 규약
  - 타입: list[str], 순서 = 시점 비중 내림차순
  - 값역: EntityBridge.character_key 만 허용
  - 시점 부재: [] (공란/null 금지)
  - 원소 4개 이상: WARN (시퀀스 분할 신호)

결정론으로 못 고치는 둘
  - 공란/null → 저작 필요
  - 복수 POV 무표기 작품 → 자동 변환은 '단일 POV'라는 거짓을 확정시킨다.
    pov_status=UNRELIABLE 로 격리하고 통계에서 제외한다.

Usage: python normalize_pov_char.py <seqcard_ko_root> [bridge_dir]
"""
import os, re, sys, json, collections

SEPS = re.compile(r"[·/,、+&]")

def split_pov(v):
    if v is None:
        return []
    if isinstance(v, list):
        return [str(x).strip() for x in v if str(x).strip()]
    return [p.strip() for p in SEPS.split(str(v)) if p.strip()]

def load_bridge(d):
    reg = collections.defaultdict(dict)   # work -> surface -> character_key
    if not d or not os.path.isdir(d):
        return reg
    for f in os.listdir(d):
        if not f.endswith(".bridge.jsonl"):
            continue
        for line in open(os.path.join(d, f), encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            w = r["work_id"]
            reg[w][r["canonical_name"]] = r["character_key"]
            for a in r.get("aliases") or []:
                reg[w].setdefault(a, r["character_key"])
    return reg

def main():
    root = sys.argv[1]
    bridge = load_bridge(sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "advisory_bridge"))
    seqdir = os.path.join(root, "authored_seq")

    tot = blank = multi = over3 = legacy = 0
    matched = unmatched = 0
    unmatched_names = collections.Counter()
    work_multi = collections.Counter()
    work_seq = collections.Counter()

    for f in sorted(os.listdir(seqdir)):
        if not f.endswith(".jsonl"):
            continue
        work = f.split(".")[0].rsplit("_", 1)[0]
        for line in open(os.path.join(seqdir, f), encoding="utf-8"):
            line = line.strip()
            if not line:
                continue
            r = json.loads(line)
            tot += 1
            work_seq[work] += 1
            v = r.get("pov_char")
            if isinstance(v, str):
                legacy += 1
            parts = split_pov(v)
            if not parts:
                blank += 1
                continue
            if len(parts) > 1:
                multi += 1
                work_multi[work] += 1
            if len(parts) >= 4:
                over3 += 1
            reg = bridge.get(work, {})
            for p in parts:
                if p in reg:
                    matched += 1
                else:
                    unmatched += 1
                    unmatched_names[f"{work}:{p}"] += 1

    unreliable = sorted(w for w in work_seq if work_multi[w] == 0)
    print(json.dumps({
        "sequences": tot,
        "legacy_str_type": legacy,
        "blank_or_null": blank,
        "multi_pov": multi,
        "multi_pov_rate": round(multi / tot, 4) if tot else 0.0,
        "over3_warn": over3,
        "bridge_join": {"matched": matched, "unmatched": unmatched,
                        "match_rate": round(matched / (matched + unmatched), 4) if matched + unmatched else None},
        "unreliable_works": {"count": len(unreliable), "of": len(work_seq), "works": unreliable},
        "top_unmatched": unmatched_names.most_common(15),
    }, ensure_ascii=False, indent=1))

if __name__ == "__main__":
    main()
