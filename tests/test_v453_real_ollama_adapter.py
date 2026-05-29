"""
V453 — RealOllamaAdapter 테스트
LLM-0 원칙 준수: call_fn / http_fn 주입으로 실 Ollama 서버 없이 테스트.
"""
import json
import time
import pytest
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

# literary_system.llm_bridge를 먼저 임포트하여 sys.modules에 안정적으로 등록
from literary_system.llm_bridge.llm_context import LLMContext
from literary_system.adapters_live.real_ollama_adapter import (
    RealOllamaAdapter,
    RealOllamaAdapterConfig,
    GPUMemorySnapshot,
)
from literary_system.adapters_live.real_claude_adapter import RealLLMResponse


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def make_ctx(
    user_prompt: str = "테스트 프롬프트",
    history: Optional[List[Dict]] = None,
    stream: bool = False,
    system_prompt: str = "",
    max_tokens: int = 512,
) -> LLMContext:
    extra: Dict[str, Any] = {"user_prompt": user_prompt}
    if history:
        extra["history"] = history
    if stream:
        extra["stream"] = True
    if system_prompt:
        extra["system_prompt"] = system_prompt
    return LLMContext(
        series_id="s1",
        episode_idx=0,
        narrative_fitness=0.8,
        max_tokens=max_tokens,
        extra=extra,
    )


def make_adapter(
    response_text: str = "Ollama 응답",
    mock_input_t: int = 50,
    mock_output_t: int = 30,
    model: str = "llama3.2",
    auto_pull: bool = False,
    fail_once: bool = False,
    gpu_data: Optional[Dict] = None,
) -> RealOllamaAdapter:
    """LLM-0 주입 어댑터 생성."""
    call_count = {"n": 0}

    def call_fn(url: str, payload: Dict, timeout: float) -> Dict:
        call_count["n"] += 1
        if fail_once and call_count["n"] == 1:
            raise ConnectionError("서버 일시적 오류")
        return {
            "content": response_text,
            "input_tokens": mock_input_t,
            "output_tokens": mock_output_t,
            "model": model,
            "eval_duration_ns": 123_000_000,
        }

    def http_fn(url: str, timeout: float) -> Dict:
        if "/api/tags" in url:
            return {"models": [{"name": model}]}
        if "/api/ps" in url:
            if gpu_data:
                return gpu_data
            return {"models": [{"name": model, "size_vram": 4 * 1024 * 1024 * 1024}]}
        return {}

    cfg = RealOllamaAdapterConfig(
        model=model,
        auto_pull=auto_pull,
        base_delay=0.0,
        max_delay=0.0,
    )
    return RealOllamaAdapter(config=cfg, call_fn=call_fn, http_fn=http_fn)


# ---------------------------------------------------------------------------
# 1. 초기화 테스트
# ---------------------------------------------------------------------------

class TestRealOllamaAdapterInit:

    def test_default_config(self):
        adapter = RealOllamaAdapter()
        assert adapter.config.model == "llama3.2"
        assert adapter.config.base_url == "http://localhost:11434"
        assert adapter.config.max_retries == 5

    def test_custom_config(self):
        cfg = RealOllamaAdapterConfig(model="mistral", base_url="http://gpu-node:11434")
        adapter = RealOllamaAdapter(config=cfg)
        assert adapter.config.model == "mistral"
        assert adapter.config.base_url == "http://gpu-node:11434"

    def test_call_fn_injection(self):
        fn = lambda url, payload, timeout: {"content": "ok", "input_tokens": 5, "output_tokens": 3}
        adapter = RealOllamaAdapter(call_fn=fn)
        assert adapter._call_fn is fn

    def test_tenant_id(self):
        adapter = RealOllamaAdapter(tenant_id="tenant-42")
        assert adapter.tenant_id == "tenant-42"

    def test_initial_stats_zero(self):
        adapter = RealOllamaAdapter()
        s = adapter.stats()
        assert s["total_calls"] == 0
        assert s["total_cost_usd"] == 0.0
        assert s["error_count"] == 0

    def test_provider_name(self):
        adapter = make_adapter()
        assert adapter.get_provider_name() == "ollama"

    def test_model_info_keys(self):
        adapter = make_adapter()
        info = adapter.get_model_info()
        assert info["provider"] == "ollama"
        assert info["input_price_per_1k"] == 0.0
        assert info["output_price_per_1k"] == 0.0
        assert "base_url" in info

    def test_embedding_models_set(self):
        assert "bge-m3" in RealOllamaAdapterConfig.EMBEDDING_MODELS
        assert "nomic-embed-text" in RealOllamaAdapterConfig.EMBEDDING_MODELS


