"""
literary_system/corpus/bgem3_embedder.py  — V559
BGEM3Embedder: 1024차원 임베딩 + 인메모리 코사인 검색
실제 운영: sentence-transformers BAAI/bge-m3 사용
폴백: hash 기반 결정론적 벡터 (LLM-0, ADR-015/031)
"""
from __future__ import annotations
import hashlib
import math
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional
from .corpus_ingestor import ScenarioEntry

EMBEDDING_DIM   = 1024
MAX_CONTEXT_LEN = 8192  # 토큰 기준 (참고용)


@dataclass
class BGESearchResult:
    entry: ScenarioEntry
    score: float  # 코사인 유사도 [0, 1]


class BGEM3Embedder:
    """
    BGE-M3 임베딩 래퍼.
    sentence-transformers 설치 시 실 모델 사용.
    미설치 시 SHA-256 기반 결정론적 1024-dim 벡터로 폴백.
    """
    MODEL_NAME = "BAAI/bge-m3"

    def __init__(self) -> None:
        self._model = None
        self._use_real: bool = False
        self._index: List[Tuple[ScenarioEntry, List[float]]] = []
        self._try_load_model()

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def embed(self, text: str) -> List[float]:
        """텍스트 → 1024-dim float 벡터."""
        if self._use_real:
            return self._real_embed(text)
        return self._hash_embed(text)

    def add_entry(self, entry: ScenarioEntry) -> None:
        vec = self.embed(entry.content)
        self._index.append((entry, vec))

    def add_entries(self, entries: List[ScenarioEntry]) -> None:
        for e in entries:
            self.add_entry(e)

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """쿼리와 코사인 유사도 상위 top_k 결과 반환."""
        if not self._index:
            return []
        q_vec = self.embed(query)
        scored = [
            (entry, self._cosine(q_vec, vec))
            for entry, vec in self._index
        ]
        scored.sort(key=lambda x: x[1], reverse=True)
        return [SearchResult(entry=e, score=s) for e, s in scored[:top_k]]

    def index_info(self) -> Dict:
        return {
            "size":       len(self._index),
            "dim":        EMBEDDING_DIM,
            "model":      self.MODEL_NAME if self._use_real else "hash_fallback",
            "use_real":   self._use_real,
        }

    # ── 내부 헬퍼 ────────────────────────────────────────────────────────────

    def _try_load_model(self) -> None:
        try:
            from sentence_transformers import SentenceTransformer  # type: ignore
            self._model = SentenceTransformer(self.MODEL_NAME)
            self._use_real = True
        except Exception:
            self._use_real = False

    def _real_embed(self, text: str) -> List[float]:
        vec = self._model.encode(text, normalize_embeddings=True)
        return vec.tolist()

    def _hash_embed(self, text: str) -> List[float]:
        """SHA-256 seed로 결정론적 1024-dim 단위 벡터 생성."""
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        # 32바이트 digest를 반복 확장하여 1024 float 생성
        raw: List[float] = []
        seed = digest
        while len(raw) < EMBEDDING_DIM:
            seed = hashlib.sha256(seed).digest()
            for b in seed:
                raw.append((b / 127.5) - 1.0)  # [-1, 1]
        raw = raw[:EMBEDDING_DIM]
        # L2 정규화
        norm = math.sqrt(sum(x * x for x in raw)) or 1.0
        return [x / norm for x in raw]

    @staticmethod
    def _cosine(a: List[float], b: List[float]) -> float:
        dot  = sum(x * y for x, y in zip(a, b))
        na   = math.sqrt(sum(x * x for x in a)) or 1.0
        nb   = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (na * nb)

SearchResult = BGESearchResult  # V579 backward-compat alias
