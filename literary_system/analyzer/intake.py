from __future__ import annotations

from typing import Any

from literary_system.analyzer.text_analysis import normalize_text
from literary_system.common.ids import make_id


def ingest_inputs(inputs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for item in inputs:
        text = normalize_text(str(item.get("text", "")))
        records.append({
            "source_id": item.get("source_id") or make_id("src"),
            "kind": item.get("kind", "unknown"),
            "title": item.get("title", ""),
            "text": text,
            "meta": item.get("meta", {}),
        })
    return records
