from __future__ import annotations

from typing import Any

from literary_system.common.time import utc_now_iso


def make_envelope(
    project_id: str,
    packet_type: str,
    provenance: dict[str, Any],
    payload: dict[str, Any],
    schema_version: str = "v1",
) -> dict[str, Any]:
    return {
        "schema_version": schema_version,
        "project_id": project_id,
        "packet_type": packet_type,
        "created_at": utc_now_iso(),
        "provenance": provenance,
        "payload": payload,
    }
