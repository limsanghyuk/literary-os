"""
V441 -- BGE-M3 Self-Hosting Decision Gate (TCO)

Evaluates whether self-hosting BGE-M3 (1024-dim embedding model) is
cost-effective vs. API-based embedding (Together.ai / OpenAI).

Decision axes:
  1. monthly_embedding_calls: volume-based breakeven analysis
  2. gpu_available: hardware feasibility
  3. latency_sla_ms: latency requirement vs. API round-trip
  4. data_privacy_required: data residency constraints
  5. team_ml_capacity: ops capacity for model serving

TCO model:
  API cost = monthly_calls * cost_per_call_usd
  Self-host cost = gpu_monthly_usd + ops_cost_usd (flat)
  Breakeven = self_host_total / api_cost_per_call

Output: BGEHostingDecision with recommendation + rationale
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class HostingRecommendation(str, Enum):
    SELF_HOST   = "self_host"
    USE_API     = "use_api"
    BORDERLINE  = "borderline"


class GPUTier(str, Enum):
    NONE     = "none"
    T4       = "t4"       # GCP/AWS ~$0.40/hr
    A10G     = "a10g"     # ~$1.01/hr
    A100_40  = "a100_40"  # ~$2.50/hr
    LOCAL    = "local"    # no cloud cost


# ---------------------------------------------------------------------------
# Cost table
# ---------------------------------------------------------------------------

# API cost per 1K tokens (embedding)
API_COST_PER_1K_TOKENS: Dict[str, float] = {
    "together_bge_m3":  0.00008,   # Together.ai BGE-M3 $0.00008/1K tokens
    "openai_ada_002":   0.00010,   # OpenAI text-embedding-ada-002
    "openai_3_small":   0.00002,   # OpenAI text-embedding-3-small
    "cohere_embed_v3":  0.00010,   # Cohere Embed v3
    "mock":             0.00005,   # for testing
}

# GPU monthly cost (730 hrs)
GPU_MONTHLY_USD: Dict[str, float] = {
    "none":    0.0,
    "t4":      292.0,   # ~$0.40/hr * 730
    "a10g":    737.3,   # ~$1.01/hr * 730
    "a100_40": 1825.0,  # ~$2.50/hr * 730
    "local":   0.0,     # amortized hardware excluded
}

# Avg tokens per embedding call
AVG_TOKENS_PER_CALL = 256


# ---------------------------------------------------------------------------
# Input / Output dataclasses
# ---------------------------------------------------------------------------

@dataclass
class BGEHostingInput:
    """Input parameters for the TCO decision gate."""
    monthly_embedding_calls: int
    gpu_tier:               GPUTier = GPUTier.T4
    api_provider:           str     = "together_bge_m3"
    latency_sla_ms:         float   = 500.0
    data_privacy_required:  bool    = False
    team_ml_capacity:       bool    = True
    ops_monthly_usd:        float   = 200.0   # eng ops overhead
    api_latency_p99_ms:     float   = 300.0   # typical Together.ai
    self_host_latency_ms:   float   = 50.0    # local GPU inference
    tokens_per_call:        int     = AVG_TOKENS_PER_CALL


@dataclass
class TCOBreakdown:
    """Monthly cost breakdown."""
    api_cost_usd:       float
    self_host_cost_usd: float
    breakeven_calls:    int
    savings_usd:        float   # positive = self-host cheaper


@dataclass
class BGEHostingDecision:
    """Output of the BGE hosting decision gate."""
    recommendation:  HostingRecommendation
    tco:             TCOBreakdown
    rationale:       List[str]
    score:           float      # 0.0 (strong API) to 1.0 (strong self-host)
    blocking_issues: List[str]  # hardware / capacity blockers

    @property
    def is_self_host(self) -> bool:
        return self.recommendation == HostingRecommendation.SELF_HOST

    @property
    def is_blocked(self) -> bool:
        return len(self.blocking_issues) > 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation": self.recommendation.value,
            "score": round(self.score, 3),
            "tco": {
                "api_cost_usd": round(self.tco.api_cost_usd, 2),
                "self_host_cost_usd": round(self.tco.self_host_cost_usd, 2),
                "breakeven_calls": self.tco.breakeven_calls,
                "savings_usd": round(self.tco.savings_usd, 2),
            },
            "rationale": self.rationale,
            "blocking_issues": self.blocking_issues,
        }


# ---------------------------------------------------------------------------
# BGEHostingGate
# ---------------------------------------------------------------------------

class BGEHostingGate:
    """
    Decision gate: should we self-host BGE-M3?

    Scoring (each axis contributes 0.2):
      1. cost_axis:    self_host_cost < api_cost -> +0.2
      2. latency_axis: self_host latency meets SLA, api does not -> +0.2
      3. privacy_axis: data_privacy_required -> +0.2
      4. volume_axis:  calls > breakeven -> +0.2
      5. capacity_axis: team_ml_capacity -> +0.2

    Recommendation thresholds:
      score >= 0.6  -> SELF_HOST
      score <= 0.3  -> USE_API
      otherwise     -> BORDERLINE

    Blocking issues (prevent SELF_HOST regardless of score):
      - GPU tier = NONE and not local
      - team_ml_capacity = False
    """

    SELF_HOST_THRESHOLD  = 0.6
    USE_API_THRESHOLD    = 0.3

    def evaluate(self, inp: BGEHostingInput) -> BGEHostingDecision:
        tco = self._compute_tco(inp)
        blocking = self._find_blockers(inp)
        score, rationale = self._score(inp, tco)

        if blocking:
            rec = HostingRecommendation.USE_API
        elif score >= self.SELF_HOST_THRESHOLD:
            rec = HostingRecommendation.SELF_HOST
        elif score <= self.USE_API_THRESHOLD:
            rec = HostingRecommendation.USE_API
        else:
            rec = HostingRecommendation.BORDERLINE

        return BGEHostingDecision(
            recommendation=rec,
            tco=tco,
            rationale=rationale,
            score=score,
            blocking_issues=blocking,
        )

    def _compute_tco(self, inp: BGEHostingInput) -> TCOBreakdown:
        cost_per_1k = API_COST_PER_1K_TOKENS.get(inp.api_provider, 0.0001)
        tokens_per_month = inp.monthly_embedding_calls * inp.tokens_per_call
        api_cost = (tokens_per_month / 1000.0) * cost_per_1k

        gpu_cost = GPU_MONTHLY_USD.get(inp.gpu_tier.value, 0.0)
        self_host_cost = gpu_cost + inp.ops_monthly_usd

        if api_cost > 0:
            breakeven = int(self_host_cost / (cost_per_1k * inp.tokens_per_call / 1000.0))
        else:
            breakeven = 0

        return TCOBreakdown(
            api_cost_usd=api_cost,
            self_host_cost_usd=self_host_cost,
            breakeven_calls=breakeven,
            savings_usd=api_cost - self_host_cost,
        )

    def _find_blockers(self, inp: BGEHostingInput) -> List[str]:
        blockers = []
        if inp.gpu_tier == GPUTier.NONE:
            blockers.append("No GPU available -- self-hosting not feasible")
        if not inp.team_ml_capacity:
            blockers.append("Insufficient team ML capacity for model serving")
        return blockers

    def _score(self, inp: BGEHostingInput, tco: TCOBreakdown):
        score = 0.0
        rationale = []

        # 1. cost axis
        if tco.savings_usd > 0:
            score += 0.2
            rationale.append(
                "Cost: self-hosting saves $" + format(tco.savings_usd, ".2f") + "/mo"
            )
        else:
            rationale.append(
                "Cost: API is cheaper by $" + format(-tco.savings_usd, ".2f") + "/mo"
            )

        # 2. latency axis
        api_meets_sla = inp.api_latency_p99_ms <= inp.latency_sla_ms
        self_meets_sla = inp.self_host_latency_ms <= inp.latency_sla_ms
        if self_meets_sla and not api_meets_sla:
            score += 0.2
            rationale.append("Latency: self-host meets SLA, API does not")
        elif api_meets_sla:
            rationale.append("Latency: API meets SLA (" + str(inp.api_latency_p99_ms) + "ms)")
        else:
            rationale.append("Latency: neither meets SLA -- investigate")

        # 3. privacy axis
        if inp.data_privacy_required:
            score += 0.2
            rationale.append("Privacy: data residency requirement favors self-hosting")
        else:
            rationale.append("Privacy: no data residency constraint")

        # 4. volume axis
        if inp.monthly_embedding_calls >= tco.breakeven_calls > 0:
            score += 0.2
            rationale.append(
                "Volume: " + str(inp.monthly_embedding_calls) +                 " calls/mo exceeds breakeven (" + str(tco.breakeven_calls) + ")"
            )
        else:
            rationale.append(
                "Volume: below breakeven (" + str(tco.breakeven_calls) + " calls needed)"
            )

        # 5. capacity axis
        if inp.team_ml_capacity:
            score += 0.2
            rationale.append("Capacity: team has ML ops capability")
        else:
            rationale.append("Capacity: team lacks ML ops capability (blocker)")

        return round(score, 3), rationale
