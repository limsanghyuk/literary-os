"""
V320: E2ELoopOrchestrator
Phase 2 — End-to-End 루프 오케스트레이터.

전체 데이터 흐름 (최종 설계도 반영):

  Layer 1 (LLM 0회):
    SeedCompiler → TrajectoryFamilyInterpolator → PromptAssembler → bundle.json

  Layer 0 (LLM 호출):
    V312Bridge → run_sovereign_v312() → render_output + literary_state_after

  Layer 2 (LLM 0회):
    ReaderSimulator → ConditionalLLMGate
      ✅ PASS → commit
      🔧 PATCH_ONLY → SpecializedLocalPatch → 재판정
      🔁 RERENDER → V312Bridge 재실행

  Layer 1 (LLM 0회):
    TemporalCoherenceEngine → CausalContinuationPlan → TraceDatasetStore

이것이 V320의 핵심 — 최초 End-to-End 루프 완성.
LLM은 렌더링에만, 모든 판정은 로컬.
"""
from __future__ import annotations

import logging
import time

logger = logging.getLogger(__name__)
from dataclasses import dataclass, field
from typing import Any

from literary_system.compiler.v312_bridge import V312Bridge
from literary_system.gate.conditional_llm_gate import ConditionalLLMGate, GateDecision, GateResult
from literary_system.llm_bridge.llm_bridge_interface import LLMBridgeInterface
from literary_system.render_loop.specialized_patch import SpecializedLocalPatchEngine
from literary_system.trace.trace_dataset_store import TraceDatasetStore
from literary_system.trajectory.reader_simulator import ReaderSimulator


@dataclass
class LoopIteration:
    """단일 루프 반복 결과."""
    iteration_no: int
    bundle: dict[str, Any]
    render_output: dict[str, Any]
    reader_metrics: dict[str, float]
    gate_result: GateResult
    patch_applied: str | None
    duration_seconds: float
    llm_called: bool


@dataclass
class E2ELoopResult:
    """E2E 루프 최종 결과."""
    project_id: str
    scene_id: str
    success: bool
    final_text: str
    final_literary_state: dict[str, float]
    promotion_decision: str
    total_llm_calls: int
    total_patch_attempts: int
    total_iterations: int
    iterations: list[LoopIteration]
    gate_stats: dict[str, Any]
    duration_seconds: float
    error: str | None = None

    def summary(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "scene_id": self.scene_id,
            "success": self.success,
            "total_llm_calls": self.total_llm_calls,
            "total_patch_attempts": self.total_patch_attempts,
            "total_iterations": self.total_iterations,
            "promotion_decision": self.promotion_decision,
            "duration_seconds": round(self.duration_seconds, 2),
            "gate_stats": self.gate_stats,
            "final_text_preview": self.final_text[:200] + "..." if len(self.final_text) > 200 else self.final_text,
        }


