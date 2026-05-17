from __future__ import annotations

from typing import Iterable

from literary_system.common.time import utc_now_iso


def make_provenance(
    generator: str,
    generator_version: str,
    source_tiers: Iterable[str],
    trace_id: str,
) -> dict:
    return {
        "generator": generator,
        "generator_version": generator_version,
        "source_tiers": list(source_tiers),
        "trace_id": trace_id,
        "created_at": utc_now_iso(),
    }
