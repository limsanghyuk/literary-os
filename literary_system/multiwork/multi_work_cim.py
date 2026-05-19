"""
V567 MultiWorkCIM — 멀티워크 CIM (캐릭터 상호작용 행렬) 확장

기존 CIM (literary_system/corpus/cim_bootstrap.py) 단일 작품 대상에서 확장:
- 프로젝트별 독립 CIM 유지 (격리)
- 공유 캐릭터 간 전이 가중치 집계 (cross-project aggregation)
- 장르 가중치 보정 (GenreTransferLearning 연동)

CIM 공식 (CIMBootstrap과 동일):
    W[i][j] = 1 − exp(−decay × count[i][j])

멀티워크 집계:
    W_global[i][j] = mean(W_p[i][j]) over all projects p

LLM-0: 외부 LLM 호출 없음.
"""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class CIMEntry:
    """캐릭터 쌍 상호작용 기록."""
    char_a: str
    char_b: str
    count: int = 0
    weight: float = 0.0

    def update(self, decay: float = 0.95) -> None:
        """count 증가 후 가중치 재계산."""
        self.count += 1
        self.weight = 1.0 - math.exp(-decay * self.count)


@dataclass
class ProjectCIM:
    """단일 프로젝트 CIM.

    Attributes:
        project_id: 소유 프로젝트
        decay:      감쇠 파라미터 (CIMBootstrap 동일)
        entries:    (char_a, char_b) → CIMEntry
    """
    project_id: str
    decay: float = 0.95
    entries: Dict[Tuple[str, str], CIMEntry] = field(default_factory=dict)

    def _key(self, a: str, b: str) -> Tuple[str, str]:
        return (min(a, b), max(a, b))

    def record_interaction(self, char_a: str, char_b: str) -> None:
        """씬에서 두 캐릭터가 등장했을 때 호출."""
        if char_a == char_b:
            return
        key = self._key(char_a, char_b)
        if key not in self.entries:
            self.entries[key] = CIMEntry(char_a=key[0], char_b=key[1])
        self.entries[key].update(self.decay)

    def weight(self, char_a: str, char_b: str) -> float:
        """두 캐릭터 간 가중치 조회."""
        key = self._key(char_a, char_b)
        entry = self.entries.get(key)
        return entry.weight if entry else 0.0

    def warm_start_weights(
        self, characters: List[str]
    ) -> Dict[str, Dict[str, float]]:
        """CIMBootstrap.warm_start_weights 호환 형식 반환."""
        result: Dict[str, Dict[str, float]] = {c: {} for c in characters}
        for ci in characters:
            for cj in characters:
                if ci != cj:
                    result[ci][cj] = self.weight(ci, cj)
        return result

    def top_pairs(self, k: int = 5) -> List[CIMEntry]:
        """상위 k 상호작용 쌍."""
        sorted_entries = sorted(
            self.entries.values(), key=lambda e: e.weight, reverse=True
        )
        return sorted_entries[:k]


class MultiWorkCIM:
    """멀티워크 CIM 관리자.

    - 프로젝트별 독립 CIM 유지
    - 공유 캐릭터에 대한 전역 가중치 집계
    - 격리: 다른 프로젝트의 사설 캐릭터 CIM 데이터는 노출하지 않음
    - Thread-safe (RLock)
    """

    def __init__(self, decay: float = 0.95) -> None:
        self._decay = decay
        self._project_cims: Dict[str, ProjectCIM] = {}
        self._lock = threading.RLock()

    # ------------------------------------------------------------------ #
    # 프로젝트 CIM 관리
    # ------------------------------------------------------------------ #

    def init_project(self, project_id: str) -> ProjectCIM:
        """프로젝트 CIM 초기화.

        Raises:
            KeyError: 이미 초기화된 프로젝트
        """
        with self._lock:
            if project_id in self._project_cims:
                raise KeyError(f"CIM already initialized: {project_id}")
            cim = ProjectCIM(project_id=project_id, decay=self._decay)
            self._project_cims[project_id] = cim
            return cim

    def get_project_cim(self, project_id: str) -> Optional[ProjectCIM]:
        """프로젝트 CIM 조회."""
        return self._project_cims.get(project_id)

    def record(self, project_id: str, char_a: str, char_b: str) -> None:
        """씬 상호작용 기록.

        Raises:
            KeyError: 미초기화 프로젝트
        """
        with self._lock:
            cim = self._project_cims.get(project_id)
            if cim is None:
                raise KeyError(f"CIM not initialized for: {project_id}")
            cim.record_interaction(char_a, char_b)

    # ------------------------------------------------------------------ #
    # 전역 집계
    # ------------------------------------------------------------------ #

    def global_weight(self, char_a: str, char_b: str) -> float:
        """모든 프로젝트 CIM에서 두 캐릭터 간 평균 가중치.

        공유 캐릭터에 대한 크로스-프로젝트 집계.
        """
        with self._lock:
            weights = [
                cim.weight(char_a, char_b)
                for cim in self._project_cims.values()
            ]
            active = [w for w in weights if w > 0]
            if not active:
                return 0.0
            return round(sum(active) / len(active), 6)

    def aggregate_warm_start(
        self,
        characters: List[str],
        project_ids: Optional[List[str]] = None,
    ) -> Dict[str, Dict[str, float]]:
        """지정 프로젝트들의 CIM을 집계한 warm-start 가중치 행렬.

        Args:
            characters:  대상 캐릭터 목록
            project_ids: 집계할 프로젝트 목록 (None이면 전체)

        Returns:
            {char_a: {char_b: mean_weight}}
        """
        with self._lock:
            pids = project_ids or list(self._project_cims.keys())
            cims = [self._project_cims[p] for p in pids if p in self._project_cims]

            result: Dict[str, Dict[str, float]] = {c: {} for c in characters}
            for ci in characters:
                for cj in characters:
                    if ci == cj:
                        continue
                    ws = [cim.weight(ci, cj) for cim in cims]
                    active = [w for w in ws if w > 0]
                    result[ci][cj] = round(sum(active) / len(active), 6) if active else 0.0
            return result

    # ------------------------------------------------------------------ #
    # 통계
    # ------------------------------------------------------------------ #

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "projects": len(self._project_cims),
                "decay": self._decay,
                "per_project_pairs": {
                    pid: len(cim.entries)
                    for pid, cim in self._project_cims.items()
                },
            }
