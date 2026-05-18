"""
V563 SharedCharacterDB — 작품 간 공유 캐릭터 데이터베이스

책임:
- 캐릭터 프로필 CRUD (이름, 역할, 특성, 관계)
- 캐릭터-프로젝트 연결 관리
- 관계 그래프 (character_id → character_id → RelationType)
- 캐릭터 아크 이력 기록
- MultiWorkCore.shared_asset 인터페이스와 자동 통합

LLM-0: 외부 LLM 호출 없음.
"""

from __future__ import annotations

import time
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Set, Tuple, Any


class RelationType(Enum):
    """캐릭터 간 관계 유형."""
    ALLY = "ally"
    RIVAL = "rival"
    FAMILY = "family"
    ROMANTIC = "romantic"
    MENTOR = "mentor"
    ENEMY = "enemy"
    NEUTRAL = "neutral"


@dataclass
class CharacterProfile:
    """공유 캐릭터 프로필.

    Attributes:
        character_id:  전역 고유 ID
        name:          캐릭터 이름
        role:          역할 (주인공/조연/악당 등)
        genre_tags:    이 캐릭터가 등장하는 장르 목록
        traits:        성격·외형 특성 딕셔너리
        arc_history:   씬별 아크 변화 이력 [(scene_id, delta)]
        project_refs:  이 캐릭터를 사용하는 프로젝트 ID 집합
        created_at:    생성 타임스탬프
        metadata:      자유 형식 확장 필드
    """
    character_id: str
    name: str
    role: str
    genre_tags: List[str] = field(default_factory=list)
    traits: Dict[str, Any] = field(default_factory=dict)
    arc_history: List[Tuple[str, float]] = field(default_factory=list)
    project_refs: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def record_arc(self, scene_id: str, delta: float) -> None:
        """아크 변화 기록 (delta: -1.0 ~ +1.0)."""
        self.arc_history.append((scene_id, delta))

    def cumulative_arc(self) -> float:
        """누적 아크 변화량."""
        return sum(d for _, d in self.arc_history)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "name": self.name,
            "role": self.role,
            "genre_tags": self.genre_tags,
            "traits": self.traits,
            "arc_history_len": len(self.arc_history),
            "cumulative_arc": self.cumulative_arc(),
            "project_refs": list(self.project_refs),
        }


@dataclass
class CharacterRelation:
    """두 캐릭터 간 관계."""
    from_id: str
    to_id: str
    relation_type: RelationType
    weight: float = 1.0       # 관계 강도 (0 ~ 1)
    description: str = ""


