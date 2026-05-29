"""V360: DKGStalenessTracker v2 — 심화 테스트."""
import sys, time, hashlib
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.nkg.staleness import DKGStalenessTrackerV2, NKGNodeCache

class TestCacheEdgeCases:
    def test_cache_max_size_1(self):
        c = NKGNodeCache(max_size=1)
        c.put("a", "h1"); c.put("b", "h2")
        assert c.get("a") is None  # evicted
        assert c.get("b") == "h2"

    def test_overwrite_same_key(self):
        c = NKGNodeCache(max_size=5)
        c.put("k", "v1"); c.put("k", "v2")
        assert c.get("k") == "v2" and c.size() == 1

    def test_invalidate_nonexistent_ok(self):
        c = NKGNodeCache()
        c.invalidate("nonexistent")  # 예외 없음

    def test_lru_order_preserved(self):
        c = NKGNodeCache(max_size=3)
        c.put("a","h1"); c.put("b","h2"); c.put("c","h3")
        c.get("a")       # a → 최근
        c.put("d","h4")  # b 제거
        assert c.get("b") is None and c.get("a") is not None

    def test_cache_size_zero_not_crash(self):
        c = NKGNodeCache(max_size=1)
        for i in range(10): c.put(f"k{i}", f"v{i}")
        assert c.size() <= 1

class TestTrackerTimestamp:
    def test_register_with_explicit_timestamp(self):
        t = DKGStalenessTrackerV2()
        ts = time.time() - 1000
        t.register("n1", "h1", timestamp=ts)
        assert not t.check_stale("n1", "h1")

    def test_mark_dirty_if_stale_updates_timestamp(self):
        t = DKGStalenessTrackerV2()
        ts_old = time.time() - 100
        t.register("n1", "h1", timestamp=ts_old)
        t.mark_dirty_if_stale("n1", "h2", new_timestamp=time.time())
        rec = t._records["n1"]
        assert rec.last_modified > ts_old

    def test_check_stale_same_hash_different_time(self):
        t = DKGStalenessTrackerV2()
        t.register("n1", "h1")
        # 같은 해시 → stale 아님 (타임스탬프 무관)
        assert not t.check_stale("n1", "h1", new_timestamp=time.time()+9999)

    def test_multiple_registers_overwrite(self):
        t = DKGStalenessTrackerV2()
        t.register("n1", "h1"); t.register("n1", "h2")
        assert not t.check_stale("n1", "h2")
        assert t.check_stale("n1", "h1")  # 이전 해시는 stale

    def test_clear_all_dirty_returns_count(self):
        t = DKGStalenessTrackerV2()
        for i in range(7): t.register(f"n{i}", f"h{i}"); t.mark_dirty(f"n{i}")
        assert t.clear_all_dirty() == 7

class TestTrackerStats:
    def test_stats_total_checks_accumulate(self):
        t = DKGStalenessTrackerV2()
        t.register("n1", "h1")
        for _ in range(5): t.check_stale("n1", "h1")
        assert t.stats()["total_checks"] == 5

    def test_stats_cache_hit_rate_0_on_miss(self):
        t = DKGStalenessTrackerV2()
        t.check_stale("unknown1", "h"); t.check_stale("unknown2", "h")
        assert t.stats()["cache_hit_rate"] == 0.0

    def test_stats_dirty_count_after_mark(self):
        t = DKGStalenessTrackerV2()
        t.register("n1","h1"); t.register("n2","h2")
        t.mark_dirty("n1")
        assert t.stats()["dirty_count"] == 1

    def test_stats_after_clear_all(self):
        t = DKGStalenessTrackerV2()
        for i in range(5): t.register(f"n{i}",f"h{i}"); t.mark_dirty(f"n{i}")
        t.clear_all_dirty()
        assert t.stats()["dirty_count"] == 0

    def test_incremental_saves_vs_total_checks(self):
        t = DKGStalenessTrackerV2()
        t.register("n1","h1")
        for _ in range(10): t.mark_dirty_if_stale("n1","h1")
        s = t.stats()
        assert s["incremental_saves"] + s["dirty_count"] <= s["total_checks"] + 10

class TestTrackerBulkOperations:
    def test_1000_nodes_register_and_check(self):
        t = DKGStalenessTrackerV2(cache_size=500)
        for i in range(1000): t.register(f"n{i}", f"hash_{i:06d}")
        t0 = time.perf_counter()
        changed = 0
        for i in range(1000):
            new_h = f"hash_{i:06d}_new" if i % 5 == 0 else f"hash_{i:06d}"
            if t.mark_dirty_if_stale(f"n{i}", new_h): changed += 1
        assert time.perf_counter() - t0 < 2.0
        assert changed == 200  # 1000 / 5

    def test_dirty_nodes_after_bulk_mark(self):
        t = DKGStalenessTrackerV2()
        for i in range(20): t.register(f"n{i}", f"h{i}")
        for i in range(0, 20, 2): t.mark_dirty(f"n{i}")
        assert len(t.dirty_nodes()) == 10

    def test_clear_subset_dirty(self):
        t = DKGStalenessTrackerV2()
        for i in range(5): t.register(f"n{i}",f"h{i}"); t.mark_dirty(f"n{i}")
        t.clear_dirty("n0"); t.clear_dirty("n1")
        assert len(t.dirty_nodes()) == 3

    def test_is_dirty_false_after_register(self):
        t = DKGStalenessTrackerV2()
        t.register("n1","h1"); t.mark_dirty("n1")
        t.register("n1","h1_new")  # 재등록 → dirty 해제
        assert not t.is_dirty("n1")
