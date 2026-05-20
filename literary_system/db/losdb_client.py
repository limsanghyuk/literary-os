"""ADR-045 | V586 | L1 — LOSDBClient: LOSDB 통합 Facade.

LLM-0 원칙: 외부 LLM 호출 없음.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from literary_system.db.migration_manager import BaseMigrationAdapter
from literary_system.db.schema_registry import BackendType

logger = logging.getLogger(__name__)


@dataclass
class LOSDBClientRecord:
    """통합 쿼리 결과 레코드."""

    id: str
    backend: BackendType
    label: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "backend": self.backend.value if hasattr(self.backend, "value") else str(self.backend),
            "label": self.label,
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "LOSDBClientRecord":
        backend_val = d.get("backend", "")
        try:
            backend = BackendType(backend_val)
        except (ValueError, KeyError):
            backend = BackendType.GRAPH
        return cls(
            id=d["id"],
            backend=backend,
            label=d.get("label", ""),
            metadata=d.get("metadata", {}),
        )


class LOSDBClient:
    """LOSDB 통합 Facade — SQL / Vector / Graph 어댑터를 단일 인터페이스로 관리.

    어댑터는 모두 옵셔널: None이면 해당 백엔드 비활성.

    Example::

        from literary_system.db import LOSDBClient, SQLiteRealAdapter, VectorRealAdapter
        sql = SQLiteRealAdapter(":memory:")
        vec = VectorRealAdapter()
        client = LOSDBClient(sql=sql, vector=vec)
        records = client.cross_query([BackendType.SQL, BackendType.VECTOR], label="chapter")
    """

    def __init__(
        self,
        sql: Optional[BaseMigrationAdapter] = None,
        vector: Optional[BaseMigrationAdapter] = None,
        graph: Optional[BaseMigrationAdapter] = None,
    ) -> None:
        self._backends: Dict[BackendType, BaseMigrationAdapter] = {}
        if sql is not None:
            self._backends[BackendType.SQL] = sql
        if vector is not None:
            self._backends[BackendType.VECTOR] = vector
        if graph is not None:
            self._backends[BackendType.GRAPH] = graph

    # ------------------------------------------------------------------
    # 백엔드 관리
    # ------------------------------------------------------------------

    def available_backends(self) -> List[BackendType]:
        """활성 백엔드 목록 반환."""
        return list(self._backends.keys())

    def get_backend(self, backend_type: BackendType) -> Optional[BaseMigrationAdapter]:
        """특정 백엔드 어댑터 반환 (없으면 None)."""
        return self._backends.get(backend_type)

    def register_backend(self, backend_type: BackendType, adapter: BaseMigrationAdapter) -> None:
        """런타임에 백엔드 어댑터 등록."""
        self._backends[backend_type] = adapter
        logger.debug("LOSDBClient: %s 백엔드 등록됨", backend_type)

    def unregister_backend(self, backend_type: BackendType) -> bool:
        """백엔드 어댑터 해제. 성공 여부 반환."""
        if backend_type in self._backends:
            del self._backends[backend_type]
            logger.debug("LOSDBClient: %s 백엔드 해제됨", backend_type)
            return True
        return False

    # ------------------------------------------------------------------
    # 연결 확인
    # ------------------------------------------------------------------

    def check_all_connections(self) -> Dict[str, bool]:
        """모든 활성 백엔드 연결 상태 확인.

        Returns:
            {backend_name: bool} 딕셔너리
        """
        result: Dict[str, bool] = {}
        for bt, adapter in self._backends.items():
            key = bt.value if hasattr(bt, "value") else str(bt)
            try:
                result[key] = bool(adapter.check_connection())
            except Exception as exc:
                logger.warning("check_connection 실패 backend=%s: %s", bt, exc)
                result[key] = False
        return result

    # ------------------------------------------------------------------
    # 쿼리
    # ------------------------------------------------------------------

    def query_by_label(
        self,
        backend: BackendType,
        label: str,
    ) -> List[LOSDBClientRecord]:
        """단일 백엔드에서 label 기반 조회.

        백엔드 타입별로 적절한 쿼리 메서드를 호출한다:
        - SQL: ``get_rows_by_table`` (테이블명 = label)
        - Vector: ``search_by_label``
        - Graph: 노드 순회 후 label 필터
        """
        adapter = self._backends.get(backend)
        if adapter is None:
            logger.warning("query_by_label: 백엔드 %s 비활성", backend)
            return []

        records: List[LOSDBClientRecord] = []
        try:
            if backend == BackendType.SQL:
                records = self._query_sql(adapter, label)
            elif backend == BackendType.VECTOR:
                records = self._query_vector(adapter, label)
            elif backend == BackendType.GRAPH:
                records = self._query_graph(adapter, label)
        except Exception as exc:
            logger.warning("query_by_label 실패 backend=%s label=%s: %s", backend, label, exc)
        return records

    def cross_query(
        self,
        backends: List[BackendType],
        label: str,
    ) -> List[LOSDBClientRecord]:
        """복수 백엔드에서 label 기반 조회 후 결과 병합.

        Args:
            backends: 조회할 백엔드 목록 (비활성 백엔드는 건너뜀)
            label: 검색 label

        Returns:
            모든 백엔드의 결과를 병합한 리스트 (백엔드 순서 유지)
        """
        results: List[LOSDBClientRecord] = []
        for bt in backends:
            results.extend(self.query_by_label(bt, label))
        return results

    # ------------------------------------------------------------------
    # 스키마 정보
    # ------------------------------------------------------------------

    def schema_info(self) -> Dict[str, Any]:
        """모든 활성 백엔드의 스키마 정보 수집."""
        info: Dict[str, Any] = {
            "client_version": "V586",
            "active_backends": [
                bt.value if hasattr(bt, "value") else str(bt)
                for bt in self._backends
            ],
            "backends": {},
        }
        for bt, adapter in self._backends.items():
            key = bt.value if hasattr(bt, "value") else str(bt)
            try:
                if hasattr(adapter, "schema_info"):
                    info["backends"][key] = adapter.schema_info()
                else:
                    info["backends"][key] = {"status": "schema_info 미지원"}
            except Exception as exc:
                info["backends"][key] = {"error": str(exc)}
        return info

    # ------------------------------------------------------------------
    # 내부 쿼리 헬퍼
    # ------------------------------------------------------------------

    def _query_sql(
        self,
        adapter: BaseMigrationAdapter,
        label: str,
    ) -> List[LOSDBClientRecord]:
        """SQL 어댑터에서 테이블 이름(label) 기반 행 조회."""
        records: List[LOSDBClientRecord] = []
        # SQLiteRealAdapter: get_rows(table) 메서드 사용
        if hasattr(adapter, "get_rows"):
            try:
                rows = adapter.get_rows(label)
                for i, row in enumerate(rows):
                    rid = str(row.get("id", i)) if isinstance(row, dict) else str(i)
                    meta = row if isinstance(row, dict) else {}
                    records.append(
                        LOSDBClientRecord(
                            id=rid,
                            backend=BackendType.SQL,
                            label=label,
                            metadata=meta,
                        )
                    )
            except Exception as exc:
                logger.debug("SQL query_by_label 실패: %s", exc)
        return records

    def _query_vector(
        self,
        adapter: BaseMigrationAdapter,
        label: str,
    ) -> List[LOSDBClientRecord]:
        """Vector 어댑터에서 label 기반 레코드 조회.

        VectorRealAdapter는 label을 metadata["label"]에 저장한다.
        내부 저장소는 _store dict (id -> VectorRecord).
        """
        records: List[LOSDBClientRecord] = []
        # VectorRealAdapter: _store dict 순회
        store = getattr(adapter, "_store", None) or getattr(adapter, "_records", None)
        if store is not None:
            for vid, vrec in store.items():
                meta = getattr(vrec, "metadata", {}) or {}
                rec_label = meta.get("label", getattr(vrec, "label", ""))
                if rec_label == label:
                    records.append(
                        LOSDBClientRecord(
                            id=vid,
                            backend=BackendType.VECTOR,
                            label=label,
                            metadata=meta,
                        )
                    )
        return records

    def _query_graph(
        self,
        adapter: BaseMigrationAdapter,
        label: str,
    ) -> List[LOSDBClientRecord]:
        """Graph 어댑터에서 label 기반 노드 조회."""
        records: List[LOSDBClientRecord] = []
        # GraphRealAdapter: _nodes dict 순회
        if hasattr(adapter, "_nodes"):
            for nid, node in adapter._nodes.items():
                node_label = getattr(node, "label", "")
                if node_label == label:
                    records.append(
                        LOSDBClientRecord(
                            id=nid,
                            backend=BackendType.GRAPH,
                            label=label,
                            metadata=getattr(node, "metadata", {}),
                        )
                    )
        return records
