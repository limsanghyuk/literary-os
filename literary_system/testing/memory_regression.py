"""
memory_regression.py — V624 메모리 회귀 검증기 (ADR-091).

연속적인 실행 사이클에서 메모리 사용량이 점진적으로 증가하는
회귀(leak)를 감지한다.

설계 원칙
----------
- LLM-0: 외부 LLM 호출 없음.
- N회 연속 실행 후 선형 회귀로 메모리 증가 추세를 측정한다.
- 임계값(REGRESSION_SLOPE_MB_PER_RUN) 초과 시 FAIL 판정.
"""
from __future__ import annotations

import gc
import logging
import tracemalloc
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 상수
# ---------------------------------------------------------------------------
DEFAULT_RUN_COUNT: int = 10           # 기본 연속 실행 횟수
REGRESSION_SLOPE_MB_PER_RUN: float = 5.0   # 회귀 기울기 허용 한계 (MB/run)
WARN_SLOPE_MB_PER_RUN: float = 2.0         # 경고 임계값
MAX_TOTAL_GROWTH_MB: float = 30.0          # 전체 메모리 증가 허용 한계 (MB)


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class MemRegSnapshot:
    """단일 실행 사이클의 메모리 스냅샷."""

    run_index: int
    memory_mb: float
    delta_mb: float           # 직전 run 대비 증가량

    def to_dict(self) -> dict:
        return {
            "run_index": self.run_index,
            "memory_mb": round(self.memory_mb, 3),
            "delta_mb": round(self.delta_mb, 3),
        }


@dataclass
class RegressionResult:
    """메모리 회귀 검사 결과."""

    run_count: int
    snapshots: List[MemRegSnapshot] = field(default_factory=list)
    slope_mb_per_run: float = 0.0      # 선형 회귀 기울기
    total_growth_mb: float = 0.0       # 첫 run 대비 마지막 run 메모리 증가
    passed: bool = True
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def summary(self) -> str:
        status = "PASS" if self.passed else "FAIL"
        return (
            f"MemoryRegression {status} | "
            f"runs={self.run_count} | "
            f"slope={self.slope_mb_per_run:.3f} MB/run | "
            f"total_growth={self.total_growth_mb:.1f}MB"
        )

    def to_dict(self) -> dict:
        return {
            "run_count": self.run_count,
            "slope_mb_per_run": round(self.slope_mb_per_run, 4),
            "total_growth_mb": round(self.total_growth_mb, 3),
            "passed": self.passed,
            "warnings": self.warnings,
            "errors": self.errors,
            "snapshots": [s.to_dict() for s in self.snapshots],
            "summary": self.summary(),
        }


# ---------------------------------------------------------------------------
# MemoryRegressionChecker
# ---------------------------------------------------------------------------

