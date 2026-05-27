"""
test_v651_memory_cache.py — V651 EnsembleMemoryCache 단위 테스트 (30 TC).
TTL / LRU / stats / 만료 검증.
"""
import time
import pytest
from literary_system.ensemble.memory_cache import (
    EnsembleCacheEntry, EnsembleCacheStats, EnsembleMemoryCache,
    DEFAULT_TTL_SECONDS, DEFAULT_MAX_SIZE,
)


def _make_result(scene_id="s01", text="hello") -> dict:
    return {"scene_id": scene_id, "final_text": text, "rounds_used": 1, "success": True}


# ── TC-01~05: EnsembleCacheEntry ──────────────────────────────────────────────────────

class TestCacheEntry:
    def test_tc01_fields(self):
        e = EnsembleCacheEntry(scene_id="s", result_dict={}, ttl=60.0)
        assert hasattr(e, "scene_id")
        assert hasattr(e, "result_dict")
        assert hasattr(e, "created_at")
        assert hasattr(e, "ttl")

    def test_tc02_not_expired_fresh(self):
        e = EnsembleCacheEntry(scene_id="s", result_dict={}, ttl=3600.0)
        assert e.is_expired() is False

    def test_tc03_expired_past(self):
        e = EnsembleCacheEntry(scene_id="s", result_dict={}, created_at=time.time() - 7200.0, ttl=3600.0)
        assert e.is_expired() is True

    def test_tc04_expired_at_boundary(self):
        now = time.time()
        e = EnsembleCacheEntry(scene_id="s", result_dict={}, created_at=now - 3601.0, ttl=3600.0)
        assert e.is_expired() is True

    def test_tc05_is_expired_with_explicit_now(self):
        e = EnsembleCacheEntry(scene_id="s", result_dict={}, created_at=1000.0, ttl=100.0)
        assert e.is_expired(now=1099.0) is False
        assert e.is_expired(now=1100.0) is True


# ── TC-06~10: EnsembleCacheStats ──────────────────────────────────────────────────────

class TestCacheStats:
    def test_tc06_initial_zeros(self):
        s = EnsembleCacheStats()
        assert s.hits == 0 and s.misses == 0 and s.evictions == 0

    def test_tc07_hit_rate_zero_division(self):
        s = EnsembleCacheStats()
        assert s.hit_rate == 0.0

    def test_tc08_hit_rate_calculation(self):
        s = EnsembleCacheStats(hits=3, misses=1)
        assert s.hit_rate == pytest.approx(0.75)

    def test_tc09_to_dict_keys(self):
        s = EnsembleCacheStats(hits=5, misses=2)
        d = s.to_dict()
        for k in ("size", "hits", "misses", "evictions", "expirations", "hit_rate"):
            assert k in d

    def test_tc10_to_dict_values(self):
        s = EnsembleCacheStats(hits=3, misses=1, evictions=2)
        d = s.to_dict()
        assert d["hits"] == 3
        assert d["hit_rate"] == pytest.approx(0.75)


# ── TC-11~15: EnsembleMemoryCache 기본 동작 ───────────────────────────────────

class TestCacheBasic:
    def test_tc11_instantiate_defaults(self):
        c = EnsembleMemoryCache()
        assert c.max_size == DEFAULT_MAX_SIZE
        assert c.ttl == DEFAULT_TTL_SECONDS

    def test_tc12_put_and_get(self):
        c = EnsembleMemoryCache()
        r = _make_result("s01")
        c.put("s01", r)
        got = c.get("s01")
        assert got == r

    def test_tc13_get_missing_returns_none(self):
        c = EnsembleMemoryCache()
        assert c.get("nonexistent") is None

    def test_tc14_size_increments(self):
        c = EnsembleMemoryCache()
        c.put("a", _make_result("a"))
        c.put("b", _make_result("b"))
        assert c.size == 2

    def test_tc15_contains_existing(self):
        c = EnsembleMemoryCache()
        c.put("s1", _make_result("s1"))
        assert c.contains("s1") is True


# ── TC-16~20: TTL 만료 ────────────────────────────────────────────────────────

