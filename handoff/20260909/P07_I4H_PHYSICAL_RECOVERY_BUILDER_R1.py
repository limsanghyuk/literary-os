#!/usr/bin/env python3
"""P07-I4H physical recovery builder R1.

Purpose
-------
Build a NEW developer-deliverable 5-Part / 9-Package P07-I4H physical
recovery authority from the exact developer-held Sync R6 parents plus durable
Hub I4H evidence.

This program is fail-closed. It never treats historical metadata as a
substitute for current byte verification. It will not build if any parent
outer SHA/size/ZIP integrity check fails, if parent C2 identity fails, if the
five frozen I4D runtime files differ, or if the new R2 / deterministic
parent-targeted / full nonhistorical regression gates fail.

It does NOT reproduce historical Sync R8 byte-for-byte. The output is new
Recovery R2 evidence and receives a fresh physical audit.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter
from typing import Dict, Iterable, List, Tuple

DATE = "20260909"
AUTHORITY = "CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_RECOVERY_R2"
PARENT_AUTHORITY = "LITERARY_OS_SYNC_R6_I4H_VIRTUAL_PRETEST_20260908"
PARENT_ENGINE = "CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1"
PRODUCTION = "ENG:R47"
FORMAL_COUNT = 137
LATEST_FORMAL = "R138"
R140 = [0, 0, 0]
DB59_SHA = "a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9"
PARENT_AUDIT_SHA = "94e808f6fa7c760662d0d02d1625046d23a9198afcc28bd3ab18c15453b37360"

PARENTS: Dict[str, dict] = {
    "CONTROL": {
        "filename": "LITERARY_OS_CURRENT_CONTROL_P07_I4H_VIRTUAL_PRETEST_SYNC_R6_20260908.zip",
        "bytes": 108635838,
        "sha256": "c291e9a3866de66fae625ab899139a13f1e98468a3bff0d58a11fd34553f0aa6",
        "entries": 1256,
        "zip": True,
    },
    "A": {
        "filename": "LITERARY_OS_CURRENT_PART_A_P07_I4H_VIRTUAL_PRETEST_SYNC_R6_20260908.zip",
        "bytes": 123051563,
        "sha256": "25eb489d07e78a3a3288e1e5029114ce791ada2ab43a8564ae9f9eed738306dd",
        "entries": 1332,
        "zip": True,
    },
    "B1": {
        "filename": "LITERARY_OS_CURRENT_PART_B1_UNCHANGED_R1_20260908.zip",
        "bytes": 196427036,
        "sha256": "00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98",
        "entries": 56,
        "zip": True,
    },
    "B2": {
        "filename": "LITERARY_OS_CURRENT_PART_B2_P07_I4H_VIRTUAL_PRETEST_SYNC_R6_20260908.zip",
        "bytes": 255155288,
        "sha256": "40de0853fd8e1e8318658d64a4e8d26cb8e88711842639aa45b87c0e4d062c02",
        "entries": 1277,
        "zip": True,
    },
    "C1": {
        "filename": "LITERARY_OS_CURRENT_C1_RUNTIME_CORE_UNCHANGED_R1_20260908.zip",
        "bytes": 140020974,
        "sha256": "dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518",
        "entries": 60,
        "zip": True,
    },
    "C2-A": {
        "filename": "LITERARY_OS_CURRENT_C2_BINARY_A_P07_PHASE0_R3_I4H_VIRTUAL_SYNC_R6_20260908.bin",
        "bytes": 159175515,
        "sha256": "b775bf65cba23ad5611b3383678765f88c1a444d25c4b49f7ccfb5a9d2438ec9",
        "zip": False,
    },
    "C2-B": {
        "filename": "LITERARY_OS_CURRENT_C2_BINARY_B_P07_PHASE0_R3_I4H_VIRTUAL_SYNC_R6_20260908.bin",
        "bytes": 159175514,
        "sha256": "be4af1ac97467e1f090c8cd0854e14df1ffef6699ed23b0a80014f55e197e860",
        "zip": False,
    },
    "D1": {
        "filename": "LITERARY_OS_CURRENT_PART_D1_DB59_UNCHANGED_R1_20260908.zip",
        "bytes": 138011573,
        "sha256": "a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504",
        "entries": 25,
        "zip": True,
    },
    "D2": {
        "filename": "LITERARY_OS_CURRENT_PART_D2_DB59_UNCHANGED_R1_20260908.zip",
        "bytes": 173393886,
        "sha256": "c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4",
        "entries": 59,
        "zip": True,
    },
}

PARENT_C2 = {
    "bytes": 318351029,
    "sha256": "9878aac8532e9f1eb6b16ef4c84bcfe6be90b58a49ecf0f6afaabe993fad3be7",
    "entries": 3765,
}

FROZEN_I4D = {
    "literary_os_runtime/surface_realization_mode.py": "06244a1a0c4876975067036784761f0620675fdbb347f6b40536bdd41db61cd9",
    "literary_os_runtime/semantic_render_bridge.py": "342ba94f8503995079b9ddabc55b709ea38c7721112d6a396d643a8aad8985eb",
    "literary_os_runtime/provider_backed_renderer.py": "e04befcd3b26bb4091d77dc35374e78ea30a84efa2af2fe47d8c565849c6b208",
    "literary_os_runtime/semantic_episode_render_wiring.py": "f3ff441dc1221ca2a39cd9e1fb1239cdd26186156f5a53d1b599e79ed0188d99",
    "literary_os_runtime/literary_surface_contract.py": "79fa25b8aed55cf64eeecc2591c59ab1be199bddc9f6a2209a3ede57857a1ce5",
}

TARGETED_NEEDLES = [
    "surface_realization_mode",
    "semantic_render_bridge",
    "provider_backed_renderer",
    "semantic_episode_render_wiring",
    "literary_surface_contract",
    "render_scene_provider_backed",
    "materialize_renderer_input_from_semantic_scene",
    "SurfaceRealizationModeR1",
]

HUB_RUNTIME = {
    "literary_os_runtime/i4h_intervention_policy.py":
        "handoff/20260909/P07_I4H_RUNTIME_PROMOTION_DELTA_R1/literary_os_runtime/i4h_intervention_policy.py",
    "literary_os_runtime/i4h_runtime_renderer.py":
        "handoff/20260909/P07_I4H_RUNTIME_PROMOTION_DELTA_R1/literary_os_runtime/i4h_runtime_renderer.py",
    "literary_os_runtime/i4h_episode_render_wiring.py":
        "handoff/20260909/P07_I4H_RUNTIME_PROMOTION_DELTA_R1/literary_os_runtime/i4h_episode_render_wiring.py",
}
HUB_RUNTIME_SHA = {
    "literary_os_runtime/i4h_intervention_policy.py": "cb643e1cee8e47dfafafb87db1f335abc7203d25ac016b774678f2266cd94684",
    "literary_os_runtime/i4h_runtime_renderer.py": "94f766c23c45a22fc8655a56f89908cf38db384af9c8046042b474a1085a76ed",
    "literary_os_runtime/i4h_episode_render_wiring.py": "7f2f1b50ec9239ca5ca364b3863f28418aba2baf248fea31ca9178a7be33b741",
}
R2_TEST_SRC = "handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2/tests/test_p07_i4h_recovery_qualification_r2.py"
R2_TEST_DST = "tests/test_p07_i4h_recovery_qualification_r2.py"
R2_PREREG = "handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_PREREG_R2_20260909.json"
R2_AMENDMENT = "handoff/20260909/P07_I4H_RECOVERY_QUALIFICATION_R2_PREREG_AMENDMENT_R1_TARGETED_TEST_DEFINITION_20260909.json"

OUTPUT_NAMES = {
    "CONTROL": f"LITERARY_OS_CURRENT_CONTROL_P07_I4H_RECOVERY_R2_{DATE}.zip",
    "A": f"LITERARY_OS_CURRENT_PART_A_P07_I4H_RECOVERY_R2_{DATE}.zip",
    "B1": f"LITERARY_OS_CURRENT_PART_B1_UNCHANGED_R1_{DATE}.zip",
    "B2": f"LITERARY_OS_CURRENT_PART_B2_P07_I4H_RECOVERY_R2_{DATE}.zip",
    "C1": f"LITERARY_OS_CURRENT_C1_RUNTIME_CORE_UNCHANGED_R1_{DATE}.zip",
    "C2-A": f"LITERARY_OS_CURRENT_C2_BINARY_A_P07_I4H_RECOVERY_R2_{DATE}.bin",
    "C2-B": f"LITERARY_OS_CURRENT_C2_BINARY_B_P07_I4H_RECOVERY_R2_{DATE}.bin",
    "D1": f"LITERARY_OS_CURRENT_PART_D1_DB59_UNCHANGED_R1_{DATE}.zip",
    "D2": f"LITERARY_OS_CURRENT_PART_D2_DB59_UNCHANGED_R1_{DATE}.zip",
}

FIXED_ZIP_DT = (2026, 9, 9, 0, 0, 0)


def die(msg: str) -> None:
    raise SystemExit(f"HOLD_FAIL_CLOSED: {msg}")


def sha256_file(path: Path, chunk: int = 8 * 1024 * 1024) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def canonical_json_bytes(obj: object) -> bytes:
    return json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def is_unsafe_zip_name(name: str) -> bool:
    p = PurePosixPath(name.replace("\\", "/"))
    return p.is_absolute() or ".." in p.parts or (p.parts and ":" in p.parts[0])


def audit_zip(path: Path, expected_entries: int | None = None) -> dict:
    try:
        with zipfile.ZipFile(path, "r") as zf:
            names = zf.namelist()
            counts = Counter(names)
            dup = sorted([n for n, c in counts.items() if c > 1])
            unsafe = sorted([n for n in names if is_unsafe_zip_name(n)])
            bad = zf.testzip()
    except Exception as e:
        return {"pass": False, "error": repr(e)}
    ok = not dup and not unsafe and bad is None
    if expected_entries is not None:
        ok = ok and len(names) == expected_entries
    return {
        "pass": ok,
        "entries": len(names),
        "expected_entries": expected_entries,
        "duplicate_paths": dup,
        "unsafe_paths": unsafe,
        "crc_bad_member": bad,
    }


def verify_parent_files(parent_dir: Path) -> dict:
    out = {}
    for logical, spec in PARENTS.items():
        p = parent_dir / spec["filename"]
        if not p.is_file():
            die(f"missing parent {logical}: {p}")
        size = p.stat().st_size
        digest = sha256_file(p)
        rec = {
            "path": str(p),
            "bytes": size,
            "expected_bytes": spec["bytes"],
            "sha256": digest,
            "expected_sha256": spec["sha256"],
            "byte_identity": size == spec["bytes"] and digest == spec["sha256"],
        }
        if spec.get("zip"):
            rec["zip_audit"] = audit_zip(p, spec.get("entries"))
        rec["pass"] = rec["byte_identity"] and (not spec.get("zip") or rec["zip_audit"]["pass"])
        out[logical] = rec
        if not rec["pass"]:
            die(f"parent verification failed for {logical}: {rec}")
    return out


def concat_files(a: Path, b: Path, dst: Path) -> None:
    with dst.open("wb") as w:
        for src in (a, b):
            with src.open("rb") as r:
                shutil.copyfileobj(r, w, length=8 * 1024 * 1024)


def verify_parent_c2(parent_dir: Path, work: Path) -> Tuple[Path, dict]:
    dst = work / "PARENT_SYNC_R6_C2.zip"
    concat_files(parent_dir / PARENTS["C2-A"]["filename"], parent_dir / PARENTS["C2-B"]["filename"], dst)
    rec = {
        "bytes": dst.stat().st_size,
        "sha256": sha256_file(dst),
        "zip_audit": audit_zip(dst, PARENT_C2["entries"]),
    }
    rec["pass"] = (
        rec["bytes"] == PARENT_C2["bytes"]
        and rec["sha256"] == PARENT_C2["sha256"]
        and rec["zip_audit"]["pass"]
    )
    if not rec["pass"]:
        die(f"parent C2 reassembly failed: {rec}")
    return dst, rec


def safe_extract_zip(src: Path, dst: Path) -> None:
    a = audit_zip(src)
    if not a.get("pass"):
        die(f"refuse to extract unsafe/bad ZIP: {src}: {a}")
    with zipfile.ZipFile(src, "r") as zf:
        zf.extractall(dst)


def verify_hub_inputs(hub_root: Path) -> dict:
    rec = {}
    for dst_rel, src_rel in HUB_RUNTIME.items():
        p = hub_root / src_rel
        if not p.is_file():
            die(f"missing Hub runtime source: {src_rel}")
        h = sha256_file(p)
        ok = h == HUB_RUNTIME_SHA[dst_rel]
        rec[src_rel] = {"sha256": h, "expected": HUB_RUNTIME_SHA[dst_rel], "pass": ok}
        if not ok:
            die(f"Hub runtime source hash mismatch: {src_rel}")
    for rel in (R2_TEST_SRC, R2_PREREG, R2_AMENDMENT):
        p = hub_root / rel
        if not p.is_file():
            die(f"missing Hub recovery input: {rel}")
        rec[rel] = {"sha256": sha256_file(p), "bytes": p.stat().st_size, "pass": True}
    return rec


def materialize_i4h(parent_c2: Path, hub_root: Path, work: Path) -> Tuple[Path, dict]:
    mat = work / "materialized_i4h"
    mat.mkdir(parents=True, exist_ok=False)
    safe_extract_zip(parent_c2, mat)

    frozen = {}
    for rel, expected in FROZEN_I4D.items():
        p = mat / rel
        if not p.is_file():
            die(f"frozen I4D file missing from exact parent materialization: {rel}")
        h = sha256_file(p)
        frozen[rel] = {"sha256": h, "expected": expected, "pass": h == expected}
        if h != expected:
            die(f"frozen I4D file hash mismatch: {rel}: {h} != {expected}")

    for dst_rel, src_rel in HUB_RUNTIME.items():
        dst = mat / dst_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(hub_root / src_rel, dst)
    test_dst = mat / R2_TEST_DST
    test_dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(hub_root / R2_TEST_SRC, test_dst)

    # Re-verify frozen parent files after overlay.
    for rel, expected in FROZEN_I4D.items():
        if sha256_file(mat / rel) != expected:
            die(f"I4H overlay modified frozen parent I4D file: {rel}")
    return mat, frozen


def discover_targeted_tests(mat: Path) -> Tuple[List[str], dict]:
    tests = mat / "tests"
    selected: List[str] = []
    hashes = {}
    for p in sorted(tests.rglob("test_*.py")):
        rel = p.relative_to(mat).as_posix()
        if "history_p07_pre09" in rel or rel.endswith("test_p07_i4h_recovery_qualification_r2.py"):
            continue
        try:
            text = p.read_text(encoding="utf-8")
        except Exception:
            continue
        if any(n in text for n in TARGETED_NEEDLES):
            selected.append(rel)
            hashes[rel] = sha256_file(p)
    if not selected:
        die("deterministic targeted discovery selected zero test files")
    return selected, hashes


def run_pytest(mat: Path, args: List[str], label: str) -> dict:
    cmd = [sys.executable, "-m", "pytest", *args]
    proc = subprocess.run(cmd, cwd=mat, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    log = proc.stdout
    m = re.findall(r"(\d+) passed", log)
    passed = int(m[-1]) if m else None
    rec = {"label": label, "command": cmd, "returncode": proc.returncode, "passed": passed, "log": log}
    if proc.returncode != 0:
        die(f"{label} failed:\n{log[-12000:]}")
    return rec


def execute_qualification(mat: Path, targeted: List[str]) -> dict:
    r2 = run_pytest(mat, ["-q", R2_TEST_DST, "--tb=short"], "RECOVERY_R2_NEW_TESTS")
    if r2["passed"] != 45:
        die(f"Recovery R2 expected 45 passed, got {r2['passed']}")
    targeted_rec = run_pytest(mat, ["-q", *targeted, "--tb=short"], "R2_DETERMINISTIC_PARENT_TARGETED_REGRESSION")
    full = run_pytest(mat, ["-q", "tests", "--ignore=tests/history_p07_pre09", "--tb=short"], "FULL_NONHISTORICAL_REGRESSION")
    if full["passed"] is None or full["passed"] < 213:
        die(f"full nonhistorical regression below frozen minimum 213: {full['passed']}")
    return {"new_r2": r2, "targeted": targeted_rec, "full": full}


def add_bytes_deterministic(zf: zipfile.ZipFile, arcname: str, data: bytes) -> None:
    if arcname in zf.namelist():
        die(f"refuse duplicate archive member: {arcname}")
    zi = zipfile.ZipInfo(arcname, FIXED_ZIP_DT)
    zi.compress_type = zipfile.ZIP_DEFLATED
    zi.external_attr = 0o644 << 16
    zf.writestr(zi, data)


def add_file_deterministic(zf: zipfile.ZipFile, arcname: str, src: Path) -> None:
    add_bytes_deterministic(zf, arcname, src.read_bytes())


def evidence_paths(hub_root: Path) -> List[Path]:
    base = hub_root / "handoff" / "20260909"
    out = []
    for p in sorted(base.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(hub_root).as_posix()
        name = p.name
        if name.startswith("P07_I4H_") or name.startswith("START_HERE_P07_SYNC_R7_I4H") or name.startswith("START_HERE_P07_SYNC_R8_I4H"):
            out.append(p)
    return out


def authority_snapshot() -> dict:
    return {
        "schema": "P07I4HRecoveredPhysicalAuthoritySnapshotR2",
        "date": "2026-09-09",
        "authority": AUTHORITY,
        "parent_physical_authority": PARENT_AUTHORITY,
        "parent_active_engine": PARENT_ENGINE,
        "production": PRODUCTION,
        "formal_scored_count": FORMAL_COUNT,
        "latest_formal_authority": LATEST_FORMAL,
        "formal_r140": R140,
        "db59_sha256": DB59_SHA,
        "i4i": {"control": 0, "selector": 0, "treatment": 0, "scores": 0},
        "claim_boundary": "Development/Preformal I4H physical recovery only; no Production, formal-count, R140, OpenAI Live or human-equivalence claim.",
    }


def copy_and_append(parent: Path, dst: Path, additions: Iterable[Tuple[str, bytes]]) -> None:
    shutil.copyfile(parent, dst)
    with zipfile.ZipFile(dst, "a", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for arc, data in additions:
            add_bytes_deterministic(zf, arc, data)
    a = audit_zip(dst)
    if not a.get("pass"):
        die(f"rebuilt ZIP integrity failed: {dst}: {a}")


def make_qualification_result(parent_verify: dict, parent_c2: dict, frozen: dict, targeted_paths: List[str], targeted_hashes: dict, qual: dict) -> dict:
    # Logs are stored separately in packages to keep this JSON compact.
    return {
        "schema": "P07I4HRecoveryQualificationResultR2",
        "date": "2026-09-09",
        "experiment_id": "P07-I4H-RECOVERY-QUAL-R2",
        "classification": "DEVELOPMENT_PREFORMAL__EXACT_SYNC_R6_PARENT_RECOVERY_QUALIFICATION",
        "parent_authority": PARENT_AUTHORITY,
        "parent_engine": PARENT_ENGINE,
        "parent_c2_sha256": parent_c2["sha256"],
        "parent_9_of_9_verified": all(v["pass"] for v in parent_verify.values()),
        "frozen_parent_i4d_files": frozen,
        "new_r2_tests": {"passed": qual["new_r2"]["passed"], "failed": 0, "status": "PASS"},
        "deterministic_parent_targeted": {
            "selected_files": targeted_paths,
            "selected_file_sha256": targeted_hashes,
            "passed": qual["targeted"]["passed"],
            "failed": 0,
            "status": "PASS",
            "historical_26_of_26_reproduction_claim": False,
        },
        "full_nonhistorical_regression": {"passed": qual["full"]["passed"], "failed": 0, "minimum": 213, "status": "PASS"},
        "critical_failure_accepts": 0,
        "python_literary_prose_generated": False,
        "scientific_result": "PASS_RECOVERY_QUALIFICATION_R2__PHYSICAL_BUILD_AUTHORIZED_PENDING_FINAL_9_PACKAGE_AUDIT",
        "claim_boundary": "New recovery qualification, not historical 42/42 or 26/26 byte-identical reproduction.",
    }


def build_outputs(parent_dir: Path, hub_root: Path, out_dir: Path, work: Path, parent_verify: dict, parent_c2_path: Path, parent_c2_rec: dict, mat: Path, frozen: dict, targeted: List[str], targeted_hashes: dict, qual: dict) -> dict:
    out_dir.mkdir(parents=True, exist_ok=False)
    qres = make_qualification_result(parent_verify, parent_c2_rec, frozen, targeted, targeted_hashes, qual)
    qbytes = canonical_json_bytes(qres)

    # Store qualification logs as evidence in A/B2 only, not in runtime C2.
    logs = {
        "R2_NEW_TESTS.txt": qual["new_r2"]["log"].encode("utf-8"),
        "R2_TARGETED_REGRESSION.txt": qual["targeted"]["log"].encode("utf-8"),
        "R2_FULL_NONHISTORICAL_REGRESSION.txt": qual["full"]["log"].encode("utf-8"),
    }
    snap = canonical_json_bytes(authority_snapshot())
    read_first = (
        "P07-I4H Recovery R2 physical authority\n"
        f"Authority: {AUTHORITY}\nParent: {PARENT_AUTHORITY} / {PARENT_ENGINE}\n"
        "Production remains ENG:R47. Formal count remains 137. R140 remains 0/0/0.\n"
        "I4I remains unexecuted. See sidecar Final Physical Audit before use.\n"
    ).encode("utf-8")

    # CONTROL: minimal current state pointers.
    control_add = [
        ("P07_I4H_RECOVERY_R2/READ_FIRST.md", read_first),
        ("P07_I4H_RECOVERY_R2/CURRENT_PHYSICAL_AUTHORITY.json", snap),
        ("P07_I4H_RECOVERY_R2/P07_I4H_RECOVERY_QUALIFICATION_RESULT_R2.json", qbytes),
    ]
    copy_and_append(parent_dir / PARENTS["CONTROL"]["filename"], out_dir / OUTPUT_NAMES["CONTROL"], control_add)

    # Evidence layer: all durable I4H Hub files + exact new result/logs.
    ev_add: List[Tuple[str, bytes]] = []
    for p in evidence_paths(hub_root):
        rel = p.relative_to(hub_root).as_posix()
        ev_add.append((f"P07_I4H_RECOVERY_R2/HUB_EVIDENCE/{rel}", p.read_bytes()))
    ev_add.append(("P07_I4H_RECOVERY_R2/P07_I4H_RECOVERY_QUALIFICATION_RESULT_R2.json", qbytes))
    for n, b in logs.items():
        ev_add.append((f"P07_I4H_RECOVERY_R2/LOGS/{n}", b))
    ev_manifest = {
        arc: hashlib.sha256(data).hexdigest() for arc, data in ev_add
    }
    ev_add.append(("P07_I4H_RECOVERY_R2/EVIDENCE_MANIFEST_SHA256.json", canonical_json_bytes(ev_manifest)))
    copy_and_append(parent_dir / PARENTS["A"]["filename"], out_dir / OUTPUT_NAMES["A"], ev_add)
    copy_and_append(parent_dir / PARENTS["B2"]["filename"], out_dir / OUTPUT_NAMES["B2"], ev_add)

    # Byte-identical packages.
    for logical in ("B1", "C1", "D1", "D2"):
        shutil.copyfile(parent_dir / PARENTS[logical]["filename"], out_dir / OUTPUT_NAMES[logical])
        if sha256_file(out_dir / OUTPUT_NAMES[logical]) != PARENTS[logical]["sha256"]:
            die(f"byte-identical copy failed: {logical}")

    # Runtime C2: append only new I4H members to exact parent C2 raw bytes.
    c2_out = work / "I4H_RECOVERY_R2_C2.zip"
    shutil.copyfile(parent_c2_path, c2_out)
    c2_members: List[Tuple[str, bytes]] = []
    for dst_rel, src_rel in HUB_RUNTIME.items():
        c2_members.append((dst_rel, (hub_root / src_rel).read_bytes()))
    c2_members.append((R2_TEST_DST, (hub_root / R2_TEST_SRC).read_bytes()))
    c2_members.append(("evidence/P07_I4H_RECOVERY_QUALIFICATION_PREREG_R2_20260909.json", (hub_root / R2_PREREG).read_bytes()))
    c2_members.append(("evidence/P07_I4H_RECOVERY_QUALIFICATION_R2_TARGETED_AMENDMENT_R1_20260909.json", (hub_root / R2_AMENDMENT).read_bytes()))
    c2_members.append(("evidence/P07_I4H_RECOVERY_QUALIFICATION_RESULT_R2_20260909.json", qbytes))
    with zipfile.ZipFile(c2_out, "a", compression=zipfile.ZIP_DEFLATED, allowZip64=True) as zf:
        for arc, data in c2_members:
            add_bytes_deterministic(zf, arc, data)
    c2_audit = audit_zip(c2_out)
    if not c2_audit.get("pass"):
        die(f"output C2 integrity failed: {c2_audit}")

    total = c2_out.stat().st_size
    cut = (total + 1) // 2
    a_path = out_dir / OUTPUT_NAMES["C2-A"]
    b_path = out_dir / OUTPUT_NAMES["C2-B"]
    with c2_out.open("rb") as src, a_path.open("wb") as a:
        remaining = cut
        while remaining:
            chunk = src.read(min(8 * 1024 * 1024, remaining))
            if not chunk:
                die("unexpected EOF splitting output C2-A")
            a.write(chunk)
            remaining -= len(chunk)
        with b_path.open("wb") as b:
            shutil.copyfileobj(src, b, length=8 * 1024 * 1024)

    return {"qualification_result": qres, "c2_path": c2_out, "c2_audit": c2_audit, "c2_added_members": [x[0] for x in c2_members]}


def package_set_root(records: List[dict]) -> str:
    material = [{k: r[k] for k in ("logical_part", "filename", "bytes", "sha256")} for r in records]
    return hashlib.sha256(canonical_json_bytes(material)).hexdigest()


def final_audit(out_dir: Path, build: dict, parent_verify: dict, parent_c2_rec: dict, frozen: dict) -> dict:
    packages = []
    all_ok = True
    for logical in ("CONTROL", "A", "B1", "B2", "C1", "C2-A", "C2-B", "D1", "D2"):
        p = out_dir / OUTPUT_NAMES[logical]
        rec = {
            "logical_part": logical,
            "filename": p.name,
            "bytes": p.stat().st_size,
            "sha256": sha256_file(p),
        }
        if logical not in ("C2-A", "C2-B"):
            rec["zip_audit"] = audit_zip(p)
            rec["pass"] = rec["zip_audit"].get("pass", False)
        else:
            rec["pass"] = True
        if logical in ("B1", "C1", "D1", "D2"):
            rec["parent_byte_identical"] = rec["sha256"] == PARENTS[logical]["sha256"]
            rec["pass"] = rec["pass"] and rec["parent_byte_identical"]
        packages.append(rec)
        all_ok = all_ok and rec["pass"]

    # Reassemble final C2 from transport pieces and compare with built C2.
    with tempfile.TemporaryDirectory(prefix="i4h-final-audit-") as td:
        rejoined = Path(td) / "FINAL_C2.zip"
        concat_files(out_dir / OUTPUT_NAMES["C2-A"], out_dir / OUTPUT_NAMES["C2-B"], rejoined)
        c2_sha = sha256_file(rejoined)
        c2_a = audit_zip(rejoined)
        c2_match = c2_sha == sha256_file(build["c2_path"]) and rejoined.stat().st_size == build["c2_path"].stat().st_size
    all_ok = all_ok and c2_a.get("pass", False) and c2_match

    audit = {
        "schema": "P07I4HRecoveryR2FinalPhysicalAuditR1",
        "date": "2026-09-09",
        "authority": AUTHORITY,
        "parent_authority": PARENT_AUTHORITY,
        "parent_engine": PARENT_ENGINE,
        "parent_9_of_9_verification": parent_verify,
        "parent_c2_verification": parent_c2_rec,
        "frozen_parent_i4d_files": frozen,
        "packages": packages,
        "package_set_sha256": package_set_root(packages),
        "final_c2": {
            "bytes": build["c2_path"].stat().st_size,
            "sha256": sha256_file(build["c2_path"]),
            "entries": build["c2_audit"].get("entries"),
            "duplicate_paths": build["c2_audit"].get("duplicate_paths"),
            "unsafe_paths": build["c2_audit"].get("unsafe_paths"),
            "crc_bad_member": build["c2_audit"].get("crc_bad_member"),
            "transport_reassembly_matches_built_c2": c2_match,
            "added_members": build["c2_added_members"],
            "pass": c2_a.get("pass", False) and c2_match,
        },
        "db59": {
            "sha256": DB59_SHA,
            "verification_mode": "TRANSITIVE_BYTE_IDENTITY_FROM_SYNC_R6_FINAL_AUDIT",
            "parent_final_audit_sha256": PARENT_AUDIT_SHA,
            "D1_parent_byte_identical": next(x for x in packages if x["logical_part"] == "D1")["parent_byte_identical"],
            "D2_parent_byte_identical": next(x for x in packages if x["logical_part"] == "D2")["parent_byte_identical"],
            "pass": True,
        },
        "qualification": build["qualification_result"],
        "state_boundary": {
            "active_development_engine": AUTHORITY,
            "production": PRODUCTION,
            "formal_scored_count": FORMAL_COUNT,
            "latest_formal_authority": LATEST_FORMAL,
            "r140": R140,
            "i4i": [0, 0, 0, 0],
        },
        "overall_pass": bool(all_ok),
        "claim_boundary": "P07-I4H Development/Preformal physical recovery. No Production, formal-count, R140, OpenAI Live, human-equivalence or I4I result claim.",
    }
    if not audit["overall_pass"]:
        die("final physical audit failed")
    return audit


def write_sidecars(out_dir: Path, audit: dict) -> None:
    audit_path = out_dir / f"LITERARY_OS_I4H_RECOVERY_R2_FINAL_PHYSICAL_AUDIT_R1_{DATE}.json"
    audit_path.write_bytes(canonical_json_bytes(audit))
    lines = []
    for logical in ("CONTROL", "A", "B1", "B2", "C1", "C2-A", "C2-B", "D1", "D2"):
        p = out_dir / OUTPUT_NAMES[logical]
        lines.append(f"{sha256_file(p)}  {p.name}")
    lines.append(f"{sha256_file(audit_path)}  {audit_path.name}")
    (out_dir / "SHA256SUMS_I4H_RECOVERY_R2.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (out_dir / "READ_FIRST_I4H_RECOVERY_R2.md").write_text(
        "# P07-I4H Recovery R2 Physical Authority\n\n"
        "Use only if `LITERARY_OS_I4H_RECOVERY_R2_FINAL_PHYSICAL_AUDIT_R1_20260909.json` has `overall_pass=true`.\n\n"
        f"Authority: `{AUTHORITY}`.\n\n"
        "Production remains `ENG:R47`; formal scored count remains `137`; R140 remains `0/0/0`; I4I remains unexecuted.\n",
        encoding="utf-8",
    )


def self_test() -> None:
    assert is_unsafe_zip_name("../x")
    assert is_unsafe_zip_name("/x")
    assert not is_unsafe_zip_name("a/b.txt")
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "x.zip"
        with zipfile.ZipFile(p, "w") as zf:
            add_bytes_deterministic(zf, "a.txt", b"a")
        a = audit_zip(p, 1)
        assert a["pass"], a
        p2 = Path(td) / "copy.zip"
        copy_and_append(p, p2, [("b.txt", b"b")])
        a2 = audit_zip(p2, 2)
        assert a2["pass"], a2
    print("SELF_TEST_PASS")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parent-dir", type=Path)
    ap.add_argument("--hub-root", type=Path)
    ap.add_argument("--out-dir", type=Path)
    ap.add_argument("--verify-only", action="store_true")
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if not args.parent_dir or not args.hub_root or not args.out_dir:
        ap.error("--parent-dir, --hub-root and --out-dir are required unless --self-test")
    parent_dir = args.parent_dir.resolve()
    hub_root = args.hub_root.resolve()
    out_dir = args.out_dir.resolve()
    if out_dir.exists():
        die(f"output directory already exists; refusing mutation: {out_dir}")

    hub_verify = verify_hub_inputs(hub_root)
    parent_verify = verify_parent_files(parent_dir)
    with tempfile.TemporaryDirectory(prefix="p07-i4h-recovery-r2-") as td:
        work = Path(td)
        parent_c2_path, parent_c2_rec = verify_parent_c2(parent_dir, work)
        checkpoint = {
            "hub_inputs": hub_verify,
            "parent_9_of_9": parent_verify,
            "parent_c2": parent_c2_rec,
        }
        if args.verify_only:
            print(json.dumps(checkpoint, ensure_ascii=False, indent=2, sort_keys=True))
            return
        mat, frozen = materialize_i4h(parent_c2_path, hub_root, work)
        targeted, targeted_hashes = discover_targeted_tests(mat)
        qual = execute_qualification(mat, targeted)
        build = build_outputs(parent_dir, hub_root, out_dir, work, parent_verify, parent_c2_path, parent_c2_rec, mat, frozen, targeted, targeted_hashes, qual)
        audit = final_audit(out_dir, build, parent_verify, parent_c2_rec, frozen)
        write_sidecars(out_dir, audit)
        print(json.dumps({
            "status": "PASS_I4H_RECOVERY_R2_PHYSICAL_BUILD",
            "authority": AUTHORITY,
            "output_dir": str(out_dir),
            "package_set_sha256": audit["package_set_sha256"],
            "final_c2_sha256": audit["final_c2"]["sha256"],
            "overall_pass": audit["overall_pass"],
        }, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
