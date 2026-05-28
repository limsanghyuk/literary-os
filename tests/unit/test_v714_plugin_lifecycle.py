"""
tests/unit/test_v714_plugin_lifecycle.py
V714 SP-D.3 — PluginLifecycleManager 테스트 (33 TC)

ADR-175
"""
import pytest
from literary_system.plugins.plugin_manifest import PluginManifest, PluginPermission
from literary_system.plugins.plugin_registry import PluginRegistry
from literary_system.plugins.plugin_lifecycle import (
    PluginLifecycleManager,
    LifecycleState,
    LifecycleRecord,
)


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _make_manifest(plugin_id: str = "test-plugin", ep: str = "literary_system.core") -> PluginManifest:
    return PluginManifest(
        plugin_id=plugin_id,
        name=f"Plugin {plugin_id}",
        version="1.0.0",
        entry_point=ep,
        permissions=frozenset([PluginPermission.READ_CORPUS]),
    )


def _make_manager(*plugin_ids: str) -> PluginLifecycleManager:
    reg = PluginRegistry()
    for pid in plugin_ids:
        reg.register(_make_manifest(pid))
    return PluginLifecycleManager(registry=reg)


# ===========================================================================
# TestLifecycleBasic  TC01~10
# ===========================================================================

class TestLifecycleBasic:
    """기본 활성화/비활성화/재시작 검증."""

    def test_tc01_activate_returns_active(self):
        lm = _make_manager("plg-one")
        rec = lm.activate("plg-one")
        assert rec.state == LifecycleState.ACTIVE

    def test_tc02_activate_increments_count(self):
        lm = _make_manager("plg-one")
        lm.activate("plg-one")
        rec = lm.activate("plg-one")  # 이미 ACTIVE → 재활성화 없음
        assert rec.activation_count == 1

    def test_tc03_deactivate_returns_inactive(self):
        lm = _make_manager("plg-one")
        lm.activate("plg-one")
        rec = lm.deactivate("plg-one")
        assert rec.state == LifecycleState.INACTIVE

    def test_tc04_deactivate_non_active_is_noop(self):
        lm = _make_manager("plg-one")
        rec = lm.deactivate("plg-one")
        assert rec.state == LifecycleState.INACTIVE

    def test_tc05_restart_reactivates(self):
        lm = _make_manager("plg-one")
        lm.activate("plg-one")
        rec = lm.restart("plg-one")
        assert rec.state == LifecycleState.ACTIVE

    def test_tc06_restart_increments_count(self):
        lm = _make_manager("plg-one")
        lm.activate("plg-one")
        rec = lm.restart("plg-one")
        assert rec.activation_count == 2

    def test_tc07_activate_unknown_plugin_raises(self):
        lm = PluginLifecycleManager()
        with pytest.raises(ValueError, match="not found in registry"):
            lm.activate("ghost-plugin")

    def test_tc08_get_state_returns_none_for_unknown(self):
        lm = PluginLifecycleManager()
        assert lm.get_state("unknown") is None

    def test_tc09_get_state_after_activate(self):
        lm = _make_manager("plg-one")
        lm.activate("plg-one")
        assert lm.get_state("plg-one") == LifecycleState.ACTIVE

    def test_tc10_get_record_returns_lifecycle_record(self):
        lm = _make_manager("plg-one")
        lm.activate("plg-one")
        rec = lm.get_record("plg-one")
        assert isinstance(rec, LifecycleRecord)
        assert rec.is_active


# ===========================================================================
# TestLifecycleError  TC11~18
# ===========================================================================

class TestLifecycleError:
    """오류 상태 검증."""

    def test_tc11_bad_entry_point_causes_error(self):
        reg = PluginRegistry()
        reg.register(_make_manifest("bad-ep", ep="nonexistent.module"))
        lm = PluginLifecycleManager(registry=reg)
        rec = lm.activate("bad-ep")
        assert rec.state == LifecycleState.INACTIVE_ERROR

    def test_tc12_error_record_has_error_message(self):
        reg = PluginRegistry()
        reg.register(_make_manifest("bad-ep", ep="nonexistent.module"))
        lm = PluginLifecycleManager(registry=reg)
        rec = lm.activate("bad-ep")
        assert rec.error is not None
        assert len(rec.error) > 0

    def test_tc13_has_error_property_true_on_error(self):
        reg = PluginRegistry()
        reg.register(_make_manifest("bad-ep", ep="nonexistent.module"))
        lm = PluginLifecycleManager(registry=reg)
        rec = lm.activate("bad-ep")
        assert rec.has_error is True

    def test_tc14_has_error_property_false_on_success(self):
        lm = _make_manager("plg-one")
        rec = lm.activate("plg-one")
        assert rec.has_error is False

    def test_tc15_is_active_false_on_error(self):
        reg = PluginRegistry()
        reg.register(_make_manifest("bad-ep", ep="nonexistent.module"))
        lm = PluginLifecycleManager(registry=reg)
        rec = lm.activate("bad-ep")
        assert rec.is_active is False

    def test_tc16_list_errored_includes_error_plugins(self):
        reg = PluginRegistry()
        reg.register(_make_manifest("bad-ep", ep="nonexistent.module"))
        lm = PluginLifecycleManager(registry=reg)
        lm.activate("bad-ep")
        assert "bad-ep" in lm.list_errored()

    def test_tc17_list_errored_excludes_active(self):
        lm = _make_manager("plg-one")
        lm.activate("plg-one")
        assert "plg-one" not in lm.list_errored()

    def test_tc18_error_does_not_block_other_plugins(self):
        reg = PluginRegistry()
        reg.register(_make_manifest("bad-ep", ep="nonexistent.module"))
        reg.register(_make_manifest("good-p", ep="literary_system.core"))
        lm = PluginLifecycleManager(registry=reg)
        lm.activate("bad-ep")
        rec = lm.activate("good-p")
        assert rec.state == LifecycleState.ACTIVE


