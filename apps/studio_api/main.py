"""
V420: Studio API v2 — apps/studio_api/main.py
V316 엔드포인트 완전 보존 + 신규 라우터 통합.
ADR-001: literary_system 코어는 SchemaMapper 경유만 허용.
ADR-002: OAuth 2.1 JWT 인증 (DEV_MODE bypass 포함).
ADR-003: OTel 미들웨어 + SLO 측정.

기존 V316 코드는 main_v316.py 로 보존.
"""
from __future__ import annotations

import time
import uuid
from pathlib import Path
from typing import Any

# ── FastAPI 선택적 임포트 ─────────────────────────────────────
try:
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    from starlette.middleware.base import BaseHTTPMiddleware
    from starlette.requests import Request
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False

# ── literary_system 코어 (선택적) ────────────────────────────
try:
    from literary_system.orchestrators.build_opening_orchestrator import BuildOpeningOrchestrator
    from literary_system.trace.trace_dataset_store import TraceDatasetStore
    _CORE_AVAILABLE = True
except ImportError:
    _CORE_AVAILABLE = False

# ── V420 서브패키지 임포트 ────────────────────────────────────
from apps.studio_api.otel.setup import start_span, SLO
from apps.studio_api.ratelimit.bucket import InMemoryTokenBucket

# ── 라우터 임포트 ─────────────────────────────────────────────
if _FASTAPI_AVAILABLE:
    from apps.studio_api.routers.analyze import router as analyze_router
    from apps.studio_api.routers.io import router as io_router
    from apps.studio_api.routers.cost import router as cost_router
    from apps.studio_api.routers.jobs import router as jobs_router
    from apps.studio_api.routers.generate import router as generate_router, inject_dependencies
    from apps.studio_api.ws.energy import router as ws_router
    from apps.studio_api.middleware.idempotency import IdempotencyMiddleware

# ── Rate Limiter (전역) ───────────────────────────────────────
_rate_limiter = InMemoryTokenBucket(rate=10, burst=20)

# ── 앱 시작 시간 ──────────────────────────────────────────────
_START_TIME = time.time()


# ── OTel 요청 계측 미들웨어 ───────────────────────────────────
if _FASTAPI_AVAILABLE:
    class OtelMiddleware(BaseHTTPMiddleware):
        """
        모든 요청에 span 생성 + SLO 위반 경고 로그.
        ADR-003: /analyze P95<1.5s, /generate P95<30s, /gate P95<5s
        """
        async def dispatch(self, request: Request, call_next):
            trace_id = request.headers.get("X-Trace-ID", str(uuid.uuid4()))
            path = request.url.path

            with start_span(f"http.{request.method}.{path}", trace_id=trace_id) as span:
                span.set_attribute("http.method", request.method)
                span.set_attribute("http.path", path)
                span.set_attribute("http.trace_id", trace_id)

                response = await call_next(request)

                span.set_attribute("http.status_code", response.status_code)

                # SLO 경계 체크
                slo_limit = SLO.get(path)
                if slo_limit and span.duration_ms > slo_limit * 1000:
                    span.add_event(
                        "slo_breach",
                        {
                            "path": path,
                            "duration_ms": span.duration_ms,
                            "slo_ms": slo_limit * 1000,
                        },
                    )
                response.headers["X-Trace-ID"] = trace_id
                return response

    class RateLimitMiddleware(BaseHTTPMiddleware):
        """토큰 버킷 기반 전역 Rate Limiter. 429 반환."""
        async def dispatch(self, request: Request, call_next):
            # 클라이언트 식별: X-Forwarded-For → remote_addr
            client = (
                request.headers.get("X-Forwarded-For", "")
                or (request.client.host if request.client else "anonymous")
            )
            if not _rate_limiter.allow(client):
                return JSONResponse(
                    status_code=429,
                    content={"detail": "Rate limit exceeded — try again later."},
                    headers={"Retry-After": "1"},
                )
            return await call_next(request)


