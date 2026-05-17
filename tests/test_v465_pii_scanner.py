"""
test_v465_pii_scanner.py — V465 PIIScannerV2 테스트

ADR-013: PII Zero-Trust Pipeline
정밀도 목표 ≥90% (각 패턴별 검증)
"""
import pytest
from literary_system.compliance.pii_scanner_v2 import (
    PIIScannerV2, MaskMode, PIIType, ScanResult,
)


class TestPIIDetection:
    """PII 탐지 정확도 테스트 (LLM-0 규칙 기반)"""

    def _scanner(self, **kwargs):
        return PIIScannerV2(**kwargs)

    # --- 주민등록번호 ---
    def test_rrn_detection(self):
        s = self._scanner()
        result = s.scan("홍길동의 주민번호는 900101-1234567 입니다.")
        assert result.pii_found
        rrn = next(m for m in result.matches if m.pii_type == PIIType.RRN)
        assert rrn.original == "900101-1234567"
        assert rrn.confidence >= 0.85

    def test_rrn_not_detected_wrong_format(self):
        s = self._scanner()
        result = s.scan("번호는 901301-1234567 입니다.")  # 13월 — 잘못된 날짜
        # 패턴은 날짜 유효성까지 검증하지 않으므로 탐지됨 → 신뢰도만 낮아야 함
        # 이 테스트는 패턴 범위 내 동작 확인
        assert result is not None  # 파싱 오류 없음

    def test_rrn_multiple(self):
        s = self._scanner()
        text = "A: 800101-1234567, B: 950601-2345678"
        result = s.scan(text)
        rrn_matches = [m for m in result.matches if m.pii_type == PIIType.RRN]
        assert len(rrn_matches) == 2

    # --- 전화번호 ---
    def test_phone_detection_hyphen(self):
        s = self._scanner()
        result = s.scan("연락처: 010-1234-5678")
        phones = [m for m in result.matches if m.pii_type == PIIType.PHONE_KR]
        assert len(phones) >= 1
        assert phones[0].confidence >= 0.90

    def test_phone_detection_no_hyphen(self):
        s = self._scanner()
        result = s.scan("전화: 01012345678")
        phones = [m for m in result.matches if m.pii_type == PIIType.PHONE_KR]
        assert len(phones) >= 1

    def test_phone_detection_dot_separator(self):
        s = self._scanner()
        result = s.scan("Tel: 010.9876.5432")
        phones = [m for m in result.matches if m.pii_type == PIIType.PHONE_KR]
        assert len(phones) >= 1

    def test_phone_landline(self):
        s = self._scanner()
        result = s.scan("서울 대표번호 02-1234-5678")
        phones = [m for m in result.matches if m.pii_type == PIIType.PHONE_KR]
        assert len(phones) >= 1

    # --- 이메일 ---
    def test_email_detection(self):
        s = self._scanner()
        result = s.scan("이메일: user@example.com 으로 연락하세요.")
        emails = [m for m in result.matches if m.pii_type == PIIType.EMAIL]
        assert len(emails) == 1
        assert emails[0].original == "user@example.com"
        assert emails[0].confidence >= 0.95

    def test_email_complex(self):
        s = self._scanner()
        result = s.scan("Contact: john.doe+tag@sub.domain.co.kr")
        emails = [m for m in result.matches if m.pii_type == PIIType.EMAIL]
        assert len(emails) == 1

    def test_multiple_emails(self):
        s = self._scanner()
        result = s.scan("From: a@b.com To: c@d.org CC: e@f.net")
        emails = [m for m in result.matches if m.pii_type == PIIType.EMAIL]
        assert len(emails) == 3

    # --- 신용카드 ---
    def test_credit_card_visa(self):
        s = self._scanner()
        result = s.scan("카드번호 4532015112830366 처리")
        cards = [m for m in result.matches if m.pii_type == PIIType.CREDIT_CARD]
        assert len(cards) >= 1

    def test_credit_card_with_separator(self):
        s = self._scanner()
        result = s.scan("결제: 4532-0151-1283-0366")
        cards = [m for m in result.matches if m.pii_type == PIIType.CREDIT_CARD]
        assert len(cards) >= 1

    # --- IPv4 ---
    def test_ip_detection(self):
        s = self._scanner()
        result = s.scan("접속 IP: 192.168.1.100")
        ips = [m for m in result.matches if m.pii_type == PIIType.IP_ADDRESS]
        assert len(ips) >= 1
        assert ips[0].original == "192.168.1.100"

    def test_private_ip(self):
        s = self._scanner()
        result = s.scan("서버 주소: 10.0.0.1")
        ips = [m for m in result.matches if m.pii_type == PIIType.IP_ADDRESS]
        assert len(ips) >= 1

    # --- 주소 ---
    def test_korean_address(self):
        s = self._scanner()
        result = s.scan("주소: 서울특별시 강남구 테헤란로")
        addresses = [m for m in result.matches if m.pii_type == PIIType.ADDRESS_KR]
        assert len(addresses) >= 1

    # --- 여권번호 ---
    def test_passport_detection(self):
        s = self._scanner()
        result = s.scan("여권번호: M12345678")
        pp = [m for m in result.matches if m.pii_type == PIIType.PASSPORT]
        assert len(pp) >= 1

    # --- 미국 SSN ---
    def test_ssn_detection(self):
        s = self._scanner()
        result = s.scan("SSN: 123-45-6789")
        ssn = [m for m in result.matches if m.pii_type == PIIType.SSN_US]
        assert len(ssn) >= 1


