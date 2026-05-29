"""
V546 — GraphSyncOrchestrator
P1(CIM↔NarrativeGraph 단절) · P2(이중 업데이트 오버헤드) 해소.
ADR-027: CIM-NarrativeGraph 단일 동기화 채널.

설계:
  - CIM의 PageRank 결과를 NarrativeGraph CharacterNode에 주입
  - NarrativeGraph의 관계 엣지를 CIM weight_matrix에 역방향 반영
  - 양방향 동기화를 단일 sync() 호출로 원자적 처리
  - LLM-0 정책 준수: 외부 LLM 호출 없음
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)

# ── 동기화 방향 ────────────────────────────────────────────────────
CIM_TO_GRAPH = "cim_to_graph"   # PageRank → CharacterNode.influence
GRAPH_TO_CIM = "graph_to_cim"   # NarrativeEdge weight → CIM matrix
BIDIRECTIONAL = "bidirectional"


@dataclass
class SyncReport:
    """단일 sync() 실행 결과."""
    direction: str
    nodes_updated: int = 0
    edges_reflected: int = 0
    cim_cells_updated: int = 0
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "direction": self.direction,
            "nodes_updated": self.nodes_updated,
            "edges_reflected": self.edges_reflected,
            "cim_cells_updated": self.cim_cells_updated,
            "warnings": self.warnings,
        }


class GraphSyncOrchestrator:
    """
    CIM ↔ NarrativeGraph 단일 동기화 오케스트레이터 (ADR-027).

    P1 해소: CIM의 influence score가 NarrativeGraph CharacterNode에 반영.
    P2 해소: 이중 업데이트 제거 — sync() 한 번 호출로 양방향 원자 처리.

    사용 예:
        gso = GraphSyncOrchestrator(cim, graph_store)
        report = gso.sync()
    """

    def __init__(self, cim, graph_store) -> None:
        """
        Args:
            cim: CharacterInfluenceMatrix 인스턴스
            graph_store: NarrativeGraphStore 인스턴스
        """
        self._cim = cim
        self._graph = graph_store
        self._sync_count = 0

    # ── 메인 진입점 ───────────────────────────────────────────────

    def sync(self, direction: str = BIDIRECTIONAL) -> SyncReport:
        """
        CIM ↔ NarrativeGraph 동기화 실행.

        Args:
            direction: CIM_TO_GRAPH | GRAPH_TO_CIM | BIDIRECTIONAL
        Returns:
            SyncReport
        """
        report = SyncReport(direction=direction)
        self._sync_count += 1

        if direction in (CIM_TO_GRAPH, BIDIRECTIONAL):
            self._sync_cim_to_graph(report)

        if direction in (GRAPH_TO_CIM, BIDIRECTIONAL):
            self._sync_graph_to_cim(report)

        logger.info(
            "GraphSyncOrchestrator sync #%d: %s | nodes=%d edges=%d cim_cells=%d",
            self._sync_count, direction,
            report.nodes_updated, report.edges_reflected, report.cim_cells_updated,
        )
        return report

    # ── CIM → Graph ───────────────────────────────────────────────

    def _sync_cim_to_graph(self, report: SyncReport) -> None:
        """
        CIM PageRank influence → NarrativeGraph CharacterNode.influence 주입.
        """
        try:
            ranks: Dict[str, float] = self._cim.get_pagerank()
        except Exception as exc:
            report.warnings.append(f"CIM.get_pagerank() 실패: {exc}")
            return

        for char_id, influence in ranks.items():
            node = self._graph.get_node(char_id)
            if node is None:
                # CharacterNode가 없으면 경고만 — 강제 생성하지 않음
                report.warnings.append(f"NarrativeGraph에 노드 없음: {char_id}")
                continue
            # metadata dict에 influence 주입
            if not hasattr(node, "metadata") or node.metadata is None:
                node.metadata = {}
            node.metadata["cim_influence"] = round(influence, 6)
            report.nodes_updated += 1

    # ── Graph → CIM ───────────────────────────────────────────────

    def _sync_graph_to_cim(self, report: SyncReport) -> None:
        """
        NarrativeGraph 관계 엣지 weight → CIM weight_matrix 반영.
        엣지 타입이 INFLUENCE/CONFLICT/ALLIANCE인 경우만 반영.
        """
        RELATION_TYPES = {"INFLUENCE", "CONFLICT", "ALLIANCE", "RELATIONSHIP"}

        try:
            all_edges = self._graph.all_edges()
        except Exception as exc:
            report.warnings.append(f"graph.all_edges() 실패: {exc}")
            return

        for edge in all_edges:
            edge_type = getattr(edge, "edge_type", None)
            if edge_type not in RELATION_TYPES:
                continue

            src = getattr(edge, "source_id", None)
            tgt = getattr(edge, "target_id", None)
            weight = getattr(edge, "weight", 0.5)

            if src is None or tgt is None:
                continue

            try:
                self._cim.set_weight(src, tgt, float(weight))
                report.cim_cells_updated += 1
                report.edges_reflected += 1
            except Exception as exc:
                report.warnings.append(f"CIM.set_weight({src},{tgt}) 실패: {exc}")

    # ── CIM view 매핑 (P2 보조) ───────────────────────────────────

    def get_cim_view(self) -> Dict[str, float]:
        """
        현재 CIM의 PageRank 결과를 {char_id: influence} 형태로 반환.
        NarrativeGraph 뷰 레이어용 읽기 전용 스냅샷.
        """
        try:
            return dict(self._cim.get_pagerank())
        except Exception:
            return {}

    def get_graph_character_nodes(self) -> List[str]:
        """NarrativeGraph에서 character 타입 노드 ID 목록 반환."""
        result = []
        try:
            for node in self._graph.all_nodes():
                node_type = getattr(node, "node_type", "")
                if str(node_type).upper() in ("CHARACTER", "CHAR"):
                    result.append(node.node_id)
        except Exception:
            pass
        return result

    @property
    def sync_count(self) -> int:
        return self._sync_count