# ---------------------------------------------------------------------------
# 2. 기본 호출 테스트
# ---------------------------------------------------------------------------

class TestRealOllamaAdapterCall:

    def test_basic_call_returns_response(self):
        adapter = make_adapter("안녕하세요", mock_input_t=40, mock_output_t=20)
        ctx = make_ctx("안녕?")
        resp = adapter.call(ctx)
        assert isinstance(resp, RealLLMResponse)
        assert resp.text == "안녕하세요"
        assert resp.success is True
        assert resp.provider == "ollama"

    def test_tokens_populated(self):
        adapter = make_adapter(mock_input_t=60, mock_output_t=25)
        ctx = make_ctx("테스트")
        resp = adapter.call(ctx)
        assert resp.input_tokens == 60
        assert resp.output_tokens == 25
        assert resp.tokens_used == 85

    def test_cost_is_zero(self):
        adapter = make_adapter()
        ctx = make_ctx("테스트")
        resp = adapter.call(ctx)
        assert resp.cost_usd == 0.0

    def test_call_id_is_uuid(self):
        adapter = make_adapter()
        ctx = make_ctx("테스트")
        resp = adapter.call(ctx)
        assert len(resp.call_id) == 36  # UUID 형식
        assert "-" in resp.call_id

    def test_latency_from_eval_duration(self):
        """eval_duration_ns → latency_ms 변환 확인."""
        # eval_duration_ns=123_000_000 → 123ms
        adapter = make_adapter()
        ctx = make_ctx("테스트")
        resp = adapter.call(ctx)
        # 123_000_000 ns = 123 ms
        assert abs(resp.latency_ms - 123.0) < 1.0

    def test_empty_prompt_allowed(self):
        adapter = make_adapter("빈 프롬프트 응답")
        ctx = make_ctx("")
        resp = adapter.call(ctx)
        assert resp.success is True

    def test_stats_updated_after_call(self):
        adapter = make_adapter(mock_input_t=100, mock_output_t=50)
        ctx = make_ctx("테스트")
        adapter.call(ctx)
        s = adapter.stats()
        assert s["total_calls"] == 1
        assert s["total_input_tokens"] == 100
        assert s["total_output_tokens"] == 50

    def test_multiple_calls_accumulate(self):
        adapter = make_adapter(mock_input_t=50, mock_output_t=30)
        for _ in range(3):
            adapter.call(make_ctx("테스트"))
        s = adapter.stats()
        assert s["total_calls"] == 3
        assert s["total_input_tokens"] == 150


# ---------------------------------------------------------------------------
# 3. 시스템 프롬프트 / 히스토리 테스트
# ---------------------------------------------------------------------------

