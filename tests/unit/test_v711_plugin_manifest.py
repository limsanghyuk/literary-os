"""
V711 SP-D.3: PluginManifest + PluginLoader 단위 테스트 (ADR-172)
=================================================================
목표: 33 TC PASS
커버리지:
  - PluginManifest 유효성 검사 (plugin_id / name / version / entry_point / schema_version)
  - PluginPermission Enum
  - PluginStatus Enum
  - to_dict / from_dict 직렬화
  - PluginLoader: load / unload / list_loaded / get_status
  - 화이트리스트 차단 검사
  - 중복 등록 방지
"""
from __future__ import annotations

import pytest

from literary_system.plugins.plugin_manifest import (
    MANIFEST_SCHEMA_VERSION,
    PluginManifest,
    PluginPermission,
    PluginStatus,
    PluginValidationError,
)
from literary_system.plugins.plugin_loader import (
    DEFAULT_ALLOWED_PERMISSIONS,
    PluginLoadResult,
    PluginLoader,
)


# ═══════════════════════════════════════════════════════════════
# 헬퍼: 유효한 최소 매니페스트
# ═══════════════════════════════════════════════════════════════
def _minimal() -> PluginManifest:
    return PluginManifest(
        plugin_id="romance-plugin",
        name="Romance Genre Plugin",
        version="1.0.0",
        entry_point="literary_system.world.knowledge_state_tracker",
    )


# ═══════════════════════════════════════════════════════════════
# TC01~TC10: PluginManifest 정상 생성
# ═══════════════════════════════════════════════════════════════
class TestPluginManifestCreation:
    def test_tc01_minimal_manifest_created(self) -> None:
        m = _minimal()
        assert m.plugin_id == "romance-plugin"

    def test_tc02_default_permissions_empty(self) -> None:
        m = _minimal()
        assert m.permissions == []

    def test_tc03_default_schema_version(self) -> None:
        m = _minimal()
        assert m.schema_version == MANIFEST_SCHEMA_VERSION

    def test_tc04_permissions_assigned(self) -> None:
        m = PluginManifest(
            plugin_id="corpus-reader",
            name="Corpus Reader",
            version="2.1.0",
            entry_point="literary_system.corpus.corpus_manager",
            permissions=[PluginPermission.READ_CORPUS],
        )
        assert PluginPermission.READ_CORPUS in m.permissions

    def test_tc05_has_permission_true(self) -> None:
        m = PluginManifest(
            plugin_id="llm-caller",
            name="LLM Caller",
            version="0.1.0",
            entry_point="literary_system.llm_bridge.mock_llm_bridge",
            permissions=[PluginPermission.CALL_LLM],
        )
        assert m.has_permission(PluginPermission.CALL_LLM) is True

    def test_tc06_has_permission_false(self) -> None:
        m = _minimal()
        assert m.has_permission(PluginPermission.NETWORK_OUT) is False

    def test_tc07_to_dict_contains_keys(self) -> None:
        m = _minimal()
        d = m.to_dict()
        assert "plugin_id" in d
        assert "entry_point" in d
        assert "permissions" in d

    def test_tc08_to_dict_permissions_serialized(self) -> None:
        m = PluginManifest(
            plugin_id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            entry_point="literary_system.core",
            permissions=[PluginPermission.READ_CORPUS, PluginPermission.WRITE_OUTPUT],
        )
        d = m.to_dict()
        assert "read_corpus" in d["permissions"]
        assert "write_output" in d["permissions"]

    def test_tc09_from_dict_round_trip(self) -> None:
        m1 = _minimal()
        d = m1.to_dict()
        m2 = PluginManifest.from_dict(d)
        assert m1.plugin_id == m2.plugin_id
        assert m1.version == m2.version

    def test_tc10_tags_and_author(self) -> None:
        m = PluginManifest(
            plugin_id="tagged-plugin",
            name="Tagged",
            version="1.0.0",
            entry_point="literary_system.core",
            author="Literary OS Team",
            tags=["drama", "romance"],
        )
        assert "drama" in m.tags
        assert m.author == "Literary OS Team"


# ═══════════════════════════════════════════════════════════════
# TC11~TC18: PluginManifest 유효성 검사 (실패 케이스)
# ═══════════════════════════════════════════════════════════════
class TestPluginManifestValidation:
    def test_tc11_plugin_id_too_short(self) -> None:
        with pytest.raises(PluginValidationError, match="최소 3자"):
            PluginManifest(
                plugin_id="ab",
                name="Short ID",
                version="1.0.0",
                entry_point="literary_system.core",
            )

    def test_tc12_plugin_id_uppercase_rejected(self) -> None:
        with pytest.raises(PluginValidationError):
            PluginManifest(
                plugin_id="MyPlugin",
                name="Bad ID",
                version="1.0.0",
                entry_point="literary_system.core",
            )

    def test_tc13_plugin_id_spaces_rejected(self) -> None:
        with pytest.raises(PluginValidationError):
            PluginManifest(
                plugin_id="my plugin",
                name="Bad ID",
                version="1.0.0",
                entry_point="literary_system.core",
            )

    def test_tc14_version_bad_format(self) -> None:
        with pytest.raises(PluginValidationError, match="X.Y.Z"):
            PluginManifest(
                plugin_id="good-plugin",
                name="Good Name",
                version="1.0",
                entry_point="literary_system.core",
            )

    def test_tc15_entry_point_no_dot(self) -> None:
        with pytest.raises(PluginValidationError, match="점"):
            PluginManifest(
                plugin_id="good-plugin",
                name="Good Name",
                version="1.0.0",
                entry_point="nodot",
            )

    def test_tc16_name_empty_rejected(self) -> None:
        with pytest.raises(PluginValidationError, match="빈 문자열"):
            PluginManifest(
                plugin_id="good-plugin",
                name="",
                version="1.0.0",
                entry_point="literary_system.core",
            )

    def test_tc17_schema_version_major_mismatch(self) -> None:
        with pytest.raises(PluginValidationError, match="major 불일치"):
            PluginManifest(
                plugin_id="old-plugin",
                name="Old Plugin",
                version="1.0.0",
                entry_point="literary_system.core",
                schema_version="9.0",
            )

    def test_tc18_frozen_immutable(self) -> None:
        m = _minimal()
        with pytest.raises((AttributeError, TypeError)):
            m.plugin_id = "changed"  # type: ignore[misc]


