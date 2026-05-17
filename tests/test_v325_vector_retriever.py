"""
V325 Phase 2 테스트 — EmbeddingEncoder + SimpleVectorRetriever + LibrarianRAGBridge
목표: 40 케이스 전체 PASS → 누적 660+ PASS

커버리지:
  [A] EmbeddingEncoder — fit / transform         (10)
  [B] SimpleVectorRetriever — 문서 관리          (8)
  [C] SimpleVectorRetriever — 검색 정확도        (8)
  [D] LibrarianRAGBridge — 색인 구축             (7)
  [E] LibrarianRAGBridge — 씬별 검색             (7)
"""
from __future__ import annotations

import pytest
import numpy as np

from literary_system.retrieval.embedding_encoder import EmbeddingEncoder, _tokenize
from literary_system.retrieval.simple_vector_retriever import SimpleVectorRetriever, RetrievedDoc
from literary_system.retrieval.librarian_rag_bridge import LibrarianRAGBridge


# 공통 픽스처

CORPUS_KO = [
    "고애신이 교회 문을 밀며 들어섰다",
    "유진 초이가 뒤를 따라 걸었다",
    "구동매는 어둠 속에서 지켜보았다",
    "모리 타카시가 기밀 문서를 건넸다",
    "고애신과 유진 초이의 눈이 마주쳤다",
]

DOCS_KO = [
    {"doc_id": "d001", "content": CORPUS_KO[0], "metadata": {"ep": 1}},
    {"doc_id": "d002", "content": CORPUS_KO[1], "metadata": {"ep": 1}},
    {"doc_id": "d003", "content": CORPUS_KO[2], "metadata": {"ep": 2}},
    {"doc_id": "d004", "content": CORPUS_KO[3], "metadata": {"ep": 2}},
    {"doc_id": "d005", "content": CORPUS_KO[4], "metadata": {"ep": 3}},
]


# ════════════════════════════════════════════════════════════════
# [A] EmbeddingEncoder — fit / transform (10)
# ════════════════════════════════════════════════════════════════

class TestEmbeddingEncoder:

    def test_tokenize_korean(self):
        """한국어 음절 토크나이징."""
        tokens = _tokenize("고애신이 교회에 갔다")
        assert len(tokens) > 0

    def test_tokenize_min_length(self):
        """1글자 토큰은 제거."""
        tokens = _tokenize("나 가 이 것")
        assert all(len(t) >= 2 for t in tokens)

    def test_fit_builds_vocabulary(self):
        """fit() 후 vocabulary_ 생성."""
        enc = EmbeddingEncoder()
        enc.fit(CORPUS_KO)
        assert len(enc.vocabulary_) > 0
        assert enc.is_fitted

    def test_vocab_size_property(self):
        """vocab_size 프로퍼티."""
        enc = EmbeddingEncoder()
        enc.fit(CORPUS_KO)
        assert enc.vocab_size == len(enc.vocabulary_)

    def test_transform_shape(self):
        """transform() 출력 shape (n_texts, vocab_size)."""
        enc = EmbeddingEncoder()
        enc.fit(CORPUS_KO)
        matrix = enc.transform(CORPUS_KO)
        assert matrix.shape == (len(CORPUS_KO), enc.vocab_size)

    def test_transform_dtype_float32(self):
        """출력 dtype이 float32."""
        enc = EmbeddingEncoder()
        enc.fit(CORPUS_KO)
        matrix = enc.transform(CORPUS_KO)
        assert matrix.dtype == np.float32

    def test_l2_normalized(self):
        """각 행의 L2 놈 ≈ 1 (영벡터 제외)."""
        enc = EmbeddingEncoder()
        matrix = enc.fit_transform(CORPUS_KO)
        norms = np.linalg.norm(matrix, axis=1)
        non_zero = norms > 0
        if non_zero.any():
            assert np.allclose(norms[non_zero], 1.0, atol=1e-5)

    def test_fit_transform_equals_fit_then_transform(self):
        """fit_transform() == fit().transform()."""
        enc1 = EmbeddingEncoder()
        m1 = enc1.fit_transform(CORPUS_KO)
        enc2 = EmbeddingEncoder()
        enc2.fit(CORPUS_KO)
        m2 = enc2.transform(CORPUS_KO)
        assert np.allclose(m1, m2, atol=1e-6)

    def test_empty_corpus(self):
        """빈 코퍼스 fit → vocab_size=0."""
        enc = EmbeddingEncoder()
        enc.fit([])
        assert enc.vocab_size == 0
        assert enc.is_fitted

    def test_transform_before_fit_raises(self):
        """fit() 없이 transform() 호출 시 RuntimeError."""
        enc = EmbeddingEncoder()
        with pytest.raises(RuntimeError):
            enc.transform(["테스트"])


# ════════════════════════════════════════════════════════════════
# [B] SimpleVectorRetriever — 문서 관리 (8)
# ════════════════════════════════════════════════════════════════

