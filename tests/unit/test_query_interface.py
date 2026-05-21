"""tests/unit/test_query_interface.py — V588 SP-A.1 QueryInterface 유닛 테스트.

ADR-049 | G47 | +30 PASS 목표
LLM-0: 외부 LLM 호출 없음. 전체 MOCK 기반.
"""
import pytest
from unittest.mock import MagicMock, patch

from literary_system.db.query_interface import (
    AggregateResult,
    CharacterResult,
    QueryInterface,
    SceneResult,
)
from literary_system.db.losdb_client import LOSDBClient, LOSDBClientRecord
from literary_system.db.schema_registry import BackendType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture()
def mock_client():
    """LOSDBClient MOCK — SQL + VECTOR + GRAPH 3백엔드."""
    client = MagicMock(spec=LOSDBClient)
    client.available_backends.return_value = [
        BackendType.SQL, BackendType.VECTOR, BackendType.GRAPH
    ]
    client.check_all_connections.return_value = {
        BackendType.SQL: True,
        BackendType.VECTOR: True,
        BackendType.GRAPH: True,
    }
    return client


@pytest.fixture()
def qi(mock_client):
    """QueryInterface with mock_client."""
    return QueryInterface(client=mock_client)


@pytest.fixture()
def qi_no_client():
    """QueryInterface without LOSDBClient (no_client 모드)."""
    return QueryInterface(client=None)


def _make_record(rec_id: str, backend: BackendType, label: str, **meta) -> LOSDBClientRecord:
    return LOSDBClientRecord(id=rec_id, backend=backend, label=label, metadata=meta)


# ---------------------------------------------------------------------------
# TC01~TC05: 기본 인스턴스
# ---------------------------------------------------------------------------

class TestQueryInterfaceInit:
    def test_tc01_init_with_client(self, mock_client):
        """TC01: LOSDBClient 있는 경우 초기화."""
        qi = QueryInterface(client=mock_client)
        assert qi is not None

    def test_tc02_init_without_client(self):
        """TC02: LOSDBClient 없는 경우 초기화."""
        qi = QueryInterface(client=None)
        assert qi is not None

    def test_tc03_slo_default(self, qi):
        """TC03: 기본 SLO = 1.0초."""
        assert qi.SLO_RESPONSE_SEC == 1.0

    def test_tc04_custom_timeout(self, mock_client):
        """TC04: 커스텀 timeout 설정."""
        qi = QueryInterface(client=mock_client, response_timeout_sec=2.0)
        assert qi._timeout == 2.0

    def test_tc05_no_client_timeout_default(self):
        """TC05: 클라이언트 없어도 기본 timeout."""
        qi = QueryInterface()
        assert qi._timeout == 1.0


# ---------------------------------------------------------------------------
# TC06~TC12: find_scenes
# ---------------------------------------------------------------------------

class TestFindScenes:
    def test_tc06_no_client_returns_empty(self, qi_no_client):
        """TC06: 클라이언트 없으면 빈 리스트 반환."""
        result = qi_no_client.find_scenes(character="이준혁")
        assert result == []

    def test_tc07_find_by_character_sql(self, qi, mock_client):
        """TC07: 캐릭터 이름으로 SQL 검색."""
        mock_client.query_by_label.return_value = [
            _make_record("s001", BackendType.SQL, "이준혁", episode=1),
            _make_record("s002", BackendType.SQL, "이준혁", episode=2),
        ]
        results = qi.find_scenes(character="이준혁")
        assert len(results) == 2
        assert all(isinstance(r, SceneResult) for r in results)

    def test_tc08_episode_range_filter(self, qi, mock_client):
        """TC08: episode_range 필터 적용."""
        mock_client.query_by_label.return_value = [
            _make_record("s001", BackendType.SQL, "이준혁", episode=1),
            _make_record("s002", BackendType.SQL, "이준혁", episode=5),
            _make_record("s003", BackendType.SQL, "이준혁", episode=10),
        ]
        results = qi.find_scenes(character="이준혁", episode_range=(1, 5))
        assert len(results) == 2
        assert all(r.episode <= 5 for r in results)

    def test_tc09_limit_respected(self, qi, mock_client):
        """TC09: limit 파라미터 적용."""
        mock_client.query_by_label.return_value = [
            _make_record(f"s{i:03d}", BackendType.SQL, "이준혁", episode=i)
            for i in range(20)
        ]
        results = qi.find_scenes(character="이준혁", limit=5)
        assert len(results) <= 5

    def test_tc10_dedup_same_scene_id(self, qi, mock_client):
        """TC10: 동일 scene_id 중복 제거."""
        mock_client.query_by_label.return_value = [
            _make_record("s001", BackendType.SQL, "이준혁", episode=1),
            _make_record("s001", BackendType.SQL, "이준혁", episode=1),
        ]
        results = qi.find_scenes(character="이준혁")
        assert len(results) == 1

    def test_tc11_vector_search_no_adapter(self, qi, mock_client):
        """TC11: Vector 백엔드 없으면 vector 검색 생략."""
        mock_client.available_backends.return_value = [BackendType.SQL]
        results = qi.find_scenes(similar_to=[0.1, 0.2, 0.3])
        assert results == []

    def test_tc12_find_scenes_returns_scene_result_type(self, qi, mock_client):
        """TC12: 반환 타입 SceneResult 검증."""
        mock_client.query_by_label.return_value = [
            _make_record("s001", BackendType.SQL, "이준혁", episode=1),
        ]
        results = qi.find_scenes(character="이준혁")
        assert isinstance(results[0], SceneResult)
        assert results[0].scene_id == "s001"


