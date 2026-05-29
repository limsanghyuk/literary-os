"""
V441 tests -- BGEHostingGate (TCO decision)
"""
import pytest
from literary_system.rag.bge_hosting_gate import (
    BGEHostingInput, BGEHostingDecision, BGEHostingGate,
    HostingRecommendation, GPUTier, TCOBreakdown,
    API_COST_PER_1K_TOKENS, GPU_MONTHLY_USD,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def high_volume_self_host():
    """Should recommend self-hosting: high volume, GPU, privacy, capacity."""
    return BGEHostingInput(
        monthly_embedding_calls=30_000_000,
        gpu_tier=GPUTier.T4,
        api_provider="together_bge_m3",
        latency_sla_ms=100.0,
        data_privacy_required=True,
        team_ml_capacity=True,
        api_latency_p99_ms=300.0,
        self_host_latency_ms=50.0,
    )


def low_volume_use_api():
    """Should recommend API: low volume, no GPU preference, no privacy need."""
    return BGEHostingInput(
        monthly_embedding_calls=1_000,
        gpu_tier=GPUTier.T4,
        data_privacy_required=False,
        team_ml_capacity=False,
    )


# ---------------------------------------------------------------------------
# TestBGEHostingInput
# ---------------------------------------------------------------------------

class TestBGEHostingInput:
    def test_defaults(self):
        inp = BGEHostingInput(monthly_embedding_calls=50_000)
        assert inp.gpu_tier == GPUTier.T4
        assert inp.data_privacy_required is False
        assert inp.team_ml_capacity is True

    def test_custom_values(self):
        inp = BGEHostingInput(
            monthly_embedding_calls=1_000_000,
            gpu_tier=GPUTier.A10G,
            latency_sla_ms=50.0,
        )
        assert inp.gpu_tier == GPUTier.A10G
        assert inp.latency_sla_ms == 50.0


# ---------------------------------------------------------------------------
# TestTCOComputation
# ---------------------------------------------------------------------------

class TestTCOComputation:
    def _gate(self):
        return BGEHostingGate()

    def test_api_cost_scales_with_volume(self):
        g = self._gate()
        low = BGEHostingInput(monthly_embedding_calls=10_000)
        high = BGEHostingInput(monthly_embedding_calls=100_000)
        tco_low = g._compute_tco(low)
        tco_high = g._compute_tco(high)
        assert tco_high.api_cost_usd > tco_low.api_cost_usd

    def test_self_host_cost_includes_ops(self):
        g = self._gate()
        inp = BGEHostingInput(monthly_embedding_calls=1_000, ops_monthly_usd=500.0, gpu_tier=GPUTier.T4)
        tco = g._compute_tco(inp)
        assert tco.self_host_cost_usd > 500.0

    def test_savings_positive_at_high_volume(self):
        g = self._gate()
        inp = high_volume_self_host()
        tco = g._compute_tco(inp)
        assert tco.savings_usd > 0

    def test_savings_negative_at_low_volume(self):
        g = self._gate()
        inp = BGEHostingInput(monthly_embedding_calls=100)
        tco = g._compute_tco(inp)
        assert tco.savings_usd < 0

    def test_breakeven_positive(self):
        g = self._gate()
        tco = g._compute_tco(BGEHostingInput(monthly_embedding_calls=1_000_000))
        assert tco.breakeven_calls > 0


# ---------------------------------------------------------------------------
# TestBlockers
# ---------------------------------------------------------------------------

class TestBlockers:
    def _gate(self):
        return BGEHostingGate()

    def test_no_gpu_is_blocker(self):
        g = self._gate()
        inp = BGEHostingInput(monthly_embedding_calls=30_000_000, gpu_tier=GPUTier.NONE)
        blockers = g._find_blockers(inp)
        assert len(blockers) > 0
        assert any("GPU" in b for b in blockers)

    def test_no_ml_capacity_is_blocker(self):
        g = self._gate()
        inp = BGEHostingInput(monthly_embedding_calls=30_000_000, team_ml_capacity=False)
        blockers = g._find_blockers(inp)
        assert any("capacity" in b.lower() for b in blockers)

    def test_no_blockers_with_valid_input(self):
        g = self._gate()
        inp = BGEHostingInput(monthly_embedding_calls=1_000_000, gpu_tier=GPUTier.T4, team_ml_capacity=True)
        assert g._find_blockers(inp) == []


# ---------------------------------------------------------------------------
# TestBGEHostingGate
# ---------------------------------------------------------------------------

class TestBGEHostingGate:
    def _gate(self):
        return BGEHostingGate()

    def test_high_volume_recommends_self_host(self):
        g = self._gate()
        dec = g.evaluate(high_volume_self_host())
        assert dec.recommendation == HostingRecommendation.SELF_HOST

    def test_no_gpu_forces_use_api(self):
        g = self._gate()
        inp = BGEHostingInput(monthly_embedding_calls=30_000_000, gpu_tier=GPUTier.NONE)
        dec = g.evaluate(inp)
        assert dec.recommendation == HostingRecommendation.USE_API
        assert dec.is_blocked

    def test_low_volume_recommends_api(self):
        g = self._gate()
        dec = g.evaluate(low_volume_use_api())
        assert dec.recommendation == HostingRecommendation.USE_API

    def test_score_range(self):
        g = self._gate()
        for inp in [high_volume_self_host(), low_volume_use_api()]:
            dec = g.evaluate(inp)
            assert 0.0 <= dec.score <= 1.0

    def test_rationale_non_empty(self):
        g = self._gate()
        dec = g.evaluate(high_volume_self_host())
        assert len(dec.rationale) >= 5

    def test_to_dict(self):
        g = self._gate()
        dec = g.evaluate(high_volume_self_host())
        d = dec.to_dict()
        assert "recommendation" in d
        assert "tco" in d
        assert "rationale" in d
        assert "score" in d

    def test_privacy_required_boosts_score(self):
        g = self._gate()
        base = BGEHostingInput(monthly_embedding_calls=1_000_000, gpu_tier=GPUTier.T4)
        priv = BGEHostingInput(monthly_embedding_calls=1_000_000, gpu_tier=GPUTier.T4, data_privacy_required=True)
        dec_base = g.evaluate(base)
        dec_priv = g.evaluate(priv)
        assert dec_priv.score > dec_base.score

    def test_local_gpu_zero_cost(self):
        g = self._gate()
        inp = BGEHostingInput(
            monthly_embedding_calls=1_000_000,
            gpu_tier=GPUTier.LOCAL,
            ops_monthly_usd=0.0,
        )
        tco = g._compute_tco(inp)
        assert tco.self_host_cost_usd == 0.0

    def test_borderline_case(self):
        g = self._gate()
        # Medium volume: likely borderline
        inp = BGEHostingInput(
            monthly_embedding_calls=500_000,
            gpu_tier=GPUTier.T4,
            data_privacy_required=False,
            team_ml_capacity=True,
        )
        dec = g.evaluate(inp)
        assert dec.recommendation in (
            HostingRecommendation.BORDERLINE,
            HostingRecommendation.USE_API,
            HostingRecommendation.SELF_HOST,
        )

    def test_is_self_host_property(self):
        g = self._gate()
        dec = g.evaluate(high_volume_self_host())
        assert dec.is_self_host == (dec.recommendation == HostingRecommendation.SELF_HOST)
