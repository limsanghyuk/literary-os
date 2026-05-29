"""V340: NKGEmotionalLinker — EmotionalMomentumTracker → EmotionalEchoEdge.

V328 EmotionalMomentumTracker의 4D 벡터(tension·sympathy·dread·catharsis)를
NKG 감정 레이어로 연결하는 어댑터.

설계 원칙 (설계도 §2.1 감정 레이어):
  - EmotionalEcho:  단방향, A→B로 감정이 전파 (cosine similarity > ECHO_THRESH)
  - Resonance:      양방향, 두 장면이 강하게 공명 (similarity > RESONANCE_THRESH)
  - 사이클 허용:    감정 레이어는 BFS + visited set으로 감쇠 방문
  - EMT 연동:       history()에서 역대 벡터를 읽어 장면 간 흐름 분석
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from literary_system.nkg.schema import NKGEdge, NKGEdgeType, SceneNode


# ──────────────────────────────────────────────────────────────
#  벡터 연산 유틸
# ──────────────────────────────────────────────────────────────
def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """4D 벡터 코사인 유사도 [-1, 1]. 둘 다 0벡터면 1.0 반환."""
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(x * x for x in b))
    if mag_a < 1e-9 or mag_b < 1e-9:
        return 1.0
    return dot / (mag_a * mag_b)


def _euclidean_distance(a: List[float], b: List[float]) -> float:
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def _ev_delta(a: List[float], b: List[float]) -> List[float]:
    """두 EmotionalVector의 변화량 (b - a)."""
    return [b[i] - a[i] for i in range(min(len(a), len(b)))]


# ──────────────────────────────────────────────────────────────
#  결과 타입
# ──────────────────────────────────────────────────────────────
@dataclass
class EmotionalLinkResult:
    echo_edges:      List[NKGEdge] = field(default_factory=list)
    resonance_edges: List[NKGEdge] = field(default_factory=list)
    total_edges:     int = 0
    max_similarity:  float = 0.0
    mean_similarity: float = 0.0

    def all_edges(self) -> List[NKGEdge]:
        return self.echo_edges + self.resonance_edges


# ──────────────────────────────────────────────────────────────
#  NKGEmotionalLinker
# ──────────────────────────────────────────────────────────────
class NKGEmotionalLinker:
    """EmotionalMomentumTracker ↔ NKG 감정 레이어 연결기.

    사용법::

        linker = NKGEmotionalLinker()
        result = linker.link(scene_nodes)          # 독립 사용
        result = linker.link_with_tracker(         # EMT 연동
            scene_nodes, emt_instance)
    """

    ECHO_THRESH      = 0.75   # EmotionalEcho 엣지 생성 임계값
    RESONANCE_THRESH = 0.90   # Resonance (양방향) 엣지 생성 임계값
    MAX_PAIR_GAP     = 20     # 비교할 최대 장면 인덱스 차이

    def __init__(self) -> None:
        self._pair_cache: Dict[Tuple[str, str], float] = {}

    # ── 메인 진입점 ──────────────────────────────────────────
    def link(self, scene_nodes: List[SceneNode],
             existing_edges: Optional[List[NKGEdge]] = None) -> EmotionalLinkResult:
        """장면 노드의 emotional_vector 기반으로 감정 엣지 생성.

        Args:
            scene_nodes:    SceneNode 목록 (emotional_vector 포함).
            existing_edges: 중복 방지용 기존 엣지 목록.
        """
        result = EmotionalLinkResult()
        if len(scene_nodes) < 2:
            return result

        existing_pairs: Set[Tuple[str, str]] = set()
        if existing_edges:
            existing_pairs = {(e.source_id, e.target_id) for e in existing_edges}

        sorted_nodes = sorted(scene_nodes, key=lambda n: n.scene_index)
        sims: List[float] = []

        for i, src in enumerate(sorted_nodes):
            for j in range(i + 1, len(sorted_nodes)):
                tgt = sorted_nodes[j]
                if tgt.scene_index - src.scene_index > self.MAX_PAIR_GAP:
                    break

                sim = _cosine_similarity(src.emotional_vector, tgt.emotional_vector)
                sims.append(sim)
                self._pair_cache[(src.node_id(), tgt.node_id())] = sim

                if sim >= self.RESONANCE_THRESH:
                    # Resonance: 양방향
                    for s_id, t_id in [(src.node_id(), tgt.node_id()),
                                       (tgt.node_id(), src.node_id())]:
                        if (s_id, t_id) not in existing_pairs:
                            result.resonance_edges.append(NKGEdge(
                                source_id=s_id, target_id=t_id,
                                edge_type=NKGEdgeType.RESONANCE,
                                weight=round(sim, 3),
                                confidence=round(sim, 3),
                                metadata={"similarity": round(sim, 3),
                                          "gap": tgt.scene_index - src.scene_index},
                            ))
                            existing_pairs.add((s_id, t_id))

                elif sim >= self.ECHO_THRESH:
                    # EmotionalEcho: 단방향 (감정 전파 방향)
                    pair = (src.node_id(), tgt.node_id())
                    if pair not in existing_pairs:
                        result.echo_edges.append(NKGEdge(
                            source_id=src.node_id(),
                            target_id=tgt.node_id(),
                            edge_type=NKGEdgeType.EMOTIONAL_ECHO,
                            weight=round(sim, 3),
                            confidence=round(sim, 3),
                            metadata={"similarity": round(sim, 3),
                                      "gap": tgt.scene_index - src.scene_index},
                        ))
                        existing_pairs.add(pair)

        result.total_edges = len(result.echo_edges) + len(result.resonance_edges)
        if sims:
            result.max_similarity  = round(max(sims), 4)
            result.mean_similarity = round(sum(sims) / len(sims), 4)
        return result

    # ── EMT 연동 ─────────────────────────────────────────────
    def link_with_tracker(self, scene_nodes: List[SceneNode],
                          emt: Any,
                          existing_edges: Optional[List[NKGEdge]] = None
                          ) -> EmotionalLinkResult:
        """EmotionalMomentumTracker의 history를 이용해 감정 흐름 보강.

        EMT history의 각 벡터를 scene_nodes 순서에 맞춰 적용.
        EMT 벡터를 scene의 emotional_vector에 ALPHA 비율로 혼합하여
        더 정밀한 감정 연결을 생성한다.

        Args:
            emt: EmotionalMomentumTracker 인스턴스.
        """
        ALPHA = 0.30   # EMT 혼합 비율

        emt_history = []
        try:
            emt_history = emt.history() if hasattr(emt, "history") else []
        except Exception:
            pass

        if not emt_history:
            return self.link(scene_nodes, existing_edges)

        # EMT 벡터를 scene 순서에 맞춰 혼합
        sorted_nodes = sorted(scene_nodes, key=lambda n: n.scene_index)
        enhanced: List[SceneNode] = []
        for i, node in enumerate(sorted_nodes):
            if i < len(emt_history):
                ev_hist = emt_history[i]
                hist_list = [
                    getattr(ev_hist, "tension",   0.5),
                    getattr(ev_hist, "sympathy",  0.5),
                    getattr(ev_hist, "dread",     0.3),
                    getattr(ev_hist, "catharsis", 0.0),
                ]
                # 원본 벡터와 EMT 벡터 혼합
                mixed = [
                    (1 - ALPHA) * node.emotional_vector[k] + ALPHA * float(hist_list[k])
                    for k in range(4)
                ]
                # 임시 복사본 생성 (원본 불변)
                import dataclasses
                enhanced_node = dataclasses.replace(node, emotional_vector=mixed)
                enhanced.append(enhanced_node)
            else:
                enhanced.append(node)

        return self.link(enhanced, existing_edges)

    # ── 진단 ─────────────────────────────────────────────────
    def get_similarity(self, node_id_a: str, node_id_b: str) -> Optional[float]:
        """두 노드 간 캐시된 유사도 반환."""
        return self._pair_cache.get((node_id_a, node_id_b))

    def top_resonant_pairs(self, n: int = 5) -> List[Tuple[str, str, float]]:
        """유사도 상위 n쌍 반환."""
        sorted_pairs = sorted(self._pair_cache.items(),
                              key=lambda x: x[1], reverse=True)
        return [(a, b, sim) for (a, b), sim in sorted_pairs[:n]]

    @staticmethod
    def compute_similarity(ev_a: List[float], ev_b: List[float]) -> float:
        """외부에서 직접 유사도 계산."""
        return _cosine_similarity(ev_a, ev_b)

    @staticmethod
    def compute_ev_delta(ev_a: List[float], ev_b: List[float]) -> List[float]:
        return _ev_delta(ev_a, ev_b)
