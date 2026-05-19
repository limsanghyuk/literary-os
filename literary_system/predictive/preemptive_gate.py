"""
V553 — PreemptiveGate: NIL Step6 후 PNE 사전 차단 게이트
==========================================================
설계도 §5.1 기준:
  - NIL Step 6 완료 후 DebtPredictor.predict() 호출
  - 예측 부채 발생 확률 ≥ 0.60 시 사전 차단 신호 발생
  - 차단 신호는 Gate29(V555)로 보고됨
  - LLM 호출 없음 (LLM-0 완전 준수)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

BLOCK_THRESHOLD: float = 0.60   # 부채 발생 확률 임계값


# ─── 결과 타입 ────────────────────────────────────────────────────────────────

@dataclass
class PreemptiveResult:
    """PreemptiveGate 평가 결과."""
    scene_id:           str
    blocked:            bool                    # True = 사전 차단
    high_risk_cats:     List[str]               # 임계값 초과 카테고리 목록
    max_probability:    float                   # 최고 부채 발생 확률
    threshold:          float = BLOCK_THRESHOLD
    prediction_report:  Optional[object] = None  # PredictionReport 참조

    def block_reason(self) -> str:
        if not self.blocked:
            return ""
        cats = ", ".join(self.high_risk_cats)
        return (
            f"부채 발생 확률 ≥ {self.threshold:.0%} 카테고리: [{cats}] "
            f"(max={self.max_probability:.2%})"
        )


# ─── PreemptiveGate ───────────────────────────────────────────────────────────

class PreemptiveGate:
    """
    NIL Step6 이후 실행되는 예측적 사전 차단 게이트 (V553).

    DebtPredictor.predict()를 호출하여 다음 N 씬의 부채 발생 확률을
    평가하고, 임계값(기본 0.60) 초과 시 차단 신호를 반환한다.

    사용 예::

        gate = PreemptiveGate(predictor, horizon=3)
        result = gate.evaluate(scene_id, current_severity=0.45)
        if result.blocked:
            # NIL 루프 중단 또는 경고 발행
    """

    def __init__(
        self,
        predictor,                              # DebtPredictor
        horizon:   int   = 3,
        threshold: float = BLOCK_THRESHOLD,
    ) -> None:
        self._predictor = predictor
        self._horizon   = horizon
        self._threshold = threshold
        self._history:  List[PreemptiveResult] = []

    # ── 평가 API ─────────────────────────────────────────────────────────────

    def evaluate(
        self,
        scene_id:         str,
        current_severity: float = 0.5,
        horizon:          Optional[int] = None,
    ) -> PreemptiveResult:
        """
        씬 ID와 현재 severity를 받아 사전 차단 여부를 결정한다.

        Parameters
        ----------
        scene_id : str
            현재 씬 ID
        current_severity : float
            현재 씬 전반 severity (0~1)
        horizon : int | None
            예측 대상 씬 수 (None이면 생성자 horizon 사용)
        """
        h = horizon if horizon is not None else self._horizon

        # DebtPredictor 호출
        report = self._predictor.predict(
            scene_id=scene_id,
            current_severity=current_severity,
            horizon=h,
        )

        # 임계값 초과 카테고리 수집
        high_risk = [
            p.category
            for p in report.predictions
            if p.probability >= self._threshold
        ]
        max_prob = report.max_probability()
        blocked  = len(high_risk) > 0

        result = PreemptiveResult(
            scene_id=scene_id,
            blocked=blocked,
            high_risk_cats=high_risk,
            max_probability=max_prob,
            threshold=self._threshold,
            prediction_report=report,
        )
        self._history.append(result)
        return result

    def evaluate_batch(
        self,
        scene_ids:         List[str],
        severities:        Optional[List[float]] = None,
        horizon:           Optional[int] = None,
    ) -> List[PreemptiveResult]:
        """복수 씬 일괄 평가."""
        if severities is None:
            severities = [0.5] * len(scene_ids)
        return [
            self.evaluate(sid, sev, horizon)
            for sid, sev in zip(scene_ids, severities)
        ]

    # ── 통계 ─────────────────────────────────────────────────────────────────

    @property
    def threshold(self) -> float:
        return self._threshold

    @property
    def horizon(self) -> int:
        return self._horizon

    def block_count(self) -> int:
        return sum(1 for r in self._history if r.blocked)

    def total_evaluated(self) -> int:
        return len(self._history)

    def block_rate(self) -> float:
        total = self.total_evaluated()
        return round(self.block_count() / max(total, 1), 4)

    def history(self) -> List[PreemptiveResult]:
        return list(self._history)

    def gate_summary(self) -> Dict:
        """Gate29 보고용 요약 딕셔너리."""
        return {
            "total_evaluated": self.total_evaluated(),
            "block_count":     self.block_count(),
            "block_rate":      self.block_rate(),
            "threshold":       self._threshold,
            "horizon":         self._horizon,
        }
