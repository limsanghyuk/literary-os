"""
Gate 15 — LiveAdapterGate (SP1 실 어댑터 생존 + 골든셋 자동 회귀)
V455 신설.

검증 항목:
  1. SP1 모듈 임포트 생존 (V451 RealClaudeAdapter, V452 RealOpenAIAdapter,
                             V453 RealOllamaAdapter, V454 LiveCostMeter/SemanticCacheRedis)
  2. LLM-0 원칙 준수 (call_fn/http_fn 주입 인터페이스 존재)
  3. 골든셋 50개 자동 회귀 (mock call_fn/http_fn 주입, 실 API 호출 없음)
"""
from __future__ import annotations

from typing import Any, Dict, List

# ---------------------------------------------------------------------------
# 골든셋 정의 (50개)
# ---------------------------------------------------------------------------

GOLDEN_SET: List[Dict[str, Any]] = [
    # ── RealClaudeAdapter (V451) ── 16개
    {"type": "claude", "label": "basic_response",
     "prompt": "안녕", "mock_content": "안녕하세요", "expect": "안녕하세요"},
    {"type": "claude", "label": "long_prompt",
     "prompt": "파이썬 소개" * 10, "mock_content": "파이썬은 언어입니다", "expect": "파이썬"},
    {"type": "claude", "label": "empty_prompt",
     "prompt": "", "mock_content": "빈 입력", "expect": "빈"},
    {"type": "claude", "label": "json_response",
     "prompt": "JSON 반환", "mock_content": '{"key": "value"}', "expect": "key"},
    {"type": "claude", "label": "token_count",
     "prompt": "토큰 테스트", "mock_content": "ok", "expect_tokens_gt": 0},
    {"type": "claude", "label": "latency_tracked",
     "prompt": "지연시간", "mock_content": "ok", "expect_latency_gt": 0},
    {"type": "claude", "label": "call_id_set",
     "prompt": "call_id 확인", "mock_content": "ok", "expect_call_id": True},
    {"type": "claude", "label": "success_flag",
     "prompt": "성공 플래그", "mock_content": "ok", "expect_success": True},
    {"type": "claude", "label": "provider_name",
     "prompt": "provider", "mock_content": "ok", "expect_provider": "anthropic"},
    {"type": "claude", "label": "cost_positive",
     "prompt": "비용", "mock_content": "ok", "expect_cost_ge": 0.0},
    {"type": "claude", "label": "retries_zero",
     "prompt": "재시도", "mock_content": "ok", "expect_retries": 0},
    {"type": "claude", "label": "stats_after_call",
     "prompt": "통계", "mock_content": "ok", "expect_stats": True},
    {"type": "claude", "label": "health_check_with_fn",
     "prompt": None, "mock_content": None, "expect_health": True},
    {"type": "claude", "label": "model_info_keys",
     "prompt": None, "mock_content": None, "expect_model_info": True},
    {"type": "claude", "label": "rate_limits_keys",
     "prompt": None, "mock_content": None, "expect_rate_limits": True},
    {"type": "claude", "label": "korean_response",
     "prompt": "한국 소설의 특징은?",
     "mock_content": "한국 소설은 감성적 표현이 특징입니다",
     "expect": "한국"},

    # ── RealOpenAIAdapter (V452) ── 12개
    {"type": "openai", "label": "basic_response",
     "prompt": "Hello", "mock_content": "Hi there", "expect": "Hi"},
    {"type": "openai", "label": "provider_name",
     "prompt": "provider", "mock_content": "ok", "expect_provider": "openai"},
    {"type": "openai", "label": "success_flag",
     "prompt": "success", "mock_content": "ok", "expect_success": True},
    {"type": "openai", "label": "function_calling_passthrough",
     "prompt": "call tool", "mock_content": "",
     "mock_tool_calls": [{"id": "t1", "type": "function",
                          "function": {"name": "fn", "arguments": "{}"}}],
     "expect_tool_calls": True},
    {"type": "openai", "label": "stats_tracking",
     "prompt": "stats", "mock_content": "ok", "expect_stats": True},
    {"type": "openai", "label": "cost_calculated",
     "prompt": "cost", "mock_content": "ok", "expect_cost_ge": 0.0},
    {"type": "openai", "label": "health_with_fn",
     "prompt": None, "mock_content": None, "expect_health": True},
    {"type": "openai", "label": "model_info",
     "prompt": None, "mock_content": None, "expect_model_info": True},
    {"type": "openai", "label": "rate_limits",
     "prompt": None, "mock_content": None, "expect_rate_limits": True},
    {"type": "openai", "label": "history_passed",
     "prompt": "follow-up", "mock_content": "got it",
     "history": [{"role": "user", "content": "first msg"}], "expect": "got"},
    {"type": "openai", "label": "latency_tracked",
     "prompt": "latency", "mock_content": "ok", "expect_latency_gt": 0},
    {"type": "openai", "label": "reset_stats",
     "prompt": "reset", "mock_content": "ok", "expect_reset_stats": True},

    # ── RealOllamaAdapter (V453) ── 12개
    {"type": "ollama", "label": "basic_response",
     "prompt": "안녕", "mock_content": "반갑습니다", "expect": "반갑"},
    {"type": "ollama", "label": "provider_name",
     "prompt": "provider", "mock_content": "ok", "expect_provider": "ollama"},
    {"type": "ollama", "label": "success_flag",
     "prompt": "success", "mock_content": "ok", "expect_success": True},
    {"type": "ollama", "label": "zero_cost",
     "prompt": "cost", "mock_content": "ok", "expect_cost": 0.0},
    {"type": "ollama", "label": "health_check",
     "prompt": None, "mock_content": None, "expect_health": True},
    {"type": "ollama", "label": "model_info",
     "prompt": None, "mock_content": None, "expect_model_info": True},
    {"type": "ollama", "label": "list_models",
     "prompt": None, "mock_content": None, "expect_list_models": True},
    {"type": "ollama", "label": "gpu_memory_snapshot",
     "prompt": None, "mock_content": None, "expect_gpu_snapshot": True},
    {"type": "ollama", "label": "latency_from_eval_duration",
     "prompt": "eval_duration", "mock_content": "ok",
     "eval_duration_ns": 500_000_000, "expect_latency_approx": 500.0},
    {"type": "ollama", "label": "stats_tracking",
     "prompt": "stats", "mock_content": "ok", "expect_stats": True},
    {"type": "ollama", "label": "rate_limits",
     "prompt": None, "mock_content": None, "expect_rate_limits": True},
    {"type": "ollama", "label": "is_model_available",
     "prompt": None, "mock_content": None, "expect_model_available": True},

    # ── LiveCostMeter (V454) ── 5개
    {"type": "cost", "label": "record_and_retrieve",
     "tenant": "t1", "cost_usd": 0.01, "expect_usd": 0.01},
    {"type": "cost", "label": "krw_conversion",
     "tenant": "t2", "cost_usd": 1.0, "usd_to_krw": 1350, "expect_krw": 1350.0},
    {"type": "cost", "label": "budget_enforcement",
     "tenant": "t3", "cost_usd": 5.0, "budget": 3.0, "expect_over": True},
    {"type": "cost", "label": "tenant_isolation",
     "tenant": "t4", "cost_usd": 0.5, "other_tenant": "t5", "expect_isolated": True},
    {"type": "cost", "label": "global_stats",
     "tenant": "t6", "cost_usd": 0.1, "expect_global_stats": True},

    # ── SemanticCacheRedis (V454) ── 5개
    {"type": "cache", "label": "set_and_get_exact",
     "prompt": "캐시 테스트 프롬프트", "response": "캐시된 응답"},
    {"type": "cache", "label": "miss_returns_none",
     "prompt": "캐시에 없는 질문 xyz9999", "response": None},
    {"type": "cache", "label": "tenant_isolation",
     "prompt": "격리 테스트", "response": "tenant_a 응답",
     "tenant_a": "cache_ta", "tenant_b": "cache_tb"},
    {"type": "cache", "label": "hit_rate_tracking",
     "prompt": "hit rate", "response": "hit"},
    {"type": "cache", "label": "flush_clears_cache",
     "prompt": "flush 테스트", "response": "삭제될 응답"},
]


