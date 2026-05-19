"""
V380: arc/series_arc_planner.py — SeriesArcPlanner

16부작 전체 드라마 아크를 CausalPlotGraph로 자동 생성.

설계 원칙:
  1. 4막(기/승/전/결) 분배: 기(25%) 승(35%) 전(25%) 결(15%)
  2. S자형 텐션 곡선: 기=낮음, 승=중간, 전=절정, 결=여운
  3. 복선 예산 자동 할당: 기/승 구간은 낮게, 전/결 구간은 높게
  4. 회차별 감정 목표 자동 설정 (8개 패턴 순환)
  5. 모든 에피소드에 순방향 인과 연결 (ep_n → ep_n+1)

LLM 0회.
"""
from __future__ import annotations
import logging

import math
from typing import Dict, List, Optional

from literary_system.arc.schema import ArcAct, ArcPlotEdge, ArcPlotEdgeType, ArcPlotNode
from literary_system.arc.causal_plot_graph import CausalPlotGraph

logger = logging.getLogger(__name__)


# 회차별 감정 목표 패턴 (16부작 기준 순환)
_EMOTIONAL_TARGETS_16 = [
    "기대감",   # 1화 — 세계 입장
    "궁금증",   # 2화 — 수수께끼 제시
    "설렘",     # 3화 — 관계 형성
    "불안",     # 4화 — 균열 시작
    "갈등",     # 5화 — 대립 본격화
    "긴장",     # 6화 — 위기 심화
    "의심",     # 7화 — 배신 암시
    "충격",     # 8화 — 1차 반전
    "분노",     # 9화 — 감정 폭발
    "절망",     # 10화 — 최저점
    "결의",     # 11화 — 회복 시작
    "희망",     # 12화 — 전환점
    "서스펜스", # 13화 — 최종 결전 전야
    "카타르시스",# 14화 — 절정
    "여운",     # 15화 — 해소
    "평온",     # 16화 — 엔딩
]

# 4막 텐션 기저값 (S자형)
_ACT_TENSION_BASE: Dict[str, float] = {
    ArcAct.GI.value:    0.25,
    ArcAct.SEUNG.value: 0.55,
    ArcAct.JEON.value:  0.85,
    ArcAct.GYEOL.value: 0.45,
}

# 복선 예산 (막별)
_ACT_REVEAL_BUDGET: Dict[str, float] = {
    ArcAct.GI.value:    0.1,
    ArcAct.SEUNG.value: 0.2,
    ArcAct.JEON.value:  0.7,
    ArcAct.GYEOL.value: 0.9,
}


