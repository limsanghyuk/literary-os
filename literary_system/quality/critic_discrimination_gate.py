"""
quality/critic_discrimination_gate.py — G_CRITIC_DISCRIMINATION (V775, ADR-235).

회사 NextEpisodeBench 검토의 선결조건: 평가기(패널+공식)가 **명작 계열 > 졸작을
실제로 가르는가**를 외부 라벨로 검증. 못 가르면 연속-생성 학습 신호도 의심.

판별력 = AUC = P(scorer(긍정목표) > scorer(졸작))  (모든 긍정×부정 쌍 정렬 정확도).
- 0.5=무작위, 1.0=완벽. 임계 DISCRIMINATION_MIN=0.70.
- scorer는 외부 주입(공식 R / 패널 as_judge 등). 모델 자기 라벨링 금지(순환)와 무관 — 라벨은 외부.
LLM-0: 게이트 자체는 순수 로직. scorer가 LLM이면 그건 critic(LLM-1 허용)이고 라벨은 외부.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from literary_system.quality.quality_labels import QualityLabel, DEMO_LABELS

DISCRIMINATION_MIN = 0.70       # AUC 임계(걸작>졸작 판별력 최소)


@dataclass
class DiscriminationResult:
    auc:          float         # 긍정 vs 졸작 정렬 정확도
    n_positive:   int
    n_poor:       int
    n_pairs:      int
    passed:       bool
    detail:       str

    def to_dict(self) -> Dict[str, Any]:
        return {"auc": self.auc, "n_positive": self.n_positive, "n_poor": self.n_poor,
                "n_pairs": self.n_pairs, "passed": self.passed, "detail": self.detail}


def g_critic_discrimination(scorer: Callable[[QualityLabel], float],
                            labels: Optional[List[QualityLabel]] = None,
                            threshold: float = DISCRIMINATION_MIN) -> DiscriminationResult:
    """
    scorer: QualityLabel → 평가기 점수(높을수록 우수). 외부 라벨로 판별력 측정.
    AUC = 긍정목표가 졸작보다 높게 점수받는 쌍 비율(동점=0.5).
    """
    labels = labels or DEMO_LABELS
    pos = [l for l in labels if l.positive_target]
    poor = [l for l in labels if l.is_poor]
    if not pos or not poor:
        return DiscriminationResult(0.0, len(pos), len(poor), 0, False,
                                    "판별 불가: 긍정 또는 졸작 표본 없음")
    wins = 0.0; total = 0
    for p in pos:
        sp = scorer(p)
        for q in poor:
            sq = scorer(q)
            wins += 1.0 if sp > sq else (0.5 if sp == sq else 0.0)
            total += 1
    auc = round(wins / total, 4)
    passed = auc >= threshold
    detail = (f"판별력 AUC={auc} (긍정 {len(pos)}×졸작 {len(poor)}={total}쌍) "
              f"{'≥' if passed else '<'} 임계 {threshold} → "
              f"{'평가기 신뢰(학습신호 사용가능)' if passed else '판별 약함 → 평가기 보정 선결'}")
    return DiscriminationResult(auc, len(pos), len(poor), total, passed, detail)


def craft_axis_scorer(label: QualityLabel) -> float:
    """기준 비교용: 작품성 축 점수(완벽 라벨 추종 → AUC 상한 확인)."""
    return label.craft
