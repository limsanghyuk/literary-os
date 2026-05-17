"""
AgentCalibrator — V513
Phase 2 RubricCalibrator 격주 통합

- Phase 1: 기본 에이전트 성과 기록 (작품별 pass/fail 누적)
- Phase 2: RubricCalibrator 격주 실행 → 룰릭 점수 기반 가중치 재보정
           MAEOrchestratorV2.update_weights() 호출
- 활성화 조건: 누적 작품 수 >= PHASE2_ACTIVATION_WORKS (기본 10)
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Tuple



# ─── 상수 ─────────────────────────────────────────────────────────────────────
PHASE2_ACTIVATION_WORKS: int = 10      # Phase 2 활성화 임계값
BIWEEKLY_INTERVAL_WORKS: int = 2       # 격주 ≈ 작품 2편 처리 간격(작품 단위)
RUBRIC_SMOOTHING: float = 0.20         # Laplace smoothing for rubric score
MIN_WEIGHT: float = 0.05               # 에이전트 최소 가중치
WEIGHT_ADJUST_CAP: float = 0.15        # 1회 재보정 시 최대 변동폭
SIGMA_ESCALATION_THRESHOLD: float = 0.15  # σ 초과 시 escalation 기록


# ─── 데이터 클래스 ─────────────────────────────────────────────────────────────
class CalibratorPhase(Enum):
    INACTIVE = "inactive"
    PHASE1 = "phase1"
    PHASE2 = "phase2"


@dataclass
class AgentRecord:
    """에이전트별 누적 성과 레코드."""
    agent: str
    pass_count: int = 0
    fail_count: int = 0
    sigma_escalations: int = 0        # σ > SIGMA_ESCALATION_THRESHOLD 횟수
    rubric_scores: List[float] = field(default_factory=list)

    @property
    def total(self) -> int:
        return self.pass_count + self.fail_count

    @property
    def pass_rate(self) -> float:
        if self.total == 0:
            return 0.5
        return (self.pass_count + RUBRIC_SMOOTHING) / (self.total + 2 * RUBRIC_SMOOTHING)


@dataclass
class RubricScore:
    """RubricCalibrator 평가 결과."""
    agent: str
    score: float                       # 0~1
    weight_delta: float                # 제안 가중치 변동
    reason: str = ""


@dataclass
class CalibrationResult:
    """격주 재보정 결과 스냅샷."""
    works_count: int
    old_weights: Dict[str, float]
    new_weights: Dict[str, float]
    rubric_scores: List[RubricScore]
    triggered_by: str = "biweekly"


# ─── RubricCalibrator ─────────────────────────────────────────────────────────
class RubricCalibrator:
    """
    Phase 2 룰릭 기반 가중치 재보정기.
    각 에이전트의 누적 pass_rate 와 sigma_escalation 을 룰릭 점수로 환산,
    가중치 delta 를 계산한다.
    """

    RUBRIC_WEIGHTS = {
        "pass_rate": 0.70,
        "sigma_penalty": 0.30,
    }

    def evaluate(
        self,
        records: Dict[str, AgentRecord],
        current_weights: Dict[str, float],
    ) -> List[RubricScore]:
        scores: List[RubricScore] = []
        for agent, rec in records.items():
            pass_score = rec.pass_rate
            sigma_ratio = rec.sigma_escalations / max(rec.total, 1)
            sigma_score = max(0.0, 1.0 - sigma_ratio * 2)

            rubric = (
                self.RUBRIC_WEIGHTS["pass_rate"] * pass_score
                + self.RUBRIC_WEIGHTS["sigma_penalty"] * sigma_score
            )

            # 가중치 델타: 룰릭 점수 0.5 기준으로 ±비례
            delta = (rubric - 0.5) * WEIGHT_ADJUST_CAP * 2
            delta = max(-WEIGHT_ADJUST_CAP, min(WEIGHT_ADJUST_CAP, delta))

            scores.append(RubricScore(
                agent=agent,
                score=rubric,
                weight_delta=delta,
                reason=f"pass_rate={pass_score:.3f}, sigma_ratio={sigma_ratio:.3f}",
            ))
        return scores

    def compute_new_weights(
        self,
        scores: List[RubricScore],
        current_weights: Dict[str, float],
    ) -> Dict[str, float]:
        """룰릭 점수 기반으로 새 가중치 계산. 합산 = 1.0 로 정규화."""
        raw: Dict[str, float] = {}
        for rs in scores:
            old_w = current_weights.get(rs.agent, 0.25)
            raw[rs.agent] = old_w + rs.weight_delta

        agents = list(raw.keys())
        if not agents:
            return dict(current_weights)
        # Iterative floor-budget normalization: guarantee all weights >= MIN_WEIGHT
        weights = {a: raw[a] for a in agents}
        for _ in range(len(agents) + 1):
            floored = {a for a in agents if weights.get(a, 0.0) < MIN_WEIGHT}
            if not floored:
                break
            for a in floored:
                weights[a] = MIN_WEIGHT
            free = [a for a in agents if a not in floored]
            remaining = 1.0 - len(floored) * MIN_WEIGHT
            if remaining <= 0 or not free:
                for a in agents:
                    weights[a] = 1.0 / len(agents)
                break
            free_total = sum(max(raw[a], 0.0) for a in free)
            if free_total <= 0:
                share = remaining / len(free)
                for a in free:
                    weights[a] = share
            else:
                for a in free:
                    weights[a] = max(raw[a], 0.0) / free_total * remaining
        # Final normalization to ensure exact sum=1.0
        total = sum(weights.values())
        if total <= 0:
            return dict(current_weights)
        return {a: w / total for a, w in weights.items()}


# ─── AgentCalibrator ──────────────────────────────────────────────────────────
class AgentCalibrator:
    """
    MAEOrchestratorV2 의 에이전트 가중치를 생애주기 동안 지속 보정.
    Phase 1: 성과 기록만.
    Phase 2: BIWEEKLY_INTERVAL_WORKS 마다 RubricCalibrator 실행.
    """

    def __init__(self) -> None:
        self._phase = CalibratorPhase.PHASE1
        self._records: Dict[str, AgentRecord] = {}
        self._works_count: int = 0
        self._last_calibration_works: int = 0
        self._calibration_history: List[CalibrationResult] = []
        self._rubric = RubricCalibrator()

    # ── 공개 API ─────────────────────────────────────────────────────────────
    def record_result(
        self,
        agent: str,
        passed: bool,
        sigma: float = 0.0,
    ) -> None:
        """
        씬 평가 결과를 기록한다.
        agent: "reader" | "writer" | "editor" | "cultural"
        passed: MAE pass/fail
        sigma: 해당 씬의 에이전트 점수 표준편차
        """
        if agent not in self._records:
            self._records[agent] = AgentRecord(agent=agent)
        rec = self._records[agent]
        if passed:
            rec.pass_count += 1
        else:
            rec.fail_count += 1
        if sigma > SIGMA_ESCALATION_THRESHOLD:
            rec.sigma_escalations += 1

    def complete_work(self) -> None:
        """작품 1편 완료 시 호출. 격주 캘리브레이션 트리거 점검."""
        self._works_count += 1
        if self._works_count >= PHASE2_ACTIVATION_WORKS:
            self._phase = CalibratorPhase.PHASE2

    def maybe_calibrate(
        self,
        orchestrator,                # MAEOrchestratorV2 인스턴스 (타입 순환 방지)
    ) -> Optional[CalibrationResult]:
        """
        Phase 2 이고 격주 간격 도달 시 룰릭 재보정 수행.
        calibration 결과를 반환하거나 None 반환.
        """
        if self._phase != CalibratorPhase.PHASE2:
            return None
        if not self._records:
            return None
        since_last = self._works_count - self._last_calibration_works
        if since_last < BIWEEKLY_INTERVAL_WORKS:
            return None

        return self._run_calibration(orchestrator)

    def force_calibrate(self, orchestrator) -> CalibrationResult:
        """테스트·수동 강제 실행용. Phase 무관하게 재보정 수행."""
        return self._run_calibration(orchestrator)

    def activate_phase2(self) -> None:
        """외부에서 명시적 Phase 2 활성화 (MetaLearner 연동)."""
        self._phase = CalibratorPhase.PHASE2

    @property
    def phase(self) -> CalibratorPhase:
        return self._phase

    @property
    def works_count(self) -> int:
        return self._works_count

    @property
    def calibration_history(self) -> List[CalibrationResult]:
        return list(self._calibration_history)

    def get_record(self, agent: str) -> Optional[AgentRecord]:
        return self._records.get(agent)

    def get_all_records(self) -> Dict[str, AgentRecord]:
        return dict(self._records)

    # ── 내부 헬퍼 ────────────────────────────────────────────────────────────
    def _run_calibration(self, orchestrator) -> CalibrationResult:
        old_weights = dict(getattr(orchestrator, "_weights", {}))
        rubric_scores = self._rubric.evaluate(self._records, old_weights)
        new_weights = self._rubric.compute_new_weights(rubric_scores, old_weights)

        orchestrator.update_weights(new_weights)

        result = CalibrationResult(
            works_count=self._works_count,
            old_weights=old_weights,
            new_weights=new_weights,
            rubric_scores=rubric_scores,
        )
        self._calibration_history.append(result)
        self._last_calibration_works = self._works_count
        return result
