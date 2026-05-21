"""tests/integration/test_qdrant_live.py — V588 Qdrant 통합 테스트.

ADR-049 | G47 | SP-A.1
Qdrant 미실행 시 자동 SKIP. CI qdrant_integration 잡에서만 실행.
"""
import pytest

# Qdrant 미실행 시 전체 SKIP
qdrant_client = pytest.importorskip("qdrant_client", reason="qdrant_client 미설치 — SKIP")


@pytest.mark.integration
class TestQdrantLive:
    """Qdrant 실 연결 테스트 — 로컬 Docker Qdrant 필요 (port 6333)."""

    @pytest.fixture(autouse=True)
    def _require_qdrant(self):
        try:
            from qdrant_client import QdrantClient
            client = QdrantClient(host="localhost", port=6333, timeout=2.0)
            client.get_collections()
        except Exception:
            pytest.skip("Qdrant 서버 미실행 — SKIP (docker-compose up qdrant 필요)")

    def test_qdrant_connection(self):
        """Qdrant 서버 접속 확인."""
        from qdrant_client import QdrantClient
        client = QdrantClient(host="localhost", port=6333, timeout=2.0)
        collections = client.get_collections()
        assert hasattr(collections, "collections")

    def test_qdrant_create_collection(self):
        """컬렉션 생성/삭제 사이클."""
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, VectorParams
        client = QdrantClient(host="localhost", port=6333)
        cname = "test_v588_temp"
        try:
            client.recreate_collection(
                collection_name=cname,
                vectors_config=VectorParams(size=128, distance=Distance.COSINE),
            )
            info = client.get_collection(cname)
            assert info is not None
        finally:
            try:
                client.delete_collection(cname)
            except Exception:
                pass

    def test_qdrant_upsert_search(self):
        """벡터 upsert 후 검색 SLO < 1초 검증 (ADR-049 C1)."""
        import time
        from qdrant_client import QdrantClient
        from qdrant_client.models import Distance, PointStruct, VectorParams
        client = QdrantClient(host="localhost", port=6333)
        cname = "test_v588_slo"
        try:
            client.recreate_collection(
                collection_name=cname,
                vectors_config=VectorParams(size=4, distance=Distance.COSINE),
            )
            client.upsert(
                collection_name=cname,
                points=[
                    PointStruct(id=i, vector=[float(i % 4) * 0.1] * 4, payload={"scene": f"s{i:03d}"})
                    for i in range(10)
                ],
            )
            t0 = time.monotonic()
            results = client.search(
                collection_name=cname,
                query_vector=[0.1, 0.2, 0.3, 0.4],
                limit=5,
            )
            elapsed = time.monotonic() - t0
            assert elapsed < 1.0, f"SLO 초과: {elapsed:.3f}s > 1.0s"
            assert len(results) > 0
        finally:
            try:
                client.delete_collection(cname)
            except Exception:
                pass
