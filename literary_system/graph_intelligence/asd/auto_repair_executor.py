"""
AutoRepairExecutor — V544
===========================
Literary OS Phase 5 ASD SP1

StoryDoctorOrchestrator 의 RepairRecommendation 을 받아
PlanBuildProtocol(Gate26 + Gate27)을 통과한 경우에만 수리를 실행한다.

수리 실행 방식
--------------
RepairCategory → PatchType 매핑
  RESOLVE_SECRET / FIX_FORESHADOW → EDIT
  REVIVE_THREAD / ARC_TRACKING / ARC_POST_DEATH
  / ARC_CONTRADICTION / ARC_INVERSION       → EDIT

실제 그래프 변이(graph mutation)는 repair_fn 콜백에 위임한다.
콜백이 없으면 dry_run 모드(Gate만 통과 여부 확인).

LLM-0: 외부 호출 없음.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Dict, List, Optional

from ..narrative_graph_store import NarrativeGraphStore
from ..scene_change_pre_gate import SceneChangePreGate
from ..sp2.code_dependency_graph import CodeDependencyGraph
from ..sp2.gate27 import Gate27
from ..sp2.plan_build_protocol import PlanBuildProtocol, ProtocolResult
from ..sp2.stage_patch_impact_calculator import (
    PatchType,
    StagePatchImpactCalculator,
    StagePatchRequest,
)
from .story_doctor_orchestrator import RepairCategory, RepairRecommendation

# 콜백 타입: (recommendation) → bool (성공 여부)
RepairFn = Callable[[RepairRecommendation], bool]


class ExecutionStatus(str, Enum):
    APPROVED   = "approved"    # Gate 통과 + repair_fn 성공
    DRY_RUN    = "dry_run"     # Gate 통과 + repair_fn 없음
    GATE_FAIL  = "gate_fail"   # Gate 차단
    PLAN_ABORT = "plan_abort"  # PLAN 단계 combined_risk >= threshold
    ERROR      = "error"       # 예외 발생


@dataclass
class ExecutionResult:
    recommendation_id: str
    scene_id:          str
    status:            ExecutionStatus
    protocol_result:   Optional[ProtocolResult] = None
    repair_success:    Optional[bool]            = None
    error_message:     str                       = ""

    def ok(self) -> bool:
        return self.status in (ExecutionStatus.APPROVED, ExecutionStatus.DRY_RUN)


@dataclass
class BatchExecutionResult:
    total:             int
    approved:          int
    dry_run:           int
    gate_failed:       int
    plan_aborted:      int
    errors:            int
    results:           List[ExecutionResult] = field(default_factory=list)

    def success_rate(self) -> float:
        ok = self.approved + self.dry_run
        return round(ok / max(self.total, 1), 4)


# Category → PatchType
_CAT_TO_PATCH: Dict[RepairCategory, PatchType] = {
    RepairCategory.RESOLVE_SECRET:    PatchType.EDIT,
    RepairCategory.FIX_FORESHADOW:    PatchType.EDIT,
    RepairCategory.REVIVE_THREAD:     PatchType.EDIT,
    RepairCategory.ARC_TRACKING:      PatchType.EDIT,
    RepairCategory.ARC_POST_DEATH:    PatchType.EDIT,
    RepairCategory.ARC_CONTRADICTION: PatchType.EDIT,
    RepairCategory.ARC_INVERSION:     PatchType.EDIT,
}


class AutoRepairExecutor:
    """
    Parameters
    ----------
    store : NarrativeGraphStore
    code_dep : CodeDependencyGraph
        빌드된 상태의 CodeDependencyGraph.
    abort_threshold : float
        PlanBuildProtocol abort 기준 combined_risk (default 0.90).
    repair_fn : RepairFn | None
        실제 그래프 변이 콜백. None 이면 dry_run.
    """

    def __init__(
        self,
        store: NarrativeGraphStore,
        code_dep: CodeDependencyGraph,
        *,
        abort_threshold: float = 0.90,
        repair_fn: Optional[RepairFn] = None,
    ) -> None:
        self._store     = store
        self._repair_fn = repair_fn

        gate26      = SceneChangePreGate(store)  # Bug-1 fix: store 직접 전달 (SceneChangePreGate가 내부적으로 analyzer 생성)
        calculator  = StagePatchImpactCalculator(store, code_dep)
        gate27      = Gate27(code_dep, calculator)
        self._protocol = PlanBuildProtocol(
            gate26, gate27, calculator,
            abort_threshold=abort_threshold,
        )

    # ------------------------------------------------------------------
    def execute(self, rec: RepairRecommendation) -> ExecutionResult:
        """단일 RepairRecommendation 을 실행한다."""
        patch_type = _CAT_TO_PATCH.get(rec.category, PatchType.EDIT)
        request    = StagePatchRequest(
            scene_id    = rec.node_id,
            patch_type  = patch_type,
            description = f"ASD repair: {rec.category.value} — {rec.label}",
        )

        try:
            prot_result = self._protocol.run(
                request,
                build_fn=(
                    (lambda sid, pt: bool(self._repair_fn(rec)))
                    if self._repair_fn else None
                ),
            )
        except Exception as exc:
            return ExecutionResult(
                recommendation_id = rec.recommendation_id,
                scene_id          = rec.node_id,
                status            = ExecutionStatus.ERROR,
                error_message     = str(exc),
            )

        if not prot_result.approved:
            status = (
                ExecutionStatus.PLAN_ABORT
                if prot_result.abort_reason.startswith("PLAN")
                else ExecutionStatus.GATE_FAIL
            )
            return ExecutionResult(
                recommendation_id = rec.recommendation_id,
                scene_id          = rec.node_id,
                status            = status,
                protocol_result   = prot_result,
            )

        # Gate 통과
        if self._repair_fn is None:
            return ExecutionResult(
                recommendation_id = rec.recommendation_id,
                scene_id          = rec.node_id,
                status            = ExecutionStatus.DRY_RUN,
                protocol_result   = prot_result,
                repair_success    = None,
            )

        # repair_fn 이미 build_fn 으로 호출됨 → approved == True
        return ExecutionResult(
            recommendation_id = rec.recommendation_id,
            scene_id          = rec.node_id,
            status            = ExecutionStatus.APPROVED,
            protocol_result   = prot_result,
            repair_success    = True,
        )

    def execute_batch(
        self,
        recommendations: List[RepairRecommendation],
    ) -> BatchExecutionResult:
        """우선순위 순서대로 목록 전체를 실행한다."""
        results: List[ExecutionResult] = []
        for rec in recommendations:
            results.append(self.execute(rec))

        approved    = sum(1 for r in results if r.status == ExecutionStatus.APPROVED)
        dry_run     = sum(1 for r in results if r.status == ExecutionStatus.DRY_RUN)
        gate_failed = sum(1 for r in results if r.status == ExecutionStatus.GATE_FAIL)
        plan_aborted= sum(1 for r in results if r.status == ExecutionStatus.PLAN_ABORT)
        errors      = sum(1 for r in results if r.status == ExecutionStatus.ERROR)

        return BatchExecutionResult(
            total        = len(results),
            approved     = approved,
            dry_run      = dry_run,
            gate_failed  = gate_failed,
            plan_aborted = plan_aborted,
            errors       = errors,
            results      = results,
        )
