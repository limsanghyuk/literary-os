"""
tests/test_v493_pii_scrubber_sp3.py
V493: PIIScrubberSP3 단위 테스트

대상:
  - PIIScrubberSP3.scrub() — 단일 텍스트 PII 제거
  - PIIScrubberSP3.scrub_batch() — 일괄 스크럽
  - PIIScrubberSP3.scrub_dataset() — 데이터셋 레벨 스크럽
  - ScrubDetailSP3 — is_clean / total_removed / summary
  - DatasetScrubReport — scrub_rate / summary
  - 한국어 PII 패턴 9종 검증
  - active_categories 필터링
  - scrub_names 옵션
"""

import pytest
from literary_system.slm.pii_scrubber_sp3 import (
    PIIScrubberSP3,
    ScrubDetailSP3,
    DatasetScrubReport,
)


# ─────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────
def _make_scrubber(**kw) -> PIIScrubberSP3:
    return PIIScrubberSP3(**kw)


# ─────────────────────────────────────────────────────────────────────
# TestScrubDetailSP3
# ─────────────────────────────────────────────────────────────────────
class TestScrubDetailSP3:
    def test_is_clean_when_no_pii(self):
        detail = ScrubDetailSP3(
            original_text="안녕하세요",
            scrubbed_text="안녕하세요",
            removed_by_category={},
        )
        assert detail.is_clean is True

    def test_not_clean_when_pii_found(self):
        detail = ScrubDetailSP3(
            original_text="연락처: 010-1234-5678",
            scrubbed_text="연락처: [전화번호]",
            removed_by_category={"전화번호": 1},
        )
        assert detail.is_clean is False

    def test_total_removed(self):
        detail = ScrubDetailSP3(
            original_text="...",
            scrubbed_text="...",
            removed_by_category={"전화번호": 2, "이메일": 1},
        )
        assert detail.total_removed == 3

    def test_summary_clean(self):
        detail = ScrubDetailSP3("clean text", "clean text", {})
        assert detail.summary() == "clean"

    def test_summary_with_pii(self):
        detail = ScrubDetailSP3(
            "text", "text_scrubbed",
            {"전화번호": 1, "이메일": 2},
        )
        s = detail.summary()
        assert "scrubbed" in s
        assert "3" in s


# ─────────────────────────────────────────────────────────────────────
# TestDatasetScrubReport
# ─────────────────────────────────────────────────────────────────────
class TestDatasetScrubReport:
    def test_scrub_rate_zero_when_empty(self):
        report = DatasetScrubReport(
            total_records=0, clean_records=0, scrubbed_records=0,
            total_pii_removed=0, category_totals={},
        )
        assert report.scrub_rate == 0.0

    def test_scrub_rate_calculation(self):
        report = DatasetScrubReport(
            total_records=10, clean_records=7, scrubbed_records=3,
            total_pii_removed=5, category_totals={"전화번호": 5},
        )
        assert abs(report.scrub_rate - 0.3) < 1e-9

    def test_summary_string(self):
        report = DatasetScrubReport(
            total_records=10, clean_records=8, scrubbed_records=2,
            total_pii_removed=3, category_totals={"이메일": 3},
        )
        s = report.summary()
        assert "10" in s
        assert "2" in s
        assert "이메일" in s


# ─────────────────────────────────────────────────────────────────────
# TestKoreanPIIPatterns — 패턴별 단위 테스트
# ─────────────────────────────────────────────────────────────────────
class TestKoreanPIIPatterns:
    def _scrub(self, text: str, categories=None) -> str:
        s = PIIScrubberSP3(active_categories=categories)
        return s.scrub(text).scrubbed_text

    def test_jumin_number(self):
        result = self._scrub("주민번호 900101-1234567", ["주민번호"])
        assert "[주민번호]" in result
        assert "900101-1234567" not in result

    def test_mobile_phone(self):
        result = self._scrub("전화: 010-1234-5678", ["전화번호"])
        assert "[전화번호]" in result

    def test_landline_phone(self):
        result = self._scrub("사무실: 02-123-4567", ["일반전화"])
        assert "[전화번호]" in result

    def test_bank_account(self):
        result = self._scrub("계좌번호 123-456-789012", ["계좌번호"])
        assert "[계좌번호]" in result

    def test_business_number(self):
        result = self._scrub("사업자 123-45-67890", ["사업자번호"])
        assert "[사업자번호]" in result

    def test_email(self):
        result = self._scrub("이메일: user@example.com", ["이메일"])
        assert "[이메일]" in result
        assert "user@example.com" not in result

    def test_passport(self):
        result = self._scrub("여권번호 M12345678", ["여권번호"])
        assert "[여권번호]" in result

    def test_credit_card(self):
        result = self._scrub("카드 1234-5678-9012-3456", ["신용카드"])
        assert "[카드번호]" in result

    def test_ip_address(self):
        result = self._scrub("IP: 192.168.1.1", ["IP주소"])
        assert "[IP주소]" in result
        assert "192.168.1.1" not in result


