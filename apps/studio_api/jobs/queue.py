"""
V420: 장기 작업 Job Queue (인메모리 stub).
V430+: Dramatiq + Redis로 교체 예정.
ADR-001 L4 API Gateway 컴포넌트.
"""
from __future__ import annotations

import uuid
import time
from threading import Thread
from typing import Any, Callable

_jobs: dict[str, dict[str, Any]] = {}


def create_job(fn: Callable, *args, **kwargs) -> str:
    """백그라운드 작업 생성. Job ID 반환."""
    job_id = str(uuid.uuid4())
    _jobs[job_id] = {
        "job_id": job_id,
        "status": "queued",
        "progress": 0.0,
        "result_url": None,
        "error": None,
        "created_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "updated_at": __import__("datetime").datetime.utcnow().isoformat() + "Z",
        "progress": 0,
        "result": None,
    }

    def _run():
        import datetime as _dt
        _jobs[job_id]["status"] = "running"
        _jobs[job_id]["updated_at"] = _dt.datetime.utcnow().isoformat() + "Z"
        try:
            result = fn(*args, **kwargs)
            _jobs[job_id]["status"] = "completed"
            _jobs[job_id]["progress"] = 100
            _jobs[job_id]["result"] = result if isinstance(result, dict) else {"value": str(result)}
            _jobs[job_id]["updated_at"] = _dt.datetime.utcnow().isoformat() + "Z"
        except Exception as e:
            _jobs[job_id]["status"] = "failed"
            _jobs[job_id]["error"] = str(e)
            _jobs[job_id]["updated_at"] = _dt.datetime.utcnow().isoformat() + "Z"

    Thread(target=_run, daemon=True).start()
    return job_id


def get_job(job_id: str) -> dict[str, Any] | None:
    return _jobs.get(job_id)


def cancel_job(job_id: str) -> bool:
    """
    실행 중인 작업 취소 요청.
    NOTE: Thread 기반이므로 강제 종료 불가. 상태만 cancelled로 변경.
    V430 Dramatiq 교체 시 실제 취소 구현.
    """
    import time as _time
    job = _jobs.get(job_id)
    if job is None:
        return False
    if job.get("status") in ("completed", "failed", "cancelled"):
        return False
    job["status"] = "cancelled"
    job["updated_at"] = _time.time()
    return True


def list_jobs(
    status_filter: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    """작업 목록 조회 (상태 필터 지원)."""
    jobs = list(_jobs.values())
    if status_filter:
        jobs = [j for j in jobs if j.get("status") == status_filter]
    return jobs[-limit:]
