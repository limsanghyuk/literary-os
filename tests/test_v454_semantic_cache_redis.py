"""
V454 — SemanticCacheRedis 테스트
LLM-0 원칙: redis_fn / embed_fn 주입으로 실 Redis/임베딩 서버 없이 테스트.
"""
import math
import pytest
from literary_system.cost_cache.semantic_cache_redis import (
    SemanticCacheRedis,
    InMemoryRedis,
    CacheEntry,
    _tfidf_embed,
    _sparse_cosine,
    _dense_cosine,
    _tokenize,
)


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def make_cache(threshold=0.92, embed_fn=None, tenant_id="t1"):
    redis = InMemoryRedis()
    return SemanticCacheRedis(
        redis_fn=redis,
        embed_fn=embed_fn,
        tenant_id=tenant_id,
        ttl_s=3600,
        similarity_threshold=threshold,
    )


def perfect_embed(text: str):
    """동일 텍스트에 항상 같은 밀집 벡터 반환 (테스트용)."""
    # 단어 기반 고정 해시 벡터 (차원 8)
    tokens = text.lower().split()
    vec = [0.0] * 8
    for i, t in enumerate(tokens[:8]):
        vec[i % 8] += hash(t) % 100 / 100.0
    norm = math.sqrt(sum(x * x for x in vec)) or 1.0
    return [x / norm for x in vec]


def similar_embed(text_a: str, text_b: str, score: float):
    """
    두 텍스트에 대해 코사인 유사도 ≈ score 가 되는 벡터쌍 반환.
    단순화: text_a 기준 벡터를 회전해 score 만큼 유사한 벡터 생성.
    """
    a = [1.0, 0.0]
    # cos(θ) = score → b = [score, sqrt(1-score^2)]
    b = [score, math.sqrt(max(0.0, 1 - score ** 2))]
    return a, b


# ---------------------------------------------------------------------------
# 유틸리티 함수 테스트
# ---------------------------------------------------------------------------

class TestUtils:
    def test_tokenize_english(self):
        tokens = _tokenize("Hello World test")
        assert "hello" in tokens
        assert "world" in tokens

    def test_tokenize_korean(self):
        tokens = _tokenize("한국어 소설 주인공")
        assert "한국어" in tokens
        assert "소설" in tokens

    def test_tokenize_mixed(self):
        tokens = _tokenize("Python 프로그래밍 tutorial")
        assert "python" in tokens
        assert "프로그래밍" in tokens

    def test_tfidf_embed_returns_dict(self):
        emb = _tfidf_embed("hello world hello")
        assert isinstance(emb, dict)
        assert "hello" in emb

    def test_tfidf_embed_frequency(self):
        emb = _tfidf_embed("a a b")
        # a: 2/3, b: 1/3
        assert emb["a"] > emb["b"]

    def test_tfidf_embed_empty(self):
        emb = _tfidf_embed("")
        assert emb == {}

    def test_sparse_cosine_identical(self):
        a = {"x": 0.5, "y": 0.5}
        score = _sparse_cosine(a, a)
        assert abs(score - 1.0) < 1e-6

    def test_sparse_cosine_orthogonal(self):
        a = {"x": 1.0}
        b = {"y": 1.0}
        score = _sparse_cosine(a, b)
        assert abs(score) < 1e-6

    def test_sparse_cosine_empty(self):
        assert _sparse_cosine({}, {"x": 1.0}) == 0.0

    def test_dense_cosine_identical(self):
        a = [1.0, 0.0, 0.0]
        score = _dense_cosine(a, a)
        assert abs(score - 1.0) < 1e-6

    def test_dense_cosine_orthogonal(self):
        a = [1.0, 0.0]
        b = [0.0, 1.0]
        assert abs(_dense_cosine(a, b)) < 1e-6

    def test_dense_cosine_zero_vector(self):
        assert _dense_cosine([0.0, 0.0], [1.0, 0.0]) == 0.0

    def test_dense_cosine_length_mismatch(self):
        assert _dense_cosine([1.0, 2.0], [1.0]) == 0.0


# ---------------------------------------------------------------------------
# CacheEntry
# ---------------------------------------------------------------------------