# ---------------------------------------------------------------------------
# Gate 실행
# ---------------------------------------------------------------------------

def _gate_live_adapter_sp1() -> dict:
    """Gate 15 — SP1 실 어댑터 생존 + 골든셋 50개 자동 회귀."""
    errors: List[str] = []
    passed = 0
    total = len(GOLDEN_SET)

    # 1. 모듈 임포트 생존
    try:
        from literary_system.adapters_live import (
            GPUMemorySnapshot,
            LiveAdapterCall,
            RealClaudeAdapter,
            RealClaudeAdapterConfig,
            RealLLMResponse,
            RealOllamaAdapter,
            RealOllamaAdapterConfig,
            RealOpenAIAdapter,
            RealOpenAIAdapterConfig,
        )
        from literary_system.cost_cache import (
            InMemoryRedis,
            LiveCostMeter,
            SemanticCacheRedis,
        )
    except Exception as e:
        return {
            "pass": False,
            "reason": f"SP1 모듈 임포트 실패: {e}",
            "golden_passed": 0,
            "golden_total": total,
        }

    # 2. LLM-0 원칙 준수 (call_fn 주입 인터페이스)
    for cls, fn_attr in [
        (RealClaudeAdapter, "_call_fn"),
        (RealOpenAIAdapter, "_call_fn"),
        (RealOllamaAdapter, "_call_fn"),
    ]:
        obj = cls()
        if not hasattr(obj, fn_attr):
            errors.append(f"LLM-0: {cls.__name__} 에 {fn_attr} 없음")

    # 3. 골든셋 자동 회귀
    for case in GOLDEN_SET:
        try:
            ok = _run_golden_case(case)
            if ok:
                passed += 1
            else:
                errors.append(f"GOLDEN FAIL: {case['type']}/{case['label']}")
        except Exception as exc:
            errors.append(f"GOLDEN ERROR: {case['type']}/{case['label']}: {exc}")

    golden_pass_rate = passed / total if total > 0 else 0.0
    gate_pass = len(errors) == 0 and golden_pass_rate >= 1.0

    return {
        "pass": gate_pass,
        "golden_passed": passed,
        "golden_total": total,
        "golden_pass_rate": round(golden_pass_rate, 4),
        "error_count": len(errors),
        "errors": errors[:10],
        "reason": (
            f"Gate15 PASS: 골든셋 {passed}/{total}" if gate_pass
            else f"Gate15 FAIL: {len(errors)}개 오류 ({passed}/{total} 골든셋)"
        ),
        "summary": f"SP1 LiveAdapterGate: {passed}/{total} golden cases passed",
    }


