"""
V607 SharedCharacterDB v2.0 — RLHF-aware 캐릭터 DB + 버전 스냅샷 + 충돌 감지

V563 SharedCharacterDB v1 확장:
  - CharacterSnapshot  : 불변 버전 스냅샷 (checkpoint / restore)
  - RewardTrace        : 캐릭터별 RLHF 보상 점수 이력
  - ConflictRecord     : 동시 수정 충돌 기록
  - consistency_score  : 아크 + 보상 일관성 0.0~1.0
  - export / import    : 완전 직렬화 JSON 스냅샷

LLM-0: 외부 LLM 호출 없음.
ADR-067
"""

from __future__ import annotations

import copy
import hashlib
import time
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .shared_character_db import SharedCharacterDB, CharacterProfile


# ────────────────────────────────────────────────────────────────
# 보조 데이터클래스
# ────────────────────────────────────────────────────────────────

@dataclass
class CharacterSnapshot:
    """캐릭터 불변 버전 스냅샷."""
    snapshot_id: str
    character_id: str
    timestamp: float
    data: Dict[str, Any]                 # to_dict() 결과의 복사본

    def checksum(self) -> str:
        """스냅샷 내용의 SHA-256 체크섬."""
        import json
        raw = json.dumps(self.data, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode()).hexdigest()[:16]


@dataclass
class RewardTrace:
    """캐릭터별 RLHF 보상 점수 이력."""
    character_id: str
    scores: List[float] = field(default_factory=list)
    timestamps: List[float] = field(default_factory=list)

    def record(self, score: float) -> None:
        self.scores.append(score)
        self.timestamps.append(time.time())

    def mean(self) -> float:
        return sum(self.scores) / len(self.scores) if self.scores else 0.0

    def trend(self) -> float:
        """최근 5개 평균 - 전체 평균 (양수 = 개선 중)."""
        if len(self.scores) < 2:
            return 0.0
        recent = self.scores[-5:]
        return sum(recent) / len(recent) - self.mean()


@dataclass
class ConflictRecord:
    """동시 수정 충돌 레코드."""
    conflict_id: str
    character_id: str
    project_a: str
    project_b: str
    field_conflicts: List[str]           # 충돌된 필드 목록
    detected_at: float = field(default_factory=time.time)
    resolved: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "conflict_id": self.conflict_id,
            "character_id": self.character_id,
            "project_a": self.project_a,
            "project_b": self.project_b,
            "field_conflicts": self.field_conflicts,
            "detected_at": self.detected_at,
            "resolved": self.resolved,
        }


# ────────────────────────────────────────────────────────────────
# SharedCharacterDBV2
# ────────────────────────────────────────────────────────────────