class TestCacheEntry:
    def test_creation(self):
        entry = CacheEntry(
            prompt="test prompt",
            embedding={"test": 0.5},
            response="answer",
        )
        assert entry.prompt == "test prompt"
        assert entry.response == "answer"
        assert len(entry.entry_id) > 0

    def test_prompt_key_deterministic(self):
        e1 = CacheEntry("same", {}, "r1", model_id="m1")
        e2 = CacheEntry("same", {}, "r2", model_id="m1")
        assert e1.prompt_key == e2.prompt_key

    def test_prompt_key_model_sensitive(self):
        e1 = CacheEntry("same", {}, "r1", model_id="m1")
        e2 = CacheEntry("same", {}, "r2", model_id="m2")
        assert e1.prompt_key != e2.prompt_key

    def test_to_from_dict(self):
        entry = CacheEntry("p", [1.0, 2.0], "resp", model_id="m")
        d = entry.to_dict()
        restored = CacheEntry.from_dict(d)
        assert restored.prompt == entry.prompt
        assert restored.response == entry.response
        assert restored.model_id == entry.model_id
        assert restored.embedding == [1.0, 2.0]

    def test_hit_count_serialized(self):
        entry = CacheEntry("p", {}, "r")
        entry.hit_count = 5
        d = entry.to_dict()
        restored = CacheEntry.from_dict(d)
        assert restored.hit_count == 5


# ---------------------------------------------------------------------------
# InMemoryRedis
# ---------------------------------------------------------------------------

class TestInMemoryRedis:
    def test_set_get(self):
        r = InMemoryRedis()
        r(op="set", key="k1", value="v1", ttl_s=60)
        assert r(op="get", key="k1") == "v1"

    def test_get_missing(self):
        r = InMemoryRedis()
        assert r(op="get", key="no_such_key") is None

    def test_delete(self):
        r = InMemoryRedis()
        r(op="set", key="k1", value="v1", ttl_s=60)
        r(op="delete", key="k1")
        assert r(op="get", key="k1") is None

    def test_keys_prefix_match(self):
        r = InMemoryRedis()
        r(op="set", key="ns:t1:a", value="1", ttl_s=60)
        r(op="set", key="ns:t1:b", value="2", ttl_s=60)
        r(op="set", key="ns:t2:c", value="3", ttl_s=60)
        keys = r(op="keys", pattern="ns:t1:*")
        assert len(keys) == 2
        assert all(k.startswith("ns:t1:") for k in keys)

    def test_mget(self):
        r = InMemoryRedis()
        r(op="set", key="k1", value="v1", ttl_s=60)
        r(op="set", key="k2", value="v2", ttl_s=60)
        results = r(op="mget", keys=["k1", "k2", "k3"])
        assert results[0] == "v1"
        assert results[1] == "v2"
        assert results[2] is None

    def test_no_ttl_persists(self):
        r = InMemoryRedis()
        r(op="set", key="k1", value="forever", ttl_s=None)
        assert r(op="get", key="k1") == "forever"

    def test_unknown_op_raises(self):
        r = InMemoryRedis()
        with pytest.raises(ValueError):
            r(op="unknown_op", key="k")


# ---------------------------------------------------------------------------
# SemanticCacheRedis — 기본 동작
# ---------------------------------------------------------------------------

class TestSemanticCacheRedisBasic:
    def test_set_returns_entry_id(self):
        cache = make_cache()
        entry_id = cache.set("hello world", "response text")
        assert isinstance(entry_id, str)
        assert len(entry_id) > 0

    def test_exact_hit(self):
        cache = make_cache()
        cache.set("What is the capital of France?", "Paris")
        result = cache.get("What is the capital of France?")
        assert result == "Paris"

    def test_miss_returns_none(self):
        cache = make_cache()
        result = cache.get("completely unrelated question xyz123")
        assert result is None

    def test_size_after_set(self):
        cache = make_cache()
        assert cache.size() == 0
        cache.set("p1", "r1")
        assert cache.size() == 1
        cache.set("p2", "r2")
        assert cache.size() == 2

    def test_delete_exact(self):
        cache = make_cache()
        cache.set("to be deleted", "response")
        assert cache.size() == 1
        cache.delete("to be deleted")
        assert cache.size() == 0

    def test_delete_nonexistent(self):
        cache = make_cache()
        result = cache.delete("not in cache")
        assert result is False

    def test_flush_tenant(self):
        cache = make_cache()
        cache.set("p1", "r1")
        cache.set("p2", "r2")
        n = cache.flush_tenant()
        assert n == 2
        assert cache.size() == 0


# ---------------------------------------------------------------------------
# SemanticCacheRedis — Fuzzy 유사도 (embed_fn 주입)
# ---------------------------------------------------------------------------

