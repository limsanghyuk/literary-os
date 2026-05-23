"""
AdaptiveThrottler v1.0 — SLO 기반 동적 처리량 조절기 (V618, SP-B.4)

PerformanceSLOGate + LongRunMonitor 측정값을 읽어 실시간으로
최대 동시성(max_concurrency)을 자동 조정한다.

설계 원칙
----------
- **반응형 조절**: P95 ≥ warn_threshold_ms 이면 concurrency 를 step 만큼 줄인다.
- **점진 회복**: P95 < recover_threshold_ms 이면 step 만큼 늘린다(max_concurrency 상한).
- **메모리 안전망**: 메모리 사용량 > memory_budget_mb 이면 즉시 1로 줄인다(비상 제동).
- **슬라이딩 윈도우**: 최근 window_size 샘플의 이동 평균 P95를 기준으로 판단한다.
- **순수 stdlib**: threading.Semaphore 만 사용, 외부 의존성 없음.
"""
from __future__ import annotations

import logging
import threading
import time
from collections import deque
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Callable, Deque, Iterator, List, Optional

_log = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# 설정 dataclass
# ---------------------------------------------------------------------------

@dataclass
class ThrottleConfig:
    """AdaptiveThrottler 설정."""

    initial_concurrency: int = 4
    """초기 최대 동시성."""

    min_concurrency: int = 1
    """하한: 동시성이 이 값 아래로 내려가지 않는다."""

    max_concurrency: int = 16
    """상한: 동시성이 이 값을 초과하지 않는다."""

    step: int = 1
    """한 번에 조정하는 동시성 단위."""

    warn_threshold_ms: float = 1200.0
    """P95(ms) 이 값 이상이면 동시성을 줄인다."""

    recover_threshold_ms: float = 800.0
    """P95(ms) 이 값 미만이면 동시성을 늘린다."""

    memory_budget_mb: Optional[float] = None
    """메모리 예산(MB). 초과 시 비상 제동(concurrency=1)."""

    window_size: int = 20
    """이동 평균 P95 계산에 사용할 샘플 수."""

    def __post_init__(self) -> None:
        if self.min_concurrency < 1:
            raise ValueError("min_concurrency must be >= 1")
        if self.max_concurrency < self.min_concurrency:
            raise ValueError("max_concurrency must be >= min_concurrency")
        if self.initial_concurrency < self.min_concurrency:
            self.initial_concurrency = self.min_concurrency
        if self.initial_concurrency > self.max_concurrency:
            self.initial_concurrency = self.max_concurrency
        if self.warn_threshold_ms <= self.recover_threshold_ms:
            raise ValueError("warn_threshold_ms must be > recover_threshold_ms")


# ---------------------------------------------------------------------------
# 조정 이벤트 (감사 로그용)
# ---------------------------------------------------------------------------

@dataclass
class ThrottleEvent:
    """동시성 조정 단일 이벤트."""

    timestamp: float
    """이벤트 발생 시각 (time.monotonic)."""

    action: str
    """'reduce' | 'increase' | 'emergency' | 'noop'."""

    previous: int
    """조정 전 동시성."""

    current: int
    """조정 후 동시성."""

    p95_ms: float
    """판단 기준 P95(ms)."""

    memory_mb: Optional[float]
    """판단 시점 메모리 사용량(MB). 미제공 시 None."""

    reason: str
    """조정 이유 요약 문자열."""

    def to_dict(self) -> dict:
        return {
            "timestamp": self.timestamp,
            "action": self.action,
            "previous": self.previous,
            "current": self.current,
            "p95_ms": self.p95_ms,
            "memory_mb": self.memory_mb,
            "reason": self.reason,
        }


# ---------------------------------------------------------------------------
# 조정 보고서
# ---------------------------------------------------------------------------

@dataclass
class ThrottleReport:
    """AdaptiveThrottler 전체 실행 보고서."""

    config: ThrottleConfig
    events: List[ThrottleEvent] = field(default_factory=list)
    total_calls: int = 0
    total_latency_ms: float = 0.0
    peak_concurrency: int = 0
    min_concurrency_reached: int = 0

    @property
    def avg_latency_ms(self) -> float:
        return self.total_latency_ms / self.total_calls if self.total_calls else 0.0

    @property
    def reduce_count(self) -> int:
        return sum(1 for e in self.events if e.action in ("reduce", "emergency"))

    @property
    def increase_count(self) -> int:
        return sum(1 for e in self.events if e.action == "increase")

    def to_dict(self) -> dict:
        return {
            "total_calls": self.total_calls,
            "avg_latency_ms": round(self.avg_latency_ms, 2),
            "peak_concurrency": self.peak_concurrency,
            "min_concurrency_reached": self.min_concurrency_reached,
            "reduce_count": self.reduce_count,
            "increase_count": self.increase_count,
            "events": [e.to_dict() for e in self.events],
        }


