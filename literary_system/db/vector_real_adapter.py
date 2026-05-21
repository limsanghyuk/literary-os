"""literary_system/db/vector_real_adapter.py — VectorRealAdapter (LOSDB Phase B, V584).

numpy-optional 코사인/L2 유사도 기반 인메모리 벡터 스토어.
stdlib(json, math, os, heapq, copy)만 필수 의존성이며
numpy 설치 시 자동으로 가속 경로 활성화.

ADR-043 | V584 | L1
LLM-0 원칙: 외부 LLM 호출 없음.
G32 준수: print() 없음.
"""

from __future__ import annotations

import copy
import heapq
import json
import logging
import math
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from literary_system.db.migration_manager import (
    BaseMigrationAdapter,
    Migration,
)
from literary_system.db.schema_registry import BackendType, MigrationRecord, SchemaRegistry

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# numpy-optional
# ---------------------------------------------------------------------------
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:  # pragma: no cover
    HAS_NUMPY = False


# ---------------------------------------------------------------------------
# 유사도 함수 (모듈 레벨 — Gate 체크포인트에서 직접 검증 가능)
# ---------------------------------------------------------------------------

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    """코사인 유사도 계산 (numpy-optional). 범위 [-1, 1], 1이 완전 동일."""
    if HAS_NUMPY:
        va = np.array(a, dtype=float)
        vb = np.array(b, dtype=float)
        denom = float(np.linalg.norm(va) * np.linalg.norm(vb))
        return float(np.dot(va, vb) / denom) if denom > 1e-10 else 0.0
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    denom = na * nb
    return dot / denom if denom > 1e-10 else 0.0


def _l2_distance(a: List[float], b: List[float]) -> float:
    """L2(유클리드) 거리. 작을수록 유사."""
    if HAS_NUMPY:
        return float(np.linalg.norm(np.array(a, dtype=float) - np.array(b, dtype=float)))
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


# ---------------------------------------------------------------------------
# 데이터 컨테이너
# ---------------------------------------------------------------------------

@dataclass
class VectorRecord:
    """단일 벡터 레코드."""

    id: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {"id": self.id, "vector": self.vector, "metadata": self.metadata}

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "VectorRecord":
        return cls(id=d["id"], vector=d["vector"], metadata=d.get("metadata", {}))


# ---------------------------------------------------------------------------
# VectorRealAdapter
# ---------------------------------------------------------------------------

