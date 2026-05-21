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


# =============================================================================
# SP-A.6 (V593) — CorpusEntryValidator: CorpusEntry 4단 필터
# (기존 CorpusValidator/ValidationResult/BatchValidationReport는 ScenarioEntry 전용 — 보존)
# =============================================================================

import hashlib
import math
import random
from dataclasses import dataclass, field as dc_field
from typing import Dict, Set

from .corpus_ingestor import CorpusEntry


# ---------------------------------------------------------------------------
# 허용 라이선스 집합 (SP-A.6)
# ---------------------------------------------------------------------------
_ALLOWED_CORPUS_LICENSES: Set[str] = {
    "public_domain",
    "CC-BY-4.0",
    "CC-BY-SA-4.0",
    "CC0",
    "academic",
    "퍼블릭 도메인",
    "협약",
}

_FORBIDDEN_CORPUS_LICENSES: Set[str] = {
    "proprietary",
    "all_rights_reserved",
    "copyright",
    "unknown",
}


# ---------------------------------------------------------------------------
# CorpusEntryValidationResult — 항목별 검증 결과
# ---------------------------------------------------------------------------

@dataclass
class CorpusEntryValidationResult:
    """
    단일 CorpusEntry에 대한 4단 검증 결과.
    (기존 ValidationResult Enum과 별도 — CorpusEntry 전용)
    """
    entry_id:       str
    passed:         bool

    # 단계별 통과/실패
    license_ok:     bool = True
    pii_ok:         bool = True
    drse_ok:        bool = True
    dedup_ok:       bool = True

    # 상세 값
    license:        str  = ""
    drse_score:     float = 0.0
    fail_reason:    str  = ""

    def to_dict(self) -> dict:
        return {
            "entry_id":    self.entry_id,
            "passed":      self.passed,
            "license_ok":  self.license_ok,
            "pii_ok":      self.pii_ok,
            "drse_ok":     self.drse_ok,
            "dedup_ok":    self.dedup_ok,
            "license":     self.license,
            "drse_score":  self.drse_score,
            "fail_reason": self.fail_reason,
        }


# ---------------------------------------------------------------------------
# CorpusEntryValidationReport — 배치 집계 보고서
# ---------------------------------------------------------------------------

@dataclass
class CorpusEntryValidationReport:
    """
    CorpusEntry 배치 검증 집계 보고서.
    (기존 BatchValidationReport는 ScenarioEntry 전용 — 별도 클래스)
    """
    total:          int = 0
    passed:         int = 0
    failed_license: int = 0
    failed_pii:     int = 0
    failed_drse:    int = 0
    failed_dedup:   int = 0
    results:        list = dc_field(default_factory=list)

    @property
    def pass_rate(self) -> float:
        return self.passed / self.total if self.total else 0.0

    def summary(self) -> dict:
        return {
            "total":          self.total,
            "passed":         self.passed,
            "pass_rate":      round(self.pass_rate, 4),
            "failed_license": self.failed_license,
            "failed_pii":     self.failed_pii,
            "failed_drse":    self.failed_drse,
            "failed_dedup":   self.failed_dedup,
        }


# ---------------------------------------------------------------------------
# CorpusMinHashDedup — MinHash 기반 중복 제거
# (기존 DedupReport/DedupStats와 별도 — 코퍼스 전용)
# ---------------------------------------------------------------------------

