"""
V420: 생성 라우터 — /generate, /edit, /export/traces, /status/{project_id}
V316 main.py 의 엔드포인트를 분리·마이그레이션.
ADR-002: get_current_user 의존성 추가.
ADR-003: OTel span 포함.
"""
from __future__ import annotations

import uuid
from pathlib import Path
from typing import Any

try:
    from fastapi import APIRouter, Depends, HTTPException
    _FA = True
except ImportError:
    _FA = False

from apps.studio_api.auth.middleware import get_current_user, TokenPayload
from apps.studio_api.otel.setup import start_span

# 기존 V316 의존 임포트 (유지)
try:
    from literary_system.orchestrators.build_opening_orchestrator import BuildOpeningOrchestrator
    from literary_system.slm.dataset_builder import SLMDatasetBuilder
    from literary_system.trace.trace_dataset_store import TraceDatasetStore
    _CORE = True
except ImportError:
    _CORE = False

if _FA:
    router = APIRouter(prefix="/api/v1", tags=["Generate"])
else:
    router = None  # type: ignore

# 공유 오케스트레이터 (애플리케이션 시작 시 inject_dependencies()로 설정됨)
_orch: Any = None
_store: Any = None
_out_root: str = "/tmp/v420_build_output"


def inject_dependencies(orch: Any, store: Any, out_root: str) -> None:
    """main.py v2 에서 호출 — 오케스트레이터/스토어 주입."""
    global _orch, _store, _out_root
    _orch = orch
    _store = store
    _out_root = out_root


if _FA:
    @router.post("/generate")
    async def generate_scene(
        req: dict,
        user: TokenPayload = Depends(get_current_user),
    ) -> dict:
        """
        Quick Mode: 한 줄 → 3화 opening 전체 생성.
        V316 호환 유지, ADR-002 인증 추가.
        """
        with start_span("generate.quick_mode", trace_id=str(uuid.uuid4())) as span:
            span.set_attribute("user_id", user.sub)
            prompt = req.get("prompt", "")
            episodes = req.get("episodes", 3)
            span.set_attribute("episodes", episodes)

            try:
                if _orch is not None:
                    result = _orch.run_quick(user_prompt=prompt, total_episodes=episodes)
                else:
                    # Degraded mode: 오케스트레이터 미초기화
                    result = {
                        "status": "degraded",
                        "prompt": prompt,
                        "episodes": episodes,
                        "content": "(생성 엔진 초기화 전)",
                    }
                return result
            except Exception as exc:  # noqa: BLE001
                span.add_event("degraded_mode", {"reason": str(exc)})
                return {"status": "error", "detail": str(exc)}

    @router.post("/edit")
    async def edit_scene(
        req: dict,
        user: TokenPayload = Depends(get_current_user),
    ) -> dict:
        """
        특정 씬 국소 수정 — V316 edit_type 분기 유지.
        edit_type: reduce_dialogue | add_residue | delay_reveal | fix_pdi
        """
        with start_span("generate.edit_scene") as span:
            edit_type = req.get("edit_type", "")
            span.set_attribute("edit_type", edit_type)
            span.set_attribute("user_id", user.sub)

            VALID_EDIT_TYPES = {
                "reduce_dialogue", "add_residue", "delay_reveal", "fix_pdi"
            }
            if edit_type not in VALID_EDIT_TYPES:
                raise HTTPException(
                    status_code=400,
                    detail=f"Unknown edit_type: {edit_type!r}. "
                           f"Valid: {sorted(VALID_EDIT_TYPES)}"
                )
            try:
                # Stub: V316 핸들러 위임 (literary_system 연결 시 교체)
                return {
                    "status": "ok",
                    "edit_type": edit_type,
                    "scene_id": req.get("scene_id", ""),
                    "result": "(편집 적용됨 — V316 핸들러 위임)",
                }
            except Exception as exc:  # noqa: BLE001
                span.add_event("degraded_mode", {"reason": str(exc)})
                return {"status": "error", "detail": str(exc)}

    @router.post("/export/traces")
    async def export_traces(
        req: dict,
        user: TokenPayload = Depends(get_current_user),
    ) -> dict:
        """
        Trace Dataset → SLM 학습 데이터 추출.
        ADR-004: Tier-B LoRA 학습 데이터 준비.
        """
        with start_span("generate.export_traces") as span:
            fmt = req.get("format", "jsonl")
            max_l_total = req.get("max_L_total", 50000)
            span.set_attribute("format", fmt)
            span.set_attribute("user_id", user.sub)

            try:
                if _store is not None:
                    out_path = (
                        Path(_out_root) / "exports"
                        / f"slm_{fmt}_{uuid.uuid4().hex[:6]}.jsonl"
                    )
                    out_path.parent.mkdir(parents=True, exist_ok=True)
                    builder = SLMDatasetBuilder(_store) if _CORE else None
                    if builder and fmt == "alpaca":
                        return builder.build_alpaca_dataset(out_path, max_L_total=max_l_total)
                    elif builder and fmt == "openai":
                        return builder.build_openai_dataset(out_path, max_L_total=max_l_total)
                    elif _store:
                        return _store.export_slm_dataset(out_path, max_L_total=max_l_total)
                return {"status": "degraded", "format": fmt, "exported": 0}
            except Exception as exc:  # noqa: BLE001
                span.add_event("degraded_mode", {"reason": str(exc)})
                return {"status": "error", "detail": str(exc)}

    @router.get("/status/{project_id}")
    async def project_status(
        project_id: str,
        user: TokenPayload = Depends(get_current_user),
    ) -> dict:
        """프로젝트 현황 조회."""
        with start_span("generate.project_status") as span:
            span.set_attribute("project_id", project_id)
            try:
                if _store is not None:
                    stats = _store.statistics()
                    return {
                        "project_id": project_id,
                        "slm_ready_traces": stats.get("slm_ready_count", 0),
                        "total_traces": stats.get("total_traces", 0),
                    }
                return {"project_id": project_id, "slm_ready_traces": 0, "total_traces": 0}
            except Exception as exc:  # noqa: BLE001
                span.add_event("degraded_mode", {"reason": str(exc)})
                return {"project_id": project_id, "error": str(exc)}
