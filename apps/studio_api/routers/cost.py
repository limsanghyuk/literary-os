"""
V429: 비용 원장 라우터 v2 — /cost/ledger, /cost/summary
V420 인메모리 원장 유지 + budget 예산 추적 + by_endpoint alias (dashboard 단절 해결).
ADR-003: OTel span 포함.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

try:
    from fastapi import APIRouter, Depends, Query
    _FA = True
except ImportError:
    _FA = False

from apps.studio_api.schema.mapper import (
    CostLedgerRequest, CostLedgerResponse,
    CostEntry, CostSummaryResponse,
)
from apps.studio_api.auth.middleware import get_current_user, TokenPayload
from apps.studio_api.otel.setup import start_span

# 인메모리 원장 (프로세스 재시작 시 초기화 — V430에서 파일/DB 영속화 가능)
_LEDGER: list[dict[str, Any]] = []

# V429: 예산 한도 설정 (환경변수로 오버라이드 가능)
import os
_BUDGET_LIMIT_USD: float = float(os.environ.get("LITERARY_OS_COST_BUDGET_USD", "100.0"))

if _FA:
    router = APIRouter(prefix="/api/v1/cost", tags=["Cost"])
else:
    router = None  # type: ignore


if _FA:
    @router.post("/ledger", response_model=CostLedgerResponse)
    async def record_cost(
        req: CostLedgerRequest,
        user: TokenPayload = Depends(get_current_user),
    ) -> CostLedgerResponse:
        """
        비용 항목 기록.
        operation_type: analyze | generate | gate | import | export | voice
        """
        with start_span("cost.record_ledger", trace_id=str(uuid.uuid4())) as span:
            span.set_attribute("series_id", req.series_id)
            span.set_attribute("operation_type", req.operation_type)
            span.set_attribute("cost_usd", req.cost_usd)

            try:
                entry_id = str(uuid.uuid4())
                ts = datetime.now(timezone.utc).isoformat()
                _LEDGER.append({
                    "entry_id": entry_id,
                    "series_id": req.series_id,
                    "operation_type": req.operation_type,
                    "cost_usd": req.cost_usd,
                    "token_count": req.token_count,
                    "model": req.model,
                    "recorded_by": user.sub,
                    "timestamp": ts,
                })
                return CostLedgerResponse(
                    entry_id=entry_id,
                    series_id=req.series_id,
                    operation_type=req.operation_type,
                    cost_usd=req.cost_usd,
                    timestamp=ts,
                    recorded=True,
                )
            except Exception as exc:
                span.add_event("degraded_mode", {"reason": str(exc)})
                return CostLedgerResponse(
                    entry_id="",
                    series_id=req.series_id,
                    operation_type=req.operation_type,
                    cost_usd=0.0,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                    recorded=False,
                )

    @router.get("/summary", response_model=CostSummaryResponse)
    async def get_cost_summary(
        series_id: str | None = Query(None),
        operation_type: str | None = Query(None),
        limit: int = Query(100, ge=1, le=1000),
        user: TokenPayload = Depends(get_current_user),
    ) -> CostSummaryResponse:
        """
        비용 집계 조회. series_id / operation_type 필터 지원.
        V429: budget_used_pct + by_endpoint (dashboard alias) 포함.
        """
        with start_span("cost.get_summary") as span:
            span.set_attribute("series_id", series_id or "all")
            span.set_attribute("operation_type", operation_type or "all")

            try:
                entries = list(_LEDGER)
                if series_id:
                    entries = [e for e in entries if e["series_id"] == series_id]
                if operation_type:
                    entries = [e for e in entries if e["operation_type"] == operation_type]
                entries = entries[-limit:]

                total_cost   = sum(e["cost_usd"] for e in entries)
                total_tokens = sum(e.get("token_count") or 0 for e in entries)

                # 타입별 집계
                by_type: dict[str, float] = {}
                for e in entries:
                    by_type[e["operation_type"]] = round(
                        by_type.get(e["operation_type"], 0.0) + e["cost_usd"], 6
                    )

                # V429: budget 사용률 계산
                budget_pct = round(min(100.0, (total_cost / _BUDGET_LIMIT_USD) * 100), 2)

                # V429: by_endpoint alias (dashboard_v425 연결 단절 해결)
                # operation_type 키를 그대로 사용 (analyze→analyze, gate→gate 등)
                by_endpoint = dict(by_type)

                return CostSummaryResponse(
                    total_entries=len(entries),
                    total_cost_usd=round(total_cost, 6),
                    total_tokens=total_tokens,
                    by_operation_type=by_type,
                    entries=[CostEntry(**{k: v for k, v in e.items() if k in CostEntry.model_fields}) for e in entries],
                    budget_limit_usd=_BUDGET_LIMIT_USD,
                    budget_used_pct=budget_pct,
                    by_endpoint=by_endpoint,
                )
            except Exception as exc:
                span.add_event("degraded_mode", {"reason": str(exc)})
                return CostSummaryResponse(
                    total_entries=0,
                    total_cost_usd=0.0,
                    total_tokens=0,
                    by_operation_type={},
                    entries=[],
                    budget_limit_usd=_BUDGET_LIMIT_USD,
                    budget_used_pct=0.0,
                    by_endpoint={},
                )

    @router.delete("/ledger", tags=["Cost"])
    async def clear_ledger(
        user: TokenPayload = Depends(get_current_user),
    ) -> dict:
        """원장 초기화 (테스트/관리자용). V429 신규."""
        _LEDGER.clear()
        return {"cleared": True, "message": "원장이 초기화되었습니다."}
