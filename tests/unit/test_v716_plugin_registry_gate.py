"""
test_v716_plugin_registry_gate.py — V716 Gate G87 Plugin Registry Gate 단위 테스트

33 TC:
  TestManifestValidation       TC01~TC10
  TestPluginRegistryCRUD       TC11~TC18
  TestPluginSandboxGate        TC19~TC22
  TestLifecycleGate            TC23~TC27
  TestPluginSDKGate            TC28~TC30
  TestG87Gate                  TC31~TC33
"""
import pytest
from literary_system.plugins import (
    PluginManifest, PluginPermission, PluginValidationError,
    PluginRegistry, RegistryEntry,
    PluginSandbox, PluginWhitelist, SandboxResult,
    PluginLifecycleManager, LifecycleState,
    BasePlugin, PluginContext, MissingManifestError,
    PluginTestHarness,
)
from literary_system.gates.plugin_registry_gate import run_g87_gate


# ──────────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────────

def _manifest(plugin_id="my-plugin", name="My Plugin", version="1.0.0",
              entry_point="my.plugin", permissions=None):
    return PluginManifest(
        plugin_id=plugin_id, name=name, version=version,
        entry_point=entry_point,
        permissions=permissions if permissions is not None else [PluginPermission.READ_CORPUS],
    )


# ──────────────────────────────────────────────────────────────────────────
# TestManifestValidation  TC01~TC10
# ──────────────────────────────────────────────────────────────────────────

class TestManifestValidation:
    def test_tc01_valid_manifest_created(self):
        """TC01: 유효한 매니페스트 생성"""
        m = _manifest()
        assert m.plugin_id == "my-plugin"
        assert m.schema_version == "1.0"

    def test_tc02_plugin_id_too_short_raises(self):
        """TC02: plugin_id 2자 이하 → PluginValidationError"""
        with pytest.raises(Exception):
            PluginManifest(plugin_id="ab", name="n", version="1.0.0",
                           entry_point="a.b", permissions=[])

    def test_tc03_plugin_id_invalid_chars_raises(self):
        """TC03: plugin_id 대문자 포함 → PluginValidationError"""
        with pytest.raises(Exception):
            PluginManifest(plugin_id="Bad_ID", name="n", version="1.0.0",
                           entry_point="a.b", permissions=[])

    def test_tc04_entry_point_no_dot_raises(self):
        """TC04: entry_point에 점 없음 → PluginValidationError"""
        with pytest.raises(Exception):
            PluginManifest(plugin_id="ok-id", name="n", version="1.0.0",
                           entry_point="nodot", permissions=[])

    def test_tc05_version_bad_format_raises(self):
        """TC05: version 형식 X.Y.Z 불일치 → PluginValidationError"""
        with pytest.raises(Exception):
            PluginManifest(plugin_id="ok-id", name="n", version="1.0",
                           entry_point="a.b", permissions=[])

    def test_tc06_empty_name_raises(self):
        """TC06: name 빈 문자열 → PluginValidationError"""
        with pytest.raises(Exception):
            PluginManifest(plugin_id="ok-id", name="", version="1.0.0",
                           entry_point="a.b", permissions=[])

    def test_tc07_valid_permissions_list(self):
        """TC07: 허용 권한 목록 정상 저장"""
        m = PluginManifest(
            plugin_id="ok-id", name="n", version="1.0.0",
            entry_point="a.b",
            permissions=[PluginPermission.READ_CORPUS, PluginPermission.WRITE_OUTPUT],
        )
        assert PluginPermission.READ_CORPUS in m.permissions
        assert PluginPermission.WRITE_OUTPUT in m.permissions

    def test_tc08_schema_version_default(self):
        """TC08: schema_version 기본값 '1.0'"""
        m = _manifest()
        assert m.schema_version == "1.0"

    def test_tc09_manifest_has_permission(self):
        """TC09: has_permission() 정상 동작"""
        m = _manifest(permissions=[PluginPermission.READ_CORPUS])
        assert m.has_permission(PluginPermission.READ_CORPUS)
        assert not m.has_permission(PluginPermission.WRITE_OUTPUT)

    def test_tc10_manifest_to_dict(self):
        """TC10: to_dict() 직렬화 검증"""
        m = _manifest()
        d = m.to_dict()
        assert d["plugin_id"] == "my-plugin"
        assert isinstance(d["permissions"], list)


