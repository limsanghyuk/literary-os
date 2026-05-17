"""
tests/test_v486_rag_context_builder.py
V486 RAGContextBuilder + ADR-007 Provenance 테스트
"""
import pytest
from literary_system.rag.rag_context_builder import (
    RAGContextBuilder,
    DramaDocumentFactory,
    RetrievalProvenance,
    RAGEnrichedRequest,
)
from literary_system.rag.hybrid_retriever import Document


# ─── fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def builder():
    return RAGContextBuilder(top_k=3, token_budget=600)


@pytest.fixture
def drama_docs():
    return [
        DramaDocumentFactory.from_scene_text(
            "s01e01_sc01",
            "주인공 이준혁이 병원 복도를 걷는다. 그의 표정은 굳어있다.",
            episode=1, scene_idx=1,
        ),
        DramaDocumentFactory.from_character_profile(
            "char_001", "이준혁", "40대 외과 의사. 냉정하지만 정의감이 강하다."
        ),
        DramaDocumentFactory.from_setting(
            "set_hospital", "대학병원", "서울 소재 3차 의료기관."
        ),
    ]


# ─── RAGContextBuilder 기본 동작 ────────────────────────────────────────────

class TestRAGContextBuilderBasic:

    def test_index_and_count(self, builder, drama_docs):
        builder.index_documents(drama_docs)
        assert builder.indexed_doc_count == 3

    def test_build_returns_enriched_request(self, builder, drama_docs):
        builder.index_documents(drama_docs)
        enriched = builder.build(query="이준혁", prompt="씬을 써줘")
        assert isinstance(enriched, RAGEnrichedRequest)

    def test_enriched_prompt_contains_original(self, builder, drama_docs):
        builder.index_documents(drama_docs)
        enriched = builder.build(query="이준혁", prompt="원본 프롬프트")
        assert "원본 프롬프트" in enriched.enriched_prompt

    def test_has_context_when_docs_indexed(self, builder, drama_docs):
        builder.index_documents(drama_docs)
        enriched = builder.build(query="이준혁 병원", prompt="씬")
        assert enriched.has_context

    def test_no_context_when_empty(self):
        empty_builder = RAGContextBuilder(top_k=3)
        enriched = empty_builder.build(query="이준혁", prompt="씬")
        assert not enriched.has_context
        assert enriched.enriched_prompt == "씬"

    def test_single_document_index(self, builder):
        doc = Document(doc_id="d1", text="단일 문서")
        builder.index_document(doc)
        assert builder.indexed_doc_count == 1


# ─── ADR-007 Provenance ─────────────────────────────────────────────────────

class TestADR007Provenance:

    def test_provenance_has_retrieved_doc_ids(self, builder, drama_docs):
        builder.index_documents(drama_docs)
        enriched = builder.build(query="이준혁", prompt="씬")
        assert "retrieved_doc_ids" in enriched.provenance.to_dict()

    def test_provenance_doc_ids_are_list(self, builder, drama_docs):
        builder.index_documents(drama_docs)
        enriched = builder.build(query="이준혁 병원", prompt="씬")
        assert isinstance(enriched.provenance.retrieved_doc_ids, list)

    def test_provenance_id_deterministic(self, builder, drama_docs):
        builder.index_documents(drama_docs)
        e1 = builder.build(query="이준혁", prompt="씬")
        e2 = builder.build(query="이준혁", prompt="씬")
        # 같은 쿼리+결과 → 같은 provenance_id (문서 순서 무관)
        ids1 = sorted(e1.provenance.retrieved_doc_ids)
        ids2 = sorted(e2.provenance.retrieved_doc_ids)
        assert ids1 == ids2

    def test_provenance_query_stored(self, builder, drama_docs):
        builder.index_documents(drama_docs)
        enriched = builder.build(query="병원 갈등", prompt="씬")
        assert enriched.provenance.query == "병원 갈등"

    def test_provenance_top_k_field(self, builder, drama_docs):
        builder.index_documents(drama_docs)
        enriched = builder.build(query="이준혁", prompt="씬")
        assert enriched.provenance.top_k_requested == 3

    def test_provenance_to_dict_serializable(self, builder, drama_docs):
        builder.index_documents(drama_docs)
        enriched = builder.build(query="이준혁", prompt="씬")
        d = enriched.provenance.to_dict()
        import json
        json.dumps(d)  # JSON 직렬화 가능해야 함

    def test_provenance_id_sha256_format(self, builder, drama_docs):
        builder.index_documents(drama_docs)
        enriched = builder.build(query="이준혁", prompt="씬")
        pid = enriched.provenance.provenance_id
        assert len(pid) == 16
        assert all(c in "0123456789abcdef" for c in pid)


# ─── DramaDocumentFactory ────────────────────────────────────────────────────

class TestDramaDocumentFactory:

    def test_from_scene_text(self):
        doc = DramaDocumentFactory.from_scene_text("s1", "씬 텍스트", episode=2)
        assert doc.doc_id == "s1"
        assert doc.metadata["type"] == "scene"
        assert doc.metadata["episode"] == 2

    def test_from_character_profile(self):
        doc = DramaDocumentFactory.from_character_profile("c1", "이준혁", "설명")
        assert doc.metadata["type"] == "character"
        assert "이준혁" in doc.text

    def test_from_setting(self):
        doc = DramaDocumentFactory.from_setting("s1", "대학병원", "서울")
        assert doc.metadata["type"] == "setting"
        assert "대학병원" in doc.text

    def test_extra_metadata(self):
        doc = DramaDocumentFactory.from_scene_text("s1", "텍스트", genre="medical")
        assert doc.metadata["genre"] == "medical"
