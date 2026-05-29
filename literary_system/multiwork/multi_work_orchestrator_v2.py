"""
V608 MultiWorkOrchestratorV2 — SharedCharacterDBV2 + SharedWorldDBV2 통합 오케스트레이터

MultiWorkOrchestrator v1 완전 상속 + v2 DB 교체:
  - SharedCharacterDB  → SharedCharacterDBV2 (스냅샷, RLHF 추적, 충돌 감지)
  - SharedWorldDB      → SharedWorldDBV2     (스냅샷, 충돌 감지, 일관성 점수)

신규 API:
  - checkpoint_project(project_id, label)         : 프로젝트 단위 체크포인트
  - restore_project(project_id, checkpoint_id)    : 체크포인트 복원
  - detect_inter_project_conflicts(project_ids)   : 다중 프로젝트 간 충돌 탐지
  - dual_consistency_score(project_a, project_b)  : 캐릭터+월드 통합 일관성
  - process_scene_v2(event, reward_score)         : 씬 처리 + RLHF 보상 기록
  - export_state_v2() / import_state_v2(data)     : 전체 v2 상태 직렬화

LLM-0: 외부 LLM 호출 없음.
ADR-068
"""

from __future__ import annotations

import hashlib
import threading
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Set

from .multi_work_orchestrator import (
    MultiWorkOrchestrator,
    OrchestratorSnapshot,
    SceneProcessEvent,
)
from .shared_character_db_v2 import ConflictRecord, SharedCharacterDBV2
from .shared_world_db_v2 import LocationConflict, SharedWorldDBV2

# ────────────────────────────────────────────────────────────────
# 보조 데이터클래스
# ────────────────────────────────────────────────────────────────

@dataclass
class ProjectCheckpoint:
    """프로젝트 단위 체크포인트 — 캐릭터 스냅샷 ID 목록 + 월드 스냅샷 ID."""
    checkpoint_id: str
    project_id: str
    label: str
    timestamp: float
    char_snapshot_ids: Dict[str, str]   # character_id → snapshot_id
    world_snapshot_id: str


@dataclass
class InterProjectConflictReport:
    """다중 프로젝트 간 충돌 탐지 보고서."""
    project_ids: List[str]
    character_conflicts: List[ConflictRecord]
    location_conflicts: List[LocationConflict]
    detected_at: float = field(default_factory=time.time)

    @property
    def total_conflicts(self) -> int:
        return len(self.character_conflicts) + len(self.location_conflicts)

    @property
    def is_clean(self) -> bool:
        return self.total_conflicts == 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "project_ids": self.project_ids,
            "character_conflicts": [c.to_dict() for c in self.character_conflicts],
            "location_conflicts": [lc.to_dict() for lc in self.location_conflicts],
            "total_conflicts": self.total_conflicts,
            "is_clean": self.is_clean,
            "detected_at": self.detected_at,
        }


# ────────────────────────────────────────────────────────────────
# MultiWorkOrchestratorV2
# ────────────────────────────────────────────────────────────────

