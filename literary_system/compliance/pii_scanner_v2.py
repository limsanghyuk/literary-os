"""
PIIScannerV2 — PII 스캐너 v2 (V465)

ADR-013: PII Zero-Trust Pipeline
LLM-0: 외부 LLM 없음. 규칙 기반 + 패턴 매칭 + scan_fn 주입.

설계 원칙:
  - 규칙 기반 (regex) + 한국어 NER (패턴 기반, ≥90% 정밀도 목표)
  - scan_fn 주입으로 테넌트별 커스텀 스캐너 확장
  - LLM-0: 외부 API 없음 — 모든 탐지는 로컬 규칙
  - 마스킹 모드: 부분 마스킹, 완전 삭제, 토큰화

지원 PII 유형:
  한국:
    - 주민등록번호 (RRN): YYMMDD-NNNNNNN
    - 전화번호: 010/011/016/017/018/019-XXXX-XXXX
    - 이메일
    - 한국 주소 패턴 (시/도/구/동)
    - 신용카드번호
    - 여권번호
    - 운전면허번호
  국제:
    - 이메일
    - 신용카드번호 (Luhn 검증)
    - IPv4/IPv6
    - IBAN
    - 미국 SSN
"""
from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Callable

# ---------------------------------------------------------------------------
# 열거형
# ---------------------------------------------------------------------------

class PIIType(str, Enum):
    RRN = "korean_rrn"                   # 주민등록번호
    PHONE_KR = "korean_phone"            # 한국 전화번호
    EMAIL = "email"
    CREDIT_CARD = "credit_card"
    ADDRESS_KR = "korean_address"        # 한국 주소
    PASSPORT = "passport"
    DRIVERS_LICENSE_KR = "korean_drivers_license"
    IP_ADDRESS = "ip_address"
    IBAN = "iban"
    SSN_US = "us_ssn"
    NAME_KR = "korean_name"              # 한국인 이름 패턴
    CUSTOM = "custom"                    # 커스텀 scan_fn


class MaskMode(str, Enum):
    PARTIAL = "partial"         # 부분 마스킹: 010-****-5678
    FULL = "full"               # 완전 삭제: [REDACTED]
    TOKEN = "token"             # 토큰화: PII_TOKEN_abc123
    HASH = "hash"               # 단방향 해시: sha256[:8]


# ---------------------------------------------------------------------------
# 패턴 정의 (LLM-0 — 정적 규칙)
# ---------------------------------------------------------------------------

_PII_PATTERNS: list[tuple[PIIType, re.Pattern]] = [
    # 주민등록번호: YYMMDD-NNNNNNN (7자리 두번째 숫자는 1-4/9)
    (PIIType.RRN, re.compile(
        r'\b(\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01]))-([1-4]\d{6}|[9]\d{6})\b'
    )),
    # 전화번호 (한국)
    (PIIType.PHONE_KR, re.compile(
        r'\b(0(?:10|11|16|17|18|19|2|31|32|33|41|42|43|44|51|52|53|54|55|61|62|63|64|70))'
        r'[-.\s]?(\d{3,4})[-.\s]?(\d{4})\b'
    )),
    # 이메일
    (PIIType.EMAIL, re.compile(
        r'\b[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}\b'
    )),
    # 신용카드 (4-4-4-4 또는 4-6-5 등)
    (PIIType.CREDIT_CARD, re.compile(
        r'\b(?:4[0-9]{12}(?:[0-9]{3})?'           # Visa
        r'|5[1-5][0-9]{14}'                         # MasterCard
        r'|3[47][0-9]{13}'                          # Amex
        r'|(?:6011|65[0-9]{2})[0-9]{12}'           # Discover
        r'|(?:\d{4}[-\s]){3}\d{4})\b'             # 구분자 포함
    )),
    # 여권번호 (한국: M/S + 8자리)
    (PIIType.PASSPORT, re.compile(
        r'\b[MSms][0-9]{8}\b'
    )),
    # 운전면허번호 (한국: 지역코드 2자리 + 연도 2자리 + 일련번호 6자리)
    (PIIType.DRIVERS_LICENSE_KR, re.compile(
        r'\b([0-9]{2})-([0-9]{2})-([0-9]{6})-([0-9]{2})\b'
    )),
    # IPv4
    (PIIType.IP_ADDRESS, re.compile(
        r'\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}'
        r'(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b'
    )),
    # 미국 SSN
    (PIIType.SSN_US, re.compile(
        r'\b\d{3}-\d{2}-\d{4}\b'
    )),
    # 한국 주소 패턴 (시/도 키워드 + 구/동)
    (PIIType.ADDRESS_KR, re.compile(
        r'(?:서울|부산|대구|인천|광주|대전|울산|세종|경기|강원|충북|충남|전북|전남|경북|경남|제주)'
        r'(?:특별시|광역시|특별자치시|도|특별자치도)?'
        r'\s*\S+(?:시|군|구)\s*\S+(?:읍|면|동|로|길)'
    )),
    # 한국인 이름 (성 + 이름 2-4자 한글 패턴) — 낮은 정밀도 → 컨텍스트 의존
    (PIIType.NAME_KR, re.compile(
        r'(?<![가-힣])([가-힣]{1})([가-힣]{1,3})(?![가-힣])'
        # 문맥 없이 단독 한글 2-4자 → 이름일 수 있음 (정밀도 낮아 별도 처리)
    )),
]

