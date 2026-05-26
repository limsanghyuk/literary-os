"""
RetrainingScheduler — SP-C.1 V634 (ADR-076)

F1 drift 기반 재학습 스케줄러.
- DRIFT_THRESHOLD: 현재 F1 - 기준 F1 의 절댓값이 이 값 이상일 때 재학습 트리거
- MIN_INTERVAL_DAYS: 마지막 재학습 이후 최소 경과 일수 (기본 7일)
- LOSDB JSONL 영속화 (append-only)
- LLM-0 원칙 완전 준수 (외부 LLM 호출 없음)
"""
from __future__ import annotations

import json
import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
DRIFT_THRESHOLD: float = 0.03       # F1 drift 감지 임계값
MIN_INTERVAL_DAYS: int = 7          # 재학습 최소 간격 (일)
_DEFAULT_STORE: str = "data/losdb/retraining_schedule.jsonl"
_MEMORY_SENTINEL: str = ":memory:"


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_iso(s: str) -> datetime:
    """ISO-8601 문자열 → timezone-aware datetime."""
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------
@dataclass
class ScheduleRecord:
    """단일 재학습 스케줄 이벤트."""
    record_id: str
    scheduled_at: str          # ISO-8601 UTC
    current_f1: float          # 측정 시점 F1
    baseline_f1: float         # 기준 F1
    drift: float               # current_f1 - baseline_f1 (부호 있음)
    reason: str                # 트리거 사유 설명
    note: str = ""             # 자유 메모

    # ---- 직렬화 ----
    def to_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "scheduled_at": self.scheduled_at,
            "current_f1": self.current_f1,
            "baseline_f1": self.baseline_f1,
            "drift": self.drift,
            "reason": self.reason,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "ScheduleRecord":
        return cls(
            record_id=d["record_id"],
            scheduled_at=d["scheduled_at"],
            current_f1=float(d["current_f1"]),
            baseline_f1=float(d["baseline_f1"]),
            drift=float(d["drift"]),
            reason=d["reason"],
            note=d.get("note", ""),
        )


# ---------------------------------------------------------------------------
# 스케줄러
# ---------------------------------------------------------------------------
class RetrainingScheduler:
    """
    F1 drift 기반 재학습 스케줄러.

    Parameters
    ----------
    store_path : str
        JSONL 파일 경로. `:memory:` 이면 메모리 전용 모드.
    drift_threshold : float
        F1 drift 감지 임계값 (기본 0.03).
    min_interval_days : int
        재학습 최소 간격 일수 (기본 7).
    """

    def __init__(
        self,
        store_path: str = _DEFAULT_STORE,
        drift_threshold: float = DRIFT_THRESHOLD,
        min_interval_days: int = MIN_INTERVAL_DAYS,
    ) -> None:
        if not (0.0 < drift_threshold <= 1.0):
            raise ValueError(
                f"drift_threshold 는 (0, 1] 범위여야 합니다: {drift_threshold}"
            )
        if min_interval_days < 0:
            raise ValueError(
                f"min_interval_days 는 0 이상이어야 합니다: {min_interval_days}"
            )

        self._store_path = store_path
        self._drift_threshold = drift_threshold
        self._min_interval_days = min_interval_days
        self._records: List[ScheduleRecord] = []
        self._memory_mode = (store_path == _MEMORY_SENTINEL)

        if not self._memory_mode:
            self._load_from_file()

    # ------------------------------------------------------------------
    # 내부 I/O
    # ------------------------------------------------------------------
    def _load_from_file(self) -> None:
        p = Path(self._store_path)
        if not p.exists():
            return
        with p.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    self._records.append(ScheduleRecord.from_dict(json.loads(line)))

    def _append_to_file(self, record: ScheduleRecord) -> None:
        p = Path(self._store_path)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    # ------------------------------------------------------------------
    # 핵심 메서드
    # ------------------------------------------------------------------
    def should_retrain(
        self,
        current_f1: float,
        baseline_f1: float,
        now: Optional[datetime] = None,
    ) -> Tuple[bool, str]:
        """
        재학습이 필요한지 판단한다.

        Returns
        -------
        (bool, str)
            (재학습 필요 여부, 사유 문자열)
        """
        drift = current_f1 - baseline_f1

        # 1) drift 체크
        if abs(drift) < self._drift_threshold:
            return False, (
                f"drift {abs(drift):.4f} < threshold {self._drift_threshold} — 재학습 불필요"
            )

        # 2) 최소 간격 체크
        last = self.last_scheduled()
        if last is not None:
            reference = now if now is not None else datetime.now(timezone.utc)
            elapsed = reference - _parse_iso(last.scheduled_at)
            if elapsed < timedelta(days=self._min_interval_days):
                remaining = timedelta(days=self._min_interval_days) - elapsed
                return False, (
                    f"drift {abs(drift):.4f} ≥ threshold 이지만 "
                    f"최소 간격 미충족 — 잔여 {remaining.days}일 {remaining.seconds//3600}시간"
                )

        direction = "하락" if drift < 0 else "상승"
        return True, (
            f"F1 drift {drift:+.4f} ({direction}) ≥ threshold {self._drift_threshold} — 재학습 필요"
        )

    def schedule(
        self,
        current_f1: float,
        baseline_f1: float,
        note: str = "",
        now: Optional[datetime] = None,
        force: bool = False,
    ) -> ScheduleRecord:
        """
        재학습 스케줄을 등록한다.

        Parameters
        ----------
        current_f1 : float
            현재 측정 F1 점수.
        baseline_f1 : float
            비교 기준 F1 점수.
        note : str
            자유 메모.
        now : datetime, optional
            현재 시각 (테스트용 주입). None 이면 UTC now.
        force : bool
            True 이면 drift/interval 조건을 무시하고 강제 스케줄.

        Returns
        -------
        ScheduleRecord
            생성된 스케줄 레코드.

        Raises
        ------
        RuntimeError
            force=False 이고 should_retrain()이 False 인 경우.
        """
        ts = now if now is not None else datetime.now(timezone.utc)
        drift = current_f1 - baseline_f1

        if not force:
            ok, reason = self.should_retrain(current_f1, baseline_f1, now=ts)
            if not ok:
                raise RuntimeError(f"재학습 스케줄 거부: {reason}")
        else:
            reason = f"강제 스케줄 (force=True), drift={drift:+.4f}"

        record = ScheduleRecord(
            record_id=str(uuid.uuid4()),
            scheduled_at=ts.isoformat(),
            current_f1=current_f1,
            baseline_f1=baseline_f1,
            drift=drift,
            reason=reason,
            note=note,
        )

        self._records.append(record)
        if not self._memory_mode:
            self._append_to_file(record)

        return record

    # ------------------------------------------------------------------
    # 조회 메서드
    # ------------------------------------------------------------------
    def history(self) -> List[ScheduleRecord]:
        """전체 스케줄 이력 (오래된 순)."""
        return list(self._records)

    def last_scheduled(self) -> Optional[ScheduleRecord]:
        """가장 최근 스케줄 레코드. 없으면 None."""
        if not self._records:
            return None
        return self._records[-1]

    def count(self) -> int:
        """총 스케줄 횟수."""
        return len(self._records)

    def clear(self) -> None:
        """전체 이력 삭제 (메모리 + 파일)."""
        self._records.clear()
        if not self._memory_mode:
            p = Path(self._store_path)
            if p.exists():
                p.unlink()

    @property
    def drift_threshold(self) -> float:
        return self._drift_threshold

    @property
    def min_interval_days(self) -> int:
        return self._min_interval_days
