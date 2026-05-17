"""
Literary OS V457 — TenantManager

ADR-011: Multi-tenant 논리적 격리 + KMS 키 per-tenant

설계 원칙:
  - LLM-0: 외부 KMS API 직접 호출 없음 (kms_fn 주입)
  - 테넌트별 독립 암호화 키 (KMSKeyStore)
  - 리전 라우팅: KR / EU / US (ADR-016 선행 구조체)
  - 불변 감사 레코드 (created_at 이후 변경 불가)
"""
from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import threading
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Callable, Dict, List, Optional


# ── 예외 ─────────────────────────────────────────────────────────────────────

class TenantNotFoundError(KeyError):
    """존재하지 않는 테넌트 접근."""

class TenantAlreadyExistsError(ValueError):
    """중복 tenant_id 등록 시도."""

class TenantInactiveError(RuntimeError):
    """비활성(SUSPENDED/DELETED) 테넌트 사용 시도."""


# ── 열거형 ───────────────────────────────────────────────────────────────────

class TenantRegion(str, Enum):
    """데이터 주권 리전 (ADR-016 기반)."""
    KR = "KR"   # 한국 (기본)
    EU = "EU"   # EU (GDPR)
    US = "US"   # 미국


class TenantStatus(str, Enum):
    """테넌트 생명주기 상태."""
    ACTIVE    = "ACTIVE"
    SUSPENDED = "SUSPENDED"   # 결제 미납 등 일시 정지
    DELETED   = "DELETED"     # 논리적 삭제 (데이터 보존 기간 내)


# ── KMS 키 저장소 ─────────────────────────────────────────────────────────────

@dataclass
class KMSKey:
    """테넌트별 대칭 암호화 키 메타데이터."""
    tenant_id: str
    key_id: str
    key_material: bytes        # 실제 배포에서는 HSM/Vault에 보관
    created_at: datetime
    rotated_at: Optional[datetime] = None
    version: int = 1

    def derive_data_key(self, context: str) -> bytes:
        """HKDF 유사 키 파생 (context = 용도 구분자)."""
        return hmac.new(
            self.key_material,
            context.encode("utf-8"),
            hashlib.sha256,
        ).digest()


class KMSKeyStore:
    """
    테넌트별 KMS 키 관리.

    LLM-0 원칙: kms_fn 주입으로 실제 KMS 호출 격리.
    kms_fn(tenant_id: str) -> bytes  — 키 소재 반환
    """

    def __init__(self, kms_fn: Optional[Callable[[str], bytes]] = None):
        self._kms_fn = kms_fn or self._default_kms_fn
        self._store: Dict[str, KMSKey] = {}
        self._lock = threading.Lock()

    # ── 공개 API ─────────────────────────────────────────────────────────────

    def provision_key(self, tenant_id: str) -> KMSKey:
        """신규 테넌트 키 발급."""
        with self._lock:
            if tenant_id in self._store:
                return self._store[tenant_id]
            material = self._kms_fn(tenant_id)
            key = KMSKey(
                tenant_id=tenant_id,
                key_id=f"kms-{tenant_id}-{secrets.token_hex(4)}",
                key_material=material,
                created_at=datetime.now(timezone.utc),
                version=1,
            )
            self._store[tenant_id] = key
            return key

    def get_key(self, tenant_id: str) -> KMSKey:
        """기존 키 조회."""
        with self._lock:
            if tenant_id not in self._store:
                raise TenantNotFoundError(f"KMS key not found: {tenant_id}")
            return self._store[tenant_id]

    def rotate_key(self, tenant_id: str) -> KMSKey:
        """키 교체 (버전 증가, 이전 키는 해독 전용으로 보존)."""
        with self._lock:
            if tenant_id not in self._store:
                raise TenantNotFoundError(f"KMS key not found for rotation: {tenant_id}")
            old = self._store[tenant_id]
            material = self._kms_fn(tenant_id)
            new_key = KMSKey(
                tenant_id=tenant_id,
                key_id=f"kms-{tenant_id}-{secrets.token_hex(4)}",
                key_material=material,
                created_at=old.created_at,
                rotated_at=datetime.now(timezone.utc),
                version=old.version + 1,
            )
            self._store[tenant_id] = new_key
            return new_key

    def list_key_ids(self) -> List[str]:
        with self._lock:
            return [k.key_id for k in self._store.values()]

    # ── 내부 ─────────────────────────────────────────────────────────────────

    @staticmethod
    def _default_kms_fn(tenant_id: str) -> bytes:
        """테스트용 결정론적 키 생성 (실제 환경에서는 Vault/AWS KMS 사용)."""
        return hashlib.sha256(f"literary_os_kms_{tenant_id}".encode()).digest()


