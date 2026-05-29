"""
tests/unit/test_v715_plugin_sdk.py
V715 SP-D.3 — Plugin SDK 단위 테스트 (33 TC)

TestPluginContext   (TC01~10): PluginContext 기능 검증
TestBasePlugin      (TC11~22): BasePlugin 서브클래스 동작 검증
TestPluginTestHarness (TC23~33): PluginTestHarness 통합 검증
"""
from __future__ import annotations

import pytest

from literary_system.plugins.plugin_manifest import PluginManifest, PluginPermission
from literary_system.plugins.plugin_sdk import (
    BasePlugin,
    MissingManifestError,
    PluginContext,
    PluginSDKError,
)
from literary_system.plugins.plugin_test_harness import PluginTestHarness


# ===========================================================================
# 테스트용 구체 플러그인 픽스처
# ===========================================================================

def _make_manifest(pid: str = "test-plugin") -> PluginManifest:
    return PluginManifest(
        plugin_id=pid,
        name="Test Plugin",
        version="1.0.0",
        entry_point=f"test_package.{pid.replace('-', '_')}.Plugin",
    )


class GoodPlugin(BasePlugin):
    MANIFEST = _make_manifest("good-plugin")
    activated_count = 0
    deactivated_count = 0
    error_received: list = []

    def on_activate(self) -> None:
        GoodPlugin.activated_count += 1
        self.context.emit("activated")

    def on_deactivate(self) -> None:
        GoodPlugin.deactivated_count += 1

    def on_error(self, exc: Exception) -> None:
        GoodPlugin.error_received.append(exc)


class EmitPlugin(BasePlugin):
    MANIFEST = _make_manifest("emit-plugin")

    def on_activate(self) -> None:
        self.context.emit("hello")
        self.context.emit("world")

    def on_deactivate(self) -> None:
        pass


class ErrorPlugin(BasePlugin):
    MANIFEST = _make_manifest("error-plugin")

    def on_activate(self) -> None:
        raise RuntimeError("activation failed")

    def on_deactivate(self) -> None:
        pass


class PermPlugin(BasePlugin):
    MANIFEST = PluginManifest(
        plugin_id="perm-plugin",
        name="Perm Plugin",
        version="1.0.0",
        entry_point="test_package.perm_plugin.Plugin",
        permissions=[PluginPermission.READ_CORPUS],
    )

    def on_activate(self) -> None:
        self.context.require_permission(PluginPermission.READ_CORPUS)
        self.context.emit("corpus-access-ok")

    def on_deactivate(self) -> None:
        pass


# ===========================================================================
# TestPluginContext (TC01~10)
# ===========================================================================

class TestPluginContext:

    def _ctx(self, permissions=None, metadata=None):
        return PluginContext(
            plugin_id="ctx-test",
            permissions=frozenset(permissions or []),
            metadata=metadata,
        )

    def test_tc01_plugin_id(self):
        ctx = self._ctx()
        assert ctx.plugin_id == "ctx-test"

    def test_tc02_emit_appends_output(self):
        ctx = self._ctx()
        ctx.emit("hello")
        assert ctx.get_outputs() == ["hello"]

    def test_tc03_emit_multiple(self):
        ctx = self._ctx()
        ctx.emit("a")
        ctx.emit("b")
        ctx.emit("c")
        assert ctx.get_outputs() == ["a", "b", "c"]

    def test_tc04_emit_non_str_raises(self):
        ctx = self._ctx()
        with pytest.raises(TypeError):
            ctx.emit(123)  # type: ignore

    def test_tc05_get_outputs_returns_copy(self):
        ctx = self._ctx()
        ctx.emit("x")
        out = ctx.get_outputs()
        out.append("y")  # 외부 수정이 내부에 영향 없어야 함
        assert ctx.get_outputs() == ["x"]

    def test_tc06_clear_outputs(self):
        ctx = self._ctx()
        ctx.emit("a")
        ctx.clear_outputs()
        assert ctx.get_outputs() == []

    def test_tc07_has_permission_true(self):
        ctx = self._ctx(permissions=[PluginPermission.READ_CORPUS])
        assert ctx.has_permission(PluginPermission.READ_CORPUS) is True

    def test_tc08_has_permission_false(self):
        ctx = self._ctx()
        assert ctx.has_permission(PluginPermission.WRITE_OUTPUT) is False

    def test_tc09_require_permission_ok(self):
        ctx = self._ctx(permissions=[PluginPermission.WRITE_OUTPUT])
        ctx.require_permission(PluginPermission.WRITE_OUTPUT)  # raises 없어야 함

    def test_tc10_require_permission_raises(self):
        ctx = self._ctx()
        with pytest.raises(PermissionError):
            ctx.require_permission(PluginPermission.CALL_LLM)


# ===========================================================================
# TestBasePlugin (TC11~22)
# ===========================================================================

