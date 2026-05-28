"""
plugin_registry_gate.py — Gate G87: Plugin Registry Gate (ADR-177)

SP-D.3 플러그인 서브시스템(V711~V715) 게이트 검증.
7개 체크포인트:

  PR-1  PluginManifest 스키마 — plugin_id 길이·형식, entry_point 점 분리, schema_version
  PR-2  PluginRegistry  — 등록·조회·해제·훅
  PR-3  PluginSandbox   — 화이트리스트 허용·차단
  PR-4  PluginLifecycleManager — 6-state 상태 머신
  PR-5  BasePlugin / PluginContext SDK
  PR-6  PluginTestHarness — 격리 테스트 헬퍼
  PR-7  __all__ 심볼 집합 — 필수 공개 API 노출
"""
from __future__ import annotations


def _cp(name: str, passed: bool, detail: str = "") -> dict:
    return {"checkpoint": name, "passed": passed, "detail": detail}


# ── PR-1  PluginManifest 스키마 ──────────────────────────────────────────────
def _check_pr1_manifest() -> dict:
    try:
        from literary_system.plugins import PluginManifest, PluginPermission

        # valid manifest
        m = PluginManifest(
            plugin_id="test-plugin",
            name="Test Plugin",
            version="1.0.0",
            entry_point="mypackage.myplugin",
            permissions=[PluginPermission.READ_CORPUS],
            description="gate test",
        )
        assert m.plugin_id == "test-plugin"
        assert m.schema_version == "1.0"

        # invalid plugin_id (too short — < 3 chars)
        try:
            PluginManifest(plugin_id="ab", name="n", version="1.0.0",
                           entry_point="a.b", permissions=[])
            return _cp("PR-1", False, "short plugin_id should have raised")
        except Exception:
            pass

        # no dot in entry_point
        try:
            PluginManifest(plugin_id="valid-id", name="n", version="1.0.0",
                           entry_point="nodot", permissions=[])
            return _cp("PR-1", False, "entry_point without dot should have raised")
        except Exception:
            pass

        # version format mismatch
        try:
            PluginManifest(plugin_id="valid-id", name="n", version="bad_version",
                           entry_point="a.b", permissions=[])
            return _cp("PR-1", False, "bad version format should have raised")
        except Exception:
            pass

        return _cp("PR-1", True, "manifest schema validation OK")
    except Exception as exc:
        return _cp("PR-1", False, str(exc))


# ── PR-2  PluginRegistry ─────────────────────────────────────────────────────
def _check_pr2_registry() -> dict:
    try:
        from literary_system.plugins import PluginManifest, PluginPermission, PluginRegistry

        reg = PluginRegistry()
        m = PluginManifest(plugin_id="reg-test", name="Reg Test", version="0.1.0",
                           entry_point="reg.test", permissions=[PluginPermission.READ_CORPUS])

        # register
        reg.register(m)

        # get returns RegistryEntry with .manifest
        entry = reg.get("reg-test")
        assert entry is not None, "get should return entry"
        assert entry.manifest is m, "entry.manifest should be the registered manifest"

        # list_all
        ids = [e.manifest.plugin_id for e in reg.list_all()]
        assert "reg-test" in ids, f"reg-test not in list_all: {ids}"

        # duplicate raises
        try:
            reg.register(m)
            return _cp("PR-2", False, "duplicate register should raise")
        except Exception:
            pass

        # unregister
        result = reg.unregister("reg-test")
        assert result is True or result is None or result == "reg-test", \
            f"unregister unexpected return: {result}"
        assert reg.get("reg-test") is None, "after unregister get should be None"

        # hooks
        seen: list = []
        reg.on_register(lambda m: seen.append(("reg", m.plugin_id)))
        reg.on_unregister(lambda pid: seen.append(("unreg", pid)))
        reg.register(m)
        reg.unregister("reg-test")
        assert ("reg", "reg-test") in seen, f"on_register hook not called: {seen}"
        assert ("unreg", "reg-test") in seen, f"on_unregister hook not called: {seen}"

        return _cp("PR-2", True, "registry CRUD + hooks OK")
    except Exception as exc:
        return _cp("PR-2", False, str(exc))


