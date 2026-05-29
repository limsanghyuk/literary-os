"""FeedbackToRLHF Adapter — 피드백 → RLHF 배치 변환 (ADR-120).

처리 파이프라인:
  1. AnonymizedFeedback 수집
  2. z-score 이상치 제거 (|z| > Z_THRESHOLD 제거)
  3. 정규화 점수 산출 (1~5 → 0~1)
  4. RLHFSample 배치 생성 → RLHF 파이프라인 공급

ADR-015/031 LLM-0 원칙: 이 모듈은 외부 LLM API를 호출하지 않는다.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any

from literary_system.feedback.reader_feedback_collector import AnonymizedFeedback, FeedbackType

__all__ = [
    "RLHFSample",
    "RLHFBatch",
    "FeedbackToRLHFAdapter",
    "OutlierPolicy",
    "AdapterStats",
]

# ── 상수 ──────────────────────────────────────────────────────────────────

Z_THRESHOLD = 2.0        # |z| 초과 시 이상치로 분류
MIN_BATCH_SIZE = 5       # 배치 최소 크기
SCORE_MIN = 1.0
SCORE_MAX = 5.0


# ── 데이터 모델 ────────────────────────────────────────────────────────────

@dataclass
class RLHFSample:
    """RLHF 파이프라인 입력 단위."""
    sample_id: str
    text: str
    normalized_score: float   # 0.0~1.0
    raw_score: float          # 1.0~5.0
    feedback_type: FeedbackType
    scene_id: str = ""
    weight: float = 1.0       # 피드백 신뢰 가중치
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class RLHFBatch:
    """RLHF 배치 — 이상치 제거 후 최종 샘플 묶음."""
    batch_id: str
    samples: list[RLHFSample]
    outliers_removed: int
    mean_score: float
    std_score: float
    z_threshold: float
    created_at: float = field(default_factory=lambda: __import__("time").time())

    @property
    def size(self) -> int:
        return len(self.samples)

    @property
    def is_valid(self) -> bool:
        return self.size >= MIN_BATCH_SIZE


@dataclass
class OutlierPolicy:
    """이상치 처리 정책."""
    z_threshold: float = Z_THRESHOLD
    min_samples_after_filter: int = MIN_BATCH_SIZE
    strategy: str = "remove"   # "remove" | "cap" (현재 remove만 구현)


@dataclass
class AdapterStats:
    """누적 변환 통계."""
    total_input: int = 0
    total_output: int = 0
    total_outliers: int = 0
    batches_created: int = 0

    @property
    def outlier_rate(self) -> float:
        if self.total_input == 0:
            return 0.0
        return self.total_outliers / self.total_input

    @property
    def pass_rate(self) -> float:
        if self.total_input == 0:
            return 0.0
        return self.total_output / self.total_input


# ── 어댑터 ─────────────────────────────────────────────────────────────────

class FeedbackToRLHFAdapter:
    """피드백 → RLHF 배치 변환기.

    사용법:
        adapter = FeedbackToRLHFAdapter()
        batch = adapter.convert(feedbacks)
    """

    def __init__(self, policy: OutlierPolicy | None = None) -> None:
        self._policy = policy or OutlierPolicy()
        self._stats = AdapterStats()
        self._batch_counter = 0

    # ── 공개 메서드 ────────────────────────────────────────────────────

    def convert(self, feedbacks: list[AnonymizedFeedback]) -> RLHFBatch:
        """피드백 목록을 RLHF 배치로 변환.

        Raises
        ------
        ValueError : 유효 샘플 수 < min_samples_after_filter
        """
        self._stats.total_input += len(feedbacks)

        # 1. 기본 유효성 필터 (점수 범위)
        valid = [f for f in feedbacks if SCORE_MIN <= f.score <= SCORE_MAX]

        # 2. z-score 이상치 제거
        filtered, outlier_count, mean_s, std_s = self._filter_outliers(valid)
        self._stats.total_outliers += outlier_count

        if len(filtered) < self._policy.min_samples_after_filter:
            raise ValueError(
                f"Insufficient samples after outlier removal: "
                f"{len(filtered)} < {self._policy.min_samples_after_filter}"
            )

        # 3. RLHFSample 생성
        samples = [self._to_sample(f) for f in filtered]

        # 4. 배치 조립
        self._batch_counter += 1
        batch_id = f"batch_{self._batch_counter:06d}"
        batch = RLHFBatch(
            batch_id=batch_id,
            samples=samples,
            outliers_removed=outlier_count,
            mean_score=round(mean_s, 4),
            std_score=round(std_s, 4),
            z_threshold=self._policy.z_threshold,
        )

        self._stats.total_output += len(samples)
        self._stats.batches_created += 1
        return batch

    def convert_by_type(
        self,
        feedbacks: list[AnonymizedFeedback],
        feedback_type: FeedbackType,
    ) -> RLHFBatch:
        """특정 유형 피드백만 필터링 후 변환."""
        typed = [f for f in feedbacks if f.feedback_type == feedback_type]
        return self.convert(typed)

    @property
    def stats(self) -> AdapterStats:
        return self._stats

    def reset_stats(self) -> None:
        self._stats = AdapterStats()

    # ── 내부 ────────────────────────────────────────────────────────────

    def _filter_outliers(
        self,
        feedbacks: list[AnonymizedFeedback],
    ) -> tuple[list[AnonymizedFeedback], int, float, float]:
        """z-score 기반 이상치 제거.

        Returns
        -------
        (filtered_list, outlier_count, mean, std)
        """
        if not feedbacks:
            return [], 0, 0.0, 0.0

        scores = [f.score for f in feedbacks]

        if len(scores) < 2:
            return list(feedbacks), 0, scores[0], 0.0

        mean_s = statistics.mean(scores)
        std_s = statistics.pstdev(scores)  # 모표준편차

        if std_s < 1e-9:
            # 모든 점수가 동일하면 이상치 없음
            return list(feedbacks), 0, mean_s, std_s

        threshold = self._policy.z_threshold
        filtered = []
        outlier_count = 0

        for fb in feedbacks:
            z = abs((fb.score - mean_s) / std_s)
            if z <= threshold:
                filtered.append(fb)
            else:
                outlier_count += 1

        return filtered, outlier_count, mean_s, std_s

    def _to_sample(self, fb: AnonymizedFeedback) -> RLHFSample:
        """AnonymizedFeedback → RLHFSample 변환."""
        normalized = (fb.score - SCORE_MIN) / (SCORE_MAX - SCORE_MIN)
        normalized = max(0.0, min(1.0, normalized))
        return RLHFSample(
            sample_id=fb.feedback_id,
            text=fb.text,
            normalized_score=round(normalized, 4),
            raw_score=fb.score,
            feedback_type=fb.feedback_type,
            scene_id=fb.scene_id,
            weight=self._compute_weight(fb),
            meta={"hashed_reader_id": fb.hashed_reader_id},
        )

    @staticmethod
    def _compute_weight(fb: AnonymizedFeedback) -> float:
        """피드백 신뢰 가중치 계산.

        극단 점수(1.0, 5.0)는 신뢰도를 약간 낮춤.
        """
        if fb.score in (1.0, 5.0):
            return 0.85
        return 1.0
