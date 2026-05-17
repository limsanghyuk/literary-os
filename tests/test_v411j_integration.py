"""
V411-J 통합 테스트 — LLM 멀티 프로바이더 레이어 전체 통합.

검증:
  - 전체 레이어 스택 (LLMContext → TaskRouter → UnifiedLLMGateway → 어댑터)
  - NKGCurator + NarrativeConductor 연동
  - CostLedger + EpisodeMemory 연동
  - Gate 10 Release Gate 등록
  - LLM-0 원칙 시스템 전체 준수
  - make_default_gateway() E2E 흐름
"""
from __future__ import annotations
import pytest
from literary_system.llm_bridge.llm_context import LLMContext, LLMResponse, coerce_context
from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge
from literary_system.llm_bridge.openai_compatible_adapter import OpenAICompatibleAdapter
from literary_system.llm_bridge.ollama_adapter import OllamaAdapter, make_ollama_adapter
from literary_system.llm_bridge.routing.task_router import TaskRouter
from literary_system.llm_bridge.health.provider_health_monitor import ProviderHealthMonitor
from literary_system.llm_bridge.gateway.unified_llm_gateway import UnifiedLLMGateway, make_default_gateway
from literary_system.llm_bridge.cost_ledger import CostLedger
from literary_system.nkg.curators.nkg_curator import NKGCurator
from literary_system.gates.gate10_llm_contract import LLMAdapterContractGate
from literary_system.gates.release_gate import GATES, run_release_gate


# ────────────────────────────────────────────────────────────────
# 헬퍼
# ────────────────────────────────────────────────────────────────

def _make_full_stack(fitness: float = 5.0, hint: str = ""):
    """3티어 MockBridge 기반 전체 스택 구성."""
    def mock(pid, resp):
        class M(MockLLMBridge):
            def is_available(self): return True
            def get_provider_id(self): return pid
            @property
            def provider_name(self): return pid
            def __init__(self): super().__init__(scripted_response=resp)
        return M()

    providers = {
        "local":   mock("ollama",  f"[ollama:{fitness}]"),
        "speed":   mock("haiku",   f"[haiku:{fitness}]"),
        "quality": mock("sonnet",  f"[sonnet:{fitness}]"),
    }
    health = ProviderHealthMonitor({p.get_provider_id(): p for p in providers.values()})
    router = TaskRouter(providers=providers, health_monitor=health)
    gw = UnifiedLLMGateway(task_router=router, health_monitor=health)
    ctx = LLMContext(narrative_fitness=fitness, provider_hint=hint)
    return gw, ctx


# ────────────────────────────────────────────────────────────────
# 통합 테스트
# ────────────────────────────────────────────────────────────────

# ── 1. 전체 스택 E2E — fitness 기반 라우팅 ──────────────────────
def test_e2e_fitness_routing_local():
    gw, ctx = _make_full_stack(fitness=2.0)
    resp = gw.call("prompt", ctx)
    assert resp.provider_id == "ollama"
    assert "ollama" in resp.text

def test_e2e_fitness_routing_speed():
    gw, ctx = _make_full_stack(fitness=5.5)
    resp = gw.call("prompt", ctx)
    assert resp.provider_id == "haiku"

def test_e2e_fitness_routing_quality():
    gw, ctx = _make_full_stack(fitness=8.0)
    resp = gw.call("prompt", ctx)
    assert resp.provider_id == "sonnet"


# ── 4. provider_hint E2E ────────────────────────────────────────
def test_e2e_hint_cost():
    gw, _ = _make_full_stack(fitness=9.0)
    ctx = LLMContext(narrative_fitness=9.0, provider_hint="cost")
    resp = gw.call("prompt", ctx)
    assert resp.provider_id == "ollama"


# ── 5. CostLedger + LLMResponse 연동 ────────────────────────────
def test_cost_ledger_integration():
    gw, ctx = _make_full_stack(fitness=2.0)
    resp = gw.call("prompt", ctx)
    ledger = CostLedger(episode_idx=1, series_id="test_series")
    ledger.record_call(resp)
    assert ledger.total_calls == 1
    assert resp.provider_id in ledger.provider_ids


# ── 6. CostLedger to_dict 완전성 ────────────────────────────────
def test_cost_ledger_to_dict_complete():
    ledger = CostLedger(episode_idx=2, series_id="s1")
    ledger.record_raw("ollama", tokens=300, latency_ms=500.0)
    d = ledger.to_dict()
    assert all(k in d for k in ["episode_idx", "series_id", "total_calls",
                                  "total_tokens", "records"])


