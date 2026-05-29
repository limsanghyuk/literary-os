"""
Literary OS V712 — PluginRegistry
===================================
ADR-173: 플러그인 등록·조회·탐색 핵심 레지스트리.

책임:
  1. PluginManifest 등록/해제/조회
  2. 태그 기반 필터 조회
  3. 권한 기반 필터 조회
  4. 중복 ID 등록 방지 (덮어쓰기 금지, overwrite=True 명시 필요)
  5. 이벤트 훅: on_register / on_unregister (콜백 리스트)

의존성:
  - PluginManifest / PluginPermission (V711)
  - PluginLoader (V711) — register 시 자동 로드 옵션
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from literary_system.plugins.plugin_manifest import (
    PluginManifest,
    PluginPermission,
    PluginStatus,
)
from literary_system.plugins.plugin_loader import PluginLoader, PluginLoadResult

_logger = logging.getLogger(__name__)

OnRegisterHook   = Callable[[PluginManifest], None]
OnUnregisterHook = Callable[[str], None]


@dataclass
class RegistryEntry:
    """레지스트리 내 단일 플러그인 항목."""
    manifest:    PluginManifest
    load_result: Optional[PluginLoadResult] = None

    @property
    def plugin_id(self) -> str:
        return self.manifest.plugin_id

    @property
    def is_loaded(self) -> bool:
        return (
            self.load_result is not None
            and self.load_result.status == PluginStatus.LOADED
        )


class PluginRegistry:
    """
    Literary OS 플러그인 레지스트리.

    Usage:
        registry = PluginRegistry()
        registry.register(manifest)
        entries = registry.query_by_tag("romance")
        registry.unregister("romance-plugin")
    """

    def __init__(
        self,
        loader: Optional[PluginLoader] = None,
        auto_load: bool = False,
    ) -> None:
        """
        Args:
            loader:    PluginLoader 인스턴스 (None 이면 내부 생성)
            auto_load: True 이면 register 시 자동으로 loader.load() 호출
        """
        self._loader: PluginLoader = loader if loader is not None else PluginLoader()
        self._auto_load: bool = auto_load
        self._entries: Dict[str, RegistryEntry] = {}
        self._on_register:   List[OnRegisterHook]   = []
        self._on_unregister: List[OnUnregisterHook] = []

    # ── 등록 API ─────────────────────────────────────────────
    def register(
        self,
        manifest: PluginManifest,
        overwrite: bool = False,
    ) -> RegistryEntry:
        """
        플러그인을 레지스트리에 등록한다.

        Args:
            manifest:  등록할 PluginManifest
            overwrite: 기존 항목 덮어쓰기 허용 여부

        Returns:
            RegistryEntry

        Raises:
            ValueError: 중복 등록 시 overwrite=False
        """
        pid = manifest.plugin_id
        if pid in self._entries and not overwrite:
            raise ValueError(
                f"플러그인 '{pid}' 이미 등록됨. overwrite=True 로 재등록 가능."
            )

        load_result: Optional[PluginLoadResult] = None
        if self._auto_load:
            load_result = self._loader.load(manifest)

        entry = RegistryEntry(manifest=manifest, load_result=load_result)
        self._entries[pid] = entry

        for hook in self._on_register:
            hook(manifest)

        _logger.info("PluginRegistry.register('%s') auto_load=%s", pid, self._auto_load)
        return entry

    def unregister(self, plugin_id: str) -> bool:
        """
        플러그인을 레지스트리에서 제거하고 언로드한다.

        Returns:
            True = 정상 제거, False = 미존재
        """
        if plugin_id not in self._entries:
            return False
        self._loader.unload(plugin_id)
        del self._entries[plugin_id]
        for hook in self._on_unregister:
            hook(plugin_id)
        _logger.info("PluginRegistry.unregister('%s')", plugin_id)
        return True

    # ── 조회 API ─────────────────────────────────────────────
    def get(self, plugin_id: str) -> Optional[RegistryEntry]:
        """plugin_id 로 항목 조회. 미존재 시 None."""
        return self._entries.get(plugin_id)

    def list_all(self) -> List[RegistryEntry]:
        """전체 등록 항목 리스트."""
        return list(self._entries.values())

    def query_by_tag(self, tag: str) -> List[RegistryEntry]:
        """태그가 포함된 플러그인 목록."""
        return [e for e in self._entries.values() if tag in e.manifest.tags]

    def query_by_permission(
        self, permission: PluginPermission
    ) -> List[RegistryEntry]:
        """특정 권한을 가진 플러그인 목록."""
        return [
            e
            for e in self._entries.values()
            if e.manifest.has_permission(permission)
        ]

    def query_loaded(self) -> List[RegistryEntry]:
        """LOADED 상태 플러그인 목록."""
        return [e for e in self._entries.values() if e.is_loaded]

    # ── 이벤트 훅 ────────────────────────────────────────────
    def on_register(self, hook: OnRegisterHook) -> None:
        self._on_register.append(hook)

    def on_unregister(self, hook: OnUnregisterHook) -> None:
        self._on_unregister.append(hook)

    # ── 통계 ─────────────────────────────────────────────────
    @property
    def count(self) -> int:
        return len(self._entries)

    @property
    def loader(self) -> PluginLoader:
        return self._loader
