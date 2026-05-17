from __future__ import annotations

from literary_system.storage.base import JsonStore


class CatalogStore(JsonStore):
    def __init__(self, root: str = "./out/catalog") -> None:
        super().__init__(root, "catalog.json")
