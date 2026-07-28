# -*- coding: utf-8 -*-
"""authored_cast 게이트 — CastPresenceRecord 10키 검증.
사용: python3 gate_cast_authored.py <authored_cast_dir> <authored_dir>
  authored_dir 는 SceneCard(*.seqcard.jsonl) 디렉터리. scene_no 참조 무결성 검사에 쓴다.

게이트 코드
  CAST-1 키셋 정확히 10키
  CAST-2 grain 중복 (work,ep,scene,character_key 유일)
  CAST-3 enum 위반
  CAST-4 evidence_ref 공백/누락
  CAST-5 scene_no 가 SceneCard 원장에 없음 (참조 무결성)
  CAST-W1 (WARN) 편 전체에서 focality=PRIMARY 인 인물이 0명
  CAST-W2 (WARN) 인물 없는 씬 비율 10% 초과
"""
import sys, os, json, glob, collections

KEYS = {"work_id","episode_no","scene_no","character_key","entity_id",
        "presence_mode","focality","speaking_status","evidence_ref","by"}
PM = {"ONSCREEN","VOICE_ONLY","PHONE_OR_REMOTE","ARCHIVAL_OR_MEMORY","REFERENCED_ONLY"}
FO = {"PRIMARY","SECONDARY","PRESENT_ONLY"}
SS = {"SPEAKING","NONSPEAKING"}


def scene_index(authored_dir):
    idx = {}
    for f in glob.glob(os.path.join(authored_dir, "*.seqcard.jsonl")):
        b = os.path.basename(f)[: -len(".seqcard.jsonl")]
        w, ep = b.rsplit("_", 1)
        idx[(w, int(ep))] = {json.loads(l)["scene_no"] for l in open(f, encoding="utf-8")}
    return idx


def main(cast_dir, authored_dir):
    idx = scene_index(authored_dir)
    err = collections.Counter(); warn = collections.Counter()
    detail = []; nrow = 0; nfile = 0
    for f in sorted(glob.glob(os.path.join(cast_dir, "*.cast.jsonl"))):
        nfile += 1
        b = os.path.basename(f)[: -len(".cast.jsonl")]
        w, ep = b.rsplit("_", 1); ep = int(ep)
        rows = [json.loads(l) for l in open(f, encoding="utf-8")]
        nrow += len(rows)
        seen = set(); prim = 0; scenes_with = set()
        for r in rows:
            if set(r) != KEYS:
                err["CAST-1"] += 1; detail.append(f"CAST-1 {b} {sorted(set(r)^KEYS)}")
            g = (r.get("work_id"), r.get("episode_no"), r.get("scene_no"), r.get("character_key"))
            if g in seen:
                err["CAST-2"] += 1; detail.append(f"CAST-2 {b} {g}")
            seen.add(g)
            if r.get("presence_mode") not in PM or r.get("focality") not in FO \
               or r.get("speaking_status") not in SS:
                err["CAST-3"] += 1; detail.append(f"CAST-3 {b} s{r.get('scene_no')} {r.get('character_key')}")
            if not str(r.get("evidence_ref", "")).strip():
                err["CAST-4"] += 1; detail.append(f"CAST-4 {b} s{r.get('scene_no')} {r.get('character_key')}")
            if (w, ep) in idx and r.get("scene_no") not in idx[(w, ep)]:
                err["CAST-5"] += 1; detail.append(f"CAST-5 {b} scene {r.get('scene_no')} 원장에 없음")
            if r.get("focality") == "PRIMARY": prim += 1
            scenes_with.add(r.get("scene_no"))
        if prim == 0:
            warn["CAST-W1"] += 1; detail.append(f"CAST-W1 {b} PRIMARY 0")
        if (w, ep) in idx:
            tot = len(idx[(w, ep)])
            empty = tot - len(scenes_with & idx[(w, ep)])
            if tot and empty / tot > 0.10:
                warn["CAST-W2"] += 1
                detail.append(f"CAST-W2 {b} 인물없는씬 {empty}/{tot} = {empty/tot:.1%}")
    out = {"files": nfile, "rows": nrow, "ERRORS": dict(err), "WARNS": dict(warn),
           "ERRORS_TOTAL": sum(err.values()), "WARNS_TOTAL": sum(warn.values())}
    print(json.dumps(out, ensure_ascii=False, indent=1))
    for d in detail[:80]:
        print(" ", d)
    return 1 if out["ERRORS_TOTAL"] else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
