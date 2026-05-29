"""
tests/unit/test_v713_plugin_sandbox.py
V713 SP-D.3 — PluginWhitelist + PluginSandbox 테스트 (33 TC)

ADR-174
"""
import pytest
from literary_system.plugins.plugin_whitelist import (
    PluginWhitelist,
    DEFAULT_ALLOWED_MODULES,
    BLOCKED_MODULES,
)
from literary_system.plugins.plugin_sandbox import (
    PluginSandbox,
    SandboxResult,
    SandboxSecurityError,
    SandboxTimeoutError,
)


# ===========================================================================
# TestPluginWhitelistDefaults  TC01~08
# ===========================================================================

class TestPluginWhitelistDefaults:
    """기본 화이트리스트 동작 검증."""

    def test_tc01_math_allowed_by_default(self):
        w = PluginWhitelist()
        assert w.is_allowed("math") is True

    def test_tc02_os_blocked_by_default(self):
        w = PluginWhitelist()
        assert w.is_allowed("os") is False

    def test_tc03_sys_blocked_by_default(self):
        w = PluginWhitelist()
        assert w.is_allowed("sys") is False

    def test_tc04_subprocess_blocked(self):
        w = PluginWhitelist()
        assert w.is_allowed("subprocess") is False

    def test_tc05_json_allowed_by_default(self):
        w = PluginWhitelist()
        assert w.is_allowed("json") is True

    def test_tc06_re_allowed_by_default(self):
        w = PluginWhitelist()
        assert w.is_allowed("re") is True

    def test_tc07_default_allowed_modules_is_frozenset(self):
        assert isinstance(DEFAULT_ALLOWED_MODULES, frozenset)
        assert "math" in DEFAULT_ALLOWED_MODULES

    def test_tc08_blocked_modules_is_frozenset(self):
        assert isinstance(BLOCKED_MODULES, frozenset)
        assert "os" in BLOCKED_MODULES
        assert "subprocess" in BLOCKED_MODULES


# ===========================================================================
# TestPluginWhitelistMutation  TC09~16
# ===========================================================================

class TestPluginWhitelistMutation:
    """화이트리스트 동적 변경 검증."""

    def test_tc09_allow_custom_module(self):
        w = PluginWhitelist()
        w.allow("custom_lib")
        assert w.is_allowed("custom_lib") is True

    def test_tc10_block_allowed_module(self):
        w = PluginWhitelist()
        w.block("math")
        assert w.is_allowed("math") is False

    def test_tc11_allow_blocked_module_raises(self):
        w = PluginWhitelist()
        with pytest.raises(ValueError, match="immutable blocked list"):
            w.allow("os")

    def test_tc12_extra_allowed_init(self):
        w = PluginWhitelist(extra_allowed={"my_pkg"})
        assert w.is_allowed("my_pkg") is True

    def test_tc13_extra_blocked_init(self):
        w = PluginWhitelist(extra_blocked={"json"})
        assert w.is_allowed("json") is False

    def test_tc14_allowed_modules_snapshot(self):
        w = PluginWhitelist()
        snap = w.allowed_modules()
        assert isinstance(snap, frozenset)
        assert "math" in snap

    def test_tc15_blocked_modules_snapshot_includes_defaults(self):
        w = PluginWhitelist()
        bm = w.blocked_modules()
        assert "os" in bm
        assert "subprocess" in bm

    def test_tc16_parent_package_allows_submodule(self):
        w = PluginWhitelist(extra_allowed={"xml"})
        # xml 허용 → xml.etree도 허용
        assert w.is_allowed("xml.etree") is True


# ===========================================================================
# TestSandboxBasic  TC17~24
# ===========================================================================

class TestSandboxBasic:
    """PluginSandbox 기본 실행 검증."""

    def setup_method(self):
        self.sb = PluginSandbox()

    def test_tc17_execute_arithmetic(self):
        r = self.sb.execute("result = 2 + 3")
        assert r.success is True
        assert r.return_value == 5

    def test_tc18_execute_string_ops(self):
        r = self.sb.execute("result = 'hello' + ' world'")
        assert r.success is True
        assert r.return_value == "hello world"

    def test_tc19_execute_list_comprehension(self):
        r = self.sb.execute("result = [x * 2 for x in [1, 2, 3]]")
        assert r.success is True
        assert r.return_value == [2, 4, 6]

    def test_tc20_execute_math_import(self):
        r = self.sb.execute("import math\nresult = math.sqrt(25)")
        assert r.success is True
        assert r.return_value == pytest.approx(5.0)

    def test_tc21_execute_no_result_var(self):
        r = self.sb.execute("x = 42")
        assert r.success is True
        assert r.return_value is None

    def test_tc22_result_locals_snapshot(self):
        r = self.sb.execute("x = 10\ny = 20\nresult = x + y")
        assert r.success is True
        assert r.locals_snapshot.get("x") == 10
        assert r.locals_snapshot.get("y") == 20

    def test_tc23_syntax_error_returns_failure(self):
        r = self.sb.execute("def broken(:\n    pass")
        assert r.success is False
        assert r.error is not None

    def test_tc24_sandbox_result_is_dataclass(self):
        r = self.sb.execute("result = 1")
        assert isinstance(r, SandboxResult)
        assert hasattr(r, "success")
        assert hasattr(r, "return_value")
        assert hasattr(r, "error")
        assert hasattr(r, "stdout")


# ===========================================================================
# TestSandboxSecurity  TC25~33
# ===========================================================================

class TestSandboxSecurity:
    """샌드박스 보안 차단 검증."""

    def setup_method(self):
        self.sb = PluginSandbox()

    def test_tc25_import_os_blocked(self):
        r = self.sb.execute("import os")
        assert r.success is False
        assert "os" in (r.error or "")

    def test_tc26_import_sys_blocked(self):
        r = self.sb.execute("import sys")
        assert r.success is False

    def test_tc27_import_subprocess_blocked(self):
        r = self.sb.execute("import subprocess")
        assert r.success is False

    def test_tc28_import_socket_blocked(self):
        r = self.sb.execute("import socket")
        assert r.success is False

    def test_tc29_custom_whitelist_restricts(self):
        w = PluginWhitelist(extra_blocked={"math"})
        sb = PluginSandbox(whitelist=w)
        r = sb.execute("import math")
        assert r.success is False

    def test_tc30_custom_whitelist_allows_extra(self):
        """custom_lib이 화이트리스트에 추가되면 import 허용 (실제 모듈 없어도 validate_import는 True)."""
        w = PluginWhitelist(extra_allowed={"custom_lib"})
        sb = PluginSandbox(whitelist=w)
        assert sb.validate_import("custom_lib") is True

    def test_tc31_validate_import_os_false(self):
        sb = PluginSandbox()
        assert sb.validate_import("os") is False

    def test_tc32_validate_import_math_true(self):
        sb = PluginSandbox()
        assert sb.validate_import("math") is True

    def test_tc33_sandbox_isolates_runs(self):
        """두 번 실행해도 상태가 공유되지 않는다."""
        r1 = self.sb.execute("counter = 1")
        r2 = self.sb.execute("result = counter")
        # 두 번째 실행에서 counter가 없어야 함 → error 또는 NameError
        assert r2.success is False or r2.return_value is None
