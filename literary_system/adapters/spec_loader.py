from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

DEFAULT_SPEC = {
    "schema_version": "adapter_spec_v1",
    "name": "default_creator_project_spec",
    "description": "Default spec for creative-project package ingestion into the standard literary analyzer.",
    "engine_compat": {"min": "v3", "recommended": "v5"},
    "file_slots": {
        "project_context": ["project_context.json", "project.json"],
        "constitution": ["constitution.json", "format_constitution.json", "engine_constitution.json"],
        "characters": ["characters.json", "cast.json"],
        "scenes": ["scenes.json", "scene_plan.json", "beats.json"],
        "raw_inputs": ["raw_inputs.json"],
        "seed": ["seed.md", "seed.txt", "master_seed.md", "master_seed.txt"],
    },
    "required_slots": [],
    "context_aliases": {
        "projectId": "project_id",
        "projectMode": "project_mode",
        "mediaType": "media_type",
        "masterSeed": "master_seed",
        "episodeRuntimeMin": "episode_runtime_min",
        "totalEpisodes": "total_episode_count",
        "actBundleSize": "act_bundle_size",
        "pdiProfile": "pdi_profile",
        "authorialProfileHint": "authorial_profile_hint",
        "kHybridBias": "k_hybrid_bias",
        "criticPatternCodes": "critic_pattern_codes",
        "fewshotPromotionDecision": "fewshot_promotion_decision",
    },
    "character_field_aliases": {
        "id": "character_id",
        "name": "display_name",
        "role": "role_type",
        "pressureTarget": "pressure_target",
        "memoryWeight": "memory_weight",
        "entryAct": "entry_act",
        "entryTrigger": "entry_trigger",
        "exitCondition": "exit_condition",
        "residueBinding": "residue_binding",
        "actEvolution": "act_evolution",
    },
    "scene_field_aliases": {
        "id": "scene_id",
        "goal": "scene_goal",
        "focus": "scene_focus",
        "characters": "active_characters",
        "tensionAxes": "active_tension_axes",
        "bundleId": "bundle_id",
        "rawText": "raw_text",
        "sceneText": "scene_text",
        "continuityNotes": "continuity_notes",
        "continuityRisks": "continuity_risks",
    },
    "input_folder_rules": [
        {"folder": "sources", "default_kind": "canon", "extensions": [".txt", ".md", ".json"]},
        {"folder": "notes", "default_kind": "project_doc", "extensions": [".txt", ".md", ".json"]},
    ],
    "extension_packet_folders": ["packets", "extensions"],
    "packet_slot_map": {},
    "merge_order": ["constitution", "project_context"],
    "local_spec_candidates": ["adapter_spec.json", "adapter.spec.json"],
}

ALLOWED_SCHEMA_VERSIONS = {"adapter_spec_v1"}


class AdapterSpecError(ValueError):
    pass


@dataclass(slots=True)
class AdapterSpec:
    schema_version: str
    name: str
    description: str = ""
    engine_compat: dict[str, str] = field(default_factory=dict)
    file_slots: dict[str, list[str]] = field(default_factory=dict)
    required_slots: list[str] = field(default_factory=list)
    context_aliases: dict[str, str] = field(default_factory=dict)
    character_field_aliases: dict[str, str] = field(default_factory=dict)
    scene_field_aliases: dict[str, str] = field(default_factory=dict)
    input_folder_rules: list[dict[str, Any]] = field(default_factory=list)
    extension_packet_folders: list[str] = field(default_factory=list)
    packet_slot_map: dict[str, str] = field(default_factory=dict)
    merge_order: list[str] = field(default_factory=list)
    local_spec_candidates: list[str] = field(default_factory=list)
    source_chain: list[str] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: dict[str, Any], *, source_chain: list[str] | None = None) -> "AdapterSpec":
        return cls(
            schema_version=str(data.get("schema_version", "adapter_spec_v1")),
            name=str(data.get("name", "unnamed_adapter_spec")),
            description=str(data.get("description", "")),
            engine_compat=dict(data.get("engine_compat", {})),
            file_slots={k: list(v) for k, v in data.get("file_slots", {}).items()},
            required_slots=list(data.get("required_slots", [])),
            context_aliases=dict(data.get("context_aliases", {})),
            character_field_aliases=dict(data.get("character_field_aliases", {})),
            scene_field_aliases=dict(data.get("scene_field_aliases", {})),
            input_folder_rules=list(data.get("input_folder_rules", [])),
            extension_packet_folders=list(data.get("extension_packet_folders", [])),
            packet_slot_map=dict(data.get("packet_slot_map", {})),
            merge_order=list(data.get("merge_order", [])),
            local_spec_candidates=list(data.get("local_spec_candidates", ["adapter_spec.json", "adapter.spec.json"])),
            source_chain=list(source_chain or []),
        )


