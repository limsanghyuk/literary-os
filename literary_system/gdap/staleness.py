"""V350: GDAP — DKGStalenessTracker.

설계도 섹션 4.1 구현.
Literary OS V329 NKGStalenessTracker를 범용화한 버전.
SHA-256(앞 16자리) 해시 비교 기반 Dirty Flag 관리.
"""
from __future__ import annotations

from typing import Dict, Optional, Set


class GDAPStalenessTracker:
    """파일/노드 단위 Dirty Flag 관리자.

    Attributes:
        _hashes:  node_id → 마지막 확인 content_hash
        _dirty:   현재 DIRTY 상태인 node_id 집합
    """

    def __init__(self) -> None:
        self._hashes: Dict[str, str] = {}
        self._dirty:  Set[str]       = set()

    # ── 등록 ────────────────────────────────────────────────

    def register(self, node_id: str, content_hash: str) -> None:
        """노드를 해시와 함께 등록. 이미 존재하면 해시만 갱신."""
        self._hashes[node_id] = content_hash
        self._dirty.discard(node_id)

    def register_content(self, node_id: str, content: str) -> str:
        """문자열 content로 등록 — 내부적으로 sha256_short 계산."""
        from literary_system.gdap.schema import _sha256_short
        h = _sha256_short(content)
        self.register(node_id, h)
        return h

    # ── 상태 조회 ────────────────────────────────────────────

    def is_dirty(self, node_id: str) -> bool:
        """DIRTY 집합에 있는지 여부."""
        return node_id in self._dirty

    def is_stale(self, node_id: str, new_hash: str) -> bool:
        """저장된 해시와 new_hash가 다른지 여부 (미등록이면 True)."""
        stored = self._hashes.get(node_id)
        if stored is None:
            return True
        return stored != new_hash

    def is_registered(self, node_id: str) -> bool:
        return node_id in self._hashes

    def get_hash(self, node_id: str) -> Optional[str]:
        return self._hashes.get(node_id)

    def dirty_nodes(self) -> Set[str]:
        """현재 DIRTY 노드 집합 복사본 반환."""
        return set(self._dirty)

    # ── Dirty 마킹 ───────────────────────────────────────────

    def mark_dirty(self, node_id: str) -> None:
        """node_id를 DIRTY로 표시."""
        self._dirty.add(node_id)

    def mark_dirty_if_stale(self, node_id: str, new_hash: str) -> bool:
        """해시가 다를 때만 DIRTY 마킹. 마킹 여부 반환."""
        if self.is_stale(node_id, new_hash):
            self._dirty.add(node_id)
            return True
        return False

    def mark_dirty_batch(self, node_ids) -> int:
        """여러 노드를 한번에 DIRTY 마킹. 마킹된 수 반환."""
        count = 0
        for nid in node_ids:
            if nid not in self._dirty:
                self._dirty.add(nid)
                count += 1
        return count

    # ── Dirty 해제 ───────────────────────────────────────────

    def clear_dirty(self, node_id: str, new_hash: Optional[str] = None) -> None:
        """DIRTY 해제. new_hash가 있으면 해시도 갱신."""
        self._dirty.discard(node_id)
        if new_hash is not None:
            self._hashes[node_id] = new_hash

    def clear_all_dirty(self) -> int:
        """전체 DIRTY 플래그 클리어. 클리어된 수 반환."""
        count = len(self._dirty)
        self._dirty.clear()
        return count

    # ── 노드 제거 ────────────────────────────────────────────

    def remove(self, node_id: str) -> bool:
        """노드를 트래커에서 완전 제거. 존재했으면 True."""
        existed = node_id in self._hashes
        self._hashes.pop(node_id, None)
        self._dirty.discard(node_id)
        return existed

    # ── 통계 ────────────────────────────────────────────────

    def stats(self) -> dict:
        return {
            "registered_count": len(self._hashes),
            "dirty_count":      len(self._dirty),
            "dirty_nodes":      sorted(self._dirty),
        }

    def __repr__(self) -> str:
        return (f"DKGStalenessTracker("
                f"registered={len(self._hashes)}, "
                f"dirty={len(self._dirty)})")

DKGStalenessTracker = GDAPStalenessTracker  # V579 backward-compat alias
