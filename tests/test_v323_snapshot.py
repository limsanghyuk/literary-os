"""
V323 Phase 1 — SnapshotManager 테스트 (20개)
[CSC] JSON 직렬화 스냅샷 & 롤백 검증.
"""
import json
import pytest
from literary_system.action_compiler.snapshot_manager import Snapshot, SnapshotManager
from literary_system.relation_graph.relation_graph_store import (
    RelationGraphStore, StoryNode, StoryEdge, NodeType, RelationType
)


def make_graph(nodes=None):
    """테스트용 그래프 생성."""
    rgs = RelationGraphStore()
    default_nodes = nodes or [
        StoryNode(node_id="n1", node_type=NodeType.CHARACTER, content="김민준"),
        StoryNode(node_id="n2", node_type=NodeType.CHARACTER, content="이서연"),
    ]
    for n in default_nodes:
        rgs.add_node(n)
    return rgs


# ── 1. 기본 push/pop ────────────────────────────────────────────

class TestBasicPushPop:
    def test_push_returns_snapshot_id(self):
        mgr = SnapshotManager()
        rgs = make_graph()
        snap_id = mgr.push_snapshot(rgs, label="test")
        assert isinstance(snap_id, str)
        assert len(snap_id) > 0

    def test_depth_increases_on_push(self):
        mgr = SnapshotManager()
        rgs = make_graph()
        assert mgr.depth == 0
        mgr.push_snapshot(rgs, label="first")
        assert mgr.depth == 1
        mgr.push_snapshot(rgs, label="second")
        assert mgr.depth == 2

    def test_pop_restores_graph(self):
        mgr = SnapshotManager()
        rgs = make_graph()
        mgr.push_snapshot(rgs, label="before")

        # 그래프 변경
        rgs.add_node(StoryNode(node_id="n3", node_type=NodeType.CHARACTER, content="박준혁"))
        assert len(rgs.all_nodes()) == 3

        # 롤백
        rgs, _ = mgr.pop_snapshot(rgs)
        assert len(rgs.all_nodes()) == 2

    def test_pop_empty_raises(self):
        mgr = SnapshotManager()
        rgs = make_graph()
        with pytest.raises(RuntimeError):
            mgr.pop_snapshot(rgs)

    def test_is_empty_flag(self):
        mgr = SnapshotManager()
        rgs = make_graph()
        assert mgr.is_empty
        mgr.push_snapshot(rgs)
        assert not mgr.is_empty


# ── 2. peek & list ─────────────────────────────────────────────

class TestPeekAndList:
    def test_peek_returns_latest(self):
        mgr = SnapshotManager()
        rgs = make_graph()
        mgr.push_snapshot(rgs, label="alpha")
        mgr.push_snapshot(rgs, label="beta")
        snap = mgr.peek_snapshot()
        assert snap.label == "beta"

    def test_peek_does_not_pop(self):
        mgr = SnapshotManager()
        rgs = make_graph()
        mgr.push_snapshot(rgs, label="test")
        mgr.peek_snapshot()
        assert mgr.depth == 1

    def test_list_snapshots(self):
        mgr = SnapshotManager()
        rgs = make_graph()
        mgr.push_snapshot(rgs, label="s1")
        mgr.push_snapshot(rgs, label="s2")
        listing = mgr.list_snapshots()
        assert len(listing) == 2
        assert listing[0]["label"] == "s1"
        assert listing[1]["label"] == "s2"


# ── 3. 스택 크기 제한 ────────────────────────────────────────────

class TestStackSizeLimit:
    def test_max_stack_size_enforced(self):
        mgr = SnapshotManager(max_stack_size=3)
        rgs = make_graph()
        for i in range(5):
            mgr.push_snapshot(rgs, label=f"s{i}")
        assert mgr.depth == 3

    def test_oldest_removed_on_overflow(self):
        mgr = SnapshotManager(max_stack_size=2)
        rgs = make_graph()
        mgr.push_snapshot(rgs, label="oldest")
        mgr.push_snapshot(rgs, label="middle")
        mgr.push_snapshot(rgs, label="newest")
        labels = [s["label"] for s in mgr.list_snapshots()]
        assert "oldest" not in labels
        assert "newest" in labels


# ── 4. JSON 직렬화 ────────────────────────────────────────────────

class TestJsonSerialization:
    def test_snapshot_json_serializable(self):
        mgr = SnapshotManager()
        rgs = make_graph()
        mgr.push_snapshot(rgs, label="json_test")
        snap = mgr.peek_snapshot()
        # to_dict가 JSON 직렬화 가능한지 확인
        d = snap.to_dict()
        json_str = json.dumps(d)
        assert isinstance(json_str, str)

    def test_snapshot_from_dict_roundtrip(self):
        mgr = SnapshotManager()
        rgs = make_graph()
        mgr.push_snapshot(rgs, label="roundtrip")
        snap = mgr.peek_snapshot()
        restored = Snapshot.from_dict(snap.to_dict())
        assert restored.label == snap.label
        assert restored.graph_json == snap.graph_json


# ── 5. 디스크 퍼시스턴스 ─────────────────────────────────────────

class TestDiskPersistence:
    def test_disk_save(self, tmp_path):
        mgr = SnapshotManager(snapshot_dir=tmp_path)
        rgs = make_graph()
        snap_id = mgr.push_snapshot(rgs, label="disk_test")
        expected_file = tmp_path / f"snapshot_{snap_id}.json"
        assert expected_file.exists()

    def test_disk_load(self, tmp_path):
        mgr = SnapshotManager(snapshot_dir=tmp_path)
        rgs = make_graph()
        snap_id = mgr.push_snapshot(rgs, label="load_test")
        loaded = mgr.load_from_disk(snap_id)
        assert loaded is not None
        assert loaded.label == "load_test"

    def test_stats_with_disk(self, tmp_path):
        mgr = SnapshotManager(snapshot_dir=tmp_path)
        s = mgr.stats()
        assert s["has_disk_persistence"] is True
        assert s["disk_dir"] is not None


# ── 6. clear ─────────────────────────────────────────────────────

class TestClear:
    def test_clear_empties_stack(self):
        mgr = SnapshotManager()
        rgs = make_graph()
        mgr.push_snapshot(rgs)
        mgr.push_snapshot(rgs)
        mgr.clear()
        assert mgr.is_empty

    def test_commit_is_noop(self):
        mgr = SnapshotManager()
        rgs = make_graph()
        mgr.push_snapshot(rgs, label="pre")
        mgr.commit()
        assert mgr.depth == 1
