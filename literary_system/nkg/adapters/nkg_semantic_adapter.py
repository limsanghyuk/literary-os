"""NKGSemanticAdapter — V401.
NKGSearchEngine을 SemanticScorer 인터페이스로 감싸는 어댑터.
DualSemanticScorer에서 사용. LLM 0 calls.

설계 결정 (3인 합의):
  - 교체형이 아닌 병렬형 — TF-IDF와 함께 사용
  - NKG가 없거나 비었으면 is_ready()=False → DualScorer가 TF-IDF로 fallback
  - RRF 점수 집계: top_k 결과 중 node_text 토큰 겹침 가중 평균
  - 닭-달걀 해결: 첫 실행엔 NKG 비어→TF-IDF, 씬 쌓이면 자동 활성화
"""
from __future__ import annotations
import re
from typing import Optional

from literary_system.nkg.graph_store import NKGGraphStore
from literary_system.nkg.search.engine import NKGSearchEngine, SearchResult


def _simple_tokenize(text: str) -> list:
    return [t for t in re.findall(r"[\w가-힣]+", text.lower()) if len(t) > 1]


class NKGSemanticAdapter:
    """NKGSearchEngine → SemanticScorer 어댑터 (V401)."""

    TOP_K: int = 3

    def __init__(self, nkg: NKGGraphStore) -> None:
        self._nkg = nkg
        self._engine: Optional[NKGSearchEngine] = None

    def is_ready(self) -> bool:
        """NKG에 노드가 1개 이상 있으면 True."""
        return self._nkg.node_count() > 0

    def _ensure_engine(self) -> NKGSearchEngine:
        if self._engine is None:
            self._engine = NKGSearchEngine(self._nkg)
            self._engine.build_index()
        return self._engine

    def score(self, node_text: str, scene_goal: str) -> float:
        """[0, 1] NKG 기반 의미 유사도. NKG 비어있으면 0.0."""
        if not self.is_ready():
            return 0.0
        try:
            engine = self._ensure_engine()
            results: list = engine.search(scene_goal, top_k=self.TOP_K)
            if not results:
                return 0.0
            total_rrf = sum(r.score for r in results)
            if total_rrf == 0.0:
                return 0.0
            node_tokens = set(_simple_tokenize(node_text))
            weighted = 0.0
            for r in results:
                label_tokens = set(_simple_tokenize(r.label))
                overlap = (len(node_tokens & label_tokens)
                           / max(len(node_tokens | label_tokens), 1))
                weighted += r.score * overlap
            raw = weighted / max(total_rrf, 1e-9)
            return float(max(0.0, min(1.0, raw)))
        except Exception:
            return 0.0

    def rebuild_index(self) -> int:
        """NKG 변경 후 인덱스 재빌드. 노드 수 반환."""
        self._engine = NKGSearchEngine(self._nkg)
        return self._engine.build_index()
