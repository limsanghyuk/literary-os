"""
Literary OS — Plugin System (SP-D.3)
=====================================
V711: PluginManifest + PluginLoader
V712: PluginRegistry
V713: PluginWhitelist + PluginSandbox
V714: PluginLifecycleManager
"""
from literary_system.plugins.plugin_manifest import (
    PluginManifest,
    PluginPermission,
    PluginStatus,
    PluginValidationError,
)
from literary_system.plugins.plugin_loader import PluginLoader, PluginLoadResult
from literary_system.plugins.plugin_registry import PluginRegistry, RegistryEntry
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
from literary_system.plugins.plugin_lifecycle import (
    PluginLifecycleManager,
    LifecycleState,
    LifecycleRecord,
)

__all__ = [
    # V711
    "PluginManifest",
    "PluginPermission",
    "PluginStatus",
    "PluginValidationError",
    "PluginLoader",
    "PluginLoadResult",
    # V712
    "PluginRegistry",
    "RegistryEntry",
    # V713
    "PluginWhitelist",
    "DEFAULT_ALLOWED_MODULES",
    "BLOCKED_MODULES",
    "PluginSandbox",
    "SandboxResult",
    "SandboxSecurityError",
    "SandboxTimeoutError",
    # V714
    "PluginLifecycleManager",
    "LifecycleState",
    "LifecycleRecord",
]

from literary_system.plugins.plugin_sdk import (
    BasePlugin,
    PluginContext,
    PluginSDKError,
    MissingManifestError,
)
from literary_system.plugins.plugin_test_harness import PluginTestHarness

__all__ += [
    # V715
    "BasePlugin",
    "PluginContext",
    "PluginSDKError",
    "MissingManifestError",
    "PluginTestHarness",
]

from literary_system.plugins.plugin_auth import (
    PluginAuthAdapter,
    PluginAuthResult,
    PluginAuthError,
    PluginTokenInvalid,
    PluginTokenExpired,
    PluginAccessDenied,
    PluginTenantNotFound,
    PERMISSION_ROLE_MAP,
)

__all__ += [
    # V721 — Zero-Trust 인증 어댑터
    "PluginAuthAdapter",
    "PluginAuthResult",
    "PluginAuthError",
    "PluginTokenInvalid",
    "PluginTokenExpired",
    "PluginAccessDenied",
    "PluginTenantNotFound",
    "PERMISSION_ROLE_MAP",
]