# ── 앱 팩토리 ─────────────────────────────────────────────────
def create_studio_app(
    out_root: str | Path = "./out",
    sovereign_backend: str | Path | None = None,
) -> Any:
    """
    Literary OS Studio API v2 팩토리.

    구조:
      - POST /api/v1/analyze        → routers/analyze.py
      - POST /api/v1/gate           → routers/analyze.py
      - GET  /api/v1/nkg/{id}       → routers/analyze.py
      - POST /api/v1/voice/analyze  → routers/analyze.py
      - POST /api/v1/import         → routers/io.py
      - POST /api/v1/export         → routers/io.py
      - POST /api/v1/cost/ledger    → routers/cost.py
      - GET  /api/v1/cost/summary   → routers/cost.py
      - GET  /api/v1/jobs/{id}      → routers/jobs.py
      - DELETE /api/v1/jobs/{id}    → routers/jobs.py
      - POST /api/v1/generate       → routers/generate.py  (V316 마이그레이션)
      - POST /api/v1/edit           → routers/generate.py  (V316 마이그레이션)
      - POST /api/v1/export/traces  → routers/generate.py  (V316 마이그레이션)
      - GET  /api/v1/status/{id}    → routers/generate.py  (V316 마이그레이션)
      - WS   /ws/energy/{series_id} → ws/energy.py
      - GET  /health                → 내장
    """
    if not _FASTAPI_AVAILABLE:
        return _MockStudioApp(out_root, sovereign_backend)

    app = FastAPI(
        title="Literary OS Studio API",
        description="V420 — 7-Layer 아키텍처 기반 문학 운영체계 HTTP 인터페이스",
        version="0.2.0",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # ── 미들웨어 체인 (등록 역순으로 실행) ──────────────────────
    # CORS (최외곽)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",   # React 개발 서버
            "http://localhost:8080",
            "https://literary-os.dev", # 프로덕션 (V430 업데이트 예정)
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Trace-ID", "X-Idempotency-Replayed"],
    )
    # Idempotency
    app.add_middleware(IdempotencyMiddleware)
    # Rate Limiter
    app.add_middleware(RateLimitMiddleware)
    # OTel 계측
    app.add_middleware(OtelMiddleware)

    # ── 라우터 등록 ──────────────────────────────────────────────
    app.include_router(analyze_router)
    app.include_router(io_router)
    app.include_router(cost_router)
    app.include_router(jobs_router)
    app.include_router(generate_router)
    app.include_router(ws_router)

    # ── generate 라우터에 의존성 주입 ────────────────────────────
    if _CORE_AVAILABLE:
        try:
            orch = BuildOpeningOrchestrator(
                out_root=out_root,
                sovereign_backend=sovereign_backend,
            )
            store = TraceDatasetStore(store_root=Path(out_root) / "traces")
            inject_dependencies(orch, store, str(out_root))
        except Exception:
            pass  # 코어 초기화 실패 → degraded mode

    # ── 헬스체크 ─────────────────────────────────────────────────
    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        """V420 서비스 상태 및 Circuit Breaker 상태 반환."""
        from apps.studio_api.resilience.circuit_breaker import (
            drse_cb, nkg_cb, gate_cb, voice_cb
        )
        return {
            "status": "ok",
            "version": "V427",
            "uptime_seconds": round(time.time() - _START_TIME, 1),
            "core_available": _CORE_AVAILABLE,
            "circuit_breakers": [
                cb.status()
                for cb in [drse_cb, nkg_cb, gate_cb, voice_cb]
            ],
        }

    @app.get("/", include_in_schema=False)
    async def root() -> dict:
        return {"message": "Literary OS Studio API v2 (V427)", "docs": "/docs"}

    # V425: React 대시보드 v1 서빙
    try:
        from fastapi.responses import HTMLResponse
        from fastapi.staticfiles import StaticFiles
        _STATIC_DIR = Path(__file__).parent / "static"
        if _STATIC_DIR.exists():
            app.mount("/static", StaticFiles(directory=str(_STATIC_DIR)), name="static")

        @app.get("/dashboard", include_in_schema=False, response_class=HTMLResponse)
        async def dashboard():
            """V425 React 대시보드 v1."""
            html_path = _STATIC_DIR / "dashboard_v425.html"
            if html_path.exists():
                return HTMLResponse(content=html_path.read_text(encoding="utf-8"))
            return HTMLResponse(content="<h1>Dashboard not found</h1>", status_code=404)
    except ImportError:
        pass  # StaticFiles not available (headless env)

    return app


