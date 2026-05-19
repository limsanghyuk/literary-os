from __future__ import annotations

import json
from pathlib import Path

from .slot_registry import SLOT_REGISTRY, normalize_slot_name

TEXT_SUFFIXES = {'.json', '.md', '.txt'}

def _slot_for_path(path: Path) -> str | None:
    stem = path.stem.lower().replace('-', '_')
    direct = normalize_slot_name(stem)
    if direct:
        return direct
    parent = normalize_slot_name(path.parent.name)
    if parent in {"sources", "notes", "packets", "extensions"}:
        return parent
    return None

def design_adapter_spec(project_root: str | Path) -> dict:
    root = Path(project_root)
    discovered: dict[str, list[str]] = {k: [] for k in SLOT_REGISTRY.keys()}
    for p in root.rglob('*'):
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_SUFFIXES:
            continue
        rel = p.relative_to(root).as_posix()
        slot = _slot_for_path(p)
        if slot:
            discovered.setdefault(slot, []).append(rel)
    file_slots = {k: v for k, v in discovered.items() if v}
    required_slots = [s for s in ["project_context", "constitution", "characters", "scenes", "seed"] if s in file_slots]
    return {
        "schema_version": "adapter_spec_v1",
        "project_package_mode": "creative_engine",
        "required_slots": required_slots,
        "file_slots": file_slots,
        "merge_order": ["seed", "project_context", "constitution", "characters", "scenes", "sources", "notes", "packets", "extensions"],
        "packet_slot_map": {
            "seed": "intent_seed_packet",
            "constitution": "format_constitution_packet",
            "characters": "character_ledger",
            "scenes": "scene_digest"
        }
    }

def write_generated_spec(project_root: str | Path, out_name: str = 'adapter_spec.generated.json') -> Path:
    root = Path(project_root)
    spec = design_adapter_spec(root)
    out = root / out_name
    out.write_text(json.dumps(spec, ensure_ascii=False, indent=2), encoding='utf-8')
    return out
