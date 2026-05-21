"""
literary_system/corpus — ExternalCorpusBridge (Stage B SP2)
V557~V561: CorpusIngestor · CorpusValidator · BGEM3Embedder · CIMBootstrap · Gate30
"""

from .bgem3_embedder import BGEM3Embedder
from .cim_bootstrap import BootstrapReport, CIMBootstrap
from .corpus_ingestor import CorpusIngestor, IngestReport, ScenarioEntry
from .corpus_validator import CorpusValidator, ValidationResult

__all__ = [
    "CorpusIngestor", "ScenarioEntry", "IngestReport",
    "CorpusValidator", "ValidationResult",
    "BGEM3Embedder",
    "CIMBootstrap", "BootstrapReport",
]

# SP-A.5 (V592) 추가
from .corpus_ingestor import (
    CorpusEntry,
    CorpusFallbackOption,
    CorpusFallbackPipeline,
    PublicDomainIngestor,
    SyntheticCorpusIngestor,
    AcademicCorpusIngestor,
)
from .provenance_index import CorpusProvenanceIndex, CorpusProvenanceRecord
from .corpus_pii_filter import CorpusPiiFilter, CorpusPiiMatch

__all__ += [
    "CorpusEntry", "CorpusFallbackOption", "CorpusFallbackPipeline",
    "PublicDomainIngestor", "SyntheticCorpusIngestor", "AcademicCorpusIngestor",
    "CorpusProvenanceIndex", "CorpusProvenanceRecord",
    "CorpusPiiFilter", "CorpusPiiMatch",
]

# SP-A.6 (V593) — CorpusEntryValidator + CorpusDatasetCardGenerator
from literary_system.corpus.corpus_validator import (
    CorpusEntryValidationResult,
    CorpusEntryValidationReport,
    CorpusEntryValidator,
    CorpusMinHashDedup,
)
from literary_system.corpus.dataset_card_generator import (
    CorpusDatasetCard,
    CorpusDatasetCardGenerator,
)
