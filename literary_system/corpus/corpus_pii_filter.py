"""
SP-A.5 (V592) — CorpusPiiFilter: 코퍼스 PII 필터링

코퍼스 수집 단계에서 CorpusEntry 텍스트의 PII(개인식별정보)를 탐지·제거.
기존 slm/pii_scrubber.py(PIIScrubber), slm/pii_scrubber_sp3.py(PIIScrubberSP3),
compliance/pii_scanner_v2.py(PIIScannerV2)와 별도 — 코퍼스 수집 전용.

지원 PII 유형:
  - 한국 주민등록번호 (6자리-7자리)
  - 한국 전화번호 (010-XXXX-XXXX 등)
  - 이메일 주소
  - 한국 계좌번호 (은행코드-계좌번호 패턴)

LLM-0 준수: 외부 LLM API 호출 없음. 순수 정규식 기반.
ADR-053 참조.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from literary_system.corpus.corpus_ingestor import CorpusEntry


# ---------------------------------------------------------------------------
# PII 패턴 정의 (코퍼스 전용)
# ---------------------------------------------------------------------------

@dataclass
class CorpusPiiMatch:
    """단일 PII 탐지 결과."""
    pattern_name: str       # PII 유형 이름
    matched:      str       # 탐지된 원문
    start:        int       # 시작 인덱스
    end:          int       # 종료 인덱스
    placeholder:  str       # 대체 텍스트

    def to_dict(self) -> dict:
        return {
            "pattern_name": self.pattern_name,
            "matched":      self.matched,
            "start":        self.start,
            "end":          self.end,
            "placeholder":  self.placeholder,
        }


_CORPUS_PII_PATTERNS = [
    # (이름, 패턴, 플레이스홀더)
    ("주민등록번호", re.compile(r"\b\d{6}[-\s]\d{7}\b"),                "[SSN]"),
    ("전화번호",    re.compile(r"\b01[016789][-\s]\d{3,4}[-\s]\d{4}\b"), "[PHONE]"),
    ("이메일",      re.compile(r"\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b"), "[EMAIL]"),
    ("계좌번호",    re.compile(r"\b\d{3}[-\s]\d{2,6}[-\s]\d{6,}\b"),     "[ACCOUNT]"),
]


# ---------------------------------------------------------------------------
# CorpusPiiFilter
# ---------------------------------------------------------------------------

class CorpusPiiFilter:
    """
    코퍼스 수집 단계 PII 필터링기.
    (기존 PIIScrubber/PIIScrubberSP3/PIIScannerV2와 별도 — 코퍼스 수집 전용)

    Usage::

        flt = CorpusPiiFilter()

        # 단일 텍스트 탐지
        matches = flt.detect("연락처: 010-1234-5678")
        assert len(matches) == 1

        # 단일 텍스트 제거
        clean = flt.scrub("이메일: test@example.com 참조")
        assert "[EMAIL]" in clean

        # 엔트리 필터링
        clean_entries, removed = flt.filter_entries(entries)
    """

    def __init__(self, strict: bool = False) -> None:
        """
        Args:
            strict: True이면 PII 포함 엔트리를 완전 제거.
                    False이면 PII를 플레이스홀더로 대체 후 유지 (기본).
        """
        self._strict = strict

    # ── 텍스트 단위 ─────────────────────────────────────────

    def detect(self, text: str) -> List[CorpusPiiMatch]:
        """PII 패턴 탐지. 발견된 모든 CorpusPiiMatch 반환."""
        matches: List[CorpusPiiMatch] = []
        for name, pattern, placeholder in _CORPUS_PII_PATTERNS:
            for m in pattern.finditer(text):
                matches.append(CorpusPiiMatch(
                    pattern_name = name,
                    matched      = m.group(),
                    start        = m.start(),
                    end          = m.end(),
                    placeholder  = placeholder,
                ))
        # 위치 순 정렬
        matches.sort(key=lambda x: x.start)
        return matches

    def scrub(self, text: str) -> str:
        """PII를 플레이스홀더로 대체한 정제 텍스트 반환."""
        result = text
        # 역순으로 치환 (인덱스 변화 방지)
        matches = self.detect(text)
        for m in reversed(matches):
            result = result[: m.start] + m.placeholder + result[m.end :]
        return result

    def is_clean(self, text: str) -> bool:
        """PII가 없으면 True."""
        return len(self.detect(text)) == 0

    # ── 엔트리 배치 ─────────────────────────────────────────

    def filter_entries(
        self,
        entries: List["CorpusEntry"],
    ) -> tuple:
        """
        CorpusEntry 목록 필터링.

        strict=False (기본): PII 대체 후 엔트리 유지.
        strict=True:         PII 포함 엔트리 제거.

        Returns:
            (clean_entries, removed_count)
        """
        clean: List["CorpusEntry"] = []
        removed = 0

        for entry in entries:
            pii_matches = self.detect(entry.text)
            if not pii_matches:
                clean.append(entry)
                continue

            if self._strict:
                removed += 1
            else:
                # 플레이스홀더 대체 후 유지
                entry.text = self.scrub(entry.text)
                clean.append(entry)

        return clean, removed

    def scan_summary(self, entries: List["CorpusEntry"]) -> dict:
        """
        전체 엔트리 PII 스캔 요약.
        Returns: {total, clean_count, pii_count, by_type}
        """
        total     = len(entries)
        pii_count = 0
        by_type: dict = {}
        for entry in entries:
            matches = self.detect(entry.text)
            if matches:
                pii_count += 1
                for m in matches:
                    by_type[m.pattern_name] = by_type.get(m.pattern_name, 0) + 1
        return {
            "total":       total,
            "clean_count": total - pii_count,
            "pii_count":   pii_count,
            "by_type":     by_type,
        }