# ──────────────────────────────────────────────────────────────────────────
# TestPluginRegistryCRUD  TC11~TC18
# ──────────────────────────────────────────────────────────────────────────

class TestPluginRegistryCRUD:
    def test_tc11_register_and_get(self):
        """TC11: 등록 후 get() 성공"""
        reg = PluginRegistry()
        m = _manifest()
        reg.register(m)
        entry = reg.get("my-plugin")
        assert entry is not None
        assert entry.manifest is m

    def test_tc12_get_nonexistent_returns_none(self):
        """TC12: 미등록 플러그인 get() → None"""
        reg = PluginRegistry()
        assert reg.get("ghost") is None

    def test_tc13_duplicate_register_raises(self):
        """TC13: 중복 등록 → 예외"""
        reg = PluginRegistry()
        m = _manifest()
        reg.register(m)
        with pytest.raises(Exception):
            reg.register(m)

    def test_tc14_unregister_removes_entry(self):
        """TC14: unregister 후 get() → None"""
        reg = PluginRegistry()
        m = _manifest()
        reg.register(m)
        reg.unregister("my-plugin")
        assert reg.get("my-plugin") is None

    def test_tc15_list_all_contains_registered(self):
        """TC15: list_all()에 등록된 항목 포함"""
        reg = PluginRegistry()
        m = _manifest()
        reg.register(m)
        ids = [e.manifest.plugin_id for e in reg.list_all()]
        assert "my-plugin" in ids

    def test_tc16_on_register_hook_fires(self):
        """TC16: on_register 훅 호출 확인"""
        reg = PluginRegistry()
        fired = []
        reg.on_register(lambda m: fired.append(m.plugin_id))
        reg.register(_manifest())
        assert "my-plugin" in fired

    def test_tc17_on_unregister_hook_fires(self):
        """TC17: on_unregister 훅 호출 확인"""
        reg = PluginRegistry()
        fired = []
        reg.on_unregister(lambda pid: fired.append(pid))
        reg.register(_manifest())
        reg.unregister("my-plugin")
        assert "my-plugin" in fired

    def test_tc18_registry_entry_has_manifest(self):
        """TC18: RegistryEntry.manifest 접근 가능"""
        reg = PluginRegistry()
        m = _manifest()
        reg.register(m)
        entry = reg.get("my-plugin")
        assert isinstance(entry, RegistryEntry)
        assert entry.manifest.plugin_id == "my-plugin"


# ──────────────────────────────────────────────────────────────────────────
# TestPluginSandboxGate  TC19~TC22
# ──────────────────────────────────────────────────────────────────────────

class TestPluginSandboxGate:
    def test_tc19_safe_code_executes(self):
        """TC19: 안전한 코드 실행 성공"""
        sb = PluginSandbox(whitelist=PluginWhitelist())
        res = sb.execute("result = 2 ** 10")
        assert res.success
        assert res.return_value == 1024

    def test_tc20_blocked_import_fails(self):
        """TC20: 차단된 모듈 import 실패"""
        sb = PluginSandbox(whitelist=PluginWhitelist())
        res = sb.execute("import os")
        assert not res.success

    def test_tc21_validate_import_allowed(self):
        """TC21: validate_import — 허용 모듈 True 반환"""
        sb = PluginSandbox(whitelist=PluginWhitelist())
        assert sb.validate_import("math") is True

    def test_tc22_validate_import_blocked(self):
        """TC22: validate_import — 차단 모듈 False 반환"""
        sb = PluginSandbox(whitelist=PluginWhitelist())
        assert sb.validate_import("subprocess") is False


# ──────────────────────────────────────────────────────────────────────────
# TestLifecycleGate  TC23~TC27
# ──────────────────────────────────────────────────────────────────────────

