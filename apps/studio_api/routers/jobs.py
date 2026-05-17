"""
V420: 비동기 작업 라우터 — /jobs/{job_id}
장시간 작업(생성, 임포트 등) 의 상태 조회 및 취소.
"""
from __future__ import annotations

import uuid
from typing import Any

try:
    from fastapi import APIRouter, Depends, HTTPException
    _FA = True
except ImportError:
    _FA = False

from apps.studio_api.schema.mapper import JobStatusResponse
from apps.studio_api.auth.middleware import get_current_user, TokenPayload
from apps.studio_api.jobs.queue import get_job, cancel_job
from apps.studio_api.otel.setup import start_span

if _FA:
    router = APIRouter(prefix="/api/v1/jobs", tags=["Jobs"])
else:
    router = None  # type: ignore


if _FA:
    @router.get("/{job_id}", response_model=JobStatusResponse)
    async def get_job_status(
        job_id: str,
        user: TokenPayload = Depends(get_current_user),
    ) -> JobStatusResponse:
        """
        비동기 작업 상태 조회.
        status: pending | running | completed | failed | cancelled
        """
        with start_span("jobs.get_status", trace_id=job_id) as span:
            span.set_attribute("job_id", job_id)
            span.set_attribute("user_id", user.sub)

            job = get_job(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")

            return JobStatusResponse(
                job_id=job_id,
                status=job.get("status", "unknown"),
                progress=job.get("progress", 0),
                result=job.get("result"),
                error=job.get("error"),
                created_at=job.get("created_at", ""),
                updated_at=job.get("updated_at", ""),
            )

    @router.delete("/{job_id}", response_model=JobStatusResponse)
    async def cancel_job_endpoint(
        job_id: str,
        user: TokenPayload = Depends(get_current_user),
    ) -> JobStatusResponse:
        """
        실행 중인 작업 취소 요청.
        완료된 작업에 대한 취소는 409를 반환.
        """
        with start_span("jobs.cancel", trace_id=job_id) as span:
            span.set_attribute("job_id", job_id)

            job = get_job(job_id)
            if job is None:
                raise HTTPException(status_code=404, detail=f"Job {job_id!r} not found")
            if job.get("status") in ("completed", "failed"):
                raise HTTPException(
                    status_code=409,
                    detail=f"Cannot cancel job in status: {job.get('status')}"
                )

            try:
                cancel_job(job_id)
            except Exception as exc:  # noqa: BLE001
                span.add_event("cancel_failed", {"reason": str(exc)})

            updated = get_job(job_id) or job
            return JobStatusResponse(
                job_id=job_id,
                status=updated.get("status", "cancelled"),
                progress=updated.get("progress", 0),
                result=updated.get("result"),
                error=updated.get("error"),
                created_at=updated.get("created_at", ""),
                updated_at=updated.get("updated_at", ""),
            )
