"""
literary_system/plugins/plugin_sdk.py
V715 SP-D.3 — Plugin SDK

플러그인 개발자가 구현해야 하는 기반 추상 클래스(BasePlugin)와
런타임에 주입되는 컨텍스트 객체(PluginContext)를 제공한다.

ADR-176 참조.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, ClassVar, Dict, FrozenSet, List, Optional

from literary_system.plugins.plugin_manifest import PluginManifest, PluginPermission


# ---------------------------------------------------------------------------
# PluginContext — 런타임 실행 컨텍스트
# ---------------------------------------------------------------------------

class PluginContext:
    """
    플러그인 실행 컨텍스트.

    PluginLifecycleManager가 플러그인을 활성화할 때 생성하여 주입한다.
    플러그인은 이 객체를 통해 출력 방출, 권한 조회, 메타데이터 접근을 수행한다.
    """

    def __init__(
        self,
        plugin_id: str,
        permissions: FrozenSet[PluginPermission],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._plugin_id = plugin_id
        self._permissions: FrozenSet[PluginPermission] = frozenset(permissions)
        self._metadata: Dict[str, Any] = dict(metadata or {})
        self._outputs: List[str] = []

    # ------------------------------------------------------------------
    # 출력
    # ------------------------------------------------------------------

    def emit(self, text: str) -> None:
        """플러그인이 텍스트 출력을 방출한다."""
        if not isinstance(text, str):
            raise TypeError(f"emit()은 str만 허용합니다. 받은 타입: {type(text).__name__}")
        self._outputs.append(text)

    def get_outputs(self) -> List[str]:
        """방출된 출력 리스트의 복사본을 반환한다."""
        return list(self._outputs)

    def clear_outputs(self) -> None:
        """방출된 출력을 초기화한다."""
        self._outputs.clear()

    # ------------------------------------------------------------------
    # 권한
    # ------------------------------------------------------------------

    def has_permission(self, perm: PluginPermission) -> bool:
        """주어진 권한이 허용되어 있는지 확인한다."""
        return perm in self._permissions

    def require_permission(self, perm: PluginPermission) -> None:
        """권한이 없으면 PermissionError를 발생시킨다."""
        if not self.has_permission(perm):
            raise PermissionError(
                f"Plugin '{self._plugin_id}' requires permission {perm.value!r} "
                f"but only has: {[p.value for p in self._permissions]}"
            )

    @property
    def permissions(self) -> FrozenSet[PluginPermission]:
        """허용된 권한 집합."""
        return self._permissions

    # ------------------------------------------------------------------
    # 메타데이터
    # ------------------------------------------------------------------

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """메타데이터 값을 반환한다. 키가 없으면 default 반환."""
        return self._metadata.get(key, default)

    def set_metadata(self, key: str, value: Any) -> None:
        """메타데이터를 설정한다."""
        self._metadata[key] = value

    # ------------------------------------------------------------------
    # 속성
    # ------------------------------------------------------------------

    @property
    def plugin_id(self) -> str:
        return self._plugin_id

    def __repr__(self) -> str:
        return (
            f"PluginContext(plugin_id={self._plugin_id!r}, "
            f"permissions={[p.value for p in self._permissions]}, "
            f"outputs={len(self._outputs)})"
        )


# ---------------------------------------------------------------------------
# BasePlugin — 플러그인 추상 기반 클래스
# ---------------------------------------------------------------------------

class PluginSDKError(Exception):
    """Plugin SDK 관련 오류 기반 클래스."""


class MissingManifestError(PluginSDKError):
    """MANIFEST 클래스 변수를 선언하지 않은 플러그인 클래스에서 발생."""


class BasePlugin(ABC):
    """
    Literary OS 플러그인의 기반 추상 클래스.

    플러그인 개발자는 이 클래스를 상속하고 다음을 구현해야 한다:
      1. 클래스 변수 MANIFEST: PluginManifest  (플러그인 메타데이터 선언)
      2. on_activate() → None                  (활성화 시 실행)
      3. on_deactivate() → None                (비활성화 시 실행)

    선택적 오버라이드:
      - on_error(exc)                          (오류 발생 시 처리)

    사용 예:
        class MyPlugin(BasePlugin):
            MANIFEST = PluginManifest(
                plugin_id="my-plugin",
                name="My Plugin",
                version="1.0.0",
                entry_point="my_package.my_plugin.MyPlugin",
            )

            def on_activate(self) -> None:
                self.context.emit("activated!")

            def on_deactivate(self) -> None:
                pass
    """

    # 서브클래스에서 반드시 선언해야 한다.
    MANIFEST: ClassVar[PluginManifest]

    def __init_subclass__(cls, **kwargs: Any) -> None:
        """서브클래스 생성 시 MANIFEST 선언 여부를 검증한다."""
        super().__init_subclass__(**kwargs)
        # ABC 자체는 건너뜀; 구체 서브클래스만 검증
        if not getattr(cls, "__abstractmethods__", None):
            if not isinstance(getattr(cls, "MANIFEST", None), PluginManifest):
                raise MissingManifestError(
                    f"Class {cls.__name__} must declare "
                    f"MANIFEST: PluginManifest as a class variable."
                )

    def __init__(self, context: PluginContext) -> None:
        if not isinstance(context, PluginContext):
            raise TypeError(f"context must be PluginContext, got {type(context).__name__}")
        self._context = context

    # ------------------------------------------------------------------
    # 추상 메서드 (필수 구현)
    # ------------------------------------------------------------------

    @abstractmethod
    def on_activate(self) -> None:
        """플러그인 활성화 시 호출. 초기화 로직을 여기에 작성한다."""

    @abstractmethod
    def on_deactivate(self) -> None:
        """플러그인 비활성화 시 호출. 정리 로직을 여기에 작성한다."""

    # ------------------------------------------------------------------
    # 선택적 오버라이드
    # ------------------------------------------------------------------

    def on_error(self, exc: Exception) -> None:
        """오류 발생 시 호출. 기본 구현은 무시한다."""

    # ------------------------------------------------------------------
    # 속성
    # ------------------------------------------------------------------

    @property
    def context(self) -> PluginContext:
        """런타임 컨텍스트 객체."""
        return self._context

    @property
    def plugin_id(self) -> str:
        """플러그인 ID (MANIFEST.plugin_id)."""
        return self.MANIFEST.plugin_id

    @property
    def manifest(self) -> PluginManifest:
        """플러그인 매니페스트."""
        return self.MANIFEST

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(plugin_id={self.plugin_id!r})"
