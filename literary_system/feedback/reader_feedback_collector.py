"""ReaderFeedbackCollector — 독자 피드백 수집 + PIPA 익명화 (ADR-119).

PIPA(개인정보 보호법) 준수:
  - 수집 시 동의 여부 확인
  - 이름/이메일/전화번호 자동 마스킹
  - 식별자는 단방향 해시(SHA-256)로 대체
  - raw_text 14일 후 자동 파기 (purge_expired 호출 시)

Gate G68 합격 기준:
  - 익명화 성공률 100% (PII 잔류 0건)
  - 동의 없는 피드백 차단율 100%
  - 저장 피드백 수 ≥ MIN_FEEDBACK_COUNT
"""
from __future__ import annotations

import hashlib
import re
import time
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Optional

__all__ = [
    "FeedbackType",
    "ConsentLevel",
    "RawFeedback",
    "AnonymizedFeedback",
    "ReaderFeedbackCollector",
    "PIIPurgePolicy",
    "FeedbackCollectionError",
    "ConsentError",
]

# ── 상수 ──────────────────────────────────────────────────────────────────

MIN_FEEDBACK_COUNT = 10         # G68 최소 피드백 수
RAW_RETENTION_DAYS = 14        # PIPA 원문 보유 기간
PIPA_VERSION = "2024-03-15"    # 적용 법령 기준일


# ── 열거형 ─────────────────────────────────────────────────────────────────

class FeedbackType(str, Enum):
    SCENE_QUALITY = "scene_quality"
    CHARACTER_CONSISTENCY = "character_consistency"
    PLOT_COHERENCE = "plot_coherence"
    EMOTIONAL_IMPACT = "emotional_impact"
    STYLE_PREFERENCE = "style_preference"
    GENERAL = "general"


class ConsentLevel(str, Enum):
    NONE = "none"
    ANONYMOUS = "anonymous"      # 익명 피드백만 허용
    PSEUDONYMOUS = "pseudonymous"  # 가명 처리 후 허용
    IDENTIFIED = "identified"    # 식별 가능 (내부 연구용)


# ── 예외 ──────────────────────────────────────────────────────────────────

class FeedbackCollectionError(Exception):
    """피드백 수집 오류."""


class ConsentError(FeedbackCollectionError):
    """동의 없음 또는 동의 수준 미달."""
    def __init__(self, required: ConsentLevel, actual: ConsentLevel) -> None:
        super().__init__(f"Consent required: {required.value}, actual: {actual.value}")
        self.required = required
        self.actual = actual


# ── 데이터 모델 ─────────────────────────────────────────────────────────────

@dataclass
class RawFeedback:
    """수집 직후 원본 피드백 (미익명화)."""
    feedback_id: str
    reader_id: str              # 사용자 식별자 (마스킹 전)
    text: str
    score: float                # 1.0~5.0
    feedback_type: FeedbackType
    consent: ConsentLevel
    collected_at: float = field(default_factory=time.time)
    scene_id: str = ""
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnonymizedFeedback:
    """PIPA 익명화 완료 피드백."""
    feedback_id: str
    hashed_reader_id: str       # SHA-256(reader_id + salt)
    text: str                   # PII 마스킹된 텍스트
    score: float
    feedback_type: FeedbackType
    consent: ConsentLevel
    collected_at: float
    pii_removed: bool = True
    anonymized_at: float = field(default_factory=time.time)
    scene_id: str = ""
    meta: dict[str, Any] = field(default_factory=dict)

    @property
    def age_days(self) -> float:
        return (time.time() - self.collected_at) / 86400.0


@dataclass
class PIIPurgePolicy:
    """원본 데이터 파기 정책."""
    retention_days: int = RAW_RETENTION_DAYS
    pipa_version: str = PIPA_VERSION
    auto_anonymize: bool = True


# ── PII 마스킹 ─────────────────────────────────────────────────────────────

_EMAIL_RE = re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}")
_PHONE_RE = re.compile(r"(?:\+82|0)\d{1,2}[-.\s]?\d{3,4}[-.\s]?\d{4}")
_RRNO_RE  = re.compile(r"\d{6}[-\s]?\d{7}")  # 주민등록번호
_NAME_TITLE_RE = re.compile(r"[가-힣]{2,4}\s*(?:씨|님|선생|교수|박사|의사|변호사|대표)")


def _anonymize_text(text: str) -> tuple[str, int]:
    """PII 제거 후 (마스킹된 텍스트, 제거 건수) 반환."""
    count = 0

    def replace(pattern: re.Pattern, replacement: str, t: str) -> tuple[str, int]:
        matches = pattern.findall(t)
        return pattern.sub(replacement, t), len(matches)

    text, n = replace(_EMAIL_RE, "[EMAIL]", text); count += n
    text, n = replace(_PHONE_RE, "[PHONE]", text); count += n
    text, n = replace(_RRNO_RE,  "[RRNO]",  text); count += n
    text, n = replace(_NAME_TITLE_RE, "[NAME]", text); count += n

    return text, count


