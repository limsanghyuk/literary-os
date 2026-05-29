from __future__ import annotations

from typing import Any


def latest_briefing(bundle: dict[str, Any]) -> dict[str, Any] | None:
    briefings = [p["payload"] for p in bundle["packets"] if p["packet_type"] == "commander_briefing"]
    return briefings[-1] if briefings else None
