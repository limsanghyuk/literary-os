"""Feedback 패키지 (ADR-119)."""
from literary_system.feedback.reader_feedback_collector import (
    AnonymizedFeedback,
    ConsentError,
    ConsentLevel,
    FeedbackCollectionError,
    FeedbackType,
    PIIPurgePolicy,
    RawFeedback,
    ReaderFeedbackCollector,
)

__all__ = [
    "ReaderFeedbackCollector",
    "AnonymizedFeedback",
    "RawFeedback",
    "FeedbackType",
    "ConsentLevel",
    "PIIPurgePolicy",
    "FeedbackCollectionError",
    "ConsentError",
]