class TestSemanticCacheRedisFuzzy:
    def test_high_similarity_hit(self):
        """유사도 ≥ 0.92 → 히트."""
        cache = make_cache(threshold=0.92, embed_fn=perfect_embed)
        # 동일 프롬프트 → 코사인 1.0
        cache.set("the quick brown fox", "fox answer")
        result = cache.get("the quick brown fox")
        assert result == "fox answer"

    def test_low_similarity_miss(self):
        """유사도 < 0.92 → 미스 (B2 수정: 직교 벡터로 격리 보장)."""
        # perfect_embed는 해시 충돌로 우연히 고유사도를 줄 수 있음 →
        # 명시적으로 직교 벡터를 반환하는 격리 embed_fn 사용
        call_count = [0]
        def isolated_embed(text: str):
            call_count[0] += 1
            if call_count[0] == 1:
                return [1.0, 0.0, 0.0, 0.0]  # 저장 텍스트 벡터
            else:
                return [0.0, 1.0, 0.0, 0.0]  # 조회 텍스트: 직교 → 코사인=0.0

        cache = make_cache(threshold=0.92, embed_fn=isolated_embed)
        cache.set("Python programming tutorial", "py answer")
        # 직교 벡터 → 코사인 0.0 → 임계값 0.92 미달 → 미스
        result = cache.get("스파게티 요리 레시피")
        assert result is None

    def test_threshold_boundary(self):
        """임계값 정확히 0.92에서 히트/미스 경계 테스트."""
        # embed_fn이 제어된 유사도 반환
        call_count = [0]

        def controlled_embed(text):
            call_count[0] += 1
            if call_count[0] == 1:  # set 호출 (저장 시)
                return [1.0, 0.0]
            else:
                # 0.92 → 히트
                return [0.92, math.sqrt(1 - 0.92**2)]

        cache = make_cache(threshold=0.92, embed_fn=controlled_embed)
        cache.set("original prompt", "response")
        # get 시 유사도 ≈ 0.92
        result = cache.get("query prompt")
        assert result == "response"

    def test_below_threshold_miss(self):
        """임계값 0.92 미만 → 미스."""
        call_count = [0]

        def controlled_embed(text):
            call_count[0] += 1
            if call_count[0] == 1:
                return [1.0, 0.0]
            else:
                # 0.80 → 미스
                return [0.80, math.sqrt(1 - 0.80**2)]

        cache = make_cache(threshold=0.92, embed_fn=controlled_embed)
        cache.set("original", "response")
        result = cache.get("different")
        assert result is None

    def test_multiple_entries_best_match(self):
        """여러 항목 중 가장 높은 유사도 선택."""
        embed_map = {
            "cat": [1.0, 0.0, 0.0],
            "dog": [0.0, 1.0, 0.0],
            "feline": [0.95, 0.1, 0.0],  # cat과 매우 유사
        }

        def lookup_embed(text):
            key = text.lower().strip()
            if key in embed_map:
                v = embed_map[key]
            else:
                v = [0.33, 0.33, 0.34]
            norm = math.sqrt(sum(x*x for x in v)) or 1.0
            return [x/norm for x in v]

        cache = make_cache(threshold=0.90, embed_fn=lookup_embed)
        cache.set("cat", "cats are felines")
        cache.set("dog", "dogs are canines")
        # "feline"은 "cat"과 유사도 높아야 함
        result = cache.get("feline")
        assert result == "cats are felines"

    def test_hit_count_increments(self):
        """캐시 히트 시 hit_count 증가."""
        call_count = [0]

        def embed(text):
            call_count[0] += 1
            return [1.0, 0.0]  # 항상 동일 벡터

        cache = make_cache(threshold=0.90, embed_fn=embed)
        cache.set("prompt", "response")
        cache.get("prompt")
        cache.get("prompt")
        # 내부 hit_count가 업데이트됐는지 stats로 간접 확인
        assert cache._hits == 2


# ---------------------------------------------------------------------------
# SemanticCacheRedis — per-tenant 격리
# ---------------------------------------------------------------------------

class TestSemanticCacheRedisTenantIsolation:
    def test_different_tenants_isolated(self):
        redis = InMemoryRedis()
        cache_a = SemanticCacheRedis(redis_fn=redis, tenant_id="tenant_a")
        cache_b = SemanticCacheRedis(redis_fn=redis, tenant_id="tenant_b")

        cache_a.set("shared prompt", "answer from A")
        # tenant_b는 tenant_a의 캐시 접근 불가
        result = cache_b.get("shared prompt")
        assert result is None

    def test_same_tenant_shares_data(self):
        redis = InMemoryRedis()
        cache1 = SemanticCacheRedis(redis_fn=redis, tenant_id="same_tenant")
        cache2 = SemanticCacheRedis(redis_fn=redis, tenant_id="same_tenant")

        cache1.set("question", "answer")
        result = cache2.get("question")
        assert result == "answer"

    def test_flush_only_own_tenant(self):
        redis = InMemoryRedis()
        cache_a = SemanticCacheRedis(redis_fn=redis, tenant_id="ta")
        cache_b = SemanticCacheRedis(redis_fn=redis, tenant_id="tb")

        cache_a.set("a_prompt", "a_resp")
        cache_b.set("b_prompt", "b_resp")

        cache_a.flush_tenant()
        assert cache_a.size() == 0
        assert cache_b.size() == 1  # tb 데이터 유지

    def test_key_namespace_format(self):
        redis = InMemoryRedis()
        cache = SemanticCacheRedis(redis_fn=redis, tenant_id="my_tenant")
        cache.set("test", "resp")
        keys = redis(op="keys", pattern="sem_cache:my_tenant:*")
        assert len(keys) == 1
        assert keys[0].startswith("sem_cache:my_tenant:")


