from __future__ import annotations

from literary_system.storage.base import JsonStore


class ProvenanceLedger(JsonStore):
    def __init__(self, root: str = "./out/provenance") -> None:
        super().__init__(root, "provenance.json")
