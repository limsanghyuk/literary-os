"""
quality/quality_labels.py — 2축 외부 품질 라벨 (V775, ADR-235).

사용자 정정 반영: 흥행 성공작도 '명작 계열(긍정 학습 목표)'에 포함.
단 인기≠작품성 교란을 막기 위해 **2축 분리**:
  - craft(작품성): 전문가 평점·수상·평단 합의 (1순위 예술 축)
  - commercial(흥행성): 시청률·관객수 (대중/상업 성공 축)
둘 다 [0,1] 외부 신호(전문가+일반인+흥행). **모델 자기 critic 라벨링 금지(순환)**.

등급:
  MASTERPIECE_BOTH  craft高·commercial高   (긍정)
  CRAFT_MASTERPIECE craft高·commercial非高  무명 걸작 (긍정)
  COMMERCIAL_HIT    commercial高·craft非高  흥행작 (긍정) ← 흥행 성공 = 명작 계열
  AVERAGE           중간                    (중립)
  POOR              둘 다 低                졸작=대조 신호(부정)
positive_target = {MASTERPIECE_BOTH, CRAFT_MASTERPIECE, COMMERCIAL_HIT}
LLM-0: 순수 라벨 로직(외부 신호만, LLM 미호출).
"""
from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, List

HIGH = 0.70
LOW = 0.50


class QualityTier(str, Enum):
    MASTERPIECE_BOTH  = "masterpiece_both"
    CRAFT_MASTERPIECE = "craft_masterpiece"
    COMMERCIAL_HIT    = "commercial_hit"
    AVERAGE           = "average"
    POOR              = "poor"


@dataclass(frozen=True)
class QualityLabel_Quality:
    work:        str
    craft:       float       # 작품성 [0,1] (전문가·수상)
    commercial:  float       # 흥행성 [0,1] (시청률·관객)
    tier:        QualityTier
    note:        str = ""

    @property
    def positive_target(self) -> bool:
        return self.tier in (QualityTier.MASTERPIECE_BOTH,
                             QualityTier.CRAFT_MASTERPIECE, QualityTier.COMMERCIAL_HIT)

    @property
    def is_poor(self) -> bool:
        return self.tier == QualityTier.POOR

    def to_dict(self) -> Dict[str, Any]:
        return {"work": self.work, "craft": self.craft, "commercial": self.commercial,
                "tier": self.tier.value, "positive_target": self.positive_target, "note": self.note}


def classify(craft: float, commercial: float) -> QualityTier:
    ch, ah = craft >= HIGH, commercial >= HIGH
    cl, al = craft < LOW, commercial < LOW
    if ch and ah:  return QualityTier.MASTERPIECE_BOTH
    if ch:         return QualityTier.CRAFT_MASTERPIECE
    if ah:         return QualityTier.COMMERCIAL_HIT       # 흥행작 → 명작 계열
    if cl and al:  return QualityTier.POOR
    return QualityTier.AVERAGE


def make_label(work: str, craft: float, commercial: float, note: str = "") -> QualityLabel_Quality:
    return QualityLabel_Quality(work, round(craft, 3), round(commercial, 3), classify(craft, commercial), note)


# 14편 데모(quality_labels_v1.md 근거 → 2축 점수화). 근사값(데모).
DEMO_LABELS: List[QualityLabel_Quality] = [
    make_label("살인의 추억", 0.97, 0.85, "전문가·캐논 최상"),
    make_label("마더",        0.92, 0.70, "봉준호 대표작"),
    make_label("박쥐",        0.90, 0.55, "칸 심사위원상"),
    make_label("곡성",        0.85, 0.78, "687만·문제작"),
    make_label("신세계",      0.82, 0.75, "평·대중 호평"),
    make_label("미생",        0.90, 0.88, "직장극 명작·신드롬"),
    make_label("시그널",      0.90, 0.80, "백상 극본상·12.5%"),
    make_label("써니",        0.60, 0.85, "736만 대중 수작"),
    make_label("과속스캔들",  0.55, 0.85, "824만 흥행"),
    make_label("태양의 후예", 0.45, 0.95, "시청률 38.8% 흥행대작 → 흥행 명작"),
    make_label("신사의 품격", 0.50, 0.65, "김은숙 대중극"),
    make_label("각설탕",      0.45, 0.35, "144만 부진"),
    make_label("미스터 소크라테스", 0.40, 0.45, "산만·졸작 경계"),
]


def summary(labels: List[QualityLabel_Quality] = None) -> Dict[str, int]:
    labels = labels or DEMO_LABELS
    out: Dict[str, int] = {}
    for l in labels:
        out[l.tier.value] = out.get(l.tier.value, 0) + 1
    out["positive_target"] = sum(1 for l in labels if l.positive_target)
    out["poor"] = sum(1 for l in labels if l.is_poor)
    return out


# G37 DuplicateZero(ADR-033): 클래스명 전역 고유화 — 외부 import 하위호환 별칭
QualityLabel = QualityLabel_Quality