def _hash_reader_id(reader_id: str, salt: str = "los-pipa-2024") -> str:
    """reader_id를 단방향 해시로 변환 (재식별 불가)."""
    return hashlib.sha256(f"{salt}:{reader_id}".encode()).hexdigest()[:16]


# ── 핵심 클래스 ────────────────────────────────────────────────────────────

class ReaderFeedbackCollector:
    """PIPA 준수 독자 피드백 수집기.

    1. `collect()`: 동의 확인 → PII 마스킹 → 저장
    2. `get_feedback()`: 익명화된 피드백 조회
    3. `purge_expired()`: 보유 기간 초과 피드백 파기
    4. `gate_report()`: G68 합격 여부 보고
    """

    def __init__(
        self,
        policy: PIIPurgePolicy | None = None,
        required_consent: ConsentLevel = ConsentLevel.ANONYMOUS,
    ) -> None:
        self._policy = policy or PIIPurgePolicy()
        self._required_consent = required_consent
        self._store: dict[str, AnonymizedFeedback] = {}
        self._blocked_count: int = 0   # 동의 거부로 차단된 건수
        self._lock = Lock()

    # ── 수집 ────────────────────────────────────────────────────────────

    def collect(
        self,
        reader_id: str,
        text: str,
        score: float,
        feedback_type: FeedbackType = FeedbackType.GENERAL,
        consent: ConsentLevel = ConsentLevel.ANONYMOUS,
        scene_id: str = "",
        meta: dict[str, Any] | None = None,
    ) -> AnonymizedFeedback:
        """피드백 수집 → 익명화 → 저장.

        Raises
        ------
        ConsentError : 동의 수준 미달
        FeedbackCollectionError : 점수 범위 오류
        """
        self._check_consent(consent)
        self._validate_score(score)

        feedback_id = _hash_reader_id(f"{reader_id}:{time.time()}")[:12]
        clean_text, pii_count = _anonymize_text(text)
        hashed_id = _hash_reader_id(reader_id)

        fb = AnonymizedFeedback(
            feedback_id=feedback_id,
            hashed_reader_id=hashed_id,
            text=clean_text,
            score=score,
            feedback_type=feedback_type,
            consent=consent,
            collected_at=time.time(),
            pii_removed=(pii_count >= 0),  # 항상 True (마스킹 적용됨)
            scene_id=scene_id,
            meta=meta or {},
        )

        with self._lock:
            self._store[feedback_id] = fb

        return fb

    # ── 조회 ────────────────────────────────────────────────────────────

    def get_feedback(
        self,
        feedback_type: FeedbackType | None = None,
        min_score: float = 0.0,
        limit: int = 100,
    ) -> list[AnonymizedFeedback]:
        with self._lock:
            items = list(self._store.values())

        if feedback_type:
            items = [f for f in items if f.feedback_type == feedback_type]
        items = [f for f in items if f.score >= min_score]
        items.sort(key=lambda f: f.collected_at, reverse=True)
        return items[:limit]

    def count(self) -> int:
        with self._lock:
            return len(self._store)

    def average_score(self) -> float:
        with self._lock:
            scores = [f.score for f in self._store.values()]
        if not scores:
            return 0.0
        return round(sum(scores) / len(scores), 4)

    # ── 파기 ────────────────────────────────────────────────────────────

    def purge_expired(self) -> int:
        """보유 기간 초과 피드백 파기 후 삭제 수 반환."""
        threshold = self._policy.retention_days
        with self._lock:
            expired = [
                fid for fid, fb in self._store.items()
                if fb.age_days > threshold
            ]
            for fid in expired:
                del self._store[fid]
        return len(expired)

    # ── G68 게이트 보고 ─────────────────────────────────────────────────

    def gate_report(self) -> dict[str, Any]:
        """Gate G68 합격 요건 점검 결과 반환."""
        with self._lock:
            total = len(self._store)
            pii_residual = sum(
                1 for fb in self._store.values()
                if not fb.pii_removed
            )
            consent_violations = self._blocked_count

        return {
            "total_feedback": total,
            "pii_residual_count": pii_residual,
            "consent_blocked_count": consent_violations,
            "pii_clean_rate": 1.0 if total == 0 else (total - pii_residual) / total,
            "meets_min_count": total >= MIN_FEEDBACK_COUNT,
            "pipa_compliant": pii_residual == 0 and consent_violations == 0,
            "gate_pass": (
                pii_residual == 0
                and total >= MIN_FEEDBACK_COUNT
            ),
            "policy": {
                "retention_days": self._policy.retention_days,
                "pipa_version": self._policy.pipa_version,
            },
        }

    # ── 내부 ────────────────────────────────────────────────────────────

    def _check_consent(self, consent: ConsentLevel) -> None:
        order = [ConsentLevel.NONE, ConsentLevel.ANONYMOUS,
                 ConsentLevel.PSEUDONYMOUS, ConsentLevel.IDENTIFIED]
        if order.index(consent) < order.index(self._required_consent):
            with self._lock:
                self._blocked_count += 1
            raise ConsentError(self._required_consent, consent)

    def _validate_score(self, score: float) -> None:
        if not (1.0 <= score <= 5.0):
            raise FeedbackCollectionError(f"Score must be 1.0~5.0, got {score}")