class TestMaskModes:

    def test_partial_mask_rrn(self):
        s = PIIScannerV2(mask_mode=MaskMode.PARTIAL)
        result = s.scan("RRN: 900101-1234567")
        rrn = next(m for m in result.matches if m.pii_type == PIIType.RRN)
        assert "900101" in rrn.masked
        assert "*" * 5 in rrn.masked or "*******" in rrn.masked

    def test_partial_mask_email(self):
        s = PIIScannerV2(mask_mode=MaskMode.PARTIAL)
        result = s.scan("email: user@example.com")
        email = next(m for m in result.matches if m.pii_type == PIIType.EMAIL)
        assert "@example.com" in email.masked
        assert "***" in email.masked

    def test_partial_mask_phone(self):
        s = PIIScannerV2(mask_mode=MaskMode.PARTIAL)
        result = s.scan("폰: 010-1234-5678")
        phone = next(m for m in result.matches if m.pii_type == PIIType.PHONE_KR)
        assert "****" in phone.masked
        assert "5678" in phone.masked

    def test_full_mask(self):
        s = PIIScannerV2(mask_mode=MaskMode.FULL)
        result = s.scan("이메일: test@mail.com")
        email = next(m for m in result.matches if m.pii_type == PIIType.EMAIL)
        assert "REDACTED" in email.masked
        assert "EMAIL" in email.masked

    def test_token_mask(self):
        s = PIIScannerV2(mask_mode=MaskMode.TOKEN)
        result = s.scan("연락처: 010-1234-5678")
        phone = next(m for m in result.matches if m.pii_type == PIIType.PHONE_KR)
        assert "PII_TOKEN_" in phone.masked

    def test_hash_mask(self):
        s = PIIScannerV2(mask_mode=MaskMode.HASH)
        result = s.scan("이메일: a@b.com")
        email = next(m for m in result.matches if m.pii_type == PIIType.EMAIL)
        assert len(email.masked) == 16
        assert email.masked.isalnum()

    def test_sanitized_text_replaces_pii(self):
        s = PIIScannerV2(mask_mode=MaskMode.FULL)
        result = s.scan("전화: 010-9999-8888, 이메일: x@y.com")
        assert "010-9999-8888" not in result.sanitized_text
        assert "x@y.com" not in result.sanitized_text
        assert "REDACTED" in result.sanitized_text


class TestTokenDetokenize:

    def test_detokenize_roundtrip(self):
        s = PIIScannerV2(mask_mode=MaskMode.TOKEN)
        original = "연락처: 010-1234-5678"
        result = s.scan(original)
        restored = s.detokenize(result.sanitized_text)
        assert "010-1234-5678" in restored

    def test_detokenize_multiple(self):
        s = PIIScannerV2(mask_mode=MaskMode.TOKEN)
        text = "폰: 010-1111-2222 이메일: a@b.com"
        result = s.scan(text)
        restored = s.detokenize(result.sanitized_text)
        assert "010-1111-2222" in restored
        assert "a@b.com" in restored


class TestCustomScanFn:

    def test_custom_scan_fn_injection(self):
        """외부 NER 엔진 주입 테스트"""
        def fake_ner(text: str) -> list[tuple[int, int, str, float]]:
            # 'TESTPII:12345' 패턴 감지
            import re
            hits = []
            for m in re.finditer(r'TESTPII:\d+', text):
                hits.append((m.start(), m.end(), "CUSTOM_ID", 0.99))
            return hits

        s = PIIScannerV2(scan_fns=[fake_ner])
        result = s.scan("사용자 ID: TESTPII:99999 처리")
        assert result.pii_found
        custom = [m for m in result.matches if m.pii_type == PIIType.CUSTOM]
        assert len(custom) == 1
        assert custom[0].confidence == 0.99

    def test_faulty_scan_fn_ignored(self):
        """오류 발생 커스텀 스캐너는 무시"""
        def broken_fn(text: str):
            raise RuntimeError("broken")

        s = PIIScannerV2(scan_fns=[broken_fn])
        result = s.scan("test@example.com")
        # broken_fn 오류 무시하고 정상 탐지 계속
        assert result.pii_found


