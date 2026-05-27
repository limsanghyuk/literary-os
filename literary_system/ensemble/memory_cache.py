"""
V651 — EnsembleMemoryCache (SP-C.2 Multi-Agent Ensemble).
AgentCoordinator 결과를 scene_id 기반으로 캐싱.
TTL 만료 + 최대 크기 LRU 퇴출.
LLM-0: 외부 API 직접 호출 없음.
"""
from __future__ import annotations

import logging
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# 기본값 상수
DEFAULT_TTL_SECONDS: float   = 3600.0   # 1시간
DEFAULT_MAX_SIZE:    int      = 256


@dataclass
class EnsembleCacheEntry:
    """캐시 단일 엔트리."""
    scene_id:   str
    result_dict: Dict[str, Any]
    created_at:  float = field(default_factory=time.time)
    ttl:         float = DEFAULT_TTL_SECONDS

    def is_expired(self, now: Optional[float] = None) -> bool:
        t = now if now is not None else time.time()
        return (t - self.created_at) >= self.ttl


@dataclass
class EnsembleCacheStats:
    """캐시 통계."""
    size:     int   = 0
    hits:     int   = 0
    misses:   int   = 0
    evictions: int  = 0
    expirations: int = 0

    @property
    def hit_rate(self) -> float:
        total = self.hits + self.misses
        return self.hits / total if total > 0 else 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "size":        self.size,
            "hits":        self.hits,
            "misses":      self.misses,
            "evictions":   self.evictions,
            "expirations": self.expirations,
            "hit_rate":    round(self.hit_rate, 4),
        }


class EnsembleMemoryCache:
    """
    AgentCoordinator CoordinatorResult 캐시.

    - 스레드 비안전(단일 스레드 전용). 멀티 워커 시 외부 락 필요.
    - put() 시 max_size 초과 → 가장 오래된 항목(LRU) 퇴출.
    - get() 시 TTL 만료 항목은 즉시 삭제 후 None 반환.
    """

    def __init__(
        self,
        max_size: int   = DEFAULT_MAX_SIZE,
        ttl:      float = DEFAULT_TTL_SECONDS,
    ) -> None:
        if max_size < 1:
            raise ValueError(f"max_size must be >= 1, got {max_size}")
        if ttl <= 0:
            raise ValueError(f"ttl must be > 0, got {ttl}")

        self._max_size:  int   = max_size
        self._ttl:       float = ttl
        # OrderedDict: FIFO 삽입 순서 유지 (LRU 퇴출용)
        self._store: OrderedDict[str, EnsembleCacheEntry] = OrderedDict()
        self._stats = EnsembleCacheStats()

    # ── 공개 API ────────────────────────────────────────────────────────────

    def put(self, scene_id: str, result_dict: Dict[str, Any]) -> None:
        """씬 결과를 캐시에 저장. 이미 존재하면 갱신(LRU 갱신)."""
        if scene_id in self._store:
            # 기존 항목 삭제 후 맨 뒤에 재삽입 (LRU 갱신)
            del self._store[scene_id]

        entry = EnsembleCacheEntry(
            scene_id=scene_id,
            result_dict=result_dict,
            created_at=time.time(),
            ttl=self._ttl,
        )
        self._store[scene_id] = entry

        # 초과 시 가장 오래된 항목 퇴출
        while len(self._store) > self._max_size:
            old_key, _ = self._store.popitem(last=False)
            self._stats.evictions += 1
            logger.debug("EnsembleMemoryCache: 퇴출 scene_id=%s", old_key)

        self._stats.size = len(self._store)

    def get(self, scene_id: str) -> Optional[Dict[str, Any]]:
        """캐시 조회. TTL 만료 또는 미존재 시 None 반환."""
        entry = self._store.get(scene_id)
        if entry is None:
            self._stats.misses += 1
            return None

        if entry.is_expired():
            del self._store[scene_id]
            self._stats.expirations += 1
            self._stats.misses      += 1
            self._stats.size = len(self._store)
            logger.debug("EnsembleMemoryCache: 만료 scene_id=%s", scene_id)
            return None

        # LRU 갱신: 접근된 항목을 맨 뒤로 이동
        self._store.move_to_end(scene_id)
        self._stats.hits += 1
        return entry.result_dict

    def invalidate(self, scene_id: str) -> bool:
        """특정 씬 캐시 무효화. 존재하면 True, 없으면 False."""
        if scene_id in self._store:
            del self._store[scene_id]
            self._stats.size = len(self._store)
            logger.debug("EnsembleMemoryCache: 무효화 scene_id=%s", scene_id)
            return True
        return False

    def clear(self) -> int:
        """전체 캐시 삭제. 삭제된 항목 수 반환."""
        count = len(self._store)
        self._store.clear()
        self._stats.size = 0
        return count

    def purge_expired(self) -> int:
        """만료된 항목 일괄 삭제. 삭제 수 반환."""
        now = time.time()
        expired_keys = [k for k, e in self._store.items() if e.is_expired(now)]
        for k in expired_keys:
            del self._store[k]
            self._stats.expirations += 1
        self._stats.size = len(self._store)
        return len(expired_keys)

    def stats(self) -> EnsembleCacheStats:
        """현재 통계 스냅샷 반환."""
        self._stats.size = len(self._store)
        return self._stats

    def contains(self, scene_id: str) -> bool:
        """만료 여부를 포함한 존재 확인 (만료 시 False)."""
        entry = self._store.get(scene_id)
        if entry is None:
            return False
        if entry.is_expired():
            del self._store[scene_id]
            self._stats.size = len(self._store)
            return False
        return True

    # ── 프로퍼티 ────────────────────────────────────────────────────────────

    @property
    def size(self) -> int:
        return len(self._store)

    @property
    def max_size(self) -> int:
        return self._max_size

    @property
    def ttl(self) -> float:
        return self._ttl
