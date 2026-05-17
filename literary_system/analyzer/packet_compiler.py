from __future__ import annotations

from typing import Any, Iterable

from literary_system.common.enums import PacketType
from literary_system.common.ids import make_id
from literary_system.common.provenance import make_provenance
from literary_system.schemas.envelope import make_envelope


ANALYZER_VERSION = "1.0.0"


def compile_packets(project_id: str, packets: Iterable[tuple[str, dict[str, Any]]], source_tiers: list[str]) -> dict[str, Any]:
    trace_id = make_id("trace")
    provenance = make_provenance(
        generator="standard_literary_analyzer",
        generator_version=ANALYZER_VERSION,
        source_tiers=source_tiers,
        trace_id=trace_id,
    )
    bundle_packets = [make_envelope(project_id=project_id, packet_type=p_type, provenance=provenance, payload=payload)
                      for p_type, payload in packets]
    return {
        "bundle_id": make_id("bundle"),
        "project_id": project_id,
        "trace_id": trace_id,
        "packets": bundle_packets,
        "motif_catalog": sorted({p["payload"]["motif"] for p in bundle_packets if p["packet_type"] == PacketType.RESIDUE_VARIATION_PLAN.value}),
    }
