"""
V314: NarrativeTrajectory
Literary State를 8개 스칼라 점에서 연속 궤도(Trajectory)로 승격.

핵심 개념:
  - 점(Point): SP=0.45 — "지금 이 값"
  - 궤도(Trajectory): "이 값이 MacroArc 목표 형상에서 어느 위치인가"
  - 이탈(Deviation): "현재 위치가 목표 궤도에서 얼마나 벗어났는가"

MacroArc가 목표 형상을 정의하고,
Render Runtime은 그 형상을 따라가는 곡선을 그린다.
Critic은 이탈 거리를 계측한다.

LLM 0회.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any

# ── 표준 궤도 형상 (MacroArc Constitution 정의) ──────────────
_TRAJECTORY_SHAPES: dict[str, dict[str, list[float]]] = {
    # SP: Scene Pressure 궤도 (정규화된 에피소드 비율 기준)
    # [ep_start, ep_25%, ep_50%, ep_75%, ep_end]
    "tension_rising_spiral": {
        "SP": [0.30, 0.42, 0.58, 0.68, 0.75],
        "RU": [0.65, 0.60, 0.52, 0.45, 0.38],
        "ET": [0.00, 0.05, 0.10, 0.15, 0.20],
    },
    "slow_burn_to_revelation": {
        "SP": [0.25, 0.32, 0.45, 0.62, 0.72],
        "RU": [0.70, 0.68, 0.62, 0.50, 0.35],
        "ET": [-0.05, 0.00, 0.08, 0.18, 0.28],
    },
    "false_opening_deepen": {
        "SP": [0.35, 0.50, 0.40, 0.58, 0.70],
        "RU": [0.60, 0.55, 0.65, 0.52, 0.40],
        "ET": [0.00, 0.10, -0.05, 0.12, 0.22],
    },
    "steady_pressure": {
        "SP": [0.45, 0.50, 0.55, 0.60, 0.65],
        "RU": [0.55, 0.52, 0.50, 0.48, 0.45],
        "ET": [0.05, 0.08, 0.10, 0.12, 0.15],
    },
    "melodramatic_peak": {
        "SP": [0.30, 0.45, 0.65, 0.80, 0.70],
        "RU": [0.60, 0.55, 0.45, 0.30, 0.40],
        "ET": [0.10, 0.20, 0.40, 0.60, 0.35],
    },
}

# 장르 → 궤도 형상 매핑
_GENRE_TO_SHAPE: dict[str, str] = {
    "political_thriller":  "tension_rising_spiral",
    "noir_crime":          "slow_burn_to_revelation",
    "thriller_suspense":   "tension_rising_spiral",
    "revenge_drama":       "false_opening_deepen",
    "family_melodrama":    "melodramatic_peak",
    "romance_drama":       "melodramatic_peak",
    "corporate_drama":     "steady_pressure",
    "legal_drama":         "tension_rising_spiral",
    "medical_drama":       "steady_pressure",
    "general_drama":       "steady_pressure",
}


@dataclass
class TrajectoryPoint:
    """단일 에피소드의 Literary State 점."""
    episode_no: int
    SP: float
    RU: float
    ET: float
    RD: float = 0.12
    RT: float = 0.30
    AC: float = 0.70
    RO: float = 0.50
    MR: float = 0.10

    def as_dict(self) -> dict[str, float]:
        return {
            "SP": self.SP, "RU": self.RU, "ET": self.ET,
            "RD": self.RD, "RT": self.RT,
            "AC": self.AC, "RO": self.RO, "MR": self.MR,
        }


@dataclass
class NarrativeTrajectory:
    """
    Literary State의 연속 궤도.
    점(Point) → 형상(Shape) + 이탈(Deviation) + 예측(Prediction).
    """
    project_id: str
    shape_name: str
    total_episodes: int

    # 실제 기록된 점들 {episode_no: TrajectoryPoint}
    recorded: dict[int, TrajectoryPoint] = field(default_factory=dict)

    def record(self, point: TrajectoryPoint) -> None:
        self.recorded[point.episode_no] = point

    def target_at(self, episode_no: int, variable: str = "SP") -> float:
        """주어진 화의 목표값 (궤도 보간)."""
        shape = _TRAJECTORY_SHAPES.get(self.shape_name, {})
        waypoints = shape.get(variable, [0.40, 0.50, 0.55, 0.60, 0.65])
        # 에피소드 비율 → 보간
        ratio = (episode_no - 1) / max(self.total_episodes - 1, 1)
        idx_f = ratio * (len(waypoints) - 1)
        lo = int(idx_f)
        hi = min(lo + 1, len(waypoints) - 1)
        t = idx_f - lo
        return waypoints[lo] * (1 - t) + waypoints[hi] * t

    def deviation(self, episode_no: int) -> dict[str, float]:
        """현재 기록값과 목표값의 이탈 거리 (변수별)."""
        point = self.recorded.get(episode_no)
        if not point:
            return {}
        result = {}
        for var in ["SP", "RU", "ET"]:
            actual  = getattr(point, var)
            target  = self.target_at(episode_no, var)
            result[var] = round(actual - target, 4)
        return result

    def total_deviation(self, episode_no: int) -> float:
        """3개 핵심 변수의 이탈 벡터 크기 (Euclidean)."""
        dev = self.deviation(episode_no)
        if not dev:
            return 0.0
        return round(math.sqrt(sum(v ** 2 for v in dev.values())), 4)

    def predict_landing(self, current_episode: int) -> dict[str, float]:
        """현재 추세로 계속 가면 최종화에서 어느 점에 도달하는가."""
        if len(self.recorded) < 2:
            # 데이터 부족 → 목표 궤도 끝점 반환
            return {
                "SP": self.target_at(self.total_episodes, "SP"),
                "RU": self.target_at(self.total_episodes, "RU"),
                "ET": self.target_at(self.total_episodes, "ET"),
            }
        # 최근 2개 점으로 선형 외삽
        eps = sorted(self.recorded.keys())[-2:]
        p1, p2 = self.recorded[eps[0]], self.recorded[eps[1]]
        remaining = self.total_episodes - current_episode
        rate_sp = p2.SP - p1.SP
        rate_ru = p2.RU - p1.RU
        rate_et = p2.ET - p1.ET
        return {
            "SP": round(min(1.0, max(0.0, p2.SP + rate_sp * remaining)), 3),
            "RU": round(min(1.0, max(0.0, p2.RU + rate_ru * remaining)), 3),
            "ET": round(min(1.0, max(-1.0, p2.ET + rate_et * remaining)), 3),
        }

    def trajectory_report(self, current_episode: int) -> dict[str, Any]:
        """현재 궤도 상태 전체 리포트."""
        dev = self.deviation(current_episode)
        total_dev = self.total_deviation(current_episode)
        prediction = self.predict_landing(current_episode)

        # 이탈 심각도 분류
        if total_dev < 0.05:
            severity = "on_track"
        elif total_dev < 0.12:
            severity = "minor_deviation"
        elif total_dev < 0.22:
            severity = "moderate_deviation"
        else:
            severity = "critical_deviation"

        return {
            "project_id":       self.project_id,
            "episode_no":       current_episode,
            "shape_name":       self.shape_name,
            "current_state":    self.recorded.get(current_episode, TrajectoryPoint(current_episode, 0, 0, 0)).as_dict()
                                if current_episode in self.recorded else {},
            "target_state": {
                "SP": round(self.target_at(current_episode, "SP"), 3),
                "RU": round(self.target_at(current_episode, "RU"), 3),
                "ET": round(self.target_at(current_episode, "ET"), 3),
            },
            "deviation":        dev,
            "total_deviation":  total_dev,
            "severity":         severity,
            "predicted_landing": prediction,
            "needs_correction": severity in ("moderate_deviation", "critical_deviation"),
        }


class TrajectoryEngine:
    """
    NarrativeTrajectory 생성·관리 엔진.
    MacroArc Constitution에서 목표 형상을 결정.
    """

    def create(
        self,
        project_id: str,
        genre: str,
        total_episodes: int,
        shape_override: str | None = None,
    ) -> NarrativeTrajectory:
        shape = shape_override or _GENRE_TO_SHAPE.get(genre, "steady_pressure")
        return NarrativeTrajectory(
            project_id=project_id,
            shape_name=shape,
            total_episodes=total_episodes,
        )

    def ingest_episode_result(
        self,
        trajectory: NarrativeTrajectory,
        episode_no: int,
        literary_state: dict[str, float],
    ) -> NarrativeTrajectory:
        """에피소드 실행 결과를 궤도에 기록."""
        point = TrajectoryPoint(
            episode_no=episode_no,
            SP=literary_state.get("SP", 0.40),
            RU=literary_state.get("RU", 0.55),
            ET=literary_state.get("ET", 0.00),
            RD=literary_state.get("RD", 0.12),
            RT=literary_state.get("RT", 0.30),
            AC=literary_state.get("AC", 0.70),
            RO=literary_state.get("RO", 0.50),
            MR=literary_state.get("MR", 0.10),
        )
        trajectory.record(point)
        return trajectory

    def correction_vector(
        self,
        trajectory: NarrativeTrajectory,
        current_episode: int,
    ) -> dict[str, float]:
        """
        이탈 시 다음 에피소드에 적용할 보정 벡터.
        Critic이 "몇 점 이탈"이 아니라 "어떻게 복귀"를 알 수 있게.
        """
        dev = trajectory.deviation(current_episode)
        if not dev:
            return {}
        next_ep = current_episode + 1
        correction = {}
        for var, delta in dev.items():
            target_next = trajectory.target_at(next_ep, var)
            current_val = getattr(
                trajectory.recorded.get(current_episode, TrajectoryPoint(current_episode, 0.4, 0.55, 0.0)),
                var, target_next
            )
            # 목표 방향으로 이동
            correction[var] = round(target_next - current_val + (-delta * 0.5), 4)
        return correction

    def list_shapes(self) -> list[str]:
        return list(_TRAJECTORY_SHAPES.keys())