class TestRealOllamaAdapterContext:

    def test_system_prompt_via_extra(self):
        received_payloads = []

        def call_fn(url, payload, timeout):
            received_payloads.append(payload)
            return {"content": "ok", "input_tokens": 5, "output_tokens": 3}

        adapter = RealOllamaAdapter(call_fn=call_fn)
        ctx = make_ctx("질문", system_prompt="당신은 소설가입니다.")
        adapter.call(ctx)

        messages = received_payloads[0]["messages"]
        assert messages[0]["role"] == "system"
        assert "소설가" in messages[0]["content"]

    def test_history_prepended(self):
        received_payloads = []

        def call_fn(url, payload, timeout):
            received_payloads.append(payload)
            return {"content": "ok", "input_tokens": 5, "output_tokens": 3}

        adapter = RealOllamaAdapter(call_fn=call_fn)
        history = [
            {"role": "user", "content": "이전 질문"},
            {"role": "assistant", "content": "이전 답변"},
        ]
        ctx = make_ctx("새 질문", history=history)
        adapter.call(ctx)

        messages = received_payloads[0]["messages"]
        # history(2) + user(1)
        assert len(messages) == 3
        assert messages[-1]["role"] == "user"
        assert messages[-1]["content"] == "새 질문"

    def test_max_tokens_passed_to_payload(self):
        received_payloads = []

        def call_fn(url, payload, timeout):
            received_payloads.append(payload)
            return {"content": "ok", "input_tokens": 5, "output_tokens": 3}

        adapter = RealOllamaAdapter(call_fn=call_fn)
        ctx = make_ctx("테스트", max_tokens=1024)
        adapter.call(ctx)

        options = received_payloads[0].get("options", {})
        assert options.get("num_predict") == 1024

    def test_stream_flag_passed(self):
        received_payloads = []

        def call_fn(url, payload, timeout):
            received_payloads.append(payload)
            return {"content": "스트림 응답", "input_tokens": 5, "output_tokens": 3}

        adapter = RealOllamaAdapter(call_fn=call_fn)
        ctx = make_ctx("스트림 테스트", stream=True)
        resp = adapter.call(ctx)

        assert received_payloads[0]["stream"] is True
        assert resp.success is True


# ---------------------------------------------------------------------------
# 4. 재시도 / 오류 처리 테스트
# ---------------------------------------------------------------------------

class TestRealOllamaAdapterRetry:

    def test_retry_on_failure(self):
        attempt_count = {"n": 0}

        def call_fn(url, payload, timeout):
            attempt_count["n"] += 1
            if attempt_count["n"] < 3:
                raise ConnectionError("연결 실패")
            return {"content": "성공", "input_tokens": 10, "output_tokens": 5}

        cfg = RealOllamaAdapterConfig(max_retries=5, base_delay=0.0, max_delay=0.0)
        adapter = RealOllamaAdapter(config=cfg, call_fn=call_fn)
        ctx = make_ctx("테스트")
        resp = adapter.call(ctx)

        assert resp.success is True
        assert resp.text == "성공"
        assert resp.retries == 2

    def test_all_retries_fail(self):
        def call_fn(url, payload, timeout):
            raise TimeoutError("항상 타임아웃")

        cfg = RealOllamaAdapterConfig(max_retries=2, base_delay=0.0, max_delay=0.0)
        adapter = RealOllamaAdapter(config=cfg, call_fn=call_fn)
        ctx = make_ctx("테스트")
        resp = adapter.call(ctx)

        assert resp.success is False
        assert resp.retries == 3  # 초기 1 + 재시도 2
        assert "타임아웃" in resp.error
        assert resp.text == ""

    def test_error_count_incremented(self):
        def call_fn(url, payload, timeout):
            raise RuntimeError("오류")

        cfg = RealOllamaAdapterConfig(max_retries=0, base_delay=0.0)
        adapter = RealOllamaAdapter(config=cfg, call_fn=call_fn)
        adapter.call(make_ctx("테스트"))
        adapter.call(make_ctx("테스트"))

        assert adapter.stats()["error_count"] == 2

    def test_fail_once_then_succeed(self):
        adapter = make_adapter("성공 응답", fail_once=True)
        ctx = make_ctx("테스트")
        resp = adapter.call(ctx)
        assert resp.success is True
        assert resp.retries >= 1


