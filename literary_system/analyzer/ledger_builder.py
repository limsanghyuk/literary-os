from __future__ import annotations

from collections import Counter
from typing import Any

from literary_system.analyzer.text_analysis import extract_speakers, normalize_name, tokenize_keywords
from literary_system.common.enums import RoleType

_CHARACTER_HINTS = {"주인공", "형", "누나", "동생", "어머니", "엄마", "아버지", "아빠", "친구", "선배", "후배", "형사", "의사"}


def _infer_role_type(name: str, global_text: str) -> str:
    lower = global_text.lower()
    if any(token in name for token in ("목격", "증인", "witness")):
        return RoleType.WITNESS.value
    if name in {"어머니", "엄마", "아버지", "아빠"}:
        return RoleType.STRUCTURE.value
    if any(token in lower for token in ("거울", "mirror", "닮", "반사")):
        return RoleType.MIRROR.value
    if any(token in lower for token in ("압박", "pressure", "죄책감", "guilt", "분노", "anger", "회피", "avoidance")):
        return RoleType.PRESSURE.value
    return RoleType.RESIDUE_CARRIER.value if any(token in lower for token in ("침묵", "비밀", "흔적", "residue")) else RoleType.PRESSURE.value


def _infer_pressure_target(name: str, scene_texts: list[str]) -> str:
    local = "\n".join(text for text in scene_texts if name in text)
    keywords = tokenize_keywords(local)
    priority = [kw for kw in keywords if kw in {"죄책감", "회피", "분노", "비밀", "침묵", "상실", "guilt", "anger", "secret", "silence", "loss", "avoidance"}]
    if priority:
        return priority[0]
    return "story_pressure"


def _infer_residue_binding(name: str, pressure_target: str, local_texts: list[str]) -> dict[str, list[str]]:
    local = "\n".join(local_texts)
    objects = []
    gestures = []
    space = []
    if pressure_target != "story_pressure":
        objects.append(pressure_target)
    if any(tok in local for tok in ("침묵", "정적", "말을 삼", "말하지 못")):
        gestures.append("silence_hold")
    if any(tok in local for tok in ("문", "복도", "식탁", "장례식장", "방")):
        if "복도" in local:
            space.append("corridor_pressure")
        elif "문" in local:
            space.append("threshold_pause")
        else:
            space.append("domestic_surface")
    return {"object": list(dict.fromkeys(objects)), "gesture": list(dict.fromkeys(gestures)), "space_pattern": list(dict.fromkeys(space))}


def build_character_ledger(project_context: dict[str, Any], source_records: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
    provided = project_context.get("characters", [])
    if provided:
        ledgers: list[dict[str, Any]] = []
        for i, char in enumerate(provided, start=1):
            char_id = char.get("character_id") or f"char_{i:03d}"
            ledgers.append({
                "character_id": char_id,
                "display_name": char["display_name"],
                "role_type": char.get("role_type", RoleType.PRESSURE.value),
                "domain_function": char.get("domain_function", ""),
                "defect": char.get("defect", ""),
                "blindness": char.get("blindness", ""),
                "protagonist_relation": char.get("protagonist_relation", ""),
                "pressure_target": char.get("pressure_target", "story_pressure"),
                "entry_act": char.get("entry_act", 1),
                "entry_trigger": char.get("entry_trigger", ""),
                "exit_condition": char.get("exit_condition", ""),
                "residue_binding": char.get("residue_binding", {"object": [], "gesture": [], "space_pattern": []}),
                "act_evolution": char.get("act_evolution", {"act_1": "", "act_2": "", "act_3": ""}),
                "memory_weight": float(char.get("memory_weight", 0.7)),
                "prunable": bool(char.get("prunable", False)),
            })
        return ledgers

    records = source_records or []
    full_text = "\n".join(rec.get("text", "") for rec in records)
    candidates: list[str] = []
    for rec in records:
        candidates.extend(extract_speakers(rec.get("text", "")))
    tokens = Counter(tokenize_keywords(full_text))
    for token, count in tokens.most_common(25):
        token = normalize_name(token)
        if token in _CHARACTER_HINTS and count >= 1:
            candidates.append(token)
    unique_names = []
    for name in candidates:
        if name and name not in unique_names:
            unique_names.append(name)
    scene_texts = [rec.get("text", "") for rec in records]
    ledgers = []
    for i, name in enumerate(unique_names[:8], start=1):
        local_texts = [t for t in scene_texts if name in t]
        local_mentions = len(local_texts)
        role_type = _infer_role_type(name, full_text)
        pressure_target = _infer_pressure_target(name, scene_texts)
        residue_binding = _infer_residue_binding(name, pressure_target, local_texts)
        ledgers.append({
            "character_id": f"char_{i:03d}",
            "display_name": name,
            "role_type": role_type,
            "domain_function": f"auto_inferred_from_sources:{local_mentions}",
            "defect": "회피" if pressure_target in {"죄책감", "회피", "silence", "침묵"} else "",
            "blindness": "자기보존을 신중함으로 오인" if local_mentions >= 1 else "",
            "protagonist_relation": "",
            "pressure_target": pressure_target,
            "entry_act": 1,
            "entry_trigger": "auto_detected",
            "exit_condition": "",
            "residue_binding": residue_binding,
            "act_evolution": {"act_1": "detected", "act_2": "pressure_shift", "act_3": "payoff_or_reversal"},
            "memory_weight": round(min(1.0, 0.42 + local_mentions * 0.14 + (0.08 if residue_binding['gesture'] else 0.0)), 2),
            "prunable": local_mentions <= 1 and name not in {"주인공", "형", "어머니", "엄마", "아버지", "아빠"},
        })
    return ledgers
