#!/usr/bin/env python3
"""작품 1편 완성 시 개발자 인계 번들 생성.

usage: make_work_delivery.py <work_id> <cast_dir> <authored_dir> <out_dir>

전 회차 .cast.jsonl 을 모아 <work>_cast_v1.zip 을 만든다.
번들 = 회차별 jsonl + MANIFEST.json + <work>_gate.txt
게이트 ERRORS 가 0 이 아니면 번들을 만들지 않고 종료 코드 2 로 실패한다.
"""
import sys, os, json, glob, hashlib, zipfile, subprocess, datetime

STANDARD = "LOS-STD-CAST-AUTHORING-V1"
BY = "claude-opus-direct-reading"


def sha256(p):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def main():
    if len(sys.argv) != 5:
        print(__doc__); return 1
    work, cast_dir, authored_dir, out_dir = sys.argv[1:5]
    files = sorted(glob.glob(os.path.join(cast_dir, f"{work}_*.cast.jsonl")))
    if not files:
        print(f"[FAIL] {work}: cast 파일 없음"); return 2

    gate = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gate_cast_authored.py")
    r = subprocess.run([sys.executable, gate, cast_dir, authored_dir],
                       capture_output=True, text=True)
    report = r.stdout + r.stderr
    errs = [l for l in report.splitlines() if l.startswith("ERROR") and work in l]
    warns = [l for l in report.splitlines() if l.startswith("WARN") and work in l]
    if errs:
        print(f"[FAIL] {work}: 게이트 ERRORS {len(errs)}건 — 번들 생성 중단")
        print("\n".join(errs[:20])); return 2

    entries, rows, scenes = [], 0, set()
    for p in files:
        n = 0
        with open(p, encoding="utf-8") as f:
            for line in f:
                if not line.strip():
                    continue
                n += 1
                d = json.loads(line)
                scenes.add((d["episode_no"], d["scene_no"]))
        rows += n
        entries.append({"name": os.path.basename(p), "rows": n, "sha256": sha256(p)})

    manifest = {
        "work_id": work,
        "episodes": len(files),
        "scenes": len(scenes),
        "rows": rows,
        "files": entries,
        "gate": {"errors": 0, "warns": len(warns)},
        "standard_doc_id": STANDARD,
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "by": BY,
    }

    os.makedirs(out_dir, exist_ok=True)
    zp = os.path.join(out_dir, f"{work}_cast_v1.zip")
    with zipfile.ZipFile(zp, "w", zipfile.ZIP_DEFLATED) as z:
        for p in files:
            z.write(p, os.path.basename(p))
        z.writestr("MANIFEST.json", json.dumps(manifest, ensure_ascii=False, indent=2))
        z.writestr(f"{work}_gate.txt", report)
    print(f"[OK] {zp}")
    print(f"     회차 {len(files)} / 씬 {len(scenes)} / 행 {rows} / WARN {len(warns)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
