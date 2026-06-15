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
from literary_system.validation.human_gt import (
    GTMode,
    GTPair,
    GTRecord,
    build_blind_sheet,
    record_from_sheet,
    aggregate_winrate,
    inter_rater_alpha,
    panel_alignment,
    run_g_human_gt_alignment,
    HUMAN_GT_ALPHA_MIN,
)

__all__ = [
    "GTMode", "GTPair", "GTRecord", "build_blind_sheet", "record_from_sheet",
    "aggregate_winrate", "inter_rater_alpha", "panel_alignment",
    "run_g_human_gt_alignment", "HUMAN_GT_ALPHA_MIN",
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
