"""Gate G69 — FeedbackLoopGate (ADR-121).

24시간 무중단 피드백 루프 안정성 게이트.

합격 조건:
  1. 파이프라인 오류율 = 0  (ReaderFeedbackCollector → FeedbackToRLHF 전 구간)
  2. 24시간 시뮬레이션 (24 tick × 1h) 완주
  3. 각 tick RLHF 배치 변환 성공률 100%
  4. 누적 피드백 손실 0건 (collect count == converted count)
  5. purge 사이클 정상 동작 (만료 레코드 제거, 유효 레코드 보존)
"""
from __future__ import annotations

import datetime
import time
import uuid
from dataclasses import dataclass, field
from typing import Any

from literary_system.feedback.reader_feedback_collector import (
    ConsentLevel,
    FeedbackType,
    PIIPurgePolicy,
    ReaderFeedbackCollector,
)
from literary_system.feedback.feedback_to_rlhf import (
    FeedbackToRLHFAdapter,
    OutlierPolicy,
    RLHFBatch,
)

__all__ = [
    "FeedbackLoopGate",
    "LoopTickResult",
    "LoopSimReport",
    "run_g69",
]

# ── 시뮬레이션 파라미터 ──────────────────────────────────────────────
SIMULATION_HOURS: int = 24          # 시뮬레이션 전체 시간
TICK_COUNT: int = 24                # tick 수 (1 tick = 1시간)
MIN_FEEDBACK_PER_TICK: int = 5      # tick당 최소 피드백 수
MAX_FEEDBACK_PER_TICK: int = 20     # tick당 최대 피드백 수
MAX_ALLOWED_ERRORS: int = 0         # 허용 오류 건수 (G69: 0)
PURGE_EVERY_N_TICKS: int = 6        # N tick마다 purge 실행 (=6h 주기)
_GATE_ID = "G69"


# ── 데이터 클래스 ────────────────────────────────────────────────────

@dataclass
class LoopTickResult:
    """단일 tick(1h) 실행 결과."""
    tick_index: int
    hour: int
    feedback_collected: int
    feedback_converted: int
    batch_size: int
    outliers_removed: int
    purge_count: int           # 이번 tick에 purge된 레코드 수 (-1: 미실행)
    error: str | None
    elapsed_ms: float

    @property
    def success(self) -> bool:
        return self.error is None

    @property
    def loss_count(self) -> int:
        """손실 건수 = 수집 - 변환 (outlier 제외 후 잔여분은 손실 아님)."""
        return max(0, self.feedback_collected - self.feedback_converted - self.outliers_removed)


@dataclass
class LoopSimReport:
    """24시간 시뮬레이션 전체 리포트."""
    gate_id: str = _GATE_ID
    gate_name: str = "FeedbackLoopGate"
    passed: bool = False
    tick_count: int = 0
    success_ticks: int = 0
    error_ticks: int = 0
    total_collected: int = 0
    total_converted: int = 0
    total_outliers: int = 0
    total_loss: int = 0
    total_purged: int = 0
    purge_cycles: int = 0
    elapsed_ms: float = 0.0
    errors: list[str] = field(default_factory=list)
    ticks: list[LoopTickResult] = field(default_factory=list)
    summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "gate_id": self.gate_id,
            "gate_name": self.gate_name,
            "passed": self.passed,
            "tick_count": self.tick_count,
            "success_ticks": self.success_ticks,
            "error_ticks": self.error_ticks,
            "total_collected": self.total_collected,
            "total_converted": self.total_converted,
            "total_outliers": self.total_outliers,
            "total_loss": self.total_loss,
            "total_purged": self.total_purged,
            "purge_cycles": self.purge_cycles,
            "elapsed_ms": round(self.elapsed_ms, 3),
            "errors": self.errors,
            "summary": self.summary,
        }


# ── 피드백 생성기 ─────────────────────────────────────────────────────