class TestSimpleVectorRetrieverManagement:

    def test_initial_empty(self):
        """초기 상태: corpus_size=0, is_empty=True."""
        r = SimpleVectorRetriever()
        assert r.corpus_size == 0
        assert r.is_empty

    def test_add_documents_increments_size(self):
        """add_documents() 후 corpus_size 증가."""
        r = SimpleVectorRetriever()
        r.add_documents(DOCS_KO[:3])
        assert r.corpus_size == 3

    def test_add_empty_list_no_change(self):
        """빈 리스트 추가 시 corpus_size 불변."""
        r = SimpleVectorRetriever()
        r.add_documents(DOCS_KO)
        size_before = r.corpus_size
        r.add_documents([])
        assert r.corpus_size == size_before

    def test_duplicate_doc_id_overwrite(self):
        """동일 doc_id 추가 시 기존 문서 덮어씀."""
        r = SimpleVectorRetriever()
        r.add_documents([{"doc_id": "d001", "content": "원본", "metadata": {}}])
        r.add_documents([{"doc_id": "d001", "content": "수정본", "metadata": {}}])
        assert r.corpus_size == 1

    def test_clear_resets_state(self):
        """clear() 후 corpus_size=0, is_empty=True."""
        r = SimpleVectorRetriever()
        r.add_documents(DOCS_KO)
        r.clear()
        assert r.corpus_size == 0
        assert r.is_empty

    def test_get_status_keys(self):
        """get_status() 필수 키 존재."""
        r = SimpleVectorRetriever()
        status = r.get_status()
        for key in ("corpus_size", "vocab_size", "encoder_fitted", "index_ready"):
            assert key in status

    def test_add_multiple_batches(self):
        """여러 배치 add_documents() → 누적 합산."""
        r = SimpleVectorRetriever()
        r.add_documents(DOCS_KO[:2])
        r.add_documents(DOCS_KO[2:])
        assert r.corpus_size == len(DOCS_KO)

    def test_retrieve_empty_returns_empty(self):
        """코퍼스 없으면 retrieve() → []."""
        r = SimpleVectorRetriever()
        result = r.retrieve("고애신", k=3)
        assert result == []


# ════════════════════════════════════════════════════════════════
# [C] SimpleVectorRetriever — 검색 정확도 (8)
# ════════════════════════════════════════════════════════════════

class TestSimpleVectorRetrieverSearch:

    @pytest.fixture
    def retriever(self):
        r = SimpleVectorRetriever()
        r.add_documents(DOCS_KO)
        return r

    def test_retrieve_returns_list(self, retriever):
        """retrieve() 반환 타입이 list."""
        result = retriever.retrieve("고애신이 교회")
        assert isinstance(result, list)

    def test_retrieve_doc_type(self, retriever):
        """반환 요소가 RetrievedDoc 인스턴스."""
        result = retriever.retrieve("고애신이 교회", k=1)
        if result:
            assert isinstance(result[0], RetrievedDoc)

    def test_retrieve_k_limit(self, retriever):
        """k=2이면 최대 2개 반환."""
        result = retriever.retrieve("고애신이 교회", k=2)
        assert len(result) <= 2

    def test_retrieve_score_descending(self, retriever):
        """결과가 score 내림차순."""
        result = retriever.retrieve("고애신이 유진", k=5)
        scores = [r.score for r in result]
        assert scores == sorted(scores, reverse=True)

    def test_top_result_relevance(self, retriever):
        """TF-IDF 코퍼스 토큰 쿼리 → 관련 문서 반환."""
        # 코퍼스에 실제 있는 토큰 사용 (TF-IDF 정확 매칭)
        result = retriever.retrieve("고애신이 교회", k=3)
        assert len(result) > 0
        top_content = result[0].content
        assert "고애신" in top_content

    def test_retrieve_metadata_preserved(self, retriever):
        """검색 결과에 metadata 보존."""
        result = retriever.retrieve("고애신이 교회", k=1)
        if result:
            assert isinstance(result[0].metadata, dict)

    def test_retrieve_all_above_threshold(self, retriever):
        """retrieve_all_above() — threshold 미만 결과 제외."""
        result = retriever.retrieve_all_above("고애신이 교회", threshold=0.01)
        assert all(r.score >= 0.01 for r in result)

    def test_unknown_query_low_scores(self, retriever):
        """무관련 쿼리 → 빈 결과 또는 저점수."""
        result = retriever.retrieve("파이썬 알고리즘 데이터베이스", k=5)
        assert all(r.score < 0.9 for r in result)


# ════════════════════════════════════════════════════════════════
# [D] LibrarianRAGBridge — 색인 구축 (7)
# ════════════════════════════════════════════════════════════════