class VectorRealAdapter(BaseMigrationAdapter):
    """LOSDB Vector 레이어 REAL 구현.

    Args:
        dim: 벡터 차원. upsert 시 차원 불일치면 ValueError.
        path: JSON 영속화 파일 경로 (None = 메모리 전용).
        metric: 기본 유사도 메트릭 ("cosine" | "l2").
        mock: True면 apply/rollback 실제 실행 없이 성공 반환.
    """

    SUPPORTED_METRICS = ("cosine", "l2")

    def __init__(
        self,
        dim: int,
        path: Optional[str] = None,
        metric: str = "cosine",
        mock: bool = False,
    ) -> None:
        super().__init__(mock=mock)
        if dim <= 0:
            raise ValueError(f"dim must be > 0, got {dim}")
        if metric not in self.SUPPORTED_METRICS:
            raise ValueError(
                f"metric must be one of {self.SUPPORTED_METRICS}, got {metric!r}"
            )

        self._dim = dim
        self._path: Optional[str] = os.path.abspath(path) if path else None
        self._metric = metric

        self._store: Dict[str, VectorRecord] = {}
        self._snapshot: Dict[str, VectorRecord] = {}  # rollback 용 스냅샷

        logger.debug(
            "VectorRealAdapter 초기화: dim=%d metric=%s path=%s mock=%s",
            dim, metric, self._path, mock,
        )

    # ------------------------------------------------------------------
    # 기본 CRUD
    # ------------------------------------------------------------------

    def upsert(
        self,
        id: str,
        vector: List[float],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """벡터 삽입 또는 갱신."""
        if len(vector) != self._dim:
            raise ValueError(
                f"Vector dim mismatch: expected {self._dim}, got {len(vector)}"
            )
        self._store[id] = VectorRecord(
            id=id, vector=list(vector), metadata=metadata or {}
        )
        logger.debug("upsert id=%s", id)

    def get(self, id: str) -> Optional[VectorRecord]:
        """단건 조회."""
        return self._store.get(id)

    def delete(self, id: str) -> bool:
        """삭제. 존재하면 True, 없으면 False."""
        if id in self._store:
            del self._store[id]
            logger.debug("delete id=%s", id)
            return True
        return False

    def count(self) -> int:
        """저장된 벡터 수."""
        return len(self._store)

    # ------------------------------------------------------------------
    # 유사도 검색
    # ------------------------------------------------------------------

    def search(
        self,
        query: List[float],
        top_k: int = 10,
        metric: Optional[str] = None,
    ) -> List[Tuple[str, float]]:
        """유사도 검색. 반환: [(id, score), ...] top_k 개.

        코사인: score 높을수록 유사.
        L2:     score(거리) 작을수록 유사.
        """
        if len(query) != self._dim:
            raise ValueError(
                f"Query dim mismatch: expected {self._dim}, got {len(query)}"
            )
        m = metric or self._metric
        if m not in self.SUPPORTED_METRICS:
            raise ValueError(f"metric must be one of {self.SUPPORTED_METRICS}")

        if not self._store:
            return []

        k = min(top_k, len(self._store))
        if m == "cosine":
            scores = [
                (rec.id, _cosine_similarity(query, rec.vector))
                for rec in self._store.values()
            ]
            return heapq.nlargest(k, scores, key=lambda x: x[1])
        else:  # l2
            scores = [
                (rec.id, _l2_distance(query, rec.vector))
                for rec in self._store.values()
            ]
            return heapq.nsmallest(k, scores, key=lambda x: x[1])

    # ------------------------------------------------------------------
    # JSON 영속화
    # ------------------------------------------------------------------

    def save(self) -> None:
        """현재 스토어를 JSON 파일로 저장."""
        if not self._path:
            logger.debug("save 스킵: path 미설정")
            return
        data = {
            "dim": self._dim,
            "metric": self._metric,
            "records": {id_: rec.to_dict() for id_, rec in self._store.items()},
        }
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.debug("저장 완료: %d records → %s", len(self._store), self._path)

    def load(self) -> None:
        """JSON 파일에서 스토어 복원."""
        if not self._path or not os.path.exists(self._path):
            logger.debug("load 스킵: 파일 없음 (%s)", self._path)
            return
        with open(self._path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if data.get("dim") != self._dim:
            raise ValueError(
                f"Dimension 불일치: 파일={data.get('dim')}, 어댑터={self._dim}"
            )
        self._store = {
            id_: VectorRecord.from_dict(d)
            for id_, d in data.get("records", {}).items()
        }
        logger.debug("복원 완료: %d records ← %s", len(self._store), self._path)

    # ------------------------------------------------------------------
    # BaseMigrationAdapter 구현
    # ------------------------------------------------------------------

    def check_connection(self) -> bool:
        """연결 상태 확인 (인메모리 — 항상 True)."""
        return True

    def apply(self, migration: Migration) -> bool:
        """Migration 적용. migration.vector_ops 처리.

        vector_ops 항목 형식:
        - {"op": "upsert", "id": str, "vector": List[float], "metadata": Dict}
        - {"op": "delete", "id": str}
        - {"op": "save"}

        Returns:
            True = 성공, False = 실패
        """
        if self.mock:
            logger.info("[MOCK-Vector] apply %s", migration.migration_id)
            return True

        # FIX-B (V595.3): 메모리 + 파일 양쪽 스냅샷 저장
        # save op 이후 다른 op에서 실패해도 파일까지 완전 복원.
        self._snapshot = copy.deepcopy(self._store)
        file_snapshot: Optional[bytes] = None
        if self._path and os.path.exists(self._path):
            with open(self._path, "rb") as _f:
                file_snapshot = _f.read()

        vector_ops = getattr(migration, "vector_ops", None)
        if not vector_ops:
            logger.debug("apply(%s): vector_ops 없음 — 스킵", migration.migration_id)
            self._record_migration(migration)
            return True

        try:
            # save op는 모든 mutation 완료 후 마지막에만 실행 (FIX-B)
            should_save = any(op_dict.get("op") == "save" for op_dict in vector_ops)
            mutation_ops = [op_dict for op_dict in vector_ops if op_dict.get("op") != "save"]
            for op_dict in mutation_ops:
                op = op_dict.get("op")
                if op == "upsert":
                    self.upsert(
                        id=op_dict["id"],
                        vector=op_dict["vector"],
                        metadata=op_dict.get("metadata"),
                    )
                elif op == "delete":
                    self.delete(op_dict["id"])
                else:
                    raise ValueError(f"알 수 없는 vector_op: {op!r}")
            if should_save:
                self.save()  # 모든 mutation 성공 후에만 저장

            self._record_migration(migration)
            logger.info(
                "VectorRealAdapter.apply OK: %s (%d ops)",
                migration.migration_id, len(vector_ops),
            )
            return True
        except Exception as exc:
            logger.exception("VectorRealAdapter.apply 실패 (롤백 완료): %s", exc)
            # 메모리 복원
            self._store = self._snapshot
            # 파일 복원 (FIX-B 핵심)
            if self._path:
                if file_snapshot is not None:
                    with open(self._path, "wb") as _f:
                        _f.write(file_snapshot)
                elif os.path.exists(self._path):
                    os.remove(self._path)  # apply 전 파일이 없었으면 제거
            return False

    def rollback(self, migration: Migration) -> bool:
        """마지막 apply() 이전 스냅샷으로 복원.

        Returns:
            True = 성공, False = 실패
        """
        if self.mock:
            logger.info("[MOCK-Vector] rollback %s", migration.migration_id)
            return True
        try:
            self._store = copy.deepcopy(self._snapshot)
            logger.info(
                "VectorRealAdapter.rollback OK: %s (%d records 복원)",
                migration.migration_id, len(self._store),
            )
            return True
        except Exception as exc:
            logger.exception("VectorRealAdapter.rollback 실패: %s", exc)
            return False

    # ------------------------------------------------------------------
    # 내부 유틸
    # ------------------------------------------------------------------

    def _record_migration(self, migration: Migration) -> None:
        """SchemaRegistry에 마이그레이션 기록 등록."""
        try:
            reg = SchemaRegistry.get_instance()
            parts = migration.to_version.split(".")
            major = int(parts[0]) if len(parts) > 0 else 1
            minor = int(parts[1]) if len(parts) > 1 else 0
            patch = int(parts[2]) if len(parts) > 2 else 0
            reg.register(BackendType.VECTOR, major, minor, patch, migration.description)
            record = MigrationRecord(
                migration_id=migration.migration_id,
                backend=BackendType.VECTOR,
                from_version=migration.from_version,
                to_version=migration.to_version,
                description=migration.description,
                applied_at=datetime.now(timezone.utc).isoformat(),
                success=True,
            )
            reg.record_migration(record)
        except Exception as exc:
            logger.warning("SchemaRegistry 등록 실패 (무시): %s", exc)

    def query_by_label(self, label: str) -> list:
        """공개 API: metadata["label"] 기준 레코드 목록 반환.

        LOSDBClient가 private _store를 직접 참조하지 않도록 제공하는
        공개 쿼리 인터페이스 (P1-1 ADR-048 fix).

        Returns:
            List[VectorRecord]: label이 일치하는 레코드 목록
        """
        results = []
        for vid, vrec in self._store.items():
            meta = getattr(vrec, "metadata", {}) or {}
            rec_label = meta.get("label", getattr(vrec, "label", ""))
            if rec_label == label:
                results.append(vrec)
        return results

    def schema_info(self) -> dict:
        """어댑터 메타 정보."""
        return {
            "adapter": "VectorRealAdapter",
            "version": "V584",
            "adr": "ADR-043",
            "dim": self._dim,
            "metric": self._metric,
            "count": self.count(),
            "path": self._path,
            "numpy": HAS_NUMPY,
        }
