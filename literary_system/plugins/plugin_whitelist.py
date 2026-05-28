"""
literary_system/plugins/plugin_whitelist.py
V713 SP-D.3 — Plugin Whitelist

허용 모듈 목록 관리. 플러그인이 import 할 수 있는 모듈을 화이트리스트로 제한한다.

ADR-174 참조.
"""
from __future__ import annotations

from typing import FrozenSet, Set, Optional

# ---------------------------------------------------------------------------
# 기본 화이트리스트
# ---------------------------------------------------------------------------

#: 모든 플러그인에 항상 허용되는 표준 라이브러리 모듈
DEFAULT_ALLOWED_MODULES: FrozenSet[str] = frozenset(
    {
        "builtins", "math", "random", "re", "string", "datetime",
        "collections", "itertools", "functools", "operator", "typing",
        "abc", "enum", "dataclasses", "json", "copy", "textwrap",
        "unicodedata", "hashlib", "hmac", "base64", "struct", "io",
        "os.path", "pathlib", "logging", "warnings", "traceback",
        "contextlib",
    }
)

#: 항상 차단되는 위험 모듈
BLOCKED_MODULES: FrozenSet[str] = frozenset(
    {
        "os", "sys", "subprocess", "socket", "shutil", "pickle", "marshal",
        "ctypes", "importlib", "importlib.util", "multiprocessing",
        "threading", "concurrent", "asyncio", "signal", "gc", "weakref",
        "inspect", "ast", "dis", "code", "codeop", "pty", "tty",
        "rlcompleter", "urllib", "http", "ftplib", "smtplib", "imaplib",
        "xmlrpc",
    }
)


class PluginWhitelist:
    """
    플러그인이 import 할 수 있는 모듈 목록을 관리한다.

    - 기본 허용 목록(DEFAULT_ALLOWED_MODULES)에서 시작.
    - 추가 허용/추가 차단을 동적으로 설정 가능.
    - is_allowed()는 항상 BLOCKED_MODULES를 먼저 확인한다.
    """

    def __init__(
        self,
        extra_allowed: Optional[Set[str]] = None,
        extra_blocked: Optional[Set[str]] = None,
    ) -> None:
        self._allowed: Set[str] = set(DEFAULT_ALLOWED_MODULES)
        if extra_allowed:
            self._allowed.update(extra_allowed)
        self._extra_blocked: Set[str] = set(extra_blocked) if extra_blocked else set()

    def allow(self, module_name: str) -> None:
        """모듈을 허용 목록에 추가. BLOCKED_MODULES에 있으면 ValueError."""
        if module_name in BLOCKED_MODULES:
            raise ValueError(
                f"Module '{module_name}' is in the immutable blocked list and cannot be allowed."
            )
        self._allowed.add(module_name)

    def block(self, module_name: str) -> None:
        """모듈을 추가 차단 목록에 넣는다."""
        self._allowed.discard(module_name)
        self._extra_blocked.add(module_name)

    def is_allowed(self, module_name: str) -> bool:
        """모듈 허용 여부를 반환한다."""
        if module_name in BLOCKED_MODULES or module_name in self._extra_blocked:
            return False
        if module_name in self._allowed:
            return True
        # 부모 패키지 검사
        parts = module_name.split(".")
        for i in range(len(parts) - 1, 0, -1):
            parent = ".".join(parts[:i])
            if parent in self._allowed:
                return True
        return False

    def allowed_modules(self) -> FrozenSet[str]:
        return frozenset(self._allowed)

    def blocked_modules(self) -> FrozenSet[str]:
        return frozenset(BLOCKED_MODULES | self._extra_blocked)