# ═══════════════════════════════════════════════════════════════
# TC19~TC28: PluginPermission + PluginStatus
# ═══════════════════════════════════════════════════════════════
class TestPluginEnums:
    def test_tc19_permission_read_corpus_value(self) -> None:
        assert PluginPermission.READ_CORPUS.value == "read_corpus"

    def test_tc20_permission_network_out_value(self) -> None:
        assert PluginPermission.NETWORK_OUT.value == "network_out"

    def test_tc21_permission_write_nkg(self) -> None:
        assert PluginPermission.WRITE_NKG.value == "write_nkg"

    def test_tc22_status_loaded(self) -> None:
        assert PluginStatus.LOADED.value == "loaded"

    def test_tc23_status_error(self) -> None:
        assert PluginStatus.ERROR.value == "error"

    def test_tc24_status_pending(self) -> None:
        assert PluginStatus.PENDING.value == "pending"

    def test_tc25_status_disabled(self) -> None:
        assert PluginStatus.DISABLED.value == "disabled"

    def test_tc26_allowed_permissions_default_set(self) -> None:
        assert PluginPermission.READ_CORPUS in DEFAULT_ALLOWED_PERMISSIONS
        assert PluginPermission.NETWORK_OUT not in DEFAULT_ALLOWED_PERMISSIONS

    def test_tc27_write_nkg_not_default_allowed(self) -> None:
        assert PluginPermission.WRITE_NKG not in DEFAULT_ALLOWED_PERMISSIONS

    def test_tc28_from_dict_permission_round_trip(self) -> None:
        m = PluginManifest(
            plugin_id="perm-test",
            name="Perm Test",
            version="1.0.0",
            entry_point="literary_system.core",
            permissions=[PluginPermission.CALL_LLM],
        )
        d = m.to_dict()
        m2 = PluginManifest.from_dict(d)
        assert PluginPermission.CALL_LLM in m2.permissions


# ═══════════════════════════════════════════════════════════════
# TC29~TC33: PluginLoader
# ═══════════════════════════════════════════════════════════════
class TestPluginLoader:
    def test_tc29_load_valid_module_succeeds(self) -> None:
        loader = PluginLoader()
        m = PluginManifest(
            plugin_id="core-loader",
            name="Core Loader",
            version="1.0.0",
            entry_point="literary_system.core",
        )
        result = loader.load(m)
        assert result.success

    def test_tc30_blocked_permission_returns_error(self) -> None:
        loader = PluginLoader()
        m = PluginManifest(
            plugin_id="net-plugin",
            name="Network Plugin",
            version="1.0.0",
            entry_point="literary_system.core",
            permissions=[PluginPermission.NETWORK_OUT],
        )
        result = loader.load(m)
        assert result.status == PluginStatus.ERROR
        assert "차단" in result.message

    def test_tc31_duplicate_load_returns_error(self) -> None:
        loader = PluginLoader()
        m = PluginManifest(
            plugin_id="dup-plugin",
            name="Dup Plugin",
            version="1.0.0",
            entry_point="literary_system.core",
        )
        loader.load(m)
        result2 = loader.load(m)
        assert result2.status == PluginStatus.ERROR

    def test_tc32_unload_loaded_plugin(self) -> None:
        loader = PluginLoader()
        m = PluginManifest(
            plugin_id="unload-me",
            name="Unload Me",
            version="1.0.0",
            entry_point="literary_system.core",
        )
        loader.load(m)
        ok = loader.unload("unload-me")
        assert ok is True
        assert loader.get_status("unload-me") == PluginStatus.DISABLED

    def test_tc33_list_loaded_and_all(self) -> None:
        loader = PluginLoader()
        m1 = PluginManifest(
            plugin_id="list-plugin-a",
            name="List A",
            version="1.0.0",
            entry_point="literary_system.core",
        )
        m2 = PluginManifest(
            plugin_id="list-plugin-b",
            name="List B",
            version="1.0.0",
            entry_point="nonexistent.module.path",
        )
        loader.load(m1)
        loader.load(m2)
        loaded = loader.list_loaded()
        all_status = loader.list_all()
        assert "list-plugin-a" in loaded
        assert "list-plugin-b" not in loaded
        assert "list-plugin-a" in all_status
        assert "list-plugin-b" in all_status
