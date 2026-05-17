"""
V454 — LiveCostMeter
per-tenant 실시간 LLM 비용 추적기.

기능:
  - 호출당 USD 비용 누적 (provider별 가격 테이블)
  - KRW 환산 (기본 환율 설정 가능)
  - 월별 예산 상한 + 초과 알림
  - tenant 격리
LLM-0 원칙: 외부 의존 없음, 순수 Python.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ---------------------------------------------------------------------------
# Provider 가격 테이블 (USD/1K tokens, blended input+output)
# ---------------------------------------------------------------------------
_PRICING_TABLE: Dict[str, float] = {
    # Anthropic
    "claude-opus-4":        0.045000,
    "claude-opus-3":        0.045000,
    "claude-opus":          0.045000,
    "claude-sonnet-4":      0.009000,
    "claude-sonnet-3-7":    0.009000,
    "claude-sonnet-3-5":    0.009000,
    "claude-sonnet":        0.009000,
    "claude-haiku-4":       0.000750,
    "claude-haiku-3-5":     0.000750,
    "claude-haiku":         0.000750,
    # OpenAI
    "gpt-4o":               0.006250,
    "gpt-4o-mini":          0.000375,
    "gpt-4-turbo":          0.013000,
    "gpt-4":                0.048000,
    "gpt-3.5-turbo":        0.001000,
    "o1":                   0.090000,
    "o1-mini":              0.004800,
    "o3-mini":              0.003300,
    # Local / OSS
    "ollama":               0.000000,
    "local":                0.000000,
    "mock":                 0.000000,
}
_DEFAULT_COST_PER_1K: float = 0.001000


def lookup_cost_per_1k(provider_id: str) -> float:
    """provider_id → USD/1K tokens."""
    pid = provider_id.lower().strip()
    if pid in _PRICING_TABLE:
        return _PRICING_TABLE[pid]
    for kw in ("mock", "local", "ollama", "test", "dummy", "stub"):
        if kw in pid:
            return 0.0
    for key in sorted(_PRICING_TABLE, key=len, reverse=True):
        if key in pid:
            return _PRICING_TABLE[key]
    return _DEFAULT_COST_PER_1K


# ---------------------------------------------------------------------------
# 단일 호출 레코드
# ---------------------------------------------------------------------------

@dataclass
class CostRecord:
    """단일 LLM 호출 비용 레코드."""
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    cost_usd: float
    latency_ms: float
    timestamp_ms: float = field(default_factory=lambda: time.monotonic() * 1000)
    call_id: str = ""
    tenant_id: str = "default"


# ---------------------------------------------------------------------------
# per-tenant 집계
# ---------------------------------------------------------------------------

@dataclass
class TenantCostSummary:
    """테넌트별 비용 집계."""
    tenant_id: str
    total_calls: int = 0
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_cost_usd: float = 0.0
    total_latency_ms: float = 0.0
    monthly_budget_usd: float = 0.0   # 0 = 무제한
    monthly_spent_usd: float = 0.0
    budget_alert_sent: bool = False
    records: List[CostRecord] = field(default_factory=list)

    @property
    def total_tokens(self) -> int:
        return self.total_input_tokens + self.total_output_tokens

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.total_calls if self.total_calls else 0.0

    @property
    def is_over_budget(self) -> bool:
        if self.monthly_budget_usd <= 0:
            return False
        return self.monthly_spent_usd >= self.monthly_budget_usd

    @property
    def budget_remaining_usd(self) -> float:
        if self.monthly_budget_usd <= 0:
            return float("inf")
        return max(0.0, self.monthly_budget_usd - self.monthly_spent_usd)


# ---------------------------------------------------------------------------
# LiveCostMeter
# ---------------------------------------------------------------------------

class LiveCostMeter:
    """
    V454 — per-tenant 실시간 LLM 비용 추적기.

    Parameters
    ----------
    usd_to_krw : float
        USD→KRW 환율 (기본 1350).
    budget_alert_fn : Callable, optional
        예산 초과 시 호출되는 콜백 (tenant_id, spent, budget) → None.
    """

    DEFAULT_USD_TO_KRW: float = 1350.0

    def __init__(
        self,
        usd_to_krw: float = DEFAULT_USD_TO_KRW,
        budget_alert_fn: Optional[Callable[[str, float, float], None]] = None,
    ) -> None:
        self._usd_to_krw = usd_to_krw
        self._budget_alert_fn = budget_alert_fn
        self._tenants: Dict[str, TenantCostSummary] = {}

    # ------------------------------------------------------------------
    # 핵심 API
    # ------------------------------------------------------------------

    def record_call(
        self,
        tenant_id: str,
        provider: str,
        input_tokens: int,
        output_tokens: int,
        *,
        cost_usd: Optional[float] = None,
        latency_ms: float = 0.0,
        call_id: str = "",
        model: str = "",
    ) -> CostRecord:
        """
        LLM 호출 비용 기록.

        cost_usd 미지정 시 provider/model 기반 자동 계산.
        """
        if cost_usd is None:
            model_key = model or provider
            rate = lookup_cost_per_1k(model_key)
            cost_usd = round((input_tokens + output_tokens) / 1000.0 * rate, 8)

        record = CostRecord(
            provider=provider,
            model=model or provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            call_id=call_id,
            tenant_id=tenant_id,
        )

        summary = self._get_or_create(tenant_id)
        summary.total_calls += 1
        summary.total_input_tokens += input_tokens
        summary.total_output_tokens += output_tokens
        summary.total_cost_usd = round(summary.total_cost_usd + cost_usd, 8)
        summary.monthly_spent_usd = round(summary.monthly_spent_usd + cost_usd, 8)
        summary.total_latency_ms += latency_ms
        summary.records.append(record)

        # 예산 초과 알림
        self._check_budget_alert(summary)

        return record

    def record_from_response(
        self,
        tenant_id: str,
        response,  # RealLLMResponse 호환 객체
    ) -> Optional[CostRecord]:
        """RealLLMResponse 객체에서 직접 비용 기록."""
        if response is None:
            return None
        provider = getattr(response, "provider", "unknown")
        input_tokens = getattr(response, "input_tokens", 0)
        output_tokens = getattr(response, "output_tokens", 0)
        cost_usd = getattr(response, "cost_usd", None)
        latency_ms = getattr(response, "latency_ms", 0.0)
        call_id = getattr(response, "call_id", "")
        return self.record_call(
            tenant_id=tenant_id,
            provider=provider,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=cost_usd,
            latency_ms=latency_ms,
            call_id=call_id,
        )

    def get_summary(self, tenant_id: str) -> TenantCostSummary:
        """테넌트 비용 요약 반환."""
        return self._get_or_create(tenant_id)

    def get_cost_usd(self, tenant_id: str) -> float:
        """테넌트 누적 비용 (USD)."""
        return self._get_or_create(tenant_id).total_cost_usd

    def get_cost_krw(self, tenant_id: str, usd_to_krw: Optional[float] = None) -> float:
        """테넌트 누적 비용 (KRW)."""
        rate = usd_to_krw if usd_to_krw is not None else self._usd_to_krw
        return round(self.get_cost_usd(tenant_id) * rate, 2)

    def get_monthly_spent(self, tenant_id: str) -> float:
        """당월 지출 (USD)."""
        return self._get_or_create(tenant_id).monthly_spent_usd

    def set_monthly_budget(self, tenant_id: str, budget_usd: float) -> None:
        """월 예산 상한 설정. 0 = 무제한."""
        self._get_or_create(tenant_id).monthly_budget_usd = max(0.0, budget_usd)

    def is_over_budget(self, tenant_id: str) -> bool:
        """예산 초과 여부."""
        return self._get_or_create(tenant_id).is_over_budget

    def budget_remaining(self, tenant_id: str) -> float:
        """남은 예산 (USD). 무제한이면 inf."""
        return self._get_or_create(tenant_id).budget_remaining_usd

    def reset_monthly(self, tenant_id: str) -> None:
        """월별 지출 초기화 (새 달 시작)."""
        summary = self._get_or_create(tenant_id)
        summary.monthly_spent_usd = 0.0
        summary.budget_alert_sent = False

    def reset_tenant(self, tenant_id: str) -> None:
        """테넌트 전체 초기화."""
        if tenant_id in self._tenants:
            del self._tenants[tenant_id]

    def reset_all(self) -> None:
        """전체 초기화."""
        self._tenants.clear()

    def list_tenants(self) -> List[str]:
        """등록된 테넌트 ID 목록."""
        return list(self._tenants.keys())

    def global_stats(self) -> Dict[str, Any]:
        """전체 집계 통계."""
        total_calls = sum(s.total_calls for s in self._tenants.values())
        total_cost = sum(s.total_cost_usd for s in self._tenants.values())
        return {
            "tenant_count": len(self._tenants),
            "total_calls": total_calls,
            "total_cost_usd": round(total_cost, 8),
            "total_cost_krw": round(total_cost * self._usd_to_krw, 2),
            "usd_to_krw": self._usd_to_krw,
        }

    def tenant_stats(self, tenant_id: str) -> Dict[str, Any]:
        """테넌트별 상세 통계."""
        s = self._get_or_create(tenant_id)
        return {
            "tenant_id": tenant_id,
            "total_calls": s.total_calls,
            "total_input_tokens": s.total_input_tokens,
            "total_output_tokens": s.total_output_tokens,
            "total_tokens": s.total_tokens,
            "total_cost_usd": s.total_cost_usd,
            "total_cost_krw": round(s.total_cost_usd * self._usd_to_krw, 2),
            "monthly_spent_usd": s.monthly_spent_usd,
            "monthly_budget_usd": s.monthly_budget_usd,
            "budget_remaining_usd": s.budget_remaining_usd,
            "is_over_budget": s.is_over_budget,
            "avg_latency_ms": round(s.avg_latency_ms, 2),
        }

    # ------------------------------------------------------------------
    # 내부
    # ------------------------------------------------------------------

    def _get_or_create(self, tenant_id: str) -> TenantCostSummary:
        if tenant_id not in self._tenants:
            self._tenants[tenant_id] = TenantCostSummary(tenant_id=tenant_id)
        return self._tenants[tenant_id]

    def _check_budget_alert(self, summary: TenantCostSummary) -> None:
        if (
            summary.monthly_budget_usd > 0
            and summary.monthly_spent_usd >= summary.monthly_budget_usd
            and not summary.budget_alert_sent
        ):
            summary.budget_alert_sent = True
            if self._budget_alert_fn:
                try:
                    self._budget_alert_fn(
                        summary.tenant_id,
                        summary.monthly_spent_usd,
                        summary.monthly_budget_usd,
                    )
                except Exception:
                    pass  # 알림 실패는 무시
