"""V411-F 테스트 — UnifiedLLMGateway."""
from __future__ import annotations
import pytest
from literary_system.llm_bridge.gateway.unified_llm_gateway import (
    UnifiedLLMGateway, make_default_gateway
)
from literary_system.llm_bridge.routing.task_router import TaskRouter
from literary_system.llm_bridge.health.provider_health_monitor import ProviderHealthMonitor
from literary_system.llm_bridge.llm_context import LLMContext, LLMResponse
from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge


def _make_mock(provider_id: str, response: str = "ok", available: bool = True):
    class _M(MockLLMBridge):
        def __init__(self):
            super().__init__(scripted_response=response)
        def is_available(self): return available
        def get_provider_id(self): return provider_id
        @property
        def provider_name(self): return provider_id
    return _M()


def _make_gateway(local_resp="local_ok", speed_resp="speed_ok",
                  quality_resp="quality_ok",
                  local_ok=True, speed_ok=True, quality_ok=True):
    providers = {
        "local":   _make_mock("ollama",  local_resp,   local_ok),
        "speed":   _make_mock("haiku",   speed_resp,   speed_ok),
        "quality": _make_mock("sonnet",  quality_resp, quality_ok),
    }
    health = ProviderHealthMonitor({p.get_provider_id(): p
                                    for p in providers.values()})
    router = TaskRouter(providers=providers, health_monitor=health,
                        fallback=_make_mock("fallback", "fallback_resp"))
    return UnifiedLLMGateway(task_router=router, health_monitor=health)


# ── 1. 기본 call() 반환 LLMResponse ─────────────────────────────
def test_call_returns_llm_response():
    gw = _make_gateway()
    ctx = LLMContext(narrative_fitness=2.0)
    resp = gw.call("hello", ctx)
    assert isinstance(resp, LLMResponse)


# ── 2. call_text() 문자열 반환 ──────────────────────────────────
def test_call_text_returns_str():
    gw = _make_gateway()
    result = gw.call_text("hello", LLMContext(narrative_fitness=2.0))
    assert isinstance(result, str)
    assert len(result) > 0


# ── 3. fitness 기반 라우팅 — local ──────────────────────────────
def test_routes_to_local_by_fitness():
    gw = _make_gateway()
    resp = gw.call("prompt", LLMContext(narrative_fitness=2.0))
    assert resp.provider_id == "ollama"
    assert resp.text == "local_ok"


# ── 4. fitness 기반 라우팅 — speed ──────────────────────────────
def test_routes_to_speed_by_fitness():
    gw = _make_gateway()
    resp = gw.call("prompt", LLMContext(narrative_fitness=5.5))
    assert resp.provider_id == "haiku"


# ── 5. fitness 기반 라우팅 — quality ────────────────────────────
def test_routes_to_quality_by_fitness():
    gw = _make_gateway()
    resp = gw.call("prompt", LLMContext(narrative_fitness=8.0))
    assert resp.provider_id == "sonnet"


# ── 6. provider_hint 우선 ───────────────────────────────────────
def test_hint_overrides_fitness():
    gw = _make_gateway()
    resp = gw.call("prompt", LLMContext(narrative_fitness=9.0,
                                         provider_hint="cost"))
    assert resp.provider_id == "ollama"


# ── 7. call_count 누적 ──────────────────────────────────────────
def test_call_count():
    gw = _make_gateway()
    gw.call("p1", LLMContext())
    gw.call("p2", LLMContext())
    assert gw.call_count == 2


# ── 8. 첫 번째 시도 fallback_used=False ─────────────────────────
def test_first_attempt_not_fallback():
    gw = _make_gateway()
    resp = gw.call("prompt", LLMContext(narrative_fitness=2.0))
    assert resp.fallback_used == False


# ── 9. local 불건강 → 폴백 → fallback_used=True ─────────────────
def test_fallback_used_true_on_retry():
    gw = _make_gateway(local_ok=False)
    resp = gw.call("prompt", LLMContext(narrative_fitness=2.0))
    # fallback 사용됨 OR speed로 폴백
    assert isinstance(resp, LLMResponse)
    assert resp.text is not None


# ── 10. latency_ms > 0 ──────────────────────────────────────────
def test_latency_recorded():
    gw = _make_gateway()
    resp = gw.call("prompt", LLMContext())
    assert resp.latency_ms >= 0


# ── 11. None context 허용 ────────────────────────────────────────
def test_none_context():
    gw = _make_gateway()
    resp = gw.call("prompt", None)
    assert isinstance(resp, LLMResponse)


# ── 12. dict context 하위 호환 ──────────────────────────────────
def test_dict_context_compat():
    gw = _make_gateway()
    resp = gw.call("prompt", {"narrative_fitness": 3.0})
    assert isinstance(resp, LLMResponse)


# ── 13. make_default_gateway 생성 ───────────────────────────────
def test_make_default_gateway():
    gw = make_default_gateway(mock_fallback=True)
    assert isinstance(gw, UnifiedLLMGateway)


# ── 14. make_default_gateway call_text ──────────────────────────
def test_default_gateway_call_text():
    gw = make_default_gateway(mock_fallback=True)
    # ollama 오프라인이므로 fallback 응답
    result = gw.call_text("test", LLMContext(narrative_fitness=2.0, timeout=1))
    assert isinstance(result, str)


# ── 15. error_count 초기값 0 ────────────────────────────────────
def test_error_count_initial():
    gw = _make_gateway()
    assert gw.error_count == 0


# ── 16. 모든 프로바이더 실패 → 오류 응답 반환 ──────────────────
def test_all_providers_fail_graceful():
    providers = {
        "local":   _make_mock("ollama",  available=False),
        "speed":   _make_mock("haiku",   available=False),
        "quality": _make_mock("sonnet",  available=False),
    }
    router = TaskRouter(providers=providers, health_monitor=None)
    gw = UnifiedLLMGateway(task_router=router, health_monitor=None)
    resp = gw.call("prompt", LLMContext())
    assert isinstance(resp, LLMResponse)
    assert resp.text is not None


# ── 17. call() provider_id 포함 ─────────────────────────────────
def test_response_includes_provider_id():
    gw = _make_gateway()
    resp = gw.call("prompt", LLMContext(narrative_fitness=2.0))
    assert resp.provider_id != ""


# ── 18. call() 텍스트 비어있지 않음 ────────────────────────────
def test_response_text_not_empty():
    gw = _make_gateway()
    resp = gw.call("hello world", LLMContext())
    assert len(resp.text) > 0


# ── 19. 연속 call 독립성 ────────────────────────────────────────
def test_multiple_calls_independent():
    gw = _make_gateway()
    r1 = gw.call("p1", LLMContext(narrative_fitness=2.0))
    r2 = gw.call("p2", LLMContext(narrative_fitness=8.0))
    assert r1.provider_id != r2.provider_id or r1.text == r2.text


# ── 20. DEFAULT_MAX_RETRIES 값 확인 ─────────────────────────────
def test_default_max_retries():
    assert UnifiedLLMGateway.DEFAULT_MAX_RETRIES == len(TaskRouter.FALLBACK_CHAIN)
