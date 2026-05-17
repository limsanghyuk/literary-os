from __future__ import annotations

from typing import Any

from literary_system.common.errors import SchemaValidationError
from literary_system.schemas.definitions import COMMON_ENVELOPE_REQUIRED, ENUM_FIELDS, PACKET_REQUIRED_FIELDS


class PacketValidator:
    def validate_envelope(self, packet: dict[str, Any]) -> None:
        missing = COMMON_ENVELOPE_REQUIRED - packet.keys()
        if missing:
            raise SchemaValidationError("SCHEMA_MISSING_REQUIRED", f"missing envelope fields: {sorted(missing)}")
        if not isinstance(packet["payload"], dict):
            raise SchemaValidationError("SCHEMA_INVALID_TYPE", "payload must be object")
        if not isinstance(packet["provenance"], dict):
            raise SchemaValidationError("SCHEMA_INVALID_TYPE", "provenance must be object")

    def validate_packet(self, packet: dict[str, Any]) -> None:
        self.validate_envelope(packet)
        packet_type = packet["packet_type"]
        payload = packet["payload"]
        required = PACKET_REQUIRED_FIELDS.get(packet_type, set())
        missing = required - payload.keys()
        if missing:
            raise SchemaValidationError("SCHEMA_MISSING_REQUIRED", f"{packet_type} missing: {sorted(missing)}")
        enums = ENUM_FIELDS.get(packet_type, {})
        for field, allowed in enums.items():
            if field in payload and payload[field] not in allowed:
                raise SchemaValidationError("SCHEMA_INVALID_ENUM", f"{packet_type}.{field}={payload[field]!r}")
        self._validate_ranges(packet_type, payload)

    def _validate_ranges(self, packet_type: str, payload: dict[str, Any]) -> None:
        for field in ("pdi_profile", "memory_weight", "intensity"):
            if field in payload:
                value = payload[field]
                if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
                    raise SchemaValidationError("SCHEMA_RANGE_ERROR", f"{packet_type}.{field} out of range")
        for field in ("SP", "RU", "RT", "AC", "RO", "MR", "reader_trust", "reader_afterimage"):
            if field in payload:
                value = payload[field]
                if not isinstance(value, (int, float)) or not 0.0 <= float(value) <= 1.0:
                    raise SchemaValidationError("SCHEMA_RANGE_ERROR", f"{packet_type}.{field} out of range")
        if "ET" in payload:
            value = payload["ET"]
            if not isinstance(value, (int, float)) or not -1.0 <= float(value) <= 1.0:
                raise SchemaValidationError("SCHEMA_RANGE_ERROR", f"{packet_type}.ET out of range")
        if "RD" in payload:
            rd = payload["RD"]
            if not isinstance(rd, dict) or "aggregate" not in rd:
                raise SchemaValidationError("STATE_SNAPSHOT_INCOMPLETE", "RD.aggregate required")
            agg = rd["aggregate"]
            if not isinstance(agg, (int, float)) or not 0.0 <= float(agg) <= 1.0:
                raise SchemaValidationError("SCHEMA_RANGE_ERROR", f"{packet_type}.RD.aggregate out of range")
