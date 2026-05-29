"""
feedback_integrator.py — FeedbackIntegrator V640 (ADR-082)

SP-C.1 Self-Learning Loop 인간 피드백 통합기.

피드백 유형 4종:
  - SCORE_CORRECTION : 평가 점수 보정 (human score override)
  - LABEL_REVISION   : 레이블 수정 (오분류 정정)
  - STYLE_ANNOTATION : 문체 주석 (드라마 도메인 특화)
  - REJECTION        : 샘플 거부 (품질 기준 미달)

역할:
  - 인간 검증자(calibration evaluator)의 피드백을 수집·집계
  - ConstitutionEvalV2(V637) 평가 결과와 연계하여 가중치 보정 신호 생성
  - LOSDB JSONL append-only 영속화

설계 원칙:
  - LLM-0 원칙 완전 준수 (외부 LLM 호출 없음)
  - 순수 Python 표준 라이브러리만 사용
"""
from __future__ import annotations

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

# -------------------------------------------------
# 피드백 유형 및 상수
# -------------------------------------------------
FEEDBACK_TYPES: List[str] = [
    "SCORE_CORRECTION",
    "LABEL_REVISION",
    "STYLE_ANNOTATION",
    "REJECTION",
]

# 피드백 집계 임계값
MIN_FEEDBACK_FOR_SIGNAL: int = 3      # 신호 생성에 필요한 최소 피드백 수
CORRECTION_WEIGHT: float = 0.8        # 점수 보정 피드백 가중치
REJECTION_PENALTY: float = 0.5        # 거부 시 점수 페널티

_DEFAULT_STORE = "data/losdb/feedback_integrator.jsonl"
_MEMORY_SENTINEL = ":memory:"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _mean(values: Sequence[float]) -> float:
    if not values:
        return 0.0
    return sum(values) / len(values)


# -------------------------------------------------
# 데이터 클래스
# -------------------------------------------------
@dataclass
class FeedbackRecord:
    """단일 인간 피드백 레코드."""
    record_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    created_at: str = field(default_factory=_now_iso)
    scene_id: str = ""
    feedback_type: str = ""          # FEEDBACK_TYPES 중 하나
    evaluator_id: str = ""           # 인간 검증자 ID
    original_score: float = 0.0      # 자동 평가 원점수
    corrected_score: float = 0.0     # 인간 보정 점수 (SCORE_CORRECTION 시)
    label_before: str = ""           # 수정 전 레이블 (LABEL_REVISION 시)
    label_after: str = ""            # 수정 후 레이블
    annotation: str = ""             # 주석 텍스트 (STYLE_ANNOTATION 시)
    note: str = ""

    def correction_delta(self) -> float:
        """보정 점수 - 원점수 델타."""
        return self.corrected_score - self.original_score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "created_at": self.created_at,
            "scene_id": self.scene_id,
            "feedback_type": self.feedback_type,
            "evaluator_id": self.evaluator_id,
            "original_score": self.original_score,
            "corrected_score": self.corrected_score,
            "label_before": self.label_before,
            "label_after": self.label_after,
            "annotation": self.annotation,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "FeedbackRecord":
        return cls(
            record_id=d["record_id"],
            created_at=d["created_at"],
            scene_id=d.get("scene_id", ""),
            feedback_type=d.get("feedback_type", ""),
            evaluator_id=d.get("evaluator_id", ""),
            original_score=float(d.get("original_score", 0.0)),
            corrected_score=float(d.get("corrected_score", 0.0)),
            label_before=d.get("label_before", ""),
            label_after=d.get("label_after", ""),
            annotation=d.get("annotation", ""),
            note=d.get("note", ""),
        )


