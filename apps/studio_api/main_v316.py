"""
V316: Studio API — Apps 레이어 초안.
Literary OS의 HTTP 인터페이스.
사용자에게는 3개 엔드포인트만 보인다.

내부 복잡성(V313~V322)은 완전히 은닉.
이것이 "미드저니처럼 단순한 입력"의 실현.

실제 FastAPI 서버 구현 (선택적 의존성).
FastAPI 없는 환경에서는 Mock 모드로 작동.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

# FastAPI 선택적 임포트
try:
    from fastapi import FastAPI, HTTPException
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    _FASTAPI_AVAILABLE = True
except ImportError:
    _FASTAPI_AVAILABLE = False
    # Mock 클래스
    class BaseModel:  # type: ignore
        pass


# ── 요청/응답 스키마 ────────────────────────────────────────
if _FASTAPI_AVAILABLE:
    class GenerateRequest(BaseModel):
        prompt: str
        mode: str = "quick"           # quick | director | studio
        episodes: int = 3
        style_ref: str | None = None
        objects: list[str] | None = None

    class GenerateResponse(BaseModel):
        project_id: str
        mode: str
        episodes: list[dict]
        style_dna: dict
        bridge_status: dict
        memory_summary: dict

    class EditSceneRequest(BaseModel):
        project_id: str
        episode_no: int
        scene_id: str
        edit_type: str          # "reduce_dialogue" | "add_residue" | "delay_reveal" | "fix_pdi"
        instruction: str = ""

    class TraceExportRequest(BaseModel):
        project_id: str | None = None
        format: str = "alpaca"
        max_L_total: float = 0.18

    class ProjectStatusResponse(BaseModel):
        project_id: str
        episodes_completed: int
        avg_L_total: float
        slm_ready_traces: int
        trajectory_shape: str
        knowledge_facts_count: int


# ── API 팩토리 ──────────────────────────────────────────────
def create_studio_app(
    out_root: str | Path = "./out",
    sovereign_backend: str | Path | None = None,
) -> Any:
    """
    Studio API FastAPI 앱 생성.
    FastAPI 없으면 Mock 앱 반환.
    """
    if not _FASTAPI_AVAILABLE:
        return MockStudioApp(out_root, sovereign_backend)

    from literary_system.orchestrators.build_opening_orchestrator import BuildOpeningOrchestrator
    from literary_system.trace.trace_dataset_store import TraceDatasetStore
    from literary_system.slm.dataset_builder import SLMDatasetBuilder

    app = FastAPI(
        title="Literary OS Studio API",
        description="V316 — 문학 운영체계 HTTP 인터페이스",
        version="0.1.0",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["*"],
        allow_headers=["*"],
    )

    orch  = BuildOpeningOrchestrator(out_root=out_root, sovereign_backend=sovereign_backend)
    store = TraceDatasetStore(store_root=Path(out_root) / "traces")

    # ── POST /generate ─────────────────────────────────────
    @app.post("/generate", response_model=GenerateResponse)
    async def generate(req: GenerateRequest) -> GenerateResponse:
        """
        Quick Mode: 한 줄 → 3화 opening 전체 생성.
        사용자는 prompt만 입력. 내부 복잡성 완전 은닉.
        """
        result = orch.run_quick(
            user_prompt=req.prompt,
            total_episodes=req.episodes,
        )
        return GenerateResponse(**result)

    # ── POST /edit ─────────────────────────────────────────
    @app.post("/edit")
    async def edit_scene(req: EditSceneRequest) -> dict:
        """
        특정 씬 국소 수정.
        전체 재생성 없이 부분 수리만 수행.
        """
        # V316: 국소 수정 라우터 (edit_type별 분기)
        edit_routes = {
            "reduce_dialogue":  _edit_reduce_dialogue,
            "add_residue":      _edit_add_residue,
            "delay_reveal":     _edit_delay_reveal,
            "fix_pdi":          _edit_fix_pdi,
        }
        handler = edit_routes.get(req.edit_type)
        if not handler:
            raise HTTPException(400, f"Unknown edit_type: {req.edit_type}")

        return handler(req)

    # ── POST /export/traces ────────────────────────────────
    @app.post("/export/traces")
    async def export_traces(req: TraceExportRequest) -> dict:
        """
        Trace Dataset → SLM 학습 데이터 추출.
        """
        builder = SLMDatasetBuilder(store)
        out_path = Path(out_root) / "exports" / f"slm_{req.format}_{uuid.uuid4().hex[:6]}.jsonl"
        out_path.parent.mkdir(parents=True, exist_ok=True)

        if req.format == "alpaca":
            return builder.build_alpaca_dataset(out_path, max_L_total=req.max_L_total)
        elif req.format == "openai":
            return builder.build_openai_dataset(out_path, max_L_total=req.max_L_total)
        else:
            return store.export_slm_dataset(out_path, max_L_total=req.max_L_total)

    # ── GET /status/{project_id} ───────────────────────────
    @app.get("/status/{project_id}")
    async def project_status(project_id: str) -> dict:
        """프로젝트 현황 조회."""
        stats = store.statistics()
        return {
            "project_id": project_id,
            "slm_ready_traces": stats.get("slm_ready_count", 0),
            "total_traces": stats.get("total_traces", 0),
        }

    # ── GET /health ────────────────────────────────────────
    @app.get("/health")
    async def health() -> dict:
        return {
            "status": "ok",
            "version": "V316",
            "bridge_available": orch.bridge.is_available(),
        }

    return app


# ── 국소 수정 핸들러 ────────────────────────────────────────
def _edit_reduce_dialogue(req: Any) -> dict:
    """대사 압축 — 대사를 행동/오브제로 대체 지시."""
    return {
        "edit_type":    "reduce_dialogue",
        "instruction":  "대사를 50% 줄이고 행동과 오브제로 대체하라. 침묵을 압박으로 활용하라.",
        "scene_id":     req.scene_id,
        "status":       "queued",
    }

def _edit_add_residue(req: Any) -> dict:
    """residue 추가 — 오브제 복귀 지시."""
    return {
        "edit_type":    "add_residue",
        "instruction":  "이전 화에서 등장한 핵심 오브제를 이 씬에 다시 등장시켜 잔향을 강화하라.",
        "scene_id":     req.scene_id,
        "status":       "queued",
    }

def _edit_delay_reveal(req: Any) -> dict:
    """reveal 지연 — 정보 공개 늦추기."""
    return {
        "edit_type":    "delay_reveal",
        "instruction":  "핵심 정보 공개를 다음 화로 미루고 의심/암시만 남겨라.",
        "scene_id":     req.scene_id,
        "status":       "queued",
    }

def _edit_fix_pdi(req: Any) -> dict:
    """PDI 수정 — 감정 직설 → 묘사 전환."""
    return {
        "edit_type":    "fix_pdi",
        "instruction":  "감정 직설 표현(슬펐다/기뻤다/두려웠다)을 모두 행동/오브제 묘사로 대체하라.",
        "scene_id":     req.scene_id,
        "status":       "queued",
    }


# ── Mock 앱 (FastAPI 없는 환경) ────────────────────────────
class MockStudioApp:
    """FastAPI 없는 환경용 Mock Studio App."""

    def __init__(self, out_root: str | Path, sovereign_backend: Any):
        self.out_root = Path(out_root)
        self.sovereign_backend = sovereign_backend

    def run_generate(self, prompt: str, mode: str = "quick", episodes: int = 3) -> dict:
        """직접 호출 인터페이스."""
        from literary_system.orchestrators.build_opening_orchestrator import BuildOpeningOrchestrator
        orch = BuildOpeningOrchestrator(self.out_root, self.sovereign_backend, mode)
        return orch.run_quick(prompt, episodes)

    def get_status(self) -> dict:
        return {
            "status": "mock_mode",
            "fastapi_available": False,
            "hint": "pip install fastapi uvicorn to enable HTTP server",
        }


# ── CLI 진입점 ────────────────────────────────────────────────
def cli_entry() -> None:
    """
    literary-os CLI 진입점.
    FastAPI 설치 시 HTTP 서버 실행, 미설치 시 Mock 모드 안내.

    사용:
      literary-os                        # 기본 127.0.0.1:8000
      literary-os --host 0.0.0.0 --port 8080
      literary-os --mock                 # FastAPI 없이 직접 호출 모드
    """
    import argparse

    parser = argparse.ArgumentParser(
        prog="literary-os",
        description="Literary OS Studio API — V381",
    )
    parser.add_argument("--host", default="127.0.0.1", help="바인드 호스트 (기본: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, help="포트 번호 (기본: 8000)")
    parser.add_argument("--out-root", default="./out", help="출력 루트 디렉터리")
    parser.add_argument("--mock", action="store_true", help="Mock 모드 (FastAPI 없이 실행)")
    args = parser.parse_args()

    if args.mock or not _FASTAPI_AVAILABLE:
        app = MockStudioApp(args.out_root, None)
        print("Literary OS Studio — Mock 모드")
        print(f"  출력 경로: {args.out_root}")
        print("  HTTP 서버 활성화: pip install 'literary-os[server]'")
        status = app.get_status()
        print(f"  상태: {status}")
        return

    try:
        import uvicorn
    except ImportError:
        print("uvicorn 미설치. pip install 'literary-os[server]'")
        return

    app = create_studio_app(out_root=args.out_root)
    print(f"Literary OS Studio 시작 → http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port)
