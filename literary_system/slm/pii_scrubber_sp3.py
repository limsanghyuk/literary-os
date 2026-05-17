"""
literary_system/slm/pii_scrubber_sp3.py
V493: PIIScrubber SP3 확장 레이어

기존 PIIScrubber를 확장하여:
  - 한국어 PII 패턴 강화 (주민번호, 전화번호, 이름, 계좌번호)
  - 데이터셋 레벨 batch scrub API
  - ScrubStatsSP3 상세 통계
  - ADR-008 준수 리포트 생성
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── PII 패턴 정의 (한국어 + 국제) ─────────────────────────────────────
_PATTERNS: Dict[str, Tuple[re.Pattern, str]] = {
    # ── 국제 PII (특이 형식 우선) ─────────────────────────────────────
    "이메일":      (re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}'), '[이메일]'),
    "여권번호":    (re.compile(r'\b[A-Z]{1,2}\d{7,9}\b'), '[여권번호]'),
    # 신용카드: 4-4-4-4 패턴 → 계좌번호보다 반드시 먼저 적용 (B1 수정)
    "신용카드":    (re.compile(r'\b(?:\d{4}[-\s]){3}\d{4}\b'), '[카드번호]'),
    "IP주소":      (re.compile(r'\b(?:\d{1,3}\.){3}\d{1,3}\b'), '[IP주소]'),
    # ── 한국어 PII ────────────────────────────────────────────────────
    "주민번호":    (re.compile(r'\d{6}-[1-4]\d{6}'), '[주민번호]'),
    "전화번호":    (re.compile(r'01[016789]-?\d{3,4}-?\d{4}'), '[전화번호]'),
    "일반전화":    (re.compile(r'0\d{1,2}-\d{3,4}-\d{4}'), '[전화번호]'),
    "사업자번호":  (re.compile(r'\b\d{3}-\d{2}-\d{5}\b'), '[사업자번호]'),
    # 계좌번호: 신용카드 처리 이후 적용
    "계좌번호":    (re.compile(r'\d{3,6}-\d{2,6}-\d{4,9}(?:-\d{2,3})?'), '[계좌번호]'),
    "우편번호":    (re.compile(r'\b\d{5}\b'), '[우편번호]'),
}

# 이름 패턴 (한국 성씨 + 2~4자 이름) — 문맥 의존적이므로 선택적
_KR_NAME_PATTERN = re.compile(
    r'(?:김|이|박|최|정|강|조|윤|장|임|오|한|서|권|황|안|송|류|전|홍|고|문|양|손|배|백|허|노|심|하|신|주|나|진|유|엄|채|원|차|명|천|방|공|현|함|변|염|여|추|도|소|석|선|설|마|길|주|연|방)(?:[가-힣]{1,3})\b'
)


# ── 결과 타입 ─────────────────────────────────────────────────────────
@dataclass
class ScrubDetailSP3:
    """단일 레코드 스크럽 결과."""
    original_text:  str
    scrubbed_text:  str
    removed_by_category: Dict[str, int] = field(default_factory=dict)

    @property
    def is_clean(self) -> bool:
        return self.original_text == self.scrubbed_text

    @property
    def total_removed(self) -> int:
        return sum(self.removed_by_category.values())

    def summary(self) -> str:
        if self.is_clean:
            return "clean"
        cats = ", ".join(f"{k}:{v}" for k, v in self.removed_by_category.items() if v > 0)
        return f"scrubbed ({self.total_removed}개: {cats})"


@dataclass
class DatasetScrubReport:
    """데이터셋 레벨 스크럽 통계."""
    total_records:       int
    clean_records:       int
    scrubbed_records:    int
    total_pii_removed:   int
    category_totals:     Dict[str, int] = field(default_factory=dict)

    @property
    def scrub_rate(self) -> float:
        if self.total_records == 0:
            return 0.0
        return self.scrubbed_records / self.total_records

    def summary(self) -> str:
        cats = ", ".join(f"{k}:{v}" for k, v in self.category_totals.items() if v > 0)
        return (f"Dataset scrub: {self.total_records}건 중 {self.scrubbed_records}건 수정 "
                f"(scrub_rate={self.scrub_rate:.1%}) | 총 제거 {self.total_pii_removed}개 "
                f"[{cats}]")


# ── 핵심 클래스 ───────────────────────────────────────────────────────
class PIIScrubberSP3:
    """
    SP3 SLM 수출용 PII 스크러버.

    기존 PIIScrubber 대비 추가사항:
      - 한국어 PII 패턴 9종
      - 카테고리별 제거 통계
      - 데이터셋 레벨 scrub_dataset() API
      - ADR-008 준수 DatasetScrubReport
    """

    def __init__(
        self,
        active_categories: Optional[List[str]] = None,
        scrub_names: bool = False,
    ) -> None:
        if active_categories is None:
            self._active = set(_PATTERNS.keys())
        else:
            self._active = set(active_categories)
        self._scrub_names = scrub_names

    @property
    def active_categories(self) -> List[str]:
        return sorted(self._active)

    def scrub(self, text: str) -> ScrubDetailSP3:
        """단일 텍스트 PII 제거."""
        result = text
        removed_by_cat: Dict[str, int] = {}

        for cat, (pat, repl) in _PATTERNS.items():
            if cat not in self._active:
                continue
            matches = pat.findall(result)
            if matches:
                removed_by_cat[cat] = len(matches)
                result = pat.sub(repl, result)

        if self._scrub_names:
            matches = _KR_NAME_PATTERN.findall(result)
            if matches:
                removed_by_cat["이름"] = len(matches)
                result = _KR_NAME_PATTERN.sub('[이름]', result)

        return ScrubDetailSP3(
            original_text=text,
            scrubbed_text=result,
            removed_by_category=removed_by_cat,
        )

    def scrub_batch(self, texts: List[str]) -> List[ScrubDetailSP3]:
        """텍스트 리스트 일괄 스크럽."""
        return [self.scrub(t) for t in texts]

    def scrub_dataset(
        self,
        records: List[Dict[str, Any]],
        text_field: str = "text",
    ) -> Tuple[List[Dict[str, Any]], DatasetScrubReport]:
        """
        dict 레코드 리스트에서 text_field를 스크럽한 뒤
        (cleaned_records, DatasetScrubReport) 반환.
        """
        cleaned: List[Dict[str, Any]] = []
        total_pii = 0
        category_totals: Dict[str, int] = {}
        scrubbed_count = 0

        for rec in records:
            text = str(rec.get(text_field, ""))
            detail = self.scrub(text)
            new_rec = dict(rec)
            new_rec[text_field] = detail.scrubbed_text
            if not detail.is_clean:
                scrubbed_count += 1
                total_pii += detail.total_removed
                for cat, cnt in detail.removed_by_category.items():
                    category_totals[cat] = category_totals.get(cat, 0) + cnt
            cleaned.append(new_rec)

        report = DatasetScrubReport(
            total_records=len(records),
            clean_records=len(records) - scrubbed_count,
            scrubbed_records=scrubbed_count,
            total_pii_removed=total_pii,
            category_totals=category_totals,
        )
        return cleaned, report

    def is_clean(self, text: str) -> bool:
        """PII 없으면 True."""
        return self.scrub(text).is_clean