@dataclass
class IntegrationResult:
    """피드백 집계 결과 — 가중치 보정 신호."""
    result_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    computed_at: str = field(default_factory=_now_iso)
    scene_ids: List[str] = field(default_factory=list)
    feedback_count: int = 0
    avg_correction_delta: float = 0.0    # 평균 보정 델타
    rejection_rate: float = 0.0          # 거부율
    label_revision_rate: float = 0.0     # 레이블 수정율
    signal_strength: float = 0.0         # 0.0~1.0 — 신호 신뢰도
    has_signal: bool = False             # MIN_FEEDBACK_FOR_SIGNAL 충족 여부
    note: str = ""

    def summary(self) -> str:
        status = "SIGNAL" if self.has_signal else "NO_SIGNAL"
        return (
            f"[{status}] feedbacks={self.feedback_count} "
            f"delta={self.avg_correction_delta:+.3f} "
            f"rejection={self.rejection_rate:.1%} "
            f"strength={self.signal_strength:.3f}"
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "result_id": self.result_id,
            "computed_at": self.computed_at,
            "scene_ids": self.scene_ids,
            "feedback_count": self.feedback_count,
            "avg_correction_delta": self.avg_correction_delta,
            "rejection_rate": self.rejection_rate,
            "label_revision_rate": self.label_revision_rate,
            "signal_strength": self.signal_strength,
            "has_signal": self.has_signal,
            "note": self.note,
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "IntegrationResult":
        return cls(
            result_id=d["result_id"],
            computed_at=d["computed_at"],
            scene_ids=d.get("scene_ids", []),
            feedback_count=d.get("feedback_count", 0),
            avg_correction_delta=float(d.get("avg_correction_delta", 0.0)),
            rejection_rate=float(d.get("rejection_rate", 0.0)),
            label_revision_rate=float(d.get("label_revision_rate", 0.0)),
            signal_strength=float(d.get("signal_strength", 0.0)),
            has_signal=d.get("has_signal", False),
            note=d.get("note", ""),
        )


# -------------------------------------------------
# FeedbackIntegrator 본체
# -------------------------------------------------
class FeedbackIntegrator:
    """
    인간 피드백 통합기 -- SP-C.1 V640 (ADR-082).

    사용법::

        integrator = FeedbackIntegrator()                  # 메모리 모드
        integrator = FeedbackIntegrator("path/to.jsonl")  # 파일 영속화

        # 피드백 수집
        record = integrator.record_feedback(
            scene_id="scene-001",
            feedback_type="SCORE_CORRECTION",
            evaluator_id="human-1",
            original_score=0.65,
            corrected_score=0.80,
        )

        # 집계 신호 생성
        result = integrator.integrate(scene_ids=["scene-001", ...])
    """

    def __init__(self, store_path: str = _MEMORY_SENTINEL) -> None:
        self._store_path = store_path
        self._memory: List[FeedbackRecord] = []
        self._results: List[IntegrationResult] = []
        if store_path != _MEMORY_SENTINEL:
            self._load_from_disk()

    # -- 피드백 수집 --------------------------
    def record_feedback(
        self,
        scene_id: str,
        feedback_type: str,
        evaluator_id: str = "",
        original_score: float = 0.0,
        corrected_score: float = 0.0,
        label_before: str = "",
        label_after: str = "",
        annotation: str = "",
        note: str = "",
        now: Optional[str] = None,
    ) -> FeedbackRecord:
        """단일 피드백 레코드 수집."""
        record = FeedbackRecord(
            created_at=now or _now_iso(),
            scene_id=scene_id,
            feedback_type=feedback_type,
            evaluator_id=evaluator_id,
            original_score=original_score,
            corrected_score=corrected_score,
            label_before=label_before,
            label_after=label_after,
            annotation=annotation,
            note=note,
        )
        self._memory.append(record)
        if self._store_path != _MEMORY_SENTINEL:
            self._append_to_disk(record)
        return record

    def batch_record(
        self,
        items: List[Dict[str, Any]],
        evaluator_id: str = "",
    ) -> List[FeedbackRecord]:
        """여러 피드백 배치 수집."""
        results = []
        for item in items:
            results.append(self.record_feedback(
                scene_id=item.get("scene_id", ""),
                feedback_type=item.get("feedback_type", ""),
                evaluator_id=item.get("evaluator_id", evaluator_id),
                original_score=float(item.get("original_score", 0.0)),
                corrected_score=float(item.get("corrected_score", 0.0)),
                label_before=item.get("label_before", ""),
                label_after=item.get("label_after", ""),
                annotation=item.get("annotation", ""),
                note=item.get("note", ""),
            ))
        return results

    # -- 피드백 집계 --------------------------
    def integrate(
        self,
        scene_ids: Optional[List[str]] = None,
        note: str = "",
        now: Optional[str] = None,
    ) -> IntegrationResult:
        """
        수집된 피드백을 집계하여 가중치 보정 신호 생성.

        Args:
            scene_ids: 집계 대상 scene_id 목록 (None이면 전체)
            note: 메모
            now: ISO8601 타임스탬프 (테스트용)
        """
        if scene_ids:
            records = [r for r in self._memory if r.scene_id in scene_ids]
            target_scenes = scene_ids
        else:
            records = list(self._memory)
            target_scenes = list({r.scene_id for r in records})

        n = len(records)

        # 점수 보정 델타 평균
        corrections = [
            r.correction_delta()
            for r in records
            if r.feedback_type == "SCORE_CORRECTION"
        ]
        avg_delta = _mean(corrections) if corrections else 0.0

        # 거부율
        rejections = [r for r in records if r.feedback_type == "REJECTION"]
        rejection_rate = len(rejections) / n if n > 0 else 0.0

        # 레이블 수정율
        revisions = [r for r in records if r.feedback_type == "LABEL_REVISION"]
        revision_rate = len(revisions) / n if n > 0 else 0.0

        # 신호 강도: 피드백 수 충족 여부 + 보정 크기
        has_signal = n >= MIN_FEEDBACK_FOR_SIGNAL
        if has_signal:
            # |delta| * correction_weight + rejection_penalty * rejection_rate
            signal_strength = min(
                abs(avg_delta) * CORRECTION_WEIGHT
                + rejection_rate * REJECTION_PENALTY,
                1.0,
            )
        else:
            signal_strength = 0.0

        result = IntegrationResult(
            computed_at=now or _now_iso(),
            scene_ids=target_scenes,
            feedback_count=n,
            avg_correction_delta=avg_delta,
            rejection_rate=rejection_rate,
            label_revision_rate=revision_rate,
            signal_strength=signal_strength,
            has_signal=has_signal,
            note=note,
        )
        self._results.append(result)
        return result

    # -- 조회 API ----------------------------
    def feedbacks(self) -> List[FeedbackRecord]:
        """수집된 전체 피드백 레코드."""
        return list(self._memory)

    def feedbacks_by_scene(self, scene_id: str) -> List[FeedbackRecord]:
        """특정 장면의 피드백 목록."""
        return [r for r in self._memory if r.scene_id == scene_id]

    def feedbacks_by_type(self, feedback_type: str) -> List[FeedbackRecord]:
        """특정 유형의 피드백 목록."""
        return [r for r in self._memory if r.feedback_type == feedback_type]

    def feedbacks_by_evaluator(self, evaluator_id: str) -> List[FeedbackRecord]:
        """특정 검증자의 피드백 목록."""
        return [r for r in self._memory if r.evaluator_id == evaluator_id]

    def integration_history(self) -> List[IntegrationResult]:
        """집계 결과 이력."""
        return list(self._results)

    def last_result(self) -> Optional[IntegrationResult]:
        """가장 최근 집계 결과."""
        return self._results[-1] if self._results else None

    def count(self) -> int:
        """누적 피드백 수."""
        return len(self._memory)

    def clear(self) -> None:
        """메모리 및 디스크 데이터 초기화."""
        self._memory.clear()
        self._results.clear()
        if self._store_path != _MEMORY_SENTINEL:
            Path(self._store_path).write_text("", encoding="utf-8")

    # -- 영속화 ------------------------------
    def _append_to_disk(self, record: FeedbackRecord) -> None:
        """JSONL append-only 영속화."""
        path = Path(self._store_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record.to_dict(), ensure_ascii=False) + "\n")

    def _load_from_disk(self) -> None:
        """디스크에서 JSONL 로드."""
        path = Path(self._store_path)
        if not path.exists():
            return
        for line in path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                self._memory.append(
                    FeedbackRecord.from_dict(json.loads(line))
                )
            except (json.JSONDecodeError, KeyError):
                continue
