"""
V323 - SoakReplayExpander  (Phase 3)
N-씬 리플레이 & RelationGraph 드리프트 측정.

설계 원칙 (CSA/CSC/CPE 합의):
  - 동일 씬을 n_replays 회 반복 실행
  - 매 반복마다 그래프 노드/엣지 수 스냅샷 비교
  - drift_score = (node_delta + edge_delta) / (nodes_before + 1)
  - drift_threshold 초과 시 coherence_violation 카운트
  - replay_hook: 외부 콜백으로 실제 씬 처리 로직 주입 (테스트/프로덕션 공용)
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

# ================================================================
# ReplayScene - 리플레이 대상 씬 정의
# ================================================================

@dataclass
class ReplayScene:
    """리플레이 대상 씬."""
    scene_id: str
    scene_text: str
    episode_no: int
    expected_nodes: list[str] = field(default_factory=list)
    metadata: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "scene_text": self.scene_text[:80],
            "episode_no": self.episode_no,
            "expected_nodes": self.expected_nodes,
            "metadata": self.metadata,
        }


# ================================================================
# DriftReport - 단일 반복 드리프트 리포트
# ================================================================

@dataclass
class DriftReport:
    """단일 리플레이 반복의 드리프트 측정치."""
    scene_id: str
    nodes_before: int
    nodes_after: int
    edges_before: int
    edges_after: int
    node_delta: int
    edge_delta: int
    drift_score: float

    @property
    def has_drift(self) -> bool:
        return self.node_delta != 0 or self.edge_delta != 0

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "nodes_before": self.nodes_before,
            "nodes_after": self.nodes_after,
            "edges_before": self.edges_before,
            "edges_after": self.edges_after,
            "node_delta": self.node_delta,
            "edge_delta": self.edge_delta,
            "drift_score": self.drift_score,
            "has_drift": self.has_drift,
        }


# ================================================================
# ReplayResult - 씬 리플레이 전체 결과
# ================================================================

@dataclass
class ReplayResult:
    """단일 씬의 n_replays 전체 결과."""
    scene_id: str
    replay_count: int
    drift_reports: list[DriftReport]
    coherence_violations: int
    avg_drift_score: float

    @property
    def is_coherent(self) -> bool:
        return self.coherence_violations == 0

    def to_dict(self) -> dict:
        return {
            "scene_id": self.scene_id,
            "replay_count": self.replay_count,
            "coherence_violations": self.coherence_violations,
            "avg_drift_score": self.avg_drift_score,
            "is_coherent": self.is_coherent,
            "drift_reports": [r.to_dict() for r in self.drift_reports],
        }


# ================================================================
# SoakReplayExpander
# ================================================================

class SoakReplayExpander:
    """
    V323 Phase 3 장기 소크 테스트 확장기.

    replay_hook(rgs, scene, iteration):
        씬 처리 로직을 외부에서 주입.
        None이면 노-op (그래프 변경 없음).
        테스트에서는 의도적 돌연변이 훅을 주입하여 드리프트 유발.
        프로덕션에서는 실제 씬 처리 파이프라인 연결.
    """

    def __init__(
        self,
        n_replays: int = 10,
        replay_hook: Callable | None = None,
        drift_threshold: float = 0.5,
    ):
        self._n_replays = max(1, n_replays)
        self._hook = replay_hook
        self._drift_threshold = drift_threshold
        self._results: list[ReplayResult] = []

    @property
    def n_replays(self) -> int:
        return self._n_replays

    def replay_scene(self, rgs, scene: ReplayScene) -> ReplayResult:
        """
        단일 씬을 n_replays 회 반복 실행하며 드리프트 측정.
        rgs는 in-place로 수정될 수 있다 (후크 의존적).
        """
        drift_reports: list[DriftReport] = []
        violations = 0

        for i in range(self._n_replays):
            nodes_before = len(rgs.all_nodes())
            edges_before = self._count_edges(rgs)

            # 후크 실행 (씬 처리 로직)
            if self._hook is not None:
                self._hook(rgs, scene, i)

            nodes_after = len(rgs.all_nodes())
            edges_after = self._count_edges(rgs)

            node_delta = nodes_after - nodes_before
            edge_delta = edges_after - edges_before
            drift_score = (abs(node_delta) + abs(edge_delta)) / max(nodes_before + 1, 1)

            report = DriftReport(
                scene_id=scene.scene_id,
                nodes_before=nodes_before,
                nodes_after=nodes_after,
                edges_before=edges_before,
                edges_after=edges_after,
                node_delta=node_delta,
                edge_delta=edge_delta,
                drift_score=round(drift_score, 6),
            )
            drift_reports.append(report)

            if drift_score > self._drift_threshold:
                violations += 1

        avg_drift = (
            sum(r.drift_score for r in drift_reports) / len(drift_reports)
            if drift_reports else 0.0
        )

        result = ReplayResult(
            scene_id=scene.scene_id,
            replay_count=self._n_replays,
            drift_reports=drift_reports,
            coherence_violations=violations,
            avg_drift_score=round(avg_drift, 6),
        )
        self._results.append(result)
        return result

    def replay_batch(self, rgs, scenes: list[ReplayScene]) -> list[ReplayResult]:
        """씬 목록 일괄 리플레이."""
        return [self.replay_scene(rgs, scene) for scene in scenes]

    def clear(self) -> None:
        self._results.clear()

    def stats(self) -> dict[str, Any]:
        total_replays = sum(r.replay_count for r in self._results)
        total_violations = sum(r.coherence_violations for r in self._results)
        avg_drift = (
            sum(r.avg_drift_score for r in self._results) / len(self._results)
            if self._results else 0.0
        )
        return {
            "scenes_tested": len(self._results),
            "total_replays": total_replays,
            "total_violations": total_violations,
            "avg_drift_score": round(avg_drift, 6),
            "n_replays_per_scene": self._n_replays,
            "drift_threshold": self._drift_threshold,
        }

    def _count_edges(self, rgs) -> int:
        """RelationGraphStore 전체 엣지 수."""
        try:
            return rgs._graph.number_of_edges()
        except Exception:
            return 0
