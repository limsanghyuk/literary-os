"""
V411-G — NKGCurator
NKG 저품질 노드 자동 정리 — NarrativeConductor.write_episode() 내
Gate 실행 완료 후, MemoryStore 저장 전에 실행.

정리 기준:
  1. 오래된(stale) 노드: 마지막 등장 에피소드가 MAX_AGE_EPISODES 이전
  2. 약한(weak) 노드: 엣지 평균 weight < MIN_SCORE_THRESHOLD

설계 원칙:
  - NKGGraphStore 인터페이스만 사용 (내부 구조 비침투)
  - 정리 결과를 CurationReport로 반환 (감사 추적)
  - 빈 NKG, 작은 NKG(< MIN_NODES_TO_CURATE)는 스킵
  - LLM 호출 없음 (순수 그래프 수치 계산)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Set

from literary_system.nkg.graph_store import NKGGraphStore


# ────────────────────────────────────────────────────────────────
# CurationReport — 큐레이션 결과 기록
# ────────────────────────────────────────────────────────────────

@dataclass
class CurationReport:
    removed_count: int = 0
    stale_removed: int = 0
    weak_removed:  int = 0
    skipped:       bool = False
    reason:        str = ""
    episode_idx:   int = 0
    timestamp:     str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @property
    def was_cleaned(self) -> bool:
        return self.removed_count > 0


# ────────────────────────────────────────────────────────────────
# NKGCurator
# ────────────────────────────────────────────────────────────────

class NKGCurator:
    """
    NKGGraphStore 저품질 노드 자동 정리.

    Args:
        min_score_threshold: 엣지 평균 weight 하한 (미만이면 약한 노드)
        max_age_episodes:    마지막 에피소드 등장 이후 허용 최대 에피소드 수
        min_nodes_to_curate: 이 수 이하 노드면 큐레이션 건너뜀
    """

    MIN_SCORE_THRESHOLD: float = 0.15
    MAX_AGE_EPISODES:    int   = 20
    MIN_NODES_TO_CURATE: int   = 5    # 소규모 NKG는 건드리지 않음

    def __init__(
        self,
        min_score_threshold: float = MIN_SCORE_THRESHOLD,
        max_age_episodes:    int   = MAX_AGE_EPISODES,
        min_nodes_to_curate: int   = MIN_NODES_TO_CURATE,
    ) -> None:
        self._min_score = min_score_threshold
        self._max_age   = max_age_episodes
        self._min_nodes = min_nodes_to_curate

    # ── 공개 API ─────────────────────────────────────────────────

    def curate(
        self,
        nkg: NKGGraphStore,
        current_episode: int,
    ) -> CurationReport:
        """
        NKG를 정리하고 CurationReport 반환.

        Args:
            nkg:             정리할 NKGGraphStore
            current_episode: 현재 에피소드 인덱스

        Returns:
            CurationReport
        """
        if nkg.node_count() < self._min_nodes:
            return CurationReport(
                skipped=True,
                reason=f"node_count={nkg.node_count()} < min={self._min_nodes}",
                episode_idx=current_episode,
            )

        stale = self._find_stale_nodes(nkg, current_episode)
        weak  = self._find_weak_nodes(nkg)

        # 합집합으로 제거 (중복 제거)
        to_remove = stale | weak
        for node_id in to_remove:
            nkg.remove_node(node_id)

        stale_removed = len(stale & to_remove)
        weak_removed  = len(weak  & to_remove) - len(stale & weak & to_remove)

        return CurationReport(
            removed_count = len(to_remove),
            stale_removed = len(stale),
            weak_removed  = len(weak - stale),   # stale과 겹치지 않는 순수 weak
            skipped       = False,
            reason        = "auto_curation",
            episode_idx   = current_episode,
        )

    def preview(
        self,
        nkg: NKGGraphStore,
        current_episode: int,
    ) -> CurationReport:
        """
        실제 제거 없이 제거 대상만 계산하여 반환.
        드라이런(dry-run) 확인용.
        """
        if nkg.node_count() < self._min_nodes:
            return CurationReport(
                skipped=True,
                reason=f"preview:node_count={nkg.node_count()} < min={self._min_nodes}",
                episode_idx=current_episode,
            )
        stale = self._find_stale_nodes(nkg, current_episode)
        weak  = self._find_weak_nodes(nkg)
        to_remove = stale | weak
        return CurationReport(
            removed_count = len(to_remove),
            stale_removed = len(stale),
            weak_removed  = len(weak - stale),
            skipped       = False,
            reason        = "preview_only",
            episode_idx   = current_episode,
        )

    # ── 내부 메서드 ─────────────────────────────────────────────

    def _find_stale_nodes(
        self,
        nkg: NKGGraphStore,
        current_episode: int,
    ) -> Set[str]:
        """
        마지막 등장 에피소드가 MAX_AGE_EPISODES 이전인 노드 탐색.
        노드 metadata['episode_index'] 또는 NKGNode.episode_index 필드 참조.
        """
        stale: Set[str] = set()
        cutoff = current_episode - self._max_age

        for node in nkg.all_nodes():
            ep = self._get_episode_index(node)
            if ep is not None and ep < cutoff:
                stale.add(node.node_id)
        return stale

    def _find_weak_nodes(self, nkg: NKGGraphStore) -> Set[str]:
        """
        연결된 엣지의 평균 weight < MIN_SCORE_THRESHOLD 인 노드 탐색.
        엣지가 전혀 없는 노드(고립 노드)도 약한 노드로 간주.
        """
        weak: Set[str] = set()
        for node in nkg.all_nodes():
            out_edges = nkg.edges_from(node.node_id)
            in_edges  = nkg.edges_to(node.node_id)
            all_edges = out_edges + in_edges

            if not all_edges:
                # 고립 노드 — 약한 것으로 간주
                weak.add(node.node_id)
                continue

            avg_weight = sum(e.weight for e in all_edges) / len(all_edges)
            if avg_weight < self._min_score:
                weak.add(node.node_id)
        return weak

    @staticmethod
    def _get_episode_index(node) -> Optional[int]:
        """노드에서 에피소드 인덱스 추출 (다양한 스키마 지원)."""
        # NKGNode 서브클래스별 필드
        if hasattr(node, "episode_index"):
            return node.episode_index
        # metadata dict 폴백
        if hasattr(node, "metadata") and isinstance(node.metadata, dict):
            return node.metadata.get("episode_index")
        return None
