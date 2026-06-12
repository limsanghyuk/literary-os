"""
literary_system.validation — 공식 생애주기 상설 인프라 (WP-1, V747)

공개 API:
  FormulaEntry, SceneRow, REGISTRY      ← formula_registry
  STAGES                                ← stage_registry
  Harness, StageReport, FormulaResult   ← formula_harness
  record, transition, get_lifecycle     ← ledger
"""
from literary_system.validation.formula_registry import (
    FormulaEntry,
    SceneRow,
    REGISTRY,
)
from literary_system.validation.stage_registry import STAGES
from literary_system.validation.formula_harness import (
    Harness,
    StageReport,
    FormulaResult,
)
from literary_system.validation.ledger import (
    record,
    transition,
    get_lifecycle,
)

__all__ = [
    "FormulaEntry",
    "SceneRow",
    "REGISTRY",
    "STAGES",
    "Harness",
    "StageReport",
    "FormulaResult",
    "record",
    "transition",
    "get_lifecycle",
]
