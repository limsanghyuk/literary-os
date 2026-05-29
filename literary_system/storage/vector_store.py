from __future__ import annotations

from literary_system.storage.base import JsonStore


class VectorStore(JsonStore):
    def __init__(self, root: str = "./out/vector") -> None:
        super().__init__(root, "vector_cards.jsonl")