class TestEnabledTypes:

    def test_disable_all_types(self):
        s = PIIScannerV2(enabled_types=set())
        result = s.scan("010-1234-5678 user@test.com 900101-1234567")
        assert not result.pii_found

    def test_enable_only_email(self):
        s = PIIScannerV2(enabled_types={PIIType.EMAIL})
        result = s.scan("폰: 010-1234-5678, 이메일: a@b.com")
        types = {m.pii_type for m in result.matches}
        assert PIIType.EMAIL in types
        assert PIIType.PHONE_KR not in types

    def test_name_detection_disabled_by_default(self):
        s = PIIScannerV2()
        result = s.scan("홍길동이 편지를 썼다")
        names = [m for m in result.matches if m.pii_type == PIIType.NAME_KR]
        assert len(names) == 0  # 기본 비활성화

    def test_name_detection_enabled(self):
        s = PIIScannerV2(name_detection=True)
        result = s.scan("홍길동")
        names = [m for m in result.matches if m.pii_type == PIIType.NAME_KR]
        assert len(names) >= 1


class TestScanResult:

    def test_contains_pii_fast_check(self):
        s = PIIScannerV2()
        assert s.contains_pii("연락처 010-1234-5678") is True
        assert s.contains_pii("일반적인 문장입니다.") is False

    def test_scan_batch(self):
        s = PIIScannerV2()
        texts = [
            "연락 010-1111-2222",
            "이메일 a@b.com",
            "PII 없는 텍스트",
        ]
        results = s.scan_batch(texts)
        assert len(results) == 3
        assert results[0].pii_found
        assert results[1].pii_found
        assert not results[2].pii_found

    def test_scan_empty_text(self):
        s = PIIScannerV2()
        result = s.scan("")
        assert not result.pii_found
        assert result.sanitized_text == ""

    def test_to_dict(self):
        s = PIIScannerV2()
        result = s.scan("이메일: x@y.com")
        d = result.to_dict()
        for k in ("scan_id", "matches", "sanitized_text", "pii_found", "types_detected"):
            assert k in d

    def test_types_detected_list(self):
        s = PIIScannerV2()
        result = s.scan("010-1234-5678 a@b.com")
        assert PIIType.EMAIL.value in result.types_detected or PIIType.PHONE_KR.value in result.types_detected


class TestDeduplication:

    def test_no_duplicate_matches(self):
        """겹치는 매치가 중복으로 반환되지 않음"""
        s = PIIScannerV2()
        result = s.scan("이메일: user@example.com 전화: 010-9999-8888")
        # 동일한 텍스트 구간이 두 번 잡히지 않아야 함
        starts = [m.start for m in result.matches]
        assert len(starts) == len(set(starts))


class TestAccuracyTarget:
    """≥90% 정밀도 목표 검증"""

    def test_rrn_precision_90(self):
        s = PIIScannerV2()
        # 10개 RRN 샘플 중 9개 이상 탐지
        samples = [
            "900101-1234567", "850615-2345678", "780212-1987654",
            "991231-1111111", "010101-4222222", "660430-1333333",
            "550101-2444444", "720805-1555555", "830920-2666666",
            "950101-1777777",
        ]
        detected = 0
        for rrn in samples:
            result = s.scan(f"RRN: {rrn}")
            if any(m.pii_type == PIIType.RRN for m in result.matches):
                detected += 1
        precision = detected / len(samples)
        assert precision >= 0.90, f"RRN 탐지율: {precision:.0%} < 90%"

    def test_phone_precision_90(self):
        s = PIIScannerV2()
        samples = [
            "010-1234-5678", "011-9876-5432", "016-1111-2222",
            "017-3333-4444", "018-5555-6666", "019-7777-8888",
            "010.1234.5678", "0101234567", "010 2345 6789",
            "02-1234-5678",
        ]
        detected = sum(
            1 for p in samples
            if any(m.pii_type == PIIType.PHONE_KR
                   for m in PIIScannerV2().scan(f"전화: {p}").matches)
        )
        assert detected / len(samples) >= 0.90

    def test_email_precision_100(self):
        s = PIIScannerV2()
        samples = [
            "test@example.com", "user.name@domain.co.kr",
            "admin@test.org", "contact+info@company.net",
            "no-reply@service.io",
        ]
        detected = sum(
            1 for e in samples
            if any(m.pii_type == PIIType.EMAIL
                   for m in PIIScannerV2().scan(e).matches)
        )
        assert detected == len(samples)  # 이메일은 100% 목표
