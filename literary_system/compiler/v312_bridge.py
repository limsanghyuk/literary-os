"""
V313→V322: V312Bridge
literary_system → SOVEREIGN_OS_V312 연결 브릿지.
이것이 V313의 핵심 — 사전 설계층과 실행 런타임을 처음으로 연결.

흐름:
  SeedCompiler → MacroArcCompiler → CharacterGrid → Residue → StyleDNA
     → PromptAssembler → [bundle.json]
         → V312Bridge → run_sovereign_v312(state)
             → Literary Librarian → trace_commit
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from typing import Any


class V312Bridge:
    """
    literary_system의 bundle.json 출력을
    SOVEREIGN_OS_V312의 run_sovereign_v312()로 연결.
    """

    def __init__(self, sovereign_backend_path: str | Path | None = None):
        """
        sovereign_backend_path: SOVEREIGN_OS_V312 backend 디렉터리 경로.
        None이면 환경변수 SOVEREIGN_BACKEND_PATH 사용.
        """
        import os
        if sovereign_backend_path is None:
            sovereign_backend_path = os.getenv(
                "SOVEREIGN_BACKEND_PATH",
                str(Path(__file__).parent.parent.parent.parent
                    / "SOVEREIGN_OS_V312" / "backend")
            )
        self.backend_path = Path(sovereign_backend_path)
        self._engine_loaded = False

    def _load_engine(self) -> None:
        """V312 엔진 임포트 (지연 로딩)."""
        if self._engine_loaded:
            return
        bp = str(self.backend_path)
        if bp not in sys.path:
            sys.path.insert(0, bp)
        self._engine_loaded = True

    def run(
        self,
        bundle: dict[str, Any],
        timeout_seconds: float = 120.0,
    ) -> dict[str, Any]:
        """
        bundle.json → V312 실행 → 결과 반환.
        동기 래퍼 (asyncio 이벤트루프 자동 관리).
        """
        return asyncio.run(self.run_async(bundle, timeout_seconds))

    async def run_async(
        self,
        bundle: dict[str, Any],
        timeout_seconds: float = 120.0,
    ) -> dict[str, Any]:
        """비동기 버전."""
        self._load_engine()
        try:
            from sovereign_config_v100 import SovereignState
            from sovereign_engine_v100 import run_sovereign_v312
        except ImportError as e:
            return {
                "error": f"V312 engine not found: {e}",
                "backend_path": str(self.backend_path),
                "hint": "Set SOVEREIGN_BACKEND_PATH to the V312 backend directory.",
            }

        # bundle.json → SovereignState 초기화
        state = SovereignState(seed_text=bundle.get("render_instruction", ""))
        state.v311_mode = True
        state.v311_bundle_json = bundle
        state.v310_mode = True
        state.v311_call_count = 0
        state.execution_trace = []

        # Literary State 초기값 주입
        state_before = bundle.get("state_before", {})
        if state_before:
            state.v7_state_before = state_before

        try:
            result = await asyncio.wait_for(
                run_sovereign_v312(state),
                timeout=timeout_seconds,
            )
        except asyncio.TimeoutError:
            return {"error": f"V312 timeout after {timeout_seconds}s"}
        except Exception as e:
            return {"error": str(e), "type": type(e).__name__}

        # 결과 추출
        output_bundle = getattr(result, "v311_output_bundle", {})
        return {
            "render_output":     output_bundle.get("render_output", {}),
            "literary_state_after": output_bundle.get("state_after", {}),
            "promotion_decision":   output_bundle.get("promotion_decision", "archive_only"),
            "literary_loss":        output_bundle.get("critic_ensemble", {}).get("findings_count", 0),
            "call_count":           output_bundle.get("call_count", 0),
            "trace_ref":            output_bundle.get("trace_ref", ""),
            "hitl_recommended":     getattr(result, "v312_hitl_recommended", False),
            "hitl_reasons":         getattr(result, "v312_hitl_reasons", []),
            "fewshot_committed":    getattr(result, "v312_fewshot_committed", False),
            "loss_report":          getattr(result, "literary_loss_report", {}),
        }

    def is_available(self) -> bool:
        """V312 엔진 사용 가능 여부 확인."""
        try:
            self._load_engine()
            import sovereign_engine_v100  # noqa: F401
            return True
        except ImportError:
            return False

    def get_status(self) -> dict[str, Any]:
        return {
            "backend_path": str(self.backend_path),
            "available": self.is_available(),
            "backend_exists": self.backend_path.exists(),
        }