class MemoryRegressionChecker:
    """
    연속 실행 메모리 회귀 검증기 (V624 ADR-091).

    Parameters
    ----------
    run_count:
        연속 실행 횟수 (기본 10).
    workload:
        각 실행에서 호출할 워크로드 함수 (run_index: int) -> None.
        None이면 기본 워크로드(핵심 컴포넌트 순환)를 사용한다.
    """

    VERSION = "1.0.0"

    def __init__(
        self,
        run_count: int = DEFAULT_RUN_COUNT,
        workload: Optional[Callable[[int], None]] = None,
    ) -> None:
        self._run_count = run_count
        self._workload = workload or self._default_workload
        self._last_result: Optional[RegressionResult] = None

    # ── 공개 API ────────────────────────────────────────────────────────────

    def check(self) -> RegressionResult:
        """
        N회 연속 실행 후 메모리 회귀를 검사한다.
        결과를 RegressionResult로 반환한다.
        """
        _log.info("MemoryRegressionChecker 시작 — %d runs", self._run_count)

        tracemalloc.start()
        gc.collect()
        snapshots: List[MemRegSnapshot] = []
        prev_mem = self._mem_mb()

        for i in range(1, self._run_count + 1):
            try:
                self._workload(i)
            except Exception as exc:  # noqa: BLE001
                _log.warning("워크로드 run=%d 예외: %s", i, exc)

            gc.collect()
            cur_mem = self._mem_mb()
            delta = cur_mem - prev_mem
            snapshots.append(MemRegSnapshot(run_index=i, memory_mb=cur_mem, delta_mb=delta))
            prev_mem = cur_mem

        tracemalloc.stop()

        result = self._analyze(snapshots)
        self._last_result = result
        _log.info("MemoryRegressionChecker %s", result.summary())
        return result

    def last_result(self) -> Optional[RegressionResult]:
        return self._last_result

    def is_stable(self) -> bool:
        """직전 check() 결과가 안정적인지 여부."""
        return self._last_result is not None and self._last_result.passed

    # ── 분석 ────────────────────────────────────────────────────────────────

    def _analyze(self, snapshots: List[MemRegSnapshot]) -> RegressionResult:
        """선형 회귀 기울기 + 총 증가량으로 회귀 판정."""
        warnings: List[str] = []
        errors: List[str] = []

        if not snapshots:
            return RegressionResult(run_count=self._run_count, passed=False,
                                    errors=["스냅샷 없음"])

        total_growth = snapshots[-1].memory_mb - snapshots[0].memory_mb
        slope = self._linear_slope([s.memory_mb for s in snapshots])

        # 임계값 판정
        if slope > REGRESSION_SLOPE_MB_PER_RUN:
            errors.append(
                f"메모리 회귀 기울기 {slope:.3f} MB/run > 허용 {REGRESSION_SLOPE_MB_PER_RUN} MB/run"
            )
        elif slope > WARN_SLOPE_MB_PER_RUN:
            warnings.append(
                f"메모리 증가 경고 기울기 {slope:.3f} MB/run > {WARN_SLOPE_MB_PER_RUN} MB/run"
            )

        if total_growth > MAX_TOTAL_GROWTH_MB:
            errors.append(
                f"총 메모리 증가 {total_growth:.1f}MB > 허용 {MAX_TOTAL_GROWTH_MB}MB"
            )

        return RegressionResult(
            run_count=self._run_count,
            snapshots=snapshots,
            slope_mb_per_run=slope,
            total_growth_mb=total_growth,
            passed=not errors,
            warnings=warnings,
            errors=errors,
        )

    @staticmethod
    def _linear_slope(values: List[float]) -> float:
        """최소제곱법으로 선형 회귀 기울기를 계산한다."""
        n = len(values)
        if n < 2:
            return 0.0
        xs = list(range(n))
        x_mean = sum(xs) / n
        y_mean = sum(values) / n
        numerator = sum((x - x_mean) * (y - y_mean) for x, y in zip(xs, values))
        denominator = sum((x - x_mean) ** 2 for x in xs)
        return numerator / denominator if denominator != 0 else 0.0

    # ── 기본 워크로드 ────────────────────────────────────────────────────────

    @staticmethod
    def _default_workload(run_index: int) -> None:
        """기본 워크로드: 핵심 컴포넌트를 한 사이클 실행."""
        # MultiWorkCIMV2
        from literary_system.multiwork.multi_work_cim_v2 import MultiWorkCIMV2
        cim = MultiWorkCIMV2()
        cim.init_project(f"mr-proj-{run_index}")
        cim.record_v2(f"mr-proj-{run_index}", "char_a", "char_b", reward=0.75)

        # SharedCharacterDBV2
        from literary_system.multiwork.shared_character_db_v2 import SharedCharacterDBV2
        db = SharedCharacterDBV2()
        db.add_character(f"mr-char-{run_index}", name=f"캐릭터{run_index}", role="lead")

        # RewardModelV2 (경량 호출)
        from literary_system.rlhf.reward_model import RewardModelV2
        m = RewardModelV2()
        m.compute(f"run {run_index} 테스트 텍스트")

        # 명시적 GC 유도
        gc.collect()

    @staticmethod
    def _mem_mb() -> float:
        """tracemalloc 기반 메모리 측정 (MB)."""
        if tracemalloc.is_tracing():
            cur, _ = tracemalloc.get_traced_memory()
            return cur / (1024 * 1024)
        try:
            import psutil, os
            proc = psutil.Process(os.getpid())
            return proc.memory_info().rss / (1024 * 1024)
        except ImportError:
            return 0.0
