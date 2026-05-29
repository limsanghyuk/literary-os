from __future__ import annotations

from literary_system.storage.base import JsonStore


class FewshotRegistry(JsonStore):
    def __init__(self, root: str = "./out/fewshot") -> None:
        super().__init__(root, "fewshot_registry.json")
