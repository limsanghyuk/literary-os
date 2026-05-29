"""
V454 — SemanticCacheRedis
Redis 백엔드 + Fuzzy 코사인 유사도 기반 의미론적 LLM 응답 캐시.

설계:
  - redis_fn 주입 (LLM-0 원칙): 실 Redis 없이 CI 테스트 가능
  - embed_fn 주입: 임베딩 함수 교체 가능 (기본: 단어 빈도 벡터)
  - 코사인 유사도 ≥ threshold (기본 0.92) 시 캐시 히트
  - per-tenant namespace 격리: sem_cache:{tenant_id}:*
  - TTL 설정 가능 (기본 3600s)

redis_fn 시그니처: (op: str, **kwargs) -> Any
  - op="get"    : key: str → Optional[str]
  - op="set"    : key: str, value: str, ttl_s: int → None
  - op="delete" : key: str → None
  - op="keys"   : pattern: str → List[str]
  - op="mget"   : keys: List[str] → List[Optional[str]]

embed_fn 시그니처: (text: str) -> List[float]
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import time
import uuid
from typing import Any, Callable, Dict, List, Optional, Tuple

# ---------------------------------------------------------------------------
# 기본 임베딩: 단어 빈도(TF) 기반 희소 벡터 (외부 의존 없음)
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """소문자 단어 토큰화 (한글/영어 혼용 지원)."""
    return re.findall(r"[\w가-힣]+", text.lower())


def _tfidf_embed(text: str) -> Dict[str, float]:
    """단어 빈도 기반 TF 벡터 (희소 dict)."""
    tokens = _tokenize(text)
    if not tokens:
        return {}
    counts: Dict[str, int] = {}
    for t in tokens:
        counts[t] = counts.get(t, 0) + 1
    n = len(tokens)
    return {w: c / n for w, c in counts.items()}


def _sparse_cosine(a: Dict[str, float], b: Dict[str, float]) -> float:
    """희소 벡터 코사인 유사도."""
    if not a or not b:
        return 0.0
    dot = sum(a[k] * b[k] for k in a if k in b)
    norm_a = math.sqrt(sum(v * v for v in a.values()))
    norm_b = math.sqrt(sum(v * v for v in b.values()))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def _dense_cosine(a: List[float], b: List[float]) -> float:
    """밀집 벡터 코사인 유사도."""
    if len(a) != len(b) or not a:
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(y * y for y in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


# ---------------------------------------------------------------------------
# 캐시 엔트리
# ---------------------------------------------------------------------------

class CacheEntry:
    """단일 캐시 항목."""
    __slots__ = ("entry_id", "prompt_key", "prompt", "embedding",
                 "response", "model_id", "created_ms", "hit_count")

    def __init__(
        self,
        prompt: str,
        embedding: Any,  # List[float] 또는 Dict[str, float]
        response: str,
        model_id: str = "",
        entry_id: str = "",
    ) -> None:
        self.entry_id: str = entry_id or str(uuid.uuid4())
        self.prompt_key: str = hashlib.sha256(
            f"{model_id}:{prompt}".encode()
        ).hexdigest()[:16]
        self.prompt = prompt
        self.embedding = embedding
        self.response = response
        self.model_id = model_id
        self.created_ms: float = time.monotonic() * 1000
        self.hit_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "entry_id": self.entry_id,
            "prompt_key": self.prompt_key,
            "prompt": self.prompt,
            "embedding": self.embedding,
            "response": self.response,
            "model_id": self.model_id,
            "created_ms": self.created_ms,
            "hit_count": self.hit_count,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CacheEntry":
        e = cls(
            prompt=d["prompt"],
            embedding=d["embedding"],
            response=d["response"],
            model_id=d.get("model_id", ""),
            entry_id=d.get("entry_id", ""),
        )
        e.prompt_key = d.get("prompt_key", e.prompt_key)
        e.created_ms = d.get("created_ms", e.created_ms)
        e.hit_count = d.get("hit_count", 0)
        return e


# ---------------------------------------------------------------------------
# In-Memory Redis 시뮬레이터 (테스트용)
# ---------------------------------------------------------------------------

class InMemoryRedis:
    """
    CI/테스트용 In-Memory Redis 시뮬레이터.
    redis_fn 주입 대신 직접 사용 가능.
    """

    def __init__(self) -> None:
        self._store: Dict[str, Tuple[str, Optional[float]]] = {}
        # (value, expire_at_monotonic)

    def __call__(self, op: str, **kwargs) -> Any:
        if op == "get":
            return self._get(kwargs["key"])
        elif op == "set":
            self._set(kwargs["key"], kwargs["value"], kwargs.get("ttl_s"))
        elif op == "delete":
            self._delete(kwargs["key"])
        elif op == "keys":
            return self._keys(kwargs["pattern"])
        elif op == "mget":
            return [self._get(k) for k in kwargs["keys"]]
        else:
            raise ValueError(f"Unknown op: {op}")

    def _get(self, key: str) -> Optional[str]:
        entry = self._store.get(key)
        if entry is None:
            return None
        value, expire_at = entry
        if expire_at is not None and time.monotonic() > expire_at:
            del self._store[key]
            return None
        return value

    def _set(self, key: str, value: str, ttl_s: Optional[int]) -> None:
        expire_at = time.monotonic() + ttl_s if ttl_s else None
        self._store[key] = (value, expire_at)

    def _delete(self, key: str) -> None:
        self._store.pop(key, None)

    def _keys(self, pattern: str) -> List[str]:
        # 단순 prefix 매칭 (glob * → 전체)
        prefix = pattern.rstrip("*")
        return [k for k in self._store if k.startswith(prefix)]


# ---------------------------------------------------------------------------
# SemanticCacheRedis
# ---------------------------------------------------------------------------

class SemanticCacheRedis:
    """
    V454 — Redis 백엔드 의미론적 LLM 응답 캐시.

    Parameters
    ----------
    redis_fn : Callable, optional
        Redis 연산 주입 함수 (LLM-0). None 이면 InMemoryRedis 사용.
    embed_fn : Callable, optional
        임베딩 함수. None 이면 단어 빈도 희소 벡터 사용.
    tenant_id : str
        테넌트 격리 네임스페이스.
    ttl_s : int
        캐시 TTL (초). 기본 3600.
    similarity_threshold : float
        히트 판정 유사도 임계값. 기본 0.92.
    max_scan_entries : int
        유사도 비교 최대 항목 수. 기본 200.
    """

    KEY_PREFIX = "sem_cache"

    def __init__(
        self,
        redis_fn: Optional[Callable] = None,
        embed_fn: Optional[Callable[[str], Any]] = None,
        tenant_id: str = "default",
        ttl_s: int = 3600,
        similarity_threshold: float = 0.92,
        max_scan_entries: int = 200,
    ) -> None:
        self._redis = redis_fn if redis_fn is not None else InMemoryRedis()
        self._embed_fn = embed_fn
        self.tenant_id = tenant_id
        self.ttl_s = ttl_s
        self.similarity_threshold = similarity_threshold
        self.max_scan_entries = max_scan_entries

        # 통계
        self._hits: int = 0
        self._misses: int = 0
        self._sets: int = 0
        self._errors: int = 0

    # ------------------------------------------------------------------
    # 핵심 API
    # ------------------------------------------------------------------

    def get(self, prompt: str, model_id: str = "") -> Optional[str]:
        """
        프롬프트와 유사도 ≥ threshold 인 캐시 항목 반환.
        히트 없으면 None.
        """
        try:
            query_emb = self._embed(prompt)
            entries = self._load_all_entries(model_id)
            best_score = 0.0
            best_entry: Optional[CacheEntry] = None

            for entry in entries[:self.max_scan_entries]:
                score = self._similarity(query_emb, entry.embedding)
                if score > best_score:
                    best_score = score
                    best_entry = entry

            if best_entry is not None and best_score >= self.similarity_threshold:
                best_entry.hit_count += 1
                self._hits += 1
                # hit_count 업데이트 저장
                self._save_entry(best_entry)
                return best_entry.response

            self._misses += 1
            return None

        except Exception:
            self._errors += 1
            self._misses += 1
            return None

    def set(
        self,
        prompt: str,
        response: str,
        model_id: str = "",
        ttl_s: Optional[int] = None,
    ) -> str:
        """프롬프트-응답 쌍 저장. entry_id 반환."""
        try:
            embedding = self._embed(prompt)
            entry = CacheEntry(
                prompt=prompt,
                embedding=embedding,
                response=response,
                model_id=model_id,
            )
            effective_ttl = ttl_s if ttl_s is not None else self.ttl_s
            self._save_entry(entry, effective_ttl)
            self._sets += 1
            return entry.entry_id
        except Exception:
            self._errors += 1
            return ""

    def delete(self, prompt: str, model_id: str = "") -> bool:
        """프롬프트와 정확 매칭되는 항목 삭제."""
        try:
            entries = self._load_all_entries(model_id)
            target_key = hashlib.sha256(
                f"{model_id}:{prompt}".encode()
            ).hexdigest()[:16]
            deleted = False
            for entry in entries:
                if entry.prompt_key == target_key:
                    redis_key = self._entry_key(entry.entry_id)
                    self._redis(op="delete", key=redis_key)
                    deleted = True
            return deleted
        except Exception:
            self._errors += 1
            return False

    def flush_tenant(self) -> int:
        """테넌트 전체 캐시 삭제. 삭제 수 반환."""
        try:
            pattern = f"{self.KEY_PREFIX}:{self.tenant_id}:*"
            keys = self._redis(op="keys", pattern=pattern)
            for k in keys:
                self._redis(op="delete", key=k)
            return len(keys)
        except Exception:
            self._errors += 1
            return 0

    def size(self) -> int:
        """현재 캐시 항목 수."""
        try:
            pattern = f"{self.KEY_PREFIX}:{self.tenant_id}:*"
            return len(self._redis(op="keys", pattern=pattern))
        except Exception:
            return 0

    def hit_rate(self) -> float:
        """캐시 적중률 (0.0 ~ 1.0)."""
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    def stats(self) -> Dict[str, Any]:
        """통계 반환."""
        return {
            "tenant_id": self.tenant_id,
            "hits": self._hits,
            "misses": self._misses,
            "sets": self._sets,
            "errors": self._errors,
            "hit_rate": round(self.hit_rate(), 4),
            "size": self.size(),
            "similarity_threshold": self.similarity_threshold,
            "ttl_s": self.ttl_s,
        }

    def reset_stats(self) -> None:
        """통계 초기화."""
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._errors = 0

    # ------------------------------------------------------------------
    # 내부
    # ------------------------------------------------------------------

    def _embed(self, text: str) -> Any:
        """텍스트 임베딩."""
        if self._embed_fn is not None:
            return self._embed_fn(text)
        return _tfidf_embed(text)

    def _similarity(self, a: Any, b: Any) -> float:
        """임베딩 유형에 따라 코사인 유사도 계산."""
        if isinstance(a, dict) and isinstance(b, dict):
            return _sparse_cosine(a, b)
        elif isinstance(a, list) and isinstance(b, list):
            return _dense_cosine(a, b)
        # 타입 불일치: 희소 변환 시도
        try:
            return _dense_cosine(list(a), list(b))
        except Exception:
            return 0.0

    def _entry_key(self, entry_id: str) -> str:
        return f"{self.KEY_PREFIX}:{self.tenant_id}:{entry_id}"

    def _save_entry(
        self,
        entry: CacheEntry,
        ttl_s: Optional[int] = None,
    ) -> None:
        key = self._entry_key(entry.entry_id)
        value = json.dumps(entry.to_dict(), ensure_ascii=False)
        self._redis(
            op="set",
            key=key,
            value=value,
            ttl_s=ttl_s if ttl_s is not None else self.ttl_s,
        )

    def _load_all_entries(self, model_id: str = "") -> List[CacheEntry]:
        """Redis에서 테넌트 항목 전체 로드."""
        pattern = f"{self.KEY_PREFIX}:{self.tenant_id}:*"
        keys = self._redis(op="keys", pattern=pattern)
        if not keys:
            return []
        values = self._redis(op="mget", keys=keys)
        entries = []
        for raw in values:
            if raw is None:
                continue
            try:
                d = json.loads(raw)
                entry = CacheEntry.from_dict(d)
                # model_id 필터 (지정 시)
                if model_id and entry.model_id and entry.model_id != model_id:
                    continue
                entries.append(entry)
            except Exception:
                continue
        return entries
