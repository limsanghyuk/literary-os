#!/usr/bin/env python3
"""LocalEdge 자동 유도기 — 감사 처방(엣지층 유도기 초안+예외 교정) 구현.
실측(2026-08-03, 400회차 5,660건): 도착씬 core/core2로 97.6% 유도 가능, 예외 2.4%.
usage: python3 derive_local_edges.py <db_root> [work_ep ...]
  - 회차별로 derived local edges 생성 + authored와 대조해 예외(인간 판단 잔존) 리포트.
"""
import json, os, sys, glob


def derive_for_episode(db_root, ep):
    cards = {}
    with open(os.path.join(db_root, "authored", f"{ep}.seqcard.jsonl"), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            cards[r["scene_no"]] = r
    nos = sorted(cards)
    derived = []
    for a, b in zip(nos, nos[1:]):
        c = cards[b]
        derived.append(dict(work_id=ep, src_scene_no=a, tgt_scene_no=b,
                            label=c.get("core"), by="derive_local_edges_v1"))
    return derived


def compare(db_root, ep):
    path = os.path.join(db_root, "authored_edges", f"{ep}.local_edges.jsonl")
    if not os.path.exists(path):
        return None
    cards = {}
    with open(os.path.join(db_root, "authored", f"{ep}.seqcard.jsonl"), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            cards[r["scene_no"]] = r
    tot = exc = 0
    exceptions = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            tot += 1
            c = cards.get(r.get("tgt_scene_no"), {})
            if r.get("label") not in (c.get("core"), c.get("core2")):
                exc += 1
                exceptions.append(r)
    return dict(episode=ep, total=tot, exceptions=exc,
                exception_rate=round(exc / max(tot, 1), 4), rows=exceptions)


if __name__ == "__main__":
    root = sys.argv[1]
    eps = sys.argv[2:] or [os.path.basename(p).replace(".local_edges.jsonl", "")
                           for p in glob.glob(os.path.join(root, "authored_edges", "*.local_edges.jsonl"))]
    agg_t = agg_e = 0
    for ep in eps:
        r = compare(root, ep)
        if r:
            agg_t += r["total"]; agg_e += r["exceptions"]
    print(json.dumps(dict(episodes=len(eps), total_edges=agg_t, exceptions=agg_e,
                          exception_rate=round(agg_e / max(agg_t, 1), 4)), ensure_ascii=False))
