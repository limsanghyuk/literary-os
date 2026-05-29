"""EnduranceLearningBridge — V406.

EnduranceRunReport 분석 → CoefficientDelta → PhysicsCoefficientStore 업데이트.

설계 원칙:
  - MAX_UPDATES_PER_CALL = 3 (안정성 제약)
  - LEARNING_RATE = 0.01 (점진적 업데이트)
  - LLM 0회
  - 모든 update에 append_trace 의무

매핑 근거 (3인 합의, 설계도 E):
  NecessityReport.weak_scene_ratio > 0.10     → scene_energy_weight += 0.01
  AgencyReport.agency_floor_violations 존재  → arc_pressure_coupling += 0.01
  FatigueReport.mid_season_fatigue_risk > 0.35 → curiosity_weight += 0.01
  VoiceDriftReport.blocked_count > 0          → prose_physics_bridge += 0.01
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class CoefficientDelta:
    """PhysicsCoefficientStore에 적용할 계수 변경 패킷."""
    updates: Dict[str, float]   # {coefficient_name: delta_value}  최대 3개
    reason: str                 # 변경 근거 (trace 메시지용)
    source_report: str          # "EnduranceRunReport"

    def is_empty(self) -> bool:
        return len(self.updates) == 0

    def to_dict(self) -> dict:
        return {
            "updates": self.updates,
            "reason": self.reason,
            "source_report": self.source_report,
        }


class EnduranceLearningBridge:
    """V406 — EnduranceRunReport → CoefficientDelta 변환기.

    EnduranceRunReport에서 약점 지표를 읽어 PhysicsCoefficientStore
    계수를 소폭 점진적으로 업데이트하는 피드백 루프 구현.
    """

    MAX_UPDATES_PER_CALL: int = 3
    LEARNING_RATE: float = 0.01

    # 임계값
    WEAK_RATIO_THRESHOLD: float = 0.10
    FATIGUE_RISK_THRESHOLD: float = 0.35

    def analyze(self, report) -> CoefficientDelta:
        """EnduranceRunReport를 분석하여 CoefficientDelta 반환.

        Args:
            report: EnduranceRunReport 인스턴스

        Returns:
            적용할 CoefficientDelta (empty일 수 있음)
        """
        candidates: List[tuple[str, float, str]] = []
        # (coefficient_name, delta, reason_fragment)

        # 1. 씬 필요성 약화 → scene_energy_weight 상향
        necessity_report = getattr(report, "necessity_report", None)
        if necessity_report is not None:
            weak_ratio = getattr(necessity_report, "weak_scene_ratio", 0.0)
            if weak_ratio > self.WEAK_RATIO_THRESHOLD:
                candidates.append((
                    "scene_energy_weight",
                    self.LEARNING_RATE,
                    f"weak_scene_ratio={weak_ratio:.3f}>{self.WEAK_RATIO_THRESHOLD}"
                ))

        # 2. 캐릭터 에이전시 위반 → arc_pressure_coupling 상향
        agency_report = getattr(report, "agency_report", None)
        if agency_report is not None:
            violations = getattr(agency_report, "agency_floor_violations", [])
            if violations:
                candidates.append((
                    "arc_pressure_coupling",
                    self.LEARNING_RATE,
                    f"agency_floor_violations={len(violations)}"
                ))

        # 3. 중반 피로도 과잉 → curiosity_weight 상향
        fatigue_report = getattr(report, "fatigue_report", None)
        if fatigue_report is not None:
            mid_risk = getattr(fatigue_report, "mid_season_fatigue_risk", 0.0)
            if mid_risk > self.FATIGUE_RISK_THRESHOLD:
                candidates.append((
                    "curiosity_weight",
                    self.LEARNING_RATE,
                    f"mid_season_fatigue_risk={mid_risk:.3f}>{self.FATIGUE_RISK_THRESHOLD}"
                ))

        # 4. 목소리 드리프트 차단 → prose_physics_bridge 상향
        voice_drift_report = getattr(report, "voice_drift_report", None)
        if voice_drift_report is not None:
            blocked = getattr(voice_drift_report, "blocked_count", 0)
            if blocked > 0:
                candidates.append((
                    "prose_physics_bridge",
                    self.LEARNING_RATE,
                    f"voice_drift_blocked={blocked}"
                ))

        # MAX_UPDATES_PER_CALL 제한 (우선순위: 앞에서부터)
        selected = candidates[: self.MAX_UPDATES_PER_CALL]

        updates = {name: delta for name, delta, _ in selected}
        reasons = [reason for _, _, reason in selected]
        reason_str = "; ".join(reasons) if reasons else "no_update_needed"

        return CoefficientDelta(
            updates=updates,
            reason=reason_str,
            source_report="EnduranceRunReport",
        )

    def apply(self, delta: CoefficientDelta, store) -> List[str]:
        """CoefficientDelta를 PhysicsCoefficientStore에 적용.

        Args:
            delta: analyze()가 반환한 CoefficientDelta
            store: PhysicsCoefficientStore 인스턴스

        Returns:
            execution_trace에 추가할 메시지 리스트
        """
        trace: List[str] = []
        if delta.is_empty():
            trace.append("EnduranceLearningBridge: no coefficient updates")
            return trace

        for coeff_name, delta_val in delta.updates.items():
            current = getattr(store, coeff_name, None)
            if current is None:
                trace.append(
                    f"EnduranceLearningBridge: SKIP unknown coefficient '{coeff_name}'"
                )
                continue
            new_val = current + delta_val
            store.update(**{coeff_name: new_val})
            updated = getattr(store, coeff_name)
            trace.append(
                f"EnduranceLearningBridge: {coeff_name} "
                f"{current:.4f} → {updated:.4f} (delta={delta_val:+.4f})"
            )

        trace.append(
            f"EnduranceLearningBridge: coefficients updated | reason={delta.reason}"
        )
        return trace
