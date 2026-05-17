"""V411-H 테스트 — CostLedger."""
from __future__ import annotations
import pytest
from literary_system.llm_bridge.cost_ledger import CostLedger, ProviderCallRecord
from literary_system.llm_bridge.llm_context import LLMResponse


# ── 1. CostLedger 기본 생성 ─────────────────────────────────────
def test_create_cost_ledger():
    ledger = CostLedger(episode_idx=1, series_id="s1")
    assert ledger.episode_idx == 1
    assert ledger.series_id == "s1"
    assert ledger.total_calls == 0
    assert ledger.estimated_cost_usd == 0.0


# ── 2. record_call — LLMResponse로 기록 ─────────────────────────
def test_record_call():
    ledger = CostLedger(episode_idx=1)
    resp = LLMResponse(text="ok", provider_id="ollama", tokens_used=100, latency_ms=250.0)
    ledger.record_call(resp)
    assert ledger.total_calls == 1
    assert ledger.total_tokens == 100
    rec = ledger.get_record("ollama")
    assert rec.call_count == 1


# ── 3. record_call 누적 ──────────────────────────────────────────
def test_record_call_accumulate():
    ledger = CostLedger(episode_idx=1)
    for i in range(5):
        resp = LLMResponse(text="t", provider_id="haiku", tokens_used=200)
        ledger.record_call(resp)
    assert ledger.total_calls == 5
    assert ledger.total_tokens == 1000


# ── 4. record_raw 직접 입력 ──────────────────────────────────────
def test_record_raw():
    ledger = CostLedger(episode_idx=2)
    ledger.record_raw("sonnet", tokens=500, latency_ms=1200.0, success=True)
    rec = ledger.get_record("sonnet")
    assert rec.total_tokens == 500
    assert rec.success_count == 1


# ── 5. 복수 프로바이더 기록 ──────────────────────────────────────
def test_multiple_providers():
    ledger = CostLedger(episode_idx=1)
    ledger.record_raw("ollama", tokens=100)
    ledger.record_raw("haiku", tokens=200)
    assert len(ledger.provider_ids) == 2
    assert ledger.total_tokens == 300


# ── 6. ProviderCallRecord avg_latency ────────────────────────────
def test_avg_latency():
    rec = ProviderCallRecord(provider_id="p")
    rec.call_count = 2
    rec.total_latency_ms = 500.0
    assert rec.avg_latency_ms == 250.0


# ── 7. ProviderCallRecord success_rate ───────────────────────────
def test_success_rate():
    rec = ProviderCallRecord(provider_id="p", call_count=4,
                             success_count=3, failure_count=1)
    assert rec.success_rate == 0.75


# ── 8. ProviderCallRecord avg_latency 0 호출 ─────────────────────
def test_avg_latency_zero_calls():
    rec = ProviderCallRecord(provider_id="p")
    assert rec.avg_latency_ms == 0.0


# ── 9. to_dict 직렬화 ────────────────────────────────────────────
def test_to_dict():
    ledger = CostLedger(episode_idx=3, series_id="ser01")
    ledger.record_raw("ollama", tokens=50)
    d = ledger.to_dict()
    assert d["episode_idx"] == 3
    assert d["series_id"] == "ser01"
    assert "records" in d
    assert "ollama" in d["records"]


# ── 10. EpisodeMemory cost_ledger 필드 확인 ──────────────────────
def test_episode_memory_cost_ledger_field():
    from literary_system.memory.narrative_memory_store import EpisodeMemory
    import dataclasses
    fields = {f.name for f in dataclasses.fields(EpisodeMemory)}
    assert "cost_ledger" in fields
