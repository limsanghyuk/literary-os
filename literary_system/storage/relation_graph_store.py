from __future__ import annotations

from literary_system.storage.base import JsonStore


class RelationGraphStore(JsonStore):
    def __init__(self, root: str = "./out/graph") -> None:
        super().__init__(root, "relations.json")
