"""
literary_system/corpus — ExternalCorpusBridge (Stage B SP2)
V557~V561: CorpusIngestor · CorpusValidator · BGEM3Embedder · CIMBootstrap · Gate30
"""

from .corpus_ingestor import CorpusIngestor, ScenarioEntry, IngestReport
from .corpus_validator import CorpusValidator, ValidationResult
from .bgem3_embedder import BGEM3Embedder
from .cim_bootstrap import CIMBootstrap, BootstrapReport

__all__ = [
    "CorpusIngestor", "ScenarioEntry", "IngestReport",
    "CorpusValidator", "ValidationResult",
    "BGEM3Embedder",
    "CIMBootstrap", "BootstrapReport",
]
