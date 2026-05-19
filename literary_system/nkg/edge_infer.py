"""V340: NKGEdgeInferEngine — CausalEdge / ForeshadowEdge / InvolvesEdge 추출.

GitNexus의 crossFile phase (CALLS/ACCESSES 엣지 추출)의 서사 도메인 대응물.

추출 전략 (3계층):
  1. 패턴 기반 (항상 실행): 한국어/영어 인과·복선 키워드 매칭
  2. 구조 기반: 장면 인덱스 연속성, 캐릭터 이름 등장 여부
  3. LLM 기반 (선택적, lazy import): 실제 LLM 호출로 정밀 추론
     → V340에서는 Pattern+Structure만 구현. LLM은 V360 확장 포인트.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

from literary_system.nkg.schema import (
    ForeshadowNode,
    NKGEdge,
    NKGEdgeType,
    SceneNode,
)

# ──────────────────────────────────────────────────────────────
#  키워드 사전 (한국어 + 영어)
# ──────────────────────────────────────────────────────────────
_CAUSAL_KW: Tuple[str, ...] = (
    # 한국어 인과
    "때문에", "결국", "그래서", "으로 인해", "에 따라", "덕분에",
    "탓에", "인하여", "로 인해", "그 결과", "이로 인해", "따라서",
    "그러므로", "그로 인해", "그 탓에", "그 덕분에",
    # 영어 인과
    "because", "therefore", "consequently", "as a result",
    "due to", "owing to", "hence", "thus", "caused by",
)

_FORESHADOW_KW: Tuple[str, ...] = (
    # 한국어 복선/암시
    "언젠가", "나중에", "미래에", "그날이 오면", "반드시",
    "꼭", "결코", "틀림없이", "불길한", "예감", "암시",
    "복선", "징조", "전조", "예고", "낌새", "수상한",
    # 영어 복선/암시
    "someday", "eventually", "one day", "foreshadow",
    "ominous", "premonition", "foreboding", "portend",
    "hint", "sign", "omen",
)

_REVEAL_KW: Tuple[str, ...] = (
    # 한국어 회수/폭로
    "드디어", "마침내", "결국", "밝혀졌다", "알게 됐다",
    "사실은", "진실이", "폭로", "드러났다", "밝혀진",
    # 영어 회수
    "finally", "at last", "revealed", "discovered",
    "the truth", "all along", "turns out",
)

_COMPILED_CAUSAL    = re.compile("|".join(re.escape(k) for k in _CAUSAL_KW),    re.I)
_COMPILED_FORESHADOW = re.compile("|".join(re.escape(k) for k in _FORESHADOW_KW), re.I)
_COMPILED_REVEAL     = re.compile("|".join(re.escape(k) for k in _REVEAL_KW),    re.I)


# ──────────────────────────────────────────────────────────────
#  결과 타입
# ──────────────────────────────────────────────────────────────
@dataclass
class EdgeInferResult:
    edges_added:        int = 0
    foreshadow_nodes:   List[ForeshadowNode] = field(default_factory=list)
    causal_pairs:       List[Tuple[str, str]] = field(default_factory=list)
    foreshadow_pairs:   List[Tuple[str, str]] = field(default_factory=list)
    involves_pairs:     List[Tuple[str, str]] = field(default_factory=list)
    errors:             List[str] = field(default_factory=list)


# ──────────────────────────────────────────────────────────────
#  NKGEdgeInferEngine
# ──────────────────────────────────────────────────────────────
class NKGEdgeInferEngine:
    """패턴 + 구조 기반 엣지 추론 엔진.

    사용법::

        engine = NKGEdgeInferEngine()
        result = engine.infer(scene_nodes, char_names=["이준혁","박민아"])
        # result.edges_added, result.causal_pairs, ...
    """

    # 인과 confidence: 키워드 매칭 → 0.75, 순서 연속 기본 → 0.55
    CAUSAL_KW_CONF    = 0.75
    CAUSAL_SEQ_CONF   = 0.55
    # 복선 confidence
    FORESHADOW_CONF   = 0.70
    REVEAL_CONF       = 0.80
    # 캐릭터 등장 confidence
    INVOLVES_CONF     = 0.90
    # 인접 장면 쌍 최대 거리 (index 차이)
    MAX_ADJACENT_GAP  = 3
    # 복선 후보: 앞 장면에 복선 키워드, 뒤 장면에 회수 키워드
    MAX_FORESHADOW_GAP = 15

    def __init__(self, llm_bridge: Any = None) -> None:
        """
        Args:
            llm_bridge: LLMBridgeInterface 인스턴스 (선택적).
                        None이면 패턴 기반만 사용.
        """
        self._llm = llm_bridge
        self._fsh_counter = 0

    # ── 메인 진입점 ──────────────────────────────────────────
    def infer(self, scene_nodes: List[SceneNode],
              char_names: Optional[List[str]] = None,
              existing_edges: Optional[List[NKGEdge]] = None) -> EdgeInferResult:
        """장면 노드 목록에서 엣지를 추론.

        Returns:
            EdgeInferResult: 추론된 엣지 정보 + ForeshadowNode 목록
        """
        result = EdgeInferResult()
        if not scene_nodes:
            return result

        sorted_nodes = sorted(scene_nodes, key=lambda n: n.scene_index)
        existing_pairs: Set[Tuple[str, str]] = set()
        if existing_edges:
            existing_pairs = {(e.source_id, e.target_id) for e in existing_edges}

        edges: List[NKGEdge] = []

        # ① 인과 엣지 추론 (별도 existing 사본 사용 → 복선 엣지와 충돌 방지)
        existing_causal = set(existing_pairs)
        causal_edges = self._infer_causal(sorted_nodes, existing_causal)
        edges.extend(causal_edges)
        result.causal_pairs = [(e.source_id, e.target_id) for e in causal_edges]

        # ② 복선 엣지 추론 (원본 existing_pairs 기반 — 인과와 독립)
        existing_fsh = set(existing_pairs)
        fsh_edges, fsh_nodes = self._infer_foreshadowing(sorted_nodes, existing_fsh)
        edges.extend(fsh_edges)
        result.foreshadow_nodes = fsh_nodes
        result.foreshadow_pairs = [(e.source_id, e.target_id) for e in fsh_edges]

        # ③ 캐릭터 등장 엣지 (INVOLVES)
        if char_names:
            inv_edges = self._infer_involves(sorted_nodes, char_names)
            edges.extend(inv_edges)
            result.involves_pairs = [(e.source_id, e.target_id) for e in inv_edges]

        result.edges_added = len(edges)
        result.edges = edges  # type: ignore[attr-defined]
        return result

    # ── 인과 엣지 ────────────────────────────────────────────
    def _infer_causal(self, nodes: List[SceneNode],
                      existing: Set[Tuple[str, str]]) -> List[NKGEdge]:
        edges: List[NKGEdge] = []
        for i in range(len(nodes)):
            for j in range(i + 1, min(i + 1 + self.MAX_ADJACENT_GAP, len(nodes))):
                src, tgt = nodes[i], nodes[j]
                pair = (src.node_id(), tgt.node_id())
                if pair in existing:
                    continue
                conf = self._causal_confidence(src.content, tgt.content, j - i)
                if conf >= self.CAUSAL_SEQ_CONF:
                    edges.append(NKGEdge(
                        source_id=src.node_id(),
                        target_id=tgt.node_id(),
                        edge_type=NKGEdgeType.CAUSAL_LINK,
                        weight=conf,
                        confidence=conf,
                        metadata={"method": "pattern", "gap": j - i},
                    ))
                    existing.add(pair)
        return edges

    def _causal_confidence(self, src_content: str, tgt_content: str,
                           gap: int) -> float:
        """인과 confidence 계산."""
        # 대상 장면에 인과 키워드가 있으면 가중치 상승
        kw_match = bool(_COMPILED_CAUSAL.search(tgt_content))
        # 소스 장면에 복선 키워드가 있으면 추가 가중치
        src_match = bool(_COMPILED_CAUSAL.search(src_content))
        base = self.CAUSAL_SEQ_CONF if gap == 1 else max(0.4, self.CAUSAL_SEQ_CONF - (gap - 1) * 0.07)
        if kw_match:
            base = min(1.0, base + 0.20)
        if src_match:
            base = min(1.0, base + 0.05)
        return round(base, 3)

    # ── 복선 엣지 ────────────────────────────────────────────
    def _infer_foreshadowing(self,
                             nodes: List[SceneNode],
                             existing: Set[Tuple[str, str]]
                             ) -> Tuple[List[NKGEdge], List[ForeshadowNode]]:
        edges: List[NKGEdge] = []
        fsh_nodes: List[ForeshadowNode] = []

        foreshadow_candidates: List[SceneNode] = []
        for node in nodes:
            if _COMPILED_FORESHADOW.search(node.content):
                foreshadow_candidates.append(node)

        for plant_node in foreshadow_candidates:
            for payoff_node in nodes:
                if payoff_node.scene_index <= plant_node.scene_index:
                    continue
                gap = payoff_node.scene_index - plant_node.scene_index
                if gap > self.MAX_FORESHADOW_GAP:
                    continue
                if not _COMPILED_REVEAL.search(payoff_node.content):
                    continue
                pair = (plant_node.node_id(), payoff_node.node_id())
                if pair in existing:
                    continue

                # ForeshadowingOf 엣지
                conf = min(1.0, self.FORESHADOW_CONF + 0.1 * (1 - gap / self.MAX_FORESHADOW_GAP))
                edges.append(NKGEdge(
                    source_id=plant_node.node_id(),
                    target_id=payoff_node.node_id(),
                    edge_type=NKGEdgeType.FORESHADOWING,
                    weight=conf,
                    confidence=conf,
                    metadata={"gap": gap, "method": "pattern"},
                ))
                # PayoffOf 역방향
                rev_pair = (payoff_node.node_id(), plant_node.node_id())
                if rev_pair not in existing:
                    edges.append(NKGEdge(
                        source_id=payoff_node.node_id(),
                        target_id=plant_node.node_id(),
                        edge_type=NKGEdgeType.PAYOFF,
                        weight=conf * 0.9,
                        confidence=conf,
                        metadata={"gap": gap, "method": "pattern"},
                    ))
                existing.add(pair)
                existing.add(rev_pair)

                # ForeshadowNode 생성
                self._fsh_counter += 1
                fsh = ForeshadowNode(
                    fsh_id=f"fsh_{self._fsh_counter:04d}",
                    description=plant_node.content[:60] + "...",
                    planted_scene=plant_node.node_id(),
                    payoff_scene=payoff_node.node_id(),
                    reveal_budget=1.0,
                )
                fsh_nodes.append(fsh)

        return edges, fsh_nodes

    # ── 캐릭터 등장 엣지 ─────────────────────────────────────
    def _infer_involves(self, nodes: List[SceneNode],
                        char_names: List[str]) -> List[NKGEdge]:
        """장면 텍스트에 캐릭터 이름이 등장하면 INVOLVES 엣지 생성."""
        edges: List[NKGEdge] = []
        seen: Set[Tuple[str, str]] = set()
        for node in nodes:
            for name in char_names:
                if name and name in node.content:
                    _name_safe = re.sub(r'\s+', '_', name)
                    char_id = f"character:{_name_safe}"
                    pair = (node.node_id(), char_id)
                    if pair not in seen:
                        edges.append(NKGEdge(
                            source_id=node.node_id(),
                            target_id=char_id,
                            edge_type=NKGEdgeType.INVOLVES,
                            weight=1.0,
                            confidence=self.INVOLVES_CONF,
                            metadata={"char_name": name},
                        ))
                        seen.add(pair)
        return edges

    # ── 유틸 ─────────────────────────────────────────────────
    @staticmethod
    def has_causal_keyword(text: str) -> bool:
        return bool(_COMPILED_CAUSAL.search(text))

    @staticmethod
    def has_foreshadow_keyword(text: str) -> bool:
        return bool(_COMPILED_FORESHADOW.search(text))

    @staticmethod
    def has_reveal_keyword(text: str) -> bool:
        return bool(_COMPILED_REVEAL.search(text))
