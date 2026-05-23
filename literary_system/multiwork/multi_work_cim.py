"""
V610 MultiWorkCIM v2.0 — 멀티워크 CIM 파사드 (팩토리 + 업그레이드 유틸리티)

V567(v1.0) → V610(v2.0) 변경 사항:
  - CIMVersion 열거형: V1 / V2
  - ProjectCIM.to_v2(): v1 CIM 상태 → ProjectCIMV2 마이그레이션
  - MultiWorkCIM.upgrade_to_v2(): v1 인스턴스 → MultiWorkCIMV2 변환
  - create_multi_work_cim(): version 파라미터로 v1/v2 선택 팩토리
  - get_version() 헬퍼

하위 호환성:
  - 모든 v1 public API (init_project, record, global_weight, aggregate_warm_start, stats) 유지
  - v1 dataclass (CIMEntry, ProjectCIM) 변경 없음

설계 원칙:
  D-1: circular import 방지 — v2 모듈은 지연 임포트(lazy import)
  D-2: to_v2() 는 비파괴적 — v1 entries를 딥복사하여 v2 entries_v2에 주입
  D-3: upgrade_to_v2() 는 v1 _project_cims 전체를 to_v2()로 마이그레이션
  D-4: create_multi_work_cim(version='v2') 기본값 → MultiWorkCIMV2 반환
  D-5: CIMVersion.current() → 최신 지원 버전 반환 ('v2')

LLM-0: 외부 LLM 호출 없음.
ADR-070
"""

from __future__ import annotations

import math
import threading
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Any, Dict, List, Optional, Tuple

if TYPE_CHECKING:
    from .multi_work_cim_v2 import MultiWorkCIMV2, ProjectCIMV2


# ══════════════════════════════════════════════════════════════════════════════
# CIMVersion
# ══════════════════════════════════════════════════════════════════════════════

class CIMVersion(str, Enum):
    """지원되는 MultiWorkCIM 버전."""

    V1 = "v1"
    V2 = "v2"

    @classmethod
    def current(cls) -> "CIMVersion":
        """최신 지원 버전."""
        return cls.V2

    @classmethod
    def from_str(cls, s: str) -> "CIMVersion":
        """문자열로부터 버전 파싱. 알 수 없는 경우 V2 반환."""
        try:
            return cls(s.lower())
        except ValueError:
            return cls.V2


# ══════════════════════════════════════════════════════════════════════════════
# v1 데이터클래스 (하위 호환 유지)
# ══════════════════════════════════════════════════════════════════════════════

