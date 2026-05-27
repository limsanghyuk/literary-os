"""Gate G68 — ReaderFeedbackCollectionGate (ADR-119).

합격 조건:
  1. PII 잔류 0건 (익명화 100%)
  2. 수집 피드백 수 ≥ MIN_FEEDBACK_COUNT (10)
  3. PIPA 동의 차단율 = 차단건 / (차단+수집) 계산 가능
"""
from __future__ import annotations

from typing import Any

from literary_system.feedback.reader_feedback_collector import (
    ConsentLevel,
    FeedbackType,
    MIN_FEEDBACK_COUNT,
    PIIPurgePolicy,
    ReaderFeedbackCollector,
)

__all__ = ["FeedbackCollectionGate", "run_g68"]

_GATE_ID = "G68"
_PASS_THRESHOLD_PII = 0          # PII 잔류 허용 건수
_PASS_THRESHOLD_COUNT = MIN_FEEDBACK_COUNT


class FeedbackCollectionGate:
    """Gate G68: ReaderFeedbackCollector 합격 기준 검증."""

    def __init__(self, collector: ReaderFeedbackCollector | None = None) -> None:
        self._collector = collector or _build_smoke_collector()

    def run(self) -> dict[str, Any]:
        report = self._collector.gate_report()
        passed = report["gate_pass"]
        return {
            "gate_id": _GATE_ID,
            "gate_name": "ReaderFeedbackCollectionGate",
            "passed": passed,
            "pii_residual": report["pii_residual_count"],
            "feedback_count": report["total_feedback"],
            "min_required": _PASS_THRESHOLD_COUNT,
            "pipa_compliant": report["pipa_compliant"],
            "pii_clean_rate": report["pii_clean_rate"],
            "summary": (
                f"G68 {'PASS' if passed else 'FAIL'}: "
                f"{report['total_feedback']} feedbacks, "
                f"PII_residual={report['pii_residual_count']}"
            ),
        }


def _build_smoke_collector() -> ReaderFeedbackCollector:
    """스모크 테스트용 컬렉터 — 최소 10개 피드백 삽입."""
    col = ReaderFeedbackCollector(
        policy=PIIPurgePolicy(retention_days=14),
        required_consent=ConsentLevel.ANONYMOUS,
    )
    samples = [
        ("이 장면은 감동적이었습니다.", 5.0, FeedbackType.EMOTIONAL_IMPACT),
        ("캐릭터 일관성이 조금 부족해요.", 3.5, FeedbackType.CHARACTER_CONSISTENCY),
        ("문체가 매끄럽습니다.", 4.5, FeedbackType.STYLE_PREFERENCE),
        ("플롯이 너무 급하게 진행됩니다.", 3.0, FeedbackType.PLOT_COHERENCE),
        ("전반적으로 훌륭한 작품입니다.", 4.8, FeedbackType.GENERAL),
        ("감정 몰입도가 높았습니다.", 4.2, FeedbackType.EMOTIONAL_IMPACT),
        ("씬의 품질이 뛰어납니다.", 4.6, FeedbackType.SCENE_QUALITY),
        ("대화가 자연스럽습니다.", 4.0, FeedbackType.GENERAL),
        ("긴장감이 잘 유지됩니다.", 4.3, FeedbackType.SCENE_QUALITY),
        ("결말이 인상적이었습니다.", 4.7, FeedbackType.GENERAL),
    ]
    for i, (text, score, ftype) in enumerate(samples):
        col.collect(
            reader_id=f"reader_{i:03d}",
            text=text,
            score=score,
            feedback_type=ftype,
            consent=ConsentLevel.ANONYMOUS,
        )
    return col


def run_g68(collector: ReaderFeedbackCollector | None = None) -> dict[str, Any]:
    """G68 게이트 실행 진입점."""
    gate = FeedbackCollectionGate(collector)
    return gate.run()
