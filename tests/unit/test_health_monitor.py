"""V589 — BackendHealthMonitor 유닛 테스트 (ADR-050).

T1~T4 시나리오 + Circuit Breaker + HybridRetrieverV2 폴백 검증
총 25 PASS 목표.
"""
from __future__ import annotations

import time
import pytest

from literary_system.db.health_monitor import (
    BackendCircuitState,
    AvailabilityState,
    BackendHealthMonitor,
    BackendHealthRecord,

)
from literary_system.db.schema_registry import BackendType


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

def make_monitor(**kwargs) -> BackendHealthMonitor:
    """기본 파라미터 모니터 생성 (ping_interval=0 → 캐시 없음)."""
    return BackendHealthMonitor(
        ping_interval_sec=0.0,
        failure_threshold=3,
        recovery_timeout_sec=9999.0,  # 테스트에서 자동 복구 안 됨
        **kwargs,
    )


def all_healthy_monitor() -> BackendHealthMonitor:
    m = make_monitor()
    m.register(BackendType.SQL,    ping_fn=lambda: True)
    m.register(BackendType.VECTOR, ping_fn=lambda: True)
    m.register(BackendType.GRAPH,  ping_fn=lambda: True)
    return m


# ---------------------------------------------------------------------------
# T1: FULL — 모든 백엔드 정상
# ---------------------------------------------------------------------------

class TestT1Full:
    def test_t1_overall_state_full(self):
        """T1: 3개 백엔드 모두 정상 → FULL."""
        m = all_healthy_monitor()
        m.check_all()
        assert m.overall_state() == AvailabilityState.FULL

    def test_t1_available_backends_count(self):
        """T1: 가용 백엔드 3개."""
        m = all_healthy_monitor()
        m.check_all()
        assert len(m.get_available_backends()) == 3

    def test_t1_all_circuits_closed(self):
        """T1: 모든 Circuit CLOSED."""
        m = all_healthy_monitor()
        states = m.check_all()
        assert all(s == BackendCircuitState.CLOSED for s in states.values())

    def test_t1_health_report_structure(self):
        """T1: health_report 딕셔너리 구조 검증."""
        m = all_healthy_monitor()
        m.check_all()
        report = m.health_report()
        assert report["overall_state"] == "FULL"
        assert report["total_backends"] == 3
        assert len(report["available_backends"]) == 3
        assert "backends" in report


# ---------------------------------------------------------------------------
# T2: PARTIAL_DEGRADED — 1개 백엔드 장애
# ---------------------------------------------------------------------------

class TestT2PartialDegraded:
    def test_t2_overall_state_partial_degraded(self):
        """T2: VECTOR 장애 → PARTIAL_DEGRADED."""
        m = make_monitor()
        m.register(BackendType.SQL,    ping_fn=lambda: True)
        m.register(BackendType.VECTOR, ping_fn=lambda: True)
        m.register(BackendType.GRAPH,  ping_fn=lambda: True)
        m.check_all()
        m.force_open(BackendType.VECTOR)
        assert m.overall_state() == AvailabilityState.PARTIAL_DEGRADED

    def test_t2_vector_not_in_available(self):
        """T2: 장애 백엔드는 get_available_backends에서 제외."""
        m = make_monitor()
        m.register(BackendType.SQL,    ping_fn=lambda: True)
        m.register(BackendType.VECTOR, ping_fn=lambda: True)
        m.register(BackendType.GRAPH,  ping_fn=lambda: True)
        m.check_all()
        m.force_open(BackendType.VECTOR)
        available = m.get_available_backends()
        assert BackendType.VECTOR not in available
        assert BackendType.SQL in available

    def test_t2_consecutive_failure_triggers_open(self):
        """T2: 3회 연속 실패 → Circuit OPEN."""
        m = make_monitor()
        m.register(BackendType.VECTOR, ping_fn=lambda: False)
        for _ in range(3):
            m.check(BackendType.VECTOR)
        rec = m._records[BackendType.VECTOR]
        assert rec.circuit_state == BackendCircuitState.OPEN

    def test_t2_circuit_open_excludes_backend(self):
        """T2: Circuit OPEN 백엔드는 is_available False."""
        m = make_monitor()
        m.register(BackendType.VECTOR, ping_fn=lambda: True)
        m.force_open(BackendType.VECTOR)
        rec = m._records[BackendType.VECTOR]
        assert not rec.is_available()