# ---------------------------------------------------------------------------
# TC13~TC18: find_characters
# ---------------------------------------------------------------------------

class TestFindCharacters:
    def test_tc13_no_client_returns_empty(self, qi_no_client):
        """TC13: 클라이언트 없으면 빈 리스트."""
        result = qi_no_client.find_characters([0.1, 0.2])
        assert result == []

    def test_tc14_vector_backend_missing(self, qi, mock_client):
        """TC14: VECTOR 백엔드 없으면 빈 리스트."""
        mock_client.available_backends.return_value = [BackendType.SQL]
        result = qi.find_characters([0.1, 0.2])
        assert result == []

    def test_tc15_find_characters_returns_list(self, qi, mock_client):
        """TC15: 반환 타입 List[CharacterResult]."""
        vec_adapter = MagicMock()
        vec_adapter.search.return_value = [("char001", 0.95), ("char002", 0.82)]
        mock_client.get_backend.return_value = vec_adapter
        results = qi.find_characters([0.1, 0.2, 0.3])
        assert isinstance(results, list)
        assert all(isinstance(r, CharacterResult) for r in results)

    def test_tc16_similarity_values(self, qi, mock_client):
        """TC16: similarity 점수 반환 검증."""
        vec_adapter = MagicMock()
        vec_adapter.search.return_value = [("char001", 0.95)]
        mock_client.get_backend.return_value = vec_adapter
        results = qi.find_characters([0.1, 0.2])
        assert results[0].similarity == pytest.approx(0.95)

    def test_tc17_limit_applied(self, qi, mock_client):
        """TC17: limit 적용."""
        vec_adapter = MagicMock()
        vec_adapter.search.return_value = [(f"char{i:03d}", 0.9 - i * 0.01) for i in range(20)]
        mock_client.get_backend.return_value = vec_adapter
        results = qi.find_characters([0.1, 0.2], limit=5)
        assert len(results) <= 5

    def test_tc18_character_result_to_dict(self, qi, mock_client):
        """TC18: CharacterResult.to_dict() 직렬화."""
        vec_adapter = MagicMock()
        vec_adapter.search.return_value = [("char001", 0.88)]
        mock_client.get_backend.return_value = vec_adapter
        results = qi.find_characters([0.1, 0.2])
        d = results[0].to_dict()
        assert "character_id" in d
        assert "similarity" in d


# ---------------------------------------------------------------------------
# TC19~TC24: cross_backend_aggregate
# ---------------------------------------------------------------------------

