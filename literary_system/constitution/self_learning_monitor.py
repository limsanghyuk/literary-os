"""
self_learning_monitor.py — SelfLearningMonitor V636 (ADR-078)

SP-C.1 Self-Learning Loop 전체 파이프라인 상태 모니터.

모니터링 대상 컴포넌트:
  - MetaLearner      (V631): Bayesian Opt 가중치 탐색
  - WeightTracker    (V632): 가중치 이력 + 롤백
  - PatternLibraryV2 (V633): 패턴 압축/랭킹
  - RetrainingScheduler (V634): F1 drift 기반 재학습 스케줄
  - AutoPromotionGate   (V635): R≥0.78 + 롤백0 자동 승격

이상 감지 규칙:
  - ROLLBACK_SURGE  : WeightTracker 롤백 횟수 ≥ ROLLBACK_SURGE_THRESHOLD(3)
  - F1_EXTREME_DROP : RetrainingScheduler 최근 drift ≤ -F1_DROP_THRESHOLD(-0.10)
  - PATTERN_EMPTY   : PatternLibraryV2 패턴 수 = 0
  - GATE_FAIL_STREAK: AutoPromotionGate 연속 FAIL ≥ GATE_FAIL_STREAK_THRESHOLD(3)

LLM-0 원칙 완전 준수 (외부 LLM 호출 없음)
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# ─────────────────────────────────────────────
# 이상 감지 상수
# ─────────────────────────────────────────────
ROLLBACK_SURGE_THRESHOLD: int = 3      # 롤백 누적 ≥ 3 → ROLLBACK_SURGE
F1_DROP_THRESHOLD: float = 0.10        # drift ≤ -0.10 → F1_EXTREME_DROP
GATE_FAIL_STREAK_THRESHOLD: int = 3    # 연속 FAIL ≥ 3 → GATE_FAIL_STREAK

_DEFAULT_STORE = "data/losdb/self_learning_monitor.jsonl"
_MEMORY_SENTINEL = ":memory:"

# 알려진 SP-C.1 컴포넌트 이름
COMPONENT_NAMES = [
    "MetaLearner",
    "WeightTracker",
    "PatternLibraryV2",
    "RetrainingScheduler",
    "AutoPromotionGate",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


# ─────────────────────────────────────────────
# 데이터 클래스
# ─────────────────────────────────────────────
@dataclass
class ComponentStatus:
    """개별 컴포넌트 상태."""
    name: str
    healthy: bool
    details: Dict[str, Any] = field(default_factory=dict)
    checked_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "healthy": self.healthy,
            "details": self.details,
            "checked_at": self.checked_at,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ComponentStatus":
        return cls(
            name=d["name"],
            healthy=bool(d["healthy"]),
            details=d.get("details", {}),
            checked_at=d.get("checked_at", _now_iso()),
        )


@dataclass
class MonitorSnapshot:
    """단일 모니터링 스냅샷."""
    snapshot_id: str
    captured_at: str
    components: List[ComponentStatus]
    anomalies: List[str]        # 감지된 이상 징후 코드 목록
    healthy: bool               # 모든 컴포넌트 정상 AND 이상 없음
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "snapshot_id": self.snapshot_id,
            "captured_at": self.captured_at,
            "components": [c.to_dict() for c in self.components],
            "anomalies": self.anomalies,
            "healthy": self.healthy,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "MonitorSnapshot":
        return cls(
            snapshot_id=d["snapshot_id"],
            captured_at=d["captured_at"],
            components=[ComponentStatus.from_dict(c) for c in d.get("components", [])],
            anomalies=d.get("anomalies", []),
            healthy=bool(d["healthy"]),
            note=d.get("note", ""),
        )

    def summary(self) -> str:
        """한 줄 요약."""
        n_components = len(self.components)
        n_healthy = sum(1 for c in self.components if c.healthy)
        status = "HEALTHY" if self.healthy else "DEGRADED"
        anomaly_str = f", 이상: {self.anomalies}" if self.anomalies else ""
        return (
            f"[{status}] 컴포넌트 {n_healthy}/{n_components} 정상"
            f"{anomaly_str}"
        )


# ─────────────────────────────────────────────
# SelfLearningMonitor
# ─────────────────────────────────────────────
class SelfLearningMonitor:
    """
    SP-C.1 Self-Learning Loop 상태 모니터.

    Parameters
    ----------
    store_path : str
        JSONL 파일 경로. `:memory:` 이면 메모리 전용 모드.
    rollback_surge_threshold : int
        롤백 누적 수 이상 임계값 (기본 3).
    f1_drop_threshold : float
        F1 극단 하락 임계값 (기본 0.10 → drift ≤ -0.10).
    gate_fail_streak_threshold : int
        AutoPromotionGate 연속 FAIL 임계값 (기본 3).
    """

    def __init__(
        self,
        store_path: str = _DEFAULT_STORE,
        rollback_surge_threshold: int = ROLLBACK_SURGE_THRESHOLD,
        f1_drop_threshold: float = F1_DROP_THRESHOLD,
        gate_fail_streak_threshold: int = GATE_FAIL_STREAK_THRESHOLD,
    ) -> None:
        if rollback_surge_threshold < 1:
            raise ValueError(f"rollback_surge_threshold ≥ 1 필요: {rollback_surge_threshold}")
        if not (0.0 < f1_drop_threshold <= 1.0):
            raise ValueError(f"f1_drop_threshold (0,1] 범위 필요: {f1_drop_threshold}")
        if gate_fail_streak_threshold < 1:
            raise ValueError(f"gate_fail_streak_threshold ≥ 1 필요: {gate_fail_streak_threshold}")

        self._store_path = store_path
        self._rollback_surge_threshold = rollback_surge_threshold
        self._f1_drop_threshold = f1_drop_threshold
        self._gate_fail_streak_threshold = gate_fail_streak_threshold
        self._snapshots: List[MonitorSnapshot] = []
        self._memory_mode = (store_path == _MEMORY_SENTINEL)

        if not self._memory_mode:
            self._load_from_file()

    # ── I/O ──
    def _load_from_file(self) -> None:
        p = Path(self._store_path)
        if not p.exists():
            return
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self._snapshots.append(MonitorSnapshot.from_dict(json.loads(line)))

    def _append_to_file(self, snap: MonitorSnapshot) -> None:
        p = Path(self._store_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(snap.to_dict(), ensure_ascii=False) + "\n")

    # ── 이상 감지 ──
    def detect_anomalies(
        self,
        components: Sequence[ComponentStatus],
        rollback_count: int = 0,
        recent_drift: Optional[float] = None,
        gate_fail_streak: int = 0,
        pattern_count: int = -1,   # -1 = 미제공 (패턴 없음 감지 비활성)
    ) -> List[str]:
        """
        이상 징후를 감지한다.

        Parameters
        ----------
        components : Sequence[ComponentStatus]
            컴포넌트 상태 목록.
        rollback_count : int
            WeightTracker 누적 롤백 횟수.
        recent_drift : float, optional
            RetrainingScheduler 최근 F1 drift (부호 있음).
        gate_fail_streak : int
            AutoPromotionGate 연속 FAIL 횟수.
        pattern_count : int
            PatternLibraryV2 현재 패턴 수 (-1이면 체크 미수행).

        Returns
        -------
        List[str]: 감지된 이상 코드 목록
        """
        anomalies: List[str] = []

        # ROLLBACK_SURGE
        if rollback_count >= self._rollback_surge_threshold:
            anomalies.append(
                f"ROLLBACK_SURGE(count={rollback_count}"
                f"≥threshold={self._rollback_surge_threshold})"
            )

        # F1_EXTREME_DROP
        if recent_drift is not None and recent_drift <= -self._f1_drop_threshold:
            anomalies.append(
                f"F1_EXTREME_DROP(drift={recent_drift:.4f}"
                f"≤-{self._f1_drop_threshold})"
            )

        # PATTERN_EMPTY
        if pattern_count == 0:
            anomalies.append("PATTERN_EMPTY(PatternLibraryV2 패턴 0개)")

        # GATE_FAIL_STREAK
        if gate_fail_streak >= self._gate_fail_streak_threshold:
            anomalies.append(
                f"GATE_FAIL_STREAK(streak={gate_fail_streak}"
                f"≥threshold={self._gate_fail_streak_threshold})"
            )

        return anomalies

    # ── 핵심 메서드 ──
    def capture(
        self,
        components: Sequence[ComponentStatus],
        rollback_count: int = 0,
        recent_drift: Optional[float] = None,
        gate_fail_streak: int = 0,
        pattern_count: int = -1,
        note: str = "",
        now: Optional[datetime] = None,
    ) -> MonitorSnapshot:
        """
        모니터링 스냅샷을 캡처한다.

        Parameters
        ----------
        components : Sequence[ComponentStatus]
            컴포넌트 상태 목록.
        rollback_count, recent_drift, gate_fail_streak, pattern_count :
            이상 감지 입력 (detect_anomalies 참조).
        note : str
            자유 메모.
        now : datetime, optional
            캡처 시각 (테스트용 주입).

        Returns
        -------
        MonitorSnapshot
        """
        ts = now if now is not None else datetime.now(timezone.utc)
        anomalies = self.detect_anomalies(
            components=components,
            rollback_count=rollback_count,
            recent_drift=recent_drift,
            gate_fail_streak=gate_fail_streak,
            pattern_count=pattern_count,
        )
        all_healthy = all(c.healthy for c in components) and len(anomalies) == 0

        snap = MonitorSnapshot(
            snapshot_id=str(uuid.uuid4()),
            captured_at=ts.isoformat(),
            components=list(components),
            anomalies=anomalies,
            healthy=all_healthy,
            note=note,
        )
        self._snapshots.append(snap)
        if not self._memory_mode:
            self._append_to_file(snap)

        return snap

    # ── 조회 ──
    def history(self) -> List[MonitorSnapshot]:
        """전체 스냅샷 이력 (오래된 순)."""
        return list(self._snapshots)

    def last_snapshot(self) -> Optional[MonitorSnapshot]:
        """가장 최근 스냅샷. 없으면 None."""
        if not self._snapshots:
            return None
        return self._snapshots[-1]

    def count(self) -> int:
        """총 스냅샷 수."""
        return len(self._snapshots)

    def unhealthy_snapshots(self) -> List[MonitorSnapshot]:
        """healthy=False 인 스냅샷 목록."""
        return [s for s in self._snapshots if not s.healthy]

    def clear(self) -> None:
        """전체 이력 삭제."""
        self._snapshots.clear()
        if not self._memory_mode:
            p = Path(self._store_path)
            if p.exists():
                p.unlink()

    @property
    def rollback_surge_threshold(self) -> int:
        return self._rollback_surge_threshold

    @property
    def f1_drop_threshold(self) -> float:
        return self._f1_drop_threshold

    @property
    def gate_fail_streak_threshold(self) -> int:
        return self._gate_fail_streak_threshold