# ---------------------------------------------------------------------------
# T3: CRITICAL — 2개 백엔드 장애
# ---------------------------------------------------------------------------

class TestT3Critical:
    def test_t3_overall_state_critical(self):
        """T3: 3개 중 2개 장애 → CRITICAL."""
        m = make_monitor()
        m.register(BackendType.SQL,    ping_fn=lambda: True)
        m.register(BackendType.VECTOR, ping_fn=lambda: True)
        m.register(BackendType.GRAPH,  ping_fn=lambda: True)
        m.check_all()
        m.force_open(BackendType.VECTOR)
        m.force_open(BackendType.GRAPH)
        assert m.overall_state() == AvailabilityState.CRITICAL

    def test_t3_only_sql_available(self):
        """T3: SQL만 가용."""
        m = make_monitor()
        m.register(BackendType.SQL,    ping_fn=lambda: True)
        m.register(BackendType.VECTOR, ping_fn=lambda: True)
        m.register(BackendType.GRAPH,  ping_fn=lambda: True)
        m.check_all()
        m.force_open(BackendType.VECTOR)
        m.force_open(BackendType.GRAPH)
        available = m.get_available_backends()
        assert available == [BackendType.SQL]

    def test_t3_health_report_critical_state(self):
        """T3: health_report overall_state == CRITICAL."""
        m = make_monitor()
        m.register(BackendType.SQL,    ping_fn=lambda: True)
        m.register(BackendType.VECTOR, ping_fn=lambda: True)
        m.register(BackendType.GRAPH,  ping_fn=lambda: True)
        m.check_all()
        m.force_open(BackendType.VECTOR)
        m.force_open(BackendType.GRAPH)
        report = m.health_report()
        assert report["overall_state"] == "CRITICAL"
        assert len(report["available_backends"]) == 1


# ---------------------------------------------------------------------------
# T4: OFFLINE — 전체 장애
# ---------------------------------------------------------------------------

class TestT4Offline:
    def test_t4_overall_state_offline(self):
        """T4: 전체 장애 → OFFLINE."""
        m = make_monitor()
        m.register(BackendType.SQL,    ping_fn=lambda: True)
        m.register(BackendType.VECTOR, ping_fn=lambda: True)
        m.register(BackendType.GRAPH,  ping_fn=lambda: True)
        m.check_all()
        m.force_open(BackendType.SQL)
        m.force_open(BackendType.VECTOR)
        m.force_open(BackendType.GRAPH)
        assert m.overall_state() == AvailabilityState.OFFLINE

    def test_t4_no_available_backends(self):
        """T4: get_available_backends 빈 리스트."""
        m = make_monitor()
        m.register(BackendType.SQL,    ping_fn=lambda: True)
        m.register(BackendType.VECTOR, ping_fn=lambda: True)
        m.register(BackendType.GRAPH,  ping_fn=lambda: True)
        m.check_all()
        for b in [BackendType.SQL, BackendType.VECTOR, BackendType.GRAPH]:
            m.force_open(b)
        assert m.get_available_backends() == []

    def test_t4_empty_monitor_is_offline(self):
        """T4: 등록 백엔드 없으면 OFFLINE."""
        m = make_monitor()
        assert m.overall_state() == AvailabilityState.OFFLINE

    def test_t4_offline_health_report(self):
        """T4: health_report overall_state == OFFLINE."""
        m = make_monitor()
        m.register(BackendType.SQL,    ping_fn=lambda: True)
        m.check_all()
        m.force_open(BackendType.SQL)
        report = m.health_report()
        assert report["overall_state"] == "OFFLINE"


# ---------------------------------------------------------------------------
# Circuit Breaker 상세 동작
# ---------------------------------------------------------------------------

