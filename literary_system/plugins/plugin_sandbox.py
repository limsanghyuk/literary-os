"""
literary_system/plugins/plugin_sandbox.py
V713 SP-D.3 — Plugin Sandbox

RestrictedPython 기반 플러그인 코드 실행 격리 샌드박스.
PluginWhitelist와 연동하여 허용된 모듈만 import 가능하게 제한한다.

ADR-174 참조.
"""
from __future__ import annotations

import builtins
import copy
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from RestrictedPython import (
    compile_restricted,
    safe_builtins,
    safe_globals,
    limited_builtins,
    utility_builtins,
    PrintCollector,
)
from RestrictedPython.Guards import (
    guarded_iter_unpack_sequence,
    guarded_unpack_sequence,
)

from literary_system.plugins.plugin_whitelist import PluginWhitelist


# ---------------------------------------------------------------------------
# 결과 데이터클래스
# ---------------------------------------------------------------------------

@dataclass
class SandboxResult:
    """샌드박스 실행 결과."""

    success: bool
    return_value: Any = None
    stdout: str = ""
    error: Optional[str] = None
    locals_snapshot: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# 샌드박스 예외
# ---------------------------------------------------------------------------

class SandboxSecurityError(Exception):
    """샌드박스 보안 위반 시 발생."""


class SandboxTimeoutError(Exception):
    """샌드박스 실행 시간 초과 시 발생."""


# ---------------------------------------------------------------------------
# PluginSandbox
# ---------------------------------------------------------------------------

class PluginSandbox:
    """
    RestrictedPython 기반 플러그인 코드 실행 격리 환경.

    - 화이트리스트에 없는 모듈은 import 불가.
    - 위험한 빌트인(exec, eval, open, __import__ 등)은 차단.
    - 실행 결과를 SandboxResult 로 반환.
    """

    def __init__(
        self,
        whitelist: Optional[PluginWhitelist] = None,
        max_output_bytes: int = 64 * 1024,  # 64 KB
    ) -> None:
        self._whitelist = whitelist or PluginWhitelist()
        self._max_output_bytes = max_output_bytes

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def execute(self, code: str, plugin_id: str = "<sandbox>") -> SandboxResult:
        """
        code 를 제한 환경에서 실행한다.

        Args:
            code: 실행할 Python 소스 코드.
            plugin_id: 로깅·오류 메시지용 식별자.

        Returns:
            SandboxResult
        """
        # 1) RestrictedPython 컴파일
        try:
            byte_code = compile_restricted(code, filename=plugin_id, mode="exec")
        except SyntaxError as exc:
            return SandboxResult(
                success=False,
                error=f"SyntaxError in plugin '{plugin_id}': {exc}",
            )

        if byte_code is None:
            return SandboxResult(
                success=False,
                error=f"RestrictedPython compilation failed for plugin '{plugin_id}'",
            )

        # 2) 실행 환경 구성
        # PrintCollector 기반 print 캡처
        _print_collector = PrintCollector()

        globs = self._build_globals(plugin_id, _print_collector)
        local_ns: Dict[str, Any] = {}

        # 3) 실행
        try:
            exec(byte_code, globs, local_ns)  # noqa: S102 — RestrictedPython이 이미 제한
        except SandboxSecurityError as exc:
            return SandboxResult(
                success=False,
                error=str(exc),
                stdout=_print_collector(),
            )
        except Exception as exc:  # noqa: BLE001
            return SandboxResult(
                success=False,
                error=f"{type(exc).__name__}: {exc}",
                stdout=_print_collector(),
            )

        # 4) 안전한 로컬 스냅샷 (비직렬화 가능 타입만 보존)
        safe_locals = {
            k: v
            for k, v in local_ns.items()
            if not k.startswith("_") and isinstance(v, (int, float, str, bool, list, dict, tuple, type(None)))
        }

        return SandboxResult(
            success=True,
            return_value=local_ns.get("result"),
            stdout=_print_collector(),
            locals_snapshot=safe_locals,
        )

    def validate_import(self, module_name: str) -> bool:
        """모듈이 샌드박스에서 허용되는지 확인한다."""
        return self._whitelist.is_allowed(module_name)

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _build_globals(self, plugin_id: str, print_collector: Any) -> Dict[str, Any]:
        """제한된 글로벌 네임스페이스를 구성한다."""
        whitelist = self._whitelist

        def _restricted_import(
            name: str,
            globals: Any = None,
            locals: Any = None,
            fromlist: Any = (),
            level: int = 0,
        ) -> Any:
            if not whitelist.is_allowed(name):
                raise SandboxSecurityError(
                    f"Import of '{name}' is not allowed in plugin '{plugin_id}'"
                )
            return builtins.__import__(name, globals, locals, fromlist, level)

        # RestrictedPython safe_builtins 기반 복사
        restricted_builtins = dict(safe_builtins)
        restricted_builtins["__import__"] = _restricted_import
        restricted_builtins["_print_"] = print_collector
        restricted_builtins["_getiter_"] = iter
        # 명시적으로 위험 빌트인 제거
        for dangerous in ("eval", "exec", "compile", "open", "__loader__",
                          "__spec__", "breakpoint", "input"):
            restricted_builtins.pop(dangerous, None)

        globs: Dict[str, Any] = {
            "__builtins__": restricted_builtins,
            "__name__": f"plugin.{plugin_id}",
            "__file__": plugin_id,
            "_getiter_": iter,
            "_getattr_": getattr,
            "_write_": lambda x: x,
            "_inplacevar_": _inplacevar,
            "_iter_unpack_sequence_": guarded_iter_unpack_sequence,
        }
        return globs


def _inplacevar(op: str, x: Any, y: Any) -> Any:
    """RestrictedPython 인플레이스 연산자 핸들러."""
    _ops = {
        "+=": lambda a, b: a + b,
        "-=": lambda a, b: a - b,
        "*=": lambda a, b: a * b,
        "/=": lambda a, b: a / b,
        "//=": lambda a, b: a // b,
        "%=": lambda a, b: a % b,
        "**=": lambda a, b: a ** b,
    }
    fn = _ops.get(op)
    if fn is None:
        raise SandboxSecurityError(f"Unsupported inplace operator: {op}")
    return fn(x, y)