class SharedCharacterDBV2(SharedCharacterDB):
    """
    SharedCharacterDB v2.0 — RLHF-aware 확장.

    v1 API 완전 호환 유지.
    """

    VERSION = "2.0.0"

    def __init__(self) -> None:
        super().__init__()
        # snapshot_id → CharacterSnapshot
        self._snapshots: Dict[str, CharacterSnapshot] = {}
        # character_id → List[snapshot_id] (순서 보장)
        self._snapshot_index: Dict[str, List[str]] = {}
        # character_id → RewardTrace
        self._reward_traces: Dict[str, RewardTrace] = {}
        # conflict_id → ConflictRecord
        self._conflicts: Dict[str, ConflictRecord] = {}
        # project_id → Dict[character_id → trait_hash] (충돌 감지용)
        self._project_trait_hashes: Dict[str, Dict[str, str]] = {}
        self._lock_v2 = threading.Lock()

    # ── 스냅샷 관리 ──────────────────────────────────────────────

    def checkpoint(self, character_id: str, label: str = "") -> str:
        """
        캐릭터의 현재 상태를 스냅샷으로 저장.

        Returns:
            snapshot_id (str)

        Raises:
            KeyError: character_id 미존재 시
        """
        char = self.get_character(character_id)
        if char is None:
            raise KeyError(f"character_id={character_id!r} not found")

        ts = time.time()
        raw_id = f"{character_id}:{ts}:{label}"
        snapshot_id = hashlib.sha256(raw_id.encode()).hexdigest()[:12]

        snap = CharacterSnapshot(
            snapshot_id=snapshot_id,
            character_id=character_id,
            timestamp=ts,
            data=copy.deepcopy(char.to_dict()),
        )
        with self._lock_v2:
            self._snapshots[snapshot_id] = snap
            self._snapshot_index.setdefault(character_id, []).append(snapshot_id)

        return snapshot_id

    def restore(self, character_id: str, snapshot_id: str) -> None:
        """
        스냅샷에서 캐릭터 상태 복원.

        Raises:
            KeyError: snapshot_id 미존재 또는 character_id 불일치 시
        """
        with self._lock_v2:
            snap = self._snapshots.get(snapshot_id)
        if snap is None:
            raise KeyError(f"snapshot_id={snapshot_id!r} not found")
        if snap.character_id != character_id:
            raise KeyError(
                f"snapshot {snapshot_id!r} belongs to "
                f"{snap.character_id!r}, not {character_id!r}"
            )

        data = snap.data
        with self._lock:
            char = self._chars.get(character_id)
            if char is None:
                raise KeyError(f"character_id={character_id!r} not found")
            char.name = data.get("name", char.name)
            char.role = data.get("role", char.role)
            raw_traits = data.get("traits", char.traits)
            char.traits = dict(raw_traits) if isinstance(raw_traits, dict) else char.traits

    def list_snapshots(self, character_id: str) -> List[CharacterSnapshot]:
        """캐릭터의 모든 스냅샷을 시간순으로 반환."""
        with self._lock_v2:
            ids = self._snapshot_index.get(character_id, [])
            return [self._snapshots[sid] for sid in ids if sid in self._snapshots]

    def get_snapshot(self, snapshot_id: str) -> Optional[CharacterSnapshot]:
        with self._lock_v2:
            return self._snapshots.get(snapshot_id)

    # ── RLHF 보상 추적 ──────────────────────────────────────────

    def record_reward(self, character_id: str, reward: float) -> None:
        """
        캐릭터에 RLHF 보상 점수를 기록.

        Raises:
            KeyError: character_id 미존재 시
        """
        if self.get_character(character_id) is None:
            raise KeyError(f"character_id={character_id!r} not found")
        with self._lock_v2:
            if character_id not in self._reward_traces:
                self._reward_traces[character_id] = RewardTrace(character_id)
            self._reward_traces[character_id].record(reward)

    def get_reward_trace(self, character_id: str) -> Optional[RewardTrace]:
        with self._lock_v2:
            return self._reward_traces.get(character_id)

    # ── 일관성 점수 ──────────────────────────────────────────────

    def consistency_score(self, character_id: str) -> float:
        """
        캐릭터 일관성 점수 0.0~1.0.

        arc_score  : 아크 이력 표준편차 역수 (변동 적을수록 높음)
        reward_score: 보상 이력 평균 (정규화)
        """
        char = self.get_character(character_id)
        if char is None:
            return 0.0

        # 아크 일관성 — arc delta 표준편차
        arc_values = [v for _, v in char.arc_history] if char.arc_history else []
        if len(arc_values) >= 2:
            mean = sum(arc_values) / len(arc_values)
            variance = sum((v - mean) ** 2 for v in arc_values) / len(arc_values)
            std = variance ** 0.5
            arc_score = 1.0 / (1.0 + std)
        elif len(arc_values) == 1:
            arc_score = 1.0
        else:
            arc_score = 0.5  # 데이터 없음 → 중립

        # 보상 일관성 — 평균 보상 ([-10,+10] 정규화)
        with self._lock_v2:
            trace = self._reward_traces.get(character_id)
        if trace and trace.scores:
            raw_mean = trace.mean()
            reward_score = (raw_mean + 10.0) / 20.0
            reward_score = max(0.0, min(1.0, reward_score))
        else:
            reward_score = 0.5

        return round((arc_score + reward_score) / 2.0, 4)

    # ── 충돌 감지 ─────────────────────────────────────────────────

    def _trait_hash(self, character_id: str) -> str:
        """현재 캐릭터 traits 의 짧은 해시."""
        char = self.get_character(character_id)
        if char is None:
            return ""
        key = "|".join(sorted(char.traits))
        return hashlib.sha256(key.encode()).hexdigest()[:8]

    def register_project_state(self, project_id: str, character_id: str) -> None:
        """특정 시점의 project × character trait 해시를 등록 (충돌 감지 기준점)."""
        with self._lock_v2:
            self._project_trait_hashes.setdefault(project_id, {})[
                character_id
            ] = self._trait_hash(character_id)

    def detect_conflicts(
        self, character_id: str, project_a: str, project_b: str
    ) -> Optional[ConflictRecord]:
        """
        두 프로젝트의 캐릭터 상태가 기준점에서 서로 다르게 변경됐는지 감지.

        Returns:
            ConflictRecord if conflict detected, else None
        """
        with self._lock_v2:
            hash_a_base = self._project_trait_hashes.get(project_a, {}).get(character_id)
            hash_b_base = self._project_trait_hashes.get(project_b, {}).get(character_id)

        current_hash = self._trait_hash(character_id)

        # 둘 다 기준점에서 달라졌고, 기준점도 서로 다른 경우 → 충돌
        changed_a = hash_a_base is not None and hash_a_base != current_hash
        changed_b = hash_b_base is not None and hash_b_base != current_hash
        bases_differ = hash_a_base != hash_b_base

        if changed_a and changed_b and bases_differ:
            conflict_id = hashlib.sha256(
                f"{character_id}:{project_a}:{project_b}:{time.time()}".encode()
            ).hexdigest()[:10]
            record = ConflictRecord(
                conflict_id=conflict_id,
                character_id=character_id,
                project_a=project_a,
                project_b=project_b,
                field_conflicts=["traits"],
            )
            with self._lock_v2:
                self._conflicts[conflict_id] = record
            return record
        return None

    def resolve_conflict(self, conflict_id: str) -> bool:
        """충돌을 해결됨으로 표시."""
        with self._lock_v2:
            rec = self._conflicts.get(conflict_id)
            if rec is None:
                return False
            rec.resolved = True
            return True

    def list_conflicts(self, resolved: bool = False) -> List[ConflictRecord]:
        """충돌 목록 반환 (resolved=False → 미해결만)."""
        with self._lock_v2:
            return [r for r in self._conflicts.values() if r.resolved == resolved]

    # ── 직렬화 ─────────────────────────────────────────────────

    def export_snapshot(self) -> Dict[str, Any]:
        """전체 DB 상태를 JSON 직렬화 가능 dict으로 내보내기."""
        with self._lock:
            chars = {cid: c.to_dict() for cid, c in self._chars.items()}
        with self._lock_v2:
            snaps = {
                sid: {
                    "snapshot_id": s.snapshot_id,
                    "character_id": s.character_id,
                    "timestamp": s.timestamp,
                    "data": s.data,
                }
                for sid, s in self._snapshots.items()
            }
            rewards = {
                cid: {"scores": t.scores, "timestamps": t.timestamps}
                for cid, t in self._reward_traces.items()
            }
            conflicts = {cid: r.to_dict() for cid, r in self._conflicts.items()}

        return {
            "version": self.VERSION,
            "exported_at": time.time(),
            "characters": chars,
            "snapshots": snaps,
            "snapshot_index": {
                k: list(v) for k, v in self._snapshot_index.items()
            },
            "reward_traces": rewards,
            "conflicts": conflicts,
        }

    def import_snapshot(self, data: Dict[str, Any]) -> int:
        """
        export_snapshot() 결과를 DB에 로드.

        Returns:
            로드된 캐릭터 수
        """
        chars = data.get("characters", {})
        for cid, cdata in chars.items():
            if self.get_character(cid) is None:
                self.add_character(
                    character_id=cid,
                    name=cdata.get("name", cid),
                    role=cdata.get("role", "unknown"),
                    traits=cdata.get("traits", []),
                )

        with self._lock_v2:
            for sid, sdata in data.get("snapshots", {}).items():
                snap = CharacterSnapshot(
                    snapshot_id=sdata["snapshot_id"],
                    character_id=sdata["character_id"],
                    timestamp=sdata["timestamp"],
                    data=sdata["data"],
                )
                self._snapshots[sid] = snap

            for cid, ids in data.get("snapshot_index", {}).items():
                self._snapshot_index[cid] = list(ids)

            for cid, tdata in data.get("reward_traces", {}).items():
                trace = RewardTrace(character_id=cid)
                trace.scores = list(tdata.get("scores", []))
                trace.timestamps = list(tdata.get("timestamps", []))
                self._reward_traces[cid] = trace

        return len(chars)

    # ── 상태 요약 ────────────────────────────────────────────────

    def status(self) -> Dict[str, Any]:
        """DB 상태 요약 dict."""
        with self._lock_v2:
            n_snaps = len(self._snapshots)
            n_rewards = len(self._reward_traces)
            n_conflicts = len(self._conflicts)
            n_unresolved = sum(1 for r in self._conflicts.values() if not r.resolved)
        with self._lock:
            n_chars = len(self._chars)
        return {
            "version": self.VERSION,
            "characters": n_chars,
            "snapshots": n_snaps,
            "reward_traces": n_rewards,
            "conflicts_total": n_conflicts,
            "conflicts_unresolved": n_unresolved,
        }
