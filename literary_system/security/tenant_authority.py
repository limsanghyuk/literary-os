"""
literary_system.security.tenant_authority
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V718 — TenantAuthority: 테넌트 격리·권한 관리 서비스 (ADR-179).

책임:
  - 테넌트 등록·조회·비활성화
  - 테넌트별 허용 역할(allowed_roles) 관리
  - TokenClaims 기반 접근 승인/거부 판정
  - 크로스-테넌트 데이터 접근 차단 (strict isolation)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Set


# ---------------------------------------------------------------------------
# 예외
# ---------------------------------------------------------------------------

class TenantNotFoundError(KeyError):
    """등록되지 않은 테넌트 ID."""


class TenantDisabledError(PermissionError):
    """비활성화된 테넌트의 접근 시도."""


class AccessDeniedError(PermissionError):
    """역할 미충족 또는 크로스-테넌트 접근 시도."""


# ---------------------------------------------------------------------------
# DTO
# ---------------------------------------------------------------------------

@dataclass
class TenantRecord:
    """테넌트 메타데이터."""
    tenant_id: str
    display_name: str
    allowed_roles: FrozenSet[str]
    active: bool = True
    tags: dict = field(default_factory=dict)

    def is_role_permitted(self, role: str) -> bool:
        return role in self.allowed_roles


@dataclass
class AccessDecision:
    """접근 판정 결과."""
    granted: bool
    tenant_id: str
    subject: str
    reason: str


# ---------------------------------------------------------------------------
# TenantAuthority
# ---------------------------------------------------------------------------

class TenantAuthority:
    """
    테넌트 격리·권한 관리 서비스.

    사용 예::

        authority = TenantAuthority()
        authority.register("tenant_A", "Tenant Alpha", allowed_roles=["writer", "editor"])
        decision = authority.authorize(claims, required_role="writer")
        if not decision.granted:
            raise PermissionError(decision.reason)
    """

    def __init__(self) -> None:
        self._tenants: Dict[str, TenantRecord] = {}

    # ------------------------------------------------------------------
    # 테넌트 관리
    # ------------------------------------------------------------------

    def register(
        self,
        tenant_id: str,
        display_name: str,
        allowed_roles: Optional[List[str]] = None,
        tags: Optional[dict] = None,
    ) -> TenantRecord:
        """테넌트 등록 (이미 존재하면 업데이트)."""
        if not tenant_id:
            raise ValueError("tenant_id must not be empty")
        record = TenantRecord(
            tenant_id=tenant_id,
            display_name=display_name,
            allowed_roles=frozenset(allowed_roles or []),
            tags=tags or {},
        )
        self._tenants[tenant_id] = record
        return record

    def get(self, tenant_id: str) -> TenantRecord:
        """테넌트 조회. 없으면 TenantNotFoundError."""
        try:
            return self._tenants[tenant_id]
        except KeyError:
            raise TenantNotFoundError(f"Tenant not found: {tenant_id!r}")

    def disable(self, tenant_id: str) -> None:
        """테넌트 비활성화."""
        record = self.get(tenant_id)
        # dataclass 는 frozen=False 이므로 직접 수정
        object.__setattr__(record, "active", False) if False else None
        self._tenants[tenant_id] = TenantRecord(
            tenant_id=record.tenant_id,
            display_name=record.display_name,
            allowed_roles=record.allowed_roles,
            active=False,
            tags=record.tags,
        )

    def enable(self, tenant_id: str) -> None:
        """테넌트 재활성화."""
        record = self.get(tenant_id)
        self._tenants[tenant_id] = TenantRecord(
            tenant_id=record.tenant_id,
            display_name=record.display_name,
            allowed_roles=record.allowed_roles,
            active=True,
            tags=record.tags,
        )

    def add_role(self, tenant_id: str, role: str) -> None:
        """테넌트 허용 역할 추가."""
        record = self.get(tenant_id)
        new_roles = record.allowed_roles | {role}
        self._tenants[tenant_id] = TenantRecord(
            tenant_id=record.tenant_id,
            display_name=record.display_name,
            allowed_roles=new_roles,
            active=record.active,
            tags=record.tags,
        )

    def remove_role(self, tenant_id: str, role: str) -> None:
        """테넌트 허용 역할 제거."""
        record = self.get(tenant_id)
        new_roles = record.allowed_roles - {role}
        self._tenants[tenant_id] = TenantRecord(
            tenant_id=record.tenant_id,
            display_name=record.display_name,
            allowed_roles=new_roles,
            active=record.active,
            tags=record.tags,
        )

    def list_all(self) -> List[TenantRecord]:
        return list(self._tenants.values())

    @property
    def tenant_count(self) -> int:
        return len(self._tenants)

    # ------------------------------------------------------------------
    # 접근 판정
    # ------------------------------------------------------------------

    def authorize(
        self,
        claims,  # TokenClaims (순환 임포트 방지를 위해 타입 힌트 생략)
        required_role: Optional[str] = None,
        target_tenant_id: Optional[str] = None,
    ) -> AccessDecision:
        """
        TokenClaims 기반 접근 판정.

        Parameters
        ----------
        claims         : TokenClaims — 검증된 토큰 클레임
        required_role  : 필요 역할 (None 이면 역할 검사 생략)
        target_tenant_id : 접근 대상 테넌트 (None 이면 claims.tenant_id 사용)

        Returns
        -------
        AccessDecision
        """
        subject = claims.subject
        token_tenant = claims.tenant_id
        effective_target = target_tenant_id or token_tenant

        # 1. 크로스-테넌트 검사
        if effective_target != token_tenant:
            return AccessDecision(
                granted=False,
                tenant_id=effective_target,
                subject=subject,
                reason=(
                    f"Cross-tenant access denied: "
                    f"token.tenant_id={token_tenant!r} vs target={effective_target!r}"
                ),
            )

        # 2. 테넌트 존재 확인
        try:
            record = self.get(token_tenant)
        except TenantNotFoundError:
            return AccessDecision(
                granted=False,
                tenant_id=token_tenant,
                subject=subject,
                reason=f"Tenant not registered: {token_tenant!r}",
            )

        # 3. 테넌트 활성 확인
        if not record.active:
            return AccessDecision(
                granted=False,
                tenant_id=token_tenant,
                subject=subject,
                reason=f"Tenant {token_tenant!r} is disabled",
            )

        # 4. 역할 검사
        if required_role is not None:
            # 토큰 클레임 내 역할에 required_role 이 있어야 하고,
            # 테넌트 설정에서도 허용되어야 한다.
            token_roles: list = claims.roles if hasattr(claims, "roles") else []
            if required_role not in token_roles:
                return AccessDecision(
                    granted=False,
                    tenant_id=token_tenant,
                    subject=subject,
                    reason=f"Required role {required_role!r} not in token roles {token_roles}",
                )
            if not record.is_role_permitted(required_role):
                return AccessDecision(
                    granted=False,
                    tenant_id=token_tenant,
                    subject=subject,
                    reason=(
                        f"Role {required_role!r} not permitted for tenant {token_tenant!r}"
                    ),
                )

        return AccessDecision(
            granted=True,
            tenant_id=token_tenant,
            subject=subject,
            reason="Access granted",
        )

    def authorize_or_raise(
        self,
        claims,
        required_role: Optional[str] = None,
        target_tenant_id: Optional[str] = None,
    ) -> AccessDecision:
        """authorize() + denied 시 AccessDeniedError 발생."""
        decision = self.authorize(claims, required_role, target_tenant_id)
        if not decision.granted:
            raise AccessDeniedError(decision.reason)
        return decision
