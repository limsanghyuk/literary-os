"""
V325 - SimpleVectorRetriever  (Phase 2)
numpy 코사인 유사도 기반 씬별 관련 문서 검색.

설계 원칙 (P3 추가 패키지 0개):
  - numpy만 사용
  - EmbeddingEncoder(TF-IDF)로 내부 벡터화
  - add_documents() → 인덱스 갱신
  - retrieve(query, k) → List[RetrievedDoc] 반환
  - sentence-transformers 교체 가능 인터페이스 제공
  - ChiefLibrarian 카탈로그 문서를 소비 (LibrarianRAGBridge 경유)
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np

from literary_system.retrieval.embedding_encoder import EmbeddingEncoder

# ────────────────────────────────────────────────────────────────
# 데이터 타입
# ────────────────────────────────────────────────────────────────

@dataclass
class RetrievedDoc:
    """검색 결과 단위."""
    doc_id:   str
    content:  str
    score:    float
    metadata: dict[str, Any] = field(default_factory=dict)


# ────────────────────────────────────────────────────────────────
# SimpleVectorRetriever
# ────────────────────────────────────────────────────────────────

class SimpleVectorRetriever:
    """
    numpy 코사인 유사도 기반 RAG 검색기.

    사용 예:
        retriever = SimpleVectorRetriever()
        retriever.add_documents([
            {"doc_id": "char_001", "content": "고애신. 양반가 여식.", "metadata": {}},
        ])
        docs = retriever.retrieve("고애신 교회", k=3)
    """

    def __init__(self, max_features: int = 5000, min_df: int = 1) -> None:
        self._encoder    = EmbeddingEncoder(max_features=max_features, min_df=min_df)
        self._corpus:    list[dict[str, Any]] = []   # 원본 문서
        self._matrix:    np.ndarray | None = None    # (n_docs, vocab_size)
        self._dirty:     bool = False                # 재인덱싱 필요 플래그

    # ── 문서 관리 ────────────────────────────────────────────────

    def add_documents(self, docs: list[dict[str, Any]]) -> None:
        """
        문서를 코퍼스에 추가하고 인덱스를 갱신한다.

        Args:
            docs: List[{doc_id: str, content: str, metadata: dict}]
                  doc_id가 중복되면 기존 문서를 덮어씀.
        """
        if not docs:
            return

        # doc_id 중복 제거 (최신 우선)
        existing_ids = {d["doc_id"]: i for i, d in enumerate(self._corpus)}
        for doc in docs:
            doc_id = doc.get("doc_id", "")
            if doc_id in existing_ids:
                self._corpus[existing_ids[doc_id]] = doc
            else:
                existing_ids[doc_id] = len(self._corpus)
                self._corpus.append(doc)

        self._dirty = True
        self._reindex()

    def clear(self) -> None:
        """코퍼스 + 인덱스 전체 초기화."""
        self._corpus = []
        self._matrix = None
        self._dirty  = False

    # ── 검색 ─────────────────────────────────────────────────────

    def retrieve(self, query: str, k: int = 5) -> list[RetrievedDoc]:
        """
        쿼리와 코사인 유사도 상위 k개 문서를 반환한다.

        Args:
            query: 검색 쿼리 문자열
            k:     반환 문서 수 (기본 5)

        Returns:
            List[RetrievedDoc] — score 내림차순
        """
        if not self._corpus or self._matrix is None:
            return []

        if self._dirty:
            self._reindex()

        # 쿼리 벡터 (이미 fit된 어휘 기반)
        q_vec = self._encoder.transform([query])   # shape (1, vocab_size)
        if q_vec.shape[1] == 0:
            return []

        # 코사인 유사도 (매트릭스는 이미 L2 정규화 완료)
        scores = (self._matrix @ q_vec.T).flatten()   # shape (n_docs,)

        # 상위 k 인덱스
        k = min(k, len(self._corpus))
        top_indices = np.argsort(scores)[::-1][:k]

        results: list[RetrievedDoc] = []
        for idx in top_indices:
            doc  = self._corpus[idx]
            score = float(scores[idx])
            if score <= 0.0:
                break  # 유사도 0 이하는 무관련 문서
            results.append(RetrievedDoc(
                doc_id   = doc.get("doc_id", str(idx)),
                content  = doc.get("content", ""),
                score    = round(score, 4),
                metadata = doc.get("metadata", {}),
            ))
        return results

    def retrieve_all_above(self, query: str, threshold: float = 0.1) -> list[RetrievedDoc]:
        """
        유사도 threshold 이상인 모든 문서 반환.

        Args:
            query:     검색 쿼리
            threshold: 최소 유사도 컷오프 (기본 0.1)
        """
        all_docs = self.retrieve(query, k=len(self._corpus) or 1)
        return [d for d in all_docs if d.score >= threshold]

    # ── 상태 조회 ────────────────────────────────────────────────

    @property
    def corpus_size(self) -> int:
        """현재 코퍼스 문서 수."""
        return len(self._corpus)

    @property
    def is_empty(self) -> bool:
        return len(self._corpus) == 0

    def get_status(self) -> dict[str, Any]:
        return {
            "corpus_size":  self.corpus_size,
            "vocab_size":   self._encoder.vocab_size,
            "encoder_fitted": self._encoder.is_fitted,
            "index_ready":  self._matrix is not None,
        }

    # ── 내부 ────────────────────────────────────────────────────

    def _reindex(self) -> None:
        """코퍼스 전체를 재벡터화하여 내부 매트릭스 갱신."""
        if not self._corpus:
            self._matrix = None
            self._dirty  = False
            return

        texts = [doc.get("content", "") for doc in self._corpus]
        # fit_transform: 코퍼스 전체로 어휘 재구축 + 벡터화
        self._matrix = self._encoder.fit_transform(texts)
        self._dirty  = False
