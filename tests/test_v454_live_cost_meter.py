"""
V454 — LiveCostMeter 테스트
LLM-0 원칙: 외부 의존 없음, 순수 Python.
"""
import pytest
from literary_system.cost_cache.live_cost_meter import (
    LiveCostMeter,
    TenantCostSummary,
    CostRecord,
    lookup_cost_per_1k,
    _PRICING_TABLE,
)


# ---------------------------------------------------------------------------
# 가격 테이블
# ---------------------------------------------------------------------------

class TestPricingTable:
    def test_claude_haiku_price(self):
        assert lookup_cost_per_1k("claude-haiku") == 0.000750

    def test_gpt4o_mini_price(self):
        assert lookup_cost_per_1k("gpt-4o-mini") == 0.000375

    def test_ollama_is_free(self):
        assert lookup_cost_per_1k("ollama") == 0.0

    def test_local_is_free(self):
        assert lookup_cost_per_1k("local") == 0.0

    def test_mock_is_free(self):
        assert lookup_cost_per_1k("mock-llm") == 0.0

    def test_unknown_has_default(self):
        price = lookup_cost_per_1k("unknown-model-xyz")
        assert price > 0.0

    def test_partial_match_claude_sonnet(self):
        price = lookup_cost_per_1k("claude-sonnet-4-custom")
        assert price == 0.009000

    def test_case_insensitive(self):
        assert lookup_cost_per_1k("OLLAMA") == 0.0
        assert lookup_cost_per_1k("GPT-4O") == lookup_cost_per_1k("gpt-4o")

    def test_stub_is_free(self):
        assert lookup_cost_per_1k("stub-provider") == 0.0

    def test_test_keyword_is_free(self):
        assert lookup_cost_per_1k("test-model") == 0.0


# ---------------------------------------------------------------------------
# CostRecord
# ---------------------------------------------------------------------------

class TestCostRecord:
    def test_creation(self):
        rec = CostRecord(
            provider="claude",
            model="claude-haiku",
            input_tokens=100,
            output_tokens=50,
            cost_usd=0.001,
            latency_ms=80.0,
        )
        assert rec.provider == "claude"
        assert rec.input_tokens == 100
        assert rec.output_tokens == 50

    def test_timestamp_set(self):
        rec = CostRecord("p", "m", 1, 1, 0.0, 0.0)
        assert rec.timestamp_ms > 0


# ---------------------------------------------------------------------------
# TenantCostSummary
# ---------------------------------------------------------------------------

class TestTenantCostSummary:
    def test_defaults(self):
        s = TenantCostSummary(tenant_id="t1")
        assert s.total_calls == 0
        assert s.total_cost_usd == 0.0
        assert s.is_over_budget is False

    def test_total_tokens(self):
        s = TenantCostSummary(tenant_id="t1")
        s.total_input_tokens = 300
        s.total_output_tokens = 200
        assert s.total_tokens == 500

    def test_avg_latency_zero_calls(self):
        s = TenantCostSummary(tenant_id="t1")
        assert s.avg_latency_ms == 0.0

    def test_budget_remaining_no_limit(self):
        s = TenantCostSummary(tenant_id="t1")
        assert s.budget_remaining_usd == float("inf")

    def test_budget_remaining_with_limit(self):
        s = TenantCostSummary(tenant_id="t1")
        s.monthly_budget_usd = 10.0
        s.monthly_spent_usd = 3.0
        assert abs(s.budget_remaining_usd - 7.0) < 1e-6

    def test_is_over_budget_false(self):
        s = TenantCostSummary(tenant_id="t1")
        s.monthly_budget_usd = 10.0
        s.monthly_spent_usd = 5.0
        assert s.is_over_budget is False

    def test_is_over_budget_true(self):
        s = TenantCostSummary(tenant_id="t1")
        s.monthly_budget_usd = 5.0
        s.monthly_spent_usd = 5.0
        assert s.is_over_budget is True

    def test_is_over_budget_zero_limit(self):
        # 0 = 무제한
        s = TenantCostSummary(tenant_id="t1")
        s.monthly_budget_usd = 0.0
        s.monthly_spent_usd = 99999.0
        assert s.is_over_budget is False


# ---------------------------------------------------------------------------
# LiveCostMeter — 기본 동작
# ---------------------------------------------------------------------------

