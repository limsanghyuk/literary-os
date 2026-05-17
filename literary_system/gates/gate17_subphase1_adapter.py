"""
Literary OS V463 -- Gate17: SubPhase1 Adapter Layer (V431~V436) 생존 검증

검증 항목:
  1. AdapterContractV2 6요소 계약 생존 (V431)
  2. AdaptersV2 3종 + CircuitBreakerState 생존 (V432)
  3. ModelRegistry CRUD + ModelSelectionPolicy (V433)
  4. CascadeOrchestrator + SemanticCache + StreamingNormalizer (V434)
  5. Resilience 4종 생존 (V435)
  6. SubPhase1 통합 round-trip (V436)

LLM-0 원칙: 실 API 미호출. MockLLMBridge 주입으로 격리.
"""
from __future__ import annotations


def _gate_subphase1_adapter_survival() -> dict:
    """Gate 17 -- SubPhase1 (V431~V436) 핵심 모듈 생존 검증."""
    try:
        # ── 1. AdapterContractV2 6요소 (V431) ────────────────────────────────
        from literary_system.llm_bridge.adapter_contract import (
            AdapterContractV2, KeyConfig, RetryPolicy, TimeoutConfig,
            TokenBudget, CostConfig,
        )
        key      = KeyConfig(env_var="GATE17_TEST_KEY")
        retry    = RetryPolicy(max_attempts=3, backoff_factor=1.5)
        timeout  = TimeoutConfig(connect_timeout=10.0, read_timeout=30.0)
        token    = TokenBudget(max_input_tokens=4096, max_output_tokens=1024)
        cost     = CostConfig(enabled=False)
        contract = AdapterContractV2(key=key, retry=retry, timeout=timeout,
                                     token=token, cost=cost)
        assert contract.retry.max_attempts == 3
        assert contract.token.max_input_tokens == 4096

        # ── 2. AdaptersV2 3종 + CircuitBreakerState (V432) ───────────────────
        from literary_system.llm_bridge.adapters_v2 import (
            ClaudeAdapterV2, OpenAIAdapterV2, OllamaAdapterV2,
            CircuitBreakerState,
        )
        cb = CircuitBreakerState()
        assert cb.can_pass(), "CircuitBreakerState 초기 CLOSED 아님"

        for AdapterCls in (ClaudeAdapterV2, OpenAIAdapterV2, OllamaAdapterV2):
            a = AdapterCls(contract=contract)
            assert not a.is_available(), f"{AdapterCls.__name__} no-key 환경 available 반환"
            resp = a.generate("ping", {})
            assert resp == "", f"{AdapterCls.__name__} no-client 빈 문자열 기대: {resp!r}"

        # ── 3. ModelRegistry + ModelSelectionPolicy (V433) ───────────────────
        from literary_system.llm_bridge.model_registry import (
            ModelRegistry, ModelEntry, ModelCapabilities,
            SelectionWeights, ModelSelectionPolicy, TaskContext,
        )
        reg = ModelRegistry()
        entry = ModelEntry(
            model_id="gate17-mock-model",
            provider="mock",
            tier="speed",
            capabilities=ModelCapabilities(
                supports_streaming=True,
                max_context_tokens=8192,
            ),
        )
        reg.register(entry)
        assert reg.get("gate17-mock-model").model_id == "gate17-mock-model"
        assert reg.list_active()

        policy   = ModelSelectionPolicy(reg)
        task_ctx = TaskContext(task_type="generation", preferred_tier="speed")
        selected_id = policy.select(task_ctx)
        assert selected_id, "ModelSelectionPolicy.select 반환 None/빈값"

        # ── 4. CascadeOrchestrator + SemanticCache + StreamingNormalizer (V434)
        from literary_system.llm_bridge.cascade import (
            CascadeOrchestrator, SemanticCache, StreamingNormalizer,
        )
        from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge

        cache = SemanticCache(ttl=60)
        cache.set("gate17_key", "gate17_cached_value")
        assert cache.get("gate17_key") == "gate17_cached_value"
        assert cache.get("nonexistent_key") is None

        norm   = StreamingNormalizer()
        chunks = list(norm.normalize_text("hello world"))
        assert chunks, "StreamingNormalizer 빈 결과"

        mock_adapter = MockLLMBridge()
        orchestrator = CascadeOrchestrator(
            speed_adapter=mock_adapter,
            quality_adapter=mock_adapter,
            cache=cache,
        )
        result = orchestrator.generate("gate17 test prompt", context={})
        assert result, "CascadeOrchestrator 빈 응답"

        # ── 5. Resilience 4종 (V435) ─────────────────────────────────────────
        from literary_system.llm_bridge.resilience import (
            ExperimentRegistry, FeatureFlag, FeatureFlagService,
            RetryBudget, RetryBudgetManager, GracefulDegradation,
        )

        from literary_system.llm_bridge.resilience import Variant
        exp_reg = ExperimentRegistry()
        variants = [Variant(name="A", weight=0.5), Variant(name="B", weight=0.5)]
        exp_reg.create(experiment_id="gate17_exp", variants=variants)
        assigned = exp_reg.assign("gate17_exp", "user_gate17")
        assert assigned in ("A", "B"), f"실험 배정 이상: {assigned}"

        ff_svc = FeatureFlagService()
        flag   = FeatureFlag(flag_id="gate17_flag", enabled=True, rollout_pct=100.0)
        ff_svc.define(flag)
        assert ff_svc.is_enabled("gate17_flag",   user_id="user_gate17")
        assert not ff_svc.is_enabled("nonexistent", user_id="user_gate17")

        rb     = RetryBudget(budget_id="gate17_budget", daily_limit=10, monthly_limit=100)
        rb_mgr = RetryBudgetManager()
        rb_mgr.register(rb)
        assert rb_mgr.can_retry("gate17_budget"), "RetryBudget 초기 소진 이상"
        rb.consume()

        gd = GracefulDegradation(failure_threshold=5, recovery_window=60)
        assert not gd.is_degraded(), "GracefulDegradation 초기 상태 이상"
        gd.record_success()

        # ── 6. SubPhase1 통합 round-trip (V436) ──────────────────────────────
        final = orchestrator.generate(
            "SubPhase1 통합 round-trip 검증",
            context={"model_hint": selected_id},
        )
        assert final, "SubPhase1 통합 round-trip 응답 없음"

        return {
            "pass": True,
            "modules_verified": 6,
            "adapters_tested": 3,
            "symbols_verified": [
                "AdapterContractV2", "KeyConfig", "RetryPolicy",
                "ClaudeAdapterV2", "OpenAIAdapterV2", "OllamaAdapterV2", "CircuitBreakerState",
                "ModelRegistry", "ModelSelectionPolicy", "TaskContext",
                "CascadeOrchestrator", "SemanticCache", "StreamingNormalizer",
                "ExperimentRegistry", "FeatureFlagService",
                "RetryBudget", "RetryBudgetManager", "GracefulDegradation",
            ],
            "summary": (
                "Gate17 PASS: SubPhase1 V431~V436 "
                "AdapterContract/AdaptersV2/ModelRegistry/Cascade/Resilience ALL OK"
            ),
        }

    except Exception as e:
        import traceback
        return {"pass": False, "reason": str(e), "trace": traceback.format_exc()[-600:]}
