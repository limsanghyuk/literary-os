"""
V443 -- PIIScrubber
PII (Personally Identifiable Information) 마스킹 모듈.

GDPR/PIPA 규정 준수를 위해 훈련 데이터에서 PII를 제거.

지원 PII 유형:
  - 이름 (한국어/영어 패턴)
  - 전화번호 (한국 형식)
  - 이메일
  - 주소 (한국 주소 패턴)
  - 주민등록번호
  - 신용카드 번호

설계 원칙:
  - 마스킹 후 원문 구조 유지 (텍스트 길이 최대한 보존)
  - 각 PII 유형별 플레이스홀더 사용 ([NAME], [PHONE] 등)
  - 감사 로그: 어떤 유형이 몇 개 마스킹됐는지 반환
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

# ---------------------------------------------------------------------------
# Patterns
# ---------------------------------------------------------------------------

# Korean phone: 010-1234-5678, 02-123-4567, 031-1234-5678
_PHONE_KR = re.compile(
    r"\b(?:0\d{1,2})[\s\-]\d{3,4}[\s\-]\d{4}\b"
)

# Email
_EMAIL = re.compile(
    r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"
)

# Korean SSN: 123456-1234567
_SSN_KR = re.compile(
    r"\b\d{6}[\s\-]\d{7}\b"
)

# Credit card: 4 groups of 4 digits
_CREDIT_CARD = re.compile(
    r"\b\d{4}[\s\-]\d{4}[\s\-]\d{4}[\s\-]\d{4}\b"
)

# Korean address keywords
_ADDRESS_KR = re.compile(
    r"[가-힣]{2,}(특별시|광역시|도|시|군|구|읍|면|동|로|길|번지|아파트|빌라|오피스텔)\s*\d*"
)

# Simple Korean name pattern: 2-4 Korean characters following name markers
# Bug-Fix: added (?=[^가-힣]|$) lookahead to prevent over-capture into adjacent Korean chars
_NAME_KR = re.compile(
    r"(?:이름|성함|이름은|성함은)[\s:]+([가-힣]{2,4})(?=[^가-힣]|$)"
)

# English name: Firstname Lastname (capitalized)
_NAME_EN = re.compile(
    r"\b[A-Z][a-z]{2,15}\s+[A-Z][a-z]{2,15}\b"
)

PATTERNS: List[Tuple[str, re.Pattern, str]] = [
    ("ssn",         _SSN_KR,     "[SSN]"),
    ("credit_card", _CREDIT_CARD,"[CARD]"),
    ("phone",       _PHONE_KR,   "[PHONE]"),
    ("email",       _EMAIL,      "[EMAIL]"),
    ("address",     _ADDRESS_KR, "[ADDRESS]"),
    ("name_kr",     _NAME_KR,    "[NAME]"),
    ("name_en",     _NAME_EN,    "[NAME]"),
]


# ---------------------------------------------------------------------------
# ScrubReport
# ---------------------------------------------------------------------------

@dataclass
class ScrubReport:
    """Result of a single scrub operation."""
    original_len:  int
    scrubbed_len:  int
    counts:        Dict[str, int] = field(default_factory=dict)
    total_removed: int = 0

    @property
    def is_clean(self) -> bool:
        return self.total_removed == 0

    def summary(self) -> str:
        if self.is_clean:
            return "clean"
        parts = [f"{k}={v}" for k, v in self.counts.items() if v > 0]
        return "removed: " + ", ".join(parts)


# ---------------------------------------------------------------------------
# PIIScrubber
# ---------------------------------------------------------------------------

class PIIScrubber:
    """
    Regex-based PII masker for Korean literary training data.

    Usage:
        scrubber = PIIScrubber()
        clean_text, report = scrubber.scrub(text)

    To disable specific categories:
        scrubber = PIIScrubber(disabled={"name_en", "address"})
    """

    def __init__(self, disabled: set = None) -> None:
        self._disabled = disabled or set()
        self._active_patterns = [
            (name, pat, placeholder)
            for name, pat, placeholder in PATTERNS
            if name not in self._disabled
        ]

    def scrub(self, text: str) -> Tuple[str, ScrubReport]:
        """
        Scrub PII from text.

        Returns:
            (scrubbed_text, ScrubReport)
        """
        result = text
        counts: Dict[str, int] = {}

        for name, pat, placeholder in self._active_patterns:
            matches = pat.findall(result)
            if matches:
                # For named groups (name_kr), replace captured group too
                if name == "name_kr":
                    def replace_name(m):
                        full = m.group(0)
                        captured = m.group(1)
                        return full.replace(captured, "[NAME]", 1)  # Bug-Fix: limit=1 prevents over-replacement of same name in sentence
                    new_result = pat.sub(replace_name, result)
                else:
                    new_result = pat.sub(placeholder, result)
                count = len(matches)  # Bug-Fix: reuse already-computed matches, avoid second findall
                counts[name] = count
                result = new_result

        total = sum(counts.values())
        return result, ScrubReport(
            original_len=len(text),
            scrubbed_len=len(result),
            counts=counts,
            total_removed=total,
        )

    def scrub_batch(self, texts: List[str]) -> List[Tuple[str, ScrubReport]]:
        """Scrub a list of texts."""
        return [self.scrub(t) for t in texts]

    def is_clean(self, text: str) -> bool:
        """Return True if text contains no detected PII."""
        _, report = self.scrub(text)
        return report.is_clean

    @property
    def active_categories(self) -> List[str]:
        return [name for name, _, _ in self._active_patterns]