# ── 7. EpisodeMemory cost_ledger 필드 직렬화 ────────────────────
def test_episode_memory_cost_ledger_serialization():
    from literary_system.memory.narrative_memory_store import EpisodeMemory
    import time
    mem = EpisodeMemory(
        series_id="s1", episode_idx=1,
        created_at=str(time.time()),
        pipeline_state={}, narrative_tensor={},
        nkg_snapshot_path="", debt_ledger_snapshot={},
        coefficient_snapshot={},
        cost_ledger={"test_key": "test_val"},
    )
    d = mem.to_dict()
    assert d["cost_ledger"] == {"test_key": "test_val"}


# ── 8. EpisodeMemory cost_ledger None 기본값 ────────────────────
def test_episode_memory_cost_ledger_none():
    from literary_system.memory.narrative_memory_store import EpisodeMemory
    import time
    mem = EpisodeMemory(
        series_id="s1", episode_idx=1,
        created_at=str(time.time()),
        pipeline_state={}, narrative_tensor={},
        nkg_snapshot_path="", debt_ledger_snapshot={},
        coefficient_snapshot={},
    )
    assert mem.cost_ledger is None


# ── 9. NKGCurator + NKGGraphStore 통합 ──────────────────────────
def test_nkg_curator_integration():
    from literary_system.nkg.graph_store import NKGGraphStore
    from literary_system.nkg.schema import EpisodeNode, NKGNodeType, NKGEdge, NKGEdgeType
    nkg = NKGGraphStore()
    for i in range(8):
        nkg.add_node(EpisodeNode(node_type=NKGNodeType.EPISODE,
                                  node_id=f"ep_{i}", label=f"ep{i}",
                                  episode_index=i))
        if i > 0:
            nkg.add_edge(NKGEdge(source=f"ep_{i-1}", target=f"ep_{i}",
                                  edge_type=NKGEdgeType.CAUSAL_LINK, weight=0.9))
    curator = NKGCurator(max_age_episodes=5, min_nodes_to_curate=5)
    report = curator.curate(nkg, current_episode=20)
    assert report.removed_count >= 0  # 정상 실행


# ── 10. Gate 10 전체 어댑터 계약 검증 ───────────────────────────
def test_gate10_all_adapters_pass():
    gate = LLMAdapterContractGate()
    adapters = [
        OpenAICompatibleAdapter.for_ollama(),
        OllamaAdapter(),
        MockLLMBridge(),
        make_ollama_adapter(model="mistral"),
    ]
    result = gate.check(adapters, task_router=TaskRouter())
    assert result.passed == True
    assert result.llm0_passed == True


# ── 11. Release Gate 목록에 Gate 10 존재 ─────────────────────────
def test_release_gate_has_gate10():
    gate_ids = [g[0] for g in GATES]
    assert "llm_adapter_contract" in gate_ids
    assert len(GATES) >= 8   # 기존 7 + Gate 10


# ── 12. run_release_gate() 실행 가능 ────────────────────────────
def test_run_release_gate_executes():
    result = run_release_gate()
    assert "version" in result
    assert result["version"] in ("V411", "V430", "V436", "V442", "V446", "V450", "V456", "V462", "V467", "V468", "V474", "V480", "V481", "V485", "V491", "V497", "V546", "V555")
    assert "gates_checked" in result
    assert result["gates_checked"] >= 8


# ── 13. Gate 10 Pass ─────────────────────────────────────────────
def test_gate10_passes_in_release():
    result = run_release_gate()
    gate10_result = result["results"].get("llm_adapter_contract", {})
    assert gate10_result.get("passed") == True


# ── 14. LLM-0 시스템 전체 준수 ──────────────────────────────────
def test_llm0_system_wide():
    """전체 스택에서 TaskRouter.route()가 generate()를 호출하지 않음."""
    gw, ctx = _make_full_stack(fitness=5.0)
    # call_count 변화 확인
    router = gw._router
    for tier_adapter in router._providers.values():
        if hasattr(tier_adapter, "call_count"):
            assert tier_adapter.call_count == 0
    # route() 호출 — LLM 생성 없어야 함
    router.route(ctx)
    for tier_adapter in router._providers.values():
        if hasattr(tier_adapter, "call_count"):
            assert tier_adapter.call_count == 0   # generate() 미호출


