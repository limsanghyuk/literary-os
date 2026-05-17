"""
tests/test_v487_cached_gateway.py
V487 CachedGateway + SemanticCacheLayer 테스트
"""
import pytest
from unittest.mock import MagicMock

from literary_system.llm_bridge.cached_gateway import CachedGateway, CacheStats
from literary_system.llm_bridge.llm_context import LLMResponse


@pytest.fixture
def mock_resp():
    return LLMResponse(text="씬 생성 완료", provider_id="haiku", latency_ms=80.0)


@pytest.fixture
def cached_gw(mock_resp):
    gw = MagicMock()
    gw.call.return_value = mock_resp
    return CachedGateway(gateway=gw, enabled=True)


class TestCachedGatewayBasic:

    def test_first_call_is_miss(self, cached_gw):
        cached_gw.call("프롬프트", doc_ids=["d1"])
        assert cached_gw.stats.misses == 1
        assert cached_gw.stats.hits == 0

    def test_second_call_same_key_is_hit(self, cached_gw):
        cached_gw.call("프롬프트", doc_ids=["d1"])
        cached_gw.call("프롬프트", doc_ids=["d1"])
        assert cached_gw.stats.hits == 1
        assert cached_gw.gateway.call.call_count == 1

    def test_different_doc_ids_cause_miss(self, cached_gw):
        cached_gw.call("프롬프트", doc_ids=["d1"])
        cached_gw.call("프롬프트", doc_ids=["d2"])
        assert cached_gw.stats.misses == 2

    def test_cache_hit_returns_cache_provider(self, cached_gw):
        cached_gw.call("프롬프트", doc_ids=["d1"])
        resp = cached_gw.call("프롬프트", doc_ids=["d1"])
        assert resp.provider_id == "cache"

    def test_cache_hit_latency_is_zero(self, cached_gw):
        cached_gw.call("프롬프트", doc_ids=["d1"])
        resp = cached_gw.call("프롬프트", doc_ids=["d1"])
        assert resp.latency_ms == 0.0

    def test_total_calls_tracked(self, cached_gw):
        for _ in range(5):
            cached_gw.call("프롬프트", doc_ids=["d1"])
        assert cached_gw.stats.total_calls == 5


class TestCacheKey:

    def test_key_deterministic(self):
        k1 = CachedGateway.make_cache_key("prompt", ["b", "a"])
        k2 = CachedGateway.make_cache_key("prompt", ["a", "b"])
        assert k1 == k2

    def test_key_differs_by_prompt(self):
        k1 = CachedGateway.make_cache_key("prompt1", ["d1"])
        k2 = CachedGateway.make_cache_key("prompt2", ["d1"])
        assert k1 != k2

    def test_key_differs_by_doc_ids(self):
        k1 = CachedGateway.make_cache_key("prompt", ["d1"])
        k2 = CachedGateway.make_cache_key("prompt", ["d2"])
        assert k1 != k2

    def test_key_differs_by_model_id(self):
        k1 = CachedGateway.make_cache_key("prompt", ["d1"], model_id="haiku")
        k2 = CachedGateway.make_cache_key("prompt", ["d1"], model_id="sonnet")
        assert k1 != k2

    def test_key_is_64_char_hex(self):
        k = CachedGateway.make_cache_key("prompt", ["d1"])
        assert len(k) == 64
        assert all(c in "0123456789abcdef" for c in k)


class TestCacheStats:

    def test_hit_rate_zero_when_no_calls(self):
        stats = CacheStats()
        assert stats.hit_rate == 0.0

    def test_hit_rate_calculation(self):
        stats = CacheStats(hits=3, misses=7, total_calls=10)
        assert stats.hit_rate == 0.3

    def test_stats_to_dict(self):
        stats = CacheStats(hits=2, misses=3, total_calls=5, saved_calls=2)
        d = stats.to_dict()
        assert d["hits"] == 2
        assert d["hit_rate"] == 0.4

    def test_call_with_provenance_returns_tuple(self, cached_gw):
        resp, hit = cached_gw.call_with_provenance("프롬프트", doc_ids=["d1"])
        assert not hit
        resp2, hit2 = cached_gw.call_with_provenance("프롬프트", doc_ids=["d1"])
        assert hit2

    def test_cache_disabled_never_hits(self):
        gw = MagicMock()
        gw.call.return_value = LLMResponse(text="텍스트", provider_id="haiku")
        cached = CachedGateway(gateway=gw, enabled=False)
        for _ in range(3):
            cached.call("프롬프트", doc_ids=["d1"])
        assert cached.stats.hits == 0
        assert gw.call.call_count == 3