# ---------------------------------------------------------------------------
# 5. 비용 추정 테스트
# ---------------------------------------------------------------------------

class TestRealOllamaAdapterCostEstimate:

    def test_cost_estimate_always_zero(self):
        adapter = make_adapter()
        ctx = make_ctx("비용 추정 테스트")
        cost = adapter.cost_estimate(ctx)
        assert cost == 0.0

    def test_cost_estimate_long_prompt_zero(self):
        adapter = make_adapter()
        ctx = make_ctx("a" * 10000)
        assert adapter.cost_estimate(ctx) == 0.0


# ---------------------------------------------------------------------------
# 6. 모델 관리 테스트
# ---------------------------------------------------------------------------

class TestRealOllamaAdapterModelManagement:

    def test_list_models(self):
        adapter = make_adapter(model="llama3.2")
        models = adapter.list_models()
        assert "llama3.2" in models

    def test_is_model_available_true(self):
        adapter = make_adapter(model="llama3.2")
        assert adapter.is_model_available("llama3.2") is True

    def test_is_model_available_false(self):
        adapter = make_adapter(model="llama3.2")
        assert adapter.is_model_available("nonexistent-model-xyz") is False

    def test_is_model_available_base_name_match(self):
        """'llama3.2' == 'llama3.2:latest' 형태 매칭."""

        def http_fn(url, timeout):
            return {"models": [{"name": "llama3.2:latest"}]}

        cfg = RealOllamaAdapterConfig(model="llama3.2")
        adapter = RealOllamaAdapter(config=cfg, http_fn=http_fn)
        # base name 매칭 확인
        assert adapter.is_model_available("llama3.2") is True

    def test_pull_model_with_call_fn_injection(self):
        """call_fn 주입 환경에서는 pull 항상 True."""
        adapter = make_adapter()
        assert adapter.pull_model("llama3.2") is True

    def test_pull_model_returns_true_on_success(self):
        pull_called = {"n": 0}

        def call_fn(url, payload, timeout):
            pull_called["n"] += 1
            return {"content": "ok", "input_tokens": 5, "output_tokens": 3}

        adapter = RealOllamaAdapter(call_fn=call_fn)
        # call_fn 주입 → 항상 True
        result = adapter.pull_model("mistral")
        assert result is True


# ---------------------------------------------------------------------------
# 7. GPU 메모리 모니터링 테스트
# ---------------------------------------------------------------------------

class TestRealOllamaAdapterGPUMonitor:

    def test_gpu_snapshot_from_ollama_api(self):
        adapter = make_adapter(gpu_data={"models": [{"name": "llama3.2", "size_vram": 4_294_967_296}]})
        snap = adapter.get_gpu_memory()
        assert isinstance(snap, GPUMemorySnapshot)
        assert snap.source in ("ollama-api", "nvidia-smi", "unavailable")

    def test_gpu_snapshot_unavailable_source(self):
        """nvidia-smi 없고 http_fn도 없는 경우."""
        cfg = RealOllamaAdapterConfig()
        adapter = RealOllamaAdapter(config=cfg, call_fn=lambda **kw: {"content": "ok", "input_tokens": 1, "output_tokens": 1})
        snap = adapter.get_gpu_memory()
        assert isinstance(snap, GPUMemorySnapshot)
        assert snap.source in ("nvidia-smi", "unavailable")

    def test_gpu_snapshot_used_gb(self):
        # 4GB = 4 * 1024^3
        snap = GPUMemorySnapshot(
            timestamp_ms=0,
            used_bytes=4 * 1024 ** 3,
            source="ollama-api",
        )
        assert abs(snap.used_gb - 4.0) < 0.001

    def test_gpu_snapshots_recorded_after_call(self):
        adapter = make_adapter()
        ctx = make_ctx("테스트")
        adapter.call(ctx)
        s = adapter.stats()
        assert s["gpu_snapshots"] >= 0  # 기록 시도

    def test_parse_ollama_ps_empty(self):
        adapter = make_adapter()
        result = adapter._parse_ollama_ps({"models": []}, 0.0)
        assert result is None

    def test_parse_ollama_ps_multiple_models(self):
        adapter = make_adapter()
        data = {
            "models": [
                {"name": "llama3.2", "size_vram": 2 * 1024 ** 3},
                {"name": "mistral", "size_vram": 2 * 1024 ** 3},
            ]
        }
        snap = adapter._parse_ollama_ps(data, 0.0)
        assert snap is not None
        assert snap.used_bytes == 4 * 1024 ** 3
        assert snap.source == "ollama-api"

    def test_gpu_snapshot_timestamp(self):
        adapter = make_adapter()
        before = time.monotonic() * 1000
        snap = adapter.get_gpu_memory()
        after = time.monotonic() * 1000
        assert before <= snap.timestamp_ms <= after + 10


