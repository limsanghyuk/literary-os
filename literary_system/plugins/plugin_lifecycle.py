"""
literary_system/plugins/plugin_lifecycle.py
V714 SP-D.3 — Plugin Lifecycle Management

플러그인의 활성화(activate) / 비활성화(deactivate) / 재시작(restart) 생명주기를 관리.
PluginRegistry + PluginSandbox 와 통합되며 훅 시스템을 제공한다.

ADR-175 참조.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable, Dict, List, Optional

from literary_system.plugins.plugin_manifest import PluginManifest, PluginStatus
from literary_system.plugins.plugin_registry import PluginRegistry, RegistryEntry
from literary_system.plugins.plugin_sandbox import PluginSandbox, SandboxResult


# ---------------------------------------------------------------------------
# 생명주기 상태
# ---------------------------------------------------------------------------

class LifecycleState(str, Enum):
    """플러그인 생명주기 상태."""
    INACTIVE   = "inactive"    # 등록만 됨, 활성화 전
    ACTIVATING = "activating"  # 활성화 중
    ACTIVE     = "active"      # 활성화 완료
    DEACTIVATING = "deactivating"
    INACTIVE_ERROR = "inactive_error"  # 오류로 비활성화됨
    RESTARTING = "restarting"


# ---------------------------------------------------------------------------
# 훅 타입
# ---------------------------------------------------------------------------

OnActivateHook   = Callable[[str, PluginManifest], None]
OnDeactivateHook = Callable[[str], None]
OnErrorHook      = Callable[[str, Exception], None]


# ---------------------------------------------------------------------------
# 생명주기 레코드
# ---------------------------------------------------------------------------

@dataclass
class LifecycleRecord:
    """단일 플러그인의 생명주기 상태 레코드."""
    plugin_id: str
    state: LifecycleState = LifecycleState.INACTIVE
    error: Optional[str] = None
    activation_count: int = 0     # 누적 활성화 횟수
    last_result: Optional[SandboxResult] = None

    @property
    def is_active(self) -> bool:
        return self.state == LifecycleState.ACTIVE

    @property
    def has_error(self) -> bool:
        return self.state == LifecycleState.INACTIVE_ERROR


# ---------------------------------------------------------------------------
# PluginLifecycleManager
# ---------------------------------------------------------------------------

class PluginLifecycleManager:
    """
    플러그인 생명주기 관리자.

    - activate(plugin_id): INACTIVE → ACTIVATING → ACTIVE
    - deactivate(plugin_id): ACTIVE → DEACTIVATING → INACTIVE
    - restart(plugin_id): ACTIVE → deactivate → activate
    - 각 전환마다 등록된 훅 콜백이 호출된다.
    - 훅 실패는 로그만 남기고 전환은 계속된다.
    """

    def __init__(
        self,
        registry: Optional[PluginRegistry] = None,
        sandbox: Optional[PluginSandbox] = None,
    ) -> None:
        self._registry = registry or PluginRegistry()
        self._sandbox  = sandbox  or PluginSandbox()
        self._records:  Dict[str, LifecycleRecord] = {}
        self._on_activate:   List[OnActivateHook]   = []
        self._on_deactivate: List[OnDeactivateHook] = []
        self._on_error:      List[OnErrorHook]       = []

    # ------------------------------------------------------------------
    # 생명주기 제어
    # ------------------------------------------------------------------

    def activate(self, plugin_id: str) -> LifecycleRecord:
        """
        플러그인을 활성화한다.

        - PluginRegistry에 등록되지 않은 플러그인은 ValueError.
        - 이미 ACTIVE이면 재활성화 없이 현재 레코드 반환.
        - 활성화 오류 시 INACTIVE_ERROR 상태로 전환.
        """
        entry = self._registry.get(plugin_id)
        if entry is None:
            raise ValueError(f"Plugin '{plugin_id}' not found in registry")

        rec = self._get_or_create_record(plugin_id)

        if rec.state == LifecycleState.ACTIVE:
            return rec

        rec.state = LifecycleState.ACTIVATING
        try:
            # 엔트리포인트 모듈 임포트 검증
            import importlib
            ep = entry.manifest.entry_point
            top_module = ep.split(".")[0]
            try:
                importlib.import_module(top_module)
            except ImportError as imp_exc:
                raise RuntimeError(
                    f"Entry point module '{top_module}' cannot be imported: {imp_exc}"
                ) from imp_exc

            rec.state = LifecycleState.ACTIVE
            rec.activation_count += 1
            rec.error = None
            self._fire_activate_hooks(plugin_id, entry.manifest)

        except Exception as exc:  # noqa: BLE001
            rec.state = LifecycleState.INACTIVE_ERROR
            rec.error = str(exc)
            self._fire_error_hooks(plugin_id, exc)

        return rec

    def deactivate(self, plugin_id: str) -> LifecycleRecord:
        """
        플러그인을 비활성화한다.

        - ACTIVE가 아니면 현재 레코드를 그대로 반환.
        """
        rec = self._get_or_create_record(plugin_id)
        if rec.state != LifecycleState.ACTIVE:
            return rec

        rec.state = LifecycleState.DEACTIVATING
        try:
            self._fire_deactivate_hooks(plugin_id)
        except Exception:  # noqa: BLE001
            pass  # 훅 실패는 비활성화를 막지 않음

        rec.state = LifecycleState.INACTIVE
        return rec

    def restart(self, plugin_id: str) -> LifecycleRecord:
        """플러그인을 재시작한다 (deactivate → activate).

        deactivate를 먼저 실행해 훅이 정상 호출된 뒤 RESTARTING 상태로 전환한다.
        """
        rec = self._get_or_create_record(plugin_id)
        self.deactivate(plugin_id)          # ACTIVE → DEACTIVATING → INACTIVE (훅 실행)
        rec.state = LifecycleState.RESTARTING
        return self.activate(plugin_id)

    # ------------------------------------------------------------------
    # 조회
    # ------------------------------------------------------------------

    def get_state(self, plugin_id: str) -> Optional[LifecycleState]:
        rec = self._records.get(plugin_id)
        return rec.state if rec else None

    def list_active(self) -> List[str]:
        return [pid for pid, rec in self._records.items() if rec.is_active]

    def list_errored(self) -> List[str]:
        return [pid for pid, rec in self._records.items() if rec.has_error]

    def get_record(self, plugin_id: str) -> Optional[LifecycleRecord]:
        return self._records.get(plugin_id)

    @property
    def active_count(self) -> int:
        return sum(1 for r in self._records.values() if r.is_active)

    # ------------------------------------------------------------------
    # 훅 등록
    # ------------------------------------------------------------------

    def on_activate(self, hook: OnActivateHook) -> None:
        self._on_activate.append(hook)

    def on_deactivate(self, hook: OnDeactivateHook) -> None:
        self._on_deactivate.append(hook)

    def on_error(self, hook: OnErrorHook) -> None:
        self._on_error.append(hook)

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _get_or_create_record(self, plugin_id: str) -> LifecycleRecord:
        if plugin_id not in self._records:
            self._records[plugin_id] = LifecycleRecord(plugin_id=plugin_id)
        return self._records[plugin_id]

    def _fire_activate_hooks(self, plugin_id: str, manifest: PluginManifest) -> None:
        for hook in self._on_activate:
            try:
                hook(plugin_id, manifest)
            except Exception:  # noqa: BLE001
                pass

    def _fire_deactivate_hooks(self, plugin_id: str) -> None:
        for hook in self._on_deactivate:
            try:
                hook(plugin_id)
            except Exception:  # noqa: BLE001
                pass

    def _fire_error_hooks(self, plugin_id: str, exc: Exception) -> None:
        for hook in self._on_error:
            try:
                hook(plugin_id, exc)
            except Exception:  # noqa: BLE001
                pass