class SharedCharacterDB:
    """작품 간 공유 캐릭터 데이터베이스.

    - 캐릭터 등록·조회·삭제
    - 관계 그래프 관리
    - 프로젝트별 캐릭터 뷰 제공
    - Thread-safe (RLock)
    """

    def __init__(self) -> None:
        self._chars: Dict[str, CharacterProfile] = {}
        self._relations: Dict[Tuple[str, str], CharacterRelation] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ #
    # 캐릭터 CRUD
    # ------------------------------------------------------------------ #

    def add_character(
        self,
        character_id: str,
        name: str,
        role: str,
        genre_tags: Optional[List[str]] = None,
        traits: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> CharacterProfile:
        """캐릭터 등록.

        Returns:
            등록된 CharacterProfile

        Raises:
            KeyError: character_id 중복
        """
        with self._lock:
            if character_id in self._chars:
                raise KeyError(f"Character already exists: {character_id}")
            char = CharacterProfile(
                character_id=character_id,
                name=name,
                role=role,
                genre_tags=genre_tags or [],
                traits=traits or {},
                metadata=metadata or {},
            )
            self._chars[character_id] = char
            return char

    def get_character(self, character_id: str) -> Optional[CharacterProfile]:
        """캐릭터 조회."""
        return self._chars.get(character_id)

    def list_characters(
        self,
        genre: Optional[str] = None,
        role: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> List[CharacterProfile]:
        """캐릭터 목록 (필터 옵션)."""
        with self._lock:
            result = list(self._chars.values())
            if genre:
                result = [c for c in result if genre in c.genre_tags]
            if role:
                result = [c for c in result if c.role == role]
            if project_id:
                result = [c for c in result if project_id in c.project_refs]
            return result

    def remove_character(self, character_id: str) -> bool:
        """캐릭터 제거 (관계도 함께 삭제).

        Returns:
            삭제 성공 여부
        """
        with self._lock:
            if character_id not in self._chars:
                return False
            del self._chars[character_id]
            # 관련 관계 제거
            keys_to_remove = [
                k for k in self._relations
                if character_id in k
            ]
            for k in keys_to_remove:
                del self._relations[k]
            return True

    def update_traits(self, character_id: str, traits: Dict[str, Any]) -> None:
        """캐릭터 특성 업데이트 (merge)."""
        with self._lock:
            char = self._chars.get(character_id)
            if char is None:
                raise KeyError(f"Character not found: {character_id}")
            char.traits.update(traits)

    # ------------------------------------------------------------------ #
    # 프로젝트 연결
    # ------------------------------------------------------------------ #

    def link_to_project(self, character_id: str, project_id: str) -> None:
        """캐릭터를 프로젝트에 연결."""
        with self._lock:
            char = self._chars.get(character_id)
            if char is None:
                raise KeyError(f"Character not found: {character_id}")
            char.project_refs.add(project_id)

    def unlink_from_project(self, character_id: str, project_id: str) -> None:
        """캐릭터-프로젝트 연결 해제."""
        with self._lock:
            char = self._chars.get(character_id)
            if char:
                char.project_refs.discard(project_id)

    # ------------------------------------------------------------------ #
    # 관계 그래프
    # ------------------------------------------------------------------ #

    def add_relation(
        self,
        from_id: str,
        to_id: str,
        relation_type: RelationType,
        weight: float = 1.0,
        description: str = "",
    ) -> CharacterRelation:
        """캐릭터 간 관계 등록.

        Raises:
            KeyError: 존재하지 않는 캐릭터 참조
        """
        with self._lock:
            for cid in (from_id, to_id):
                if cid not in self._chars:
                    raise KeyError(f"Character not found: {cid}")
            key = (from_id, to_id)
            rel = CharacterRelation(
                from_id=from_id,
                to_id=to_id,
                relation_type=relation_type,
                weight=max(0.0, min(1.0, weight)),
                description=description,
            )
            self._relations[key] = rel
            return rel

    def get_relation(
        self, from_id: str, to_id: str
    ) -> Optional[CharacterRelation]:
        """두 캐릭터 간 관계 조회."""
        return self._relations.get((from_id, to_id))

    def neighbors(
        self, character_id: str, relation_type: Optional[RelationType] = None
    ) -> List[CharacterRelation]:
        """특정 캐릭터의 모든 관계 반환."""
        result = [
            r for k, r in self._relations.items()
            if k[0] == character_id
        ]
        if relation_type is not None:
            result = [r for r in result if r.relation_type == relation_type]
        return result

    # ------------------------------------------------------------------ #
    # 아크 기록
    # ------------------------------------------------------------------ #

    def record_arc(self, character_id: str, scene_id: str, delta: float) -> None:
        """씬 처리 후 캐릭터 아크 변화 기록."""
        with self._lock:
            char = self._chars.get(character_id)
            if char is None:
                raise KeyError(f"Character not found: {character_id}")
            char.record_arc(scene_id, delta)

    # ------------------------------------------------------------------ #
    # 통계
    # ------------------------------------------------------------------ #

    def stats(self) -> Dict[str, Any]:
        """DB 통계."""
        with self._lock:
            return {
                "total_characters": len(self._chars),
                "total_relations": len(self._relations),
                "roles": list({c.role for c in self._chars.values()}),
            }