class TestTTLExpiry:
    def test_tc16_expired_get_returns_none(self):
        c = EnsembleMemoryCache(ttl=0.05)
        c.put("s", _make_result("s"))
        time.sleep(0.1)
        assert c.get("s") is None

    def test_tc17_expired_removed_from_size(self):
        c = EnsembleMemoryCache(ttl=0.05)
        c.put("s", _make_result("s"))
        time.sleep(0.1)
        c.get("s")  # 만료 → 삭제
        assert c.size == 0

    def test_tc18_expiration_stat_incremented(self):
        c = EnsembleMemoryCache(ttl=0.05)
        c.put("s", _make_result("s"))
        time.sleep(0.1)
        c.get("s")
        assert c.stats().expirations == 1

    def test_tc19_purge_expired(self):
        c = EnsembleMemoryCache(ttl=0.05)
        c.put("a", _make_result("a"))
        c.put("b", _make_result("b"))
        time.sleep(0.1)
        removed = c.purge_expired()
        assert removed == 2
        assert c.size == 0

    def test_tc20_contains_expired_false(self):
        c = EnsembleMemoryCache(ttl=0.05)
        c.put("s", _make_result("s"))
        time.sleep(0.1)
        assert c.contains("s") is False


# ── TC-21~25: LRU 퇴출 ────────────────────────────────────────────────────────

class TestLRUEviction:
    def test_tc21_max_size_1_evicts_old(self):
        c = EnsembleMemoryCache(max_size=1)
        c.put("a", _make_result("a"))
        c.put("b", _make_result("b"))
        assert c.size == 1
        assert c.get("b") is not None   # 최신 항목 유지
        assert c.get("a") is None       # 퇴출된 항목

    def test_tc22_eviction_stat_incremented(self):
        c = EnsembleMemoryCache(max_size=2)
        c.put("a", _make_result("a"))
        c.put("b", _make_result("b"))
        c.put("c", _make_result("c"))
        assert c.stats().evictions >= 1

    def test_tc23_put_updates_existing(self):
        c = EnsembleMemoryCache()
        c.put("s", _make_result("s", text="v1"))
        c.put("s", _make_result("s", text="v2"))
        assert c.get("s")["final_text"] == "v2"
        assert c.size == 1

    def test_tc24_lru_order_after_get(self):
        """a→b 삽입, a 조회 후 새 항목 c 삽입 시 b가 퇴출."""
        c = EnsembleMemoryCache(max_size=2)
        c.put("a", _make_result("a"))
        c.put("b", _make_result("b"))
        c.get("a")          # a 를 최근 사용으로 갱신
        c.put("c", _make_result("c"))  # b 퇴출
        assert c.get("a") is not None
        assert c.get("c") is not None
        assert c.get("b") is None

    def test_tc25_max_size_respected(self):
        max_sz = 5
        c = EnsembleMemoryCache(max_size=max_sz)
        for i in range(10):
            c.put(f"s{i}", _make_result(f"s{i}"))
        assert c.size <= max_sz


# ── TC-26~30: invalidate / clear / stats / 에지케이스 ─────────────────────────

class TestInvalidateClearStats:
    def test_tc26_invalidate_existing(self):
        c = EnsembleMemoryCache()
        c.put("s", _make_result("s"))
        assert c.invalidate("s") is True
        assert c.get("s") is None

    def test_tc27_invalidate_nonexistent(self):
        c = EnsembleMemoryCache()
        assert c.invalidate("ghost") is False

    def test_tc28_clear_returns_count(self):
        c = EnsembleMemoryCache()
        for i in range(5):
            c.put(f"s{i}", _make_result(f"s{i}"))
        n = c.clear()
        assert n == 5
        assert c.size == 0

    def test_tc29_stats_hit_miss_tracking(self):
        c = EnsembleMemoryCache()
        c.put("s1", _make_result("s1"))
        c.get("s1")      # hit
        c.get("s1")      # hit
        c.get("ghost")   # miss
        s = c.stats()
        assert s.hits == 2
        assert s.misses == 1

    def test_tc30_invalid_params_raise(self):
        with pytest.raises(ValueError):
            EnsembleMemoryCache(max_size=0)
        with pytest.raises(ValueError):
            EnsembleMemoryCache(ttl=-1.0)
