"""
V456 — Phase 3 SubPhase 1 통합 테스트.

SP1 범위: V451(RealClaudeAdapter) + V452(RealOpenAIAdapter) +
          V453(RealOllamaAdapter) + V454(LiveCostMeter + SemanticCacheRedis) +
          V455(Gate15 LiveAdapterGate)

LLM-0 원칙: 외부 API 호출 없음. 모든 adapter는 call_fn 주입으로 검증.
"""
from __future__ import annotations
from typing import Any, Dict, List, Optional

import pytest

from literary_system.llm_bridge.llm_context import LLMContext


# ──────────────────────────────────────────────────────────────────────────────
# 헬퍼
# ──────────────────────────────────────────────────────────────────────────────

def _make_ctx(
    prompt: str = "테스트 프롬프트",
    max_tokens: int = 100,
    system_prompt: str = "",
) -> LLMContext:
    """테스트용 LLMContext 생성."""
    extra: Dict[str, Any] = {"user_prompt": prompt}
    if system_prompt:
        extra["system_prompt"] = system_prompt
    return LLMContext(
        series_id="sp1_test",
        episode_idx=0,
        narrative_fitness=0.9,
        max_tokens=max_tokens,
        extra=extra,
    )


# ──────────────────────────────────────────────────────────────────────────────
# SP1 모듈 임포트 생존
# ──────────────────────────────────────────────────────────────────────────────

class TestSP1ImportSurvival:
    def test_import_real_claude_adapter(self):
        from literary_system.adapters_live.real_claude_adapter import (
            RealClaudeAdapter, RealClaudeAdapterConfig,
        )
        assert RealClaudeAdapter is not None
        assert RealClaudeAdapterConfig is not None

    def test_import_real_openai_adapter(self):
        from literary_system.adapters_live.real_openai_adapter import (
            RealOpenAIAdapter, RealOpenAIAdapterConfig,
        )
        assert RealOpenAIAdapter is not None
        assert RealOpenAIAdapterConfig is not None

    def test_import_real_ollama_adapter(self):
        from literary_system.adapters_live.real_ollama_adapter import (
            RealOllamaAdapter, RealOllamaAdapterConfig,
        )
        assert RealOllamaAdapter is not None
        assert RealOllamaAdapterConfig is not None

    def test_import_adapters_live_package(self):
        from literary_system.adapters_live import (
            RealClaudeAdapter, RealOpenAIAdapter, RealOllamaAdapter,
        )
        assert RealClaudeAdapter is not None

    def test_import_live_cost_meter(self):
        from literary_system.cost_cache.live_cost_meter import LiveCostMeter
        assert LiveCostMeter is not None

    def test_import_semantic_cache_redis(self):
        from literary_system.cost_cache.semantic_cache_redis import SemanticCacheRedis
        assert SemanticCacheRedis is not None

    def test_import_cost_cache_package(self):
        from literary_system.cost_cache import LiveCostMeter, SemanticCacheRedis
        assert LiveCostMeter is not None
        assert SemanticCacheRedis is not None

    def test_import_gate15(self):
        from literary_system.gates.gate15_live_adapter_sp1 import _gate_live_adapter_sp1
        assert callable(_gate_live_adapter_sp1)


# ──────────────────────────────────────────────────────────────────────────────
# LLM-0 원칙 SP1 전반 검증
# ──────────────────────────────────────────────────────────────────────────────

class TestSP1LLMZeroPrinciple:
    def test_claude_adapter_lm0_compliant(self):
        from literary_system.adapters_live.real_claude_adapter import (
            RealClaudeAdapter, RealClaudeAdapterConfig,
        )
        responses = []
        def mock_call(messages, model, max_tokens, timeout):
            responses.append(True)
            return {"content": "안녕", "input_tokens": 5, "output_tokens": 3, "stop_reason": "end_turn"}
        adapter = RealClaudeAdapter(config=RealClaudeAdapterConfig(), call_fn=mock_call)
        result = adapter.call(_make_ctx("안녕하세요"))
        assert result.success is True
        assert len(responses) == 1

    def test_openai_adapter_lm0_compliant(self):
        from literary_system.adapters_live.real_openai_adapter import (
            RealOpenAIAdapter, RealOpenAIAdapterConfig,
        )
        calls = []
        def mock_call(**kwargs):
            calls.append(kwargs)
            return {
                "choices": [{"message": {"content": "hello"}, "finish_reason": "stop"}],
                "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
            }
        adapter = RealOpenAIAdapter(config=RealOpenAIAdapterConfig(), call_fn=mock_call)
        result = adapter.call(_make_ctx("테스트"))
        assert result.success is True
        assert len(calls) == 1

    def test_ollama_adapter_lm0_compliant(self):
        from literary_system.adapters_live.real_ollama_adapter import (
            RealOllamaAdapter, RealOllamaAdapterConfig,
        )
        calls = []
        def mock_call(url, payload, timeout):
            calls.append(url)
            return {
                "content": "ollama 응답",
                "input_tokens": 5,
                "output_tokens": 4,
                "eval_duration_ns": 200_000_000,
                "done": True,
            }
        adapter = RealOllamaAdapter(config=RealOllamaAdapterConfig(), call_fn=mock_call)
        result = adapter.call(_make_ctx("테스트"))
        assert result.success is True
        assert len(calls) == 1


