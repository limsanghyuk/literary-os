"""
V323 Phase 3 - SoakReplayExpander 테스트 (20개)
[CSC] N-씬 리플레이 & RelationGraph 드리프트 측정.
"""
import pytest
from literary_system.gate.soak_replay_expander import (
    SoakReplayExpander,
    ReplayScene,
    ReplayResult,
    DriftReport,
)
from literary_system.relation_graph.relation_graph_store import (
    RelationGraphStore, StoryNode, NodeType
)


# -- 헬퍼 -----------------------------------------------------------

def make_rgs(n_nodes=2) -> RelationGraphStore:
    rgs = RelationGraphStore()
    for i in range(n_nodes):
        rgs.add_node(StoryNode(
            node_id=f"n{i}",
            node_type=NodeType.CHARACTER,
            content=f"인물{i}"
        ))
    return rgs


def make_scene(scene_id="s1", text="씬 텍스트", episode=1) -> ReplayScene:
    return ReplayScene(
        scene_id=scene_id,
        scene_text=text,
        episode_no=episode,
        expected_nodes=[],
    )


# ==================================================================
# 1. ReplayScene
# ==================================================================

class TestReplayScene:
    def test_defaults(self):
        s = ReplayScene(scene_id="s1", scene_text="text", episode_no=1)
        assert s.expected_nodes == []
        assert s.metadata == {}

    def test_to_dict(self):
        s = make_scene("s1", "txt", 3)
        d = s.to_dict()
        assert d["scene_id"] == "s1"
        assert d["episode_no"] == 3


# ==================================================================
# 2. DriftReport
# ==================================================================

class TestDriftReport:
    def test_no_drift(self):
        report = DriftReport(
            scene_id="s1",
            nodes_before=5, nodes_after=5,
            edges_before=3, edges_after=3,
            node_delta=0, edge_delta=0,
            drift_score=0.0,
        )
        assert not report.has_drift

    def test_has_drift_nodes(self):
        report = DriftReport(
            scene_id="s1",
            nodes_before=5, nodes_after=7,
            edges_before=3, edges_after=3,
            node_delta=2, edge_delta=0,
            drift_score=0.3,
        )
        assert report.has_drift

    def test_drift_score_non_negative(self):
        report = DriftReport(
            scene_id="s1",
            nodes_before=3, nodes_after=3,
            edges_before=2, edges_after=4,
            node_delta=0, edge_delta=2,
            drift_score=0.5,
        )
        assert report.drift_score >= 0.0

    def test_to_dict_fields(self):
        report = DriftReport(
            scene_id="s1",
            nodes_before=2, nodes_after=3,
            edges_before=1, edges_after=2,
            node_delta=1, edge_delta=1,
            drift_score=0.2,
        )
        d = report.to_dict()
        assert "drift_score" in d
        assert "has_drift" in d
        assert "node_delta" in d


# ==================================================================
# 3. ReplayResult
# ==================================================================

class TestReplayResult:
    def test_basic_fields(self):
        result = ReplayResult(
            scene_id="s1",
            replay_count=5,
            drift_reports=[],
            coherence_violations=0,
            avg_drift_score=0.0,
        )
        assert result.is_coherent

    def test_incoherent_when_violations(self):
        result = ReplayResult(
            scene_id="s1",
            replay_count=5,
            drift_reports=[],
            coherence_violations=1,
            avg_drift_score=0.0,
        )
        assert not result.is_coherent

    def test_to_dict(self):
        result = ReplayResult(
            scene_id="s1",
            replay_count=3,
            drift_reports=[],
            coherence_violations=0,
            avg_drift_score=0.1,
        )
        d = result.to_dict()
        assert "replay_count" in d
        assert "is_coherent" in d


# ==================================================================
# 4. SoakReplayExpander - 기본
# ==================================================================

class TestSoakReplayBasic:
    def test_init(self):
        expander = SoakReplayExpander(n_replays=3)
        assert expander.n_replays == 3

    def test_replay_single_scene(self):
        rgs = make_rgs(2)
        expander = SoakReplayExpander(n_replays=3)
        scene = make_scene("s1")
        result = expander.replay_scene(rgs, scene)
        assert isinstance(result, ReplayResult)
        assert result.scene_id == "s1"
        assert result.replay_count == 3

    def test_replay_no_drift_stable_graph(self):
        """그래프 변경 없으면 드리프트 0."""
        rgs = make_rgs(2)
        expander = SoakReplayExpander(n_replays=5)
        scene = make_scene("s1")
        result = expander.replay_scene(rgs, scene)
        assert result.avg_drift_score == pytest.approx(0.0)

    def test_replay_multiple_scenes(self):
        rgs = make_rgs(3)
        expander = SoakReplayExpander(n_replays=2)
        scenes = [make_scene(f"s{i}", episode=i+1) for i in range(4)]
        results = expander.replay_batch(rgs, scenes)
        assert len(results) == 4

    def test_stats_after_replay(self):
        rgs = make_rgs(2)
        expander = SoakReplayExpander(n_replays=3)
        scene = make_scene("s1")
        expander.replay_scene(rgs, scene)
        s = expander.stats()
        assert "total_replays" in s
        assert "total_violations" in s

    def test_clear_history(self):
        rgs = make_rgs(2)
        expander = SoakReplayExpander(n_replays=2)
        expander.replay_scene(rgs, make_scene("s1"))
        expander.clear()
        s = expander.stats()
        assert s["total_replays"] == 0


# ==================================================================
# 5. SoakReplayExpander - 드리프트 감지
# ==================================================================

class TestSoakReplayDrift:
    def test_drift_detected_on_node_addition(self):
        """리플레이 콜백이 노드를 추가하면 드리프트 감지."""
        rgs = make_rgs(2)

        def mutating_hook(rgs_inner, scene, iteration):
            """매 반복마다 새 노드 추가"""
            rgs_inner.add_node(StoryNode(
                node_id=f"extra_{scene.scene_id}_{iteration}",
                node_type=NodeType.CHARACTER,
                content=f"추가인물{iteration}"
            ))

        expander = SoakReplayExpander(n_replays=3, replay_hook=mutating_hook)
        scene = make_scene("s1")
        result = expander.replay_scene(rgs, scene)
        # 노드가 추가됐으므로 드리프트 > 0
        assert result.avg_drift_score > 0.0

    def test_coherence_violation_on_large_drift(self):
        """드리프트 임계값 초과 시 위반으로 집계."""
        rgs = make_rgs(2)
        call_count = [0]

        def heavy_mutator(rgs_inner, scene, iteration):
            for j in range(5):
                nid = f"bulk_{scene.scene_id}_{iteration}_{j}"
                rgs_inner.add_node(StoryNode(
                    node_id=nid,
                    node_type=NodeType.CHARACTER,
                    content=f"대량추가{j}"
                ))

        expander = SoakReplayExpander(
            n_replays=3,
            replay_hook=heavy_mutator,
            drift_threshold=0.1,
        )
        scene = make_scene("s1")
        result = expander.replay_scene(rgs, scene)
        assert result.coherence_violations > 0