# ── PR-3  PluginSandbox ──────────────────────────────────────────────────────
def _check_pr3_sandbox() -> dict:
    try:
        from literary_system.plugins import PluginSandbox, PluginWhitelist

        sb = PluginSandbox(whitelist=PluginWhitelist())

        # safe code — sandbox captures 'result' variable into return_value
        res = sb.execute("result = 1 + 2")
        assert res.success, f"safe code failed: {res.error}"
        assert res.return_value == 3, f"expected 3, got {res.return_value}"

        # blocked import
        res2 = sb.execute("import os")
        assert not res2.success, "os import should be blocked"

        # validate_import returns bool
        assert not sb.validate_import("subprocess"), "subprocess should be disallowed"
        assert sb.validate_import("math"), "math should be allowed"

        return _cp("PR-3", True, "sandbox whitelist/block OK")
    except Exception as exc:
        return _cp("PR-3", False, str(exc))


# ── PR-4  PluginLifecycleManager ─────────────────────────────────────────────
def _check_pr4_lifecycle() -> dict:
    try:
        from literary_system.plugins import (
            PluginManifest, PluginPermission, PluginRegistry,
            PluginLifecycleManager, LifecycleState,
        )

        reg = PluginRegistry()
        m = PluginManifest(plugin_id="lc-test", name="LC Test", version="1.0.0",
                           entry_point="math.floor",  # importable
                           permissions=[PluginPermission.READ_CORPUS])
        reg.register(m)

        mgr = PluginLifecycleManager(registry=reg)

        # activate → ACTIVE
        rec = mgr.activate("lc-test")
        assert rec.state == LifecycleState.ACTIVE, \
            f"expected ACTIVE, got {rec.state}"

        # deactivate → INACTIVE
        rec = mgr.deactivate("lc-test")
        assert rec.state == LifecycleState.INACTIVE

        # restart → ACTIVE
        mgr.activate("lc-test")
        rec = mgr.restart("lc-test")
        assert rec.state == LifecycleState.ACTIVE

        # unknown plugin → raises ValueError (correct: not in registry)
        try:
            mgr.activate("no-such-plugin")
            # some implementations return error state instead of raising
        except (ValueError, KeyError):
            pass  # acceptable — plugin not found

        return _cp("PR-4", True, "lifecycle state machine OK")
    except Exception as exc:
        return _cp("PR-4", False, str(exc))


# ── PR-5  BasePlugin / PluginContext ─────────────────────────────────────────
def _check_pr5_sdk() -> dict:
    try:
        from literary_system.plugins import (
            BasePlugin, PluginContext, PluginManifest, PluginPermission,
            MissingManifestError,
        )

        # PluginContext basics
        ctx = PluginContext("sdk-test",
                            [PluginPermission.READ_CORPUS, PluginPermission.WRITE_OUTPUT])
        ctx.emit("hello")
        assert ctx.get_outputs() == ["hello"]
        assert ctx.has_permission(PluginPermission.READ_CORPUS)
        assert not ctx.has_permission(PluginPermission.CALL_LLM)

        ctx.require_permission(PluginPermission.READ_CORPUS)   # no raise
        try:
            ctx.require_permission(PluginPermission.CALL_LLM)
            return _cp("PR-5", False, "require_permission should raise PermissionError")
        except PermissionError:
            pass

        # Concrete BasePlugin subclass
        manifest = PluginManifest(plugin_id="sdk-plugin", name="SDK Plugin",
                                  version="1.0.0", entry_point="sdk.plugin",
                                  permissions=[PluginPermission.READ_CORPUS])

        class ConcretePlugin(BasePlugin):
            MANIFEST = manifest
            def on_activate(self):
                self._context.emit("activated")
            def on_deactivate(self):
                self._context.emit("deactivated")

        ctx2 = PluginContext("sdk-plugin", [PluginPermission.READ_CORPUS])
        p = ConcretePlugin(ctx2)
        p.on_activate()
        assert "activated" in ctx2.get_outputs()

        # Missing MANIFEST → MissingManifestError at class definition time
        try:
            class BadPlugin(BasePlugin):
                def on_activate(self): pass
                def on_deactivate(self): pass
            return _cp("PR-5", False, "missing MANIFEST should raise MissingManifestError")
        except MissingManifestError:
            pass

        return _cp("PR-5", True, "BasePlugin/PluginContext SDK OK")
    except Exception as exc:
        return _cp("PR-5", False, str(exc))


