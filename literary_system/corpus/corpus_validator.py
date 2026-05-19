"""
literary_system/corpus/corpus_validator.py  — V558
CorpusValidator: 라이선스·PII·품질 검증 + 마스킹
LLM-0 정책(ADR-015/031): 외부 LLM 호출 없음
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Tuple

from .corpus_ingestor import ScenarioEntry


class ValidationResult(Enum):
    PASS    = "pass"
    FAIL_LICENSE = "fail_license"
    FAIL_PII     = "fail_pii"
    FAIL_QUALITY = "fail_quality"


ALLOWED_LICENSES = {"CC-BY-4.0", "CC-BY-SA-4.0", "CC0", "협약", "퍼블릭 도메인"}

# PII 정규식 패턴
_PII_PATTERNS = {
    "주민번호": re.compile(r"\d{6}-\d{7}"),
    "전화번호": re.compile(r"0\d{1,2}-\d{3,4}-\d{4}"),
    "이메일":   re.compile(r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"),
}

MIN_WORD_COUNT = 10
MAX_WORD_COUNT = 5_000


@dataclass
class BatchValidationReport:
    total: int
    passed: int
    failed_license: int
    failed_pii: int
    failed_quality: int

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0


class CorpusValidator:
    """
    단일/배치 ScenarioEntry 검증기.
    - 라이선스 화이트리스트 검사
    - PII 감지 및 마스킹
    - 최소/최대 단어 수 품질 필터
    """

    def validate_entry(
        self, entry: ScenarioEntry
    ) -> Tuple[ValidationResult, ScenarioEntry]:
        """단일 항목 검증. (결과, 마스킹된 항목) 반환."""
        # 1. 라이선스 체크
        if entry.license not in ALLOWED_LICENSES:
            return ValidationResult.FAIL_LICENSE, entry

        # 2. PII 감지 및 마스킹
        masked_content = entry.content
        pii_found = False
        for label, pat in _PII_PATTERNS.items():
            if pat.search(masked_content):
                pii_found = True
                masked_content = pat.sub(f"[{label}_MASKED]", masked_content)

        if pii_found:
            masked_entry = ScenarioEntry(
                scene_id    = entry.scene_id,
                title       = entry.title,
                genre       = entry.genre,
                characters  = entry.characters,
                content     = masked_content,
                license     = entry.license,
                source      = entry.source,
                episode     = entry.episode,
                scene_index = entry.scene_index,
            )
            return ValidationResult.FAIL_PII, masked_entry

        # 3. 품질 필터 (단어 수)
        word_count = len(entry.content.split())
        if word_count < MIN_WORD_COUNT or word_count > MAX_WORD_COUNT:
            return ValidationResult.FAIL_QUALITY, entry

        return ValidationResult.PASS, entry

    def validate_batch(
        self, entries: List[ScenarioEntry]
    ) -> Tuple[List[ScenarioEntry], BatchValidationReport]:
        """배치 검증. (합격 항목 리스트, 리포트) 반환."""
        passed: List[ScenarioEntry] = []
        fl = fp = fq = 0

        for entry in entries:
            result, processed = self.validate_entry(entry)
            if result == ValidationResult.PASS:
                passed.append(processed)
            elif result == ValidationResult.FAIL_LICENSE:
                fl += 1
            elif result == ValidationResult.FAIL_PII:
                fp += 1
            else:
                fq += 1

        report = BatchValidationReport(
            total           = len(entries),
            passed          = len(passed),
            failed_license  = fl,
            failed_pii      = fp,
            failed_quality  = fq,
        )
        return passed, report