class TestBasePlugin:

    def test_tc11_good_plugin_instantiates(self):
        ctx = PluginContext("good-plugin", frozenset())
        plugin = GoodPlugin(ctx)
        assert plugin.plugin_id == "good-plugin"

    def test_tc12_manifest_accessible(self):
        ctx = PluginContext("good-plugin", frozenset())
        plugin = GoodPlugin(ctx)
        assert plugin.manifest.plugin_id == "good-plugin"
        assert plugin.manifest.name == "Test Plugin"

    def test_tc13_on_activate_called(self):
        GoodPlugin.activated_count = 0
        ctx = PluginContext("good-plugin", frozenset())
        plugin = GoodPlugin(ctx)
        plugin.on_activate()
        assert GoodPlugin.activated_count == 1

    def test_tc14_on_activate_emits_output(self):
        ctx = PluginContext("good-plugin", frozenset())
        plugin = GoodPlugin(ctx)
        plugin.on_activate()
        assert "activated" in ctx.get_outputs()

    def test_tc15_on_deactivate_called(self):
        GoodPlugin.deactivated_count = 0
        ctx = PluginContext("good-plugin", frozenset())
        plugin = GoodPlugin(ctx)
        plugin.on_deactivate()
        assert GoodPlugin.deactivated_count == 1

    def test_tc16_on_error_receives_exception(self):
        GoodPlugin.error_received = []
        ctx = PluginContext("good-plugin", frozenset())
        plugin = GoodPlugin(ctx)
        exc = ValueError("test error")
        plugin.on_error(exc)
        assert exc in GoodPlugin.error_received

    def test_tc17_base_on_error_default_no_raise(self):
        """BasePlugin.on_error 기본 구현은 예외를 발생시키지 않는다."""
        ctx = PluginContext("emit-plugin", frozenset())
        plugin = EmitPlugin(ctx)
        plugin.on_error(RuntimeError("ignored"))  # raises 없어야 함

    def test_tc18_context_property(self):
        ctx = PluginContext("good-plugin", frozenset())
        plugin = GoodPlugin(ctx)
        assert plugin.context is ctx

    def test_tc19_wrong_context_type_raises(self):
        with pytest.raises(TypeError):
            GoodPlugin("not-a-context")  # type: ignore

    def test_tc20_missing_manifest_raises_on_class_creation(self):
        with pytest.raises(MissingManifestError):
            class BadPlugin(BasePlugin):
                # MANIFEST 선언 없음
                def on_activate(self): pass
                def on_deactivate(self): pass

    def test_tc21_wrong_manifest_type_raises(self):
        with pytest.raises(MissingManifestError):
            class BadPlugin2(BasePlugin):
                MANIFEST = "not-a-manifest"
                def on_activate(self): pass
                def on_deactivate(self): pass

    def test_tc22_repr_includes_plugin_id(self):
        ctx = PluginContext("good-plugin", frozenset())
        plugin = GoodPlugin(ctx)
        assert "good-plugin" in repr(plugin)


# ===========================================================================
# TestPluginTestHarness (TC23~33)
# ===========================================================================

class TestPluginTestHarness:

    def setup_method(self):
        GoodPlugin.activated_count = 0
        GoodPlugin.deactivated_count = 0
        GoodPlugin.error_received = []

    def test_tc23_harness_activate_returns_plugin(self):
        harness = PluginTestHarness(GoodPlugin)
        plugin = harness.activate()
        assert isinstance(plugin, GoodPlugin)

    def test_tc24_harness_is_activated_after_activate(self):
        harness = PluginTestHarness(GoodPlugin)
        harness.activate()
        assert harness.is_activated is True

    def test_tc25_harness_outputs_capture(self):
        harness = PluginTestHarness(EmitPlugin)
        harness.activate()
        assert harness.outputs == ["hello", "world"]

    def test_tc26_harness_deactivate(self):
        harness = PluginTestHarness(GoodPlugin)
        harness.activate()
        harness.deactivate()
        assert harness.is_activated is False

    def test_tc27_harness_last_error_on_failure(self):
        harness = PluginTestHarness(ErrorPlugin)
        harness.activate()
        assert isinstance(harness.last_error, RuntimeError)
        assert "activation failed" in str(harness.last_error)

    def test_tc28_harness_not_activated_on_error(self):
        harness = PluginTestHarness(ErrorPlugin)
        harness.activate()
        assert harness.is_activated is False

    def test_tc29_harness_reset_clears_state(self):
        harness = PluginTestHarness(GoodPlugin)
        harness.activate()
        harness.reset()
        assert harness.plugin is None
        assert harness.context is None
        assert harness.is_activated is False

    def test_tc30_harness_permissions_injected(self):
        harness = PluginTestHarness(
            PermPlugin,
            permissions=frozenset([PluginPermission.READ_CORPUS])
        )
        harness.activate()
        assert harness.last_error is None
        assert "corpus-access-ok" in harness.outputs

    def test_tc31_harness_permission_denied_triggers_error(self):
        # PermPlugin은 READ_CORPUS 필요 — 권한 없이 activate()
        harness = PluginTestHarness(PermPlugin, permissions=frozenset())
        harness.activate()
        assert isinstance(harness.last_error, PermissionError)

    def test_tc32_harness_sandbox_execution(self):
        harness = PluginTestHarness(GoodPlugin)
        result = harness.run_in_sandbox("result = 2 + 3")
        assert result.success is True
        assert result.return_value == 5

    def test_tc33_harness_manifest_property(self):
        harness = PluginTestHarness(GoodPlugin)
        assert harness.manifest.plugin_id == "good-plugin"
