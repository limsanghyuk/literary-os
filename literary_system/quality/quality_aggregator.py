"""
quality/quality_aggregator.py — 다신호 → 2축 품질 점수 자동 집계 (V776, ADR-236).

외부 신호(전문가 평점·시청률/흥행·수상·채널)를 정규화·가중하여 craft/commercial [0,1] 산출.
→ V775 classify로 등급화. 14편 데모를 넘어 전 코퍼스 자동 라벨링의 엔진.

정규화 원칙:
- commercial = 시청률 / 채널 천장 (케이블은 천장 낮춤 = 채널 보정). 영화는 관객수 정규화.
- craft = 전문가(0~4)/4 + 수상 보너스. **외부 신호만**(모델 자기 critic 금지).
- 인기≠작품성: 두 축 독립 산출(흥행이 craft에 새지 않음).
LLM-0: 순수 산술(외부 신호), LLM 미호출.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from literary_system.quality.quality_labels import QualityLabel, classify

# 채널별 시청률 천장(%) — 케이블은 절대수치가 낮으므로 보정
CHANNEL_CEILING = {"KBS": 45.0, "MBC": 45.0, "SBS": 45.0, "지상파": 45.0,
                   "tvN": 10.0, "JTBC": 10.0, "OCN": 8.0, "케이블": 10.0}
DEFAULT_CEILING = 45.0
FILM_BOXOFFICE_CEILING_M = 1000.0   # 천만(만명 단위 입력 시 1000만)
AWARD_BONUS = 0.08                  # 수상 1건당 craft 보너스


def _clamp(x: float) -> float:
    return max(0.0, min(1.0, round(x, 4)))


def commercial_from_viewership(viewership_pct: float, channel: str = "") -> float:
    ceil = CHANNEL_CEILING.get(channel, DEFAULT_CEILING)
    return _clamp(viewership_pct / ceil)


def commercial_from_boxoffice(admissions_10k: float) -> float:
    """관객수(만명) → [0,1]. 1000만=1.0."""
    return _clamp(admissions_10k / FILM_BOXOFFICE_CEILING_M)


def craft_from_expert(expert_0_4: float, awards: int = 0) -> float:
    return _clamp(expert_0_4 / 4.0 + AWARD_BONUS * max(0, awards))


@dataclass
class AggInput:
    work:            str
    expert_0_4:      float
    viewership_pct:  Optional[float] = None   # 드라마
    channel:         str = ""
    admissions_10k:  Optional[float] = None   # 영화(만명)
    awards:          int = 0
    note:            str = ""


def aggregate(inp: AggInput) -> QualityLabel:
    craft = craft_from_expert(inp.expert_0_4, inp.awards)
    if inp.admissions_10k is not None:
        commercial = commercial_from_boxoffice(inp.admissions_10k)
    elif inp.viewership_pct is not None:
        commercial = commercial_from_viewership(inp.viewership_pct, inp.channel)
    else:
        commercial = 0.0
    tier = classify(craft, commercial)
    return QualityLabel(inp.work, craft, commercial, tier, inp.note)


def build_labels(records: List[AggInput]) -> List[QualityLabel]:
    return [aggregate(r) for r in records]


def from_drama_dict(drama: Dict[str, Any]) -> List[QualityLabel]:
    """meta_gt_drama.DRAMA 포맷 {series:(시청률, expert0~4, channel)} → 라벨."""
    out: List[QualityLabel] = []
    for work, v in drama.items():
        view, expert, channel = (list(v) + ["", "", ""])[:3]
        out.append(aggregate(AggInput(work, float(expert), viewership_pct=float(view), channel=str(channel))))
    return out


def label_summary(labels: List[QualityLabel]) -> Dict[str, Any]:
    tiers: Dict[str, int] = {}
    for l in labels:
        tiers[l.tier.value] = tiers.get(l.tier.value, 0) + 1
    return {"total": len(labels), "tiers": tiers,
            "positive_target": sum(1 for l in labels if l.positive_target),
            "poor": sum(1 for l in labels if l.is_poor)}