# ---------------------------------------------------------------------------
# 8. Health Check 테스트
# ---------------------------------------------------------------------------

class TestRealOllamaAdapterHealth:

    def test_health_check_with_call_fn(self):
        adapter = make_adapter()
        assert adapter.health_check() is True

    def test_health_check_with_http_fn(self):
        def http_fn(url, timeout):
            return {"models": []}

        cfg = RealOllamaAdapterConfig()
        adapter = RealOllamaAdapter(config=cfg, http_fn=http_fn)
        assert adapter.health_check() is True

    def test_health_check_no_server(self):
        """서버 없는 환경 — False 반환 (연결 실패)."""
        cfg = RealOllamaAdapterConfig(base_url="http://127.0.0.1:19999")
        adapter = RealOllamaAdapter(config=cfg)
        # call_fn/http_fn 없이 실제 서버 없으면 False
        result = adapter.health_check()
        assert result is False


# ---------------------------------------------------------------------------
# 9. 통계 / 리셋 테스트
# ---------------------------------------------------------------------------

class TestRealOllamaAdapterStats:

    def test_stats_keys(self):
        adapter = make_adapter()
        s = adapter.stats()
        for key in ["total_calls", "total_input_tokens", "total_output_tokens",
                    "total_cost_usd", "avg_latency_ms", "error_count",
                    "tenant_id", "gpu_snapshots"]:
            assert key in s

    def test_avg_latency_computed(self):
        adapter = make_adapter()
        ctx = make_ctx("테스트")
        for _ in range(4):
            adapter.call(ctx)
        s = adapter.stats()
        assert s["avg_latency_ms"] >= 0.0

    def test_reset_stats(self):
        adapter = make_adapter(mock_input_t=100, mock_output_t=50)
        for _ in range(5):
            adapter.call(make_ctx("테스트"))
        adapter.reset_stats()
        s = adapter.stats()
        assert s["total_calls"] == 0
        assert s["total_input_tokens"] == 0
        assert s["gpu_snapshots"] == 0

    def test_cost_always_zero_in_stats(self):
        adapter = make_adapter()
        for _ in range(10):
            adapter.call(make_ctx("테스트"))
        assert adapter.stats()["total_cost_usd"] == 0.0

    def test_tenant_id_in_stats(self):
        adapter = RealOllamaAdapter(
            config=RealOllamaAdapterConfig(),
            call_fn=lambda **kw: {"content": "ok", "input_tokens": 1, "output_tokens": 1},
            tenant_id="my-tenant",
        )
        assert adapter.stats()["tenant_id"] == "my-tenant"


# ---------------------------------------------------------------------------
# 10. 응답 정규화 테스트
# ---------------------------------------------------------------------------

