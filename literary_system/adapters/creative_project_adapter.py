from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from literary_system.adapters.spec_loader import AdapterSpec, load_adapter_spec


class CreativeProjectAdapter:
    """Spec-driven adapter from creator package -> analyzer inputs/context.

    Design goal:
    - Analyzer and Librarian stay stable.
    - Project-specific input drift is absorbed here.
    - Prefer declarative spec changes over code edits.
    """

    def __init__(self, package_root: str | Path, *, spec_path: str | Path | None = None) -> None:
        self.package_root = Path(package_root)
        if not self.package_root.exists():
            raise FileNotFoundError(f"project package not found: {self.package_root}")
        self.spec: AdapterSpec = load_adapter_spec(spec_path, package_root=self.package_root)

    def load(self) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, Any]]:
        slot_payloads = {slot: self._read_slot_json(slot, default=None) for slot in self.spec.file_slots}
        seed_text = self._read_slot_text("seed") or ""

        self._assert_required_slots(slot_payloads, seed_text)

        context = self._normalize_context(slot_payloads.get("project_context") or {})
        constitution = self._normalize_context(slot_payloads.get("constitution") or {})
        characters = self._normalize_characters(slot_payloads.get("characters") or [])
        scenes = self._normalize_scenes(slot_payloads.get("scenes") or [])
        raw_inputs = slot_payloads.get("raw_inputs")

        merged_context = self._merge_contexts(context=context, constitution=constitution)
        if characters and "characters" not in merged_context:
            merged_context["characters"] = characters
        if scenes and "scenes" not in merged_context:
            merged_context["scenes"] = scenes
        if seed_text and not merged_context.get("master_seed"):
            merged_context["master_seed"] = seed_text.strip()
        if "project_id" not in merged_context:
            merged_context["project_id"] = self.package_root.name

        passthrough_packets = self._collect_slot_packets(slot_payloads)
        extension_packets = self._collect_extension_packets()
        if passthrough_packets or extension_packets:
            merged_context["extension_packets"] = [*passthrough_packets, *extension_packets]

        inputs: list[dict[str, Any]] = []
        if isinstance(raw_inputs, list):
            inputs.extend(raw_inputs)
        else:
            for rule in self.spec.input_folder_rules:
                folder = rule.get("folder")
                kind = rule.get("default_kind", "source")
                exts = set(rule.get("extensions", [".txt", ".md", ".json"]))
                inputs.extend(self._collect_text_inputs(folder, kind, exts))

        if not inputs and merged_context.get("scenes"):
            for idx, scene in enumerate(merged_context["scenes"], start=1):
                raw_text = scene.get("raw_text") or scene.get("scene_text") or scene.get("summary") or scene.get("scene_focus") or ""
                if raw_text.strip():
                    inputs.append({
                        "kind": "scene_memo",
                        "title": scene.get("scene_id", f"scene_{idx:02d}"),
                        "text": raw_text,
                    })

        if not inputs and seed_text:
            inputs.append({"kind": "seed", "title": "master_seed", "text": seed_text})

        diagnostics = {
            "package_root": str(self.package_root),
            "adapter_spec_name": self.spec.name,
            "adapter_spec_version": self.spec.schema_version,
            "adapter_spec_sources": self.spec.source_chain,
            "input_count": len(inputs),
            "has_context": bool(merged_context),
            "has_characters": bool(merged_context.get("characters")),
            "has_scenes": bool(merged_context.get("scenes")),
            "extension_packet_count": len(merged_context.get("extension_packets", [])),
            "loaded_files": self._loaded_files_list(),
            "resolved_slots": {slot: self._resolve_slot_path(slot) for slot in self.spec.file_slots},
            "merge_order": self.spec.merge_order,
            "required_slots": self.spec.required_slots,
        }
        return inputs, merged_context, diagnostics

    def _assert_required_slots(self, slot_payloads: dict[str, Any], seed_text: str) -> None:
        missing: list[str] = []
        for slot in self.spec.required_slots:
            if slot == "seed":
                if not seed_text.strip():
                    missing.append(slot)
                continue
            if slot_payloads.get(slot) in (None, {}, []):
                missing.append(slot)
        if missing:
            raise ValueError(f"required adapter slots missing: {missing}")

    def _merge_contexts(self, *, context: dict[str, Any], constitution: dict[str, Any]) -> dict[str, Any]:
        slot_lookup = {
            "project_context": context,
            "constitution": constitution,
        }
        merged: dict[str, Any] = {}
        merge_order = self.spec.merge_order or ["constitution", "project_context"]
        for slot in merge_order:
            merged.update(slot_lookup.get(slot, {}))
        return merged

    def _collect_slot_packets(self, slot_payloads: dict[str, Any]) -> list[dict[str, Any]]:
        packets: list[dict[str, Any]] = []
        for slot, packet_type in self.spec.packet_slot_map.items():
            payload = slot_payloads.get(slot)
            if payload is None:
                continue
            if isinstance(payload, dict):
                packets.append({"packet_type": packet_type, "payload": payload, "_adapter_slot": slot})
            elif isinstance(payload, list):
                for item in payload:
                    if isinstance(item, dict):
                        packets.append({"packet_type": packet_type, "payload": item, "_adapter_slot": slot})
        return packets

    def _collect_extension_packets(self) -> list[dict[str, Any]]:
        packets: list[dict[str, Any]] = []
        for folder_name in self.spec.extension_packet_folders:
            folder = self.package_root / folder_name
            if not folder.exists():
                continue
            for path in sorted(folder.rglob("*.json")):
                try:
                    payload = json.loads(path.read_text(encoding="utf-8"))
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    payload.setdefault("_adapter_source_path", str(path.relative_to(self.package_root)))
                    packets.append(payload)
                elif isinstance(payload, list):
                    for item in payload:
                        if isinstance(item, dict):
                            item.setdefault("_adapter_source_path", str(path.relative_to(self.package_root)))
                            packets.append(item)
        return packets

    def _normalize_context(self, context: dict[str, Any]) -> dict[str, Any]:
        normalized: dict[str, Any] = {}
        for key, value in context.items():
            normalized[self.spec.context_aliases.get(key, key)] = value
        return normalized

    def _normalize_characters(self, characters: Any) -> list[dict[str, Any]]:
        if not isinstance(characters, list):
            return []
        out: list[dict[str, Any]] = []
        for item in characters:
            if not isinstance(item, dict):
                continue
            mapped = {self.spec.character_field_aliases.get(k, k): v for k, v in item.items()}
            if "display_name" not in mapped and "character_id" in mapped:
                mapped["display_name"] = str(mapped["character_id"])
            out.append(mapped)
        return out

    def _normalize_scenes(self, scenes: Any) -> list[dict[str, Any]]:
        if not isinstance(scenes, list):
            return []
        out: list[dict[str, Any]] = []
        for item in scenes:
            if not isinstance(item, dict):
                continue
            mapped = {self.spec.scene_field_aliases.get(k, k): v for k, v in item.items()}
            if "scene_id" not in mapped and "bundle_id" in mapped:
                mapped["scene_id"] = f"{mapped['bundle_id']}_scene"
            out.append(mapped)
        return out

    def _resolve_slot_path(self, slot_name: str) -> str | None:
        for candidate in self.spec.file_slots.get(slot_name, []):
            path = self.package_root / candidate
            if path.exists():
                return str(path.relative_to(self.package_root))
        return None

    def _read_slot_json(self, slot_name: str, default: Any) -> Any:
        path = self._resolve_existing_slot(slot_name)
        if path is None:
            return default
        if path.suffix.lower() not in {".json"}:
            return default
        return json.loads(path.read_text(encoding="utf-8"))

    def _read_slot_text(self, slot_name: str) -> str | None:
        path = self._resolve_existing_slot(slot_name)
        if path is None:
            return None
        return path.read_text(encoding="utf-8")

    def _resolve_existing_slot(self, slot_name: str) -> Path | None:
        for candidate in self.spec.file_slots.get(slot_name, []):
            path = self.package_root / candidate
            if path.exists():
                return path
        return None

    def _loaded_files_list(self) -> list[str]:
        files = []
        for path in sorted(self.package_root.rglob('*')):
            if path.is_file():
                files.append(str(path.relative_to(self.package_root)))
        return files

    def _collect_text_inputs(self, folder_name: str, default_kind: str, allowed_exts: set[str]) -> list[dict[str, Any]]:
        folder = self.package_root / folder_name
        if not folder.exists():
            return []
        inputs: list[dict[str, Any]] = []
        for path in sorted(folder.rglob('*')):
            if not path.is_file():
                continue
            if path.suffix.lower() not in allowed_exts:
                continue
            if path.suffix.lower() == '.json':
                try:
                    payload = json.loads(path.read_text(encoding='utf-8'))
                except json.JSONDecodeError:
                    payload = None
                if isinstance(payload, dict) and {'kind', 'title', 'text'} <= set(payload.keys()):
                    inputs.append(payload)
                    continue
                if isinstance(payload, list):
                    for item in payload:
                        if isinstance(item, dict) and {'kind', 'title', 'text'} <= set(item.keys()):
                            inputs.append(item)
                    continue
            text = path.read_text(encoding='utf-8').strip()
            if not text:
                continue
            inputs.append({'kind': default_kind, 'title': path.stem, 'text': text})
        return inputs
