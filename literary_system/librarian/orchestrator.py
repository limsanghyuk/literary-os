from __future__ import annotations

from pathlib import Path
from typing import Any

from literary_system.common.logging import get_logger
from literary_system.librarian.authority_control import AuthorityController
from literary_system.librarian.catalog_builder import build_catalog
from literary_system.librarian.contract_validator import ContractValidator
from literary_system.librarian.drift_alarm import detect_state_drift
from literary_system.librarian.duplication_checker import check_duplicates
from literary_system.librarian.promotion_engine import PromotionEngine
from literary_system.librarian.provenance_writer import build_provenance_record
from literary_system.librarian.storage_dispatcher import StorageDispatcher


class ChiefLibrarian:
    def __init__(self, out_root: str | Path = "./out") -> None:
        self.logger = get_logger(self.__class__.__name__)
        self.validator = ContractValidator()
        self.authority_controller = AuthorityController()
        self.promotion_engine = PromotionEngine()
        self.dispatcher = StorageDispatcher(out_root)

    def ingest(self, packet_bundle: dict[str, Any]) -> dict[str, Any]:
        self.validator.validate_bundle(packet_bundle)
        normalized = self.authority_controller.normalize_bundle(packet_bundle)
        warnings = check_duplicates(normalized)
        catalog = build_catalog(normalized)
        promotion = self.promotion_engine.decide(normalized, catalog)
        alarms = detect_state_drift(normalized)
        provenance = build_provenance_record(normalized, promotion, warnings)
        receipts = self.dispatcher.dispatch(normalized, catalog, promotion, provenance)

        report = {
            "project_id": normalized["project_id"],
            "trace_id": normalized["trace_id"],
            "ingested_packet_count": len(normalized.get("packets", [])),
            "promotion": promotion,
            "warnings": warnings,
            "alarms": alarms,
            "receipts": receipts,
            "catalog_counts": {
                "characters": len(catalog["characters"]),
                "scenes": len(catalog["scenes"]),
                "motifs": len(catalog["motifs"]),
                "relations": len(catalog["relations"]),
            },
        }
        self.logger.info("ingested project %s", normalized["project_id"])
        return report