def _deep_copy_defaults() -> dict[str, Any]:
    return json.loads(json.dumps(DEFAULT_SPEC))


def _merge_spec(base: dict[str, Any], override: dict[str, Any]) -> dict[str, Any]:
    merged = dict(base)
    for key, value in override.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            inner = dict(merged[key])
            inner.update(value)
            merged[key] = inner
        elif isinstance(value, list) and isinstance(merged.get(key), list):
            merged[key] = list(value)
        else:
            merged[key] = value
    return merged


def validate_adapter_spec_dict(data: dict[str, Any]) -> None:
    version = data.get("schema_version", "adapter_spec_v1")
    if version not in ALLOWED_SCHEMA_VERSIONS:
        raise AdapterSpecError(f"unsupported adapter spec schema_version: {version}")
    if not isinstance(data.get("name", ""), str) or not str(data.get("name", "")).strip():
        raise AdapterSpecError("adapter spec requires non-empty 'name'")
    for key in ("file_slots", "context_aliases", "character_field_aliases", "scene_field_aliases", "packet_slot_map"):
        if key in data and not isinstance(data[key], dict):
            raise AdapterSpecError(f"adapter spec field '{key}' must be an object")
    if "required_slots" in data and not isinstance(data["required_slots"], list):
        raise AdapterSpecError("adapter spec field 'required_slots' must be a list")
    if "merge_order" in data:
        merge_order = data["merge_order"]
        if not isinstance(merge_order, list):
            raise AdapterSpecError("adapter spec field 'merge_order' must be a list")
        allowed = set(data.get("file_slots", {}).keys()) | set(DEFAULT_SPEC["file_slots"].keys())
        unknown = [x for x in merge_order if x not in allowed]
        if unknown:
            raise AdapterSpecError(f"merge_order contains unknown slots: {unknown}")
    for slot, candidates in data.get("file_slots", {}).items():
        if not isinstance(candidates, list) or not all(isinstance(x, str) and x for x in candidates):
            raise AdapterSpecError(f"file_slots['{slot}'] must be a non-empty string list")
    for rule in data.get("input_folder_rules", []):
        if not isinstance(rule, dict):
            raise AdapterSpecError("every input_folder_rule must be an object")
        if "folder" not in rule or "default_kind" not in rule:
            raise AdapterSpecError("every input_folder_rule requires 'folder' and 'default_kind'")
    if "local_spec_candidates" in data and not isinstance(data["local_spec_candidates"], list):
        raise AdapterSpecError("local_spec_candidates must be a list")


def load_adapter_spec(spec_path: str | Path | None = None, *, package_root: str | Path | None = None) -> AdapterSpec:
    spec_data = _deep_copy_defaults()
    source_chain = ["builtin:default_creator_project_spec"]

    if spec_path is not None:
        raw = json.loads(Path(spec_path).read_text(encoding="utf-8"))
        validate_adapter_spec_dict(raw)
        spec_data = _merge_spec(spec_data, raw)
        source_chain.append(str(Path(spec_path)))

    if package_root is not None:
        root = Path(package_root)
        candidates = spec_data.get("local_spec_candidates", ["adapter_spec.json", "adapter.spec.json"])
        for name in candidates:
            path = root / name
            if path.exists():
                raw = json.loads(path.read_text(encoding="utf-8"))
                validate_adapter_spec_dict(raw)
                spec_data = _merge_spec(spec_data, raw)
                source_chain.append(str(path))
                break

    validate_adapter_spec_dict(spec_data)
    return AdapterSpec.from_dict(spec_data, source_chain=source_chain)
