"""
V411-A 테스트 — LLMContext + LLMResponse 강타입 계약.

검증 항목:
  1. LLMContext 기본값 생성
  2. LLMContext 필드 설정
  3. normalized_fitness() 범위 클램핑
  4. from_dict() 하위 호환 변환
  5. to_dict() 직렬화
  6. coerce_context() dict → LLMContext
  7. coerce_context() LLMContext 통과
  8. coerce_context() None → 기본 LLMContext
  9. LLMResponse 기본 생성
  10. LLMResponse 필드 설정
  11. MockLLMBridge LLMContext 수용
  12. MockLLMBridge dict context 하위 호환
  13. MockLLMBridge context=None 허용
  14. LLMBridgeInterface.is_available() 기본값
  15. LLMBridgeInterface.get_provider_id() 기본값
"""
from __future__ import annotations
import pytest
from literary_system.llm_bridge.llm_context import LLMContext, LLMResponse, coerce_context
from literary_system.llm_bridge.mock_llm_bridge import MockLLMBridge


# ── 1. LLMContext 기본값 ─────────────────────────────────────────
def test_llm_context_defaults():
    ctx = LLMContext()
    assert ctx.series_id == ""
    assert ctx.episode_idx == 0
    assert ctx.narrative_fitness == 0.0
    assert ctx.provider_hint == ""
    assert ctx.max_tokens == 2000
    assert ctx.temperature == 0.7
    assert ctx.timeout == 30
    assert ctx.extra == {}


# ── 2. LLMContext 필드 설정 ──────────────────────────────────────
def test_llm_context_fields():
    ctx = LLMContext(
        series_id="series_001",
        episode_idx=5,
        narrative_fitness=7.5,
        provider_hint="quality",
        max_tokens=4000,
        temperature=0.9,
        timeout=60,
        extra={"scene_id": "s01"},
    )
    assert ctx.series_id == "series_001"
    assert ctx.episode_idx == 5
    assert ctx.narrative_fitness == 7.5
    assert ctx.provider_hint == "quality"
    assert ctx.max_tokens == 4000
    assert ctx.timeout == 60
    assert ctx.extra["scene_id"] == "s01"


# ── 3. normalized_fitness 범위 클램핑 ────────────────────────────
def test_normalized_fitness_normal():
    ctx = LLMContext(narrative_fitness=7.5)
    assert abs(ctx.normalized_fitness() - 0.75) < 1e-9

def test_normalized_fitness_clamp_upper():
    ctx = LLMContext(narrative_fitness=15.0)
    assert ctx.normalized_fitness() == 1.0

def test_normalized_fitness_clamp_lower():
    ctx = LLMContext(narrative_fitness=-3.0)
    assert ctx.normalized_fitness() == 0.0

def test_normalized_fitness_zero():
    ctx = LLMContext(narrative_fitness=0.0)
    assert ctx.normalized_fitness() == 0.0


# ── 4. from_dict 하위 호환 변환 ──────────────────────────────────
def test_from_dict_known_fields():
    d = {"series_id": "s1", "episode_idx": 3, "narrative_fitness": 6.0}
    ctx = LLMContext.from_dict(d)
    assert ctx.series_id == "s1"
    assert ctx.episode_idx == 3
    assert ctx.narrative_fitness == 6.0

def test_from_dict_extra_preserved():
    d = {"series_id": "s1", "scene_id": "sc_02", "chars": ["A", "B"]}
    ctx = LLMContext.from_dict(d)
    assert ctx.extra["scene_id"] == "sc_02"
    assert ctx.extra["chars"] == ["A", "B"]

def test_from_dict_empty():
    ctx = LLMContext.from_dict({})
    assert ctx.series_id == ""
    assert ctx.extra == {}


# ── 5. to_dict 직렬화 ────────────────────────────────────────────
def test_to_dict_roundtrip():
    ctx = LLMContext(series_id="s99", episode_idx=2, narrative_fitness=5.0,
                     extra={"k": "v"})
    d = ctx.to_dict()
    assert d["series_id"] == "s99"
    assert d["narrative_fitness"] == 5.0
    assert d["k"] == "v"


# ── 6. coerce_context dict → LLMContext ──────────────────────────
def test_coerce_context_from_dict():
    d = {"narrative_fitness": 8.0, "provider_hint": "speed"}
    ctx = coerce_context(d)
    assert isinstance(ctx, LLMContext)
    assert ctx.narrative_fitness == 8.0
    assert ctx.provider_hint == "speed"


# ── 7. coerce_context LLMContext 통과 ────────────────────────────
def test_coerce_context_passthrough():
    original = LLMContext(series_id="pass")
    result = coerce_context(original)
    assert result is original


# ── 8. coerce_context None → 기본 LLMContext ─────────────────────
def test_coerce_context_none():
    ctx = coerce_context(None)
    assert isinstance(ctx, LLMContext)
    assert ctx.series_id == ""


# ── 9. LLMResponse 기본 생성 ─────────────────────────────────────
def test_llm_response_defaults():
    resp = LLMResponse(text="hello world")
    assert resp.text == "hello world"
    assert resp.provider_id == ""
    assert resp.tokens_used == 0
    assert resp.latency_ms == 0.0
    assert resp.cost_estimate_usd == 0.0
    assert resp.fallback_used == False


# ── 10. LLMResponse 필드 설정 ────────────────────────────────────
def test_llm_response_fields():
    resp = LLMResponse(
        text="생성된 텍스트",
        provider_id="ollama",
        tokens_used=350,
        latency_ms=1234.5,
        cost_estimate_usd=0.0,
        fallback_used=True,
    )
    assert resp.provider_id == "ollama"
    assert resp.tokens_used == 350
    assert resp.fallback_used == True


# ── 11. MockLLMBridge LLMContext 수용 ────────────────────────────
def test_mock_bridge_accepts_llm_context():
    bridge = MockLLMBridge(scripted_response="test_output")
    ctx = LLMContext(series_id="s1", narrative_fitness=6.0)
    result = bridge.generate("prompt", ctx)
    assert result == "test_output"
    assert bridge.call_count == 1


# ── 12. MockLLMBridge dict context 하위 호환 ─────────────────────
def test_mock_bridge_accepts_dict_context():
    bridge = MockLLMBridge(scripted_response="compat")
    result = bridge.generate("prompt", {"scene_id": "sc1"})
    assert result == "compat"


# ── 13. MockLLMBridge context=None 허용 ──────────────────────────
def test_mock_bridge_none_context():
    bridge = MockLLMBridge(scripted_response="none_ok")
    result = bridge.generate("prompt", None)
    assert result == "none_ok"


# ── 14. is_available 기본값 ──────────────────────────────────────
def test_mock_bridge_is_available():
    bridge = MockLLMBridge()
    assert bridge.is_available() == True


# ── 15. get_provider_id ──────────────────────────────────────────
def test_mock_bridge_get_provider_id():
    bridge = MockLLMBridge()
    assert bridge.get_provider_id() == "mock"