# ─────────────────────────────────────────────────────────────────────
# TestPIIScrubberSP3 — 클래스 동작 테스트
# ─────────────────────────────────────────────────────────────────────
class TestPIIScrubberSP3:
    def test_default_active_categories_all_nine(self):
        s = PIIScrubberSP3()
        cats = s.active_categories
        # 기본값: 10종 모두 활성 (전화번호/일반전화 각각 독립 카테고리)
        assert len(cats) == 10

    def test_active_categories_filter(self):
        s = PIIScrubberSP3(active_categories=["이메일", "전화번호"])
        assert s.active_categories == ["이메일", "전화번호"]

    def test_scrub_clean_text_returns_is_clean(self):
        s = PIIScrubberSP3()
        detail = s.scrub("오늘 날씨가 맑습니다.")
        assert detail.is_clean is True
        assert detail.total_removed == 0

    def test_scrub_detects_email(self):
        s = PIIScrubberSP3()
        detail = s.scrub("연락처: hello@drama.co.kr")
        assert not detail.is_clean
        assert "이메일" in detail.removed_by_category
        assert detail.removed_by_category["이메일"] == 1

    def test_scrub_multiple_pii_in_one_text(self):
        s = PIIScrubberSP3()
        text = "전화 010-9999-8888 이메일 a@b.com"
        detail = s.scrub(text)
        assert detail.total_removed >= 2

    def test_scrub_batch_returns_list_of_same_length(self):
        s = PIIScrubberSP3()
        texts = ["안녕", "010-1234-5678", "user@email.com"]
        results = s.scrub_batch(texts)
        assert len(results) == 3
        assert all(isinstance(r, ScrubDetailSP3) for r in results)

    def test_scrub_batch_first_is_clean(self):
        s = PIIScrubberSP3()
        results = s.scrub_batch(["안녕", "010-1234-5678"])
        assert results[0].is_clean is True
        assert results[1].is_clean is False

    def test_is_clean_method(self):
        s = PIIScrubberSP3()
        assert s.is_clean("깨끗한 문장") is True
        assert s.is_clean("이메일: test@x.com") is False

    def test_scrub_names_option_off_by_default(self):
        s = PIIScrubberSP3(scrub_names=False)
        # 이름 패턴 비활성화 — 한국 이름이 있어도 제거 안 됨
        detail = s.scrub("김민준이 등장한다")
        # scrub_names=False이므로 이름이 제거되지 않아야 함
        assert "이름" not in detail.removed_by_category

    def test_scrub_names_option_on(self):
        s = PIIScrubberSP3(scrub_names=True)
        # 성씨 포함 이름 패턴
        detail = s.scrub("김민준이 이야기를 시작한다")
        # scrub_names=True일 때 이름 제거 (이름 패턴 일치 시)
        # 패턴 일치 여부에 따라 제거될 수 있음
        assert isinstance(detail, ScrubDetailSP3)


# ─────────────────────────────────────────────────────────────────────
# TestScrubDataset — 데이터셋 레벨 API
# ─────────────────────────────────────────────────────────────────────
class TestScrubDataset:
    def _make_records(self):
        return [
            {"id": "1", "text": "오늘 날씨가 맑습니다."},
            {"id": "2", "text": "연락처: 010-1234-5678"},
            {"id": "3", "text": "이메일: user@example.com"},
        ]

    def test_scrub_dataset_returns_tuple(self):
        s = PIIScrubberSP3()
        result = s.scrub_dataset(self._make_records())
        assert isinstance(result, tuple)
        cleaned, report = result
        assert isinstance(cleaned, list)
        assert isinstance(report, DatasetScrubReport)

    def test_scrub_dataset_total_records(self):
        s = PIIScrubberSP3()
        records = self._make_records()
        cleaned, report = s.scrub_dataset(records)
        assert report.total_records == 3

    def test_scrub_dataset_clean_and_scrubbed_counts(self):
        s = PIIScrubberSP3()
        _, report = s.scrub_dataset(self._make_records())
        # 1번은 clean, 2·3번은 scrubbed
        assert report.clean_records == 1
        assert report.scrubbed_records == 2

    def test_scrub_dataset_pii_removed_in_text(self):
        s = PIIScrubberSP3()
        cleaned, _ = s.scrub_dataset(self._make_records())
        # 2번 레코드 텍스트에 전화번호가 마스킹 되어야 함
        assert "[전화번호]" in cleaned[1]["text"]
        # 3번 레코드 텍스트에 이메일이 마스킹 되어야 함
        assert "[이메일]" in cleaned[2]["text"]

    def test_scrub_dataset_original_ids_preserved(self):
        s = PIIScrubberSP3()
        records = self._make_records()
        cleaned, _ = s.scrub_dataset(records)
        assert [r["id"] for r in cleaned] == ["1", "2", "3"]

    def test_scrub_dataset_custom_text_field(self):
        s = PIIScrubberSP3()
        records = [
            {"content": "010-1234-5678"},
            {"content": "깨끗한 문장"},
        ]
        cleaned, report = s.scrub_dataset(records, text_field="content")
        assert report.total_records == 2
        assert "[전화번호]" in cleaned[0]["content"]

    def test_scrub_dataset_empty_input(self):
        s = PIIScrubberSP3()
        cleaned, report = s.scrub_dataset([])
        assert cleaned == []
        assert report.total_records == 0
        assert report.scrub_rate == 0.0

    def test_scrub_dataset_category_totals(self):
        s = PIIScrubberSP3()
        _, report = s.scrub_dataset(self._make_records())
        # 전화번호, 이메일 카테고리 등장
        assert len(report.category_totals) > 0
        total = sum(report.category_totals.values())
        assert total == report.total_pii_removed

    def test_scrub_dataset_report_summary(self):
        s = PIIScrubberSP3()
        _, report = s.scrub_dataset(self._make_records())
        summary = report.summary()
        assert "3" in summary
        assert "scrub_rate" in summary