# ---------------------------------------------------------------------------
# SemanticCacheRedis — 통계
# ---------------------------------------------------------------------------

class TestSemanticCacheRedisStats:
    def test_stats_initial(self):
        cache = make_cache()
        s = cache.stats()
        assert s["hits"] == 0
        assert s["misses"] == 0
        assert s["sets"] == 0
        assert s["hit_rate"] == 0.0

    def test_hit_rate_100_percent(self):
        cache = make_cache()
        cache.set("q", "a")
        cache.get("q")
        assert abs(cache.hit_rate() - 1.0) < 0.01

    def test_hit_rate_0_percent(self):
        cache = make_cache()
        cache.get("miss1")
        cache.get("miss2")
        assert cache.hit_rate() == 0.0

    def test_hit_rate_50_percent(self):
        cache = make_cache()
        cache.set("q", "a")
        cache.get("q")    # hit
        cache.get("xxx")  # miss
        rate = cache.hit_rate()
        assert abs(rate - 0.5) < 0.01

    def test_reset_stats(self):
        cache = make_cache()
        cache.set("q", "a")
        cache.get("q")
        cache.reset_stats()
        assert cache._hits == 0
        assert cache._misses == 0
        assert cache._sets == 0

    def test_stats_keys(self):
        cache = make_cache()
        s = cache.stats()
        required_keys = {"tenant_id", "hits", "misses", "sets", "errors",
                         "hit_rate", "size", "similarity_threshold", "ttl_s"}
        assert required_keys.issubset(s.keys())


# ---------------------------------------------------------------------------
# SemanticCacheRedis — redis_fn 외부 주입
# ---------------------------------------------------------------------------

class TestSemanticCacheRedisInjection:
    def test_external_redis_fn_injected(self):
        """외부 redis_fn 주입 동작 확인."""
        store = {}

        def my_redis(op, **kwargs):
            if op == "get":
                return store.get(kwargs["key"])
            elif op == "set":
                store[kwargs["key"]] = kwargs["value"]
            elif op == "delete":
                store.pop(kwargs["key"], None)
            elif op == "keys":
                prefix = kwargs["pattern"].rstrip("*")
                return [k for k in store if k.startswith(prefix)]
            elif op == "mget":
                return [store.get(k) for k in kwargs["keys"]]

        cache = SemanticCacheRedis(redis_fn=my_redis, tenant_id="ext")
        cache.set("hello", "world")
        result = cache.get("hello")
        assert result == "world"
        assert len(store) == 1

    def test_no_redis_fn_uses_inmemory(self):
        """redis_fn 미지정 시 InMemoryRedis 사용."""
        cache = SemanticCacheRedis()  # redis_fn=None
        cache.set("k", "v")
        assert cache.get("k") == "v"

    def test_embed_fn_injected(self):
        """embed_fn 주입 동작."""
        embed_called = []

        def my_embed(text):
            embed_called.append(text)
            return [1.0, 0.0]

        cache = make_cache(embed_fn=my_embed)
        cache.set("test", "response")
        assert len(embed_called) == 1
        cache.get("test")
        assert len(embed_called) == 2


# ---------------------------------------------------------------------------
# SemanticCacheRedis — 모델 ID 필터
# ---------------------------------------------------------------------------

class TestSemanticCacheRedisModelFilter:
    def test_model_id_stored(self):
        cache = make_cache()
        cache.set("p", "r", model_id="gpt-4o")
        result = cache.get("p", model_id="gpt-4o")
        assert result == "r"

    def test_different_model_id_filtered(self):
        """다른 model_id는 캐시 비교에서 제외."""
        cache = make_cache()
        cache.set("p", "gpt answer", model_id="gpt-4o")
        # claude model_id로 조회 → 필터링되어 미스
        result = cache.get("p", model_id="claude-haiku")
        assert result is None

    def test_no_model_id_matches_any(self):
        """model_id 미지정 → model_id 없는 항목도 매칭."""
        cache = make_cache()
        cache.set("p", "r")  # model_id=""
        result = cache.get("p")  # model_id=""
        assert result == "r"