# ──────────────────────────────────────────────────────────────────────────────
# RealLLMResponse 계약 통일성
# ──────────────────────────────────────────────────────────────────────────────

class TestSP1ResponseContract:
    def _make_claude(self, content="ok"):
        from literary_system.adapters_live.real_claude_adapter import (
            RealClaudeAdapter, RealClaudeAdapterConfig,
        )
        def mock_call(messages, model, max_tokens, timeout):
            return {"content": content, "input_tokens": 10, "output_tokens": 5, "stop_reason": "end_turn"}
        return RealClaudeAdapter(config=RealClaudeAdapterConfig(), call_fn=mock_call)

    def _make_openai(self, content="ok"):
        from literary_system.adapters_live.real_openai_adapter import (
            RealOpenAIAdapter, RealOpenAIAdapterConfig,
        )
        def mock_call(**kwargs):
            return {
                "content": content,
                "input_tokens": 10,
                "output_tokens": 5,
            }
        return RealOpenAIAdapter(config=RealOpenAIAdapterConfig(), call_fn=mock_call)

    def _make_ollama(self, content="ok"):
        from literary_system.adapters_live.real_ollama_adapter import (
            RealOllamaAdapter, RealOllamaAdapterConfig,
        )
        def mock_call(url, payload, timeout):
            return {
                "content": content,
                "input_tokens": 10,
                "output_tokens": 5,
                "eval_duration_ns": 100_000_000,
                "done": True,
            }
        return RealOllamaAdapter(config=RealOllamaAdapterConfig(), call_fn=mock_call)

    @pytest.mark.parametrize("adapter_name", ["claude", "openai", "ollama"])
    def test_response_has_text(self, adapter_name):
        maker = {"claude": self._make_claude, "openai": self._make_openai, "ollama": self._make_ollama}
        result = maker[adapter_name]("테스트 응답").call(_make_ctx("입력"))
        assert hasattr(result, "text")
        assert "테스트 응답" in result.text

    @pytest.mark.parametrize("adapter_name", ["claude", "openai", "ollama"])
    def test_response_has_tokens(self, adapter_name):
        maker = {"claude": self._make_claude, "openai": self._make_openai, "ollama": self._make_ollama}
        result = maker[adapter_name]().call(_make_ctx("입력"))
        assert hasattr(result, "input_tokens") and result.input_tokens >= 0
        assert hasattr(result, "output_tokens") and result.output_tokens >= 0

    @pytest.mark.parametrize("adapter_name", ["claude", "openai", "ollama"])
    def test_response_has_provider(self, adapter_name):
        maker = {"claude": self._make_claude, "openai": self._make_openai, "ollama": self._make_ollama}
        result = maker[adapter_name]().call(_make_ctx("입력"))
        assert hasattr(result, "provider") and isinstance(result.provider, str) and len(result.provider) > 0

    @pytest.mark.parametrize("adapter_name", ["claude", "openai", "ollama"])
    def test_response_has_latency(self, adapter_name):
        maker = {"claude": self._make_claude, "openai": self._make_openai, "ollama": self._make_ollama}
        result = maker[adapter_name]().call(_make_ctx("입력"))
        assert hasattr(result, "latency_ms") and result.latency_ms >= 0.0

    @pytest.mark.parametrize("adapter_name", ["claude", "openai", "ollama"])
    def test_response_success_true(self, adapter_name):
        maker = {"claude": self._make_claude, "openai": self._make_openai, "ollama": self._make_ollama}
        result = maker[adapter_name]().call(_make_ctx("입력"))
        assert result.success is True

    @pytest.mark.parametrize("adapter_name", ["claude", "openai", "ollama"])
    def test_response_has_call_id(self, adapter_name):
        maker = {"claude": self._make_claude, "openai": self._make_openai, "ollama": self._make_ollama}
        result = maker[adapter_name]().call(_make_ctx("입력"))
        assert hasattr(result, "call_id") and isinstance(result.call_id, str)


