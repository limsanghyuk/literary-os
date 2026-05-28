"""
Literary OS — Plugin System (SP-D.3)
=====================================
V711: PluginManifest + PluginLoader 기반 모듈.
"""
from literary_system.plugins.plugin_manifest import (
    PluginManifest,
    PluginPermission,
    PluginStatus,
    PluginValidationError,
)
from literary_system.plugins.plugin_loader import PluginLoader, PluginLoadResult

__all__ = [
    "PluginManifest",
    "PluginPermission",
    "PluginStatus",
    "PluginValidationError",
    "PluginLoader",
    "PluginLoadResult",
]

from literary_system.plugins.plugin_registry import (
    PluginRegistry,
    RegistryEntry,
)

__all__ += ["PluginRegistry", "RegistryEntry"]
