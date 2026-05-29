"""
V712 SP-D.3: PluginRegistry 단위 테스트 (ADR-173)
=================================================
목표: 33 TC PASS
커버리지:
  - PluginRegistry: register / unregister / get / list_all
  - query_by_tag / query_by_permission / query_loaded
  - 중복 등록 방지 + overwrite=True
  - 이벤트 훅 on_register / on_unregister
  - auto_load 옵션
  - count / loader 프로퍼티
  - RegistryEntry.is_loaded
"""
from __future__ import annotations

import pytest

from literary_system.plugins.plugin_manifest import (
    PluginManifest,
    PluginPermission,
    PluginStatus,
)
from literary_system.plugins.plugin_loader import PluginLoader
from literary_system.plugins.plugin_registry import PluginRegistry, RegistryEntry


# ── 헬퍼 ────────────────────────────────────────────────────
def _make(pid: str, tags: list = [], perms: list = []) -> PluginManifest:
    return PluginManifest(
        plugin_id=pid,
        name=pid.replace("-", " ").title(),
        version="1.0.0",
        entry_point="literary_system.core",
        tags=tags,
        permissions=perms,
    )


# ═══════════════════════════════════════════════════════════════
# TC01~TC08: 기본 register / unregister / get
# ═══════════════════════════════════════════════════════════════
class TestRegistryBasic:
    def test_tc01_register_returns_entry(self) -> None:
        reg = PluginRegistry()
        e = reg.register(_make("plugin-alpha"))
        assert isinstance(e, RegistryEntry)

    def test_tc02_count_increments(self) -> None:
        reg = PluginRegistry()
        assert reg.count == 0
        reg.register(_make("plugin-a"))
        assert reg.count == 1

    def test_tc03_get_returns_entry(self) -> None:
        reg = PluginRegistry()
        reg.register(_make("plugin-b"))
        e = reg.get("plugin-b")
        assert e is not None
        assert e.plugin_id == "plugin-b"

    def test_tc04_get_missing_returns_none(self) -> None:
        reg = PluginRegistry()
        assert reg.get("no-such-plugin") is None

    def test_tc05_unregister_existing(self) -> None:
        reg = PluginRegistry()
        reg.register(_make("plugin-c"))
        ok = reg.unregister("plugin-c")
        assert ok is True
        assert reg.get("plugin-c") is None

    def test_tc06_unregister_missing_returns_false(self) -> None:
        reg = PluginRegistry()
        assert reg.unregister("ghost") is False

    def test_tc07_list_all_empty(self) -> None:
        reg = PluginRegistry()
        assert reg.list_all() == []

    def test_tc08_list_all_populated(self) -> None:
        reg = PluginRegistry()
        reg.register(_make("plugin-x"))
        reg.register(_make("plugin-y"))
        ids = {e.plugin_id for e in reg.list_all()}
        assert ids == {"plugin-x", "plugin-y"}


# ═══════════════════════════════════════════════════════════════
# TC09~TC14: 중복 등록 방지 + overwrite
# ═══════════════════════════════════════════════════════════════
class TestRegistryDuplicate:
    def test_tc09_duplicate_raises_valueerror(self) -> None:
        reg = PluginRegistry()
        reg.register(_make("dup-plugin"))
        with pytest.raises(ValueError, match="이미 등록됨"):
            reg.register(_make("dup-plugin"))

    def test_tc10_overwrite_true_succeeds(self) -> None:
        reg = PluginRegistry()
        reg.register(_make("over-plugin"))
        reg.register(_make("over-plugin"), overwrite=True)
        assert reg.count == 1

    def test_tc11_count_stable_after_overwrite(self) -> None:
        reg = PluginRegistry()
        reg.register(_make("stable-plugin"))
        reg.register(_make("stable-plugin"), overwrite=True)
        assert reg.count == 1

    def test_tc12_register_multiple_different(self) -> None:
        reg = PluginRegistry()
        for i in range(5):
            reg.register(_make(f"plugin-{i:02d}"))
        assert reg.count == 5

    def test_tc13_unregister_then_reregister(self) -> None:
        reg = PluginRegistry()
        reg.register(_make("reuse-plugin"))
        reg.unregister("reuse-plugin")
        reg.register(_make("reuse-plugin"))
        assert reg.count == 1

    def test_tc14_entry_manifest_preserved(self) -> None:
        reg = PluginRegistry()
        m = _make("manifest-check", tags=["drama"])
        reg.register(m)
        e = reg.get("manifest-check")
        assert e is not None
        assert "drama" in e.manifest.tags


