"""
V488 -- TenantIsolationV2

기존 TenantIsolation(qdrant_bridge.py 내장)을 확장.
테넌트별 RAG 인덱스 격리 강화 + KMS 키 추상화 + DataRightsAPI v2 연동.

설계:
  TenantIsolationV2  -- 테넌트 RAG 인덱스 네임스페이싱 + KMS 키 분리
  KMSKeyManager      -- 테넌트별 AES-256 키 추상화 (실제 KMS 없이 HMAC 기반)
  DataHygieneFilter  -- ADR-008: PII·품질·옵트인·라이선스 4단 필터
  TenantRAGRegistry  -- 테넌트별 인덱스 등록·조회·격리 검증
"""
from __future__ import annotations

import hashlib
import hmac
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set


# ---------------------------------------------------------------------------
# KMS 키 관리
# ---------------------------------------------------------------------------

class KMSKeyManager:
    """
    테넌트별 HMAC-SHA256 기반 데이터 키 추상화.
    실제 KMS(AWS KMS, Azure Key Vault 등) 연동 전 로컬 fallback.
    """
    _MASTER_SECRET = b"literary_os_kms_v2_master"  # 실 운영 시 환경변수 주입

    def __init__(self) -> None:
        self._key_cache: Dict[str, bytes] = {}

    def derive_key(self, tenant_id: str) -> bytes:
        """테넌트 전용 32바이트 데이터 키 파생 (결정론적)."""
        if tenant_id in self._key_cache:
            return self._key_cache[tenant_id]
        key = hmac.new(
            self._MASTER_SECRET,
            tenant_id.encode("utf-8"),
            hashlib.sha256,
        ).digest()
        self._key_cache[tenant_id] = key
        return key

    def key_id(self, tenant_id: str) -> str:
        """키 식별자 (16진수 앞 8바이트)."""
        return self.derive_key(tenant_id).hex()[:16]

    def rotate(self, tenant_id: str, new_secret: bytes) -> str:
        """키 회전 (기존 키 무효화 후 신규 키 생성)."""
        key = hmac.new(new_secret, tenant_id.encode("utf-8"), hashlib.sha256).digest()
        self._key_cache[tenant_id] = key
        return key.hex()[:16]


# ---------------------------------------------------------------------------
# ADR-008: Data Hygiene 4단 필터
# ---------------------------------------------------------------------------

class DataHygieneViolation(Enum):
    PII_DETECTED       = "pii_detected"
    QUALITY_TOO_LOW    = "quality_too_low"
    OPT_IN_REQUIRED    = "opt_in_required"
    LICENSE_VIOLATION  = "license_violation"


@dataclass
class HygieneResult:
    passed:     bool
    violations: List[DataHygieneViolation] = field(default_factory=list)
    metadata:   Dict[str, Any]             = field(default_factory=dict)

    @property
    def violation_codes(self) -> List[str]:
        return [v.value for v in self.violations]


class DataHygieneFilter:
    """
    ADR-008: Training Data Hygiene — PII·품질·옵트인·라이선스 4단 필터.
    """
    # PII 패턴 (간소화 — 실 운영은 PIIScannerV2 위임)
    _PII_PATTERNS = ["주민번호", "전화번호", "이메일", "계좌번호", "여권번호"]

    def __init__(
        self,
        min_quality_score:   float = 0.3,
        require_opt_in:      bool  = True,
        allowed_licenses:    Optional[Set[str]] = None,
    ) -> None:
        self._min_quality      = min_quality_score
        self._require_opt_in   = require_opt_in
        self._allowed_licenses = allowed_licenses or {"cc-by", "cc0", "public-domain", "internal"}

    def check(
        self,
        text:          str,
        quality_score: float = 1.0,
        opt_in:        bool  = True,
        license_type:  str   = "internal",
    ) -> HygieneResult:
        """4단 필터 통과 여부 반환."""
        violations: List[DataHygieneViolation] = []

        # 1. PII 검사
        text_lower = text.lower()
        if any(p in text_lower for p in self._PII_PATTERNS):
            violations.append(DataHygieneViolation.PII_DETECTED)

        # 2. 품질 점수
        if quality_score < self._min_quality:
            violations.append(DataHygieneViolation.QUALITY_TOO_LOW)

        # 3. 옵트인
        if self._require_opt_in and not opt_in:
            violations.append(DataHygieneViolation.OPT_IN_REQUIRED)

        # 4. 라이선스
        if license_type not in self._allowed_licenses:
            violations.append(DataHygieneViolation.LICENSE_VIOLATION)

        return HygieneResult(
            passed=len(violations) == 0,
            violations=violations,
            metadata={
                "quality_score": quality_score,
                "opt_in":        opt_in,
                "license_type":  license_type,
            },
        )


