"""ADR-049 | V588 | L1 — QueryInterface: LOSDB 통합 쿼리 레이어.

SP-A.1: LOSDBClient Facade 위에 시나리오 도메인 쿼리 API를 제공한다.
- find_scenes(): 씬 복합 조건 검색 (캐릭터 / 유사도 / 그래프 홉 / 에피소드 범위)
- find_characters(): 성격 벡터 유사도 기반 캐릭터 검색
- cross_backend_aggregate(): 복수 백엔드 집계

LLM-0 원칙: 외부 LLM 호출 없음.
"""
from __future__ import annotations

import logging
import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from literary_system.db.losdb_client import LOSDBClient, LOSDBClientRecord
from literary_system.db.schema_registry import BackendType

logger = logging.getLogger(__name__)


@dataclass
class SceneResult:
    """find_scenes() 결과 레코드."""
    scene_id: str
    episode: int
    label: str
    backend: BackendType
    score: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "scene_id": self.scene_id,
            "episode": self.episode,
            "label": self.label,
            "backend": self.backend.value if hasattr(self.backend, "value") else str(self.backend),
            "score": self.score,
            "metadata": self.metadata,
        }


@dataclass
class CharacterResult:
    """find_characters() 결과 레코드."""
    character_id: str
    name: str
    similarity: float
    backend: BackendType
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "character_id": self.character_id,
            "name": self.name,
            "similarity": self.similarity,
            "backend": self.backend.value if hasattr(self.backend, "value") else str(self.backend),
            "metadata": self.metadata,
        }


@dataclass
class AggregateResult:
    """cross_backend_aggregate() 결과."""
    group_key: str
    metric_value: float
    backend_counts: Dict[str, int] = field(default_factory=dict)
    records: List[LOSDBClientRecord] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "group_key": self.group_key,
            "metric_value": self.metric_value,
            "backend_counts": self.backend_counts,
            "record_count": len(self.records),
        }