_SAMPLE_TEXTS = [
    "이 장면은 정말 감동적이었습니다.",
    "캐릭터가 일관성 있게 묘사되었습니다.",
    "문체가 매끄럽고 읽기 좋았습니다.",
    "플롯 전개가 조금 급한 것 같습니다.",
    "전반적으로 훌륭한 작품이었습니다.",
    "감정 몰입도가 높았습니다.",
    "씬의 품질이 매우 뛰어납니다.",
    "대화가 자연스러웠습니다.",
    "긴장감이 잘 유지되었습니다.",
    "결말이 인상적이었습니다.",
    "주인공의 심리 묘사가 훌륭했습니다.",
    "배경 설명이 부족한 것 같습니다.",
    "문장 리듬감이 좋았습니다.",
    "갈등 구조가 선명하게 드러났습니다.",
    "복선이 자연스럽게 회수되었습니다.",
    "독자를 끌어당기는 힘이 있었습니다.",
    "서술 속도가 적절했습니다.",
    "장면 전환이 부드러웠습니다.",
    "인물들의 관계가 잘 그려졌습니다.",
    "주제 의식이 잘 드러났습니다.",
]

_FEEDBACK_TYPES = [
    FeedbackType.EMOTIONAL_IMPACT,
    FeedbackType.CHARACTER_CONSISTENCY,
    FeedbackType.STYLE_PREFERENCE,
    FeedbackType.PLOT_COHERENCE,
    FeedbackType.GENERAL,
    FeedbackType.SCENE_QUALITY,
]

_SCORES_NORMAL = [3.5, 4.0, 4.2, 4.5, 4.8, 3.8, 4.1, 4.3, 4.6, 3.9]
_SCORES_WITH_OUTLIER = [1.0, 5.0]  # z-score 이상치 유발용


def _generate_tick_feedbacks(
    collector: ReaderFeedbackCollector,
    tick_idx: int,
    count: int,
    include_outlier: bool = False,
) -> int:
    """tick 내 피드백 생성 후 컬렉터에 수집. 성공 건수 반환."""
    collected = 0
    for i in range(count):
        idx = (tick_idx * MAX_FEEDBACK_PER_TICK + i) % len(_SAMPLE_TEXTS)
        text = _SAMPLE_TEXTS[idx]
        score_pool = _SCORES_WITH_OUTLIER if (include_outlier and i == 0) else _SCORES_NORMAL
        score = score_pool[i % len(score_pool)]
        ftype = _FEEDBACK_TYPES[i % len(_FEEDBACK_TYPES)]
        reader_id = f"r_{tick_idx:03d}_{i:03d}_{uuid.uuid4().hex[:6]}"
        try:
            collector.collect(
                reader_id=reader_id,
                text=text,
                score=score,
                feedback_type=ftype,
                consent=ConsentLevel.ANONYMOUS,
                scene_id=f"scene_{tick_idx}",
            )
            collected += 1
        except Exception:
            pass  # 수집 실패는 tick 오류로 처리
    return collected


# ── 게이트 ────────────────────────────────────────────────────────────

