from __future__ import annotations

from typing import Any

from literary_system.common.time import utc_now_iso


def build_provenance_record(bundle: dict[str, Any], promotion: dict[str, Any], warnings: list[str]) -> dict[str, Any]:
    return {
        "project_id": bundle["project_id"],
        "trace_id": bundle["trace_id"],
        "written_at": utc_now_iso(),
        "packet_count": len(bundle["packets"]),
        "promotion": promotion,
        "warnings": warnings,
    }
