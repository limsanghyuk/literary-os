"""
tests/test_v489_rag_pipeline_orchestrator.py
V489 RAGPipelineOrchestrator + SP2 통합 테스트
"""
import os
import pytest
from unittest.mock import MagicMock

from literary_system.llm_bridge.llm_context import LLMResponse
from literary_system.llm_bridge.cached_gateway import CachedGateway
from literary_system.rag.rag_context_builder import DramaDocumentFactory
from literary_system.pipelines.rag_pipeline_orchestrator import (
    RAGPipelineOrchestrator,
    RAGSceneResult,
)


# ─── fixtures ──────────────────────────────────────────────────────────────

@pytest.fixture
def mock_gateway():
    gw = MagicMock()
    gw.call.return_value = LLMResponse(
        text="이준혁이 원장실 문을 밀고 들어갔다.",
        provider_id="haiku-mock",
        latency_ms=60.0,
    )
    return gw


@pytest.fixture
def orchestrator(mock_gateway):
    os.environ.pop("ANTHROPIC_API_KEY", None)
    cached = CachedGateway(gateway=mock_gateway, enabled=True)
    orch = RAGPipelineOrchestrator(gateway=cached, top_k=3)
    docs = [
        DramaDocumentFactory.from_scene_text("s01", "이준혁이 복도를 걷는다", episode=1),
        DramaDocumentFactory.from_character_profile("c01", "이준혁", "외과 의사"),
        DramaDocumentFactory.from_setting("loc01", "대학병원", "서울"),
    ]
    orch.index_documents(docs)
    return orch


# ─── 기본 생성 ──────────────────────────────────────────────────────────────

class TestRAGPipelineOrchestratorBasic:

    def test_generate_returns_result(self, orchestrator):
        r = orchestrator.generate(query="이준혁", prompt="씬을 써줘")
        assert isinstance(r, RAGSceneResult)

    def test_scene_text_not_empty(self, orchestrator):
        r = orchestrator.generate(query="이준혁", prompt="씬을 써줘")
        assert r.scene_text.strip()

    def test_enriched_true_when_docs_indexed(self, orchestrator):
        r = orchestrator.generate(query="이준혁 병원", prompt="씬을 써줘")
        assert r.enriched

    def test_provenance_has_doc_ids(self, orchestrator):
        r = orchestrator.generate(query="이준혁", prompt="씬을 써줘")
        assert isinstance(r.provenance.retrieved_doc_ids, list)

    def test_indexed_doc_count(self, orchestrator):
        assert orchestrator.indexed_doc_count == 3

    def test_generate_count_increments(self, orchestrator):
        assert orchestrator.generate_count == 0
        orchestrator.generate(query="이준혁", prompt="씬")
        assert orchestrator.generate_count == 1


# ─── 캐시 통합 ──────────────────────────────────────────────────────────────

class TestCacheIntegration:

    def test_second_call_hits_cache(self, orchestrator, mock_gateway):
        orchestrator.generate(query="이준혁", prompt="씬")
        r2 = orchestrator.generate(query="이준혁", prompt="씬")
        assert r2.cache_hit
        assert mock_gateway.call.call_count == 1

    def test_different_query_causes_miss(self, orchestrator, mock_gateway):
        orchestrator.generate(query="이준혁", prompt="씬")
        orchestrator.generate(query="원장 갈등", prompt="씬")
        assert mock_gateway.call.call_count == 2

    def test_cache_hit_rate(self, orchestrator):
        orchestrator.generate(query="이준혁", prompt="씬")
        orchestrator.generate(query="이준혁", prompt="씬")
        orchestrator.generate(query="이준혁", prompt="씬")
        assert orchestrator.cache_hit_count == 2
        assert orchestrator.cache_hit_rate == pytest.approx(2 / 3)


# ─── ADR-007 Provenance ─────────────────────────────────────────────────────

class TestProvenance:

    def test_provenance_in_result(self, orchestrator):
        r = orchestrator.generate(query="이준혁", prompt="씬")
        d = r.to_dict()
        assert "provenance" in d
        assert "retrieved_doc_ids" in d["provenance"]

    def test_result_serializable(self, orchestrator):
        import json
        r = orchestrator.generate(query="이준혁", prompt="씬")
        json.dumps(r.to_dict())

    def test_cache_hit_provider_is_cache(self, orchestrator):
        orchestrator.generate(query="이준혁", prompt="씬")
        r2 = orchestrator.generate(query="이준혁", prompt="씬")
        assert r2.provider_id == "cache"


# ─── 문서 인덱싱 ────────────────────────────────────────────────────────────

class TestDocumentIndexing:

    def test_index_additional_document(self, orchestrator):
        before = orchestrator.indexed_doc_count
        extra = DramaDocumentFactory.from_scene_text("s99", "추가 씬", episode=5)
        orchestrator.index_document(extra)
        assert orchestrator.indexed_doc_count == before + 1

    def test_generate_without_docs(self, mock_gateway):
        cached = CachedGateway(gateway=mock_gateway, enabled=True)
        orch = RAGPipelineOrchestrator(gateway=cached, top_k=3)
        r = orch.generate(query="이준혁", prompt="씬을 써줘")
        assert not r.enriched  # 문서 없으면 RAG 컨텍스트 없음