# ---------------------------------------------------------------------------
# 메인 클래스
# ---------------------------------------------------------------------------

class AdaptiveThrottler:
    """
    SLO 기반 동적 처리량 조절기.

    사용 예::

        cfg = ThrottleConfig(initial_concurrency=4, warn_threshold_ms=1200)
        throttler = AdaptiveThrottler(cfg)

        def memory_sampler():
            import tracemalloc
            cur, _ = tracemalloc.get_traced_memory()
            return cur / 1024 / 1024

        with throttler.slot():           # Semaphore 획득
            result = my_scene_fn()
            throttler.record(latency_ms, memory_sampler())

        report = throttler.get_report()
    """

    def __init__(self, config: Optional[ThrottleConfig] = None) -> None:
        self.config: ThrottleConfig = config or ThrottleConfig()
        self._concurrency: int = self.config.initial_concurrency
        self._semaphore: threading.Semaphore = threading.Semaphore(self._concurrency)
        self._lock: threading.Lock = threading.Lock()
        self._window: Deque[float] = deque(maxlen=self.config.window_size)
        self._report: ThrottleReport = ThrottleReport(
            config=self.config,
            peak_concurrency=self._concurrency,
            min_concurrency_reached=self._concurrency,
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def current_concurrency(self) -> int:
        return self._concurrency

    @contextmanager
    def slot(self) -> Iterator[None]:
        """Semaphore 기반 동시성 슬롯 컨텍스트 매니저.
        
        BUG-C3-4 수정 (2026-05-23): Semaphore를 로컬 변수로 고정하여
        동시성 조정 중 _set_concurrency()가 새 Semaphore로 교체해도
        acquire/release가 동일 인스턴스를 사용하도록 보장한다.
        """
        sem = self._semaphore  # 현재 semaphore 로컬 참조 고정
        sem.acquire()
        try:
            yield
        finally:
            sem.release()

    def record(
        self,
        latency_ms: float,
        memory_mb: Optional[float] = None,
    ) -> Optional[ThrottleEvent]:
        """
        호출 결과를 기록하고 필요 시 동시성을 조정한다.

        Parameters
        ----------
        latency_ms:
            방금 완료된 호출의 지연(ms).
        memory_mb:
            현재 메모리 사용량(MB). None 이면 메모리 기준 판단 스킵.

        Returns
        -------
        ThrottleEvent | None
            동시성 조정이 발생한 경우 이벤트 객체, 아니면 None.
        """
        with self._lock:
            self._window.append(latency_ms)
            self._report.total_calls += 1
            self._report.total_latency_ms += latency_ms

            p95 = self._p95()
            event = self._maybe_adjust(p95, memory_mb)

            if event:
                self._report.events.append(event)
                if self._concurrency > self._report.peak_concurrency:
                    self._report.peak_concurrency = self._concurrency
                if self._concurrency < self._report.min_concurrency_reached:
                    self._report.min_concurrency_reached = self._concurrency

            return event

    def get_report(self) -> ThrottleReport:
        """현재까지의 ThrottleReport를 반환한다."""
        with self._lock:
            # 피크/최솟값 최종 갱신
            if self._concurrency > self._report.peak_concurrency:
                self._report.peak_concurrency = self._concurrency
            if self._concurrency < self._report.min_concurrency_reached:
                self._report.min_concurrency_reached = self._concurrency
            return self._report

    def reset(self) -> None:
        """상태를 초기값으로 리셋한다."""
        with self._lock:
            self._concurrency = self.config.initial_concurrency
            self._semaphore = threading.Semaphore(self._concurrency)
            self._window.clear()
            self._report = ThrottleReport(
                config=self.config,
                peak_concurrency=self._concurrency,
                min_concurrency_reached=self._concurrency,
            )

    # ------------------------------------------------------------------
    # 편의 클래스메서드
    # ------------------------------------------------------------------

    @classmethod
    def quick_throttle(
        cls,
        fn: Callable[[], float],
        calls: int = 30,
        initial_concurrency: int = 4,
        warn_threshold_ms: float = 1200.0,
        memory_sampler: Optional[Callable[[], float]] = None,
    ) -> ThrottleReport:
        """
        단순 벤치마크 실행 + 자동 조절을 한 번에 수행한다.

        fn() 은 ms 단위 지연 값을 반환해야 한다.
        """
        cfg = ThrottleConfig(
            initial_concurrency=initial_concurrency,
            warn_threshold_ms=warn_threshold_ms,
        )
        throttler = cls(cfg)
        for _ in range(calls):
            with throttler.slot():
                latency = fn()
                mem = memory_sampler() if memory_sampler else None
                throttler.record(latency, mem)
        return throttler.get_report()

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _p95(self) -> float:
        """슬라이딩 윈도우 P95 계산 (선형 보간)."""
        if not self._window:
            return 0.0
        data = sorted(self._window)
        n = len(data)
        if n == 1:
            return data[0]
        idx = 0.95 * (n - 1)
        lo, hi = int(idx), min(int(idx) + 1, n - 1)
        frac = idx - lo
        return data[lo] + frac * (data[hi] - data[lo])

    def _maybe_adjust(
        self, p95: float, memory_mb: Optional[float]
    ) -> Optional[ThrottleEvent]:
        """p95/memory 기준으로 동시성을 조정하고 이벤트를 반환한다."""
        cfg = self.config
        prev = self._concurrency

        # 1) 비상 제동: 메모리 예산 초과
        if (
            memory_mb is not None
            and cfg.memory_budget_mb is not None
            and memory_mb > cfg.memory_budget_mb
        ):
            new_c = cfg.min_concurrency
            if new_c != prev:
                self._set_concurrency(new_c)
                reason = (
                    f"메모리 {memory_mb:.1f}MB > 예산 {cfg.memory_budget_mb:.1f}MB"
                )
                _log.warning("AdaptiveThrottler 비상 제동: %s", reason)
                return ThrottleEvent(
                    timestamp=time.monotonic(),
                    action="emergency",
                    previous=prev,
                    current=new_c,
                    p95_ms=p95,
                    memory_mb=memory_mb,
                    reason=reason,
                )
            return None

        # 2) 감속: P95 경고 임계값 이상
        if p95 >= cfg.warn_threshold_ms:
            new_c = max(cfg.min_concurrency, prev - cfg.step)
            if new_c != prev:
                self._set_concurrency(new_c)
                reason = f"P95 {p95:.1f}ms ≥ warn {cfg.warn_threshold_ms:.1f}ms"
                _log.info("AdaptiveThrottler 감속: %s → concurrency %d", reason, new_c)
                return ThrottleEvent(
                    timestamp=time.monotonic(),
                    action="reduce",
                    previous=prev,
                    current=new_c,
                    p95_ms=p95,
                    memory_mb=memory_mb,
                    reason=reason,
                )
            return None

        # 3) 가속: P95 회복 임계값 미만
        if p95 < cfg.recover_threshold_ms:
            new_c = min(cfg.max_concurrency, prev + cfg.step)
            if new_c != prev:
                self._set_concurrency(new_c)
                reason = (
                    f"P95 {p95:.1f}ms < recover {cfg.recover_threshold_ms:.1f}ms"
                )
                _log.info("AdaptiveThrottler 가속: %s → concurrency %d", reason, new_c)
                return ThrottleEvent(
                    timestamp=time.monotonic(),
                    action="increase",
                    previous=prev,
                    current=new_c,
                    p95_ms=p95,
                    memory_mb=memory_mb,
                    reason=reason,
                )

        return None

    def _set_concurrency(self, new_c: int) -> None:
        """Semaphore를 재구성하여 동시성을 변경한다."""
        diff = new_c - self._concurrency
        self._concurrency = new_c
        if diff > 0:
            for _ in range(diff):
                self._semaphore.release()
        else:
            # 슬롯을 줄일 때는 Semaphore 를 재생성한다
            # (이미 사용 중인 슬롯은 자연 반납 후 새 Semaphore 적용)
            self._semaphore = threading.Semaphore(new_c)
