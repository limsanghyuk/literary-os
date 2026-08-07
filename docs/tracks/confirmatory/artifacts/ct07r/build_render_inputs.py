# -*- coding: utf-8 -*-
"""CT-07R render-input materializer.
Implements LOS-CT07R-AMD-02 normalization. Run BEFORE any render exists.
"""
import json, hashlib, os, re, random, sys

HUB = "/tmp/hubclone/docs/tracks/confirmatory/ct07r_packets/CT07R_thick_correct_packets.jsonl"
DB  = "/sessions/compassionate-eager-lovelace/mnt/claude/db/seqcard_ko"
OUT = "/sessions/compassionate-eager-lovelace/mnt/claude/CT07R_run_20260807"

ANCHORS = [
    ("101번째프로포즈", 2, 28), ("101번째프로포즈", 5, 34), ("101번째프로포즈", 8, 39),
    ("101번째프로포즈", 11, 51), ("101번째프로포즈", 14, 42),
    ("38사기동대", 2, 39), ("38사기동대", 5, 67), ("38사기동대", 8, 88),
    ("38사기동대", 12, 61), ("38사기동대", 15, 56),
]
# target episode -> negative-control source episode (prereg §5, cyclic +1 within work)
TN_MAP = {
    ("101번째프로포즈", 2): 5, ("101번째프로포즈", 5): 8, ("101번째프로포즈", 8): 11,
    ("101번째프로포즈", 11): 14, ("101번째프로포즈", 14): 2,
    ("38사기동대", 2): 5, ("38사기동대", 5): 8, ("38사기동대", 8): 12,
    ("38사기동대", 12): 15, ("38사기동대", 15): 2,
}
PART_ORDER = ["PRIMARY", "OPPOSITION", "SECONDARY", "SUPPORT", "WITNESS", "OFFSCREEN_CAUSAL"]

NEUTRAL_PREAMBLE = (
    "아래는 이 작품의 한 시퀀스에 대한 설계 기록이다. "
    "이 기록이 지금 작성할 씬에 대응하는지는 보장되지 않는다. "
    "대응한다고 판단되는 내용만 사용하라."
)

packets = {}
for line in open(HUB, encoding="utf-8"):
    d = json.loads(line)
    packets[(d["work_id"], d["episode_no"])] = d


def scenecard(work, ep, scene_no):
    p = f"{DB}/authored/{work}_{ep:02d}.seqcard.jsonl"
    for line in open(p, encoding="utf-8"):
        d = json.loads(line)
        if d.get("scene_no") == scene_no:
            return d
    raise KeyError((work, ep, scene_no))


def labelize(pkt, target_idx):
    """Return a dict view with absolute scene numbers replaced by S-n labels."""
    members = pkt["member_scene_nos"]
    m = {sn: f"S-{i+1}" for i, sn in enumerate(members)}
    def lab(nos):
        return [m.get(n, "S-?") for n in (nos or [])]
    return {
        "n_members": len(members),
        "target_label": f"S-{target_idx}",
        "event": pkt["event"],
        "cast": [dict(character=c["character"], role=c["desire_or_function"],
                      participation=c["participation"]) for c in pkt.get("cast", [])],
        "info_shift": [dict(subject=i["subject"], before=i["before"], after=i["after"],
                            mode=i["mode"], labels=lab(i.get("scene_nos")))
                       for i in pkt.get("info_shift", [])],
        "plant_payoff": [dict(kind=p["kind"], thread=p["thread_id"], statement=p["statement"],
                              labels=lab(p.get("scene_nos")))
                         for p in pkt.get("plant_payoff", [])],
        "scene_notes": [dict(label=m.get(n["scene_no"], "S-?"),
                             ord=members.index(n["scene_no"]) + 1 if n["scene_no"] in members else 999,
                             props=n["functional_propositions"])
                        for n in pkt.get("scene_notes", [])],
    }


