"""V360: NarrativeScopeResolver + 장르 플러그인 아키텍처."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Type


@dataclass
class StyleDirective:
    genre_id:       str
    pov:            str   = "1인칭"
    scene_rhythm:   str   = "medium"
    emotional_amp:  float = 0.7
    metadata:       Dict[str, Any] = field(default_factory=dict)

@dataclass
class SceneContext:
    scene_id:   str = ""
    tension:    float = 0.5
    metadata:   Dict[str, Any] = field(default_factory=dict)

@dataclass
class StoryContext:
    genre:   str = "literary"
    arc:     str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

class NarrativeScopePlugin(ABC):
    genre_id:     str = ""
    display_name: str = ""

    @abstractmethod
    def resolve_scene(self, scene_ctx: SceneContext, story_ctx: StoryContext) -> StyleDirective: ...

    @abstractmethod
    def get_foreshadow_rules(self) -> List[str]: ...

class PluginRegistry_Scope:
    _plugins: Dict[str, Type[NarrativeScopePlugin]] = {}

    @classmethod
    def register(cls, plugin_cls: Type[NarrativeScopePlugin]) -> None:
        cls._plugins[plugin_cls.genre_id] = plugin_cls

    @classmethod
    def get(cls, genre_id: str) -> Optional[Type[NarrativeScopePlugin]]:
        return cls._plugins.get(genre_id)

    @classmethod
    def all_genres(cls) -> List[str]:
        return list(cls._plugins.keys())

class NarrativeScopeResolver:
    def __init__(self) -> None:
        self._active: Optional[NarrativeScopePlugin] = None
        self._load_builtin_plugins()

    def _load_builtin_plugins(self) -> None:
        from literary_system.scope.plugins import (
            genre_plugin_fantasy,
            genre_plugin_historical,
            genre_plugin_literary,
            genre_plugin_noir,
            genre_plugin_romance,
        )

    def load(self, genre_id: Optional[str] = None) -> NarrativeScopePlugin:
        gid = genre_id or "literary"
        cls = PluginRegistry.get(gid)
        if cls is None: raise ValueError(f"알 수 없는 장르: {gid}")
        self._active = cls()
        return self._active

    def resolve(self, scene_ctx: SceneContext, story_ctx: StoryContext) -> StyleDirective:
        if self._active is None: self.load(story_ctx.genre)
        return self._active.resolve_scene(scene_ctx, story_ctx)

    def available_genres(self) -> List[str]:
        return PluginRegistry.all_genres()


# G37 DuplicateZero(ADR-033): 클래스명 전역 고유화 — 외부 import 하위호환 별칭
PluginRegistry = PluginRegistry_Scope
