"""
V609 MultiWorkCIMV2 — 멀티워크 CIM v2.0

V567 MultiWorkCIM(v1) 상속 확장:
- SharedCharacterDBV2 연동: RewardTrace 기반 보상 가중치 CIM
- CIMEntryV2: reward_weighted_weight 필드 추가
- ProjectCIMV2: record_interaction_v2() 보상 연동 기록
- CIMSnapshot: 프로젝트별 CIM 상태 스냅샷/복원
- InterProjectCIMScore: 두 프로젝트 CIM 코사인 유사도 + 호환성 판정
- reward_weighted_global_weight(): 보상 가중 전역 집계
- export_state_v2() / import_state_v2(): 완전 직렬화 (7-key schema)

설계 원칙:
  D-1: 상속 기반 v2 (v1 API 완전 호환, 비파괴적 확장)
  D-2: 보상 연동은 옵셔널 (char_db=None → 기본 reward 0.5)
  D-3: CIM 유사도는 코사인 유사도 기반 (공유 캐릭터 벡터)
  D-4: 스냅샷 ID = project_id + 타임스탬프 + label SHA8
  D-5: conflict_threshold=0.30 (delta_max > threshold → 비호환)
  D-6: 직렬화 스키마 version='2.0.0' 필드 포함

LLM-0: 외부 LLM 호출 없음.
ADR-069
"""

from __future__ import annotations

import hashlib
import math
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from .multi_work_cim import CIMEntry, MultiWorkCIM, ProjectCIM
from .shared_character_db_v2 import SharedCharacterDBV2

# ══════════════════════════════════════════════════════════════════════════════
# V2 데이터클래스
# ══════════════════════════════════════════════════════════════════════════════


@dataclass
class CIMEntryV2(CIMEntry):
    """V2: 보상 가중치 포함 CIM 엔트리.

    Attributes:
        reward_weighted_weight: 보상 점수로 선형 보정된 가중치.
            reward_weighted_weight = weight × clamp(avg_reward, 0, 1)
    """

    reward_weighted_weight: float = 0.0

    def update_with_reward(self, decay: float, avg_reward: float) -> None:
        """상호작용 count 증가 + 보상 가중치 재계산.

        Args:
            decay:      감쇠 파라미터 (CIMBootstrap 동일)
            avg_reward: 캐릭터 쌍의 평균 보상 점수 [0, 1]
        """
        self.count += 1
        self.weight = 1.0 - math.exp(-decay * self.count)
        clamped = max(0.0, min(1.0, avg_reward))
        self.reward_weighted_weight = round(self.weight * clamped, 6)


