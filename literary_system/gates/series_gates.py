"""SeriesGates — V409.

시리즈 완결 검증 게이트 3종.
NarrativeConductor.validate_series() 호출 시 실행.

SG-1: EnduranceGate       — 14체크 (V400) + 체크 #15 (V405)
SG-2: MemoryConsistency   — 에피소드 간 상태 일관성 (series_id, episode_idx 순서)
SG-3: TrajectoryDeviation — SP/RU/ET/RD 궤도 이탈 ≤ 0.15

LLM 0회.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# ── 공통 결과 구조 ─────────────────────────────────────────────────────────────

@dataclass
class SeriesGateResult:
    gate_id: str
    passed: bool
    checks: Dict[str, bool] = field(default_factory=dict)
    failures: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "gate_id": self.gate_id,
            "passed": self.passed,
            "checks": self.checks,
            "failures": self.failures,
            "warnings": self.warnings,
            "metrics": self.metrics,
        }


# ── SG-1: EnduranceSeriesGate ─────────────────────────────────────────────────

class EnduranceSeriesGate:
    """SG-1 — EnduranceGate 14+1 체크를 시리즈 단위로 실행.

    EnduranceRunReport(LongformEnduranceOrchestrator 결과)를 받아
    기존 EnduranceGate에 위임.
    """

    GATE_ID = "SG-1"

    def run(self, endurance_report) -> SeriesGateResult:
        """EnduranceRunReport → EnduranceGate.run() 위임.

        endurance_report: EnduranceRunReport 또는 gate_summary dict를 가진 객체
        """
        result = SeriesGateResult(gate_id=self.GATE_ID, passed=True)

        # gate_summary 직접 읽기 (EnduranceRunReport.gate_summary)
        gate_summary = getattr(endurance_report, "gate_summary", {})
        overall_pass = getattr(endurance_report, "overall_pass", len(gate_summary) == 0)

        result.checks = {k: bool(v) for k, v in gate_summary.items()}
        result.passed = overall_pass

        if not overall_pass:
            for k, v in gate_summary.items():
                if not v:
                    result.failures.append(f"SG-1 FAIL: {k}")

        result.metrics = {
            "check_count": len(gate_summary),
            "pass_count": sum(1 for v in gate_summary.values() if v),
        }
        return result


# ── SG-2: MemoryConsistencyGate ───────────────────────────────────────────────

class MemoryConsistencyGate:
    """SG-2 — 에피소드 간 메모리 상태 일관성 검증 (LLM 0).

    검증 항목:
    - series_id 일관성 (모든 에피소드가 동일 series_id)
    - episode_idx 연속성 (0, 1, 2, ... 순서, 건너뜀 없음)
    - narrative_tensor 범위 유효성 (SP/RU 0~1, ET -1~1, RD 0~1)
    - coefficient_snapshot 존재 (모든 에피소드에 있어야 함)
    """

    GATE_ID = "SG-2"

    def run(self, episode_memories: List[Any]) -> SeriesGateResult:
        """List[EpisodeMemory] 검증.

        Args:
            episode_memories: NarrativeMemoryStore.load_series() 반환값

        Returns:
            SeriesGateResult
        """
        result = SeriesGateResult(gate_id=self.GATE_ID, passed=True)

        if not episode_memories:
            result.passed = True
            result.checks["empty_series"] = True
            return result

        checks: Dict[str, bool] = {}
        failures: List[str] = []

        # 1. series_id 일관성
        series_ids = {m.series_id for m in episode_memories}
        checks["series_id_consistent"] = len(series_ids) == 1
        if not checks["series_id_consistent"]:
            failures.append(f"series_id inconsistency: {series_ids}")

        # 2. episode_idx 연속성
        indices = [m.episode_idx for m in episode_memories]
        expected = list(range(min(indices), max(indices) + 1))
        checks["episode_idx_sequential"] = indices == expected
        if not checks["episode_idx_sequential"]:
            missing = sorted(set(expected) - set(indices))
            failures.append(f"missing episode_idx: {missing}")

        # 3. narrative_tensor 범위 유효성
        tensor_valid = True
        for m in episode_memories:
            t = m.narrative_tensor
            if not (0.0 <= t.get("SP", 0) <= 1.0):
                tensor_valid = False
                failures.append(f"ep{m.episode_idx}: SP out of range {t.get('SP')}")
            if not (0.0 <= t.get("RU", 0) <= 1.0):
                tensor_valid = False
                failures.append(f"ep{m.episode_idx}: RU out of range {t.get('RU')}")
            if not (-1.0 <= t.get("ET", 0) <= 1.0):
                tensor_valid = False
                failures.append(f"ep{m.episode_idx}: ET out of range {t.get('ET')}")
            if not (0.0 <= t.get("RD", 0) <= 1.0):
                tensor_valid = False
                failures.append(f"ep{m.episode_idx}: RD out of range {t.get('RD')}")
        checks["tensor_range_valid"] = tensor_valid

        # 4. coefficient_snapshot 존재
        coeff_present = all(
            bool(getattr(m, "coefficient_snapshot", {}))
            for m in episode_memories
        )
        checks["coefficient_snapshot_present"] = coeff_present
        if not coeff_present:
            failures.append("some episodes missing coefficient_snapshot")

        result.checks = checks
        result.failures = failures
        result.passed = len(failures) == 0
        result.metrics = {
            "episode_count": len(episode_memories),
            "series_id": list(series_ids)[0] if len(series_ids) == 1 else "mixed",
        }
        return result


# ── SG-3: TrajectoryDeviationGate ────────────────────────────────────────────

# 목표 궤도 형상 (설계도 J — tension_rising_spiral 기준)
_TARGET_TRAJECTORIES = {
    "tension_rising_spiral": {
        "SP": lambda p: 0.3 + p * 0.7,          # 선형 상승
        "RU": lambda p: 0.1 + p * 0.4 * (1 - p),  # 포물선 (중반 최대)
        "ET": lambda p: -0.3 + p * 0.6,          # 음→양
        "RD": lambda p: 1.0 - p * 0.3,           # 완만 감소
    },
}


class TrajectoryDeviationGate:
    """SG-3 — SP/RU/ET/RD 궤도 이탈 검증 (LLM 0).

    에피소드별 실제 궤도 vs 목표 궤도 평균 이탈도 ≤ DEVIATION_MAX.
    """

    GATE_ID = "SG-3"
    DEVIATION_MAX: float = 0.15
    DEFAULT_TRAJECTORY: str = "tension_rising_spiral"

    def run(
        self,
        episode_memories: List[Any],
        trajectory_name: Optional[str] = None,
    ) -> SeriesGateResult:
        """에피소드 메모리 궤도 이탈 검증.

        Args:
            episode_memories: List[EpisodeMemory] (episode_idx 순 정렬)
            trajectory_name: 목표 궤도 이름 (기본: tension_rising_spiral)

        Returns:
            SeriesGateResult
        """
        result = SeriesGateResult(gate_id=self.GATE_ID, passed=True)

        if not episode_memories:
            result.checks["empty_series"] = True
            return result

        traj_name = trajectory_name or self.DEFAULT_TRAJECTORY
        target = _TARGET_TRAJECTORIES.get(traj_name, _TARGET_TRAJECTORIES[self.DEFAULT_TRAJECTORY])

        total_eps = max(m.episode_idx for m in episode_memories)
        if total_eps == 0:
            result.checks["single_episode"] = True
            return result

        deviations: List[float] = []
        for m in episode_memories:
            if m.episode_idx == 0:
                continue
            progress = m.episode_idx / total_eps
            t = m.narrative_tensor
            dims = ["SP", "RU", "ET", "RD"]
            ep_dev = sum(
                abs(t.get(d, 0.0) - target[d](progress))
                for d in dims
            ) / 4.0
            deviations.append(ep_dev)

        if not deviations:
            result.checks["no_episodes_to_check"] = True
            return result

        mean_dev = sum(deviations) / len(deviations)
        passed = mean_dev <= self.DEVIATION_MAX

        result.passed = passed
        result.checks["trajectory_deviation"] = passed
        result.metrics = {
            "mean_deviation": round(mean_dev, 4),
            "deviation_max": self.DEVIATION_MAX,
            "trajectory_name": traj_name,
            "episodes_checked": len(deviations),
        }
        if not passed:
            result.failures.append(
                f"mean_deviation={mean_dev:.4f} > {self.DEVIATION_MAX} (trajectory={traj_name})"
            )
        return result


# ── SeriesGateRunner (통합 실행) ──────────────────────────────────────────────

class SeriesGateRunner:
    """SG-1 + SG-2 + SG-3 통합 실행."""

    def __init__(self) -> None:
        self.sg1 = EnduranceSeriesGate()
        self.sg2 = MemoryConsistencyGate()
        self.sg3 = TrajectoryDeviationGate()

    def run_all(
        self,
        endurance_report,
        episode_memories: List[Any],
        trajectory_name: Optional[str] = None,
    ) -> Dict[str, SeriesGateResult]:
        results: Dict[str, SeriesGateResult] = {}
        results["SG-1"] = self.sg1.run(endurance_report)
        results["SG-2"] = self.sg2.run(episode_memories)
        results["SG-3"] = self.sg3.run(episode_memories, trajectory_name)
        return results

    def all_passed(self, results: Dict[str, SeriesGateResult]) -> bool:
        return all(r.passed for r in results.values())
