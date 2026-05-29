from __future__ import annotations

from literary_system.storage.base import JsonStore


class RawArchiveStore(JsonStore):
    def __init__(self, root: str = "./out/raw") -> None:
        super().__init__(root, "raw_bundle.json")