# ═══════════════════════════════════════════════════════════════
# TC15~TC22: query API
# ═══════════════════════════════════════════════════════════════
class TestRegistryQuery:
    def test_tc15_query_by_tag_found(self) -> None:
        reg = PluginRegistry()
        reg.register(_make("drama-genre", tags=["drama", "romance"]))
        reg.register(_make("sci-fi-genre", tags=["sci-fi"]))
        results = reg.query_by_tag("drama")
        assert len(results) == 1
        assert results[0].plugin_id == "drama-genre"

    def test_tc16_query_by_tag_not_found(self) -> None:
        reg = PluginRegistry()
        reg.register(_make("no-tag-plugin"))
        assert reg.query_by_tag("mystery") == []

    def test_tc17_query_by_tag_multiple(self) -> None:
        reg = PluginRegistry()
        for i in range(3):
            reg.register(_make(f"tagged-{i}", tags=["shared"]))
        assert len(reg.query_by_tag("shared")) == 3

    def test_tc18_query_by_permission_found(self) -> None:
        reg = PluginRegistry()
        reg.register(_make("llm-plugin", perms=[PluginPermission.CALL_LLM]))
        reg.register(_make("read-plugin", perms=[PluginPermission.READ_CORPUS]))
        result = reg.query_by_permission(PluginPermission.CALL_LLM)
        assert len(result) == 1
        assert result[0].plugin_id == "llm-plugin"

    def test_tc19_query_by_permission_empty(self) -> None:
        reg = PluginRegistry()
        reg.register(_make("no-perm"))
        assert reg.query_by_permission(PluginPermission.WRITE_NKG) == []

    def test_tc20_query_loaded_empty_without_auto_load(self) -> None:
        reg = PluginRegistry(auto_load=False)
        reg.register(_make("not-loaded"))
        assert reg.query_loaded() == []

    def test_tc21_query_loaded_with_auto_load(self) -> None:
        reg = PluginRegistry(auto_load=True)
        reg.register(_make("auto-loaded-plugin"))
        loaded = reg.query_loaded()
        # literary_system.core 은 존재하므로 LOADED 상태
        assert len(loaded) >= 1

    def test_tc22_entry_is_loaded_false_without_auto_load(self) -> None:
        reg = PluginRegistry(auto_load=False)
        reg.register(_make("unloaded-check"))
        e = reg.get("unloaded-check")
        assert e is not None
        assert e.is_loaded is False


# ═══════════════════════════════════════════════════════════════
# TC23~TC28: 이벤트 훅
# ═══════════════════════════════════════════════════════════════
class TestRegistryHooks:
    def test_tc23_on_register_hook_called(self) -> None:
        reg = PluginRegistry()
        called: list = []
        reg.on_register(lambda m: called.append(m.plugin_id))
        reg.register(_make("hook-plugin"))
        assert "hook-plugin" in called

    def test_tc24_on_unregister_hook_called(self) -> None:
        reg = PluginRegistry()
        removed: list = []
        reg.on_unregister(lambda pid: removed.append(pid))
        reg.register(_make("hook-remove"))
        reg.unregister("hook-remove")
        assert "hook-remove" in removed

    def test_tc25_multiple_hooks_all_called(self) -> None:
        reg = PluginRegistry()
        log: list = []
        reg.on_register(lambda m: log.append(f"A:{m.plugin_id}"))
        reg.on_register(lambda m: log.append(f"B:{m.plugin_id}"))
        reg.register(_make("multi-hook"))
        assert "A:multi-hook" in log
        assert "B:multi-hook" in log

    def test_tc26_hook_not_called_on_failed_unregister(self) -> None:
        reg = PluginRegistry()
        removed: list = []
        reg.on_unregister(lambda pid: removed.append(pid))
        reg.unregister("nonexistent")
        assert removed == []

    def test_tc27_loader_property_accessible(self) -> None:
        loader = PluginLoader()
        reg = PluginRegistry(loader=loader)
        assert reg.loader is loader

    def test_tc28_custom_loader_used(self) -> None:
        loader = PluginLoader(
            allowed_permissions=frozenset({PluginPermission.READ_CORPUS})
        )
        reg = PluginRegistry(loader=loader, auto_load=True)
        m = PluginManifest(
            plugin_id="custom-loader-test",
            name="Custom Loader Test",
            version="1.0.0",
            entry_point="literary_system.core",
            permissions=[PluginPermission.NETWORK_OUT],
        )
        reg.register(m)
        e = reg.get("custom-loader-test")
        assert e is not None
        # NETWORK_OUT 차단 → is_loaded False
        assert e.is_loaded is False


# ═══════════════════════════════════════════════════════════════
# TC29~TC33: 통합 시나리오
# ═══════════════════════════════════════════════════════════════
class TestRegistryIntegration:
    def test_tc29_full_lifecycle(self) -> None:
        reg = PluginRegistry(auto_load=True)
        m = _make("lifecycle-plugin", tags=["lifecycle"])
        reg.register(m)
        assert reg.get("lifecycle-plugin") is not None
        assert "lifecycle-plugin" in [e.plugin_id for e in reg.query_by_tag("lifecycle")]
        reg.unregister("lifecycle-plugin")
        assert reg.get("lifecycle-plugin") is None

    def test_tc30_registry_count_after_operations(self) -> None:
        reg = PluginRegistry()
        for i in range(10):
            reg.register(_make(f"batch-{i:02d}"))
        reg.unregister("batch-00")
        reg.unregister("batch-05")
        assert reg.count == 8

    def test_tc31_query_by_tag_after_unregister(self) -> None:
        reg = PluginRegistry()
        reg.register(_make("tagged-remove", tags=["remove-test"]))
        reg.unregister("tagged-remove")
        assert reg.query_by_tag("remove-test") == []

    def test_tc32_registry_entry_plugin_id_matches(self) -> None:
        reg = PluginRegistry()
        m = _make("id-match-test")
        e = reg.register(m)
        assert e.plugin_id == "id-match-test"

    def test_tc33_empty_registry_all_queries_empty(self) -> None:
        reg = PluginRegistry()
        assert reg.list_all() == []
        assert reg.query_by_tag("any") == []
        assert reg.query_loaded() == []
        assert reg.count == 0
