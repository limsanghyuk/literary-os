"""
MemoryLeakDetector v1.0 — Literary OS SP-B.4 (V616)

tracemalloc 기반 메모리 누수 탐지 유틸리티.
baseline 스냅샷 → 실행 → 재스냅샷 → diff 분석 워크플로우.

주요 클래스:
  - MemorySnapshot : tracemalloc 스냅샷 래퍼
  - LeakReport     : 누수 분석 결과 (delta_bytes, is_leaking, top_allocators)
  - MemoryLeakDetector : 공개 API (start/baseline/capture/check/report)
"""

from __future__ import annotations

import logging
import tracemalloc
from dataclasses import dataclass, field
from typing import List, Optional, Tuple

__all__ = [
    "MemorySnapshot",
    "LeakReport",
    "MemoryLeakDetector",
]

_log = logging.getLogger(__name__)

# 기본 누수 임계값: 10 MB
DEFAULT_LEAK_THRESHOLD_BYTES: int = 10 * 1024 * 1024
# tracemalloc 스냅샷 상위 N개 할당자 리포트
DEFAULT_TOP_N: int = 10


# ─────────────────────────────────────────────────────────────────────────────
# 데이터 클래스
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class AllocatorEntry:
    """단일 할당 위치 정보."""
    filename: str
    lineno: int
    size_bytes: int

    def to_dict(self) -> dict:
        return {
            "filename": self.filename,
            "lineno": self.lineno,
            "size_bytes": self.size_bytes,
        }


@dataclass
class MemorySnapshot:
    """tracemalloc 스냅샷 래퍼."""
    _snapshot: object  # tracemalloc.Snapshot
    total_bytes: int = 0

    @classmethod
    def take(cls) -> "MemorySnapshot":
        """현재 시점 메모리 스냅샷을 캡처한다."""
        if not tracemalloc.is_tracing():
            tracemalloc.start()
        snap = tracemalloc.take_snapshot()
        stats = snap.statistics("lineno")
        total = sum(s.size for s in stats)
        obj = cls(_snapshot=snap, total_bytes=total)
        return obj

    def top_allocators(self, n: int = DEFAULT_TOP_N) -> List[AllocatorEntry]:
        """상위 N개 할당 위치를 반환한다.
        
        BUG-C3-1 수정 (2026-05-23): _snapshot=None 시 빈 리스트 반환
        (MemorySnapshot(_snapshot=None)으로 생성된 인스턴스 호출 방어).
        """
        if self._snapshot is None:
            return []
        stats = self._snapshot.statistics("lineno")[:n]
        result = []
        for s in stats:
            frame = s.traceback[0] if s.traceback else None
            filename = frame.filename if frame else "<unknown>"
            lineno = frame.lineno if frame else 0
            result.append(AllocatorEntry(
                filename=filename,
                lineno=lineno,
                size_bytes=s.size,
            ))
        return result


@dataclass
class LeakReport:
    """메모리 누수 분석 결과."""
    baseline_bytes: int
    current_bytes: int
    delta_bytes: int
    threshold_bytes: int
    is_leaking: bool
    top_allocators: List[AllocatorEntry] = field(default_factory=list)

    @property
    def delta_mb(self) -> float:
        return self.delta_bytes / (1024 * 1024)

    @property
    def threshold_mb(self) -> float:
        return self.threshold_bytes / (1024 * 1024)

    def to_dict(self) -> dict:
        return {
            "baseline_bytes": self.baseline_bytes,
            "current_bytes": self.current_bytes,
            "delta_bytes": self.delta_bytes,
            "delta_mb": round(self.delta_mb, 3),
            "threshold_bytes": self.threshold_bytes,
            "threshold_mb": round(self.threshold_mb, 3),
            "is_leaking": self.is_leaking,
            "top_allocators": [a.to_dict() for a in self.top_allocators],
        }