@dataclass
class CIMEntry:
    """캐릭터 쌍 상호작용 기록 (v1)."""

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
    """단일 프로젝트 CIM (v1).

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

    # ------------------------------------------------------------------ #
    # V610 신규: v2 마이그레이션
    # ------------------------------------------------------------------ #

    def to_v2(
        self,
        char_db: Optional[Any] = None,
        conflict_threshold: float = 0.30,
    ) -> "ProjectCIMV2":
        """v1 ProjectCIM → ProjectCIMV2 마이그레이션.

        비파괴적 변환: 현재 entries를 v2 _entries_v2에 주입 후
        동일한 decay/project_id를 가진 ProjectCIMV2 반환.

        Args:
            char_db:             SharedCharacterDBV2 참조 (None 허용)
            conflict_threshold:  ProjectCIMV2 충돌 임계값

        Returns:
            ProjectCIMV2 인스턴스 (v1 상태 포함)
        """
        from .multi_work_cim_v2 import CIMEntryV2, ProjectCIMV2  # lazy import

        v2 = ProjectCIMV2(
            project_id=self.project_id,
            decay=self.decay,
            char_db=char_db,
            conflict_threshold=conflict_threshold,
        )
        # v1 entries → v2 entries (기본 weight 복사, reward_weighted_weight = weight × 0.5)
        for key, e1 in self.entries.items():
            e2 = CIMEntryV2(
                char_a=e1.char_a,
                char_b=e1.char_b,
                count=e1.count,
                weight=e1.weight,
                reward_weighted_weight=round(e1.weight * 0.5, 6),
            )
            v2._entries_v2[key] = e2
            # v1 entries도 동기화
            v2.entries[key] = e2  # type: ignore[assignment]
        return v2


# ══════════════════════════════════════════════════════════════════════════════
# MultiWorkCIM v2.0
# ══════════════════════════════════════════════════════════════════════════════

class MultiWorkCIM:
    """멀티워크 CIM 관리자 v2.0.

    - 프로젝트별 독립 CIM 유지
    - 공유 캐릭터에 대한 전역 가중치 집계
    - Thread-safe (RLock)

    V610 신규:
      - upgrade_to_v2(): self → MultiWorkCIMV2 변환
      - version: CIMVersion.V1 속성
    """

    VERSION: str = "1.0.0"

    def __init__(self, decay: float = 0.95) -> None:
        self._decay = decay
        self._project_cims: Dict[str, ProjectCIM] = {}
        self._lock = threading.RLock()

    @property
    def version(self) -> CIMVersion:
        """이 인스턴스의 CIM 버전."""
        return CIMVersion.V1

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
        """모든 프로젝트 CIM에서 두 캐릭터 간 평균 가중치."""
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
        """지정 프로젝트들의 CIM을 집계한 warm-start 가중치 행렬."""
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
                    result[ci][cj] = (
                        round(sum(active) / len(active), 6) if active else 0.0
                    )
            return result

    # ------------------------------------------------------------------ #
    # 통계
    # ------------------------------------------------------------------ #

    def stats(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "version": self.VERSION,
                "projects": len(self._project_cims),
                "decay": self._decay,
                "per_project_pairs": {
                    pid: len(cim.entries)
                    for pid, cim in self._project_cims.items()
                },
            }

    # ------------------------------------------------------------------ #
    # V610 신규: v2 업그레이드
    # ------------------------------------------------------------------ #

    def upgrade_to_v2(
        self,
        char_db: Optional[Any] = None,
        conflict_threshold: float = 0.30,
    ) -> "MultiWorkCIMV2":
        """v1 MultiWorkCIM → MultiWorkCIMV2 업그레이드.

        모든 프로젝트 CIM을 ProjectCIM.to_v2()로 변환하여
        새 MultiWorkCIMV2 인스턴스에 주입.

        Args:
            char_db:             SharedCharacterDBV2 참조 (None 허용)
            conflict_threshold:  ProjectCIMV2 충돌 임계값

        Returns:
            MultiWorkCIMV2 인스턴스 (v1 상태 전체 포함)
        """
        from .multi_work_cim_v2 import MultiWorkCIMV2  # lazy import

        with self._lock:
            v2 = MultiWorkCIMV2(
                decay=self._decay,
                char_db=char_db,
                conflict_threshold=conflict_threshold,
            )
            for pid, cim_v1 in self._project_cims.items():
                cim_v2 = cim_v1.to_v2(
                    char_db=char_db,
                    conflict_threshold=conflict_threshold,
                )
                v2._project_cims_v2[pid] = cim_v2
                v2._project_cims[pid] = cim_v2  # v1 dict 동기화
        return v2


# ══════════════════════════════════════════════════════════════════════════════
# 팩토리 함수 (V610)
# ══════════════════════════════════════════════════════════════════════════════

def create_multi_work_cim(
    version: str = "v2",
    decay: float = 0.95,
    char_db: Optional[Any] = None,
    conflict_threshold: float = 0.30,
) -> "MultiWorkCIM | MultiWorkCIMV2":
    """MultiWorkCIM 팩토리.

    Args:
        version:             'v1' 또는 'v2' (기본: 'v2')
        decay:               감쇠 파라미터
        char_db:             SharedCharacterDBV2 참조 (v2 전용)
        conflict_threshold:  충돌 임계값 (v2 전용)

    Returns:
        version='v1' → MultiWorkCIM
        version='v2' → MultiWorkCIMV2

    Examples:
        >>> cim = create_multi_work_cim()           # MultiWorkCIMV2
        >>> cim_v1 = create_multi_work_cim('v1')   # MultiWorkCIM
    """
    ver = CIMVersion.from_str(version)
    if ver == CIMVersion.V1:
        return MultiWorkCIM(decay=decay)

    from .multi_work_cim_v2 import MultiWorkCIMV2  # lazy import
    return MultiWorkCIMV2(
        decay=decay,
        char_db=char_db,
        conflict_threshold=conflict_threshold,
    )


def get_cim_version(cim: "MultiWorkCIM") -> CIMVersion:
    """MultiWorkCIM 인스턴스의 버전 반환.

    Args:
        cim: MultiWorkCIM 또는 MultiWorkCIMV2 인스턴스

    Returns:
        CIMVersion.V1 또는 CIMVersion.V2
    """
    if hasattr(cim, "VERSION") and cim.VERSION.startswith("2"):
        return CIMVersion.V2
    return CIMVersion.V1
