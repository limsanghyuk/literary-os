from __future__ import annotations

from pathlib import Path
from typing import Any

from literary_system.retrieval.card_builder import build_scene_cards, build_vector_cards
from literary_system.storage.catalog_store import CatalogStore
from literary_system.storage.fewshot_registry import FewshotRegistry
from literary_system.storage.provenance_ledger import ProvenanceLedger
from literary_system.storage.raw_archive import RawArchiveStore
from literary_system.storage.relation_graph_store import RelationGraphStore
from literary_system.storage.vector_store import VectorStore


class StorageDispatcher:
    def __init__(self, root: str | Path = "./out") -> None:
        self.root = Path(root)

    def dispatch(
        self,
        bundle: dict[str, Any],
        catalog: dict[str, Any],
        promotion: dict[str, Any],
        provenance: dict[str, Any],
    ) -> dict[str, str]:
        receipts = {}
        receipts["raw_bundle"] = RawArchiveStore(self.root / "raw").write(bundle)
        receipts["catalog"] = CatalogStore(self.root / "catalog").write(catalog)
        receipts["relations"] = RelationGraphStore(self.root / "graph").write({"relations": catalog["relations"]})
        receipts["vector_cards"] = VectorStore(self.root / "vector").append_jsonl(build_vector_cards(bundle))
        receipts["fewshot_registry"] = FewshotRegistry(self.root / "fewshot").write({"promotion": promotion, "project_id": bundle["project_id"]})
        receipts["provenance"] = ProvenanceLedger(self.root / "provenance").write(provenance)
        return receipts
