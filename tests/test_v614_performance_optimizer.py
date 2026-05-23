"""
test_v614_performance_optimizer.py — V614 PerformanceOptimizer 테스트 (20 TC)
ADR-074: INT8 양자화 + KV 캐시 + SLO 검증
"""
import pytest
import time
import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from literary_system.optimization.performance_optimizer import (
    PerformanceOptimizer, QuantizationConfig, KVCacheConfig,
    QuantizationManager, KVCache, LatencyProfiler, LatencyRecord,
    GPUMemoryMonitor, SLOReport,
    QuantizationType, OptimizationStatus,
    SLO_P95_MS, SLO_GPU_MB, SLO_CACHE_HIT, VERSION,
)


# ─────────────────────────────────────────────────────────────────────────────
# TC-1: 버전 및 상수
# ─────────────────────────────────────────────────────────────────────────────

class TestConstants:
    def test_version(self):
        assert VERSION == "1.0.0"

    def test_slo_values(self):
        assert SLO_P95_MS == 1500.0
        assert SLO_GPU_MB == 8192.0
        assert SLO_CACHE_HIT == 0.60

    def test_quant_type_enum(self):
        assert QuantizationType.INT8.value == "int8"
        assert QuantizationType.INT4.value == "int4"
        assert QuantizationType.FP16.value == "fp16"


# ─────────────────────────────────────────────────────────────────────────────
# TC-2: KVCache
# ─────────────────────────────────────────────────────────────────────────────

class TestKVCache:
    def test_put_and_get(self):
        cache = KVCache()
        cache.put("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_miss_returns_none(self):
        cache = KVCache()
        assert cache.get("nonexistent") is None

    def test_lru_eviction(self):
        cfg = KVCacheConfig(max_entries=2)
        cache = KVCache(cfg)
        cache.put("a", 1)
        cache.put("b", 2)
        cache.put("c", 3)  # "a" 퇴거
        assert cache.get("a") is None
        assert cache.get("b") == 2
        assert cache.get("c") == 3

    def test_hit_rate(self):
        cache = KVCache()
        cache.put("k", "v")
        cache.get("k")   # hit
        cache.get("x")   # miss
        assert cache.hit_rate() == pytest.approx(0.5)

    def test_make_key_deterministic(self):
        k1 = KVCache.make_key("hello", "model-a")
        k2 = KVCache.make_key("hello", "model-a")
        assert k1 == k2

    def test_make_key_different_inputs(self):
        k1 = KVCache.make_key("hello", "model-a")
        k2 = KVCache.make_key("world", "model-a")
        assert k1 != k2

    def test_clear(self):
        cache = KVCache()
        cache.put("a", 1)
        cache.put("b", 2)
        n = cache.clear()
        assert n == 2
        assert cache.get("a") is None

    def test_stats_keys(self):
        cache = KVCache()
        s = cache.stats()
        assert "size" in s
        assert "hit_rate" in s
        assert "max_entries" in s


# ─────────────────────────────────────────────────────────────────────────────
# TC-3: QuantizationManager
# ─────────────────────────────────────────────────────────────────────────────

class TestQuantizationManager:
    def test_apply_stub(self):
        qm = QuantizationManager()
        result = qm.apply("test-model-614")
        assert result["applied"] is True
        assert result["model_id"] == "test-model-614"

    def test_memory_reduction_int8(self):
        cfg = QuantizationConfig(quant_type=QuantizationType.INT8)
        qm = QuantizationManager(cfg)
        result = qm.apply("model-int8")
        assert result["estimated_memory_reduction_pct"] == pytest.approx(50.0)

    def test_memory_reduction_int4(self):
        cfg = QuantizationConfig(quant_type=QuantizationType.INT4, load_in_4bit=True)
        qm = QuantizationManager(cfg)
        result = qm.apply("model-int4")
        assert result["estimated_memory_reduction_pct"] == pytest.approx(75.0)

    def test_is_applied(self):
        qm = QuantizationManager()
        qm.apply("mid-614")
        assert qm.is_applied("mid-614") is True
        assert qm.is_applied("not-applied") is False


# ─────────────────────────────────────────────────────────────────────────────
# TC-4: LatencyProfiler
# ─────────────────────────────────────────────────────────────────────────────

class TestLatencyProfiler:
    def test_percentile_empty(self):
        prof = LatencyProfiler()
        assert prof.percentile(95) == 0.0

    def test_percentile_values(self):
        prof = LatencyProfiler()
        for i in range(1, 101):
            prof.record(LatencyRecord("r", float(i), "m"))
        p50 = prof.percentile(50)
        p95 = prof.percentile(95)
        assert p50 <= p95

    def test_summary_keys(self):
        prof = LatencyProfiler()
        prof.record(LatencyRecord("r1", 100.0, "m1"))
        s = prof.summary()
        for k in ["count", "p50_ms", "p95_ms", "p99_ms"]:
            assert k in s


# ─────────────────────────────────────────────────────────────────────────────
# TC-5: PerformanceOptimizer 통합
# ─────────────────────────────────────────────────────────────────────────────

class TestPerformanceOptimizer:
    def test_version(self):
        opt = PerformanceOptimizer()
        assert opt.VERSION == "1.0.0"

    def test_apply_quantization(self):
        opt = PerformanceOptimizer()
        result = opt.apply_quantization("test-v614")
        assert result["applied"] is True

    def test_cache_put_get(self):
        opt = PerformanceOptimizer()
        opt.cache_put("hello world", "model-v614", {"tokens": [1, 2, 3]})
        val = opt.cache_get("hello world", "model-v614")
        assert val == {"tokens": [1, 2, 3]}

    def test_infer_miss_then_hit(self):
        opt = PerformanceOptimizer()
        call_count = [0]
        def fake_fn(p):
            call_count[0] += 1
            return f"result:{p}"

        r1 = opt.infer("prompt-A", "model-v614", fake_fn)
        assert r1["cached"] is False
        assert call_count[0] == 1

        r2 = opt.infer("prompt-A", "model-v614", fake_fn)
        assert r2["cached"] is True
        assert call_count[0] == 1   # inference_fn 재호출 없음

    def test_slo_report_structure(self):
        opt = PerformanceOptimizer()
        report = opt.slo_report()
        assert hasattr(report, "p95_ms")
        assert hasattr(report, "slo_p95_pass")
        assert hasattr(report, "all_pass")

    def test_slo_empty_pass(self):
        """측정값 없을 때 SLO는 통과로 간주"""
        opt = PerformanceOptimizer()
        report = opt.slo_report()
        assert report.slo_p95_pass is True
        assert report.slo_gpu_pass is True

    def test_stats_top_level_keys(self):
        opt = PerformanceOptimizer()
        s = opt.stats()
        for k in ["version", "status", "quantization", "kv_cache", "latency", "gpu", "slo"]:
            assert k in s