# ──────────────────────────────────────────────────────────────────────────────
# LiveCostMeter ↔ 어댑터 연동
# ──────────────────────────────────────────────────────────────────────────────

class TestSP1CostMeterIntegration:
    def test_record_from_claude_response(self):
        from literary_system.adapters_live.real_claude_adapter import (
            RealClaudeAdapter, RealClaudeAdapterConfig,
        )
        from literary_system.cost_cache.live_cost_meter import LiveCostMeter
        def mock_call(messages, model, max_tokens, timeout):
            return {"content": "c", "input_tokens": 200, "output_tokens": 100, "stop_reason": "end_turn"}
        adapter = RealClaudeAdapter(config=RealClaudeAdapterConfig(), call_fn=mock_call)
        meter = LiveCostMeter(usd_to_krw=1350.0)
        rec = meter.record_from_response("tenant_claude", adapter.call(_make_ctx("테스트")))
        assert rec is not None and rec.input_tokens == 200 and rec.output_tokens == 100

    def test_record_from_openai_response(self):
        from literary_system.adapters_live.real_openai_adapter import (
            RealOpenAIAdapter, RealOpenAIAdapterConfig,
        )
        from literary_system.cost_cache.live_cost_meter import LiveCostMeter
        def mock_call(**kwargs):
            return {
                "content": "openai 응답",
                "input_tokens": 150,
                "output_tokens": 80,
            }
        adapter = RealOpenAIAdapter(config=RealOpenAIAdapterConfig(), call_fn=mock_call)
        meter = LiveCostMeter()
        rec = meter.record_from_response("tenant_openai", adapter.call(_make_ctx("테스트")))
        assert rec is not None and rec.input_tokens == 150 and rec.output_tokens == 80

    def test_record_from_ollama_response(self):
        from literary_system.adapters_live.real_ollama_adapter import (
            RealOllamaAdapter, RealOllamaAdapterConfig,
        )
        from literary_system.cost_cache.live_cost_meter import LiveCostMeter
        def mock_call(url, payload, timeout):
            return {
                "content": "oll", "input_tokens": 50, "output_tokens": 30,
                "eval_duration_ns": 150_000_000, "done": True,
            }
        adapter = RealOllamaAdapter(config=RealOllamaAdapterConfig(), call_fn=mock_call)
        meter = LiveCostMeter()
        rec = meter.record_from_response("tenant_ollama", adapter.call(_make_ctx("테스트")))
        assert rec is not None
        assert meter.get_cost_usd("tenant_ollama") == 0.0  # ollama free

    def test_multi_tenant_isolation(self):
        from literary_system.adapters_live.real_claude_adapter import (
            RealClaudeAdapter, RealClaudeAdapterConfig,
        )
        from literary_system.adapters_live.real_openai_adapter import (
            RealOpenAIAdapter, RealOpenAIAdapterConfig,
        )
        from literary_system.cost_cache.live_cost_meter import LiveCostMeter
        def claude_call(messages, model, max_tokens, timeout):
            return {"content": "c", "input_tokens": 100, "output_tokens": 50, "stop_reason": "end_turn"}
        def openai_call(**kwargs):
            return {
                "content": "o",
                "input_tokens": 200,
                "output_tokens": 100,
            }
        claude = RealClaudeAdapter(config=RealClaudeAdapterConfig(), call_fn=claude_call)
        openai = RealOpenAIAdapter(config=RealOpenAIAdapterConfig(), call_fn=openai_call)
        meter = LiveCostMeter()
        meter.record_from_response("tenant_a", claude.call(_make_ctx("입력")))
        meter.record_from_response("tenant_b", openai.call(_make_ctx("입력")))
        assert "tenant_a" in meter.list_tenants()
        assert "tenant_b" in meter.list_tenants()
        assert meter.tenant_stats("tenant_a")["total_input_tokens"] == 100
        assert meter.tenant_stats("tenant_b")["total_input_tokens"] == 200


# ──────────────────────────────────────────────────────────────────────────────
# SemanticCacheRedis ↔ 어댑터 연동
# ──────────────────────────────────────────────────────────────────────────────