def _run_golden_case(case: Dict[str, Any]) -> bool:
    t = case["type"]
    if t == "claude":
        return _run_claude_case(case)
    elif t == "openai":
        return _run_openai_case(case)
    elif t == "ollama":
        return _run_ollama_case(case)
    elif t == "cost":
        return _run_cost_case(case)
    elif t == "cache":
        return _run_cache_case(case)
    return False


# ---------------------------------------------------------------------------
# Claude
# ---------------------------------------------------------------------------

def _run_claude_case(case: Dict[str, Any]) -> bool:
    from literary_system.adapters_live import RealClaudeAdapter
    from literary_system.llm_bridge.llm_context import LLMContext

    mock_content = case.get("mock_content", "ok")

    def mock_call(messages, model, max_tokens, timeout):
        return {"content": mock_content, "input_tokens": 10, "output_tokens": 5}

    adapter = RealClaudeAdapter(call_fn=mock_call)
    label = case["label"]

    if label == "health_check_with_fn":
        return adapter.health_check() is True
    if label == "model_info_keys":
        info = adapter.get_model_info()
        return all(k in info for k in ("model", "provider", "max_tokens"))
    if label == "rate_limits_keys":
        limits = adapter.get_rate_limits()
        return all(k in limits for k in ("max_retries", "timeout_s"))

    prompt = case.get("prompt") or "test"
    ctx = LLMContext(
        series_id="golden", episode_idx=0, narrative_fitness=0.8,
        max_tokens=128, extra={"user_prompt": prompt},
    )
    resp = adapter.call(ctx)

    if "expect" in case:
        return case["expect"] in resp.text
    if "expect_tokens_gt" in case:
        return resp.tokens_used > case["expect_tokens_gt"]
    if "expect_latency_gt" in case:
        return resp.latency_ms > case["expect_latency_gt"]
    if "expect_call_id" in case:
        return bool(resp.call_id)
    if "expect_success" in case:
        return resp.success == case["expect_success"]
    if "expect_provider" in case:
        return resp.provider == case["expect_provider"]
    if "expect_cost_ge" in case:
        return resp.cost_usd >= case["expect_cost_ge"]
    if "expect_retries" in case:
        return resp.retries == case["expect_retries"]
    if "expect_stats" in case:
        return adapter.stats()["total_calls"] > 0
    return True