class SeriesArcPlanner:
    """
    16부작 드라마 아크를 CausalPlotGraph로 자동 생성하는 플래너.

    사용 예:
        planner = SeriesArcPlanner(total_episodes=16, series_title="비밀의 숲")
        graph = planner.plan()
        logger.debug(graph.summary())
    """

    # 4막 분배 비율 (기:승:전:결)
    ACT_RATIOS = [
        (ArcAct.GI,    0.25),
        (ArcAct.SEUNG, 0.35),
        (ArcAct.JEON,  0.25),
        (ArcAct.GYEOL, 0.15),
    ]

    def __init__(
        self,
        total_episodes: int = 16,
        series_title:   str = "시리즈",
        tension_mode:   str = "sigmoid",  # "sigmoid" | "linear"
    ) -> None:
        if total_episodes < 2:
            raise ValueError(f"total_episodes는 2 이상이어야 합니다: {total_episodes}")
        self.total_episodes = total_episodes
        self.series_title   = series_title
        self.tension_mode   = tension_mode

    # ── 공개 API ──────────────────────────────────────────────────
    def plan(self, graph: Optional[CausalPlotGraph] = None) -> CausalPlotGraph:
        """
        CausalPlotGraph를 생성·반환.
        graph가 주어지면 해당 그래프에 노드/엣지를 추가한다.
        """
        if graph is None:
            graph = CausalPlotGraph()

        act_assignments = self._assign_acts()
        for idx, act in enumerate(act_assignments):
            ep_idx   = idx + 1  # 1-based
            ep_id    = f"ep_{ep_idx:02d}"
            tension  = self._tension_value(ep_idx)
            emotional= self._emotional_target(ep_idx)
            r_budget = self._reveal_budget(act, ep_idx)

            # 이전 에피소드를 인과 입력으로 연결
            causal_inputs = [f"ep_{ep_idx - 1:02d}"] if ep_idx > 1 else []

            node = ArcPlotNode(
                episode_id=       ep_id,
                episode_index=    ep_idx,
                title=            f"{self.series_title} {ep_idx}화",
                act=              act,
                reveal_budget=    r_budget,
                emotional_target= emotional,
                causal_inputs=    causal_inputs,
                tension_level=    tension,
            )
            graph.add_node(node)

        # 엣지 자동 추론 (순서 중요)
        graph.infer_causal_edges()
        graph.infer_foreshadow_edges()
        graph.infer_emotional_escalation_edges()
        return graph

    def plan_custom(
        self,
        episode_specs: List[Dict],
    ) -> CausalPlotGraph:
        """
        episode_specs 리스트에서 ArcPlotNode를 생성하여 그래프를 구성.
        각 spec: {episode_id, episode_index, title, act, reveal_budget,
                  emotional_target, causal_inputs, tension_level}
        """
        graph = CausalPlotGraph()
        for spec in episode_specs:
            act_val = spec.get("act", "기")
            try:
                act = ArcAct(act_val)
            except ValueError:
                act = ArcAct.GI
            node = ArcPlotNode(
                episode_id=       spec.get("episode_id", f"ep_{spec.get('episode_index', 0):02d}"),
                episode_index=    spec.get("episode_index", 0),
                title=            spec.get("title", ""),
                act=              act,
                reveal_budget=    float(spec.get("reveal_budget", 0.3)),
                emotional_target= spec.get("emotional_target", "중립"),
                causal_inputs=    spec.get("causal_inputs", []),
                tension_level=    float(spec.get("tension_level", 0.5)),
                forbidden_reveals=spec.get("forbidden_reveals", []),
                metadata=         spec.get("metadata", {}),
            )
            graph.add_node(node)
        graph.infer_causal_edges()
        graph.infer_foreshadow_edges()
        graph.infer_emotional_escalation_edges()
        return graph

    # ── 내부 헬퍼 ─────────────────────────────────────────────────
    def _assign_acts(self) -> List[ArcAct]:
        """total_episodes를 4막 비율로 배분."""
        acts: List[ArcAct] = []
        remaining = self.total_episodes
        for i, (act, ratio) in enumerate(self.ACT_RATIOS):
            if i == len(self.ACT_RATIOS) - 1:
                count = remaining
            else:
                count = max(1, round(self.total_episodes * ratio))
                remaining -= count
            acts.extend([act] * count)
        # 길이 맞추기
        while len(acts) < self.total_episodes:
            acts.append(ArcAct.GYEOL)
        return acts[:self.total_episodes]

    def _tension_value(self, ep_idx: int) -> float:
        """S자형 또는 선형 텐션 곡선 계산."""
        t = (ep_idx - 1) / max(self.total_episodes - 1, 1)  # 0.0~1.0
        if self.tension_mode == "sigmoid":
            # S자형: 중간 지점에서 빠르게 상승, 마지막에 하강
            if t < 0.7:
                raw = 1 / (1 + math.exp(-10 * (t - 0.4)))
            else:
                # 결말 하강
                raw = 1 / (1 + math.exp(-10 * (t - 0.4))) * (1 - (t - 0.7) * 2)
            return round(max(0.1, min(1.0, raw)), 3)
        else:
            # 선형
            return round(0.1 + 0.8 * t, 3)

    def _emotional_target(self, ep_idx: int) -> str:
        """에피소드 회차에 맞는 감정 목표 반환."""
        targets = _EMOTIONAL_TARGETS_16
        idx = (ep_idx - 1) % len(targets)
        return targets[idx]

    def _reveal_budget(self, act: ArcAct, ep_idx: int) -> float:
        """막 기반 복선 예산 + 회차 내 미세 변동."""
        base = _ACT_REVEAL_BUDGET.get(act.value, 0.3)
        # 마지막 화에 가까울수록 예산 증가
        progress = ep_idx / self.total_episodes
        return round(min(1.0, base + progress * 0.1), 3)