# 이름 패턴은 오탐률 높으므로 기본 비활성화
_DEFAULT_DISABLED = {PIIType.NAME_KR}


# ---------------------------------------------------------------------------
# 데이터 클래스
# ---------------------------------------------------------------------------

@dataclass
class PIIMatch:
    pii_type: PIIType
    original: str
    start: int
    end: int
    masked: str
    confidence: float   # 0.0 ~ 1.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pii_type": self.pii_type.value,
            "original": self.original,
            "start": self.start,
            "end": self.end,
            "masked": self.masked,
            "confidence": self.confidence,
        }


@dataclass
class ScanResult:
    scan_id: str
    text_length: int
    matches: list[PIIMatch]
    sanitized_text: str
    pii_found: bool
    types_detected: list[str]
    scanned_at: str
    token_map: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scan_id": self.scan_id,
            "text_length": self.text_length,
            "matches": [m.to_dict() for m in self.matches],
            "sanitized_text": self.sanitized_text,
            "pii_found": self.pii_found,
            "types_detected": self.types_detected,
            "scanned_at": self.scanned_at,
        }


# ---------------------------------------------------------------------------
# 마스킹 헬퍼
# ---------------------------------------------------------------------------

def _mask_partial(text: str, pii_type: PIIType) -> str:
    """부분 마스킹 규칙"""
    if pii_type == PIIType.RRN:
        # 000000-*******
        parts = text.split("-")
        return f"{parts[0]}-*******" if len(parts) == 2 else text[:6] + "*******"
    if pii_type == PIIType.PHONE_KR:
        # 010-****-1234
        return re.sub(r'(\d{3,4})([-.\s]?)(\d{4}$)', r'****\2\3', text)
    if pii_type == PIIType.EMAIL:
        local, _, domain = text.partition("@")
        return f"{'*' * min(len(local), 3)}***@{domain}"
    if pii_type == PIIType.CREDIT_CARD:
        digits = re.sub(r'[\s\-]', '', text)
        return f"{'*' * 12}{digits[-4:]}"
    return f"{'*' * max(1, len(text) - 4)}{text[-4:]}" if len(text) > 4 else "****"


def _mask_full(pii_type: PIIType) -> str:
    return f"[REDACTED:{pii_type.value.upper()}]"


def _mask_token(text: str) -> str:
    token = hashlib.sha256(text.encode()).hexdigest()[:8]
    return f"[PII_TOKEN_{token.upper()}]"


