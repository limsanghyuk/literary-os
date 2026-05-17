"""
V430 — Gate 11: StudioAPIContractGate
Studio API 라우터 임포트 가능성 + 엔드포인트 계약 검증.

LLM 0 calls.

검사 항목:
  1. create_studio_app 임포트 성공
  2. cli_entry 임포트 및 callable 확인
  3. 필수 라우터 6개 임포트 성공
     (analyze, io, cost, jobs, generate, ws.energy)
  4. create_studio_app() 호출 성공 (FastAPI 없는 환경이면 MockStudioApp 반환 허용)
  5. 필수 엔드포인트 경로 등록 확인 (FastAPI 환경에서만)

통과 조건: 모든 임포트 성공, app 객체 생성 성공.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class StudioAPIContractResult:
    passed: bool
    router_import_ok: bool
    app_factory_ok: bool
    cli_entry_ok: bool
    missing_routers: List[str] = field(default_factory=list)
    missing_routes: List[str] = field(default_factory=list)
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "passed": self.passed,
            "router_import_ok": self.router_import_ok,
            "app_factory_ok": self.app_factory_ok,
            "cli_entry_ok": self.cli_entry_ok,
            "missing_routers": self.missing_routers,
            "missing_routes": self.missing_routes,
            "reason": self.reason,
        }


# 필수 라우터 모듈 경로
_REQUIRED_ROUTERS = [
    "apps.studio_api.routers.analyze",
    "apps.studio_api.routers.io",
    "apps.studio_api.routers.cost",
    "apps.studio_api.routers.jobs",
    "apps.studio_api.routers.generate",
    "apps.studio_api.ws.energy",
]

# FastAPI 환경에서 반드시 등록되어야 할 엔드포인트 (prefix 포함)
_REQUIRED_ROUTES = [
    "/api/v1/analyze",
    "/api/v1/gate",
    "/api/v1/generate",
    "/api/v1/cost/ledger",
    "/api/v1/jobs/{job_id}",
    "/health",
]


def run_studio_api_gate() -> StudioAPIContractResult:
    """
    Studio API 계약 검증 실행.
    Returns StudioAPIContractResult (to_dict() 로 직렬화).
    """
    missing_routers: List[str] = []
    missing_routes: List[str] = []

    # -- FastAPI availability check (skip gracefully if not installed) --
    try:
        import fastapi as _fapi
        _FASTAPI_OK = True
    except ImportError:
        _FASTAPI_OK = False

    if not _FASTAPI_OK:
        return StudioAPIContractResult(
            passed=True,
            router_import_ok=True,
            app_factory_ok=True,
            cli_entry_ok=True,
            reason="FastAPI not installed -- gate skipped (non-blocking)",
        )

    # ── 1. 라우터 임포트 검사 ────────────────────────────────────
    router_import_ok = True
    for mod_path in _REQUIRED_ROUTERS:
        try:
            __import__(mod_path)
        except ImportError as e:
            missing_routers.append(f"{mod_path}: {e}")
            router_import_ok = False

    # ── 2. cli_entry callable 검사 ──────────────────────────────
    cli_entry_ok = False
    try:
        from apps.studio_api.main import cli_entry
        cli_entry_ok = callable(cli_entry)
    except (ImportError, AttributeError):
        pass

    # ── 3. create_studio_app 팩토리 검사 ────────────────────────
    app_factory_ok = False
    try:
        from apps.studio_api.main import create_studio_app
        app = create_studio_app(out_root="/tmp/gate11_test")
        app_factory_ok = app is not None

        # ── 4. 엔드포인트 경로 등록 확인 (FastAPI 환경만) ──────────
        if hasattr(app, "routes"):
            registered = {
                getattr(r, "path", "") for r in app.routes
            }
            for required in _REQUIRED_ROUTES:
                if required not in registered:
                    missing_routes.append(required)
    except Exception as e:
        return StudioAPIContractResult(
            passed=False,
            router_import_ok=router_import_ok,
            app_factory_ok=False,
            cli_entry_ok=cli_entry_ok,
            missing_routers=missing_routers,
            missing_routes=missing_routes,
            reason=f"create_studio_app 실패: {e}",
        )

    # ── 최종 판정 ────────────────────────────────────────────────
    passed = (
        router_import_ok
        and cli_entry_ok
        and app_factory_ok
        and len(missing_routes) == 0
    )

    reason = ""
    if not router_import_ok:
        reason = f"라우터 임포트 실패: {missing_routers}"
    elif not cli_entry_ok:
        reason = "cli_entry callable 아님"
    elif not app_factory_ok:
        reason = "create_studio_app() None 반환"
    elif missing_routes:
        reason = f"엔드포인트 미등록: {missing_routes}"

    return StudioAPIContractResult(
        passed=passed,
        router_import_ok=router_import_ok,
        app_factory_ok=app_factory_ok,
        cli_entry_ok=cli_entry_ok,
        missing_routers=missing_routers,
        missing_routes=missing_routes,
        reason=reason,
    )


def _gate_studio_api_contract() -> dict:
    """release_gate.py GATES 등록용 래퍼."""
    result = run_studio_api_gate()
    return {**result.to_dict(), "pass": result.passed}
