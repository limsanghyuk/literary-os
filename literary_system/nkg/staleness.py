"""V360: DKGStalenessTracker v2 — 증분 변경 추적."""
from __future__ import annotations

import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Dict, Optional, Set


class NKGNodeCache:
    def __init__(self, max_size: int = 500) -> None:
        self._cache: OrderedDict[str, str] = OrderedDict()
        self._max_size = max_size
    def get(self, node_id: str) -> Optional[str]:
        if node_id not in self._cache: return None
        self._cache.move_to_end(node_id)
        return self._cache[node_id]
    def put(self, node_id: str, h: str) -> None:
        if node_id in self._cache: self._cache.move_to_end(node_id)
        self._cache[node_id] = h
        if len(self._cache) > self._max_size: self._cache.popitem(last=False)
    def invalidate(self, node_id: str) -> None:
        self._cache.pop(node_id, None)
    def size(self) -> int: return len(self._cache)

@dataclass
class StalenessRecord:
    node_id: str; last_hash: str
    last_modified: float = field(default_factory=time.time)
    dirty: bool = False; check_count: int = 0

class DKGStalenessTrackerV2:
    def __init__(self, cache_size: int = 500) -> None:
        self._records: Dict[str, StalenessRecord] = {}
        self._dirty: Set[str] = set()
        self._cache = NKGNodeCache(cache_size)
        self._total_checks = 0; self._cache_hits = 0; self._incremental_saves = 0

    def register(self, node_id: str, content_hash: str, timestamp: Optional[float] = None) -> None:
        ts = timestamp or time.time()
        self._records[node_id] = StalenessRecord(node_id=node_id, last_hash=content_hash, last_modified=ts)
        self._cache.put(node_id, content_hash); self._dirty.discard(node_id)

    def check_stale(self, node_id: str, new_hash: str, new_timestamp: Optional[float] = None) -> bool:
        self._total_checks += 1
        cached = self._cache.get(node_id)
        if cached is not None:
            if cached == new_hash: self._cache_hits += 1; return False
            self._cache.put(node_id, new_hash); return True
        rec = self._records.get(node_id)
        if rec is None: return True
        if rec.last_hash == new_hash: self._cache.put(node_id, new_hash); return False
        return True

    def mark_dirty_if_stale(self, node_id: str, new_hash: str, new_timestamp: Optional[float] = None) -> bool:
        stale = self.check_stale(node_id, new_hash, new_timestamp)
        if stale:
            self._dirty.add(node_id)
            rec = self._records.get(node_id)
            if rec: rec.dirty = True; rec.last_hash = new_hash; rec.last_modified = new_timestamp or time.time(); rec.check_count += 1
        else:
            self._incremental_saves += 1
        return stale

    def mark_dirty(self, node_id: str) -> None:
        self._dirty.add(node_id)
        if node_id in self._records: self._records[node_id].dirty = True
        self._cache.invalidate(node_id)

    def clear_dirty(self, node_id: str) -> None:
        self._dirty.discard(node_id)
        if node_id in self._records: self._records[node_id].dirty = False

    def clear_all_dirty(self) -> int:
        count = len(self._dirty)
        for nid in list(self._dirty):
            if nid in self._records: self._records[nid].dirty = False
        self._dirty.clear(); return count

    def dirty_nodes(self) -> Set[str]: return set(self._dirty)
    def is_dirty(self, node_id: str) -> bool: return node_id in self._dirty

    def stats(self) -> Dict:
        rate = (self._cache_hits / max(self._total_checks, 1)) * 100
        return {"registered": len(self._records), "dirty_count": len(self._dirty),
                "cache_size": self._cache.size(), "total_checks": self._total_checks,
                "cache_hits": self._cache_hits, "cache_hit_rate": round(rate, 1),
                "incremental_saves": self._incremental_saves}

class DKGStalenessTracker(DKGStalenessTrackerV2):
    """V350 호환 alias."""
    pass

# V340 레거시 alias
NKGStalenessTracker = DKGStalenessTrackerV2