# ---------------------------------------------------------------------------
# TenantIsolationV2
# ---------------------------------------------------------------------------

@dataclass
class TenantRAGConfig:
    """테넌트별 RAG 인덱스 설정."""
    tenant_id:         str
    collection_prefix: str
    kms_key_id:        str
    max_docs:          int   = 100_000
    created_at:        float = field(default_factory=time.time)
    metadata:          Dict[str, Any] = field(default_factory=dict)

    def collection_name(self, base: str) -> str:
        """테넌트 격리된 컬렉션 이름 반환."""
        return f"{self.collection_prefix}_{base}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tenant_id":         self.tenant_id,
            "collection_prefix": self.collection_prefix,
            "kms_key_id":        self.kms_key_id,
            "max_docs":          self.max_docs,
            "created_at":        self.created_at,
        }


class TenantRAGRegistry:
    """테넌트별 RAG 인덱스 등록·격리 검증."""

    def __init__(self, kms: Optional[KMSKeyManager] = None) -> None:
        self._kms: KMSKeyManager = kms or KMSKeyManager()
        self._registry: Dict[str, TenantRAGConfig] = {}

    def register(
        self,
        tenant_id: str,
        max_docs:  int = 100_000,
        **meta: Any,
    ) -> TenantRAGConfig:
        """테넌트 등록 (이미 존재하면 기존 설정 반환)."""
        if tenant_id in self._registry:
            return self._registry[tenant_id]

        key_id = self._kms.key_id(tenant_id)
        cfg = TenantRAGConfig(
            tenant_id=tenant_id,
            collection_prefix=f"t_{hashlib.md5(tenant_id.encode()).hexdigest()[:8]}",
            kms_key_id=key_id,
            max_docs=max_docs,
            metadata=dict(meta),
        )
        self._registry[tenant_id] = cfg
        return cfg

    def get(self, tenant_id: str) -> Optional[TenantRAGConfig]:
        return self._registry.get(tenant_id)

    def verify_isolation(self, tenant_a: str, tenant_b: str) -> bool:
        """두 테넌트의 컬렉션 prefix가 다름을 보장한다."""
        cfg_a = self._registry.get(tenant_a)
        cfg_b = self._registry.get(tenant_b)
        if cfg_a is None or cfg_b is None:
            return False
        return cfg_a.collection_prefix != cfg_b.collection_prefix

    def list_tenants(self) -> List[str]:
        return list(self._registry.keys())

    @property
    def tenant_count(self) -> int:
        return len(self._registry)


class TenantIsolationV2:
    """
    RAG 인덱스 테넌트 격리 강화 (V488).

    기존 TenantIsolation(per-collection naming)을 확장:
    - KMS 키 분리
    - DataHygieneFilter 통합 (ADR-008)
    - TenantRAGRegistry로 테넌트 라이프사이클 관리

    사용법:
        iso = TenantIsolationV2()
        iso.register_tenant("tenant_42")
        col = iso.collection_name("tenant_42", "drama_scenes")
        # → "t_a3f2b1c4_drama_scenes"
    """

    def __init__(
        self,
        kms:     Optional[KMSKeyManager]    = None,
        hygiene: Optional[DataHygieneFilter] = None,
    ) -> None:
        self._kms     = kms or KMSKeyManager()
        self._hygiene = hygiene or DataHygieneFilter()
        self._registry = TenantRAGRegistry(kms=self._kms)

    # ------------------------------------------------------------------
    def register_tenant(self, tenant_id: str, **meta: Any) -> TenantRAGConfig:
        return self._registry.register(tenant_id, **meta)

    def collection_name(self, tenant_id: str, base_collection: str) -> str:
        cfg = self._registry.get(tenant_id)
        if cfg is None:
            # 자동 등록
            cfg = self._registry.register(tenant_id)
        return cfg.collection_name(base_collection)

    def kms_key_id(self, tenant_id: str) -> str:
        return self._kms.key_id(tenant_id)

    def check_hygiene(
        self,
        text: str,
        quality_score: float = 1.0,
        opt_in: bool = True,
        license_type: str = "internal",
    ) -> HygieneResult:
        """ADR-008 4단 필터 실행."""
        return self._hygiene.check(
            text=text,
            quality_score=quality_score,
            opt_in=opt_in,
            license_type=license_type,
        )

    def verify_isolation(self, tenant_a: str, tenant_b: str) -> bool:
        return self._registry.verify_isolation(tenant_a, tenant_b)

    @property
    def registry(self) -> TenantRAGRegistry:
        return self._registry

    @property
    def tenant_count(self) -> int:
        return self._registry.tenant_count
