"""
V564 SharedWorldDB — 작품 간 공유 월드/세계관 데이터베이스

책임:
- 장소(Location) CRUD
- 파벌/조직(Faction) CRUD
- 세계관 타임라인 이벤트 관리
- 로어(Lore) 항목 관리
- 프로젝트별 월드 뷰 제공

LLM-0: 외부 LLM 호출 없음.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Location:
    """세계관 내 장소."""
    location_id: str
    name: str
    description: str
    parent_id: Optional[str] = None      # 상위 지역 (대륙 → 왕국 → 도시)
    tags: List[str] = field(default_factory=list)
    project_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Faction:
    """세계관 내 파벌/조직."""
    faction_id: str
    name: str
    description: str
    alignment: str = "neutral"           # good / neutral / evil / complex
    member_ids: List[str] = field(default_factory=list)   # character_id 목록
    project_refs: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TimelineEvent:
    """세계관 타임라인 이벤트."""
    event_id: str
    timestamp: float                    # 스토리 내 시간축 (0.0 = 시작점)
    title: str
    description: str
    affected_locations: List[str] = field(default_factory=list)
    affected_factions: List[str] = field(default_factory=list)
    project_refs: List[str] = field(default_factory=list)


@dataclass
class LoreEntry:
    """세계관 로어 항목 (마법 체계, 역사, 관습 등)."""
    lore_id: str
    category: str                       # magic / history / culture / religion / …
    title: str
    content: str
    project_refs: List[str] = field(default_factory=list)
    created_at: float = field(default_factory=time.time)


class SharedWorldDB:
    """작품 간 공유 세계관 데이터베이스.

    - 장소·파벌·타임라인·로어 CRUD
    - 프로젝트별 세계관 뷰 제공
    - 계층적 장소 탐색 (parent_id 트리)
    - Thread-safe (RLock)
    """

    def __init__(self) -> None:
        self._locations: Dict[str, Location] = {}
        self._factions: Dict[str, Faction] = {}
        self._timeline: Dict[str, TimelineEvent] = {}
        self._lore: Dict[str, LoreEntry] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ #
    # 장소 CRUD
    # ------------------------------------------------------------------ #

    def add_location(
        self,
        location_id: str,
        name: str,
        description: str,
        parent_id: Optional[str] = None,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Location:
        """장소 등록.

        Raises:
            KeyError: location_id 중복, parent_id 미존재
        """
        with self._lock:
            if location_id in self._locations:
                raise KeyError(f"Location already exists: {location_id}")
            if parent_id and parent_id not in self._locations:
                raise KeyError(f"Parent location not found: {parent_id}")
            loc = Location(
                location_id=location_id,
                name=name,
                description=description,
                parent_id=parent_id,
                tags=tags or [],
                metadata=metadata or {},
            )
            self._locations[location_id] = loc
            return loc

    def get_location(self, location_id: str) -> Optional[Location]:
        return self._locations.get(location_id)

    def list_locations(
        self,
        parent_id: Optional[str] = None,
        tag: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[Location]:
        """장소 목록 (필터 옵션)."""
        with self._lock:
            result = list(self._locations.values())
            if parent_id is not None:
                result = [l for l in result if l.parent_id == parent_id]
            if tag:
                result = [l for l in result if tag in l.tags]
            if project_id:
                result = [l for l in result if project_id in l.project_refs]
            return result

    def children_of(self, parent_id: str) -> List[Location]:
        """하위 장소 목록."""
        return [l for l in self._locations.values() if l.parent_id == parent_id]

    def remove_location(self, location_id: str) -> bool:
        """장소 제거 (하위 장소가 있으면 False 반환)."""
        with self._lock:
            if location_id not in self._locations:
                return False
            children = self.children_of(location_id)
            if children:
                return False
            del self._locations[location_id]
            return True

    def link_location_to_project(self, location_id: str, project_id: str) -> None:
        """장소를 프로젝트에 연결."""
        with self._lock:
            loc = self._locations.get(location_id)
            if loc is None:
                raise KeyError(f"Location not found: {location_id}")
            if project_id not in loc.project_refs:
                loc.project_refs.append(project_id)

    # ------------------------------------------------------------------ #
    # 파벌 CRUD
    # ------------------------------------------------------------------ #

    def add_faction(
        self,
        faction_id: str,
        name: str,
        description: str,
        alignment: str = "neutral",
        member_ids: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Faction:
        """파벌 등록."""
        with self._lock:
            if faction_id in self._factions:
                raise KeyError(f"Faction already exists: {faction_id}")
            fac = Faction(
                faction_id=faction_id,
                name=name,
                description=description,
                alignment=alignment,
                member_ids=member_ids or [],
                metadata=metadata or {},
            )
            self._factions[faction_id] = fac
            return fac

    def get_faction(self, faction_id: str) -> Optional[Faction]:
        return self._factions.get(faction_id)

    def list_factions(
        self,
        alignment: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[Faction]:
        with self._lock:
            result = list(self._factions.values())
            if alignment:
                result = [f for f in result if f.alignment == alignment]
            if project_id:
                result = [f for f in result if project_id in f.project_refs]
            return result

    def add_member_to_faction(self, faction_id: str, character_id: str) -> None:
        """파벌에 캐릭터 추가."""
        with self._lock:
            fac = self._factions.get(faction_id)
            if fac is None:
                raise KeyError(f"Faction not found: {faction_id}")
            if character_id not in fac.member_ids:
                fac.member_ids.append(character_id)

    def link_faction_to_project(self, faction_id: str, project_id: str) -> None:
        """파벌을 프로젝트에 연결."""
        with self._lock:
            fac = self._factions.get(faction_id)
            if fac is None:
                raise KeyError(f"Faction not found: {faction_id}")
            if project_id not in fac.project_refs:
                fac.project_refs.append(project_id)

    # ------------------------------------------------------------------ #
    # 타임라인
    # ------------------------------------------------------------------ #

    def add_event(
        self,
        event_id: str,
        timestamp: float,
        title: str,
        description: str,
        affected_locations: Optional[List[str]] = None,
        affected_factions: Optional[List[str]] = None,
    ) -> TimelineEvent:
        """타임라인 이벤트 등록."""
        with self._lock:
            if event_id in self._timeline:
                raise KeyError(f"Event already exists: {event_id}")
            ev = TimelineEvent(
                event_id=event_id,
                timestamp=timestamp,
                title=title,
                description=description,
                affected_locations=affected_locations or [],
                affected_factions=affected_factions or [],
            )
            self._timeline[event_id] = ev
            return ev

    def get_event(self, event_id: str) -> Optional[TimelineEvent]:
        return self._timeline.get(event_id)

    def events_in_range(
        self, t_start: float, t_end: float
    ) -> List[TimelineEvent]:
        """시간 범위 내 이벤트 (정렬된 순서)."""
        result = [
            ev for ev in self._timeline.values()
            if t_start <= ev.timestamp <= t_end
        ]
        return sorted(result, key=lambda e: e.timestamp)

    # ------------------------------------------------------------------ #
    # 로어
    # ------------------------------------------------------------------ #

    def add_lore(
        self,
        lore_id: str,
        category: str,
        title: str,
        content: str,
    ) -> LoreEntry:
        """로어 항목 등록."""
        with self._lock:
            if lore_id in self._lore:
                raise KeyError(f"Lore already exists: {lore_id}")
            entry = LoreEntry(
                lore_id=lore_id,
                category=category,
                title=title,
                content=content,
            )
            self._lore[lore_id] = entry
            return entry

    def get_lore(self, lore_id: str) -> Optional[LoreEntry]:
        return self._lore.get(lore_id)

    def list_lore(self, category: Optional[str] = None) -> List[LoreEntry]:
        with self._lock:
            result = list(self._lore.values())
            if category:
                result = [l for l in result if l.category == category]
            return result

    # ------------------------------------------------------------------ #
    # 통계
    # ------------------------------------------------------------------ #

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "locations": len(self._locations),
                "factions": len(self._factions),
                "timeline_events": len(self._timeline),
                "lore_entries": len(self._lore),
            }
