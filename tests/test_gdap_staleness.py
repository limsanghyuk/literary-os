"""tests/test_gdap_staleness.py — DKGStalenessTracker 단위 테스트 (25 tests)."""
import pytest
from literary_system.gdap.staleness import DKGStalenessTracker
from literary_system.gdap.schema import _sha256_short


@pytest.fixture
def tracker():
    return DKGStalenessTracker()


class TestRegister:
    def test_register_and_is_registered(self, tracker):
        tracker.register("file:a.py", "abc123")
        assert tracker.is_registered("file:a.py")

    def test_unregistered_is_not_registered(self, tracker):
        assert not tracker.is_registered("file:x.py")

    def test_register_stores_hash(self, tracker):
        tracker.register("file:a.py", "deadbeef")
        assert tracker.get_hash("file:a.py") == "deadbeef"

    def test_register_clears_dirty(self, tracker):
        tracker.mark_dirty("file:a.py")
        tracker.register("file:a.py", "newhash")
        assert not tracker.is_dirty("file:a.py")

    def test_register_content_returns_hash(self, tracker):
        h = tracker.register_content("file:a.py", "hello world")
        expected = _sha256_short("hello world")
        assert h == expected

    def test_register_content_registers_node(self, tracker):
        tracker.register_content("file:b.py", "content")
        assert tracker.is_registered("file:b.py")


class TestDirtyFlag:
    def test_mark_dirty(self, tracker):
        tracker.register("n1", "h1")
        tracker.mark_dirty("n1")
        assert tracker.is_dirty("n1")

    def test_not_dirty_initially(self, tracker):
        tracker.register("n1", "h1")
        assert not tracker.is_dirty("n1")

    def test_mark_dirty_if_stale_triggers_on_change(self, tracker):
        tracker.register("n1", "old")
        changed = tracker.mark_dirty_if_stale("n1", "new")
        assert changed and tracker.is_dirty("n1")

    def test_mark_dirty_if_stale_no_trigger_on_same(self, tracker):
        tracker.register("n1", "same")
        changed = tracker.mark_dirty_if_stale("n1", "same")
        assert not changed and not tracker.is_dirty("n1")

    def test_mark_dirty_if_stale_triggers_unregistered(self, tracker):
        # 미등록 → is_stale 반환 True
        changed = tracker.mark_dirty_if_stale("n99", "anyhash")
        assert changed

    def test_mark_dirty_batch_count(self, tracker):
        for i in range(5):
            tracker.register(f"n{i}", f"h{i}")
        cnt = tracker.mark_dirty_batch([f"n{i}" for i in range(5)])
        assert cnt == 5

    def test_mark_dirty_batch_no_double_count(self, tracker):
        tracker.register("n1", "h1")
        tracker.mark_dirty("n1")
        cnt = tracker.mark_dirty_batch(["n1"])
        assert cnt == 0  # 이미 dirty → 추가 카운트 없음

    def test_dirty_nodes_returns_copy(self, tracker):
        tracker.mark_dirty("n1")
        nodes = tracker.dirty_nodes()
        nodes.add("n999")
        assert "n999" not in tracker.dirty_nodes()


class TestClear:
    def test_clear_dirty_removes_flag(self, tracker):
        tracker.mark_dirty("n1")
        tracker.clear_dirty("n1")
        assert not tracker.is_dirty("n1")

    def test_clear_dirty_with_new_hash(self, tracker):
        tracker.register("n1", "old")
        tracker.mark_dirty("n1")
        tracker.clear_dirty("n1", "new")
        assert tracker.get_hash("n1") == "new"
        assert not tracker.is_dirty("n1")

    def test_clear_all_dirty_returns_count(self, tracker):
        for i in range(4):
            tracker.mark_dirty(f"n{i}")
        cleared = tracker.clear_all_dirty()
        assert cleared == 4

    def test_clear_all_dirty_empties_set(self, tracker):
        tracker.mark_dirty("n1")
        tracker.mark_dirty("n2")
        tracker.clear_all_dirty()
        assert len(tracker.dirty_nodes()) == 0


class TestRemove:
    def test_remove_existing(self, tracker):
        tracker.register("n1", "h1")
        existed = tracker.remove("n1")
        assert existed
        assert not tracker.is_registered("n1")

    def test_remove_nonexistent(self, tracker):
        existed = tracker.remove("ghost")
        assert not existed

    def test_remove_clears_dirty(self, tracker):
        tracker.register("n1", "h1")
        tracker.mark_dirty("n1")
        tracker.remove("n1")
        assert not tracker.is_dirty("n1")


class TestStats:
    def test_stats_keys(self, tracker):
        s = tracker.stats()
        assert "registered_count" in s
        assert "dirty_count" in s
        assert "dirty_nodes" in s

    def test_stats_counts(self, tracker):
        tracker.register("n1", "h1")
        tracker.register("n2", "h2")
        tracker.mark_dirty("n1")
        s = tracker.stats()
        assert s["registered_count"] == 2
        assert s["dirty_count"] == 1
