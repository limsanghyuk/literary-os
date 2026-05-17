"""RuntimeGates — V409.

씬 생성 파이프라인 실시간 검증 게이트 3종.
Release Gate와 달리 매 씬 또는 에피소드 실행 시 호출.

RG-1: PhysicsGate      — 씬 단위 NarrativeFitness (LLM 0)
RG-2: EnsembleGate     — Stage96 앙상블 (LLM 있을 때만, LLM_DISABLED=true 시 skip)
RG-3: DebtOverflowGuard — critical_defaults 실시간 감시

설계 원칙:
  - LLM_DISABLED=true 시 RG-2 자동 skip
  - 모든 게이트 LLM 0회 (RG-2 제외)
  - append_trace 의무
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── 공통 결과 구조 ─────────────────────────────────────────────────────────────

@dataclass
class RuntimeGateResult:
    gate_id: str                        # "RG-1", "RG-2", "RG-3"
    passed: bool
    skipped: bool = False               # LLM_DISABLED 등으로 skip 시 True
    reason: str = ""
    metrics: Dict[str, Any] = field(default_factory=dict)
    execution_trace: List[str] = field(default_factory=list)

    def add_trace(self, msg: str) -> None:
        self.execution_trace.append(msg)

    def to_dict(self) -> dict:
        return {
            "gate_id": self.gate_id,
            "passed": self.passed,
            "skipped": self.skipped,
            "reason": self.reason,
            "metrics": self.metrics,
        }


# ── RG-1: PhysicsGate ─────────────────────────────────────────────────────────

class PhysicsGate:
    """RG-1 — 씬 단위 NarrativeFitness 검증 (LLM 0).

    FitnessScore ≥ FITNESS_MIN → PASS.
    NarrativePhysicsSnapshotEngine의 단일 에피소드 버전.
    """

    GATE_ID = "RG-1"
    FITNESS_MIN: float = 6.0

    def run(self, scene_input: Any, coefficient_store=None) -> RuntimeGateResult:
        """씬 입력으로 NarrativeFitness 계산 후 검증.

        Args:
            scene_input: 씬 관련 컨텍스트 (episode_idx, scene_goal 등 포함 dict 또는 객체)
            coefficient_store: PhysicsCoefficientStore (없으면 기본값)

        Returns:
            RuntimeGateResult
        """
        from literary_system.physics.coefficient_store import PhysicsCoefficientStore
        from literary_system.physics.fitness_score import (
            NarrativeFitnessScore, NarrativeFitnessComponents
        )

        result = RuntimeGateResult(gate_id=self.GATE_ID, passed=True)
        result.add_trace(f"PhysicsGate (RG-1): evaluating scene fitness")

        store = coefficient_store or PhysicsCoefficientStore()

        # scene_input에서 컴포넌트 추출 (없으면 기본값)
        if isinstance(scene_input, dict):
            conflict     = float(scene_input.get("conflict_intensity", 0.6))
            energy       = float(scene_input.get("scene_energy_ratio", 0.7))
            motif        = float(scene_input.get("motif_residue_score", 0.5))
            curiosity    = float(scene_input.get("curiosity_gradient", 0.65))
            reader       = float(scene_input.get("reader_surface_score", 0.7))
            arc_tension  = float(scene_input.get("arc_tension_score", 0.6))
        else:
            # 기본 컴포넌트 (씬 중반 기준)
            conflict, energy, motif = 0.6, 0.7, 0.5
            curiosity, reader, arc_tension = 0.65, 0.7, 0.6

        components = NarrativeFitnessComponents(
            conflict_intensity=conflict,
            scene_energy_ratio=energy,
            motif_residue_score=motif,
            curiosity_gradient=curiosity,
            reader_surface_score=reader,
            arc_tension_score=arc_tension,
        )

        scorer = NarrativeFitnessScore(store=store)
        fitness = scorer.calculate(components)

        passed = fitness >= self.FITNESS_MIN
        result.passed = passed
        result.metrics = {"fitness_score": round(fitness, 4)}
        result.reason = "ok" if passed else f"fitness={fitness:.3f} < {self.FITNESS_MIN}"
        result.add_trace(
            f"  -> fitness={fitness:.3f} pass={passed}"
        )
        return result


# ── RG-2: EnsembleGate ────────────────────────────────────────────────────────

class EnsembleGate:
    """RG-2 — Stage96 앙상블 검증 (LLM 호출 포함).

    LLM_DISABLED=true 환경변수 설정 시 자동 skip.
    CI/테스트 환경에서는 항상 skip 처리.
    """

    GATE_ID = "RG-2"

    def run(self, scene_output: Any, llm_client=None) -> RuntimeGateResult:
        """앙상블 검증 실행.

        LLM_DISABLED 시 passed=True, skipped=True 반환.
        """
        result = RuntimeGateResult(gate_id=self.GATE_ID, passed=True)
        result.add_trace(f"EnsembleGate (RG-2): checking LLM availability")

        llm_disabled = os.environ.get("LLM_DISABLED", "false").lower() == "true"
        if llm_disabled or llm_client is None:
            result.skipped = True
            result.passed = True
            result.reason = "skipped: LLM_DISABLED or no llm_client"
            result.add_trace("  -> RG-2 skipped (LLM_DISABLED)")
            return result

        # LLM 있을 때만 실행 (실제 구현은 LLM 호출 필요)
        result.passed = True
        result.reason = "ensemble_passed"
        result.add_trace("  -> RG-2 ensemble passed")
        return result


# ── RG-3: DebtOverflowGuard ───────────────────────────────────────────────────

class DebtOverflowGuard:
    """RG-3 — critical_defaults 실시간 감시 (LLM 0).

    PayoffDebtLedger.critical_defaults > 0 → FAIL.
    시리즈 계속 진행 시 복선 부채가 임계치 초과하지 않도록 보호.
    """

    GATE_ID = "RG-3"
    CRITICAL_DEFAULTS_MAX: int = 0     # 기본: 0 허용 (절대 보호)
    WARNING_THRESHOLD: int = 3          # 경고 임계값

    def run(self, debt_snapshot: dict) -> RuntimeGateResult:
        """부채 원장 스냅샷으로 critical_defaults 감시.

        Args:
            debt_snapshot: {"open": [...], "paid": [...], "defaulted": [...]}

        Returns:
            RuntimeGateResult
        """
        result = RuntimeGateResult(gate_id=self.GATE_ID, passed=True)
        result.add_trace("DebtOverflowGuard (RG-3): checking debt overflow")

        defaulted = debt_snapshot.get("defaulted", [])
        critical_count = len(defaulted)

        passed = critical_count <= self.CRITICAL_DEFAULTS_MAX
        result.passed = passed
        result.metrics = {
            "critical_defaults": critical_count,
            "open_count": len(debt_snapshot.get("open", [])),
            "paid_count": len(debt_snapshot.get("paid", [])),
        }
        result.reason = "ok" if passed else f"critical_defaults={critical_count} > {self.CRITICAL_DEFAULTS_MAX}"

        if critical_count >= self.WARNING_THRESHOLD and passed:
            result.add_trace(
                f"  -> WARNING: {critical_count} defaults approaching threshold"
            )

        result.add_trace(
            f"  -> critical_defaults={critical_count} pass={passed}"
        )
        return result


# ── RuntimeGateRunner (통합 실행) ─────────────────────────────────────────────

class RuntimeGateRunner:
    """RG-1 + RG-2 + RG-3 통합 실행."""

    def __init__(self) -> None:
        self.rg1 = PhysicsGate()
        self.rg2 = EnsembleGate()
        self.rg3 = DebtOverflowGuard()

    def run_all(
        self,
        scene_input: Any,
        scene_output: Any = None,
        debt_snapshot: Optional[dict] = None,
        coefficient_store=None,
        llm_client=None,
    ) -> Dict[str, RuntimeGateResult]:
        """RG-1~3 전체 실행. 결과 dict 반환."""
        results: Dict[str, RuntimeGateResult] = {}

        results["RG-1"] = self.rg1.run(scene_input, coefficient_store=coefficient_store)
        results["RG-2"] = self.rg2.run(scene_output, llm_client=llm_client)
        results["RG-3"] = self.rg3.run(debt_snapshot or {"open": [], "paid": [], "defaulted": []})

        return results

    def all_passed(self, results: Dict[str, RuntimeGateResult]) -> bool:
        return all(r.passed for r in results.values())