class TestLiveCostMeterBasic:
    def test_record_call_returns_record(self):
        meter = LiveCostMeter()
        rec = meter.record_call("t1", "gpt-4o-mini", 500, 200)
        assert isinstance(rec, CostRecord)
        assert rec.input_tokens == 500
        assert rec.output_tokens == 200

    def test_cost_auto_calculated(self):
        meter = LiveCostMeter()
        rec = meter.record_call("t1", "gpt-4o-mini", 1000, 0)
        # 0.000375/1k * 1000 = 0.000375
        assert abs(rec.cost_usd - 0.000375) < 1e-7

    def test_explicit_cost_used(self):
        meter = LiveCostMeter()
        rec = meter.record_call("t1", "gpt-4o-mini", 100, 100, cost_usd=0.99)
        assert rec.cost_usd == 0.99

    def test_tenant_isolation(self):
        meter = LiveCostMeter()
        meter.record_call("t1", "gpt-4o-mini", 1000, 0)
        meter.record_call("t2", "gpt-4o-mini", 1000, 0)
        assert meter.get_cost_usd("t1") != meter.get_cost_usd("t3")
        assert meter.get_cost_usd("t1") == meter.get_cost_usd("t2")  # same provider/tokens

    def test_cumulative_cost(self):
        meter = LiveCostMeter()
        meter.record_call("t1", "mock", 100, 100, cost_usd=1.0)
        meter.record_call("t1", "mock", 100, 100, cost_usd=2.0)
        assert abs(meter.get_cost_usd("t1") - 3.0) < 1e-7

    def test_latency_tracked(self):
        meter = LiveCostMeter()
        meter.record_call("t1", "mock", 0, 0, latency_ms=150.0)
        s = meter.get_summary("t1")
        assert abs(s.avg_latency_ms - 150.0) < 0.1

    def test_new_tenant_created(self):
        meter = LiveCostMeter()
        s = meter.get_summary("brand_new")
        assert isinstance(s, TenantCostSummary)
        assert s.total_calls == 0


# ---------------------------------------------------------------------------
# LiveCostMeter — KRW 환산
# ---------------------------------------------------------------------------

class TestLiveCostMeterKRW:
    def test_krw_default_rate(self):
        meter = LiveCostMeter(usd_to_krw=1350.0)
        meter.record_call("t1", "mock", 0, 0, cost_usd=1.0)
        assert abs(meter.get_cost_krw("t1") - 1350.0) < 0.01

    def test_krw_custom_rate(self):
        meter = LiveCostMeter(usd_to_krw=1300.0)
        meter.record_call("t1", "mock", 0, 0, cost_usd=1.0)
        assert abs(meter.get_cost_krw("t1") - 1300.0) < 0.01

    def test_krw_override_rate(self):
        meter = LiveCostMeter(usd_to_krw=1350.0)
        meter.record_call("t1", "mock", 0, 0, cost_usd=1.0)
        # 호출 시 환율 오버라이드
        assert abs(meter.get_cost_krw("t1", usd_to_krw=1400.0) - 1400.0) < 0.01

    def test_zero_cost_krw(self):
        meter = LiveCostMeter()
        assert meter.get_cost_krw("empty_tenant") == 0.0


# ---------------------------------------------------------------------------
# LiveCostMeter — 예산 관리
# ---------------------------------------------------------------------------