class TestCrossBackendAggregate:
    def test_tc19_no_client_returns_empty(self, qi_no_client):
        """TC19: 클라이언트 없으면 빈 리스트."""
        result = qi_no_client.cross_backend_aggregate(group_by="scene")
        assert result == []

    def test_tc20_count_metric(self, qi, mock_client):
        """TC20: metric=count 집계."""
        mock_client.cross_query.return_value = [
            _make_record("s001", BackendType.SQL, "scene"),
            _make_record("s002", BackendType.VECTOR, "scene"),
        ]
        results = qi.cross_backend_aggregate(group_by="scene", metric="count")
        assert len(results) == 1
        assert results[0].metric_value == 2.0

    def test_tc21_score_sum_metric(self, qi, mock_client):
        """TC21: metric=score_sum 집계."""
        mock_client.cross_query.return_value = [
            _make_record("s001", BackendType.SQL, "scene", score=0.8),
            _make_record("s002", BackendType.SQL, "scene", score=0.6),
        ]
        results = qi.cross_backend_aggregate(group_by="scene", metric="score_sum")
        assert results[0].metric_value == pytest.approx(1.4)

    def test_tc22_score_avg_metric(self, qi, mock_client):
        """TC22: metric=score_avg 집계."""
        mock_client.cross_query.return_value = [
            _make_record("s001", BackendType.SQL, "scene", score=0.8),
            _make_record("s002", BackendType.SQL, "scene", score=0.6),
        ]
        results = qi.cross_backend_aggregate(group_by="scene", metric="score_avg")
        assert results[0].metric_value == pytest.approx(0.7)

    def test_tc23_backend_counts(self, qi, mock_client):
        """TC23: backend_counts 키 검증."""
        mock_client.cross_query.return_value = [
            _make_record("s001", BackendType.SQL, "scene"),
            _make_record("s002", BackendType.VECTOR, "scene"),
        ]
        results = qi.cross_backend_aggregate(group_by="scene")
        assert "sql" in results[0].backend_counts or "SQL" in results[0].backend_counts

    def test_tc24_aggregate_result_to_dict(self, qi, mock_client):
        """TC24: AggregateResult.to_dict() 직렬화."""
        mock_client.cross_query.return_value = [
            _make_record("s001", BackendType.SQL, "scene"),
        ]
        results = qi.cross_backend_aggregate(group_by="scene")
        d = results[0].to_dict()
        assert "group_key" in d
        assert "metric_value" in d


# ---------------------------------------------------------------------------
# TC25~TC30: health + SceneResult
# ---------------------------------------------------------------------------

class TestHealthAndUtils:
    def test_tc25_health_no_client(self, qi_no_client):
        """TC25: 클라이언트 없으면 no_client 상태."""
        h = qi_no_client.health()
        assert h["status"] == "no_client"

    def test_tc26_health_all_connected(self, qi, mock_client):
        """TC26: 모든 백엔드 연결 시 HEALTHY."""
        h = qi.health()
        assert h["status"] == "HEALTHY"

    def test_tc27_health_degraded(self, qi, mock_client):
        """TC27: 일부 백엔드 실패 시 DEGRADED."""
        mock_client.check_all_connections.return_value = {
            BackendType.SQL: True, BackendType.VECTOR: False
        }
        h = qi.health()
        assert h["status"] == "DEGRADED"

    def test_tc28_scene_result_to_dict(self):
        """TC28: SceneResult.to_dict() 직렬화."""
        r = SceneResult(
            scene_id="s001", episode=1, label="test",
            backend=BackendType.SQL, score=0.9
        )
        d = r.to_dict()
        assert d["scene_id"] == "s001"
        assert d["score"] == 0.9

    def test_tc29_find_scenes_empty_no_args(self, qi, mock_client):
        """TC29: 조건 없으면 빈 결과."""
        results = qi.find_scenes()
        assert results == []

    def test_tc30_graph_hops_filter(self, qi, mock_client):
        """TC30: graph_within_hops 필터."""
        mock_client.query_by_label.side_effect = [
            # SQL call
            [_make_record("s001", BackendType.SQL, "이준혁", episode=1)],
            # Graph call
            [
                _make_record("g001", BackendType.GRAPH, "이준혁", hops=1, episode=1),
                _make_record("g002", BackendType.GRAPH, "이준혁", hops=5, episode=2),
            ],
        ]
        results = qi.find_scenes(character="이준혁", graph_within_hops=2)
        graph_results = [r for r in results if r.backend == BackendType.GRAPH]
        assert all(r.metadata.get("hops", 0) <= 2 for r in graph_results)
