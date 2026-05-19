"""
V320: ConditionalLLMGate
Phase 3 — Literary State 임계값 기반 조건부 LLM 호출 게이트.

핵심 원칙 (최고 프론티어 개발자 + 수석 아키텍트 합의):
  "GPT가 v1832 Excel로 간 이유:
   판단을 LLM에 위임 → 비용/한도 → 인간 오퍼레이터.
   
   Claude-OS의 차별화:
   판단은 로컬 → 조건부로만 LLM 재호출.
   목표: Phase 2 기준선 대비 LLM 호출 50% 감소."

설계 원칙:
  - LLM 재호출은 "마지막 수단"이다
  - SpecializedPatch가 2회 실패한 경우에만 재호출
  - Literary State 임계값이 기준선 이상이면 재호출 불필요
  - 임계값은 Phase 2 실측 데이터 기반으로 조정 (사전 선언 금지)

LLM 0회 (게이트 판정 자체는).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class GateDecision(str, Enum):
    PASS        = "PASS"        # 기준 통과 — LLM 재호출 불필요
    PATCH_ONLY  = "PATCH_ONLY"  # 로컬 패치만으로 해결 시도
    RERENDER    = "RERENDER"    # LLM 재렌더링 필요


@dataclass
class ConditionalLLMGateResult:
    """게이트 판정 결과."""
    decision: GateDecision
    literary_state: dict[str, float]
    patch_attempts: int
    reasons: list[str]
    # 재렌더링 시 전달할 보정 힌트
    correction_hints: dict[str, Any] = field(default_factory=dict)
    llm_call_prevented: bool = False  # 이번 판정으로 LLM 호출을 막았는가


class ConditionalLLMGate:
    """
    조건부 LLM 게이트.

    판정 순서:
      1. Literary State가 기준 이상인가?
         → PASS (LLM 재호출 없음)
      2. 기준 미달이지만 패치 2회 미만인가?
         → PATCH_ONLY (SpecializedPatch 시도)
      3. 패치 2회 후에도 기준 미달인가?
         → RERENDER (LLM 재호출)

    임계값은 Phase 2 실측 후 자동 조정 가능.
    """

    # 기본 임계값 (Phase 2 실측 전 초기값)
    DEFAULT_THRESHOLDS: dict[str, float] = {
        "reader_pull_min":        0.40,
        "reader_afterimage_min":  0.30,
        "reader_uncertainty_max": 0.80,
        "literary_loss_max":      3,     # critic 발견 결함 최대 허용 수
    }

    MAX_PATCH_ATTEMPTS = 2  # 최대 패치 시도 수

    def __init__(
        self,
        thresholds: dict[str, Any] | None = None,
        max_patch_attempts: int | None = None,
    ):
        self.thresholds = thresholds or self.DEFAULT_THRESHOLDS.copy()
        self.max_patch_attempts = max_patch_attempts or self.MAX_PATCH_ATTEMPTS

        # 통계 추적 (Phase 2 기준선 측정용)
        self._stats = {
            "total_evaluations": 0,
            "pass_count": 0,
            "patch_only_count": 0,
            "rerender_count": 0,
            "llm_calls_prevented": 0,
        }

    def evaluate(
        self,
        literary_state: dict[str, float],
        reader_metrics: dict[str, float],
        literary_loss: int = 0,
        patch_attempts: int = 0,
    ) -> GateResult:
        """
        현재 Literary State + ReaderSimulator 지표 → 게이트 판정.

        Args:
            literary_state: V312 엔진 출력 literary_state_after
            reader_metrics: ReaderSimulator 3지표
            literary_loss: V312 critic 발견 결함 수
            patch_attempts: 지금까지 패치를 시도한 횟수
        """
        self._stats["total_evaluations"] += 1
        reasons: list[str] = []
        correction_hints: dict[str, Any] = {}

        # ── 1. 기준 충족 여부 판단 ──
        pull       = reader_metrics.get("reader_pull", 0.0)
        afterimage = reader_metrics.get("reader_afterimage", 0.0)
        uncertainty= reader_metrics.get("reader_uncertainty", 1.0)

        pull_ok       = pull       >= self.thresholds["reader_pull_min"]
        afterimage_ok = afterimage >= self.thresholds["reader_afterimage_min"]
        uncert_ok     = uncertainty<= self.thresholds["reader_uncertainty_max"]
        loss_ok       = literary_loss <= self.thresholds["literary_loss_max"]

        all_ok = pull_ok and afterimage_ok and uncert_ok and loss_ok

        if all_ok:
            self._stats["pass_count"] += 1
            self._stats["llm_calls_prevented"] += 1
            return GateResult(
                decision=GateDecision.PASS,
                literary_state=literary_state,
                patch_attempts=patch_attempts,
                reasons=["Literary State 기준 충족 — LLM 재호출 불필요"],
                llm_call_prevented=True,
            )

        # ── 2. 어느 기준이 미달인가 ──
        if not pull_ok:
            reasons.append(f"reader_pull={pull:.3f} < {self.thresholds['reader_pull_min']} (독자 흡인력 부족)")
            correction_hints["boost_tension"] = True
        if not afterimage_ok:
            reasons.append(f"reader_afterimage={afterimage:.3f} < {self.thresholds['reader_afterimage_min']} (잔향 약함)")
            correction_hints["residue_boost"] = True
        if not uncert_ok:
            reasons.append(f"reader_uncertainty={uncertainty:.3f} > {self.thresholds['reader_uncertainty_max']} (혼란 과다)")
            correction_hints["reveal_delay"] = True
        if not loss_ok:
            reasons.append(f"literary_loss={literary_loss} > {self.thresholds['literary_loss_max']} (critic 결함 과다)")
            correction_hints["pdi_fix"] = True

        # ── 3. 패치 여부 결정 ──
        if patch_attempts < self.max_patch_attempts:
            self._stats["patch_only_count"] += 1
            self._stats["llm_calls_prevented"] += 1
            reasons.append(f"패치 시도 {patch_attempts + 1}/{self.max_patch_attempts} — LLM 재호출 보류")
            return GateResult(
                decision=GateDecision.PATCH_ONLY,
                literary_state=literary_state,
                patch_attempts=patch_attempts,
                reasons=reasons,
                correction_hints=correction_hints,
                llm_call_prevented=True,
            )

        # ── 4. 패치 한도 초과 → LLM 재호출 ──
        self._stats["rerender_count"] += 1
        reasons.append(
            f"패치 {patch_attempts}회 후 기준 미달 — LLM 재렌더링 실행"
        )

        # 재렌더링 힌트 생성
        correction_hints["rerender_reason"] = reasons
        correction_hints["current_state"] = {
            "reader_pull": round(pull, 4),
            "reader_afterimage": round(afterimage, 4),
            "reader_uncertainty": round(uncertainty, 4),
        }

        return GateResult(
            decision=GateDecision.RERENDER,
            literary_state=literary_state,
            patch_attempts=patch_attempts,
            reasons=reasons,
            correction_hints=correction_hints,
            llm_call_prevented=False,
        )

    def get_stats(self) -> dict[str, Any]:
        """Phase 2 기준선 측정용 통계."""
        total = max(self._stats["total_evaluations"], 1)
        return {
            **self._stats,
            "pass_rate":       round(self._stats["pass_count"] / total, 4),
            "patch_rate":      round(self._stats["patch_only_count"] / total, 4),
            "rerender_rate":   round(self._stats["rerender_count"] / total, 4),
            "llm_prevention_rate": round(self._stats["llm_calls_prevented"] / total, 4),
        }

    def calibrate_from_baseline(
        self,
        baseline_stats: dict[str, Any],
        target_reduction: float = 0.50,
    ) -> dict[str, Any]:
        """
        Phase 2 실측 기준선으로 임계값 교정 제안.
        target_reduction: LLM 호출 감소 목표 비율 (기본 0.50 = 50%)
        """
        current_rerender_rate = baseline_stats.get("rerender_rate", 1.0)
        target_rerender_rate  = current_rerender_rate * (1 - target_reduction)

        suggestions = {
            "target_rerender_rate": round(target_rerender_rate, 4),
            "current_rerender_rate": round(current_rerender_rate, 4),
            "reduction_target": f"{target_reduction * 100:.0f}%",
            "recommended_action": (
                "reader_pull_min을 0.02 높이고 max_patch_attempts를 3으로 증가"
                if current_rerender_rate > target_rerender_rate
                else "현재 임계값 유지"
            ),
        }
        return suggestions

    def reset_stats(self) -> None:
        """통계 초기화 (Phase 전환 시 사용)."""
        self._stats = {k: 0 for k in self._stats}

GateResult = ConditionalLLMGateResult  # V579 backward-compat alias