# ── 15. ProviderHealthMonitor 폴백 체인 통합 ─────────────────────
def test_health_monitor_fallback_chain():
    """local 오프라인 → speed로 자동 폴백."""
    def mock(pid, resp, available):
        class M(MockLLMBridge):
            def is_available(self): return available
            def get_provider_id(self): return pid
            @property
            def provider_name(self): return pid
            def __init__(self): super().__init__(scripted_response=resp)
        return M()

    providers = {
        "local":   mock("ollama", "local_resp", False),  # 오프라인
        "speed":   mock("haiku",  "speed_resp", True),
        "quality": mock("sonnet", "quality_resp", True),
    }
    health = ProviderHealthMonitor({p.get_provider_id(): p for p in providers.values()})
    router = TaskRouter(providers=providers, health_monitor=health)
    gw = UnifiedLLMGateway(task_router=router, health_monitor=health)
    resp = gw.call("prompt", LLMContext(narrative_fitness=2.0))
    # ollama 오프라인 → haiku 또는 sonnet으로 라우팅
    assert resp.provider_id in ("haiku", "sonnet")


# ── 16. OpenAICompatibleAdapter 팩토리 전체 ─────────────────────
def test_all_factories_create_valid_adapters():
    adapters = [
        OpenAICompatibleAdapter.for_ollama(),
        OpenAICompatibleAdapter.for_lmstudio(),
        OpenAICompatibleAdapter.for_openai("gpt-4o", "sk-test"),
        OpenAICompatibleAdapter.from_preset("vllm", "llama3"),
        make_ollama_adapter("gemma2"),
        OllamaAdapter("mistral"),
    ]
    gate = LLMAdapterContractGate()
    result = gate.check(adapters)
    assert result.passed == True


# ── 17. LLMContext coerce_context 전체 경로 ─────────────────────
def test_coerce_context_all_paths():
    from literary_system.llm_bridge.llm_context import coerce_context
    assert isinstance(coerce_context(None), LLMContext)
    assert isinstance(coerce_context({}), LLMContext)
    assert isinstance(coerce_context({"narrative_fitness": 7.0}), LLMContext)
    ctx = LLMContext(series_id="s1")
    assert coerce_context(ctx) is ctx


# ── 18. MultiLLMRouter Ollama 프로파일 등록 확인 ─────────────────
def test_multi_llm_router_ollama_profiles():
    from literary_system.llm_bridge.multi_llm_router import DEFAULT_PROFILES
    assert any("ollama" in k.lower() for k in DEFAULT_PROFILES.keys())


# ── 19. generate_with_response LLMResponse 타입 ─────────────────
def test_generate_with_response_all_adapters():
    adapters = [
        OpenAICompatibleAdapter(base_url="http://localhost:19999/v1",
                                 model="test"),
        OllamaAdapter(base_url="http://localhost:19999/v1"),
        MockLLMBridge(scripted_response="mock_resp"),
    ]
    ctx = LLMContext(timeout=1)
    for adapter in adapters:
        resp = adapter.generate_with_response("test prompt", ctx)
        assert isinstance(resp, LLMResponse)
        assert resp.latency_ms >= 0


# ── 20. V411 전체 신규 모듈 임포트 가능 ─────────────────────────
def test_all_v411_modules_importable():
    from literary_system.llm_bridge.llm_context import LLMContext, LLMResponse
    from literary_system.llm_bridge.openai_compatible_adapter import OpenAICompatibleAdapter
    from literary_system.llm_bridge.ollama_adapter import OllamaAdapter, make_ollama_adapter
    from literary_system.llm_bridge.routing.task_router import TaskRouter
    from literary_system.llm_bridge.health.provider_health_monitor import ProviderHealthMonitor
    from literary_system.llm_bridge.gateway.unified_llm_gateway import UnifiedLLMGateway
    from literary_system.llm_bridge.cost_ledger import CostLedger
    from literary_system.nkg.curators.nkg_curator import NKGCurator
    from literary_system.gates.gate10_llm_contract import LLMAdapterContractGate
    assert all([LLMContext, LLMResponse, OpenAICompatibleAdapter, OllamaAdapter,
                TaskRouter, ProviderHealthMonitor, UnifiedLLMGateway, CostLedger,
                NKGCurator, LLMAdapterContractGate])
