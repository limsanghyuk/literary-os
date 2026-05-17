"""
V380: arc/schema.py — SeriesArc 도메인 스키마

ArcPlotNode: 16부작 에피소드 아크 노드 (act 기/승/전/결)
ArcPlotEdge: 에피소드 간 관계 엣지 (CAUSAL/FORESHADOW/CALLBACK/EMOTIONAL_ESCALATION)
CausalPlotGraph는 이 스키마 위에서 동작한다.

LLM 0회.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


# ── 기/승/전/결 4막 구조 ──────────────────────────────────────────
class ArcAct(str, Enum):
    GI   = "기"   # 도입 — 인물·세계 설정
    SEUNG= "승"   # 전개 — 갈등 심화
    JEON = "전"   # 위기 — 반전·절정
    GYEOL= "결"   # 결말 — 해소·여운


# ── 에피소드 간 엣지 유형 ─────────────────────────────────────────
class ArcPlotEdgeType(str, Enum):
    CAUSAL              = "CAUSAL"               # 인과 연쇄 (A→B 사건 결과)
    FORESHADOW          = "FORESHADOW"           # 복선 심기 (A에서 심어 B에서 회수)
    CALLBACK            = "CALLBACK"             # 복선 회수 (FORESHADOW의 역방향)
    EMOTIONAL_ESCALATION= "EMOTIONAL_ESCALATION" # 감정 고조 연결


# ── ArcPlotNode — 에피소드 단위 아크 노드 ─────────────────────────
@dataclass
class ArcPlotNode:
    """
    16부작 CausalPlotGraph의 에피소드 노드.

    Fields:
        episode_id      : 고유 ID (예: "ep_01")
        episode_index   : 1-based 회차 번호
        title           : 에피소드 제목 (작업 제목)
        act             : 기/승/전/결 중 하나
        reveal_budget   : 이 화에서 허용된 복선 공개 예산 (0.0~1.0)
        emotional_target: 이 화의 감정 목표 레이블 (예: "불안", "희망")
        causal_inputs   : 이 에피소드에 인과적으로 입력되는 에피소드 ID 목록
        tension_level   : 이 화의 텐션 수치 (0.0~1.0)
        forbidden_reveals: 이 화에서 절대 공개하면 안 되는 사실 ID 목록
        metadata        : 추가 메타데이터
    """
    episode_id:       str
    episode_index:    int
    title:            str              = ""
    act:              ArcAct           = ArcAct.GI
    reveal_budget:    float            = 0.3
    emotional_target: str              = "중립"
    causal_inputs:    List[str]        = field(default_factory=list)
    tension_level:    float            = 0.5
    forbidden_reveals:List[str]        = field(default_factory=list)
    metadata:         Dict[str, Any]   = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "episode_id":       self.episode_id,
            "episode_index":    self.episode_index,
            "title":            self.title,
            "act":              self.act.value,
            "reveal_budget":    self.reveal_budget,
            "emotional_target": self.emotional_target,
            "causal_inputs":    self.causal_inputs,
            "tension_level":    self.tension_level,
            "forbidden_reveals":self.forbidden_reveals,
        }


# ── ArcPlotEdge — 에피소드 간 연결 엣지 ───────────────────────────
@dataclass
class ArcPlotEdge:
    """
    CausalPlotGraph 내 에피소드 간 방향성 엣지.
    """
    source:      str             # 출발 episode_id
    target:      str             # 도착 episode_id
    edge_type:   ArcPlotEdgeType
    weight:      float           = 1.0
    description: str             = ""
    metadata:    Dict[str, Any]  = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source":      self.source,
            "target":      self.target,
            "edge_type":   self.edge_type.value,
            "weight":      self.weight,
            "description": self.description,
        }
