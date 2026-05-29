"""
V554 — FeedbackLearner: 예측 vs 실제 대조 + F1 점수 추적 + 모델 재학습
==========================================================================
설계도 §5.1 기준:
  - PreemptiveGate 예측 결과와 실제 DebtDetector 발생 결과를 대조
  - Precision / Recall / F1 점수 누적 추적
  - 누적 샘플 ≥ MIN_RETRAIN_SAMPLES 시 DebtPredictor 재학습 트리거
  - LLM-0 완전 준수
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

try:
    from literary_system.predictive.preemptive_gate import PreemptiveGate
    _PREEMPTIVE_AVAILABLE = True
except ImportError:
    _PREEMPTIVE_AVAILABLE = False


# ─── 결과 타입 ────────────────────────────────────────────────────────────────

@dataclass
class PredictionRecord:
    """예측-실제 대조 레코드."""
    scene_id:         str
    category:         str
    predicted_prob:   float   # DebtPredictor 예측 확률
    predicted_high:   bool    # predicted_prob ≥ threshold
    actual_occurred:  bool    # 실제 부채 발생 여부


@dataclass
class MetricsSnapshot:
    """F1·Precision·Recall 스냅샷."""
    total:      int
    tp:         int     # True Positive
    fp:         int     # False Positive
    fn:         int     # False Negative
    tn:         int     # True Negative

    def precision(self) -> float:
        denom = self.tp + self.fp
        return round(self.tp / denom, 4) if denom else 0.0

    def recall(self) -> float:
        denom = self.tp + self.fn
        return round(self.tp / denom, 4) if denom else 0.0

    def f1(self) -> float:
        p, r = self.precision(), self.recall()
        denom = p + r
        return round(2 * p * r / denom, 4) if denom else 0.0

    def accuracy(self) -> float:
        return round((self.tp + self.tn) / max(self.total, 1), 4)

    def meets_precision_target(self, target: float = 0.70) -> bool:
        return self.precision() >= target


# ─── FeedbackLearner ─────────────────────────────────────────────────────────

class FeedbackLearner:
    """
    PNE 예측 품질 추적 + 주기적 모델 재학습 (V554).

    DebtPredictor의 예측 결과와 NarrativeDebtDetector의 실제 발생 결과를
    대조하여 F1·Precision·Recall을 누적 추적한다.

    누적 샘플이 MIN_RETRAIN_SAMPLES에 도달하면 DebtPredictor를 재학습시킨다.

    사용 예::

        learner = FeedbackLearner(predictor=predictor, pne_core=core)
        learner.record(scene_id, category, predicted_prob, actual_occurred)
        metrics = learner.metrics()
        if learner.should_retrain():
            learner.retrain()
    """

    PRECISION_TARGET:      float = 0.70
    MIN_RETRAIN_SAMPLES:   int   = 20

    def __init__(
        self,
        predictor=None,           # DebtPredictor (재학습용)
        pne_core=None,            # PNECore (재학습 데이터 소스)
        threshold: float = 0.60,  # 예측 양성 임계값
        min_retrain: int = MIN_RETRAIN_SAMPLES,
    ) -> None:
        self._predictor   = predictor
        self._pne_core    = pne_core
        self._threshold   = threshold
        self._min_retrain = min_retrain

        self._records:   List[PredictionRecord] = []
        self._retrain_count: int = 0
        self._last_retrain_at: int = 0   # 마지막 재학습 시점 (레코드 수 기준)

        # 카테고리별 TP/FP/FN/TN
        self._cat_counts: Dict[str, Dict[str, int]] = {}

    # ── 기록 API ─────────────────────────────────────────────────────────────

    def record(
        self,
        scene_id:        str,
        category:        str,
        predicted_prob:  float,
        actual_occurred: bool,
    ) -> PredictionRecord:
        """예측-실제 쌍 1건 기록."""
        predicted_high = predicted_prob >= self._threshold
        rec = PredictionRecord(
            scene_id=scene_id,
            category=category,
            predicted_prob=predicted_prob,
            predicted_high=predicted_high,
            actual_occurred=actual_occurred,
        )
        self._records.append(rec)
        self._update_counts(rec)
        return rec

    def record_batch(
        self,
        records: List[Tuple[str, str, float, bool]],
    ) -> List[PredictionRecord]:
        """(scene_id, category, predicted_prob, actual_occurred) 튜플 일괄 기록."""
        return [self.record(*r) for r in records]

    def _update_counts(self, rec: PredictionRecord) -> None:
        cat = rec.category
        if cat not in self._cat_counts:
            self._cat_counts[cat] = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
        c = self._cat_counts[cat]
        if rec.predicted_high and rec.actual_occurred:
            c["tp"] += 1
        elif rec.predicted_high and not rec.actual_occurred:
            c["fp"] += 1
        elif not rec.predicted_high and rec.actual_occurred:
            c["fn"] += 1
        else:
            c["tn"] += 1

    # ── 지표 API ─────────────────────────────────────────────────────────────

    def metrics(self, category: Optional[str] = None) -> MetricsSnapshot:
        """전체 또는 카테고리별 MetricsSnapshot 반환."""
        if category is not None:
            c = self._cat_counts.get(category, {"tp": 0, "fp": 0, "fn": 0, "tn": 0})
        else:
            # 전체 합산
            c = {"tp": 0, "fp": 0, "fn": 0, "tn": 0}
            for cat_c in self._cat_counts.values():
                for k in c:
                    c[k] += cat_c[k]

        total = c["tp"] + c["fp"] + c["fn"] + c["tn"]
        return MetricsSnapshot(
            total=total,
            tp=c["tp"], fp=c["fp"], fn=c["fn"], tn=c["tn"],
        )

    def f1(self, category: Optional[str] = None) -> float:
        return self.metrics(category).f1()

    def precision(self, category: Optional[str] = None) -> float:
        return self.metrics(category).precision()

    def recall(self, category: Optional[str] = None) -> float:
        return self.metrics(category).recall()

    def meets_precision_target(self) -> bool:
        return self.metrics().meets_precision_target(self.PRECISION_TARGET)

    # ── 재학습 API ───────────────────────────────────────────────────────────

    def should_retrain(self) -> bool:
        """재학습 필요 여부: 신규 레코드 ≥ MIN_RETRAIN_SAMPLES 시 True."""
        new_since_last = len(self._records) - self._last_retrain_at
        return new_since_last >= self._min_retrain

    def retrain(self, pne_core=None) -> Dict[str, bool]:
        """
        DebtPredictor 재학습 실행.

        Returns
        -------
        dict : {category: trained_flag}
        """
        if self._predictor is None:
            return {}

        core = pne_core or self._pne_core
        if core is None:
            return {}

        result = self._predictor.train(pne_core=core)
        self._retrain_count += 1
        self._last_retrain_at = len(self._records)
        return result

    def auto_retrain_if_needed(self, pne_core=None) -> Optional[Dict[str, bool]]:
        """should_retrain() True 시 자동 재학습."""
        if self.should_retrain():
            return self.retrain(pne_core=pne_core)
        return None

    # ── 상태 조회 ────────────────────────────────────────────────────────────

    def total_records(self) -> int:
        return len(self._records)

    def retrain_count(self) -> int:
        return self._retrain_count

    def summary(self) -> Dict:
        """Gate29 보고용 요약."""
        m = self.metrics()
        return {
            "total_records":     self.total_records(),
            "precision":         m.precision(),
            "recall":            m.recall(),
            "f1":                m.f1(),
            "meets_target":      m.meets_precision_target(self.PRECISION_TARGET),
            "retrain_count":     self._retrain_count,
            "precision_target":  self.PRECISION_TARGET,
        }
    def run_prediction_cycle(
        self,
        preemptive_gate: "PreemptiveGate",
        scene_ids: List[str],
        severities: Optional[List[float]] = None,
        actual_occurrences: Optional[List[bool]] = None,
    ) -> List["PredictionRecord"]:
        """
        V556: PreemptiveGate.evaluate_batch() 를 직접 호출하고
        결과를 FeedbackLearner에 기록하는 통합 사이클.

        Parameters
        ----------
        preemptive_gate : PreemptiveGate 인스턴스
        scene_ids       : 평가할 씬 ID 목록
        severities      : 씬별 심각도 (None이면 0.5 기본값)
        actual_occurrences : 실제 부채 발생 여부 (None이면 False 기본값)

        Returns
        -------
        List[PredictionRecord] — 기록된 예측 레코드
        """
        if not scene_ids:
            return []

        # V556 핵심: evaluate_batch() 호출
        results = preemptive_gate.evaluate_batch(
            scene_ids=scene_ids,
            severities=severities,
        )

        if actual_occurrences is None:
            actual_occurrences = [False] * len(results)

        records = []
        for res, actual in zip(results, actual_occurrences):
            rec = self.record(
                scene_id=res.scene_id,
                category=res.high_risk_cats[0] if res.high_risk_cats else "unknown",
                predicted_prob=res.max_probability,
                actual_occurred=actual,
            )
            records.append(rec)

        return records