class TestLifecycleGate:
    def _make_mgr(self, plugin_id="lc-test", entry_point="math.floor"):
        reg = PluginRegistry()
        m = _manifest(plugin_id=plugin_id, entry_point=entry_point)
        reg.register(m)
        return PluginLifecycleManager(registry=reg), plugin_id

    def test_tc23_activate_sets_active(self):
        """TC23: activate() → LifecycleState.ACTIVE"""
        mgr, pid = self._make_mgr()
        rec = mgr.activate(pid)
        assert rec.state == LifecycleState.ACTIVE

    def test_tc24_deactivate_sets_inactive(self):
        """TC24: deactivate() → LifecycleState.INACTIVE"""
        mgr, pid = self._make_mgr()
        mgr.activate(pid)
        rec = mgr.deactivate(pid)
        assert rec.state == LifecycleState.INACTIVE

    def test_tc25_restart_returns_active(self):
        """TC25: restart() → LifecycleState.ACTIVE"""
        mgr, pid = self._make_mgr()
        mgr.activate(pid)
        rec = mgr.restart(pid)
        assert rec.state == LifecycleState.ACTIVE

    def test_tc26_activate_unknown_plugin_raises_or_errors(self):
        """TC26: 미등록 플러그인 activate() → 예외 또는 INACTIVE_ERROR"""
        reg = PluginRegistry()
        mgr = PluginLifecycleManager(registry=reg)
        try:
            rec = mgr.activate("ghost")
            assert rec.state == LifecycleState.INACTIVE_ERROR
        except (ValueError, KeyError):
            pass  # 예외도 허용

    def test_tc27_lifecycle_state_is_string_serializable(self):
        """TC27: LifecycleState 값 문자열 직렬화 가능 (JSON 호환)"""
        assert isinstance(LifecycleState.ACTIVE.value, str)
        assert isinstance(LifecycleState.INACTIVE.value, str)
        assert isinstance(LifecycleState.INACTIVE_ERROR.value, str)


# ──────────────────────────────────────────────────────────────────────────
# TestPluginSDKGate  TC28~TC30
# ──────────────────────────────────────────────────────────────────────────

_SDK_MANIFEST = PluginManifest(
    plugin_id="sdk-test-plugin", name="SDK Test", version="1.0.0",
    entry_point="sdk.test", permissions=[PluginPermission.READ_CORPUS],
)


class ConcreteTestPlugin(BasePlugin):
    MANIFEST = _SDK_MANIFEST
    def on_activate(self):
        self._context.emit("activated")
    def on_deactivate(self):
        self._context.emit("deactivated")


class TestPluginSDKGate:
    def test_tc28_plugin_context_emit_and_get_outputs(self):
        """TC28: PluginContext emit/get_outputs"""
        ctx = PluginContext("sdk-test-plugin", [PluginPermission.READ_CORPUS])
        ctx.emit("hello")
        ctx.emit("world")
        assert ctx.get_outputs() == ["hello", "world"]

    def test_tc29_base_plugin_missing_manifest_raises(self):
        """TC29: MANIFEST 없는 BasePlugin 서브클래스 → MissingManifestError"""
        with pytest.raises(MissingManifestError):
            class NoBadPlugin(BasePlugin):
                def on_activate(self): pass
                def on_deactivate(self): pass

    def test_tc30_plugin_test_harness_sandbox(self):
        """TC30: PluginTestHarness 샌드박스 실행 검증"""
        harness = PluginTestHarness(ConcreteTestPlugin,
                                    permissions=[PluginPermission.READ_CORPUS])
        harness.activate()
        assert harness.is_activated
        res = harness.run_in_sandbox("result = 3 + 4")
        assert res.success
        assert res.return_value == 7


# ──────────────────────────────────────────────────────────────────────────
# TestG87Gate  TC31~TC33
# ──────────────────────────────────────────────────────────────────────────

class TestG87Gate:
    def test_tc31_g87_gate_runs(self):
        """TC31: run_g87_gate() 호출 성공"""
        result = run_g87_gate()
        assert isinstance(result, dict)
        assert "gate" in result
        assert result["gate"] == "G87"

    def test_tc32_g87_all_checkpoints_pass(self):
        """TC32: G87 7개 체크포인트 모두 PASS"""
        result = run_g87_gate()
        failures = [c for c in result["checkpoints"] if not c["passed"]]
        assert len(failures) == 0, \
            f"Failing checkpoints: {[(c['checkpoint'], c['detail']) for c in failures]}"

    def test_tc33_g87_total_count_is_7(self):
        """TC33: G87 total_count == 7"""
        result = run_g87_gate()
        assert result["total_count"] == 7
        assert result["passed_count"] == 7
        assert result["passed"] is True