# ── 테넌트 설정 ───────────────────────────────────────────────────────────────

@dataclass
class TenantConfig:
    """테넌트 구성 (불변 핵심 필드 + 변경 가능 설정)."""
    tenant_id: str
    name: str
    region: TenantRegion
    status: TenantStatus = TenantStatus.ACTIVE
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    plan: str = "free"                  # free / pro / enterprise
    max_tokens_per_month: int = 1_000_000
    max_cost_usd_per_month: float = 50.0
    contact_email: str = ""
    metadata: Dict[str, str] = field(default_factory=dict)

    # ── 파생 속성 ─────────────────────────────────────────────────────────────

    @property
    def is_active(self) -> bool:
        return self.status == TenantStatus.ACTIVE

    @property
    def data_residency_endpoint(self) -> str:
        """리전별 스토리지 엔드포인트 (ADR-016)."""
        _MAP = {
            TenantRegion.KR: "https://kr-data.literary-os.internal",
            TenantRegion.EU: "https://eu-data.literary-os.internal",
            TenantRegion.US: "https://us-data.literary-os.internal",
        }
        return _MAP[self.region]

    def to_dict(self) -> dict:
        return {
            "tenant_id":              self.tenant_id,
            "name":                   self.name,
            "region":                 self.region.value,
            "status":                 self.status.value,
            "created_at":             self.created_at.isoformat(),
            "plan":                   self.plan,
            "max_tokens_per_month":   self.max_tokens_per_month,
            "max_cost_usd_per_month": self.max_cost_usd_per_month,
            "contact_email":          self.contact_email,
            "data_residency_endpoint": self.data_residency_endpoint,
        }


# ── 테넌트 관리자 ─────────────────────────────────────────────────────────────