@dataclass
class ProjectCIMV2(ProjectCIM):
    """V2: RewardTrace 연동 ProjectCIM.

    Attributes:
        char_db: SharedCharacterDBV2 참조 (None이면 기본 reward 0.5)
        conflict_threshold: reward_weighted_weight 차이 임계값
    """

    char_db: Optional[SharedCharacterDBV2] = None
    conflict_threshold: float = 0.30
    _entries_v2: Dict[Tuple[str, str], CIMEntryV2] = field(
        default_factory=dict, repr=False
    )

    def _get_avg_reward(self, char_a: str, char_b: str) -> float:
        """두 캐릭터 보상 평균. char_db 없으면 0.5 기본값."""
        if self.char_db is None:
            return 0.5
        traces = []
        for cid in (char_a, char_b):
            rt = self.char_db.get_reward_trace(cid)
            if rt is not None:
                traces.append(rt.mean())
        if not traces:
            return 0.5
        return round(sum(traces) / len(traces), 6)

    def record_interaction_v2(
        self, char_a: str, char_b: str, reward: Optional[float] = None
    ) -> None:
        """상호작용 기록 + 보상 가중치 업데이트.

        Args:
            char_a, char_b: 등장 캐릭터 쌍
            reward: 명시적 보상 점수 (None이면 char_db에서 조회)
        """
        if char_a == char_b:
            return
        # v1 record_interaction (weight 업데이트)
        self.record_interaction(char_a, char_b)
        # v2 엔트리
        key = self._key(char_a, char_b)
        if key not in self._entries_v2:
            self._entries_v2[key] = CIMEntryV2(char_a=key[0], char_b=key[1])
        avg_r = reward if reward is not None else self._get_avg_reward(char_a, char_b)
        self._entries_v2[key].update_with_reward(self.decay, avg_r)

    def reward_weight(self, char_a: str, char_b: str) -> float:
        """두 캐릭터 간 보상 가중치 조회."""
        key = self._key(char_a, char_b)
        entry = self._entries_v2.get(key)
        return entry.reward_weighted_weight if entry else 0.0

    def to_dict(self) -> Dict[str, Any]:
        """직렬화 (스냅샷용)."""
        return {
            "project_id": self.project_id,
            "decay": self.decay,
            "entries": {
                f"{k[0]}/{k[1]}": {
                    "count": v.count,
                    "weight": round(v.weight, 6),
                }
                for k, v in self.entries.items()
            },
            "entries_v2": {
                f"{k[0]}/{k[1]}": {
                    "count": v.count,
                    "weight": round(v.weight, 6),
                    "reward_weighted_weight": v.reward_weighted_weight,
                }
                for k, v in self._entries_v2.items()
            },
        }

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
        char_db: Optional[SharedCharacterDBV2] = None,
    ) -> "ProjectCIMV2":
        """역직렬화."""
        obj = cls(
            project_id=data["project_id"],
            decay=data.get("decay", 0.95),
            char_db=char_db,
        )
        for pair_str, ev in data.get("entries", {}).items():
            a, b = pair_str.split("/", 1)
            key = (min(a, b), max(a, b))
            entry = CIMEntry(char_a=key[0], char_b=key[1])
            entry.count = ev["count"]
            entry.weight = ev["weight"]
            obj.entries[key] = entry
        for pair_str, ev in data.get("entries_v2", {}).items():
            a, b = pair_str.split("/", 1)
            key = (min(a, b), max(a, b))
            entry_v2 = CIMEntryV2(char_a=key[0], char_b=key[1])
            entry_v2.count = ev["count"]
            entry_v2.weight = ev["weight"]
            entry_v2.reward_weighted_weight = ev["reward_weighted_weight"]
            obj._entries_v2[key] = entry_v2
        return obj


@dataclass
class CIMSnapshot:
    """ProjectCIM v2 스냅샷.

    Attributes:
        project_id:  소유 프로젝트
        snapshot_id: 고유 UUID
        label:       선택 레이블
        created_at:  ISO-8601 타임스탬프
        data:        ProjectCIMV2.to_dict() 결과
    """

    project_id: str
    snapshot_id: str
    label: str
    created_at: str
    data: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_id": self.project_id,
            "snapshot_id": self.snapshot_id,
            "label": self.label,
            "created_at": self.created_at,
            "data": self.data,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "CIMSnapshot":
        return cls(
            project_id=d["project_id"],
            snapshot_id=d["snapshot_id"],
            label=d.get("label", ""),
            created_at=d["created_at"],
            data=d["data"],
        )


@dataclass
class InterProjectCIMScore:
    """두 프로젝트 간 CIM 유사도 보고서.

    Attributes:
        project_a, project_b: 비교 대상 프로젝트
        shared_chars:  공유 캐릭터 목록
        cosine_similarity: 공유 캐릭터 쌍 CIM 벡터의 코사인 유사도 [0, 1]
        weight_delta_max: 최대 가중치 차이 (v1 weight 기준)
        reward_delta_max: 최대 보상 가중치 차이 (v2 reward_weighted_weight)
        is_compatible: weight_delta_max < conflict_threshold
    """

    project_a: str
    project_b: str
    shared_chars: List[str]
    cosine_similarity: float
    weight_delta_max: float
    reward_delta_max: float
    is_compatible: bool

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_a": self.project_a,
            "project_b": self.project_b,
            "shared_chars": self.shared_chars,
            "cosine_similarity": self.cosine_similarity,
            "weight_delta_max": self.weight_delta_max,
            "reward_delta_max": self.reward_delta_max,
            "is_compatible": self.is_compatible,
        }


# ══════════════════════════════════════════════════════════════════════════════
# MultiWorkCIMV2
# ══════════════════════════════════════════════════════════════════════════════


