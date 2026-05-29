from __future__ import annotations

from typing import Any

from literary_system.analyzer.text_analysis import scene_features_from_text, split_into_candidate_scenes


def build_scene_digests(
    project_context: dict[str, Any],
    source_records: list[dict[str, Any]] | None = None,
    ledgers: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    if project_context.get("scenes"):
        digests = []
        ledger_ids = {entry["display_name"]: entry["character_id"] for entry in (ledgers or [])}
        for idx, scene in enumerate(project_context.get("scenes", []), start=1):
            text = scene.get("raw_text") or scene.get("scene_text") or ""
            features = scene_features_from_text(
                source_refs=scene.get("source_refs", []),
                text=text,
                character_names=ledger_ids.keys(),
                explicit_motifs=scene.get("motifs"),
                explicit_axes=scene.get("active_tension_axes"),
            )
            active_from_mentions = [ledger_ids[name] for name in features.mentioned_characters if name in ledger_ids]
            active_characters = scene.get("active_characters") or active_from_mentions
            digests.append({
                "scene_id": scene.get("scene_id") or f"scene_{idx:02d}",
                "bundle_id": scene.get("bundle_id", "bundle_001"),
                "scene_goal": scene.get("scene_goal") or (features.tension_axes[0] if features.tension_axes else "scene_progression"),
                "scene_focus": scene.get("scene_focus") or (features.motifs[0] if features.motifs else "interaction"),
                "continuity_notes": scene.get("continuity_notes", []),
                "active_characters": active_characters,
                "active_tension_axes": scene.get("active_tension_axes") or features.tension_axes,
                "continuity_risks": scene.get("continuity_risks", []),
                "raw_text": features.raw_text,
                "source_refs": features.source_refs,
                "detected_motifs": features.motifs,
                "detected_speakers": features.speakers,
                "quoted_turns": features.quoted_turns,
            })
        return digests

    records = source_records or []
    display_to_id = {entry["display_name"]: entry["character_id"] for entry in (ledgers or [])}
    digests = []
    idx = 0
    for rec in records:
        for chunk in split_into_candidate_scenes(rec.get("text", "")):
            idx += 1
            features = scene_features_from_text(
                source_refs=[{"source_id": rec["source_id"], "title": rec.get("title", "")}],
                text=chunk,
                character_names=display_to_id.keys(),
            )
            active = [display_to_id[name] for name in features.mentioned_characters if name in display_to_id]
            digests.append({
                "scene_id": f"scene_{idx:02d}",
                "bundle_id": f"bundle_{((idx - 1) // 3) + 1:03d}",
                "scene_goal": features.tension_axes[0] if features.tension_axes else "scene_progression",
                "scene_focus": features.motifs[0] if features.motifs else "interaction",
                "continuity_notes": [rec.get("title", "")],
                "active_characters": active,
                "active_tension_axes": features.tension_axes,
                "continuity_risks": ["sparse_context"] if len(features.tokens) < 8 else [],
                "raw_text": features.raw_text,
                "source_refs": features.source_refs,
                "detected_motifs": features.motifs,
                "detected_speakers": features.speakers,
                "quoted_turns": features.quoted_turns,
            })
    return digests