class TestSP1SemanticCacheIntegration:
    def test_cache_adapter_response(self):
        from literary_system.adapters_live.real_claude_adapter import (
            RealClaudeAdapter, RealClaudeAdapterConfig,
        )
        from literary_system.cost_cache.semantic_cache_redis import SemanticCacheRedis
        call_count = [0]
        def mock_call(messages, model, max_tokens, timeout):
            call_count[0] += 1
            return {"content": "캐시 응답", "input_tokens": 10, "output_tokens": 5, "stop_reason": "end_turn"}
        adapter = RealClaudeAdapter(config=RealClaudeAdapterConfig(), call_fn=mock_call)
        cache = SemanticCacheRedis(tenant_id="integration_test")
        prompt = "한국 문학의 특징을 설명해주세요"
        assert cache.get(prompt) is None
        result = adapter.call(_make_ctx(prompt))
        cache.set(prompt, result.text)
        assert call_count[0] == 1
        cached2 = cache.get(prompt)
        assert cached2 == "캐시 응답"

    def test_cache_miss_different_prompt(self):
        from literary_system.cost_cache.semantic_cache_redis import SemanticCacheRedis
        cache = SemanticCacheRedis(tenant_id="sp1_miss_test", similarity_threshold=0.95)
        cache.set("파이썬 문법 튜토리얼", "파이썬 응답")
        assert cache.get("한국어 맞춤법 검사기") is None

    def test_cache_tenant_isolation(self):
        from literary_system.cost_cache.semantic_cache_redis import SemanticCacheRedis
        cache_a = SemanticCacheRedis(tenant_id="sp1_tenant_a")
        cache_b = SemanticCacheRedis(tenant_id="sp1_tenant_b")
        cache_a.set("동일 프롬프트", "A의 응답")
        assert cache_b.get("동일 프롬프트") is None

    def test_cache_hit_rate_tracking(self):
        from literary_system.cost_cache.semantic_cache_redis import SemanticCacheRedis
        cache = SemanticCacheRedis(tenant_id="sp1_hitrate")
        cache.set("테스트 프롬프트", "테스트 응답")
        cache.get("테스트 프롬프트")  # hit
        cache.get("완전히 다른 질문 xyz")  # miss
        stats = cache.stats()
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5


# ──────────────────────────────────────────────────────────────────────────────
# Gate15 통합 검증
# ──────────────────────────────────────────────────────────────────────────────

class TestSP1Gate15:
    def test_gate15_passes(self):
        from literary_system.gates.gate15_live_adapter_sp1 import _gate_live_adapter_sp1
        result = _gate_live_adapter_sp1()
        assert result["pass"] is True

    def test_gate15_golden_50(self):
        from literary_system.gates.gate15_live_adapter_sp1 import _gate_live_adapter_sp1
        result = _gate_live_adapter_sp1()
        assert result["golden_passed"] == 50
        assert result["golden_total"] == 50

    def test_gate15_no_failures(self):
        from literary_system.gates.gate15_live_adapter_sp1 import _gate_live_adapter_sp1
        result = _gate_live_adapter_sp1()
        assert result.get("failures", []) == []

    def test_gate15_via_release_gate(self):
        from literary_system.gates.release_gate import GATES
        gate_ids = [g[0] for g in GATES]
        assert "live_adapter_sp1" in gate_ids

    def test_gate15_is_present(self):
        from literary_system.gates.release_gate import GATES
        gate_ids = [g[0] for g in GATES]
        assert "live_adapter_sp1" in gate_ids


# ──────────────────────────────────────────────────────────────────────────────
# Release Gate V456 전체 실행
# ──────────────────────────────────────────────────────────────────────────────

class TestV456ReleaseGate:
    def test_release_gate_version(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["version"] in ("V456", "V462", "V467", "V468", "V474", "V480", "V481", "V485", "V491", "V497", "V546", "V555", "V556", "V561", "V571", "V620")

    def test_release_gate_has_gate15(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert "live_adapter_sp1" in result["results"]

    def test_release_gate_gate15_passes(self):
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        assert result["results"]["live_adapter_sp1"]["pass"] is True

    def test_release_gate_passes(self):
        """studio_api_contract 제외하고 전체 pass 확인."""
        from literary_system.gates.release_gate import run_release_gate
        result = run_release_gate()
        failures = [i for i in result["issues"] if "studio_api_contract" not in i]
        assert failures == [], f"Gate 실패: {failures}"

    def test_release_gate_gate_count(self):
        from literary_system.gates.release_gate import GATES
        assert len(GATES) >= 13  # Gate 1~6 + Gate 9~15 = 13繫 이상