class MultiWorkOrchestratorV2(MultiWorkOrchestrator):
    """
    V608 MultiWorkOrchestrator v2.0

    v1 API 완전 호환. SharedCharacterDBV2 + SharedWorldDBV2로 업그레이드하여
    RLHF 보상 추적 / 스냅샷 체크포인트 / 충돌 탐지 / 일관성 지표를 제공.

    Usage::

        orch = MultiWorkOrchestratorV2()
        orch.register_author("alice", LicenseType.COMMERCIAL)
        proj = orch.create_project("alice", "내 드라마", "drama")
        session = orch.open_session("alice", proj.project_id)

        # v2 씬 처리 (RLHF 보상 포함)
        orch.process_scene_v2(
            SceneProcessEvent(
                project_id=proj.project_id,
                scene_id="s-001",
                characters_present=["hero", "villain"],
                arc_deltas={"hero": 0.2, "villain": -0.1},
                tokens_used=500,
            ),
            reward_score=0.82,
        )

        # 프로젝트 체크포인트
        cp = orch.checkpoint_project(proj.project_id, label="ep1-end")

        orch.close_session("alice", proj.project_id, mark_completed=True)
    """

    VERSION = "2.0.0"

    def __init__(
        self,
        max_concurrent: int = 10,
        cim_decay: float = 0.95,
    ) -> None:
        super().__init__(max_concurrent=max_concurrent, cim_decay=cim_decay)

        # v1 DB → v2 DB 교체
        self.char_db: SharedCharacterDBV2 = SharedCharacterDBV2()
        self.world_db: SharedWorldDBV2 = SharedWorldDBV2()

        # project_id → Set[character_id] — 프로젝트별 등장 캐릭터 추적
        self._project_characters: Dict[str, Set[str]] = {}
        # project_id → Set[location_id] — 프로젝트별 등장 위치 추적
        self._project_locations: Dict[str, Set[str]] = {}
        # checkpoint_id → ProjectCheckpoint
        self._project_checkpoints: Dict[str, ProjectCheckpoint] = {}
        # project_id → List[checkpoint_id] (순서 보장)
        self._project_checkpoint_index: Dict[str, List[str]] = {}

        self._lock_v2 = threading.RLock()

    # ────────────────────────────────────────────────────────────
    # 씬 처리 (v2 확장)
    # ────────────────────────────────────────────────────────────

    def process_scene_v2(
        self,
        event: SceneProcessEvent,
        reward_score: Optional[float] = None,
    ) -> None:
        """
        v1 process_scene 전체 실행 후 RLHF 보상 기록.

        등장 캐릭터는 프로젝트 캐릭터 집합에 자동 추적된다.

        Args:
            event:        SceneProcessEvent (v1과 동일)
            reward_score: 이 씬의 RLHF 보상 점수 (None 이면 기록 생략)

        Raises:
            ProjectConflict: 활성 세션 없음
        """
        # 1. v1 process_scene 그대로 실행
        self.process_scene(event)

        # 2. 프로젝트 캐릭터 집합 갱신
        with self._lock_v2:
            proj_chars = self._project_characters.setdefault(
                event.project_id, set()
            )
            proj_chars.update(event.characters_present)

        # 3. RLHF 보상 기록 (reward_score 있을 때만)
        if reward_score is not None:
            for char_id in event.characters_present:
                if self.char_db.get_character(char_id) is not None:
                    self.char_db.record_reward(char_id, reward_score)

    def track_location(self, project_id: str, location_id: str) -> None:
        """프로젝트에 위치 ID를 등록 (충돌 감지 대상 추적)."""
        with self._lock_v2:
            self._project_locations.setdefault(project_id, set()).add(
                location_id
            )

    # ────────────────────────────────────────────────────────────
    # 프로젝트 체크포인트
    # ────────────────────────────────────────────────────────────

    def checkpoint_project(
        self,
        project_id: str,
        label: str = "",
    ) -> ProjectCheckpoint:
        """
        프로젝트와 연관된 모든 캐릭터 + 월드 전체를 스냅샷.

        Returns:
            ProjectCheckpoint (checkpoint_id, char_snapshot_ids, world_snapshot_id)

        Note:
            캐릭터 스냅샷은 ``process_scene_v2`` 또는 ``process_scene``으로
            등장이 기록된 캐릭터에 한해 생성된다.
        """
        ts = time.time()
        raw_id = f"{project_id}:{label}:{ts}"
        checkpoint_id = hashlib.sha256(raw_id.encode()).hexdigest()[:12]

        # 캐릭터 스냅샷
        with self._lock_v2:
            char_ids = set(self._project_characters.get(project_id, set()))

        char_snapshot_ids: Dict[str, str] = {}
        for char_id in char_ids:
            if self.char_db.get_character(char_id) is not None:
                sid = self.char_db.checkpoint(
                    char_id, label=f"project:{project_id}:{label}"
                )
                char_snapshot_ids[char_id] = sid

        # 월드 스냅샷 (전체)
        world_snapshot_id = self.world_db.checkpoint(
            label=f"project:{project_id}:{label}"
        )

        cp = ProjectCheckpoint(
            checkpoint_id=checkpoint_id,
            project_id=project_id,
            label=label,
            timestamp=ts,
            char_snapshot_ids=char_snapshot_ids,
            world_snapshot_id=world_snapshot_id,
        )

        with self._lock_v2:
            self._project_checkpoints[checkpoint_id] = cp
            self._project_checkpoint_index.setdefault(
                project_id, []
            ).append(checkpoint_id)

        return cp

    def restore_project(
        self,
        project_id: str,
        checkpoint_id: str,
    ) -> None:
        """
        체크포인트에서 프로젝트 캐릭터 상태 복원.

        월드 복원은 전체 DB에 영향을 주므로 캐릭터만 복원한다.
        월드 복원이 필요하면 ``world_db.restore(world_snapshot_id)`` 를 직접 호출.

        Raises:
            KeyError: checkpoint_id 미존재 또는 project_id 불일치
        """
        with self._lock_v2:
            cp = self._project_checkpoints.get(checkpoint_id)
        if cp is None:
            raise KeyError(f"checkpoint_id={checkpoint_id!r} not found")
        if cp.project_id != project_id:
            raise KeyError(
                f"checkpoint {checkpoint_id!r} belongs to "
                f"project {cp.project_id!r}, not {project_id!r}"
            )

        for char_id, snap_id in cp.char_snapshot_ids.items():
            self.char_db.restore(char_id, snap_id)

    def get_project_checkpoint(
        self, checkpoint_id: str
    ) -> Optional[ProjectCheckpoint]:
        """checkpoint_id로 ProjectCheckpoint 반환."""
        with self._lock_v2:
            return self._project_checkpoints.get(checkpoint_id)

    def list_project_checkpoints(
        self, project_id: str
    ) -> List[ProjectCheckpoint]:
        """프로젝트의 모든 체크포인트를 시간순으로 반환."""
        with self._lock_v2:
            ids = self._project_checkpoint_index.get(project_id, [])
            return [
                self._project_checkpoints[cid]
                for cid in ids
                if cid in self._project_checkpoints
            ]

    # ────────────────────────────────────────────────────────────
    # 충돌 탐지
    # ────────────────────────────────────────────────────────────

    def register_project_states(self, project_ids: List[str]) -> None:
        """
        충돌 감지 기준점 등록 — 현재 상태를 프로젝트별로 기록.

        ``detect_inter_project_conflicts`` 호출 전에 실행해야 충돌을 올바르게 감지한다.
        """
        for pid in project_ids:
            with self._lock_v2:
                char_ids = set(self._project_characters.get(pid, set()))
                loc_ids = set(self._project_locations.get(pid, set()))

            for cid in char_ids:
                if self.char_db.get_character(cid) is not None:
                    self.char_db.register_project_state(pid, cid)

            for lid in loc_ids:
                self.world_db.register_project_state(pid, lid)

    def detect_inter_project_conflicts(
        self,
        project_ids: List[str],
    ) -> InterProjectConflictReport:
        """
        다중 프로젝트 간 캐릭터/위치 충돌 탐지.

        프로젝트 쌍(project_a, project_b) 조합 전수에 대해:
          - 공유 캐릭터의 ConflictRecord 탐지
          - 공유 위치의 LocationConflict 탐지

        Returns:
            InterProjectConflictReport
        """
        char_conflicts: List[ConflictRecord] = []
        loc_conflicts: List[LocationConflict] = []

        for i in range(len(project_ids)):
            for j in range(i + 1, len(project_ids)):
                pa, pb = project_ids[i], project_ids[j]

                with self._lock_v2:
                    chars_a = set(self._project_characters.get(pa, set()))
                    chars_b = set(self._project_characters.get(pb, set()))
                shared_chars = chars_a & chars_b

                for cid in shared_chars:
                    rec = self.char_db.detect_conflicts(cid, pa, pb)
                    if rec is not None:
                        char_conflicts.append(rec)

                with self._lock_v2:
                    locs_a = set(self._project_locations.get(pa, set()))
                    locs_b = set(self._project_locations.get(pb, set()))
                shared_locs = locs_a & locs_b

                for lid in shared_locs:
                    rec = self.world_db.detect_location_conflicts(lid, pa, pb)
                    if rec is not None:
                        loc_conflicts.append(rec)

        return InterProjectConflictReport(
            project_ids=list(project_ids),
            character_conflicts=char_conflicts,
            location_conflicts=loc_conflicts,
        )

    # ────────────────────────────────────────────────────────────
    # 일관성 점수
    # ────────────────────────────────────────────────────────────

    def dual_consistency_score(
        self,
        project_a: str,
        project_b: str,
    ) -> float:
        """
        두 프로젝트의 캐릭터 + 월드 통합 일관성 점수 (0.0 ~ 1.0).

        산식::

            char_score  = mean(consistency_score(c) for c in shared_chars)
            world_score = world_db.consistency_score()
            result      = (char_score + world_score) / 2

        공유 캐릭터 없으면 char_score = 0.5 (중립).
        """
        with self._lock_v2:
            chars_a = set(self._project_characters.get(project_a, set()))
            chars_b = set(self._project_characters.get(project_b, set()))
        shared_chars = chars_a & chars_b

        if shared_chars:
            scores = [
                self.char_db.consistency_score(cid)
                for cid in shared_chars
                if self.char_db.get_character(cid) is not None
            ]
            char_score = sum(scores) / len(scores) if scores else 0.5
        else:
            char_score = 0.5

        world_score = self.world_db.consistency_score()
        return round((char_score + world_score) / 2.0, 4)

    def project_char_consistency(self, project_id: str) -> float:
        """
        단일 프로젝트 내 모든 등장 캐릭터의 평균 일관성 점수 (0.0 ~ 1.0).

        캐릭터 없으면 0.5 (중립).
        """
        with self._lock_v2:
            char_ids = set(self._project_characters.get(project_id, set()))

        if not char_ids:
            return 0.5

        scores = [
            self.char_db.consistency_score(cid)
            for cid in char_ids
            if self.char_db.get_character(cid) is not None
        ]
        return round(sum(scores) / len(scores), 4) if scores else 0.5

    # ────────────────────────────────────────────────────────────
    # 직렬화
    # ────────────────────────────────────────────────────────────

    def export_state_v2(self) -> Dict[str, Any]:
        """
        전체 v2 상태를 JSON 직렬화 가능 dict으로 내보내기.

        포함 항목: char_db, world_db, project_characters,
        project_locations, checkpoints, total_scenes_processed.
        """
        char_export = self.char_db.export_snapshot()
        world_export = self.world_db.export_snapshot()

        with self._lock_v2:
            proj_chars = {
                pid: list(cids)
                for pid, cids in self._project_characters.items()
            }
            proj_locs = {
                pid: list(lids)
                for pid, lids in self._project_locations.items()
            }
            checkpoints = {
                cid: {
                    "checkpoint_id": cp.checkpoint_id,
                    "project_id": cp.project_id,
                    "label": cp.label,
                    "timestamp": cp.timestamp,
                    "char_snapshot_ids": dict(cp.char_snapshot_ids),
                    "world_snapshot_id": cp.world_snapshot_id,
                }
                for cid, cp in self._project_checkpoints.items()
            }
            cp_index = {
                pid: list(ids)
                for pid, ids in self._project_checkpoint_index.items()
            }

        with self._lock:
            total_scenes = self._total_scenes

        return {
            "version": self.VERSION,
            "exported_at": time.time(),
            "char_db": char_export,
            "world_db": world_export,
            "project_characters": proj_chars,
            "project_locations": proj_locs,
            "checkpoints": checkpoints,
            "checkpoint_index": cp_index,
            "total_scenes_processed": total_scenes,
        }

    def import_state_v2(self, data: Dict[str, Any]) -> None:
        """
        export_state_v2() 결과를 로드.

        기존 DB 상태에 병합 (덮어쓰기 아닌 추가).
        """
        if "char_db" in data:
            self.char_db.import_snapshot(data["char_db"])
        if "world_db" in data:
            self.world_db.import_snapshot(data["world_db"])

        with self._lock_v2:
            for pid, cids in data.get("project_characters", {}).items():
                self._project_characters.setdefault(pid, set()).update(cids)
            for pid, lids in data.get("project_locations", {}).items():
                self._project_locations.setdefault(pid, set()).update(lids)

            for cid, cpdata in data.get("checkpoints", {}).items():
                cp = ProjectCheckpoint(
                    checkpoint_id=cpdata["checkpoint_id"],
                    project_id=cpdata["project_id"],
                    label=cpdata.get("label", ""),
                    timestamp=cpdata["timestamp"],
                    char_snapshot_ids=dict(cpdata.get("char_snapshot_ids", {})),
                    world_snapshot_id=cpdata.get("world_snapshot_id", ""),
                )
                self._project_checkpoints[cid] = cp

            for pid, ids in data.get("checkpoint_index", {}).items():
                self._project_checkpoint_index[pid] = list(ids)

        with self._lock:
            self._total_scenes = data.get(
                "total_scenes_processed", self._total_scenes
            )

    # ────────────────────────────────────────────────────────────
    # 상태 스냅샷 오버라이드
    # ────────────────────────────────────────────────────────────

    def snapshot(self) -> OrchestratorSnapshot:
        """v2 status 정보를 포함한 전체 스냅샷."""
        base = super().snapshot()
        base.char_db_stats.update(self.char_db.status())
        base.world_db_stats.update(self.world_db.status())
        return base

    # ────────────────────────────────────────────────────────────
    # 편의 메서드
    # ────────────────────────────────────────────────────────────

    def project_character_ids(self, project_id: str) -> List[str]:
        """프로젝트에 등장한 캐릭터 ID 목록 (추적된 것만)."""
        with self._lock_v2:
            return sorted(self._project_characters.get(project_id, set()))

    def project_location_ids(self, project_id: str) -> List[str]:
        """프로젝트에 등록된 위치 ID 목록."""
        with self._lock_v2:
            return sorted(self._project_locations.get(project_id, set()))

    def v2_stats(self) -> Dict[str, Any]:
        """v2 전용 요약 통계."""
        with self._lock_v2:
            n_projects = len(self._project_characters)
            n_checkpoints = len(self._project_checkpoints)
        return {
            "version": self.VERSION,
            "tracked_projects": n_projects,
            "total_checkpoints": n_checkpoints,
            "char_db": self.char_db.status(),
            "world_db": self.world_db.status(),
        }


