"""
V325 - LibrarianRAGBridge  (Phase 2)
ChiefLibrarian 카탈로그 ↔ SimpleVectorRetriever 연결.

설계 원칙 (P2 외과적 통합):
  - ChiefLibrarian 기존 코드 무수정
  - StorageDispatcher가 저장한 catalog를 읽어 SimpleVectorRetriever에 주입
  - retrieve_for_scene()으로 씬별 관련 인물·씬·모티프 문서 반환
  - LLM 0회. 완전 로컬.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from literary_system.retrieval.simple_vector_retriever import RetrievedDoc, SimpleVectorRetriever


# ────────────────────────────────────────────────────────────────
# LibrarianRAGBridge
# ────────────────────────────────────────────────────────────────

class LibrarianRAGBridge:
    """
    ChiefLibrarian 카탈로그 → SimpleVectorRetriever 색인 + 씬별 검색.

    사용 예:
        bridge = LibrarianRAGBridge()
        bridge.index_from_catalog(catalog_dict)
        docs = bridge.retrieve_for_scene("고애신이 교회에 가는 장면", k=5)
    """

    def __init__(
        self,
        retriever: SimpleVectorRetriever | None = None,
        max_features: int = 3000,
    ) -> None:
        self._retriever = retriever or SimpleVectorRetriever(max_features=max_features)
        self._indexed_count: int = 0

    # ── 색인 구축 ────────────────────────────────────────────────

    def index_from_catalog(self, catalog: dict[str, Any]) -> int:
        """
        ChiefLibrarian catalog dict → SimpleVectorRetriever 색인 구축.

        catalog 구조 (CatalogBuilder 출력 기준):
          {
            "characters": [{"id": ..., "name": ..., "profile": ..., ...}],
            "scenes":     [{"scene_id": ..., "summary": ..., ...}],
            "motifs":     [{"motif_id": ..., "description": ..., ...}],
            "relations":  [...],
          }

        Args:
            catalog: ChiefLibrarian 카탈로그 dict

        Returns:
            색인된 문서 수
        """
        docs: list[dict[str, Any]] = []

        # 인물 카탈로그
        for char in catalog.get("characters", []):
            char_id = char.get("id") or char.get("character_id", "")
            name    = char.get("name", "")
            profile = char.get("profile", "") or char.get("description", "")
            content = f"{name} {profile}".strip()
            if content:
                docs.append({
                    "doc_id":   f"char_{char_id}",
                    "content":  content,
                    "metadata": {"type": "character", "source": char},
                })

        # 씬 카탈로그
        for scene in catalog.get("scenes", []):
            scene_id = scene.get("scene_id", "")
            summary  = scene.get("summary", "") or scene.get("text", "")
            if summary:
                docs.append({
                    "doc_id":   f"scene_{scene_id}",
                    "content":  summary,
                    "metadata": {"type": "scene", "source": scene},
                })

        # 모티프 카탈로그
        for motif in catalog.get("motifs", []):
            motif_id = motif.get("motif_id", "")
            desc     = motif.get("description", "") or motif.get("content", "")
            if desc:
                docs.append({
                    "doc_id":   f"motif_{motif_id}",
                    "content":  desc,
                    "metadata": {"type": "motif", "source": motif},
                })

        if docs:
            self._retriever.add_documents(docs)
        self._indexed_count = self._retriever.corpus_size
        return len(docs)

    def index_from_file(self, catalog_path: str | Path) -> int:
        """
        JSON 파일에서 카탈로그를 로드하여 색인.

        Args:
            catalog_path: catalog.json 경로

        Returns:
            색인된 문서 수
        """
        path = Path(catalog_path)
        if not path.exists():
            return 0
        with path.open("r", encoding="utf-8") as f:
            catalog = json.load(f)
        return self.index_from_catalog(catalog)

    def index_raw_documents(self, docs: list[dict[str, Any]]) -> int:
        """
        임의 문서 리스트를 직접 색인 (테스트·독립 사용).

        Args:
            docs: List[{doc_id, content, metadata}]

        Returns:
            색인된 문서 수
        """
        self._retriever.add_documents(docs)
        self._indexed_count = self._retriever.corpus_size
        return len(docs)

    # ── 검색 ─────────────────────────────────────────────────────

    def retrieve_for_scene(
        self,
        scene_context: str,
        k: int = 5,
        doc_types: list[str] | None = None,
    ) -> list[RetrievedDoc]:
        """
        씬 컨텍스트로 관련 문서 검색.

        Args:
            scene_context: 씬 설명 / 쿼리 문자열
            k:             최대 반환 수
            doc_types:     필터링할 문서 타입 ["character", "scene", "motif"]
                           None이면 전체 반환

        Returns:
            List[RetrievedDoc] score 내림차순
        """
        results = self._retriever.retrieve(scene_context, k=k * 2)  # 필터 여분 확보

        if doc_types:
            results = [
                r for r in results
                if r.metadata.get("type") in doc_types
            ]

        return results[:k]

    def retrieve_characters(self, scene_context: str, k: int = 5) -> list[RetrievedDoc]:
        """씬에 등장할 인물 후보 검색."""
        return self.retrieve_for_scene(scene_context, k=k, doc_types=["character"])

    def retrieve_scenes(self, scene_context: str, k: int = 5) -> list[RetrievedDoc]:
        """관련 과거 씬 검색 (연속성 유지용)."""
        return self.retrieve_for_scene(scene_context, k=k, doc_types=["scene"])

    def retrieve_motifs(self, scene_context: str, k: int = 5) -> list[RetrievedDoc]:
        """관련 모티프·오브제 검색."""
        return self.retrieve_for_scene(scene_context, k=k, doc_types=["motif"])

    # ── 상태 조회 ────────────────────────────────────────────────

    def get_status(self) -> dict[str, Any]:
        return {
            "indexed_count": self._indexed_count,
            **self._retriever.get_status(),
        }

    @property
    def retriever(self) -> SimpleVectorRetriever:
        return self._retriever