# ─────────────────────────────────────────────────────────────────────────────
# MemoryLeakDetector
# ─────────────────────────────────────────────────────────────────────────────

class MemoryLeakDetector:
    """
    tracemalloc 기반 메모리 누수 탐지기.

    사용 예:
        detector = MemoryLeakDetector(threshold_mb=10.0)
        detector.start()
        baseline = detector.baseline()
        # ... 테스트 대상 코드 실행 ...
        report = detector.check(baseline)
        if report.is_leaking:
            raise RuntimeError(f"메모리 누수 감지: {report.delta_mb:.1f} MB")
        detector.stop()
    """

    def __init__(
        self,
        threshold_mb: float = 10.0,
        top_n: int = DEFAULT_TOP_N,
    ) -> None:
        self.threshold_bytes: int = int(threshold_mb * 1024 * 1024)
        self.top_n: int = top_n
        self._baseline_snapshot: Optional[MemorySnapshot] = None
        self._tracing: bool = False

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        """tracemalloc 추적을 시작한다 (이미 시작된 경우 무시)."""
        if not tracemalloc.is_tracing():
            tracemalloc.start()
            self._tracing = True
            _log.debug("tracemalloc 추적 시작")
        else:
            _log.debug("tracemalloc 이미 활성 — 기존 세션 재사용")

    def stop(self) -> None:
        """tracemalloc 추적을 중지한다 (자신이 시작한 경우에만)."""
        if self._tracing and tracemalloc.is_tracing():
            tracemalloc.stop()
            self._tracing = False
            _log.debug("tracemalloc 추적 중지")

    def baseline(self) -> MemorySnapshot:
        """현재 시점을 베이스라인으로 스냅샷한다."""
        self.start()
        snap = MemorySnapshot.take()
        self._baseline_snapshot = snap
        _log.debug("베이스라인 스냅샷: %.2f MB", snap.total_bytes / 1024 / 1024)
        return snap

    def capture(self) -> MemorySnapshot:
        """현재 시점 스냅샷을 캡처한다."""
        self.start()
        snap = MemorySnapshot.take()
        _log.debug("현재 스냅샷: %.2f MB", snap.total_bytes / 1024 / 1024)
        return snap

    def diff(
        self,
        baseline: MemorySnapshot,
        current: MemorySnapshot,
    ) -> LeakReport:
        """두 스냅샷을 비교해 LeakReport를 생성한다."""
        delta = current.total_bytes - baseline.total_bytes
        is_leaking = delta > self.threshold_bytes
        top = current.top_allocators(self.top_n)
        report = LeakReport(
            baseline_bytes=baseline.total_bytes,
            current_bytes=current.total_bytes,
            delta_bytes=delta,
            threshold_bytes=self.threshold_bytes,
            is_leaking=is_leaking,
            top_allocators=top,
        )
        level = logging.WARNING if is_leaking else logging.DEBUG
        _log.log(level,
                 "메모리 diff: Δ%.2f MB (임계 %.0f MB) — leaking=%s",
                 report.delta_mb, report.threshold_mb, is_leaking)
        return report

    def check(self, baseline: Optional[MemorySnapshot] = None) -> LeakReport:
        """
        현재 메모리 상태를 baseline과 비교해 LeakReport를 반환한다.
        baseline 미지정 시 self._baseline_snapshot 사용.
        """
        bl = baseline or self._baseline_snapshot
        if bl is None:
            bl = MemorySnapshot(_snapshot=None, total_bytes=0)
        current = self.capture()
        return self.diff(bl, current)

    def reset(self) -> None:
        """베이스라인을 현재 상태로 갱신한다."""
        self._baseline_snapshot = self.baseline()

    # ── 컨텍스트 매니저 지원 ─────────────────────────────────────────────────

    def __enter__(self) -> "MemoryLeakDetector":
        self.start()
        self._baseline_snapshot = self.baseline()
        return self

    def __exit__(self, *_: object) -> None:
        self.stop()
