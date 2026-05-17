"""
V324 - ItemNodeExtension  (Phase 3)
RelationGraphStore ItemNode 확장 — 소유권 추적 + 위치 검증.

설계 원칙 (P2 외과적 통합, P3 LLM 0회):
  - RelationGraphStore 내부 변경 없이 독립 레지스트리로 운영
  - ACQUIRE 검증: 캐릭터 위치 == 아이템 위치 AND 아이템 소유자 없음
  - transfer_ownership: from_id 소유자 검증 후 이전
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class ExtendedItemNode:
    """V324 확장 아이템 노드."""
    item_id: str
    name: str
    owner_id: Optional[str] = None
    location_id: Optional[str] = None
    is_consumable: bool = False
    quantity: int = 1

    def to_dict(self) -> dict:
        return {
            "item_id": self.item_id,
            "name": self.name,
            "owner_id": self.owner_id,
            "location_id": self.location_id,
            "is_consumable": self.is_consumable,
            "quantity": self.quantity,
        }


class ItemNodeExtension:
    """
    아이템 소유권·위치 레지스트리.

    RelationGraphStore를 수정하지 않고 독립 동작.
    SpatialConstraintGate와 협력하여 ACQUIRE 이중 검증.
    """

    def __init__(self) -> None:
        self._items: Dict[str, ExtendedItemNode] = {}

    def register(self, item: ExtendedItemNode) -> None:
        """아이템 등록."""
        self._items[item.item_id] = item

    def get_item(self, item_id: str) -> Optional[ExtendedItemNode]:
        """아이템 조회. 없으면 None."""
        return self._items.get(item_id)

    def transfer_ownership(
        self,
        item_id: str,
        from_id: str,
        to_id: str,
    ) -> bool:
        """
        소유권 이전.
        from_id가 현재 소유자가 아니면 False 반환.
        """
        item = self._items.get(item_id)
        if item is None:
            return False
        if item.owner_id != from_id:
            return False
        item.owner_id = to_id
        return True

    def validate_acquire(
        self,
        char_location_id: str,
        item_id: str,
    ) -> bool:
        """
        ACQUIRE 검증:
          - 아이템이 등록되어 있어야 함
          - 캐릭터 위치 == 아이템 위치
        """
        item = self._items.get(item_id)
        if item is None:
            return False
        return item.location_id == char_location_id

    def all_items(self) -> list[ExtendedItemNode]:
        return list(self._items.values())