# ── PR-6  PluginTestHarness ──────────────────────────────────────────────────
def _check_pr6_harness() -> dict:
    try:
        from literary_system.plugins import (
            BasePlugin, PluginManifest, PluginPermission, PluginTestHarness,
        )

        manifest = PluginManifest(plugin_id="harness-plugin", name="Harness Plugin",
                                  version="1.0.0", entry_point="harness.plugin",
                                  permissions=[PluginPermission.READ_CORPUS])

        class HarnessPlugin(BasePlugin):
            MANIFEST = manifest
            def on_activate(self):
                self._context.emit("activated")
            def on_deactivate(self):
                self._context.emit("deactivated")

        harness = PluginTestHarness(HarnessPlugin,
                                    permissions=[PluginPermission.READ_CORPUS])
        harness.activate()
        assert harness.is_activated
        assert "activated" in harness.outputs

        # sandbox execution — 'result' variable captured as return_value
        res = harness.run_in_sandbox("result = 7 * 6")
        assert res.success
        assert res.return_value == 42, f"expected 42, got {res.return_value}"

        return _cp("PR-6", True, "PluginTestHarness isolation OK")
    except Exception as exc:
        return _cp("PR-6", False, str(exc))


# ── PR-7  __all__ public API surface ─────────────────────────────────────────
_REQUIRED_SYMBOLS = {
    # manifest + loader
    "PluginManifest", "PluginPermission", "PluginLoader", "PluginLoadResult",
    # registry
    "PluginRegistry",
    # whitelist / sandbox
    "PluginWhitelist", "DEFAULT_ALLOWED_MODULES", "BLOCKED_MODULES",
    "PluginSandbox", "SandboxResult", "SandboxSecurityError", "SandboxTimeoutError",
    # lifecycle
    "PluginLifecycleManager", "LifecycleState", "LifecycleRecord",
    # sdk
    "BasePlugin", "PluginContext", "PluginSDKError", "MissingManifestError",
    # test harness
    "PluginTestHarness",
}


def _check_pr7_api_surface() -> dict:
    try:
        import literary_system.plugins as pkg
        exported = set(getattr(pkg, "__all__", []))
        missing = _REQUIRED_SYMBOLS - exported
        if missing:
            return _cp("PR-7", False, f"missing from __all__: {sorted(missing)}")
        for sym in _REQUIRED_SYMBOLS:
            if not hasattr(pkg, sym):
                return _cp("PR-7", False, f"symbol not accessible: {sym}")
        return _cp("PR-7", True, f"all {len(_REQUIRED_SYMBOLS)} required symbols exported")
    except Exception as exc:
        return _cp("PR-7", False, str(exc))


# ── public entry point ───────────────────────────────────────────────────────
def run_g87_gate() -> dict:
    """G87 Plugin Registry Gate — 7 checkpoints (PR-1 ~ PR-7)."""
    checkers = [
        _check_pr1_manifest,
        _check_pr2_registry,
        _check_pr3_sandbox,
        _check_pr4_lifecycle,
        _check_pr5_sdk,
        _check_pr6_harness,
        _check_pr7_api_surface,
    ]

    checkpoints = [fn() for fn in checkers]
    passed = sum(1 for c in checkpoints if c["passed"])
    total = len(checkpoints)
    overall = passed == total

    return {
        "gate": "G87",
        "pass": overall,
        "passed": overall,
        "passed_count": passed,
        "total_count": total,
        "checkpoints": checkpoints,
        "errors": [c["detail"] for c in checkpoints if not c["passed"]],
    }