# ── Mock 앱 (FastAPI 미설치 환경) ─────────────────────────────
class _MockStudioApp:
    """FastAPI 없는 환경에서의 더미 앱 — 테스트 목적."""

    def __init__(self, out_root: Any, sovereign_backend: Any) -> None:
        self.out_root = out_root
        self.sovereign_backend = sovereign_backend
        self.version = "V420-mock"

    def run_generate(self, prompt: str, mode: str = "quick", episodes: int = 3) -> dict:
        return {
            "status": "mock",
            "prompt": prompt,
            "mode": mode,
            "episodes": episodes,
        }


# ── CLI 진입점 ────────────────────────────────────────────────
def main() -> None:
    """uvicorn으로 직접 실행: python -m apps.studio_api.main"""
    try:
        import uvicorn
        app = create_studio_app()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError:
        print("[Literary OS] uvicorn 미설치 — pip install uvicorn 후 재시도")


if __name__ == "__main__":
    main()


# ═══════════════════════════════════════════════════════════════
# V316 역호환 심 — 기존 테스트(test_v316_trace_slm.py) 보호
# ADR-005: baseline 2,897 PASS 유지 정책
# ═══════════════════════════════════════════════════════════════

class MockStudioApp(_MockStudioApp):
    """
    공개 이름 유지 — V316 테스트가 'MockStudioApp'을 직접 임포트.
    run_generate / get_status 인터페이스 보존.
    """

    def run_generate(self, prompt: str, mode: str = "quick", episodes: int = 3) -> dict:
        return {
            "status": "mock",
            "prompt": prompt,
            "mode": mode,
            "episodes": [{"episode_no": i + 1, "scenes": []} for i in range(episodes)],
            "style_dna": {},
            "bridge_status": {"available": False},
            "memory_summary": {},
        }

    def get_status(self) -> dict:
        return {
            "status": "mock",
            "version": self.version,
            "out_root": str(self.out_root),
        }


# ── V316 국소 수정 핸들러 (역호환) ──────────────────────────────
# generate 라우터로 이전했으나 직접 임포트 경로 유지.

def _edit_reduce_dialogue(req: Any) -> dict:
    return {
        "edit_type": "reduce_dialogue",
        "scene_id": getattr(req, "scene_id", ""),
        "instruction": getattr(req, "instruction", ""),
        "status": "applied",
        "changes": ["dialogue_ratio 감소"],
    }


def _edit_add_residue(req: Any) -> dict:
    return {
        "edit_type": "add_residue",
        "scene_id": getattr(req, "scene_id", ""),
        "instruction": getattr(req, "instruction", ""),
        "status": "applied",
        "changes": ["잔류물 삽입"],
    }


def _edit_delay_reveal(req: Any) -> dict:
    return {
        "edit_type": "delay_reveal",
        "scene_id": getattr(req, "scene_id", ""),
        "instruction": getattr(req, "instruction", ""),
        "status": "applied",
        "changes": ["폭로 지연"],
    }


def _edit_fix_pdi(req: Any) -> dict:
    return {
        "edit_type": "fix_pdi",
        "scene_id": getattr(req, "scene_id", ""),
        "instruction": getattr(req, "instruction", ""),
        "status": "applied",
        "changes": ["PDI 수정"],
    }

# V411 release_gate 역호환 심
cli_entry = main
