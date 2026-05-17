"""V360: PlanBuildGate v2 — WorkDeclaration + GUARDRAILS 통합."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from literary_system.gdap.guardrails import NKGGuardrails, GuardrailViolation, GuardrailCheck
from literary_system.gdap.blast_radius import BlastRadiusCalculator, BlastRadius

@dataclass
class WorkDeclaration:
    target_files:         List[str] = field(default_factory=list)
    preserved_files:      List[str] = field(default_factory=list)
    shared_nodes:         List[str] = field(default_factory=list)
    impact_analysis_run:  bool  = False
    rename_requested:     bool  = False
    dry_run_completed:    bool  = False
    multi_scene_edit:     bool  = False
    changes_detected:     bool  = False
    semantic_frozen:      bool  = False
    max_blast_ratio:      float = 0.30

@dataclass
class GateResult:
    passed:   bool
    checks:   List[GuardrailCheck]
    violations: List[str]
    blast:    Optional[BlastRadius] = None

class PlanBuildGate:
    def __init__(self, blast_calc: Optional[BlastRadiusCalculator] = None) -> None:
        self._blast_calc = blast_calc

    def validate(self, decl: WorkDeclaration, blast: Optional[BlastRadius] = None) -> GateResult:
        if blast is None and self._blast_calc:
            blast = self._blast_calc.calculate(decl.target_files)
        blast_ratio = blast.blast_ratio if blast else 0.0
        violations = []
        for f in decl.preserved_files:
            if f in decl.target_files: violations.append(f"보존 파일 수정 불가: {f}")
        try:
            checks = NKGGuardrails.run_all(
                impact_analysis_run=decl.impact_analysis_run,
                target_nodes=decl.target_files,
                shared_nodes=decl.shared_nodes,
                rename_requested=decl.rename_requested,
                dry_run_completed=decl.dry_run_completed,
                blast_ratio=blast_ratio,
                is_frozen=decl.semantic_frozen,
                multi_scene_edit=decl.multi_scene_edit,
                changes_detected=decl.changes_detected,
                blast_threshold=decl.max_blast_ratio,
                raise_on_violation=False,
            )
        except GuardrailViolation as e:
            checks = []; violations.append(str(e))
        for c in checks:
            if not c.passed: violations.append(c.message)
        return GateResult(passed=len(violations) == 0, checks=checks,
                          violations=violations, blast=blast)