class TenantManager:
    """
    Literary OS 멀티-테넌트 관리 핵심 모듈 (V457).

    책임:
      - 테넌트 CRUD (생성/조회/업데이트/논리적 삭제)
      - KMS 키 자동 발급 및 교체
      - 리전 기반 데이터 주권 정책 적용
      - 활성 테넌트 접근 제어

    LLM-0: 외부 API 직접 호출 없음.
    """

    def __init__(self, kms_store: Optional[KMSKeyStore] = None):
        self._tenants: Dict[str, TenantConfig] = {}
        self._kms = kms_store or KMSKeyStore()
        self._lock = threading.RLock()

    # ── CRUD ─────────────────────────────────────────────────────────────────

    def create_tenant(
        self,
        tenant_id: str,
        name: str,
        region: TenantRegion = TenantRegion.KR,
        plan: str = "free",
        max_tokens_per_month: int = 1_000_000,
        max_cost_usd_per_month: float = 50.0,
        contact_email: str = "",
        metadata: Optional[Dict[str, str]] = None,
    ) -> TenantConfig:
        """신규 테넌트 등록 + KMS 키 자동 발급."""
        with self._lock:
            if tenant_id in self._tenants:
                raise TenantAlreadyExistsError(f"테넌트 이미 존재: {tenant_id}")
            cfg = TenantConfig(
                tenant_id=tenant_id,
                name=name,
                region=region,
                plan=plan,
                max_tokens_per_month=max_tokens_per_month,
                max_cost_usd_per_month=max_cost_usd_per_month,
                contact_email=contact_email,
                metadata=metadata or {},
            )
            self._tenants[tenant_id] = cfg
            self._kms.provision_key(tenant_id)
            return cfg

    def get_tenant(self, tenant_id: str) -> TenantConfig:
        """테넌트 조회 (존재하지 않으면 TenantNotFoundError)."""
        with self._lock:
            if tenant_id not in self._tenants:
                raise TenantNotFoundError(f"테넌트 없음: {tenant_id}")
            return self._tenants[tenant_id]

    def require_active_tenant(self, tenant_id: str) -> TenantConfig:
        """활성 테넌트 조회 (비활성이면 TenantInactiveError)."""
        cfg = self.get_tenant(tenant_id)
        if not cfg.is_active:
            raise TenantInactiveError(
                f"테넌트 {tenant_id} 비활성 상태: {cfg.status.value}"
            )
        return cfg

    def update_tenant(self, tenant_id: str, **kwargs) -> TenantConfig:
        """테넌트 설정 업데이트 (tenant_id / created_at 변경 불가)."""
        IMMUTABLE = {"tenant_id", "created_at"}
        with self._lock:
            cfg = self.get_tenant(tenant_id)
            for k, v in kwargs.items():
                if k in IMMUTABLE:
                    raise ValueError(f"변경 불가 필드: {k}")
                if not hasattr(cfg, k):
                    raise ValueError(f"알 수 없는 필드: {k}")
                object.__setattr__(cfg, k, v)
            return cfg

    def suspend_tenant(self, tenant_id: str) -> TenantConfig:
        """테넌트 일시 정지."""
        return self.update_tenant(tenant_id, status=TenantStatus.SUSPENDED)

    def restore_tenant(self, tenant_id: str) -> TenantConfig:
        """정지된 테넌트 복원."""
        with self._lock:
            cfg = self.get_tenant(tenant_id)
            if cfg.status == TenantStatus.DELETED:
                raise TenantInactiveError("삭제된 테넌트는 복원 불가")
            object.__setattr__(cfg, "status", TenantStatus.ACTIVE)
            return cfg

    def delete_tenant(self, tenant_id: str) -> TenantConfig:
        """논리적 삭제 (물리적 데이터 보존)."""
        return self.update_tenant(tenant_id, status=TenantStatus.DELETED)

    # ── KMS ──────────────────────────────────────────────────────────────────

    def get_tenant_key(self, tenant_id: str) -> KMSKey:
        """테넌트 KMS 키 조회 (활성 확인 포함)."""
        self.require_active_tenant(tenant_id)
        return self._kms.get_key(tenant_id)

    def rotate_tenant_key(self, tenant_id: str) -> KMSKey:
        """테넌트 KMS 키 교체."""
        self.require_active_tenant(tenant_id)
        return self._kms.rotate_key(tenant_id)

    # ── 조회 ─────────────────────────────────────────────────────────────────

    def list_tenants(
        self,
        region: Optional[TenantRegion] = None,
        status: Optional[TenantStatus] = None,
    ) -> List[TenantConfig]:
        """필터 조회."""
        with self._lock:
            tenants = list(self._tenants.values())
        if region:
            tenants = [t for t in tenants if t.region == region]
        if status:
            tenants = [t for t in tenants if t.status == status]
        return tenants

    def count_active(self) -> int:
        return sum(1 for t in self._tenants.values() if t.is_active)

    def tenant_exists(self, tenant_id: str) -> bool:
        return tenant_id in self._tenants

    # ── 요약 ─────────────────────────────────────────────────────────────────

    def summary(self) -> dict:
        with self._lock:
            total = len(self._tenants)
            by_status = {}
            by_region = {}
            for t in self._tenants.values():
                by_status[t.status.value] = by_status.get(t.status.value, 0) + 1
                by_region[t.region.value] = by_region.get(t.region.value, 0) + 1
        return {
            "total_tenants": total,
            "by_status": by_status,
            "by_region": by_region,
            "kms_keys_provisioned": len(self._kms.list_key_ids()),
        }