def truncate_pair(a, b):
    """AMD-02 §4.3 pairwise-minimum truncation. a/b are labelized views."""
    for v in (a, b):
        ti = int(v["target_label"].split("-")[1])
        v["_ti"] = ti
    # scene_notes: keep target, then nearest by ordinal distance
    k = min(len(a["scene_notes"]), len(b["scene_notes"]))
    for v in (a, b):
        notes = sorted(v["scene_notes"], key=lambda n: (0 if n["ord"] == v["_ti"] else 1,
                                                        abs(n["ord"] - v["_ti"])))
        v["scene_notes"] = sorted(notes[:k], key=lambda n: n["ord"])
    # cast
    k = min(len(a["cast"]), len(b["cast"]))
    for v in (a, b):
        v["cast"] = sorted(v["cast"], key=lambda c: PART_ORDER.index(c["participation"])
                           if c["participation"] in PART_ORDER else 99)[:k]
    # info_shift / plant_payoff: target-label-bearing first, then original order
    for f in ("info_shift", "plant_payoff"):
        k = min(len(a[f]), len(b[f]))
        for v in (a, b):
            items = list(enumerate(v[f]))
            items.sort(key=lambda t: (0 if v["target_label"] in t[1]["labels"] else 1, t[0]))
            v[f] = [t[1] for t in items[:k]]
    for v in (a, b):
        v.pop("_ti")
    return a, b


ID_IN_TEXT = re.compile(r"EP\s*\d+\s*(화|회)?")


def scrub(s):
    """AMD-02 §4.2 — 자유 서술문 안에 남은 절대 회차 식별자를 기계적으로 중화한다.
    양팔에 동일 규칙으로 적용한다."""
    return ID_IN_TEXT.sub("다른 회차", s)


def render_design(v):
    L = []
    L.append(f"[시퀀스 구성] 이 시퀀스는 {v['n_members']}개의 씬으로 이루어진다. "
             f"작성 대상은 그중 {v['target_label']} 이다.")
    L.append("")
    L.append("[시퀀스 사건]")
    L.append(scrub(v["event"]))
    L.append("")
    L.append("[등장 인물과 기능]")
    for c in v["cast"]:
        L.append(scrub(f"- {c['character']} ({c['participation']}): {c['role']}"))
    L.append("")
    L.append("[정보 이동]")
    if v["info_shift"]:
        for i in v["info_shift"]:
            L.append(f"- {i['subject']} / {i['mode']} / {', '.join(i['labels'])}")
            L.append(scrub(f"  이전: {i['before']}"))
            L.append(scrub(f"  이후: {i['after']}"))
    else:
        L.append("- (없음)")
    L.append("")
    L.append("[심기와 회수]")
    if v["plant_payoff"]:
        for p in v["plant_payoff"]:
            L.append(f"- {p['kind']} / {p['thread']} / {', '.join(p['labels'])}")
            L.append(scrub(f"  {p['statement']}"))
    else:
        L.append("- (없음)")
    L.append("")
    L.append("[씬별 기능 명제]")
    for n in v["scene_notes"]:
        L.append(f"- {n['label']}:")
        for pr in n["props"]:
            L.append(scrub(f"  · {pr}"))
    return "\n".join(L)


TASK_TMPL = """# 씬 집필 과제

작품: {work}
회차: {ep}화
대상 씬 번호: {sn}
씬 표제: {heading}

## 지시

위 씬 하나를 한국 드라마 대본 형식으로 집필하라. 지문과 대사를 모두 포함하되,
씬 하나 분량(대략 20~60행)을 넘기지 마라. 앞뒤 씬을 쓰지 말고 이 씬만 쓴다.
해설·요약·메모를 덧붙이지 말고 대본 본문만 출력하라.
{ctx}"""