class CorpusMinHashDedup:
    """
    문자 3-gram 기반 MinHash 유사도를 이용한 코퍼스 중복 감지.
    (기존 slm/trace_quality_filter.py DedupStats / DedupReport와 별도)

    LLM-0 준수: 외부 LLM 호출 없음.
    """

    def __init__(self, num_hashes: int = 16, threshold: float = 0.85) -> None:
        self._num_hashes = num_hashes
        self._threshold  = threshold
        # 해시 파라미터 (선형 해시 a*x+b mod p)
        _p = (1 << 31) - 1
        rng = random.Random(2026)
        self._a = [rng.randint(1, _p - 1) for _ in range(num_hashes)]
        self._b = [rng.randint(0, _p - 1) for _ in range(num_hashes)]
        self._p = _p
        # 저장된 시그니처 목록
        self._sigs: list = []

    def _shingle(self, text: str, k: int = 3) -> Set[int]:
        """문자 k-gram shingle 집합 (정수화).
        BUG-08 fix: Python hash() → hashlib.md5 — PYTHONHASHSEED 무관, 세션 간 재현 가능.
        """
        import hashlib
        text = text.lower()
        return {
            int(hashlib.md5(text[i:i+k].encode("utf-8")).hexdigest(), 16) & 0x7FFFFFFF
            for i in range(len(text) - k + 1)
        }

    def _minhash(self, shingles: Set[int]) -> list:
        """MinHash 시그니처 벡터."""
        sigs = []
        for idx in range(self._num_hashes):
            a, b, p = self._a[idx], self._b[idx], self._p
            min_val = min((a * s + b) % p for s in shingles) if shingles else p
            sigs.append(min_val)
        return sigs

    def _jaccard_estimate(self, sig1: list, sig2: list) -> float:
        """MinHash로 추정한 Jaccard 유사도."""
        matches = sum(1 for x, y in zip(sig1, sig2) if x == y)
        return matches / self._num_hashes

    def is_duplicate(self, text: str) -> bool:
        """
        text가 이미 등록된 항목과 유사도 ≥ threshold이면 True(중복).
        중복이 아니면 시그니처를 저장 후 False 반환.
        """
        shingles = self._shingle(text)
        if not shingles:
            return False
        sig = self._minhash(shingles)
        for prev_sig in self._sigs:
            if self._jaccard_estimate(sig, prev_sig) >= self._threshold:
                return True
        self._sigs.append(sig)
        return False

    def reset(self) -> None:
        """시그니처 저장소 초기화."""
        self._sigs.clear()


# ---------------------------------------------------------------------------
# DRSE S-score 계산 (LLM-0, 순수 텍스트 메트릭)
# ---------------------------------------------------------------------------

# BUG-05 fix: 한국어 기본 조사(가/이/을/를/에서/으로/때) 제거 — DRSE 편향 방지
# 조사는 모든 문장에 등장하므로 내러티브 마커로 부적합 (corpus_validator DRSE +19% 과대평가)
_NARRATIVE_MARKERS = [
    "했다", "였다", "이었다", "라고", "하며", "이며", "하지만", "그러나",
    "그리고", "때문에",
]

_DIALOGUE_MARKERS = ['"', "'", '「', '」', '『', '』', '…', '。']


def _compute_drse_score(text: str) -> float:
    """
    DRSE S-score 근사 (LLM-0 준수, 순수 텍스트 메트릭).

    3개 축 가중합:
      - length_axis (0.40): 단어 수 기반 (20~500단어 최적)
      - vocab_axis  (0.35): 어휘 다양성 (TTR: type/token ratio)
      - narrative_axis (0.25): 내러티브 마커 밀도

    Returns:
        float in [0.0, 1.0]
    """
    words = text.split()
    word_count = len(words)
    if word_count < 5:
        return 0.0

    # 1) length_axis: log-scale, peak at 100 words
    length_score = min(1.0, math.log(word_count + 1) / math.log(101))

    # 2) vocab_axis: unique tokens / total tokens (TTR)
    unique_words = len(set(w.lower().strip(".,!?\"'") for w in words))
    ttr = unique_words / word_count
    vocab_score = min(1.0, ttr * 2)  # scale: TTR 0.5 → 1.0

    # 3) narrative_axis: narrative + dialogue marker density
    text_lower = text.lower()
    nm_hits  = sum(1 for m in _NARRATIVE_MARKERS if m in text_lower)
    dl_hits  = sum(1 for m in _DIALOGUE_MARKERS if m in text)
    density  = (nm_hits + dl_hits) / max(1, word_count / 10)
    narrative_score = min(1.0, density * 0.5)

    score = (0.40 * length_score) + (0.35 * vocab_score) + (0.25 * narrative_score)
    return round(min(1.0, score), 4)