class TestLiveCostMeterBudget:
    def test_set_monthly_budget(self):
        meter = LiveCostMeter()
        meter.set_monthly_budget("t1", 5.0)
        assert meter.get_summary("t1").monthly_budget_usd == 5.0

    def test_not_over_budget_initially(self):
        meter = LiveCostMeter()
        meter.set_monthly_budget("t1", 5.0)
        assert meter.is_over_budget("t1") is False

    def test_over_budget_after_spend(self):
        meter = LiveCostMeter()
        meter.set_monthly_budget("t1", 1.0)
        meter.record_call("t1", "mock", 0, 0, cost_usd=1.5)
        assert meter.is_over_budget("t1") is True

    def test_budget_remaining(self):
        meter = LiveCostMeter()
        meter.set_monthly_budget("t1", 10.0)
        meter.record_call("t1", "mock", 0, 0, cost_usd=3.0)
        assert abs(meter.budget_remaining("t1") - 7.0) < 1e-6

    def test_budget_alert_fn_called(self):
        alerts = []
        def on_alert(tenant_id, spent, budget):
            alerts.append((tenant_id, spent, budget))

        meter = LiveCostMeter(budget_alert_fn=on_alert)
        meter.set_monthly_budget("t1", 1.0)
        meter.record_call("t1", "mock", 0, 0, cost_usd=1.5)
        assert len(alerts) == 1
        assert alerts[0][0] == "t1"

    def test_budget_alert_fn_called_once(self):
        """초과 알림은 한 번만 발송."""
        alerts = []
        meter = LiveCostMeter(budget_alert_fn=lambda t, s, b: alerts.append(1))
        meter.set_monthly_budget("t1", 1.0)
        meter.record_call("t1", "mock", 0, 0, cost_usd=2.0)
        meter.record_call("t1", "mock", 0, 0, cost_usd=2.0)
        assert len(alerts) == 1

    def test_reset_monthly(self):
        meter = LiveCostMeter()
        meter.set_monthly_budget("t1", 1.0)
        meter.record_call("t1", "mock", 0, 0, cost_usd=2.0)
        assert meter.is_over_budget("t1") is True
        meter.reset_monthly("t1")
        assert meter.is_over_budget("t1") is False
        assert meter.get_monthly_spent("t1") == 0.0

    def test_no_budget_set_infinite_remaining(self):
        meter = LiveCostMeter()
        remaining = meter.budget_remaining("t1")
        assert remaining == float("inf")

    def test_budget_zero_means_unlimited(self):
        meter = LiveCostMeter()
        meter.set_monthly_budget("t1", 0.0)
        meter.record_call("t1", "mock", 0, 0, cost_usd=99999.0)
        assert meter.is_over_budget("t1") is False


# ---------------------------------------------------------------------------
# LiveCostMeter — record_from_response
# ---------------------------------------------------------------------------

class TestRecordFromResponse:
    def test_from_response_object(self):
        class MockResp:
            provider = "claude"
            input_tokens = 200
            output_tokens = 100
            cost_usd = 0.005
            latency_ms = 95.0
            call_id = "abc123"

        meter = LiveCostMeter()
        rec = meter.record_from_response("t1", MockResp())
        assert rec is not None
        assert rec.cost_usd == 0.005

    def test_from_none_response(self):
        meter = LiveCostMeter()
        result = meter.record_from_response("t1", None)
        assert result is None


# ---------------------------------------------------------------------------
# LiveCostMeter — 통계 / 관리
# ---------------------------------------------------------------------------

class TestLiveCostMeterStats:
    def test_global_stats_empty(self):
        meter = LiveCostMeter()
        stats = meter.global_stats()
        assert stats["tenant_count"] == 0
        assert stats["total_calls"] == 0

    def test_global_stats_with_tenants(self):
        meter = LiveCostMeter()
        meter.record_call("t1", "mock", 0, 0, cost_usd=1.0)
        meter.record_call("t2", "mock", 0, 0, cost_usd=2.0)
        stats = meter.global_stats()
        assert stats["tenant_count"] == 2
        assert stats["total_calls"] == 2
        assert abs(stats["total_cost_usd"] - 3.0) < 1e-7

    def test_tenant_stats(self):
        meter = LiveCostMeter(usd_to_krw=1350.0)
        meter.record_call("t1", "mock", 100, 200, cost_usd=0.5, latency_ms=100.0)
        ts = meter.tenant_stats("t1")
        assert ts["total_calls"] == 1
        assert ts["total_input_tokens"] == 100
        assert ts["total_output_tokens"] == 200
        assert abs(ts["total_cost_usd"] - 0.5) < 1e-7
        assert abs(ts["total_cost_krw"] - 675.0) < 0.1

    def test_list_tenants(self):
        meter = LiveCostMeter()
        meter.record_call("a", "mock", 0, 0)
        meter.record_call("b", "mock", 0, 0)
        tenants = meter.list_tenants()
        assert "a" in tenants
        assert "b" in tenants

    def test_reset_tenant(self):
        meter = LiveCostMeter()
        meter.record_call("t1", "mock", 0, 0, cost_usd=1.0)
        meter.reset_tenant("t1")
        assert meter.get_cost_usd("t1") == 0.0

    def test_reset_all(self):
        meter = LiveCostMeter()
        meter.record_call("t1", "mock", 0, 0, cost_usd=1.0)
        meter.record_call("t2", "mock", 0, 0, cost_usd=2.0)
        meter.reset_all()
        assert meter.list_tenants() == []