class QueryInterface:
    """LOSDB 도메인 쿼리 통합 레이어.

    LOSDBClient Facade 위에 Literary OS 도메인 쿼리를 제공한다.
    응답 SLO: 1.0초 (ADR-049 C1).
    """

    SLO_RESPONSE_SEC: float = 1.0

    def __init__(
        self,
        client: Optional[LOSDBClient] = None,
        response_timeout_sec: float = SLO_RESPONSE_SEC,
    ) -> None:
        self._client = client
        self._timeout = response_timeout_sec
        logger.debug(
            "QueryInterface 초기화 — backends=%s timeout=%.1fs",
            self._client.available_backends() if self._client else [],
            self._timeout,
        )

    def find_scenes(
        self,
        *,
        character: Optional[str] = None,
        similar_to: Optional[List[float]] = None,
        graph_within_hops: Optional[int] = None,
        episode_range: Optional[tuple] = None,
        limit: int = 10,
    ) -> List[SceneResult]:
        """씬 복합 조건 검색 (캐릭터/벡터/그래프/에피소드 범위)."""
        t0 = time.monotonic()
        results: List[SceneResult] = []

        if self._client is None:
            logger.warning("QueryInterface: LOSDBClient 미연결 — 빈 결과 반환")
            return results

        # 1) SQL 레이블 검색 (캐릭터 기반)
        if character:
            for rec in self._safe_query_label(BackendType.SQL, character):
                ep = int(rec.metadata.get("episode", 0))
                if episode_range and not (episode_range[0] <= ep <= episode_range[1]):
                    continue
                results.append(SceneResult(
                    scene_id=rec.id, episode=ep, label=rec.label,
                    backend=rec.backend, score=1.0, metadata=rec.metadata,
                ))

        # 2) Vector 유사도 검색
        if similar_to:
            for scene_id, score in self._safe_query_similar(similar_to, limit):
                results.append(SceneResult(
                    scene_id=scene_id, episode=0, label="scene_vector",
                    backend=BackendType.VECTOR, score=score,
                    metadata={"source": "vector_search"},
                ))

        # 3) Graph 홉 검색
        if graph_within_hops is not None and character:
            for rec in self._safe_query_label(BackendType.GRAPH, character):
                hops = int(rec.metadata.get("hops", 0))
                ep = int(rec.metadata.get("episode", 0))
                if hops <= graph_within_hops:
                    results.append(SceneResult(
                        scene_id=rec.id, episode=ep, label=rec.label,
                        backend=rec.backend,
                        score=max(0.0, 1.0 - hops * 0.2),
                        metadata=rec.metadata,
                    ))

        # 중복 제거 (scene_id 기준, score 내림차순)
        seen: set = set()
        deduped: List[SceneResult] = []
        for r in sorted(results, key=lambda x: -x.score):
            if r.scene_id not in seen:
                seen.add(r.scene_id)
                deduped.append(r)
            if len(deduped) >= limit:
                break

        elapsed = time.monotonic() - t0
        self._check_slo(elapsed, "find_scenes")
        logger.debug("find_scenes: %d건 반환 (%.3fs)", len(deduped), elapsed)
        return deduped

    def find_characters(
        self,
        similar_personality: List[float],
        *,
        limit: int = 10,
    ) -> List[CharacterResult]:
        """성격 벡터 유사도 기반 캐릭터 검색."""
        t0 = time.monotonic()
        results: List[CharacterResult] = []

        if self._client is None:
            logger.warning("QueryInterface: LOSDBClient 미연결 — 빈 결과 반환")
            return results

        for char_id, score in self._safe_query_similar(similar_personality, limit):
            results.append(CharacterResult(
                character_id=char_id, name=char_id,
                similarity=score, backend=BackendType.VECTOR,
                metadata={"source": "vector_personality"},
            ))
            if len(results) >= limit:
                break

        elapsed = time.monotonic() - t0
        self._check_slo(elapsed, "find_characters")
        logger.debug("find_characters: %d건 반환 (%.3fs)", len(results), elapsed)
        return results

    def cross_backend_aggregate(
        self,
        *,
        group_by: str,
        metric: str = "count",
        backends: Optional[Sequence[BackendType]] = None,
    ) -> List[AggregateResult]:
        """복수 백엔드 집계 (count / score_sum / score_avg)."""
        t0 = time.monotonic()

        if self._client is None:
            logger.warning("QueryInterface: LOSDBClient 미연결 — 빈 결과 반환")
            return []

        target_backends = list(backends) if backends else self._client.available_backends()
        all_records = self._client.cross_query(target_backends, group_by)

        backend_counts: Dict[str, int] = {}
        for rec in all_records:
            bkey = rec.backend.value if hasattr(rec.backend, "value") else str(rec.backend)
            backend_counts[bkey] = backend_counts.get(bkey, 0) + 1

        if metric == "count":
            val = float(len(all_records))
        elif metric == "score_sum":
            val = sum(float(r.metadata.get("score", 0)) for r in all_records)
        elif metric == "score_avg":
            scores = [float(r.metadata.get("score", 0)) for r in all_records]
            val = sum(scores) / len(scores) if scores else 0.0
        else:
            logger.warning("알 수 없는 metric '%s' — count 사용", metric)
            val = float(len(all_records))

        elapsed = time.monotonic() - t0
        self._check_slo(elapsed, "cross_backend_aggregate")
        return [AggregateResult(
            group_key=group_by, metric_value=val,
            backend_counts=backend_counts, records=all_records,
        )]

    def health(self) -> Dict[str, Any]:
        """QueryInterface 연결 상태 반환."""
        if self._client is None:
            return {"status": "no_client", "backends": []}
        statuses = self._client.check_all_connections()
        all_ok = all(v for v in statuses.values())
        return {
            "status": "HEALTHY" if all_ok else "DEGRADED",
            "backends": [b.value for b in self._client.available_backends()],
            "connection_statuses": {
                (k.value if hasattr(k, "value") else str(k)): v
                for k, v in statuses.items()
            },
        }

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _safe_query_label(
        self, backend: BackendType, label: str
    ) -> List[LOSDBClientRecord]:
        if backend not in self._client.available_backends():
            return []
        try:
            return self._client.query_by_label(backend, label)
        except Exception as exc:
            logger.warning("_safe_query_label(%s, %s) 실패: %s", backend, label, exc)
            return []

    def _safe_query_similar(
        self, vector: List[float], limit: int
    ) -> List[tuple]:
        if BackendType.VECTOR not in self._client.available_backends():
            return []
        try:
            vec_adapter = self._client.get_backend(BackendType.VECTOR)
            if vec_adapter is None or not hasattr(vec_adapter, "search"):
                return []
            return vec_adapter.search(vector, top_k=limit)
        except Exception as exc:
            logger.warning("_safe_query_similar 실패: %s", exc)
            return []

    def _check_slo(self, elapsed: float, method: str) -> None:
        if elapsed > self._timeout:
            logger.warning(
                "QueryInterface.%s SLO 초과: %.3fs > %.1fs",
                method, elapsed, self._timeout,
            )