# ---------------------------------------------------------------------------
# CorpusEntryValidator — 4단 필터 파이프라인
# ---------------------------------------------------------------------------

class CorpusEntryValidator:
    """
    SP-A.6 (V593) — CorpusEntry 4단 검증 파이프라인.
    (기존 CorpusValidator(ScenarioEntry 전용)와 별도 — duplicate_zero_g37 준수)

    4단계:
      1. License   — 허용 라이선스 화이트리스트
      2. PII 0건   — CorpusPiiFilter 탐지
      3. DRSE ≥ 0.35 — DRSE S-score 순수 텍스트 메트릭
      4. MinHash dedup(0.85) — 중복 제거

    LLM-0 준수: 외부 LLM 호출 없음.

    Usage::

        validator = CorpusEntryValidator()
        report = validator.validate(entries)
        clean = validator.filter_valid(entries)
        assert report.pass_rate >= 0.90
    """

    def __init__(
        self,
        drse_threshold: float = 0.35,
        dedup_threshold: float = 0.85,
        allowed_licenses: Optional[Set[str]] = None,
        forbidden_licenses: Optional[Set[str]] = None,
    ) -> None:
        from .corpus_pii_filter import CorpusPiiFilter
        self._pii          = CorpusPiiFilter(strict=True)
        self._dedup        = CorpusMinHashDedup(threshold=dedup_threshold)
        self._drse_threshold  = drse_threshold
        self._allowed_lic  = allowed_licenses or _ALLOWED_CORPUS_LICENSES
        self._forbidden_lic = forbidden_licenses or _FORBIDDEN_CORPUS_LICENSES

    def _check_license(self, entry: CorpusEntry) -> bool:
        lic = entry.license.lower().strip()
        # forbidden 우선
        if any(f in lic for f in self._forbidden_lic):
            return False
        # 허용 목록 확인
        for allowed in self._allowed_lic:
            if allowed.lower() in lic:
                return True
        return False

    def validate_entry(self, entry: CorpusEntry) -> CorpusEntryValidationResult:
        """단일 CorpusEntry 4단 검증."""
        result = CorpusEntryValidationResult(
            entry_id=entry.entry_id,
            passed=False,
            license=entry.license,
        )

        # 1단계: License
        if not self._check_license(entry):
            result.license_ok  = False
            result.fail_reason = f"license_rejected: {entry.license}"
            return result

        # 2단계: PII
        if not self._pii.is_clean(entry.text):
            result.pii_ok      = False
            result.fail_reason = "pii_detected"
            return result

        # 3단계: DRSE S-score
        score = _compute_drse_score(entry.text)
        result.drse_score = score
        if score < self._drse_threshold:
            result.drse_ok     = False
            result.fail_reason = f"drse_low: {score:.4f} < {self._drse_threshold}"
            return result

        # 4단계: MinHash 중복
        if self._dedup.is_duplicate(entry.text):
            result.dedup_ok    = False
            result.fail_reason = "duplicate_minhash"
            return result

        result.passed = True
        return result

    def validate(self, entries: List[CorpusEntry]) -> CorpusEntryValidationReport:
        """배치 검증 후 집계 보고서 반환."""
        self._dedup.reset()
        report = CorpusEntryValidationReport(total=len(entries))
        for entry in entries:
            res = self.validate_entry(entry)
            report.results.append(res)
            if res.passed:
                report.passed += 1
            else:
                if not res.license_ok:
                    report.failed_license += 1
                elif not res.pii_ok:
                    report.failed_pii += 1
                elif not res.drse_ok:
                    report.failed_drse += 1
                else:
                    report.failed_dedup += 1
        return report

    def filter_valid(self, entries: List[CorpusEntry]) -> List[CorpusEntry]:
        """검증 통과 항목만 반환."""
        self._dedup.reset()
        valid: List[CorpusEntry] = []
        for entry in entries:
            res = self.validate_entry(entry)
            if res.passed:
                valid.append(entry)
        return valid
