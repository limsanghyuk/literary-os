"""
literary_system/plugins/plugin_test_harness.py
V715 SP-D.3 — Plugin Test Harness

플러그인을 격리 환경에서 단위 테스트할 수 있는 헬퍼 클래스.
실제 PluginRegistry / PluginLifecycleManager 없이 플러그인 로직을 검증한다.

ADR-176 참조.
"""
from __future__ import annotations

from typing import Any, Dict, FrozenSet, List, Optional, Type

from literary_system.plugins.plugin_manifest import PluginManifest, PluginPermission
from literary_system.plugins.plugin_sandbox import PluginSandbox, SandboxResult
from literary_system.plugins.plugin_sdk import BasePlugin, PluginContext
from literary_system.plugins.plugin_whitelist import PluginWhitelist


# ---------------------------------------------------------------------------
# PluginTestHarness
# ---------------------------------------------------------------------------

class PluginTestHarness:
    """
    플러그인을 격리된 환경에서 테스트하는 헬퍼.

    사용 예:
        harness = PluginTestHarness(MyPlugin, permissions={PluginPermission.READ_CORPUS})
        plugin = harness.activate()
        assert harness.outputs == ["activated!"]
        harness.deactivate()
    """

    def __init__(
        self,
        plugin_class: Type[BasePlugin],
        permissions: Optional[FrozenSet[PluginPermission]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        whitelist: Optional[PluginWhitelist] = None,
    ) -> None:
        if not (isinstance(plugin_class, type) and issubclass(plugin_class, BasePlugin)):
            raise TypeError(f"plugin_class must be a BasePlugin subclass, got {plugin_class!r}")

        self._plugin_class = plugin_class
        self._permissions: FrozenSet[PluginPermission] = frozenset(permissions or set())
        self._metadata: Dict[str, Any] = dict(metadata or {})
        self._whitelist = whitelist or PluginWhitelist()
        self._sandbox = PluginSandbox(whitelist=self._whitelist)

        self._context: Optional[PluginContext] = None
        self._plugin: Optional[BasePlugin] = None
        self._last_error: Optional[Exception] = None
        self._activated = False

    # ------------------------------------------------------------------
    # 생명주기
    # ------------------------------------------------------------------

    def build_context(self) -> PluginContext:
        """테스트용 PluginContext를 새로 생성한다."""
        manifest = self._plugin_class.MANIFEST
        return PluginContext(
            plugin_id=manifest.plugin_id,
            permissions=self._permissions,
            metadata=self._metadata,
        )

    def activate(self) -> BasePlugin:
        """
        플러그인을 활성화한다.

        1. PluginContext 생성
        2. 플러그인 인스턴스 생성
        3. on_activate() 호출
        4. 인스턴스 반환
        """
        self._context = self.build_context()
        self._plugin = self._plugin_class(self._context)
        self._last_error = None
        try:
            self._plugin.on_activate()
            self._activated = True
        except Exception as exc:  # noqa: BLE001
            self._last_error = exc
            self._plugin.on_error(exc)
            self._activated = False
        return self._plugin

    def deactivate(self) -> None:
        """플러그인을 비활성화한다 (on_deactivate 호출)."""
        if self._plugin is not None:
            try:
                self._plugin.on_deactivate()
            except Exception as exc:  # noqa: BLE001
                self._last_error = exc
            finally:
                self._activated = False

    def reset(self) -> None:
        """하네스 상태를 초기화한다 (새 테스트 케이스 시작 전 사용)."""
        self._context = None
        self._plugin = None
        self._last_error = None
        self._activated = False

    # ------------------------------------------------------------------
    # 샌드박스 실행
    # ------------------------------------------------------------------

    def run_in_sandbox(self, code: str) -> SandboxResult:
        """
        코드를 격리 샌드박스에서 실행한다.
        PluginSandbox를 직접 사용하며 플러그인 ID를 컨텍스트로 전달한다.
        """
        pid = self._plugin_class.MANIFEST.plugin_id if hasattr(self._plugin_class, "MANIFEST") else "<harness>"
        return self._sandbox.execute(code, plugin_id=pid)

    # ------------------------------------------------------------------
    # 조회 속성
    # ------------------------------------------------------------------

    @property
    def outputs(self) -> List[str]:
        """현재 컨텍스트의 방출된 출력 리스트."""
        if self._context is None:
            return []
        return self._context.get_outputs()

    @property
    def last_error(self) -> Optional[Exception]:
        """마지막으로 발생한 예외. 없으면 None."""
        return self._last_error

    @property
    def is_activated(self) -> bool:
        """플러그인이 활성화 상태인지 여부."""
        return self._activated

    @property
    def plugin(self) -> Optional[BasePlugin]:
        """현재 플러그인 인스턴스. activate() 전이면 None."""
        return self._plugin

    @property
    def context(self) -> Optional[PluginContext]:
        """현재 PluginContext. activate() 전이면 None."""
        return self._context

    @property
    def manifest(self) -> PluginManifest:
        """플러그인의 MANIFEST."""
        return self._plugin_class.MANIFEST

    def __repr__(self) -> str:
        return (
            f"PluginTestHarness("
            f"plugin={self._plugin_class.__name__!r}, "
            f"activated={self._activated})"
        )