class MultiWorkCIMV2(MultiWorkCIM):
    """멀티워크 CIM v2.0.

    v1 MultiWorkCIM을 상속하며 v1 API(init_project, record, global_weight,
    aggregate_warm_start, stats)를 완전히 보존한다.

    추가 기능:
    - record_v2(): SharedCharacterDBV2 보상 연동 기록
    - snapshot_project() / restore_project(): ProjectCIMV2 스냅샷
    - inter_project_cim_score(): 프로젝트 간 CIM 코사인 유사도
    - reward_weighted_global_weight(): 보상 가중 전역 집계
    - export_state_v2() / import_state_v2(): 완전 직렬화

    Thread-safe (부모 _lock + 자체 _lock_v2).
    """

    VERSION = "2.0.0"

    def __init__(
        self,
        decay: float = 0.95,
        char_db: Optional[SharedCharacterDBV2] = None,
        conflict_threshold: float = 0.30,
    ) -> None:
        """
        Args:
            decay:              CIM 감쇠 파라미터
            char_db:            SharedCharacterDBV2 참조 (None이면 reward 0.5)
            conflict_threshold: 프로젝트 호환성 판정 임계값 (weight_delta_max)
        """
        super().__init__(decay=decay)
        self._char_db = char_db
        self._conflict_threshold = conflict_threshold
        # v2 ProjectCIMV2 저장소 (project_id → ProjectCIMV2)
        self._project_cims_v2: Dict[str, ProjectCIMV2] = {}
        # 스냅샷 저장소
        self._snapshots: Dict[str, List[CIMSnapshot]] = {}  # project_id → list
        self._snapshot_index: Dict[str, CIMSnapshot] = {}   # snapshot_id → snap
        self._lock_v2 = threading.RLock()

    # ------------------------------------------------------------------ #
    # v1 init_project override — ProjectCIMV2로 초기화
    # ------------------------------------------------------------------ #

    def init_project(self, project_id: str) -> ProjectCIMV2:
        """프로젝트 CIM 초기화 (v2 인스턴스 반환).

        Raises:
            KeyError: 이미 초기화된 프로젝트
        """
        with self._lock_v2:
            if project_id in self._project_cims_v2:
                raise KeyError(f"CIM already initialized: {project_id}")
            cim_v2 = ProjectCIMV2(
                project_id=project_id,
                decay=self._decay,
                char_db=self._char_db,
                conflict_threshold=self._conflict_threshold,
            )
            self._project_cims_v2[project_id] = cim_v2
            # v1 부모 딕셔너리도 동기화 (v1 메서드 호환)
            self._project_cims[project_id] = cim_v2
            self._snapshots[project_id] = []
            return cim_v2

    def get_project_cim_v2(self, project_id: str) -> Optional[ProjectCIMV2]:
        """ProjectCIMV2 조회."""
        return self._project_cims_v2.get(project_id)

    # ------------------------------------------------------------------ #
    # v2 기록
    # ------------------------------------------------------------------ #

    def record_v2(
        self,
        project_id: str,
        char_a: str,
        char_b: str,
        reward: Optional[float] = None,
    ) -> None:
        """상호작용 기록 + 보상 가중치 업데이트.

        Args:
            project_id: 대상 프로젝트
            char_a, char_b: 등장 캐릭터 쌍
            reward: 명시적 보상 점수 (None이면 char_db 조회 → 기본 0.5)

        Raises:
            KeyError: 미초기화 프로젝트
        """
        with self._lock_v2:
            cim_v2 = self._project_cims_v2.get(project_id)
            if cim_v2 is None:
                raise KeyError(f"CIM v2 not initialized for: {project_id}")
            cim_v2.record_interaction_v2(char_a, char_b, reward=reward)

    # ------------------------------------------------------------------ #
    # 스냅샷
    # ------------------------------------------------------------------ #

    def snapshot_project(
        self, project_id: str, label: str = ""
    ) -> CIMSnapshot:
        """ProjectCIMV2 상태를 스냅샷으로 저장.

        Args:
            project_id: 대상 프로젝트
            label:      선택 레이블

        Returns:
            저장된 CIMSnapshot

        Raises:
            KeyError: 미초기화 프로젝트
        """
        with self._lock_v2:
            cim_v2 = self._project_cims_v2.get(project_id)
            if cim_v2 is None:
                raise KeyError(f"CIM v2 not initialized for: {project_id}")
            now = datetime.now(timezone.utc).isoformat()
            label_hash = hashlib.sha256(
                f"{project_id}{now}{label}".encode()
            ).hexdigest()[:8]
            snap_id = f"{project_id}-cim-{label_hash}"
            snap = CIMSnapshot(
                project_id=project_id,
                snapshot_id=snap_id,
                label=label,
                created_at=now,
                data=cim_v2.to_dict(),
            )
            self._snapshots[project_id].append(snap)
            self._snapshot_index[snap_id] = snap
            return snap

    def restore_project(
        self, project_id: str, snapshot_id: str
    ) -> None:
        """스냅샷으로 ProjectCIMV2 복원.

        Args:
            project_id:  복원할 프로젝트
            snapshot_id: 복원할 스냅샷 ID

        Raises:
            KeyError: 스냅샷 없음 또는 프로젝트 불일치
        """
        with self._lock_v2:
            snap = self._snapshot_index.get(snapshot_id)
            if snap is None:
                raise KeyError(f"Snapshot not found: {snapshot_id}")
            if snap.project_id != project_id:
                raise KeyError(
                    f"Snapshot {snapshot_id} belongs to {snap.project_id}, "
                    f"not {project_id}"
                )
            restored = ProjectCIMV2.from_dict(snap.data, char_db=self._char_db)
            self._project_cims_v2[project_id] = restored
            self._project_cims[project_id] = restored  # v1 동기화

    def list_project_snapshots(self, project_id: str) -> List[CIMSnapshot]:
        """프로젝트의 스냅샷 목록 (생성 순서)."""
        with self._lock_v2:
            return list(self._snapshots.get(project_id, []))

    # ------------------------------------------------------------------ #
    # 프로젝트 간 CIM 유사도
    # ------------------------------------------------------------------ #

    def inter_project_cim_score(
        self,
        project_a: str,
        project_b: str,
        shared_chars: List[str],
    ) -> InterProjectCIMScore:
        """두 프로젝트 CIM의 코사인 유사도 및 호환성 판정.

        공유 캐릭터 쌍(i,j)에 대해 v1 weight 벡터를 구성하고
        코사인 유사도를 계산한다.

        Args:
            project_a, project_b: 비교 프로젝트
            shared_chars: 두 프로젝트 공유 캐릭터 목록

        Returns:
            InterProjectCIMScore
        """
        with self._lock_v2:
            cim_a = self._project_cims_v2.get(project_a)
            cim_b = self._project_cims_v2.get(project_b)

            if not shared_chars or cim_a is None or cim_b is None:
                return InterProjectCIMScore(
                    project_a=project_a,
                    project_b=project_b,
                    shared_chars=shared_chars,
                    cosine_similarity=0.0,
                    weight_delta_max=0.0,
                    reward_delta_max=0.0,
                    is_compatible=True,
                )

            # 공유 캐릭터 쌍 목록 (upper triangle)
            pairs = [
                (shared_chars[i], shared_chars[j])
                for i in range(len(shared_chars))
                for j in range(i + 1, len(shared_chars))
            ]

            if not pairs:
                return InterProjectCIMScore(
                    project_a=project_a,
                    project_b=project_b,
                    shared_chars=shared_chars,
                    cosine_similarity=1.0,
                    weight_delta_max=0.0,
                    reward_delta_max=0.0,
                    is_compatible=True,
                )

            vec_a = [cim_a.weight(ca, cb) for ca, cb in pairs]
            vec_b = [cim_b.weight(ca, cb) for ca, cb in pairs]
            rew_a = [cim_a.reward_weight(ca, cb) for ca, cb in pairs]
            rew_b = [cim_b.reward_weight(ca, cb) for ca, cb in pairs]

            cos_sim = self._cosine(vec_a, vec_b)
            delta_max = max(abs(a - b) for a, b in zip(vec_a, vec_b))
            reward_delta = max(abs(a - b) for a, b in zip(rew_a, rew_b))

            return InterProjectCIMScore(
                project_a=project_a,
                project_b=project_b,
                shared_chars=shared_chars,
                cosine_similarity=round(cos_sim, 6),
                weight_delta_max=round(delta_max, 6),
                reward_delta_max=round(reward_delta, 6),
                is_compatible=delta_max < self._conflict_threshold,
            )

    @staticmethod
    def _cosine(vec_a: List[float], vec_b: List[float]) -> float:
        """코사인 유사도 계산."""
        dot = sum(a * b for a, b in zip(vec_a, vec_b))
        norm_a = math.sqrt(sum(a * a for a in vec_a))
        norm_b = math.sqrt(sum(b * b for b in vec_b))
        if norm_a == 0.0 and norm_b == 0.0:
            return 1.0
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    # ------------------------------------------------------------------ #
    # 보상 가중 전역 집계
    # ------------------------------------------------------------------ #

    def reward_weighted_global_weight(
        self, char_a: str, char_b: str
    ) -> float:
        """모든 프로젝트 CIM에서 두 캐릭터 간 보상 가중 평균.

        v1 global_weight()의 보상 가중 버전.
        """
        with self._lock_v2:
            weights = [
                cim_v2.reward_weight(char_a, char_b)
                for cim_v2 in self._project_cims_v2.values()
            ]
            active = [w for w in weights if w > 0]
            if not active:
                return 0.0
            return round(sum(active) / len(active), 6)

    # ------------------------------------------------------------------ #
    # 직렬화
    # ------------------------------------------------------------------ #

    def export_state_v2(self) -> Dict[str, Any]:
        """v2 전체 상태 직렬화 (7-key schema).

        Keys: version, exported_at, decay, conflict_threshold,
              project_cims, snapshots, total_interactions
        """
        with self._lock_v2:
            total = sum(
                len(c.entries)
                for c in self._project_cims_v2.values()
            )
            return {
                "version": self.VERSION,
                "exported_at": datetime.now(timezone.utc).isoformat(),
                "decay": self._decay,
                "conflict_threshold": self._conflict_threshold,
                "project_cims": {
                    pid: cim.to_dict()
                    for pid, cim in self._project_cims_v2.items()
                },
                "snapshots": {
                    pid: [s.to_dict() for s in snaps]
                    for pid, snaps in self._snapshots.items()
                },
                "total_interactions": total,
            }

    def import_state_v2(self, data: Dict[str, Any]) -> None:
        """v2 상태 복원.

        Args:
            data: export_state_v2() 반환값

        Raises:
            ValueError: 버전 불일치
        """
        if data.get("version") != self.VERSION:
            raise ValueError(
                f"Version mismatch: expected {self.VERSION}, "
                f"got {data.get('version')}"
            )
        with self._lock_v2:
            self._project_cims_v2.clear()
            self._project_cims.clear()
            self._snapshots.clear()
            self._snapshot_index.clear()

            for pid, cim_data in data.get("project_cims", {}).items():
                cim_v2 = ProjectCIMV2.from_dict(cim_data, char_db=self._char_db)
                self._project_cims_v2[pid] = cim_v2
                self._project_cims[pid] = cim_v2
                self._snapshots[pid] = []

            for pid, snap_list in data.get("snapshots", {}).items():
                snaps = [CIMSnapshot.from_dict(s) for s in snap_list]
                self._snapshots[pid] = snaps
                for s in snaps:
                    self._snapshot_index[s.snapshot_id] = s

    # ------------------------------------------------------------------ #
    # 통계
    # ------------------------------------------------------------------ #

    def status_v2(self) -> Dict[str, Any]:
        """v2 통계 (v1 stats() 확장)."""
        with self._lock_v2:
            base = self.stats()
            return {
                **base,
                "version": self.VERSION,
                "conflict_threshold": self._conflict_threshold,
                "has_char_db": self._char_db is not None,
                "per_project_snapshots": {
                    pid: len(snaps)
                    for pid, snaps in self._snapshots.items()
                },
                "per_project_reward_pairs": {
                    pid: len(cim._entries_v2)
                    for pid, cim in self._project_cims_v2.items()
                },
            }