# ════════════════════════════════════════════════════════════════
# V622 ADR-089 — WorkloadProfile + SLO 상수 + schedule()
# ════════════════════════════════════════════════════════════════

from enum import Enum


class WorkloadProfile(str, Enum):
    """다중 작업 부하 프로파일 (ADR-089 §4.1).

    SINGLE : 단일 프로젝트 — SLO 3,000 ms
    DUAL   : 2개 프로젝트 동시 — SLO 5,000 ms
    TRIPLE : 3개 이상 프로젝트 동시 — SLO 8,000 ms
    """
    SINGLE = "SINGLE"
    DUAL   = "DUAL"
    TRIPLE = "TRIPLE"


# SLO 목표 응답시간 (ms) — 프로파일별
SLO_SINGLE_MS: int = 3_000   # 단일 프로젝트 SLO
SLO_DUAL_MS:   int = 5_000   # 2개 동시 SLO
SLO_TRIPLE_MS: int = 8_000   # 3개+ 동시 SLO

_SLO_MAP: Dict[WorkloadProfile, int] = {
    WorkloadProfile.SINGLE: SLO_SINGLE_MS,
    WorkloadProfile.DUAL:   SLO_DUAL_MS,
    WorkloadProfile.TRIPLE: SLO_TRIPLE_MS,
}


