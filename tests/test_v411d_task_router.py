"""V411-D 테스트 — TaskRouter (LLM-0 준수 순수 수치 라우터)."""
from __future__ import annotations
import inspect
import pytest
from literary_system.llm_bridge.routing.task_router import TaskRouter
from literary_system.llm_bridge.llm_context import LLMContext
from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
from literary_system.llm_bridge.health.provider_health_monitor import ProviderHealthMonitor


def _make_mock(provider_id: str, available: bool = True):
    class _M(MockLLMBridge):
        def is_available(self): return available
        def get_provider_id(self): return provider_id
        @property
        def provider_name(self): return provider_id
    return _M()


def _make_router(local_ok=True, speed_ok=True, quality_ok=True):
    providers = {
        "local":   _make_mock("ollama",  local_ok),
        "speed":   _make_mock("haiku",   speed_ok),
        "quality": _make_mock("sonnet",  quality_ok),
    }
    mon = ProviderHealthMonitor({p.get_provider_id(): p for p in providers.values()})
    return TaskRouter(providers=providers, health_monitor=mon), providers


# ── 1. 기본 생성 ─────────────────────────────────────────────────
def test_create_empty():
    router = TaskRouter()
    assert router.available_tiers() == []


# ── 2. fitness=0.2 → local 티어 ─────────────────────────────────
def test_route_low_fitness_local():
    router, providers = _make_router()
    ctx = LLMContext(narrative_fitness=2.0)   # normalized=0.2
    result = router.route(ctx)
    assert result.get_provider_id() == "ollama"


# ── 3. fitness=0.55 → speed 티어 ────────────────────────────────
def test_route_mid_fitness_speed():
    router, providers = _make_router()
    ctx = LLMContext(narrative_fitness=5.5)   # normalized=0.55
    result = router.route(ctx)
    assert result.get_provider_id() == "haiku"


# ── 4. fitness=0.8 → quality 티어 ───────────────────────────────
def test_route_high_fitness_quality():
    router, providers = _make_router()
    ctx = LLMContext(narrative_fitness=8.0)   # normalized=0.8
    result = router.route(ctx)
    assert result.get_provider_id() == "sonnet"


# ── 5. provider_hint="cost" → local 우선 ────────────────────────
def test_hint_cost_overrides_fitness():
    router, providers = _make_router()
    ctx = LLMContext(narrative_fitness=9.0, provider_hint="cost")
    result = router.route(ctx)
    assert result.get_provider_id() == "ollama"


# ── 6. provider_hint="speed" → haiku ────────────────────────────
def test_hint_speed():
    router, providers = _make_router()
    ctx = LLMContext(provider_hint="speed")
    result = router.route(ctx)
    assert result.get_provider_id() == "haiku"


# ── 7. provider_hint="quality" → sonnet ─────────────────────────
def test_hint_quality():
    router, providers = _make_router()
    ctx = LLMContext(provider_hint="quality")
    result = router.route(ctx)
    assert result.get_provider_id() == "sonnet"


# ── 8. local 불건강 → speed 폴백 ────────────────────────────────
def test_fallback_local_down():
    router, providers = _make_router(local_ok=False)
    ctx = LLMContext(narrative_fitness=2.0)
    result = router.route(ctx)
    # local 불건강 → speed 또는 quality 폴백
    assert result.get_provider_id() in ("haiku", "sonnet")


# ── 9. local+speed 불건강 → quality 폴백 ────────────────────────
def test_fallback_chain_two_down():
    router, providers = _make_router(local_ok=False, speed_ok=False)
    ctx = LLMContext(narrative_fitness=2.0)
    result = router.route(ctx)
    assert result.get_provider_id() == "sonnet"


# ── 10. 모든 티어 불건강 → fallback 어댑터 ──────────────────────
def test_fallback_all_down():
    router, providers = _make_router(local_ok=False, speed_ok=False, quality_ok=False)
    fb = _make_mock("fallback_mock")
    router.set_fallback(fb)
    ctx = LLMContext(narrative_fitness=5.0)
    result = router.route(ctx)
    assert result.get_provider_id() == "fallback_mock"


# ── 11. LLM-0: route() 내 generate 호출 없음 ───────────────────
def test_llm0_no_generate_calls():
    """route()는 LLM generate()를 절대 호출하지 않는다."""
    router, providers = _make_router()
    ctx = LLMContext(narrative_fitness=5.0)
    # 모든 어댑터의 call_count가 0이어야 함
    router.route(ctx)
    for adapter in providers.values():
        assert adapter.call_count == 0


# ── 12. tier_for_fitness 경계값 ─────────────────────────────────
def test_tier_for_fitness_boundaries():
    router = TaskRouter()
    assert router.tier_for_fitness(0.0)  == "local"
    assert router.tier_for_fitness(0.39) == "local"
    assert router.tier_for_fitness(0.40) == "speed"
    assert router.tier_for_fitness(0.74) == "speed"
    assert router.tier_for_fitness(0.75) == "quality"
    assert router.tier_for_fitness(1.0)  == "quality"


# ── 13. register 동적 등록 ───────────────────────────────────────
def test_dynamic_register():
    router = TaskRouter()
    adapter = _make_mock("dynamic")
    router.register("local", adapter)
    assert "local" in router.available_tiers()


# ── 14. health_monitor=None → 항상 건강으로 간주 ────────────────
def test_no_health_monitor_always_healthy():
    providers = {"local": _make_mock("ollama")}
    router = TaskRouter(providers=providers, health_monitor=None)
    ctx = LLMContext(narrative_fitness=2.0)
    result = router.route(ctx)
    assert result.get_provider_id() == "ollama"


# ── 15. hint 대소문자 무관 ──────────────────────────────────────
def test_hint_case_insensitive():
    router, _ = _make_router()
    ctx = LLMContext(provider_hint="QUALITY")
    result = router.route(ctx)
    assert result.get_provider_id() == "sonnet"


# ── 16. fitness=0.0 → local ─────────────────────────────────────
def test_zero_fitness():
    router, _ = _make_router()
    ctx = LLMContext(narrative_fitness=0.0)
    result = router.route(ctx)
    assert result.get_provider_id() == "ollama"


# ── 17. fitness=10.0 (최대) → quality ───────────────────────────
def test_max_fitness():
    router, _ = _make_router()
    ctx = LLMContext(narrative_fitness=10.0)
    result = router.route(ctx)
    assert result.get_provider_id() == "sonnet"


# ── 18. THRESHOLDS 구조 확인 ────────────────────────────────────
def test_thresholds_structure():
    for tier, (lo, hi) in TaskRouter.THRESHOLDS.items():
        assert lo < hi
        assert 0.0 <= lo <= 1.0
        assert 0.0 <  hi <= 1.1


# ── 19. FALLBACK_CHAIN 순서 확인 ────────────────────────────────
def test_fallback_chain_order():
    chain = TaskRouter.FALLBACK_CHAIN
    assert chain[0] == "local"
    assert chain[-1] == "quality"


# ── 20. route() 시그니처에 LLM generate 관련 코드 없음 ──────────
def test_route_source_no_generate():
    """route() 소스에 generate() 직접 호출이 없음을 검증."""
    import inspect
    src = inspect.getsource(TaskRouter.route)
    assert ".generate(" not in src
    assert "llm.generate" not in src
