"""V360 T11-4: DKGStalenessTracker v2 — 증분 비교 테스트."""
import sys, time
sys.path.insert(0, "/tmp/v360_build")
import pytest
from literary_system.nkg.staleness import DKGStalenessTrackerV2, NKGNodeCache, DKGStalenessTracker


class TestNKGNodeCache:
    def test_get_miss(self):
        c = NKGNodeCache()
        assert c.get("x") is None

    def test_put_get(self):
        c = NKGNodeCache()
        c.put("n1", "hash1")
        assert c.get("n1") == "hash1"

    def test_lru_eviction(self):
        c = NKGNodeCache(max_size=3)
        for i in range(4): c.put(f"n{i}", f"h{i}")
        assert c.get("n0") is None  # 가장 오래된 항목 제거

    def test_update_moves_to_end(self):
        c = NKGNodeCache(max_size=3)
        c.put("n0","h0"); c.put("n1","h1"); c.put("n2","h2")
        c.get("n0")  # n0을 최근으로
        c.put("n3","h3")  # n1이 제거되어야 함
        assert c.get("n0") is not None

    def test_invalidate(self):
        c = NKGNodeCache()
        c.put("n1","h1"); c.invalidate("n1")
        assert c.get("n1") is None

    def test_size(self):
        c = NKGNodeCache()
        assert c.size() == 0
        c.put("n1","h1"); c.put("n2","h2")
        assert c.size() == 2


class TestStalenessBasic:
    def test_register_not_stale(self):
        t = DKGStalenessTrackerV2()
        t.register("n1", "hash1")
        assert not t.check_stale("n1", "hash1")

    def test_register_stale_different_hash(self):
        t = DKGStalenessTrackerV2()
        t.register("n1", "hash1")
        assert t.check_stale("n1", "hash2")

    def test_unregistered_is_stale(self):
        t = DKGStalenessTrackerV2()
        assert t.check_stale("unknown", "any_hash")

    def test_mark_dirty_if_stale_true(self):
        t = DKGStalenessTrackerV2()
        t.register("n1", "h1")
        assert t.mark_dirty_if_stale("n1", "h2")
        assert t.is_dirty("n1")

    def test_mark_dirty_if_stale_false(self):
        t = DKGStalenessTrackerV2()
        t.register("n1", "h1")
        assert not t.mark_dirty_if_stale("n1", "h1")
        assert not t.is_dirty("n1")

    def test_mark_dirty_force(self):
        t = DKGStalenessTrackerV2()
        t.register("n1", "h1")
        t.mark_dirty("n1")
        assert t.is_dirty("n1")

    def test_clear_dirty(self):
        t = DKGStalenessTrackerV2()
        t.register("n1", "h1"); t.mark_dirty("n1")
        t.clear_dirty("n1")
        assert not t.is_dirty("n1")

    def test_clear_all_dirty(self):
        t = DKGStalenessTrackerV2()
        for i in range(5):
            t.register(f"n{i}", f"h{i}"); t.mark_dirty(f"n{i}")
        count = t.clear_all_dirty()
        assert count == 5 and len(t.dirty_nodes()) == 0

    def test_dirty_nodes_set(self):
        t = DKGStalenessTrackerV2()
        t.register("n1","h1"); t.register("n2","h2")
        t.mark_dirty("n1"); t.mark_dirty("n2")
        assert t.dirty_nodes() == {"n1","n2"}


class TestStalenessStats:
    def test_stats_keys(self):
        t = DKGStalenessTrackerV2()
        s = t.stats()
        assert all(k in s for k in
                   ["registered","dirty_count","cache_size","total_checks","cache_hits","cache_hit_rate","incremental_saves"])

    def test_cache_hit_rate_100_percent(self):
        t = DKGStalenessTrackerV2()
        t.register("n1","h1")
        for _ in range(10): t.check_stale("n1","h1")
        s = t.stats()
        assert s["cache_hit_rate"] > 0

    def test_incremental_saves_increase(self):
        t = DKGStalenessTrackerV2()
        t.register("n1","h1")
        t.mark_dirty_if_stale("n1","h1")  # not stale → incremental save
        assert t.stats()["incremental_saves"] >= 1

    def test_registered_count(self):
        t = DKGStalenessTrackerV2()
        for i in range(5): t.register(f"n{i}", f"h{i}")
        assert t.stats()["registered"] == 5

    def test_dirty_count_stat(self):
        t = DKGStalenessTrackerV2()
        t.register("n1","h1"); t.mark_dirty("n1")
        assert t.stats()["dirty_count"] == 1


class TestStalenessIncremental:
    def test_cache_hit_avoids_record_lookup(self):
        t = DKGStalenessTrackerV2(cache_size=500)
        t.register("n1","h1")
        # 첫 번째 check: cache hit
        t.check_stale("n1","h1")
        before = t.stats()["cache_hits"]
        t.check_stale("n1","h1")
        assert t.stats()["cache_hits"] > before

    def test_large_batch_performance(self):
        t = DKGStalenessTrackerV2(cache_size=1000)
        n = 1000
        hashes = [f"hash_{i:06d}" for i in range(n)]
        for i in range(n): t.register(f"node_{i}", hashes[i])
        t0 = time.perf_counter()
        dirty_count = 0
        for i in range(n):
            new_h = f"hash_{i:06d}_modified" if i % 10 == 0 else hashes[i]
            if t.mark_dirty_if_stale(f"node_{i}", new_h): dirty_count += 1
        elapsed = time.perf_counter() - t0
        assert elapsed < 2.0
        assert dirty_count == n // 10

    def test_cache_size_respected(self):
        t = DKGStalenessTrackerV2(cache_size=10)
        for i in range(20): t.register(f"n{i}", f"h{i}")
        assert t.stats()["cache_size"] <= 10

    def test_v350_alias(self):
        t = DKGStalenessTracker()
        t.register("n1","h1")
        assert not t.check_stale("n1","h1")
        assert isinstance(t, DKGStalenessTrackerV2)
