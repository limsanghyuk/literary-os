"""literary_system.world — WorldState, WorldEvent, 장르 플러그인 레지스트리."""
# V11.39.0: scope/ NarrativeScopePlugin 연결 (ADR-128)
try:
    from literary_system.scope.resolver import PluginRegistry, NarrativeScopePlugin
    from literary_system.scope.genre_plugin_noir import NoirPlugin
    from literary_system.scope.genre_plugin_fantasy import FantasyPlugin
    from literary_system.scope.genre_plugin_romance import RomancePlugin
    from literary_system.scope.genre_plugin_historical import HistoricalPlugin
    from literary_system.scope.genre_plugin_literary import LiteraryPlugin

    _GENRE_REGISTRY = PluginRegistry()
    for _plugin_cls in [NoirPlugin, FantasyPlugin, RomancePlugin, HistoricalPlugin, LiteraryPlugin]:
        try:
            _GENRE_REGISTRY.register(_plugin_cls())
        except Exception:
            pass
except ImportError:
    PluginRegistry = None
    NarrativeScopePlugin = None
    _GENRE_REGISTRY = None