# ===========================================================================
# TestLifecycleQuery  TC19~24
# ===========================================================================

class TestLifecycleQuery:
    """조회 API 검증."""

    def test_tc19_list_active_returns_active_ids(self):
        lm = _make_manager("plg-one", "plg-two", "plg-three")
        lm.activate("plg-one")
        lm.activate("plg-two")
        active = lm.list_active()
        assert "plg-one" in active
        assert "plg-two" in active
        assert "plg-three" not in active

    def test_tc20_active_count_correct(self):
        lm = _make_manager("plg-one", "plg-two")
        lm.activate("plg-one")
        assert lm.active_count == 1
        lm.activate("plg-two")
        assert lm.active_count == 2

    def test_tc21_deactivate_reduces_active_count(self):
        lm = _make_manager("plg-one")
        lm.activate("plg-one")
        assert lm.active_count == 1
        lm.deactivate("plg-one")
        assert lm.active_count == 0

    def test_tc22_list_active_empty_initially(self):
        lm = _make_manager("plg-one")
        assert lm.list_active() == []

    def test_tc23_get_record_none_before_any_action(self):
        lm = _make_manager("plg-one")
        assert lm.get_record("plg-one") is None

    def test_tc24_activation_count_zero_before_activate(self):
        lm = _make_manager("plg-one")
        lm.activate("plg-one")
        lm.deactivate("plg-one")
        rec = lm.get_record("plg-one")
        assert rec.activation_count == 1


# ===========================================================================
# TestLifecycleHooks  TC25~33
# ===========================================================================

class TestLifecycleHooks:
    """훅 시스템 검증."""

    def test_tc25_on_activate_hook_called(self):
        lm = _make_manager("plg-one")
        calls = []
        lm.on_activate(lambda pid, manifest: calls.append(pid))
        lm.activate("plg-one")
        assert "plg-one" in calls

    def test_tc26_on_deactivate_hook_called(self):
        lm = _make_manager("plg-one")
        calls = []
        lm.activate("plg-one")
        lm.on_deactivate(lambda pid: calls.append(pid))
        lm.deactivate("plg-one")
        assert "plg-one" in calls

    def test_tc27_on_error_hook_called_on_bad_ep(self):
        reg = PluginRegistry()
        reg.register(_make_manifest("bad-ep2", ep="nonexistent.module"))
        lm = PluginLifecycleManager(registry=reg)
        errors = []
        lm.on_error(lambda pid, exc: errors.append(pid))
        lm.activate("bad-ep2")
        assert "bad-ep2" in errors

    def test_tc28_multiple_hooks_all_called(self):
        lm = _make_manager("plg-one")
        calls = []
        lm.on_activate(lambda pid, m: calls.append("hook1"))
        lm.on_activate(lambda pid, m: calls.append("hook2"))
        lm.activate("plg-one")
        assert "hook1" in calls
        assert "hook2" in calls

    def test_tc29_failing_hook_does_not_abort_activation(self):
        lm = _make_manager("plg-one")
        def bad_hook(pid, m): raise RuntimeError("hook failed")
        lm.on_activate(bad_hook)
        rec = lm.activate("plg-one")
        assert rec.state == LifecycleState.ACTIVE

    def test_tc30_on_activate_receives_manifest(self):
        lm = _make_manager("plg-one")
        manifests = []
        lm.on_activate(lambda pid, m: manifests.append(m))
        lm.activate("plg-one")
        assert len(manifests) == 1
        assert manifests[0].plugin_id == "plg-one"

    def test_tc31_restart_triggers_deactivate_then_activate_hooks(self):
        lm = _make_manager("plg-one")
        deactivate_calls = []
        activate_calls = []
        lm.on_deactivate(lambda pid: deactivate_calls.append(pid))
        lm.on_activate(lambda pid, m: activate_calls.append(pid))
        lm.activate("plg-one")
        lm.restart("plg-one")
        assert deactivate_calls.count("plg-one") >= 1
        assert activate_calls.count("plg-one") == 2  # initial + restart

    def test_tc32_on_error_hook_receives_exception(self):
        reg = PluginRegistry()
        reg.register(_make_manifest("bad-ep2", ep="nonexistent.module"))
        lm = PluginLifecycleManager(registry=reg)
        exceptions = []
        lm.on_error(lambda pid, exc: exceptions.append(exc))
        lm.activate("bad-ep2")
        assert len(exceptions) == 1
        assert isinstance(exceptions[0], Exception)

    def test_tc33_hook_registered_after_activate_not_retro_called(self):
        lm = _make_manager("plg-one")
        lm.activate("plg-one")
        calls = []
        lm.on_activate(lambda pid, m: calls.append(pid))
        # 이미 활성화된 상태에서 재호출 없음 (이미 ACTIVE)
        lm.activate("plg-one")
        assert calls == []  # ACTIVE 상태라 재진입 안 함
