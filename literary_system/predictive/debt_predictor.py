"""
V552 — DebtPredictor: RandomForest 기반 서사 부채 예측기
=========================================================
설계도 §5.1 기준:
  - PNECore.PatternLibrary에서 피처 벡터를 읽어 RandomForest 학습
  - 다음 N 씬에서 카테고리별 부채 발생 확률 예측
  - precision ≥ 0.70 목표 (FeedbackLearner V554가 추적)
  - sklearn 미설치 시 폴백 휴리스틱 모드로 동작

LLM-0 정책 준수: 외부 LLM 호출 없음
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import random
import math


# ─── 결과 타입 ────────────────────────────────────────────────────────────────

@dataclass
class DebtPrediction:
    """단일 카테고리의 부채 발생 확률 예측."""
    category:    str
    probability: float          # 0.0 ~ 1.0
    confidence:  float          # 모델 신뢰도 0.0 ~ 1.0
    horizon:     int            # 예측 대상 씬 수 (N)
    mode:        str = "rf"     # "rf" | "heuristic"


@dataclass
class PredictionReport:
    """전체 카테고리 예측 보고서."""
    scene_id:    str
    horizon:     int
    predictions: List[DebtPrediction] = field(default_factory=list)
    high_risk:   List[str]            = field(default_factory=list)  # prob ≥ 0.60

    def __post_init__(self) -> None:
        if not self.high_risk:
            self.high_risk = [
                p.category for p in self.predictions if p.probability >= 0.60
            ]

    def any_high_risk(self) -> bool:
        return len(self.high_risk) > 0

    def max_probability(self) -> float:
        if not self.predictions:
            return 0.0
        return max(p.probability for p in self.predictions)


# ─── DebtPredictor ────────────────────────────────────────────────────────────

class DebtPredictor:
    """
    RandomForest 기반 서사 부채 예측기 (V552).

    sklearn이 설치된 경우 RandomForestClassifier를 사용하고,
    미설치 시 PatternLibrary 성공률 역산 휴리스틱으로 폴백한다.

    precision ≥ 0.70 목표는 FeedbackLearner(V554)가 검증한다.
    """

    # 기본 학습 파라미터
    N_ESTIMATORS:   int   = 100
    MAX_DEPTH:      int   = 5
    RANDOM_STATE:   int   = 42
    MIN_SAMPLES:    int   = 5    # 학습 최소 샘플 수

    # 부채 카테고리 목록 (NarrativeDebtDetector + ArcConsistencyChecker 기준)
    DEBT_CATEGORIES = [
        "unresolved_secret",
        "broken_foreshadow",
        "abandoned_thread",
        "arc_not_tracked",
        "arc_post_death",
        "arc_contradiction",
        "arc_inversion",
    ]

    def __init__(self, pne_core=None, n_estimators: int = N_ESTIMATORS) -> None:
        self._pne_core = pne_core           # PNECore (선택)
        self._n_estimators = n_estimators
        self._models: Dict[str, object] = {}  # category → 모델 (sklearn or None)
        self._is_trained = False
        self._sklearn_available = self._check_sklearn()

    @staticmethod
    def _check_sklearn() -> bool:
        try:
            import sklearn  # noqa: F401
            return True
        except ImportError:
            return False

    # ── 학습 ─────────────────────────────────────────────────────────────────

    def train(self, pne_core=None) -> Dict[str, bool]:
        """
        PatternLibrary 데이터로 카테고리별 모델 학습.

        Returns
        -------
        dict : {category: trained_flag}
        """
        core = pne_core or self._pne_core
        if core is None:
            return {cat: False for cat in self.DEBT_CATEGORIES}

        if pne_core is not None:
            self._pne_core = pne_core

        result: Dict[str, bool] = {}

        for cat in self.DEBT_CATEGORIES:
            stats = core.library.get_stats(cat)
            if stats is None or stats.total < self.MIN_SAMPLES:
                result[cat] = False
                continue

            if self._sklearn_available:
                trained = self._train_rf(cat, core)
            else:
                trained = True  # 휴리스틱 모드: 학습 불필요
            result[cat] = trained

        self._is_trained = any(result.values())
        return result

    def _train_rf(self, category: str, core) -> bool:
        """sklearn RandomForest 학습."""
        try:
            from sklearn.ensemble import RandomForestClassifier
            outcomes = [
                o for o in core.library.all_outcomes()
                if o.category == category
            ]
            if len(outcomes) < self.MIN_SAMPLES:
                return False

            X = [
                [o.severity, o.blast_ratio, math.log1p(i)]
                for i, o in enumerate(outcomes)
            ]
            y = [1 if o.success else 0 for o in outcomes]

            clf = RandomForestClassifier(
                n_estimators=self._n_estimators,
                max_depth=self.MAX_DEPTH,
                random_state=self.RANDOM_STATE,
            )
            clf.fit(X, y)
            self._models[category] = clf
            return True
        except Exception:
            return False

    # ── 예측 ─────────────────────────────────────────────────────────────────

    def predict(
        self,
        scene_id: str,
        current_severity: float = 0.5,
        horizon: int = 3,
    ) -> PredictionReport:
        """
        다음 horizon 씬에서 카테고리별 부채 발생 확률 예측.

        Parameters
        ----------
        scene_id : str
            현재 씬 ID
        current_severity : float
            현재 씬의 전반적 severity 컨텍스트 (0~1)
        horizon : int
            예측 대상 씬 수 (기본 3)
        """
        predictions: List[DebtPrediction] = []

        for cat in self.DEBT_CATEGORIES:
            prob, conf, mode = self._predict_category(cat, current_severity, horizon)
            predictions.append(DebtPrediction(
                category=cat,
                probability=prob,
                confidence=conf,
                horizon=horizon,
                mode=mode,
            ))

        report = PredictionReport(
            scene_id=scene_id,
            horizon=horizon,
            predictions=predictions,
        )
        return report

    def predict_category(
        self,
        category: str,
        scene_id: str,
        current_severity: float = 0.5,
        horizon: int = 3,
    ) -> DebtPrediction:
        """단일 카테고리 예측."""
        prob, conf, mode = self._predict_category(category, current_severity, horizon)
        return DebtPrediction(
            category=category,
            probability=prob,
            confidence=conf,
            horizon=horizon,
            mode=mode,
        )

    def _predict_category(
        self, category: str, severity: float, horizon: int
    ) -> Tuple[float, float, str]:
        """(probability, confidence, mode) 반환."""
        # sklearn 모델 사용
        if self._sklearn_available and category in self._models:
            return self._rf_predict(category, severity, horizon)

        # 휴리스틱 폴백
        return self._heuristic_predict(category, severity, horizon)

    def _rf_predict(
        self, category: str, severity: float, horizon: int
    ) -> Tuple[float, float, str]:
        """RandomForest 예측."""
        try:
            import numpy as np
            clf = self._models[category]
            X = [[severity, 0.0, math.log1p(horizon)]]
            prob = float(clf.predict_proba(X)[0][1])  # class=1 확률
            # 신뢰도: 트리 투표 분산이 낮을수록 높음
            proba_arr = np.array([
                tree.predict_proba(X)[0][1]
                for tree in clf.estimators_
            ])
            conf = float(1.0 - proba_arr.std() * 2)
            conf = max(0.0, min(1.0, conf))
            return round(prob, 4), round(conf, 4), "rf"
        except Exception:
            return self._heuristic_predict(category, severity, horizon)

    def _heuristic_predict(
        self, category: str, severity: float, horizon: int
    ) -> Tuple[float, float, str]:
        """
        PatternLibrary 성공률 역산 휴리스틱.
        성공률이 낮을수록 → 다음 씬에서 부채 발생 확률 높음.
        """
        core = self._pne_core
        if core is None:
            # 컨텍스트 없음 — severity 기반 단순 추정
            base = severity * 0.8
            horizon_adj = min(1.0, base * (1 + 0.05 * (horizon - 1)))
            return round(horizon_adj, 4), 0.50, "heuristic"

        stats = core.library.get_stats(category)
        if stats is None or stats.total == 0:
            base = severity * 0.8
            horizon_adj = min(1.0, base * (1 + 0.05 * (horizon - 1)))
            return round(horizon_adj, 4), 0.50, "heuristic"

        # 실패율이 높을수록 → 향후 부채 발생 가능성 높음
        fail_rate = 1.0 - stats.success_rate()
        # severity 가중 조합
        prob = 0.6 * fail_rate + 0.4 * stats.mean_severity()
        # horizon 보정 (거리가 멀수록 불확실성 증가)
        prob = prob * (1 + 0.03 * (horizon - 1))
        prob = min(1.0, max(0.0, prob))
        # 누적 샘플 수가 많을수록 신뢰도 향상
        conf = min(0.95, 0.50 + 0.01 * stats.total)
        return round(prob, 4), round(conf, 4), "heuristic"

    # ── 상태 ─────────────────────────────────────────────────────────────────

    @property
    def is_trained(self) -> bool:
        return self._is_trained

    @property
    def sklearn_available(self) -> bool:
        return self._sklearn_available

    def trained_categories(self) -> List[str]:
        return list(self._models.keys())
