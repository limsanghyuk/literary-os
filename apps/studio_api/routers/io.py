"""
V424: 입출력 라우터 v2 — /import, /export
ManuscriptImporter v2 + ManuscriptExporter v2 실 연결.
ADR-001: L3 io/ 서브패키지 경유 — literary_system 직접 접근 허용.
ADR-002: 인증 의존성 주입.
ADR-003: OTel span + SLO 측정.

V420 stub 인터페이스 완전 보존 (GitNexus 불변 원칙):
  ImportResponse: series_id, format, scene_count, imported_scene_ids, warnings
  ExportResponse: series_id, format, scene_count, content, download_url
"""
from __future__ import annotations

import uuid
from typing import Any

try:
    from fastapi import APIRouter, Depends, HTTPException
    _FA = True
except ImportError:
    _FA = False

from apps.studio_api.schema.mapper import (
    ImportRequest, ImportResponse,
    ExportRequest, ExportResponse,
)
from apps.studio_api.auth.middleware import get_current_user, TokenPayload
from apps.studio_api.otel.setup import start_span
from apps.studio_api.io.importer.manuscript_importer import ManuscriptImporter
from apps.studio_api.io.exporter.manuscript_exporter import ManuscriptExporter

if _FA:
    router = APIRouter(prefix="/api/v1", tags=["IO"])
else:
    router = None  # type: ignore

# ── 싱글톤 (애플리케이션 수명 동안 재사용) ───────────────────
_importer = ManuscriptImporter(store=None, enable_learning=False)
_exporter = ManuscriptExporter(store=None, enable_render=False)


def inject_io_store(store: Any) -> None:
    """
    NKGGraphStore 주입 — main.py v2에서 호출.
    V425+ React 대시보드 연동 시 활성화.
    """
    global _importer, _exporter
    _importer = ManuscriptImporter(store=store, enable_learning=True)
    _exporter = ManuscriptExporter(store=store, enable_render=False)


if _FA:
    @router.post("/import", response_model=ImportResponse)
    async def import_manuscript(
        req: ImportRequest,
        user: TokenPayload = Depends(get_current_user),
    ) -> ImportResponse:
        """
        원고 텍스트 임포트.
        V423 ManuscriptImporter v2: 구분자 기반 씬 분리 + NKGGraphStore 저장.

        지원 format: txt | md | docx | pdf
        content: 원고 전체 텍스트 (max 1MB)
        """
        with start_span("io.import_manuscript", trace_id=str(uuid.uuid4())) as span:
            span.set_attribute("series_id", req.series_id)
            span.set_attribute("format", req.format)
            span.set_attribute("content_length", len(req.content))
            span.set_attribute("user_id", user.sub)

            result = _importer.parse(
                content=req.content,
                series_id=req.series_id,
                format=req.format,
            )

            span.set_attribute("scene_count", result.get("scene_count", 0))
            if result.get("warnings"):
                span.add_event("import_warnings", {"count": len(result["warnings"])})

            return ImportResponse(
                series_id=result["series_id"],
                format=result["format"],
                scene_count=result["scene_count"],
                imported_scene_ids=result["imported_scene_ids"],
                characters=result.get("characters", []),
                warnings=result.get("warnings", []),
            )

    @router.post("/export", response_model=ExportResponse)
    async def export_manuscript(
        req: ExportRequest,
        user: TokenPayload = Depends(get_current_user),
    ) -> ExportResponse:
        """
        씬 목록 → 포맷 변환 내보내기.
        V424 ManuscriptExporter v2: NKGGraphStore 조회 + FormatConverter.

        지원 format: txt | md | docx
        scene_ids: 내보낼 씬 ID 목록
        """
        with start_span("io.export_manuscript", trace_id=str(uuid.uuid4())) as span:
            span.set_attribute("series_id", req.series_id)
            span.set_attribute("format", req.format)
            span.set_attribute("scene_count", len(req.scene_ids))
            span.set_attribute("user_id", user.sub)

            result = _exporter.export(
                series_id=req.series_id,
                scene_ids=req.scene_ids,
                fmt=req.format,
            )

            span.set_attribute("output_bytes", result.get("size_bytes", 0))
            if result.get("warnings"):
                span.add_event("export_warnings", {"count": len(result["warnings"])})

            return ExportResponse(
                series_id=result["series_id"],
                format=result["format"],
                scene_count=result["scene_count"],
                content=result["content"],
                download_url=result.get("download_url"),
                size_bytes=result.get("size_bytes", 0),
            )
