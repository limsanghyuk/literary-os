#!/usr/bin/env python3
"""R74 fully-fresh primary materialization and freeze harness R1.

Scope:
- verify DB64 frozen bytes;
- verify historical exclusion custody;
- enumerate DB64 consumer_ready_r53 episode inputs;
- apply canonical R74 exclusions;
- deterministically freeze 24 fully fresh episodes;
- write a sealed ledger and selected-input bundle.

This program does NOT run Control or Treatment and generates no literary prose.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import tempfile
import zipfile
from collections import Counter
from pathlib import Path
from typing import Any, Iterable

PREREG_SHA256 = "8ae36a1a2c56b147bb76181b6b9f9a16e979977c3ec6d34fd74c0be7e61cf0dd"
DB64_PART01_SHA256 = "b033ebf5c00c844634a8180812382d68657d59fd98643d45e8470314ca5994e3"
DB64_PART02_SHA256 = "a618f48503afb5b5465f49264259302e4e3c90434ede6ea4c99be700cd4f1785"
DB64_LOGICAL_SHA256 = "4703e9a99da2deb66eef08f09b08141db6c4d19bc76f77d1c8159dcb7633d6e7"
R72_R5_LEDGER_SHA256 = "d4398a3568f55258fb664f782f5542431795ab471f944a5df168c5501478a364"

R71_EXCLUDED_WORKS = {
    "라이벌", "오마이레이디", "대장금", "미생", "스타일", "스카이캐슬",
    "뉴하트", "공주가돌아왔다", "시그널", "구해줘", "그들이사는세상", "공주의남자",
}
SOURCE_HOLD_WORKS = {"W", "개인의취향", "베토벤바이러스", "최강칠우"}

PLANNER_RE = re.compile(r"^(?P<work>.+)_(?P<ep>\d+)\.planner_input\.json$")


class FreezeError(RuntimeError):
    pass


def sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(obj: Any) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256_json(obj: Any) -> str:
    return hashlib.sha256(canonical_json_bytes(obj)).hexdigest()


def normalize_member(name: str) -> str:
    return name.replace("\\", "/").lstrip("/")


def reconstruct_db64(args: argparse.Namespace, workdir: Path) -> Path:
    if args.db64_zip:
        logical = Path(args.db64_zip)
        if not logical.is_file():
            raise FreezeError(f"DB64 logical ZIP not found: {logical}")
        if sha256_file(logical) != DB64_LOGICAL_SHA256:
            raise FreezeError("DB64 logical SHA256 mismatch")
        return logical

    if not (args.part01 and args.part02):
        raise FreezeError("Provide --db64-zip OR both --part01 and --part02")

    p1, p2 = Path(args.part01), Path(args.part02)
    if sha256_file(p1) != DB64_PART01_SHA256:
        raise FreezeError("DB64 part01 SHA256 mismatch")
    if sha256_file(p2) != DB64_PART02_SHA256:
        raise FreezeError("DB64 part02 SHA256 mismatch")

    logical = workdir / "DB64_R127_LOGICAL.zip"
    with logical.open("wb") as out:
        for src in (p1, p2):
            with src.open("rb") as f:
                shutil.copyfileobj(f, out, length=1024 * 1024)
    if sha256_file(logical) != DB64_LOGICAL_SHA256:
        raise FreezeError("Reconstructed logical DB64 SHA256 mismatch")
    return logical


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_r72_exclusion_manifest(obj: dict[str, Any], strict: bool = True) -> set[str]:
    if obj.get("schema") != "R74_R72_EXCLUSION_CUSTODY_MANIFEST_R1":
        raise FreezeError("Unexpected R72 exclusion manifest schema")
    revs = obj.get("revisions")
    if not isinstance(revs, dict):
        raise FreezeError("R72 exclusion manifest missing revisions")

    excluded: set[str] = set()
    for rev in ("R2", "R3", "R4", "R5"):
        item = revs.get(rev)
        if not isinstance(item, dict):
            raise FreezeError(f"R72 exclusion custody missing {rev}")
        status = item.get("status")
        evidence_hash = str(item.get("evidence_sha256") or "")
        if strict and not re.fullmatch(r"[0-9a-f]{64}", evidence_hash):
            raise FreezeError(f"{rev} evidence SHA256 missing/invalid")

        if status == "PRIMARY_CASES":
            ids = item.get("case_ids")
            if not isinstance(ids, list) or not ids:
                raise FreezeError(f"{rev} PRIMARY_CASES without case_ids")
            excluded.update(str(x) for x in ids)
            if strict and rev == "R5" and evidence_hash != R72_R5_LEDGER_SHA256:
                raise FreezeError("R72 R5 ledger SHA256 does not match frozen authority")
        elif status == "NO_PRIMARY_CASES":
            # Allowed only when accompanied by a durable evidence receipt.
            continue
        else:
            raise FreezeError(f"{rev} status must be PRIMARY_CASES or NO_PRIMARY_CASES")
    return excluded


def collect_thread_refs(value: Any) -> set[str]:
    refs: set[str] = set()
    if isinstance(value, dict):
        for v in value.values():
            refs.update(collect_thread_refs(v))
    elif isinstance(value, list):
        for v in value:
            refs.update(collect_thread_refs(v))
    elif isinstance(value, str) and value.replace("\\", "/").endswith(".thread_state.json"):
        refs.add(normalize_member(value))
    return refs


def suffix_lookup(names: Iterable[str], suffix: str) -> str | None:
    suffix = normalize_member(suffix)
    hits = [n for n in names if normalize_member(n).endswith(suffix)]
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        raise FreezeError(f"Ambiguous archive suffix {suffix}: {len(hits)} matches")
    return None


def enumerate_candidates(zf: zipfile.ZipFile) -> list[dict[str, Any]]:
    names = [normalize_member(n) for n in zf.namelist()]
    name_set = set(names)
    planner_members = [
        n for n in names
        if "consumer_ready_r53" in n
        and "/seqcard_ko/reinforcement_v1/planner_input/" in ("/" + n)
        and n.endswith(".planner_input.json")
    ]
    if not planner_members:
        raise FreezeError("No consumer_ready_r53 planner_input members found in DB64")

    rows: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    for planner in sorted(planner_members):
        parts = planner.split("/")
        try:
            idx = parts.index("planner_input")
        except ValueError:
            continue
        if idx + 2 >= len(parts):
            continue
        work_dir = parts[idx + 1]
        filename = parts[-1]
        m = PLANNER_RE.match(filename)
        if not m:
            continue
        work = work_dir
        ep = int(m.group("ep"))
        case_id = f"{work}__EP{ep:02d}"
        if case_id in seen_ids:
            raise FreezeError(f"Duplicate case ID in DB64: {case_id}")
        seen_ids.add(case_id)

        stem = f"{work}_{ep:02d}"
        thick_suffix = f"seqcard_ko/reinforcement_v1/thick_sequence/{work}/{stem}.thick_sequence.jsonl"
        arc_suffix = f"seqcard_ko/authored_arc/{stem}.episodearc.json"
        thick = suffix_lookup(names, thick_suffix)
        arc = suffix_lookup(names, arc_suffix)
        if not thick or not arc:
            raise FreezeError(f"Required planner/thick/arc artifact missing for {case_id}")

        try:
            planner_obj = json.loads(zf.read(planner).decode("utf-8"))
        except Exception as e:
            raise FreezeError(f"Planner JSON unreadable for {case_id}: {e}") from e

        thread_refs = sorted(collect_thread_refs(planner_obj))
        resolved_threads: list[str] = []
        for ref in thread_refs:
            exact = ref if ref in name_set else suffix_lookup(names, ref)
            if not exact:
                raise FreezeError(f"Referenced thread_state missing for {case_id}: {ref}")
            resolved_threads.append(exact)

        rows.append({
            "case_id": case_id,
            "work": work,
            "episode_no": ep,
            "planner_member": planner,
            "thick_member": thick,
            "arc_member": arc,
            "thread_state_members": resolved_threads,
        })
    if not rows:
        raise FreezeError("No valid DB64 candidate episodes enumerated")
    return rows


def deterministic_select(
    candidates: list[dict[str, Any]],
    exclusions: set[str],
    r73_exclusions: set[str],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    eligible = []
    rejection_counts = Counter()

    for row in candidates:
        cid, work = row["case_id"], row["work"]
        if work in R71_EXCLUDED_WORKS:
            rejection_counts["R71_WORK"] += 1
            continue
        if work in SOURCE_HOLD_WORKS:
            rejection_counts["SOURCE_HOLD"] += 1
            continue
        if cid in exclusions:
            rejection_counts["R72_CASE"] += 1
            continue
        if cid in r73_exclusions:
            rejection_counts["R73_STAGE_A_CASE"] += 1
            continue
        rank = hashlib.sha256(f"{PREREG_SHA256}|{cid}".encode("utf-8")).hexdigest()
        x = dict(row)
        x["selection_rank_sha256"] = rank
        eligible.append(x)

    eligible.sort(key=lambda x: (x["selection_rank_sha256"], x["case_id"]))
    selected: list[dict[str, Any]] = []
    per_work = Counter()
    for row in eligible:
        if per_work[row["work"]] >= 2:
            continue
        selected.append(row)
        per_work[row["work"]] += 1
        if len(selected) == 24:
            break

    if len(selected) != 24:
        raise FreezeError(f"Only {len(selected)} fully fresh cases selectable; require 24")
    if len({x["work"] for x in selected}) < 12:
        raise FreezeError("Selected cohort has fewer than 12 distinct works")
    if max(per_work.values(), default=0) > 2:
        raise FreezeError("Per-work cap violated")

    diagnostics = {
        "candidate_count": len(candidates),
        "eligible_count": len(eligible),
        "selected_count": len(selected),
        "selected_distinct_works": len({x["work"] for x in selected}),
        "rejection_counts": dict(sorted(rejection_counts.items())),
    }
    return selected, diagnostics


def write_selected_bundle(
    zf: zipfile.ZipFile,
    selected: list[dict[str, Any]],
    ledger: dict[str, Any],
    r72_manifest: dict[str, Any],
    r73_manifest: dict[str, Any],
    out_path: Path,
) -> None:
    members: set[str] = set()
    for row in selected:
        members.add(row["planner_member"])
        members.add(row["thick_member"])
        members.add(row["arc_member"])
        members.update(row["thread_state_members"])

    with zipfile.ZipFile(out_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as out:
        out.writestr("R74_FROZEN_24_CASE_LEDGER.json", json.dumps(ledger, ensure_ascii=False, indent=2, sort_keys=True))
        out.writestr("R74_R72_EXCLUSION_CUSTODY_MANIFEST.json", json.dumps(r72_manifest, ensure_ascii=False, indent=2, sort_keys=True))
        out.writestr("R74_R73_STAGE_A_EXCLUSION_MANIFEST.json", json.dumps(r73_manifest, ensure_ascii=False, indent=2, sort_keys=True))
        for member in sorted(members):
            out.writestr("db64_selected/" + normalize_member(member), zf.read(member))


def run_production(args: argparse.Namespace) -> int:
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    r72_manifest = load_json(Path(args.r72_exclusion_manifest))
    r73_manifest = load_json(Path(args.r73_exclusion_manifest))

    r72_exclusions = validate_r72_exclusion_manifest(r72_manifest, strict=True)
    r73_ids = r73_manifest.get("case_ids")
    if r73_manifest.get("schema") != "R74_R73_STAGE_A_EXCLUSION_MANIFEST_R1" or not isinstance(r73_ids, list) or len(r73_ids) != 41:
        raise FreezeError("R73 Stage-A exclusion manifest invalid; require exact 41-case manifest")
    r73_exclusions = {str(x) for x in r73_ids}

    with tempfile.TemporaryDirectory(prefix="r74freeze_") as td:
        logical = reconstruct_db64(args, Path(td))
        logical_sha = sha256_file(logical)
        with zipfile.ZipFile(logical, "r") as zf:
            bad = zf.testzip()
            if bad is not None:
                raise FreezeError(f"DB64 ZIP CRC failure at {bad}")
            candidates = enumerate_candidates(zf)
            selected, diagnostics = deterministic_select(candidates, r72_exclusions, r73_exclusions)

            ledger = {
                "schema": "R74_FULLY_FRESH_24_CASE_FROZEN_LEDGER_R1",
                "date": "2026-09-22",
                "preregistration_sha256": PREREG_SHA256,
                "db64_logical_sha256": logical_sha,
                "r72_exclusion_manifest_sha256": sha256_file(Path(args.r72_exclusion_manifest)),
                "r73_exclusion_manifest_sha256": sha256_file(Path(args.r73_exclusion_manifest)),
                "selection_rule": "SHA256(preregistration_sha256|case_id), ascending; max 2/work; first 24; >=12 works",
                "treatment_outputs_at_freeze": 0,
                "control_outputs_at_freeze": 0,
                "diagnostics": diagnostics,
                "selected": selected,
            }
            ledger_path = out_dir / "R74_FULLY_FRESH_24_CASE_FROZEN_LEDGER_R1.json"
            ledger_path.write_bytes(canonical_json_bytes(ledger))
            ledger_sha = sha256_file(ledger_path)

            bundle_path = out_dir / "R74_FULLY_FRESH_24_CASE_INPUT_BUNDLE_R1.zip"
            write_selected_bundle(zf, selected, ledger, r72_manifest, r73_manifest, bundle_path)
            bundle_sha = sha256_file(bundle_path)

        receipt = {
            "schema": "R74_PRIMARY_FREEZE_RECEIPT_R1",
            "status": "FROZEN_BEFORE_ANY_CONTROL_OR_TREATMENT_OUTPUT",
            "ledger_sha256": ledger_sha,
            "input_bundle_sha256": bundle_sha,
            "db64_logical_sha256": logical_sha,
            "selected_count": 24,
            "distinct_work_count": len({x["work"] for x in selected}),
            "control_outputs": 0,
            "treatment_outputs": 0,
        }
        (out_dir / "R74_PRIMARY_FREEZE_RECEIPT_R1.json").write_bytes(canonical_json_bytes(receipt))
        print(json.dumps(receipt, ensure_ascii=False, indent=2))
    return 0


def selftest() -> int:
    with tempfile.TemporaryDirectory(prefix="r74selftest_") as td:
        td = Path(td)
        fixture = td / "fixture.zip"
        with zipfile.ZipFile(fixture, "w", compression=zipfile.ZIP_DEFLATED) as z:
            for w in range(1, 17):
                work = f"테스트작{w:02d}"
                for ep in range(1, 4):
                    stem = f"{work}_{ep:02d}"
                    base = f"x/consumer_ready_r53/{work}/seqcard_ko"
                    z.writestr(f"{base}/reinforcement_v1/planner_input/{work}/{stem}.planner_input.json", "{}")
                    z.writestr(f"{base}/reinforcement_v1/thick_sequence/{work}/{stem}.thick_sequence.jsonl", "{}\n")
                    z.writestr(f"{base}/authored_arc/{stem}.episodearc.json", "{}")

        with zipfile.ZipFile(fixture, "r") as zf:
            rows = enumerate_candidates(zf)
        selected, diag = deterministic_select(rows, set(), set())
        assert len(selected) == 24
        assert len({x["work"] for x in selected}) >= 12
        assert max(Counter(x["work"] for x in selected).values()) <= 2

        good = {
            "schema": "R74_R72_EXCLUSION_CUSTODY_MANIFEST_R1",
            "revisions": {
                "R2": {"status": "NO_PRIMARY_CASES", "evidence_sha256": "1" * 64},
                "R3": {"status": "NO_PRIMARY_CASES", "evidence_sha256": "2" * 64},
                "R4": {"status": "NO_PRIMARY_CASES", "evidence_sha256": "3" * 64},
                "R5": {"status": "PRIMARY_CASES", "evidence_sha256": R72_R5_LEDGER_SHA256, "case_ids": ["가상__EP01"]},
            },
        }
        assert "가상__EP01" in validate_r72_exclusion_manifest(good, strict=True)
        bad = json.loads(json.dumps(good))
        del bad["revisions"]["R4"]
        try:
            validate_r72_exclusion_manifest(bad, strict=True)
            raise AssertionError("fail-closed test did not fail")
        except FreezeError:
            pass

        result = {
            "status": "PASS",
            "fixture_candidates": len(rows),
            "selected": len(selected),
            "distinct_works": len({x["work"] for x in selected}),
            "fail_closed_missing_R4": True,
            "literary_prose_generation_bytes": 0,
            "diagnostics": diag,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--selftest", action="store_true")
    p.add_argument("--db64-zip")
    p.add_argument("--part01")
    p.add_argument("--part02")
    p.add_argument("--r72-exclusion-manifest")
    p.add_argument("--r73-exclusion-manifest")
    p.add_argument("--out-dir", default="r74_primary_freeze")
    args = p.parse_args()

    if args.selftest:
        return selftest()
    if not args.r72_exclusion_manifest or not args.r73_exclusion_manifest:
        raise FreezeError("--r72-exclusion-manifest and --r73-exclusion-manifest are required")
    return run_production(args)


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FreezeError as e:
        print(json.dumps({"status": "HOLD", "reason": str(e)}, ensure_ascii=False, indent=2))
        raise SystemExit(4)
