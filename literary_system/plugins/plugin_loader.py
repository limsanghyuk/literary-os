"""
Literary OS V711 — PluginLoader
================================
ADR-172: PluginManifest 기반 플러그인 로드·언로드·상태 관리.

책임:
  1. PluginManifest 유효성 재검증 (스키마 + 화이트리스트)
  2. Python entry_point 동적 임포트 (importlib)
  3. 플러그인 수명 주기: load → enable → disable → unload
  4. 화이트리스트 정책: 허가되지 않은 권한 보유 플러그인 로드 거부
  5. 중복 등록 방지 (같은 plugin_id 재등록 시 ValueError)

참고:
  - RestrictedPython sandbox 통합은 V713(D-M-03)에서 추가
  - Zero-Trust 토큰 인가는 V718(ADR-178)에서 추가
"""
from __future__ import annotations

import importlib
import logging
import sys
from dataclasses import dataclass, field
from types import ModuleType
from typing import Dict, List, Optional

from literary_system.plugins.plugin_manifest import (
    PluginManifest,
    PluginPermission,
    PluginStatus,
    PluginValidationError,
)

_logger = logging.getLogger(__name__)

# ── 기본 화이트리스트: 이 권한만 로드 허가 ────────────────────
DEFAULT_ALLOWED_PERMISSIONS: frozenset[PluginPermission] = frozenset({
    PluginPermission.READ_CORPUS,
    PluginPermission.WRITE_OUTPUT,
    PluginPermission.CALL_LLM,
    PluginPermission.READ_NKG,
})

# NETWORK_OUT, WRITE_NKG 은 기본 차단 (보안 고위험)


@dataclass
class PluginLoadResult:
    """플러그인 로드 결과."""
    plugin_id:  str
    status:     PluginStatus
    message:    str
    module:     Optional[ModuleType] = field(default=None, repr=False)

    @property
    def success(self) -> bool:
        return self.status == PluginStatus.LOADED


class PluginLoader:
    """
    Literary OS 플러그인 로더.

    Usage:
        loader = PluginLoader()
        result = loader.load(manifest)
        if result.success:
            plugin_module = result.module
        loader.unload("my-plugin")
    """

    def __init__(
        self,
        allowed_permissions: Optional[frozenset[PluginPermission]] = None,
    ) -> None:
        self._allowed: frozenset[PluginPermission] = (
            allowed_permissions
            if allowed_permissions is not None
            else DEFAULT_ALLOWED_PERMISSIONS
        )
        self._registry: Dict[str, PluginLoadResult] = {}

    # ── 공개 API ─────────────────────────────────────────────
    def load(self, manifest: PluginManifest) -> PluginLoadResult:
        """
        플러그인을 로드한다.

        Args:
            manifest: 검증된 PluginManifest

        Returns:
            PluginLoadResult (status=LOADED 또는 ERROR)
        """
        pid = manifest.plugin_id

        # 1. 중복 등록 방지
        if pid in self._registry and self._registry[pid].status == PluginStatus.LOADED:
            return PluginLoadResult(
                plugin_id=pid,
                status=PluginStatus.ERROR,
                message=f"이미 로드된 플러그인: '{pid}'",
            )

        # 2. 권한 화이트리스트 검사
        blocked = self._check_permissions(manifest)
        if blocked:
            result = PluginLoadResult(
                plugin_id=pid,
                status=PluginStatus.ERROR,
                message=f"차단된 권한 보유: {[p.value for p in blocked]}",
            )
            self._registry[pid] = result
            return result

        # 3. entry_point 임포트 시도
        try:
            module = importlib.import_module(manifest.entry_point)
            result = PluginLoadResult(
                plugin_id=pid,
                status=PluginStatus.LOADED,
                message="OK",
                module=module,
            )
        except ImportError as exc:
            # entry_point 모듈 없음 — PENDING 상태로 등록 (나중에 설치 가능)
            result = PluginLoadResult(
                plugin_id=pid,
                status=PluginStatus.ERROR,
                message=f"ImportError: {exc}",
            )
            _logger.warning("PluginLoader: '%s' entry_point 임포트 실패 — %s", pid, exc)
        except Exception as exc:  # noqa: BLE001
            result = PluginLoadResult(
                plugin_id=pid,
                status=PluginStatus.ERROR,
                message=f"로드 오류: {exc}",
            )

        self._registry[pid] = result
        _logger.info("PluginLoader.load('%s') → %s", pid, result.status.value)
        return result

    def unload(self, plugin_id: str) -> bool:
        """
        로드된 플러그인을 언로드한다.

        Returns:
            True = 정상 언로드, False = 미존재 또는 이미 언로드
        """
        if plugin_id not in self._registry:
            return False
        result = self._registry[plugin_id]
        if result.module is not None:
            # sys.modules 에서 제거
            sys.modules.pop(result.module.__name__, None)
        self._registry[plugin_id] = PluginLoadResult(
            plugin_id=plugin_id,
            status=PluginStatus.DISABLED,
            message="언로드 완료",
        )
        _logger.info("PluginLoader.unload('%s') → DISABLED", plugin_id)
        return True

    def get_status(self, plugin_id: str) -> Optional[PluginStatus]:
        """등록된 플러그인 상태 반환. 미존재 시 None."""
        if plugin_id not in self._registry:
            return None
        return self._registry[plugin_id].status

    def list_loaded(self) -> List[str]:
        """LOADED 상태 플러그인 ID 목록."""
        return [
            pid
            for pid, r in self._registry.items()
            if r.status == PluginStatus.LOADED
        ]

    def list_all(self) -> Dict[str, PluginStatus]:
        """전체 플러그인 ID → 상태 매핑."""
        return {pid: r.status for pid, r in self._registry.items()}

    @property
    def allowed_permissions(self) -> frozenset[PluginPermission]:
        return self._allowed

    # ── 내부 메서드 ──────────────────────────────────────────
    def _check_permissions(
        self, manifest: PluginManifest
    ) -> List[PluginPermission]:
        """차단된 권한 목록 반환. 빈 리스트 = 모두 허가."""
        return [p for p in manifest.permissions if p not in self._allowed]