class E2ELoopOrchestrator:
    """
    V320 핵심 오케스트레이터 — 최초 End-to-End 루프.

    Claude-OS 차별화:
      - LLM은 렌더링에만 사용
      - 판정은 ReaderSimulator (로컬)
      - 패치는 SpecializedLocalPatchEngine (로컬)
      - 재호출 결정은 ConditionalLLMGate (로컬)
    """

    MAX_TOTAL_LLM_CALLS = 3   # 씬당 최대 LLM 호출 수
    MAX_LOOP_ITERATIONS = 7   # 루프 최대 반복 수 (무한루프 방지)

    def __init__(
        self,
        v312_backend_path: str | None = None,
        reader_simulator: ReaderSimulator | None = None,
        patch_engine: SpecializedLocalPatchEngine | None = None,
        llm_gate: ConditionalLLMGate | None = None,
        trace_store: TraceDatasetStore | None = None,
        bridge: LLMBridgeInterface | None = None,  # V325: ClaudeAdapter 주입 지점
    ):
        self.bridge         = bridge or V312Bridge(v312_backend_path)
        self.reader_sim     = reader_simulator or ReaderSimulator()
        self.patch_engine   = patch_engine or SpecializedLocalPatchEngine()
        self.gate           = llm_gate or ConditionalLLMGate()
        self.trace_store    = trace_store or TraceDatasetStore()

    def run(
        self,
        bundle: dict[str, Any],
        project_id: str = "default",
        scene_id: str | None = None,
        verbose: bool = True,
    ) -> E2ELoopResult:
        """
        End-to-End 루프 1회 실행.

        1. V312Bridge → LLM 렌더링
        2. ReaderSimulator → 3지표 측정
        3. ConditionalLLMGate → PASS / PATCH_ONLY / RERENDER
        4. PATCH_ONLY → SpecializedPatch → 재판정
        5. RERENDER → V312Bridge 재실행
        6. commit → TraceDatasetStore
        """
        import uuid
        scene_id = scene_id or f"scene_{uuid.uuid4().hex[:8]}"
        start_time = time.time()

        iterations: list[LoopIteration] = []
        total_llm_calls = 0
        total_patches = 0
        current_bundle = bundle.copy()
        current_text = ""
        current_state: dict[str, float] = {}
        promotion = "archive_only"
        literary_loss = 0
        error = None
        success = False

        if verbose:
            logger.info("V320 E2E Loop — project=%s scene=%s", project_id, scene_id)

        for i in range(self.MAX_LOOP_ITERATIONS):
            iter_start = time.time()
            llm_called = False
            patch_applied = None

            # ── Step 1: V312 렌더링 (LLM 호출) ──
            if total_llm_calls == 0 or (
                len(iterations) > 0 and
                iterations[-1].gate_result.decision == GateDecision.RERENDER
            ):
                if total_llm_calls >= self.MAX_TOTAL_LLM_CALLS:
                    if verbose:
                        logger.debug(f"  [LOOP] 최대 LLM 호출 {self.MAX_TOTAL_LLM_CALLS}회 초과 → 중단")
                    break

                if verbose:
                    logger.debug(f"\n  [LOOP {i+1}] ★ V312 렌더링 시작 (LLM 호출 #{total_llm_calls+1})")

                render_result = self.bridge.run(current_bundle, timeout_seconds=120.0)
                total_llm_calls += 1
                llm_called = True

                if "error" in render_result:
                    error = render_result["error"]
                    if verbose:
                        logger.debug(f"  [LOOP {i+1}] 실패: {error}")
                    break

                current_text   = self._extract_text(render_result)
                current_state  = render_result.get("literary_state_after", {})
                promotion      = render_result.get("promotion_decision", "archive_only")
                literary_loss  = render_result.get("literary_loss", 0)

                if verbose:
                    logger.debug(f"  [LOOP {i+1}] 렌더링 완료 | loss={literary_loss} | promo={promotion}")
                    logger.debug(f"    텍스트: {current_text[:80]}...")

            # ── Step 2: ReaderSimulator 측정 (LLM 0회) ──
            _est = self.reader_sim.estimate(current_text)
            reader_metrics = {
                "reader_pull": _est.reader_pull,
                "reader_afterimage": _est.reader_afterimage,
                "reader_uncertainty": _est.reader_uncertainty,
            }
            if verbose:
                logger.debug(f"  [LOOP {i+1}] ReaderSim: pull={reader_metrics.get('reader_pull',0):.3f} "
                      f"after={reader_metrics.get('reader_afterimage',0):.3f} "
                      f"unc={reader_metrics.get('reader_uncertainty',0):.3f}")

            # ── Step 3: ConditionalLLMGate ──
            gate_result = self.gate.evaluate(
                literary_state=current_state,
                reader_metrics=reader_metrics,
                literary_loss=literary_loss,
                patch_attempts=total_patches,
            )

            if verbose:
                logger.debug(f"  [LOOP {i+1}] Gate: {gate_result.decision.value}")
                for r in gate_result.reasons:
                    logger.debug(f"    → {r}")

            # 반복 기록
            iter_result = LoopIteration(
                iteration_no=i + 1,
                bundle=current_bundle,
                render_output={"text": current_text, "state": current_state},
                reader_metrics=reader_metrics,
                gate_result=gate_result,
                patch_applied=patch_applied,
                duration_seconds=round(time.time() - iter_start, 2),
                llm_called=llm_called,
            )
            iterations.append(iter_result)

            # ── Step 4: 분기 처리 ──
            if gate_result.decision == GateDecision.PASS:
                success = True
                if verbose:
                    logger.debug(f"  [LOOP {i+1}] PASS — 루프 완료")
                break

            elif gate_result.decision == GateDecision.PATCH_ONLY:
                hints = gate_result.correction_hints
                family = self._pick_patch_family(hints)
                patch_result = self.patch_engine.apply(current_text, family, scene_id=scene_id)
                current_text = patch_result.edited_text
                patch_applied = family
                total_patches += 1

                current_bundle = self._inject_soft_instruction(
                    current_bundle, patch_result.soft_instruction
                )
                if verbose:
                    logger.debug(f"  [LOOP {i+1}] PATCH [{family}] 적용: {patch_result.guidance_applied}")

                _est2 = self.reader_sim.estimate(current_text)
                reader_metrics_after = {
                    "reader_pull": _est2.reader_pull,
                    "reader_afterimage": _est2.reader_afterimage,
                    "reader_uncertainty": _est2.reader_uncertainty,
                }
                gate_after = self.gate.evaluate(
                    literary_state=current_state,
                    reader_metrics=reader_metrics_after,
                    literary_loss=literary_loss,
                    patch_attempts=total_patches,
                )
                if gate_after.decision == GateDecision.PASS:
                    success = True
                    if verbose:
                        logger.debug(f"  [LOOP {i+1}] 패치 후 PASS — 루프 완료")
                    break

            elif gate_result.decision == GateDecision.RERENDER:
                current_bundle = self._inject_correction_hints(
                    current_bundle, gate_result.correction_hints
                )
                if verbose:
                    logger.debug(f"  [LOOP {i+1}] RERENDER — 다음 반복에서 LLM 재호출")

        # ── Step 5: TraceDatasetStore 커밋 ──
        if current_text:
            self._commit_trace(
                project_id, scene_id, current_bundle,
                current_text, current_state,
                reader_metrics if iterations else {},
                promotion, total_llm_calls, success,
            )

        total_duration = round(time.time() - start_time, 2)

        if verbose:
            logger.info("V320 E2E 루프 완료: LLM %s회 | 패치 %s회 | %ss", total_llm_calls, total_patches, total_duration)

        return E2ELoopResult(
            project_id=project_id,
            scene_id=scene_id,
            success=success,
            final_text=current_text,
            final_literary_state=current_state,
            promotion_decision=promotion,
            total_llm_calls=total_llm_calls,
            total_patch_attempts=total_patches,
            total_iterations=len(iterations),
            iterations=iterations,
            gate_stats=self.gate.get_stats(),
            duration_seconds=total_duration,
            error=error,
        )

    def is_v312_available(self) -> bool:
        """V312 엔진 사용 가능 여부."""
        return self.bridge.is_available()

    def get_v312_status(self) -> dict[str, Any]:
        return self.bridge.get_status()

    # ── 내부 헬퍼 ──────────────────────────────────────────────────

    def _extract_text(self, render_result: dict[str, Any]) -> str:
        """V312 렌더링 결과에서 텍스트 추출."""
        ro = render_result.get("render_output", {})
        if isinstance(ro, dict):
            for key in ["text", "prose", "scene_text", "output", "content"]:
                if key in ro and ro[key]:
                    return str(ro[key])
            return str(ro)
        return str(ro) if ro else ""

    def _pick_patch_family(self, hints: dict[str, Any]) -> str:
        """correction_hints → 적용할 SpecializedPatch 패밀리 선택."""
        if hints.get("pdi_fix"):
            return "pdi_fix"
        if hints.get("residue_boost"):
            return "residue_boost"
        if hints.get("reveal_delay"):
            return "reveal_delay"
        if hints.get("boost_tension"):
            return "dialogue_compression"
        return "pdi_fix"

    def _inject_soft_instruction(
        self, bundle: dict[str, Any], instruction: str
    ) -> dict[str, Any]:
        """bundle에 soft_instruction 주입."""
        b = bundle.copy()
        existing = b.get("render_instruction", "")
        b["render_instruction"] = existing + "\n\n" + instruction
        return b

    def _inject_correction_hints(
        self, bundle: dict[str, Any], hints: dict[str, Any]
    ) -> dict[str, Any]:
        """재렌더링 시 보정 힌트를 bundle에 반영."""
        b = bundle.copy()
        b["correction_hints"] = hints
        if hints.get("boost_tension"):
            b["render_instruction"] = b.get("render_instruction", "") + "\n[긴장감 강화 요청]"
        if hints.get("residue_boost"):
            b["render_instruction"] = b.get("render_instruction", "") + "\n[잔향 오브제 재등장 요청]"
        return b

    def _commit_trace(
        self,
        project_id: str,
        scene_id: str,
        bundle: dict[str, Any],
        text: str,
        state: dict[str, float],
        reader_metrics: dict[str, float],
        promotion: str,
        llm_calls: int,
        success: bool,
    ) -> None:
        """TraceDatasetStore에 결과 커밋."""
        try:
            self.trace_store.commit(
                project_id=project_id,
                episode_no=bundle.get("episode_no", 1),
                scene_id=scene_id,
                render_output={"text": text},
                literary_state_before=bundle.get("state_before", {}),
                literary_state_after=state,
                critic_findings={"reader_metrics": reader_metrics},
                promotion_decision=promotion,
                call_count=llm_calls,
            )
        except Exception:
            pass  # Trace 커밋 실패는 치명적이지 않음
