"""
Literary OS V458 — TenantRouter + QuotaEnforcer

책임:
  - TenantRouter: region_id 기반 요청 라우팅 (ADR-016)
  - QuotaEnforcer: 월별 토큰/비용 한도 관리 + QuotaExceededError
  - TenantContextMiddleware: 요청 컨텍스트에 테넌트 정보 주입
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Optional, Tuple

from literary_system.tenant.tenant_manager import (
    TenantConfig,
    TenantInactiveError,
    TenantManager,
    TenantNotFoundError,
    TenantRegion,
)

# ── 예외 ─────────────────────────────────────────────────────────────────────

class QuotaExceededError(RuntimeError):
    """월별 토큰 또는 비용 한도 초과."""
    def __init__(self, tenant_id: str, quota_type: str, used: float, limit: float):
        self.tenant_id   = tenant_id
        self.quota_type  = quota_type
        self.used        = used
        self.limit       = limit
        super().__init__(
            f"[{tenant_id}] {quota_type} 한도 초과: {used:.2f} / {limit:.2f}"
        )


class TenantRoutingError(RuntimeError):
    """라우팅 실패 (리전 매핑 없음 등)."""


# ── 사용량 스냅샷 ─────────────────────────────────────────────────────────────

@dataclass
class UsageSnapshot:
    """테넌트 월별 사용량 스냅샷."""
    tenant_id: str
    year_month: str               # "YYYY-MM"
    tokens_used: int   = 0
    cost_usd_used: float = 0.0
    request_count: int = 0
    last_updated: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def tokens_k(self) -> float:
        return self.tokens_used / 1000

    def to_dict(self) -> dict:
        return {
            "tenant_id":     self.tenant_id,
            "year_month":    self.year_month,
            "tokens_used":   self.tokens_used,
            "cost_usd_used": round(self.cost_usd_used, 4),
            "request_count": self.request_count,
        }


# ── 할당량 강제 ───────────────────────────────────────────────────────────────

class QuotaEnforcer:
    """
    테넌트별 월별 할당량 관리.

    - check_and_record(tenant_id, tokens, cost_usd): 사용 가능 여부 확인 후 기록
    - 한도 초과 시 QuotaExceededError 발생 (호출 측에서 처리)
    - 월 교체 시 자동 리셋 (UTC 기준)
    """

    def __init__(self, tenant_manager: TenantManager):
        self._mgr   = tenant_manager
        self._usage: Dict[str, UsageSnapshot] = {}
        self._lock  = threading.Lock()

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def check_and_record(
        self,
        tenant_id: str,
        tokens: int,
        cost_usd: float,
    ) -> UsageSnapshot:
        """
        할당량 확인 + 사용량 기록.

        Raises:
            TenantNotFoundError: 테넌트 없음
            TenantInactiveError: 비활성 테넌트
            QuotaExceededError: 토큰 또는 비용 초과
        """
        cfg = self._mgr.require_active_tenant(tenant_id)
        with self._lock:
            snap = self._get_or_reset_snapshot(tenant_id)

            # 토큰 한도 검사
            projected_tokens = snap.tokens_used + tokens
            if projected_tokens > cfg.max_tokens_per_month:
                raise QuotaExceededError(
                    tenant_id, "tokens",
                    projected_tokens, cfg.max_tokens_per_month,
                )

            # 비용 한도 검사
            projected_cost = snap.cost_usd_used + cost_usd
            if projected_cost > cfg.max_cost_usd_per_month:
                raise QuotaExceededError(
                    tenant_id, "cost_usd",
                    projected_cost, cfg.max_cost_usd_per_month,
                )

            # 기록
            snap.tokens_used    += tokens
            snap.cost_usd_used  += cost_usd
            snap.request_count  += 1
            snap.last_updated    = datetime.now(timezone.utc)
            return snap

    def get_usage(self, tenant_id: str) -> Optional[UsageSnapshot]:
        with self._lock:
            return self._usage.get(tenant_id)

    def reset_usage(self, tenant_id: str) -> None:
        """강제 리셋 (관리자 도구 / 테스트 용도)."""
        with self._lock:
            ym = self._current_ym()
            self._usage[tenant_id] = UsageSnapshot(
                tenant_id=tenant_id, year_month=ym
            )

    def remaining_quota(self, tenant_id: str) -> dict:
        """남은 할당량 반환."""
        cfg  = self._mgr.require_active_tenant(tenant_id)
        with self._lock:
            snap = self._get_or_reset_snapshot(tenant_id)
        return {
            "tokens_remaining":   cfg.max_tokens_per_month  - snap.tokens_used,
            "cost_usd_remaining": cfg.max_cost_usd_per_month - snap.cost_usd_used,
            "year_month":         snap.year_month,
        }

    # ── 내부 ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _current_ym() -> str:
        now = datetime.now(timezone.utc)
        return f"{now.year}-{now.month:02d}"

    def _get_or_reset_snapshot(self, tenant_id: str) -> UsageSnapshot:
        """현재 월 스냅샷 반환, 월 변경 시 자동 리셋."""
        ym = self._current_ym()
        existing = self._usage.get(tenant_id)
        if existing is None or existing.year_month != ym:
            self._usage[tenant_id] = UsageSnapshot(
                tenant_id=tenant_id, year_month=ym
            )
        return self._usage[tenant_id]


# ── 테넌트 라우터 ─────────────────────────────────────────────────────────────

@dataclass
class RouteDecision:
    """라우팅 결정 결과."""
    tenant_id: str
    region: TenantRegion
    endpoint: str
    routing_key: str      # 로드밸런서 키 (리전+테넌트ID 해시)
    latency_hint_ms: int  # 예상 왕복 지연 (ms)

    def to_dict(self) -> dict:
        return {
            "tenant_id":      self.tenant_id,
            "region":         self.region.value,
            "endpoint":       self.endpoint,
            "routing_key":    self.routing_key,
            "latency_hint_ms": self.latency_hint_ms,
        }


class TenantRouter:
    """
    리전 기반 테넌트 요청 라우팅 (ADR-016).

    KR → kr-data.literary-os.internal  (예상 지연 20ms)
    EU → eu-data.literary-os.internal  (예상 지연 80ms)
    US → us-data.literary-os.internal  (예상 지연 120ms)

    LLM-0: 실제 네트워크 호출 없음 — 라우팅 결정만 반환.
    """

    # 리전별 엔드포인트 + 예상 지연 테이블
    _REGION_TABLE: Dict[TenantRegion, Tuple[str, int]] = {
        TenantRegion.KR: ("https://kr-api.literary-os.internal", 20),
        TenantRegion.EU: ("https://eu-api.literary-os.internal", 80),
        TenantRegion.US: ("https://us-api.literary-os.internal", 120),
    }

    def __init__(self, tenant_manager: TenantManager):
        self._mgr = tenant_manager

    def route(self, tenant_id: str) -> RouteDecision:
        """
        테넌트 요청 라우팅 결정 반환.

        Raises:
            TenantNotFoundError / TenantInactiveError
            TenantRoutingError: 알 수 없는 리전
        """
        cfg = self._mgr.require_active_tenant(tenant_id)
        if cfg.region not in self._REGION_TABLE:
            raise TenantRoutingError(f"알 수 없는 리전: {cfg.region}")

        endpoint, latency = self._REGION_TABLE[cfg.region]
        routing_key = f"{cfg.region.value}:{tenant_id}"

        return RouteDecision(
            tenant_id=tenant_id,
            region=cfg.region,
            endpoint=endpoint,
            routing_key=routing_key,
            latency_hint_ms=latency,
        )

    def bulk_route(self, tenant_ids: list) -> Dict[str, RouteDecision]:
        """다수 테넌트 일괄 라우팅."""
        results = {}
        for tid in tenant_ids:
            try:
                results[tid] = self.route(tid)
            except (TenantNotFoundError, TenantInactiveError, TenantRoutingError):
                results[tid] = None  # 라우팅 불가 표시
        return results


# ── 테넌트 컨텍스트 미들웨어 ──────────────────────────────────────────────────

@dataclass
class TenantContext:
    """요청 처리 중 사용하는 테넌트 컨텍스트."""
    tenant_id: str
    config: TenantConfig
    route: RouteDecision
    request_id: str


class TenantContextMiddleware:
    """
    요청 파이프라인에 테넌트 컨텍스트를 주입.

    사용 패턴:
        ctx = middleware.build_context(tenant_id)
        middleware.execute(ctx, handler_fn, tokens=100, cost_usd=0.002)
    """

    def __init__(
        self,
        tenant_manager: TenantManager,
        quota_enforcer: QuotaEnforcer,
        tenant_router: TenantRouter,
    ):
        self._mgr    = tenant_manager
        self._quota  = quota_enforcer
        self._router = tenant_router
        self._counter = 0
        self._lock = threading.Lock()

    def build_context(self, tenant_id: str) -> TenantContext:
        """테넌트 컨텍스트 빌드 (라우팅 포함)."""
        with self._lock:
            self._counter += 1
            req_id = f"req-{tenant_id}-{self._counter:06d}"
        cfg   = self._mgr.require_active_tenant(tenant_id)
        route = self._router.route(tenant_id)
        return TenantContext(
            tenant_id=tenant_id,
            config=cfg,
            route=route,
            request_id=req_id,
        )

    def execute(
        self,
        ctx: TenantContext,
        handler: Callable[[TenantContext], Any],
        tokens: int = 0,
        cost_usd: float = 0.0,
    ) -> Any:
        """
        할당량 확인 → 핸들러 실행.

        Raises:
            QuotaExceededError: 한도 초과 시 핸들러 미실행
        """
        self._quota.check_and_record(ctx.tenant_id, tokens, cost_usd)
        return handler(ctx)