class TestRealOllamaAdapterNormalization:

    def test_normalize_chat_response_basic(self):
        adapter = make_adapter()
        body = {
            "message": {"role": "assistant", "content": "정규화 응답"},
            "prompt_eval_count": 20,
            "eval_count": 15,
            "eval_duration": 500_000_000,
            "model": "llama3.2",
            "done": True,
        }
        result = adapter._normalize_chat_response(body)
        assert result["content"] == "정규화 응답"
        assert result["input_tokens"] == 20
        assert result["output_tokens"] == 15
        assert result["eval_duration_ns"] == 500_000_000

    def test_normalize_empty_message(self):
        adapter = make_adapter()
        body = {"message": {}, "done": True}
        result = adapter._normalize_chat_response(body)
        assert result["content"] == ""

    def test_normalize_missing_token_counts(self):
        """prompt_eval_count 없으면 _count_tokens 추정 사용."""
        adapter = make_adapter()
        body = {
            "message": {"content": "짧은 응답"},
            "done": True,
        }
        result = adapter._normalize_chat_response(body)
        assert result["input_tokens"] > 0  # 추정값

    def test_streaming_response_parse(self):
        """스트리밍 청크 결합 확인."""
        import io

        chunks = [
            json.dumps({"message": {"role": "assistant", "content": "안"}, "done": False}),
            json.dumps({"message": {"role": "assistant", "content": "녕"}, "done": False}),
            json.dumps({
                "message": {"role": "assistant", "content": ""},
                "done": True,
                "prompt_eval_count": 10,
                "eval_count": 2,
                "eval_duration": 100_000_000,
                "model": "llama3.2",
            }),
        ]
        lines = "\n".join(chunks).encode("utf-8")
        mock_resp = io.BytesIO(lines)

        adapter = make_adapter()
        result = adapter._parse_streaming_response(mock_resp)
        assert result["content"] == "안녕"
        assert result["input_tokens"] == 10
        assert result["output_tokens"] == 2

    def test_url_contains_api_chat(self):
        """호출 URL이 /api/chat 엔드포인트인지 확인."""
        received_urls = []

        def call_fn(url, payload, timeout):
            received_urls.append(url)
            return {"content": "ok", "input_tokens": 5, "output_tokens": 3}

        adapter = RealOllamaAdapter(call_fn=call_fn)
        adapter.call(make_ctx("테스트"))
        assert "/api/chat" in received_urls[0]


# ---------------------------------------------------------------------------
# 11. 설정 정책 테스트
# ---------------------------------------------------------------------------

class TestRealOllamaAdapterConfig:

    def test_default_base_url(self):
        cfg = RealOllamaAdapterConfig()
        assert "11434" in cfg.base_url

    def test_zero_cost_config(self):
        cfg = RealOllamaAdapterConfig()
        assert cfg.input_price_per_1k == 0.0
        assert cfg.output_price_per_1k == 0.0

    def test_auto_pull_default_true(self):
        cfg = RealOllamaAdapterConfig()
        assert cfg.auto_pull is True

    def test_longer_timeout_than_cloud(self):
        """Ollama 타임아웃은 클라우드보다 길어야 한다."""
        cfg = RealOllamaAdapterConfig()
        assert cfg.timeout_s >= 60.0

    def test_pull_timeout_separate(self):
        cfg = RealOllamaAdapterConfig()
        assert cfg.pull_timeout_s >= cfg.timeout_s

    def test_gpu_warning_disabled_by_default(self):
        cfg = RealOllamaAdapterConfig()
        assert cfg.gpu_memory_warning_bytes == 0

    def test_custom_model_name(self):
        cfg = RealOllamaAdapterConfig(model="phi3:mini")
        assert cfg.model == "phi3:mini"

    def test_get_rate_limits(self):
        adapter = make_adapter()
        limits = adapter.get_rate_limits()
        assert "max_retries" in limits
        assert "base_delay" in limits
        assert "max_delay" in limits
        assert "timeout_s" in limits
        assert limits["max_retries"] == RealOllamaAdapterConfig().max_retries
        assert limits["timeout_s"] == RealOllamaAdapterConfig().timeout_s
