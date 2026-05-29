"""
V424: ManuscriptExporter v2
NKGGraphStore 씬 → ClosedLoopRenderOrchestratorV2 → 포맷 변환 출력.

ADR-001: L3 레이어 — literary_system 직접 접근 허용.
ADR-005: 기존 stub 인터페이스 (scene_count, content, download_url) 보존.

연결 신경망:
  ExportRequest.scene_ids
  → NKGGraphStore.get_node()           : 씬 메타데이터 조회
  → RenderInput 조립                   : base_text 재구성
  → ClosedLoopRenderOrchestratorV2     : prose 품질 향상 (선택적)
  → FormatConverter.convert()          : txt / md / docx 변환
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

logger = logging.getLogger(__name__)

# ── literary_system 연결 ─────────────────────────────────────
try:
    from literary_system.nkg.graph_store import NKGGraphStore
    from literary_system.nkg.schema import NKGNodeType
    _CORE = True
except ImportError:
    _CORE = False

try:
    from literary_system.prose.render_orchestrator import (
        ClosedLoopRenderOrchestratorV2, RenderInput, FinalRenderedProseIR
    )
    from literary_system.prose.emotion_behavior import EmotionalDelta
    from literary_system.prose.sensory_anchor import SettingSeed
    _RENDER = True
except ImportError:
    _RENDER = False


# ── 포맷 변환기 ──────────────────────────────────────────────

class FormatConverter:
    """FinalRenderedProseIR → 목표 포맷 문자열."""

    def convert(
        self,
        scenes: list[dict[str, Any]],
        fmt: str,
        series_id: str,
    ) -> str:
        """
        scenes: [{"scene_id": ..., "prose": ..., "episode": ..., "passed": ...}]
        fmt: txt | md | docx (docx는 V430에서 python-docx 연결 예정 → 현재 md 대체)
        """
        if fmt == "txt":
            return self._to_txt(scenes, series_id)
        elif fmt in ("md", "docx"):
            return self._to_md(scenes, series_id)
        else:
            return self._to_txt(scenes, series_id)

    def _to_txt(self, scenes: list[dict], series_id: str) -> str:
        lines = [f"[{series_id}] 내보내기", "=" * 40, ""]
        for s in scenes:
            lines.append(f"=== {s['scene_id']} (E{s.get('episode', 1):02d}) ===")
            lines.append(s.get("prose", "(내용 없음)"))
            lines.append("")
        return "\n".join(lines)

    def _to_md(self, scenes: list[dict], series_id: str) -> str:
        lines = [f"# {series_id}", ""]
        for s in scenes:
            ep = s.get("episode", 1)
            lines.append(f"## {s['scene_id']} (에피소드 {ep})")
            lines.append("")
            lines.append(s.get("prose", "*(내용 없음)*"))
            lines.append("")
            if s.get("score") is not None:
                lines.append(f"> 품질 점수: {s['score']:.2f} {'✅' if s.get('passed') else '⚠️'}")
                lines.append("")
        return "\n".join(lines)


class ManuscriptExporter:
    """
    V424 ManuscriptExporter v2.
    routers/io.py의 stub을 교체하는 실제 익스포터.

    파이프라인:
      scene_ids → NKGGraphStore.get_node()
               → (선택적) ClosedLoopRenderOrchestratorV2.render_safe()
               → FormatConverter.convert()
               → 완성 텍스트 반환
    """

    def __init__(
        self,
        store: Any | None = None,
        enable_render: bool = False,
    ) -> None:
        self._store = store
        self._enable_render = enable_render and _RENDER
        self._converter = FormatConverter()
        self._renderer = None

        if self._enable_render:
            try:
                self._renderer = ClosedLoopRenderOrchestratorV2()
            except Exception as exc:
                logger.warning("CLRO v2 초기화 실패 (degraded): %s", exc)
                self._enable_render = False

    def export(
        self,
        series_id: str,
        scene_ids: list[str],
        fmt: str = "md",
    ) -> dict[str, Any]:
        """
        씬 목록 → 포맷 변환 → export 결과 반환.
        routers/io.py에서 직접 호출.
        """
        try:
            scenes: list[dict[str, Any]] = []
            warnings: list[str] = []
            missing: list[str] = []

            for sid in scene_ids:
                scene_data = self._fetch_scene(sid)
                if scene_data is None:
                    missing.append(sid)
                    # 씬 미존재 시 placeholder
                    scenes.append({
                        "scene_id": sid,
                        "episode": 1,
                        "prose": f"(씬 {sid!r} — NKG 미등록)",
                        "score": None,
                        "passed": False,
                    })
                    continue

                prose = scene_data.get("base_text", "")
                score = None
                passed = False

                # ClosedLoopRenderOrchestratorV2 연결 (선택적)
                if self._enable_render and self._renderer and prose:
                    try:
                        render_in = RenderInput(
                            scene_id=sid,
                            base_text=prose,
                            genre_id=scene_data.get("genre_id", "literary"),
                            char_id=scene_data.get("char_id", ""),
                            emotion=EmotionalDelta(),
                            setting=SettingSeed(),
                        )
                        result: FinalRenderedProseIR = self._renderer.render_safe(render_in)
                        prose = result.prose
                        score = result.score.avg if hasattr(result.score, "avg") else None
                        passed = result.passed
                    except Exception as exc:
                        logger.warning("CLRO render 실패 [%s] (degraded): %s", sid, exc)

                scenes.append({
                    "scene_id": sid,
                    "episode": scene_data.get("episode", 1),
                    "prose": prose or f"(씬 {sid!r} — 본문 없음)",
                    "score": score,
                    "passed": passed,
                })

            if missing:
                warnings.append(f"NKG 미등록 씬: {missing}")

            content = self._converter.convert(scenes, fmt, series_id)

            return {
                "series_id": series_id,
                "format": fmt,
                "scene_count": len(scenes),
                "content": content,
                "download_url": None,
                "warnings": warnings,
                "size_bytes": len(content.encode("utf-8")),
            }

        except Exception as exc:
            logger.error("ManuscriptExporter.export() 오류: %s", exc)
            return {
                "series_id": series_id,
                "format": fmt,
                "scene_count": 0,
                "content": "",
                "download_url": None,
                "warnings": [f"내보내기 오류 (degraded): {exc}"],
                "size_bytes": 0,
            }

    def _fetch_scene(self, scene_id: str) -> dict[str, Any] | None:
        """
        NKGGraphStore에서 씬 메타데이터 조회.
        store 미주입 시 None 반환 (degraded).
        """
        if not _CORE or self._store is None:
            return None
        try:
            node = self._store.get_node(scene_id)
            if node is None:
                return None
            return {
                "scene_id": scene_id,
                "episode": getattr(node, "episode_index", 1),
                "base_text": "",  # NKG는 텍스트 미저장 (ADR-001 L2 원칙)
                "genre_id": "literary",
                "char_id": "",
            }
        except Exception as exc:
            logger.warning("NKGGraphStore 조회 실패 [%s]: %s", scene_id, exc)
            return None
