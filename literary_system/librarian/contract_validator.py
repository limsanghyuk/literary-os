from __future__ import annotations

from typing import Any

from literary_system.schemas.cross_packet import validate_invariants
from literary_system.schemas.validator import PacketValidator


class ContractValidator:
    def __init__(self) -> None:
        self.packet_validator = PacketValidator()

    def validate_bundle(self, bundle: dict[str, Any]) -> None:
        for packet in bundle["packets"]:
            self.packet_validator.validate_packet(packet)
        validate_invariants(bundle)