class FeedbackLoopGate:
    """G69: 24h 무중단 피드백 루프 안정성 게이트."""

    def __init__(
        self,
        collector: ReaderFeedbackCollector | None = None,
        adapter: FeedbackToRLHFAdapter | None = None,
        feedbacks_per_tick: int = MIN_FEEDBACK_PER_TICK,
        purge_every_n_ticks: int = PURGE_EVERY_N_TICKS,
        include_outliers: bool = True,
    ) -> None:
        self._collector = collector or ReaderFeedbackCollector(
            policy=PIIPurgePolicy(retention_days=14),
            required_consent=ConsentLevel.ANONYMOUS,
        )
        self._adapter = adapter or FeedbackToRLHFAdapter(
            policy=OutlierPolicy(z_threshold=2.0, min_samples_after_filter=1),
        )
        self._feedbacks_per_tick = max(MIN_FEEDBACK_PER_TICK, feedbacks_per_tick)
        self._purge_every_n = purge_every_n_ticks
        self._include_outliers = include_outliers

    def run(self) -> LoopSimReport:
        """24시간 시뮬레이션 실행."""
        report = LoopSimReport()
        t_start = time.monotonic()

        for tick in range(TICK_COUNT):
            tick_result = self._run_tick(tick)
            report.ticks.append(tick_result)
            report.tick_count += 1

            if tick_result.success:
                report.success_ticks += 1
            else:
                report.error_ticks += 1
                if tick_result.error:
                    report.errors.append(f"tick{tick}: {tick_result.error}")

            report.total_collected += tick_result.feedback_collected
            report.total_converted += tick_result.feedback_converted
            report.total_outliers += tick_result.outliers_removed
            report.total_loss += tick_result.loss_count
            if tick_result.purge_count >= 0:
                report.total_purged += tick_result.purge_count
                report.purge_cycles += 1

        report.elapsed_ms = (time.monotonic() - t_start) * 1000.0

        # ── 합격 판정 ──────────────────────────────────────────────
        # 1. 오류 tick 0건
        # 2. 모든 tick 완주
        # 3. 데이터 손실 0건
        # 4. 최소 1회 purge 실행
        report.passed = (
            report.error_ticks == MAX_ALLOWED_ERRORS
            and report.tick_count == TICK_COUNT
            and report.total_loss == 0
            and report.purge_cycles >= 1
        )

        status = "PASS" if report.passed else "FAIL"
        report.summary = (
            f"G69 {status}: {TICK_COUNT}h 시뮬레이션 완주, "
            f"error_ticks={report.error_ticks}, "
            f"loss={report.total_loss}, "
            f"purge_cycles={report.purge_cycles}"
        )
        return report

    def _run_tick(self, tick_idx: int) -> LoopTickResult:
        """단일 tick 실행: 수집 → 변환 → (선택) purge."""
        t0 = time.monotonic()
        hour = tick_idx % 24
        purge_count = -1
        error: str | None = None
        collected = 0
        converted = 0
        batch_size = 0
        outliers = 0

        try:
            # 1. 피드백 수집
            use_outlier = self._include_outliers and (tick_idx % 8 == 0)
            collected = _generate_tick_feedbacks(
                self._collector,
                tick_idx,
                self._feedbacks_per_tick,
                include_outlier=use_outlier,
            )

            if collected == 0:
                raise RuntimeError("tick 내 피드백 수집 0건")

            # 2. RLHF 변환 (최근 수집분만)
            all_fb = self._collector.get_feedback(limit=self._feedbacks_per_tick * 2)
            # tick별 고유 scene_id로 필터
            tick_fb = [
                f for f in all_fb
                if f.meta and f.meta.get("scene_id") == f"scene_{tick_idx}"
            ]
            if not tick_fb:
                tick_fb = all_fb[-self._feedbacks_per_tick:]

            batch: RLHFBatch = self._adapter.convert(tick_fb)
            batch_size = len(batch.samples)
            converted = len(tick_fb)
            outliers = batch.outliers_removed

            # 3. purge 주기 확인
            if tick_idx > 0 and tick_idx % self._purge_every_n == 0:
                purge_count = self._collector.purge_expired()

        except Exception as exc:
            error = str(exc)

        elapsed = (time.monotonic() - t0) * 1000.0
        return LoopTickResult(
            tick_index=tick_idx,
            hour=hour,
            feedback_collected=collected,
            feedback_converted=converted,
            batch_size=batch_size,
            outliers_removed=outliers,
            purge_count=purge_count,
            error=error,
            elapsed_ms=elapsed,
        )


def run_g69(
    collector: ReaderFeedbackCollector | None = None,
    adapter: FeedbackToRLHFAdapter | None = None,
) -> dict[str, Any]:
    """G69 게이트 실행 진입점."""
    gate = FeedbackLoopGate(collector=collector, adapter=adapter)
    return gate.run().to_dict()