class TestLibrarianRAGBridgeIndex:

    def _make_catalog(self):
        return {
            "characters": [
                {"id": "c001", "name": "고애신", "profile": "양반가 여식. 의병 활동."},
                {"id": "c002", "name": "유진 초이", "profile": "조선인 출신 미국 군인."},
                {"id": "c003", "name": "구동매", "profile": "행상단 출신 낭인."},
            ],
            "scenes": [
                {"scene_id": "s001", "summary": "고애신이 교회에서 총기를 수령하는 장면."},
                {"scene_id": "s002", "summary": "유진이 일본군을 저지하는 장면."},
            ],
            "motifs": [
                {"motif_id": "m001", "description": "호롱불 — 고애신 등장 전조."},
            ],
            "relations": [],
        }

    def test_index_from_catalog_returns_count(self):
        """index_from_catalog() → 색인된 문서 수 반환."""
        bridge = LibrarianRAGBridge()
        count = bridge.index_from_catalog(self._make_catalog())
        assert count > 0

    def test_index_characters(self):
        """인물 3명 색인 후 corpus_size >= 3."""
        bridge = LibrarianRAGBridge()
        bridge.index_from_catalog(self._make_catalog())
        assert bridge.get_status()["corpus_size"] >= 3

    def test_index_all_types(self):
        """인물 + 씬 + 모티프 모두 색인."""
        bridge = LibrarianRAGBridge()
        count = bridge.index_from_catalog(self._make_catalog())
        assert count == 6

    def test_index_raw_documents(self):
        """index_raw_documents() 직접 색인."""
        bridge = LibrarianRAGBridge()
        n = bridge.index_raw_documents(DOCS_KO)
        assert n == len(DOCS_KO)
        assert bridge.get_status()["corpus_size"] == len(DOCS_KO)

    def test_empty_catalog_no_error(self):
        """빈 카탈로그 색인 → 오류 없음."""
        bridge = LibrarianRAGBridge()
        count = bridge.index_from_catalog({})
        assert count == 0

    def test_retriever_property(self):
        """retriever 프로퍼티가 SimpleVectorRetriever 반환."""
        bridge = LibrarianRAGBridge()
        assert isinstance(bridge.retriever, SimpleVectorRetriever)

    def test_get_status_indexed_count(self):
        """get_status()에 indexed_count 포함."""
        bridge = LibrarianRAGBridge()
        bridge.index_from_catalog(self._make_catalog())
        status = bridge.get_status()
        assert "indexed_count" in status
        assert status["indexed_count"] > 0


# ════════════════════════════════════════════════════════════════
# [E] LibrarianRAGBridge — 씬별 검색 (7)
# ════════════════════════════════════════════════════════════════

class TestLibrarianRAGBridgeSearch:

    @pytest.fixture
    def bridge(self):
        b = LibrarianRAGBridge()
        b.index_from_catalog({
            "characters": [
                {"id": "c001", "name": "고애신", "profile": "양반가 여식 의병"},
                {"id": "c002", "name": "유진 초이", "profile": "미국 군인 조선"},
                {"id": "c003", "name": "구동매", "profile": "낭인 행상"},
            ],
            "scenes": [
                {"scene_id": "s001", "summary": "고애신 교회 총기 수령"},
                {"scene_id": "s002", "summary": "유진 일본군 저지"},
            ],
            "motifs": [
                {"motif_id": "m001", "description": "호롱불 고애신 등장"},
            ],
            "relations": [],
        })
        return b

    def test_retrieve_for_scene_returns_list(self, bridge):
        """retrieve_for_scene() 반환 타입이 list."""
        result = bridge.retrieve_for_scene("교회 총기")
        assert isinstance(result, list)

    def test_retrieve_for_scene_k_limit(self, bridge):
        """k=2 시 최대 2개 반환."""
        result = bridge.retrieve_for_scene("교회", k=2)
        assert len(result) <= 2

    def test_retrieve_characters_type_filter(self, bridge):
        """retrieve_characters() → type=character만 반환."""
        result = bridge.retrieve_characters("의병 여식", k=5)
        assert all(r.metadata.get("type") == "character" for r in result)

    def test_retrieve_scenes_type_filter(self, bridge):
        """retrieve_scenes() → type=scene만 반환."""
        result = bridge.retrieve_scenes("교회 총기", k=5)
        assert all(r.metadata.get("type") == "scene" for r in result)

    def test_retrieve_motifs_type_filter(self, bridge):
        """retrieve_motifs() → type=motif만 반환."""
        result = bridge.retrieve_motifs("호롱불", k=5)
        assert all(r.metadata.get("type") == "motif" for r in result)

    def test_retrieve_top_result_relevant(self, bridge):
        """관련 쿼리 → score > 0 결과 반환."""
        result = bridge.retrieve_for_scene("고애신 교회 총기 수령", k=5)
        assert len(result) > 0
        assert result[0].score > 0

    def test_retrieve_for_scene_doc_id_format(self, bridge):
        """doc_id 형식이 type_id 패턴 (char_, scene_, motif_)."""
        result = bridge.retrieve_for_scene("고애신", k=10)
        for doc in result:
            assert any(
                doc.doc_id.startswith(prefix)
                for prefix in ("char_", "scene_", "motif_")
            )
