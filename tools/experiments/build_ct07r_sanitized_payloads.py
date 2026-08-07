#!/usr/bin/env python3
"""Build CT-07R sanitized T/TN renderer payloads deterministically.

This tool performs NO literary semantic generation. It only:
- strips archival provenance/identity fields,
- converts scene numbers to target-relative slots,
- applies the preregistered within-work cyclic +1 TN donor mapping,
- equalizes T/TN target-slot coverage,
- injects the exact same neutral context notice into T and TN,
- writes a private orchestration mapping + SHA256 manifest.

Authority:
- DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1
- CT-07R prereg v1.0
- prereg amendments v1.1 + v1.1.1 + amendment 02
- CT07R_RENDER_PAYLOAD_CONTRACT_V1_0_2
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any

ANCHORS = {
    "101번째프로포즈": [
        "101번째프로포즈_02_S05",
        "101번째프로포즈_05_S06",
        "101번째프로포즈_08_S07",
        "101번째프로포즈_11_S07",
        "101번째프로포즈_14_S07",
    ],
    "38사기동대": [
        "38사기동대_02_S05",
        "38사기동대_05_S08",
        "38사기동대_08_S09",
        "38사기동대_12_S08",
        "38사기동대_15_S07",
    ],
}

SLOT_IDS = {
    seq_id: f"CT07R_A{i:02d}"
    for i, seq_id in enumerate(
        ANCHORS["101번째프로포즈"] + ANCHORS["38사기동대"], start=1
    )
}

NEUTRAL_CONTEXT_NOTICE = "이 설계 맥락은 검증되지 않았을 수 있다."

FORBIDDEN_KEYS = {
    "work_id", "episode_no", "seq_id", "seq_index", "member_scene_nos",
    "evidence_refs", "source_hashes", "by", "existing_refs", "thread_id",
    "arm_label", "donor_id", "negative_type",
}

_EP_LABEL = re.compile(r"(?i)\bEP\s*0*\d+\b")


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as f:
        for lineno, line in enumerate(f, start=1):
            if not line.strip():
                continue
            obj = json.loads(line)
            if not isinstance(obj, dict):
                raise ValueError(f"line {lineno}: expected object")
            rows.append(obj)
    return rows


def source_scene_to_ordinal(packet: dict[str, Any]) -> dict[int, int]:
    return {int(scene_no): i for i, scene_no in enumerate(packet["member_scene_nos"], start=1)}


def nearest_target_slot_from_donor_ordinal(i: int, D: int, T: int) -> int:
    if D <= 1 or T <= 1:
        return 1
    x = (i - 1) * (T - 1) / (D - 1)
    return 1 + int(x + 0.5)


def nearest_donor_ordinal_for_target_slot(j: int, D: int, T: int) -> int:
    if D <= 1 or T <= 1:
        return 1
    x = (j - 1) * (D - 1) / (T - 1)
    return 1 + int(x + 0.5)


def sanitize_text(text: str) -> str:
    return _EP_LABEL.sub("[LATER]", text)


def strip_cast(packet: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        {
            "character": c["character"],
            "desire_or_function": sanitize_text(c["desire_or_function"]),
            "participation": c["participation"],
        }
        for c in packet.get("cast", [])
    ]


def map_scene_refs(
    packet: dict[str, Any],
    scene_nos: list[int],
    target_n: int,
    *,
    identity: bool,
) -> list[str]:
    src_to_ord = source_scene_to_ordinal(packet)
    donor_n = len(packet["member_scene_nos"])
    out: list[int] = []
    for scene_no in scene_nos:
        if int(scene_no) not in src_to_ord:
            raise ValueError(f"scene ref {scene_no} absent from {packet['seq_id']}")
        donor_ord = src_to_ord[int(scene_no)]
        slot = donor_ord if identity else nearest_target_slot_from_donor_ordinal(donor_ord, donor_n, target_n)
        if slot not in out:
            out.append(slot)
    return [f"slot_{n}" for n in sorted(out)]


def strip_info(packet: dict[str, Any], target_n: int, *, identity: bool) -> list[dict[str, Any]]:
    result = []
    for item in packet.get("info_shift", []):
        result.append({
            "subject": item["subject"],
            "before": sanitize_text(item["before"]),
            "after": sanitize_text(item["after"]),
            "mode": item["mode"],
            "scene_slots": map_scene_refs(packet, item.get("scene_nos", []), target_n, identity=identity),
        })
    return result


def strip_plant(packet: dict[str, Any], target_n: int, *, identity: bool) -> list[dict[str, Any]]:
    result = []
    for item in packet.get("plant_payoff", []):
        result.append({
            "kind": item["kind"],
            "statement": sanitize_text(item["statement"]),
            "scene_slots": map_scene_refs(packet, item.get("scene_nos", []), target_n, identity=identity),
        })
    return result


def target_scene_notes(packet: dict[str, Any]) -> list[dict[str, Any]]:
    member = list(packet["member_scene_nos"])
    notes = {int(n["scene_no"]): n for n in packet.get("scene_notes", [])}
    if set(notes) != set(map(int, member)):
        raise ValueError(f"scene-note coverage mismatch in {packet['seq_id']}")
    return [
        {
            "slot": f"slot_{i}",
            "functional_propositions": [sanitize_text(x) for x in notes[int(scene_no)]["functional_propositions"]],
        }
        for i, scene_no in enumerate(member, start=1)
    ]


def donor_scene_notes(donor: dict[str, Any], target_n: int) -> list[dict[str, Any]]:
    member = list(donor["member_scene_nos"])
    notes = {int(n["scene_no"]): n for n in donor.get("scene_notes", [])}
    if set(notes) != set(map(int, member)):
        raise ValueError(f"scene-note coverage mismatch in donor {donor['seq_id']}")
    D = len(member)
    result = []
    for target_slot in range(1, target_n + 1):
        donor_ord = nearest_donor_ordinal_for_target_slot(target_slot, D, target_n)
        donor_scene_no = int(member[donor_ord - 1])
        props = [sanitize_text(x) for x in notes[donor_scene_no]["functional_propositions"]]
        if not props:
            raise ValueError(f"empty donor propositions: {donor['seq_id']} ordinal {donor_ord}")
        result.append({"slot": f"slot_{target_slot}", "functional_propositions": props})
    return result


def materialize(target: dict[str, Any], source: dict[str, Any], *, is_target: bool) -> dict[str, Any]:
    target_n = len(target["member_scene_nos"])
    payload = {
        "schema": "CT07R_SANITIZED_THICK_RENDER_PAYLOAD_V1_0_2",
        "neutral_context_notice": NEUTRAL_CONTEXT_NOTICE,
        "target_slot_id": SLOT_IDS[target["seq_id"]],
        "cast": strip_cast(source),
        "event": sanitize_text(source["event"]),
        "info_shift": strip_info(source, target_n, identity=is_target),
        "plant_payoff": strip_plant(source, target_n, identity=is_target),
        "scene_notes": target_scene_notes(source) if is_target else donor_scene_notes(source, target_n),
    }
    required = {
        "schema", "neutral_context_notice", "target_slot_id", "cast", "event",
        "info_shift", "plant_payoff", "scene_notes"
    }
    if set(payload) != required:
        raise AssertionError("renderer keyset drift")
    if payload["neutral_context_notice"] != NEUTRAL_CONTEXT_NOTICE:
        raise AssertionError("neutral notice drift")
    if len(payload["scene_notes"]) != target_n:
        raise AssertionError("target-slot count mismatch")
    if any(not n["functional_propositions"] for n in payload["scene_notes"]):
        raise AssertionError("empty scene-note slot")
    forbidden = FORBIDDEN_KEYS.intersection(payload)
    if forbidden:
        raise AssertionError(f"forbidden renderer keys: {forbidden}")
    return payload


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> str:
    data = "".join(json.dumps(r, ensure_ascii=False, separators=(",", ":")) + "\n" for r in rows).encode("utf-8")
    path.write_bytes(data)
    return sha256_bytes(data)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--out-dir", required=True, type=Path)
    args = ap.parse_args()

    rows = load_jsonl(args.input)
    by_seq = {r["seq_id"]: r for r in rows}
    expected = [x for work in ("101번째프로포즈", "38사기동대") for x in ANCHORS[work]]
    if set(by_seq) != set(expected) or len(rows) != 10:
        raise ValueError(f"packet set mismatch: expected 10 exact anchors, got {len(rows)}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    T_rows: list[dict[str, Any]] = []
    TN_rows: list[dict[str, Any]] = []
    private_map = []

    for work in ("101번째프로포즈", "38사기동대"):
        anchors = ANCHORS[work]
        for idx, target_seq in enumerate(anchors):
            donor_seq = anchors[(idx + 1) % len(anchors)]
            target = by_seq[target_seq]
            donor = by_seq[donor_seq]
            t_payload = materialize(target, target, is_target=True)
            tn_payload = materialize(target, donor, is_target=False)
            if t_payload["neutral_context_notice"] != tn_payload["neutral_context_notice"]:
                raise AssertionError("T/TN neutral notice asymmetry")
            if len(t_payload["scene_notes"]) != len(tn_payload["scene_notes"]):
                raise AssertionError("T/TN scene-note slot asymmetry")
            T_rows.append(t_payload)
            TN_rows.append(tn_payload)
            private_map.append({
                "target_slot_id": SLOT_IDS[target_seq],
                "target_seq_id": target_seq,
                "tn_donor_seq_id": donor_seq,
                "target_scene_count": len(target["member_scene_nos"]),
                "donor_scene_count": len(donor["member_scene_nos"]),
            })

    t_path = args.out_dir / "CT07R_sanitized_T_payloads.jsonl"
    tn_path = args.out_dir / "CT07R_sanitized_TN_payloads.jsonl"
    map_path = args.out_dir / "CT07R_private_orchestration_map.json"
    manifest_path = args.out_dir / "CT07R_sanitized_payload_manifest.json"

    t_sha = write_jsonl(t_path, T_rows)
    tn_sha = write_jsonl(tn_path, TN_rows)
    map_bytes = (json.dumps({"schema":"CT07R_PRIVATE_ORCHESTRATION_MAP_V1","mapping":private_map}, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    map_path.write_bytes(map_bytes)
    map_sha = sha256_bytes(map_bytes)

    manifest = {
        "schema": "CT07R_SANITIZED_PAYLOAD_MANIFEST_V1_0_2",
        "input_path": str(args.input),
        "input_sha256": sha256_bytes(args.input.read_bytes()),
        "contract": "CT07R_RENDER_PAYLOAD_CONTRACT_V1_0_2",
        "neutral_context_notice": NEUTRAL_CONTEXT_NOTICE,
        "records_per_arm": 10,
        "T_sha256": t_sha,
        "TN_sha256": tn_sha,
        "private_map_sha256": map_sha,
        "density_checks": "PASS",
        "neutral_notice_symmetry": "PASS",
        "semantic_generation_performed": false
    }
    manifest_bytes = (json.dumps(manifest, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    manifest_path.write_bytes(manifest_bytes)

    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