def build():
    rows = []
    for work, ep, sn in ANCHORS:
        card = scenecard(work, ep, sn)
        tpk = packets[(work, ep)]
        npk = packets[(work, TN_MAP[(work, ep)])]
        ti = tpk["member_scene_nos"].index(sn) + 1
        nlen = len(npk["member_scene_nos"])
        ni = ti if ti <= nlen else max(1, round(ti * nlen / len(tpk["member_scene_nos"])))
        tv = labelize(tpk, ti)
        nv = labelize(npk, ni)
        tv, nv = truncate_pair(tv, nv)

        base = dict(work=work, ep=ep, sn=sn, heading=card["heading"])
        arms = {}
        arms["A"] = TASK_TMPL.format(ctx="", **base)
        bctx = ("\n## 참고 설계 (씬카드)\n\n"
                f"제목: {card['title']}\n"
                f"의도: {card['intent_gist']}\n"
                f"핵심 기능: {card['core']} / {card.get('core2','-')}\n"
                f"배경: {card.get('skin','-')}\n")
        arms["B"] = TASK_TMPL.format(ctx=bctx, **base)
        for armname, view in (("T", tv), ("TN", nv)):
            ctx = ("\n## 참고 설계\n\n" + NEUTRAL_PREAMBLE + "\n\n" + render_design(view) + "\n")
            arms[armname] = TASK_TMPL.format(ctx=ctx, **base)
        for a, txt in arms.items():
            rows.append(dict(work=work, ep=ep, scene_no=sn, arm=a, prompt=txt))
    return rows


def main():
    rows = build()
    d = f"{OUT}/render_inputs"
    os.makedirs(d, exist_ok=True)
    rng = random.Random(20260807)
    order = list(range(len(rows)))
    rng.shuffle(order)
    blind, checks = [], []
    for i, idx in enumerate(order):
        r = rows[idx]
        rid = f"R{i+1:02d}"
        open(f"{d}/{rid}.prompt.md", "w", encoding="utf-8").write(r["prompt"])
        blind.append(dict(render_id=rid, work=r["work"], episode=r["ep"],
                          scene_no=r["scene_no"], arm=r["arm"]))
    json.dump(blind, open(f"{OUT}/BLIND_MAP.json", "w", encoding="utf-8"),
              ensure_ascii=False, indent=1)

    # AMD-02 §5 verification
    by = {(r["work"], r["ep"], r["arm"]): r["prompt"] for r in rows}
    print("=== AMD-02 §5.1 T/TN 문자수 대칭 ===")
    for work, ep, sn in ANCHORS:
        t, n = len(by[(work, ep, "T")]), len(by[(work, ep, "TN")])
        dv = abs(t - n) / max(t, n)
        flag = "OK " if dv <= 0.15 else "OVER"
        print(f"{flag} {work}_{ep:02d} T={t} TN={n} diff={dv*100:.1f}%")
        checks.append((f"{work}_{ep:02d}", t, n, round(dv * 100, 1)))
    print("\n=== AMD-02 §5.2 잔존 식별자 스캔 ===")
    pat = re.compile(r"EP\d|_\d{2}_S\d{2}|시퀀스\s*\d|episode_no|seq_id")
    hits = 0
    for r in rows:
        if r["arm"] in ("T", "TN"):
            body = r["prompt"].split("## 참고 설계", 1)[1]
            for m in pat.finditer(body):
                hits += 1
                print("  HIT", r["work"], r["ep"], r["arm"], repr(m.group(0)))
    print(f"  잔존 식별자 {hits}건")

    h = hashlib.sha256()
    for i in range(len(rows)):
        h.update(open(f"{d}/R{i+1:02d}.prompt.md", "rb").read())
    sha = h.hexdigest()
    open(f"{d}/PROMPT_SET_SHA256.txt", "w", encoding="utf-8").write(
        f"CT-07R render prompt set (40 files, R01..R40)\nsha256(concat)={sha}\n")
    bm = hashlib.sha256(open(f"{OUT}/BLIND_MAP.json", "rb").read()).hexdigest()
    print(f"\nPROMPT_SET sha256 = {sha}")
    print(f"BLIND_MAP  sha256 = {bm}")


if __name__ == "__main__":
    main()