def classify_workload(project_ids: List[str]) -> WorkloadProfile:
    """프로젝트 수로 WorkloadProfile 자동 분류."""
    n = len(project_ids)
    if n <= 1:
        return WorkloadProfile.SINGLE
    elif n == 2:
        return WorkloadProfile.DUAL
    else:
        return WorkloadProfile.TRIPLE


def get_slo_ms(profile: WorkloadProfile) -> int:
    """WorkloadProfile에 해당하는 SLO 목표(ms) 반환."""
    return _SLO_MAP[profile]


class ScheduleResult:
    """schedule() 반환 결과."""

    def __init__(
        self,
        profile: WorkloadProfile,
        slo_ms: int,
        project_order: List[str],
        estimated_ms: int,
        slo_ok: bool,
    ) -> None:
        self.profile: WorkloadProfile = profile
        self.slo_ms: int = slo_ms
        self.project_order: List[str] = project_order
        self.estimated_ms: int = estimated_ms
        self.slo_ok: bool = slo_ok

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile":       self.profile.value,
            "slo_ms":        self.slo_ms,
            "project_order": self.project_order,
            "estimated_ms":  self.estimated_ms,
            "slo_ok":        self.slo_ok,
        }


def schedule(
    project_ids: List[str],
    scene_ms_each: int = 1_000,
) -> "ScheduleResult":
    """WorkloadProfile 기반 스케줄 계획 반환 (ADR-089 §4.3).

    Args:
        project_ids:   처리할 프로젝트 ID 목록.
        scene_ms_each: 프로젝트당 씬 처리 예상 시간(ms), 기본 1,000 ms.

    Returns:
        ScheduleResult — profile / slo_ms / 예상 완료 시간 / SLO 충족 여부.

    알고리즘:
        SINGLE → 단순 직렬.
        DUAL   → 병렬 2-way (최대 처리 시간 기준).
        TRIPLE → 병렬 N-way, Round-Robin 슬롯 배분.
    """
    if not project_ids:
        return ScheduleResult(
            profile=WorkloadProfile.SINGLE,
            slo_ms=SLO_SINGLE_MS,
            project_order=[],
            estimated_ms=0,
            slo_ok=True,
        )

    profile = classify_workload(project_ids)
    slo_ms  = get_slo_ms(profile)

    if profile == WorkloadProfile.SINGLE:
        estimated_ms = scene_ms_each
        order = list(project_ids)
    elif profile == WorkloadProfile.DUAL:
        # 병렬 2-way → 둘 중 더 긴 작업이 기준
        estimated_ms = scene_ms_each  # 동시 처리 → 단일 SLO 내
        order = list(project_ids)
    else:
        # TRIPLE: N-way 병렬 — 슬롯 수 = ceil(N / 2)
        import math
        slots = math.ceil(len(project_ids) / 2)
        estimated_ms = slots * scene_ms_each
        # Round-Robin 순서로 정렬
        order = []
        for i in range(slots):
            for j in range(i, len(project_ids), slots):
                order.append(project_ids[j])

    return ScheduleResult(
        profile=profile,
        slo_ms=slo_ms,
        project_order=order,
        estimated_ms=estimated_ms,
        slo_ok=(estimated_ms <= slo_ms),
    )