# ---------------------------------------------------------------------------
# OpenAI
# ---------------------------------------------------------------------------

def _run_openai_case(case: Dict[str, Any]) -> bool:
    from literary_system.adapters_live import RealOpenAIAdapter
    from literary_system.llm_bridge.llm_context import LLMContext

    mock_content = case.get("mock_content", "ok")
    mock_tool_calls = case.get("mock_tool_calls")

    def mock_call(**kwargs):
        return {
            "content": mock_content,
            "input_tokens": 10,
            "output_tokens": 5,
            "tool_calls": mock_tool_calls,
        }

    adapter = RealOpenAIAdapter(call_fn=mock_call)
    label = case["label"]

    if label == "health_with_fn":
        return adapter.health_check() is True
    if label == "model_info":
        info = adapter.get_model_info()
        return all(k in info for k in ("model", "provider", "max_tokens"))
    if label == "rate_limits":
        limits = adapter.get_rate_limits()
        return all(k in limits for k in ("max_retries", "timeout_s"))
    if label == "reset_stats":
        adapter.reset_stats()
        return adapter.stats()["total_calls"] == 0

    prompt = case.get("prompt") or "test"
    ctx = LLMContext(
        series_id="golden", episode_idx=0, narrative_fitness=0.8,
        max_tokens=128,
        extra={"user_prompt": prompt, "history": case.get("history", [])},
    )
    resp = adapter.call(ctx)

    if "expect" in case:
        return case["expect"] in resp.text
    if "expect_tool_calls" in case:
        tc = resp.__dict__.get("tool_calls")
        return isinstance(tc, list) and len(tc) > 0
    if "expect_provider" in case:
        return resp.provider == case["expect_provider"]
    if "expect_success" in case:
        return resp.success == case["expect_success"]
    if "expect_cost_ge" in case:
        return resp.cost_usd >= case["expect_cost_ge"]
    if "expect_stats" in case:
        return adapter.stats()["total_calls"] > 0
    if "expect_latency_gt" in case:
        return resp.latency_ms > case["expect_latency_gt"]
    return True


# ---------------------------------------------------------------------------
# Ollama — call_fn은 정규화된 형식으로 반환해야 함
# (call_fn 주입 시 _normalize_chat_response 우회됨)
# ---------------------------------------------------------------------------

