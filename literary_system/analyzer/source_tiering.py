from __future__ import annotations

from typing import Any

from literary_system.common.enums import SourceTier


_KIND_TO_TIER = {
    "canon": SourceTier.T0.value,
    "project_doc": SourceTier.T1.value,
    "reference": SourceTier.T2.value,
    "critique": SourceTier.T3.value,
}


def assign_source_tiers(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    assigned = []
    for record in records:
        clone = dict(record)
        clone["source_tier"] = clone.get("source_tier") or _KIND_TO_TIER.get(clone.get("kind"), SourceTier.T1.value)
        assigned.append(clone)
    return assigned