class TestCircuitBreaker:
    def test_cb_half_open_after_recovery(self):
        """recovery_timeout 경과 후 HALF_OPEN 전환."""
        m = BackendHealthMonitor(
            ping_interval_sec=0.0,
            failure_threshold=3,
            recovery_timeout_sec=0.01,  # 10ms
        )
        m.register(BackendType.VECTOR, ping_fn=lambda: False)
        for _ in range(3):
            m.check(BackendType.VECTOR)
        assert m._records[BackendType.VECTOR].circuit_state == BackendCircuitState.OPEN
        time.sleep(0.02)
        m._records[BackendType.VECTOR].try_recover()
        assert m._records[BackendType.VECTOR].circuit_state == BackendCircuitState.HALF_OPEN

    def test_cb_success_resets_to_closed(self):
        """record_success → CLOSED, consecutive_failures = 0."""
        rec = BackendHealthRecord(backend=BackendType.SQL)
        rec.consecutive_failures = 2
        rec.circuit_state = BackendCircuitState.HALF_OPEN
        rec.record_success()
        assert rec.circuit_state == BackendCircuitState.CLOSED
        assert rec.consecutive_failures == 0

    def test_cb_total_counts_tracked(self):
        """total_checks / total_failures 누적 추적."""
        m = make_monitor()
        m.register(BackendType.SQL, ping_fn=lambda: False)
        for _ in range(5):
            m.check(BackendType.SQL)
        rec = m._records[BackendType.SQL]
        assert rec.total_checks == 5
        assert rec.total_failures == 5

    def test_cb_to_dict_has_required_keys(self):
        """to_dict() 필수 키 포함."""
        rec = BackendHealthRecord(backend=BackendType.VECTOR)
        d = rec.to_dict()
        for key in ["backend", "circuit_state", "available", "consecutive_failures"]:
            assert key in d


# ---------------------------------------------------------------------------
# HybridRetrieverV2 폴백 동작
# ---------------------------------------------------------------------------

class TestHybridRetrieverV2:
    def _make_v2(self, dense_available: bool):
        from literary_system.rag.hybrid_retriever import (
            BM25Retriever, DenseRetriever, Document, HybridRetrieverV2,
        )
        from literary_system.rag.qdrant_bridge import QdrantBridge

        bm25 = BM25Retriever()
        bridge = QdrantBridge(host="localhost", port=9999)
        dense = DenseRetriever(bridge=bridge, collection="test_col")

        m = make_monitor()
        m.register(BackendType.VECTOR, ping_fn=lambda: True)
        if not dense_available:
            m.force_open(BackendType.VECTOR)

        v2 = HybridRetrieverV2(bm25=bm25, dense=dense, health_monitor=m)
        for i in range(5):
            v2.index(Document(doc_id=f"d{i}", text=f"drama scene {i} character tension"))
        return v2

    def test_v2_health_report_hybrid_mode(self):
        """V2 dense 가용 → mode=hybrid."""
        v2 = self._make_v2(dense_available=True)
        report = v2.health_report()
        assert report["mode"] == "hybrid"
        assert report["dense_available"] is True

    def test_v2_health_report_fallback_mode(self):
        """V2 dense 불가용 → mode=bm25_fallback."""
        v2 = self._make_v2(dense_available=False)
        report = v2.health_report()
        assert report["mode"] == "bm25_fallback"
        assert report["dense_available"] is False

    def test_v2_fallback_search_returns_results(self):
        """V2 폴백 모드에서도 BM25 결과 반환."""
        v2 = self._make_v2(dense_available=False)
        results = v2.search("drama scene", top_k=3)
        assert len(results) > 0

    def test_v2_fallback_source_is_bm25_fallback(self):
        """V2 폴백 결과 source == bm25_fallback."""
        v2 = self._make_v2(dense_available=False)
        results = v2.search("drama", top_k=3)
        for r in results:
            assert r.source == "bm25_fallback"

    def test_v2_no_monitor_uses_hybrid(self):
        """monitor 없으면 항상 hybrid 경로."""
        from literary_system.rag.hybrid_retriever import (
            BM25Retriever, DenseRetriever, Document, HybridRetrieverV2,
        )
        from literary_system.rag.qdrant_bridge import QdrantBridge
        bm25 = BM25Retriever()
        bridge = QdrantBridge(host="localhost", port=9999)
        dense = DenseRetriever(bridge=bridge, collection="test_col")
        v2 = HybridRetrieverV2(bm25=bm25, dense=dense)
        assert v2._is_dense_available() is True

    def test_v2_indexed_count_in_health_report(self):
        """V2 health_report에 indexed_docs 포함."""
        v2 = self._make_v2(dense_available=True)
        report = v2.health_report()
        assert report["indexed_docs"] == 5
        assert report["version"] == "V2"
