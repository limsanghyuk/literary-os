#!/usr/bin/env python3
"""Cast Layer v3 — Tier1 결정론 인물명부 부트스트랩 (무LLM, 100% 재현)

CharacterArc(authored_chararc)에서 작품별 인물 명부를 생성한다.
산출 등급은 advisory_ — EXT6 계약 §1-3의 3구분 중 '가치증명 전 참고'.
authored_bridge(정독 저작 정본)를 덮어쓰지 않는다.

한계(산출물 헤더에 반드시 병기): 입력 CharacterArc 자체가 LLM 저작물이므로
본 명부는 '객관적 명부'가 아니라 '기존 저작 판단의 일관된 재정리'이다.
실측 포착률(파일럿 24회 대조): DOMINANT 100% / MAJOR 100% / MINOR 74% / CAMEO 24%.

Usage: python bootstrap_advisory_bridge.py <seqcard_ko_root> [out_dir]
"""
import os, re, sys, json, collections

SPLIT = re.compile(r"[/()]")

def norm(n: str) -> str:
    return SPLIT.split(n)[0].strip()

def mergekey(n: str) -> str:
    """표기 변형 병합키 — 끝 2자. 이은찬/고은찬/은찬 → '은찬'."""
    n = norm(n)
    return n[-2:] if len(n) >= 2 else n

def collect(root):
    freq = collections.defaultdict(collections.Counter)
    d = os.path.join(root, "authored_chararc")
    for f in sorted(os.listdir(d)):
        if not f.endswith(".jsonl"):
            continue
        work = f.rsplit("_", 1)[0]
        with open(os.path.join(d, f), encoding="utf-8") as fp:
            for line in fp:
                line = line.strip()
                if line:
                    freq[work][json.loads(line).get("character", "")] += 1
    return freq

def build(work, counter):
    groups = collections.defaultdict(list)
    for name in counter:
        groups[mergekey(name)].append(name)
    out = []
    for members in groups.values():
        members.sort(key=lambda n: (-counter[n], len(n)))
        canon = norm(members[0])
        aliases = sorted({a
                          for m in members
                          for a in [norm(m)] + [x.strip() for x in SPLIT.split(m) if x.strip()]
                          if a != canon})
        heads = {norm(m)[0] for m in members if norm(m)}
        status = "CONFLICT" if len(members) > 1 and len(heads) > 1 else "PROVISIONAL"
        out.append({"work_id": work,
                    "character_key": f"{work}:{canon}",
                    "canonical_name": canon,
                    "aliases": aliases,
                    "entity_id": None,
                    "mapping_status": status,
                    "source_registry_ref": None,
                    "source_registry_sha": None,
                    "by": "derived_bootstrap_v3"})
    return sorted(out, key=lambda r: r["canonical_name"])

def main():
    root = sys.argv[1]
    outdir = sys.argv[2] if len(sys.argv) > 2 else os.path.join(root, "advisory_bridge")
    os.makedirs(outdir, exist_ok=True)
    freq = collect(root)
    total = conflicts = aliased = raw = 0
    for work, counter in freq.items():
        raw += len(counter)
        recs = build(work, counter)
        total += len(recs)
        conflicts += sum(1 for r in recs if r["mapping_status"] == "CONFLICT")
        aliased += sum(1 for r in recs if r["aliases"])
        with open(os.path.join(outdir, f"{work}.bridge.jsonl"), "w", encoding="utf-8") as fp:
            for r in recs:
                fp.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(json.dumps({"works": len(freq), "raw_names": raw, "records": total,
                      "merged": raw - total, "aliased": aliased,
                      "conflicts": conflicts,
                      "conflict_rate": round(conflicts / total, 4) if total else 0.0},
                     ensure_ascii=False))

if __name__ == "__main__":
    main()