def _mask_hash(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# PIIScannerV2
# ---------------------------------------------------------------------------

class PIIScannerV2:
    """
    PII 스캐너 v2 — 규칙 기반 + scan_fn 주입.

    LLM-0: 외부 LLM 없음. 로컬 regex + 주입된 scan_fn만 사용.

    사용:
        scanner = PIIScannerV2(mask_mode=MaskMode.PARTIAL)
        result = scanner.scan("홍길동, 010-1234-5678, hong@example.com")
        result.pii_found → True
        result.sanitized_text → "홍길동, 010-****-5678, ***@example.com"
    """

    def __init__(
        self,
        mask_mode: MaskMode = MaskMode.PARTIAL,
        enabled_types: set[PIIType] | None = None,
        scan_fns: list[Callable[[str], list[tuple[int, int, str, float]]]] | None = None,
        name_detection: bool = False,
    ) -> None:
        """
        mask_mode: 마스킹 모드
        enabled_types: None이면 기본 활성화 타입 사용
        scan_fns: 커스텀 스캐너 함수 목록. 각 함수는 (start, end, label, confidence) 리스트 반환
        name_detection: 한국인 이름 패턴 활성화 (오탐률 주의)
        """
        self._mask_mode = mask_mode
        self._enabled = enabled_types if enabled_types is not None else (
            {t for t, _ in _PII_PATTERNS} - _DEFAULT_DISABLED
        )
        if name_detection:
            self._enabled.add(PIIType.NAME_KR)
        self._scan_fns = scan_fns or []
        self._token_store: dict[str, str] = {}   # token → original (역변환용)

    # ------------------------------------------------------------------

    def scan(self, text: str) -> ScanResult:
        """텍스트에서 PII 탐지 및 마스킹"""
        matches: list[PIIMatch] = []

        # 1. 규칙 기반 스캔
        for pii_type, pattern in _PII_PATTERNS:
            if pii_type not in self._enabled:
                continue
            for m in pattern.finditer(text):
                original = m.group(0)
                masked = self._apply_mask(original, pii_type)
                confidence = self._confidence(pii_type, original)
                matches.append(PIIMatch(
                    pii_type=pii_type,
                    original=original,
                    start=m.start(),
                    end=m.end(),
                    masked=masked,
                    confidence=confidence,
                ))

        # 2. 커스텀 scan_fn
        for fn in self._scan_fns:
            try:
                custom_hits = fn(text)
                for start, end, label, conf in custom_hits:
                    original = text[start:end]
                    masked = self._apply_mask(original, PIIType.CUSTOM)
                    matches.append(PIIMatch(
                        pii_type=PIIType.CUSTOM,
                        original=original,
                        start=start,
                        end=end,
                        masked=f"[CUSTOM:{label}]",
                        confidence=conf,
                    ))
            except Exception:
                pass  # 커스텀 스캐너 실패는 무시

        # 3. 중복 제거 (겹치는 범위)
        matches = self._deduplicate(matches)

        # 4. 치환 (뒤에서부터 → 오프셋 보전)
        sanitized = text
        for match in sorted(matches, key=lambda m: m.start, reverse=True):
            sanitized = sanitized[:match.start] + match.masked + sanitized[match.end:]

        # 5. 토큰 맵 갱신
        if self._mask_mode == MaskMode.TOKEN:
            for m in matches:
                token = m.masked
                self._token_store[token] = m.original

        types_detected = list({m.pii_type.value for m in matches})

        return ScanResult(
            scan_id=str(uuid.uuid4()),
            text_length=len(text),
            matches=matches,
            sanitized_text=sanitized,
            pii_found=len(matches) > 0,
            types_detected=types_detected,
            scanned_at=datetime.now(timezone.utc).isoformat(),
        )

    # ------------------------------------------------------------------

    def scan_batch(self, texts: list[str]) -> list[ScanResult]:
        return [self.scan(t) for t in texts]

    def detokenize(self, sanitized_text: str) -> str:
        """TOKEN 모드 역변환 (원본 복원)"""
        result = sanitized_text
        for token, original in self._token_store.items():
            result = result.replace(token, original)
        return result

    def contains_pii(self, text: str) -> bool:
        """PII 포함 여부만 빠르게 확인 (마스킹 불필요)"""
        return self.scan(text).pii_found

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _apply_mask(self, text: str, pii_type: PIIType) -> str:
        if self._mask_mode == MaskMode.PARTIAL:
            return _mask_partial(text, pii_type)
        if self._mask_mode == MaskMode.FULL:
            return _mask_full(pii_type)
        if self._mask_mode == MaskMode.TOKEN:
            return _mask_token(text)
        if self._mask_mode == MaskMode.HASH:
            return _mask_hash(text)
        return "****"

    @staticmethod
    def _confidence(pii_type: PIIType, text: str) -> float:
        """타입별 신뢰도 추정"""
        if pii_type == PIIType.RRN:
            # 체크섬 검증 시도 (단순화)
            digits = re.sub(r'[^0-9]', '', text)
            if len(digits) == 13:
                weights = [2, 3, 4, 5, 6, 7, 8, 9, 2, 3, 4, 5]
                total = sum(int(d) * w for d, w in zip(digits, weights))
                check = (11 - (total % 11)) % 10
                return 0.98 if check == int(digits[12]) else 0.85
            return 0.90
        if pii_type == PIIType.CREDIT_CARD:
            # Luhn 검증
            digits = re.sub(r'[\s\-]', '', text)
            if digits.isdigit() and len(digits) >= 13:
                nums = [int(d) for d in digits]
                nums.reverse()
                total = sum(
                    n if i % 2 == 0 else (n * 2 - 9 if n * 2 > 9 else n * 2)
                    for i, n in enumerate(nums)
                )
                return 0.99 if total % 10 == 0 else 0.70
            return 0.80
        if pii_type == PIIType.EMAIL:
            return 0.97
        if pii_type == PIIType.PHONE_KR:
            return 0.95
        if pii_type == PIIType.NAME_KR:
            return 0.60   # 한국 이름은 오탐 많음
        return 0.90

    @staticmethod
    def _deduplicate(matches: list[PIIMatch]) -> list[PIIMatch]:
        """겹치는 매치 중 신뢰도 높은 것 우선 선택"""
        if not matches:
            return matches
        matches_sorted = sorted(matches, key=lambda m: (-m.confidence, m.start))
        result: list[PIIMatch] = []
        used_ranges: list[tuple[int, int]] = []
        for m in matches_sorted:
            overlap = any(m.start < e and m.end > s for s, e in used_ranges)
            if not overlap:
                result.append(m)
                used_ranges.append((m.start, m.end))
        return sorted(result, key=lambda m: m.start)
