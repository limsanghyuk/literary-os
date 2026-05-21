"""SP-A.5 (V592) -- test_pii_scrubber.py: TC01-TC15"""
from __future__ import annotations
import sys, os, pytest
_ROOT = os.path.join(os.path.dirname(__file__), "..", "..")
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)
from literary_system.corpus.corpus_pii_filter import CorpusPiiFilter, CorpusPiiMatch
from literary_system.corpus.corpus_ingestor import CorpusEntry


class TestPiiDetect:
    def setup_method(self):
        self.pii = CorpusPiiFilter()

    def test_tc01_detect_ssn(self):
        """TC01: 주민등록번호 탐지"""
        text = "주민번호 850101-1234567 확인"
        matches = self.pii.detect(text)
        assert any(m.pattern_name == "주민등록번호" for m in matches)

    def test_tc02_detect_phone(self):
        """TC02: 전화번호 탐지 -- word boundary 위해 숫자 뒤 공백"""
        text = "연락처: 010-1234-5678 로 문의"
        matches = self.pii.detect(text)
        assert any(m.pattern_name == "전화번호" for m in matches)

    def test_tc03_detect_email(self):
        """TC03: 이메일 주소 탐지"""
        text = "문의: contact@example.com 으로"
        matches = self.pii.detect(text)
        assert any(m.pattern_name == "이메일" for m in matches)

    def test_tc04_detect_no_pii(self):
        """TC04: PII 없는 텍스트 -> 빈 리스트"""
        text = "춘향이와 이도령은 광한루에서 만났습니다."
        assert self.pii.detect(text) == []


class TestPiiScrub:
    def setup_method(self):
        self.pii = CorpusPiiFilter()

    def test_tc05_scrub_ssn(self):
        """TC05: 주민번호 -> [SSN]"""
        result = self.pii.scrub("주민번호 850101-1234567 확인")
        assert "850101-1234567" not in result
        assert "[SSN]" in result

    def test_tc06_scrub_phone(self):
        """TC06: 전화번호 -> [PHONE]"""
        result = self.pii.scrub("전화: 010-9876-5432 ")
        assert "010-9876-5432" not in result
        assert "[PHONE]" in result

    def test_tc07_scrub_email(self):
        """TC07: 이메일 -> [EMAIL]"""
        result = self.pii.scrub("이메일: user@domain.co.kr 로")
        assert "user@domain.co.kr" not in result
        assert "[EMAIL]" in result

    def test_tc08_scrub_email_multi(self):
        """TC08: 이메일 복수 제거"""
        result = self.pii.scrub("a@b.com 과 c@d.org 에 보내라")
        assert "a@b.com" not in result
        assert "c@d.org" not in result

    def test_tc09_scrub_no_pii_unchanged(self):
        """TC09: PII 없는 텍스트는 원문 그대로"""
        text = "고전 소설의 아름다운 문체."
        assert self.pii.scrub(text) == text


class TestPiiClean:
    def setup_method(self):
        self.pii = CorpusPiiFilter()

    def test_tc10_is_clean_true(self):
        """TC10: PII 없음 -> True"""
        assert self.pii.is_clean("조선 시대 한양의 풍경") is True

    def test_tc11_is_clean_false(self):
        """TC11: 이메일 포함 -> False"""
        assert self.pii.is_clean("내 메일은 secret@test.com 입니다") is False

    def test_tc12_filter_entries_strict(self):
        """TC12: strict=True -> PII 포함 항목 제거"""
        pii_strict = CorpusPiiFilter(strict=True)
        entries = [
            CorpusEntry("E1", "깨끗한 텍스트입니다.", "synthetic", "CC-BY-4.0"),
            CorpusEntry("E2", "이메일 dirty@los.com 포함", "synthetic", "CC-BY-4.0"),
            CorpusEntry("E3", "또 다른 깨끗한 텍스트", "synthetic", "CC-BY-4.0"),
        ]
        clean, removed = pii_strict.filter_entries(entries)
        assert len(clean) == 2
        assert removed == 1


class TestPiiSummary:
    def setup_method(self):
        self.pii = CorpusPiiFilter()

    def test_tc13_scan_summary_structure(self):
        """TC13: scan_summary() 구조 확인"""
        entries = [
            CorpusEntry("E1", "깨끗한 텍스트", "public_domain", "public_domain"),
            CorpusEntry("E2", "이메일 test@los.com 포함", "public_domain", "public_domain"),
        ]
        summary = self.pii.scan_summary(entries)
        total_val = summary.get("total") or summary.get("total_entries", 0)
        assert total_val == 2
        dirty_val = summary.get("pii_count") or summary.get("dirty_entries", 0)
        assert dirty_val == 1

    def test_tc14_pii_match_to_dict(self):
        """TC14: CorpusPiiMatch.to_dict() 구조"""
        matches = self.pii.detect("주민번호 900101-1234567 확인")
        assert len(matches) >= 1
        d = matches[0].to_dict()
        for key in ("pattern_name", "matched", "placeholder"):
            assert key in d

    def test_tc15_llm0_compliance(self):
        """TC15: LLM-0 -- 외부 LLM 호출 없음"""
        import inspect
        import literary_system.corpus.corpus_pii_filter as mod
        src = inspect.getsource(mod)
        for pat in ["openai.ChatCompletion", "anthropic.Anthropic", "requests.post"]:
            assert pat not in src, f"LLM-0 위반: {pat}"