def _run_ollama_case(case: Dict[str, Any]) -> bool:
    from literary_system.adapters_live import (
        GPUMemorySnapshot,
        RealOllamaAdapter,
    )
    from literary_system.llm_bridge.llm_context import LLMContext

    eval_ns = case.get("eval_duration_ns", 100_000_000)
    mock_content = case.get("mock_content", "ok")

    def mock_call(url, payload, timeout):
        # 정규화된 형식 반환 (_normalize_chat_response 출력과 동일)
        return {
            "content": mock_content,
            "input_tokens": 10,
            "output_tokens": 5,
            "eval_duration_ns": eval_ns,
            "done": True,
        }

    def mock_http(url, timeout):
        if "tags" in url:
            return {"models": [{"name": "llama3.2"}]}
        if "ps" in url:
            return {"models": [{"name": "llama3.2", "size_vram": 4_000_000_000}]}
        return {}

    adapter = RealOllamaAdapter(call_fn=mock_call, http_fn=mock_http)
    label = case["label"]

    if label == "health_check":
        return adapter.health_check() is True
    if label == "model_info":
        info = adapter.get_model_info()
        return all(k in info for k in ("model", "provider"))
    if label == "list_models":
        return isinstance(adapter.list_models(), list)
    if label == "gpu_memory_snapshot":
        snap = adapter.get_gpu_memory()
        return isinstance(snap, GPUMemorySnapshot)
    if label == "rate_limits":
        limits = adapter.get_rate_limits()
        return all(k in limits for k in ("max_retries", "timeout_s"))
    if label == "is_model_available":
        return adapter.is_model_available("llama3.2") is True

    prompt = case.get("prompt") or "test"
    ctx = LLMContext(
        series_id="golden", episode_idx=0, narrative_fitness=0.8,
        max_tokens=128, extra={"user_prompt": prompt},
    )
    resp = adapter.call(ctx)

    if "expect" in case:
        return case["expect"] in resp.text
    if "expect_provider" in case:
        return resp.provider == case["expect_provider"]
    if "expect_success" in case:
        return resp.success == case["expect_success"]
    if "expect_cost" in case:
        return resp.cost_usd == case["expect_cost"]
    if "expect_latency_approx" in case:
        expected = case["expect_latency_approx"]
        return abs(resp.latency_ms - expected) < expected * 0.1
    if "expect_stats" in case:
        return adapter.stats()["total_calls"] > 0
    return True


# ---------------------------------------------------------------------------
# Cost
# ---------------------------------------------------------------------------

def _run_cost_case(case: Dict[str, Any]) -> bool:
    from literary_system.cost_cache import LiveCostMeter

    meter = LiveCostMeter(usd_to_krw=case.get("usd_to_krw", 1350.0))
    tenant = case["tenant"]
    cost = case.get("cost_usd", 0.0)
    label = case["label"]

    if label == "record_and_retrieve":
        meter.record_call(tenant, "mock", 0, 0, cost_usd=cost)
        return abs(meter.get_cost_usd(tenant) - case["expect_usd"]) < 1e-7
    if label == "krw_conversion":
        meter.record_call(tenant, "mock", 0, 0, cost_usd=cost)
        return abs(meter.get_cost_krw(tenant) - case["expect_krw"]) < 0.01
    if label == "budget_enforcement":
        meter.set_monthly_budget(tenant, case["budget"])
        meter.record_call(tenant, "mock", 0, 0, cost_usd=cost)
        return meter.is_over_budget(tenant) == case["expect_over"]
    if label == "tenant_isolation":
        meter.record_call(tenant, "mock", 0, 0, cost_usd=cost)
        return meter.get_cost_usd(case["other_tenant"]) == 0.0
    if label == "global_stats":
        meter.record_call(tenant, "mock", 0, 0, cost_usd=cost)
        return meter.global_stats()["tenant_count"] >= 1
    return False


# ---------------------------------------------------------------------------
# Cache
# ---------------------------------------------------------------------------

def _run_cache_case(case: Dict[str, Any]) -> bool:
    from literary_system.cost_cache import InMemoryRedis, SemanticCacheRedis

    label = case["label"]

    if label == "set_and_get_exact":
        cache = SemanticCacheRedis()
        cache.set(case["prompt"], case["response"])
        return cache.get(case["prompt"]) == case["response"]

    if label == "miss_returns_none":
        cache = SemanticCacheRedis()
        return cache.get(case["prompt"]) is None

    if label == "tenant_isolation":
        redis = InMemoryRedis()
        ca = SemanticCacheRedis(redis_fn=redis, tenant_id=case["tenant_a"])
        cb = SemanticCacheRedis(redis_fn=redis, tenant_id=case["tenant_b"])
        ca.set(case["prompt"], case["response"])
        return cb.get(case["prompt"]) is None

    if label == "hit_rate_tracking":
        cache = SemanticCacheRedis()
        cache.set(case["prompt"], case["response"])
        cache.get(case["prompt"])
        cache.get("miss_xyz999")
        return abs(cache.hit_rate() - 0.5) < 0.01

    if label == "flush_clears_cache":
        cache = SemanticCacheRedis()
        cache.set(case["prompt"], case["response"])
        n = cache.flush_tenant()
        return n == 1 and cache.size() == 0

    return False
