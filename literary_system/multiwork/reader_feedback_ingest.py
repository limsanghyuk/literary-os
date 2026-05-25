"""literary_system/multiwork/reader_feedback_ingest.py

ReaderFeedbackIngest (P-IF-03) — V621, ADR-088.

역할:
    독자 피드백을 수집·보상 신호로 변환하는 인터페이스를 정의한다.
    Phase B에서는 인터페이스(Protocol + dataclass)만 정의하며,
    실제 파이프라인 연결(ingest())은 Phase C+에서 활성화된다.

LLM-0 원칙: 외부 LLM API 호출 없음.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from typing import Protocol, runtime_checkable


# ══════════════════════════════════════════════════════════════════════════════
#  P-IF-03 데이터 모델
# ══════════════════════════════════════════════════════════════════════════════


@dataclass(frozen=True)
class ReaderFeedback:
    """독자 피드백 레코드 (P-IF-03, ADR-088).

    Args:
        reader_id:            독자 식별자.
        work_id:              작품 식별자.
        scene_id:             씬 식별자.
        rating:               평점 (1~5).
        comment:              선택적 텍스트 코멘트.
        timestamp:            피드백 타임스탬프 (기본: UTC now).
        reader_demographic:   독자 인구통계 딕셔너리 (선택).
        engagement_seconds:   실제 읽기 소요 시간 (선택).
    """

    reader_id:           str
    work_id:             str
    scene_id:            str
    rating:              int          # 1~5
    comment:             Optional[str]  = None
    timestamp:           Optional[datetime] = None
    reader_demographic:  Optional[Dict[str, Any]] = None
    engagement_seconds:  Optional[float] = None

    def __post_init__(self) -> None:
        if not (1 <= self.rating <= 5):
            raise ValueError(
                f"rating은 1~5 사이여야 합니다. 현재: {self.rating!r}"
            )
        if self.timestamp is None:
            object.__setattr__(
                self, "timestamp", datetime.now(tz=timezone.utc)
            )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reader_id":           self.reader_id,
            "work_id":             self.work_id,
            "scene_id":            self.scene_id,
            "rating":              self.rating,
            "comment":             self.comment,
            "timestamp":           self.timestamp.isoformat() if self.timestamp else None,
            "reader_demographic":  self.reader_demographic,
            "engagement_seconds":  self.engagement_seconds,
        }


@dataclass
class RewardSignal:
    """피드백 → 보상 신호 변환 결과 (Phase C+ 내부 타입)."""
    scene_id:    str
    reward:      float           # 0.0 ~ 1.0
    source:      str = "reader_feedback"
    metadata:    Dict[str, Any] = field(default_factory=dict)


# ══════════════════════════════════════════════════════════════════════════════
#  P-IF-03 어댑터 프로토콜
# ══════════════════════════════════════════════════════════════════════════════


@runtime_checkable
class RewardSignalAdapter(Protocol):
    """피드백 → 보상 신호 변환기 프로토콜 (Phase C+ 구현체가 준수)."""

    def from_feedback(self, fb: ReaderFeedback) -> RewardSignal:
        """ReaderFeedback을 RewardSignal로 변환."""
        ...


# ══════════════════════════════════════════════════════════════════════════════
#  P-IF-03 인제스트 게이트
# ══════════════════════════════════════════════════════════════════════════════


class ReaderFeedbackIngest:
    """독자 피드백 수집·변환 게이트 (P-IF-03, ADR-088).

    Phase B: RewardSignalAdapter 미연결 시 NotImplementedError.
    Phase C+: adapter 주입 후 ingest()가 활성화된다.

    Example::

        # Phase B — 인터페이스 확인만
        ingest = ReaderFeedbackIngest()
        assert not ingest.is_phase_c_active()

        # Phase C+ — 어댑터 주입 후 활성화
        ingest = ReaderFeedbackIngest(reward_adapter=MyAdapter())
        signal = ingest.ingest(feedback)
    """

    PHASE_C_FEATURE: bool = True   # 설계도 §2.2 — Phase C+ 기능임을 명시

    def __init__(
        self,
        reward_adapter: Optional[RewardSignalAdapter] = None,
    ) -> None:
        self._adapter = reward_adapter
        self._ingested_count: int = 0
        self._history: List[ReaderFeedback] = []

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def ingest(self, feedback: ReaderFeedback) -> RewardSignal:
        """피드백 수집 및 보상 신호 변환.

        Phase B: adapter 미연결 → NotImplementedError 발생.
        Phase C+: adapter.from_feedback(feedback) 위임.

        Raises:
            NotImplementedError: Phase B 환경 (adapter 미연결).
            TypeError: feedback이 ReaderFeedback 인스턴스가 아닐 때.
        """
        if not isinstance(feedback, ReaderFeedback):
            raise TypeError(
                f"feedback은 ReaderFeedback 인스턴스여야 합니다. "
                f"받은 타입: {type(feedback).__name__}"
            )
        if self._adapter is None:
            raise NotImplementedError(
                "Phase C+ 기능 (P-IF-03). "
                "Phase B에서는 인터페이스 정의만 존재합니다. "
                "RewardSignalAdapter 주입 후 사용하세요."
            )
        self._history.append(feedback)
        self._ingested_count += 1
        return self._adapter.from_feedback(feedback)

    def is_phase_c_active(self) -> bool:
        """Phase C+ 어댑터 연결 여부."""
        return self._adapter is not None

    def ingested_count(self) -> int:
        """총 수집 피드백 수."""
        return self._ingested_count

    def recent_history(self, n: int = 10) -> List[ReaderFeedback]:
        """최근 n건 피드백 반환."""
        return self._history[-n:]

    def summary(self) -> Dict[str, Any]:
        """현재 상태 요약."""
        return {
            "phase_c_active":  self.is_phase_c_active(),
            "ingested_count":  self._ingested_count,
            "history_size":    len(self._history),
        }
