"""
literary_system.plugins.plugin_auth
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V721 — PluginAuthAdapter: 플러그인 실행 전 Zero-Trust 인증·인가 어댑터 (ADR-182).

설계 원칙:
  - plugins/ → security/ 단방향 의존 (역방향 금지, 순환 방지)
  - 플러그인 실행 전 반드시 token 검증 + 테넌트 인가
  - PluginPermission → 역할 매핑 테이블로 권한 제어
  - 선택적 ZeroTrustAuditLog 연동 (audit_log 인자)
  - G32: sys.stdout.write 사용 (print 금지)
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional, List

from literary_system.security.zero_trust_token import (
    ZeroTrustTokenService,
    TokenClaims,
    TokenValidationError,
    TokenExpiredError,
)
from literary_system.security.tenant_authority import (
    TenantAuthority,
    AccessDecision,
    AccessDeniedError,
    TenantNotFoundError,
)
from literary_system.plugins.plugin_manifest import PluginPermission


# ── 예외 계층 ─────────────────────────────────────────────────────────────────

class PluginAuthError(Exception):
    """플러그인 인증 실패 기반 예외."""


class PluginTokenInvalid(PluginAuthError):
    """토큰 형식 오류 또는 변조 감지."""


class PluginTokenExpired(PluginAuthError):
    """토큰 만료."""


class PluginAccessDenied(PluginAuthError):
    """테넌트 권한 부족."""


class PluginTenantNotFound(PluginAuthError):
    """테넌트 미등록."""


# ── 역할 매핑 ─────────────────────────────────────────────────────────────────

#: PluginPermission → ZeroTrust 역할 이름 매핑
PERMISSION_ROLE_MAP: dict[PluginPermission, str] = {
    PluginPermission.READ_CORPUS:  "corpus_reader",
    PluginPermission.WRITE_OUTPUT: "output_writer",
    PluginPermission.CALL_LLM:     "llm_caller",
    PluginPermission.READ_NKG:     "nkg_reader",
    PluginPermission.WRITE_NKG:    "nkg_writer",
    PluginPermission.NETWORK_OUT:  "network_agent",
}


# ── 인증 결과 DTO ─────────────────────────────────────────────────────────────

@dataclass
class PluginAuthResult:
    """플러그인 인증·인가 결과."""
    authenticated: bool
    claims: Optional[TokenClaims] = None
    granted_permissions: List[PluginPermission] = field(default_factory=list)
    denied_permissions: List[PluginPermission] = field(default_factory=list)
    reason: str = ""

    @property
    def fully_authorized(self) -> bool:
        """요청된 권한 전부 승인됐는지 여부."""
        return self.authenticated and not self.denied_permissions


# ── 어댑터 ────────────────────────────────────────────────────────────────────

class PluginAuthAdapter:
    """
    플러그인 실행 전 Zero-Trust 인증·인가 어댑터.

    Usage::

        adapter = PluginAuthAdapter(token_svc, tenant_auth)
        result = adapter.authenticate(
            token_str="Bearer <token>",
            tenant_id="tenant-A",
            required_permissions=[PluginPermission.READ_CORPUS],
        )
        if not result.fully_authorized:
            raise PluginAccessDenied(result.reason)
    """

    def __init__(
        self,
        token_service: ZeroTrustTokenService,
        tenant_authority: TenantAuthority,
        *,
        strict: bool = True,
    ) -> None:
        """
        Args:
            token_service:    ZeroTrustTokenService 인스턴스
            tenant_authority: TenantAuthority 인스턴스
            strict:           True이면 권한 일부 거부 시 즉시 PluginAccessDenied 발생
        """
        self._token_svc = token_service
        self._tenant_auth = tenant_authority
        self._strict = strict

    # ── 공개 API ────────────────────────────────────────────────────────────

    def authenticate(
        self,
        token_str: str,
        tenant_id: str,
        required_permissions: Optional[List[PluginPermission]] = None,
    ) -> PluginAuthResult:
        """
        토큰 검증 후 required_permissions 각 항목에 대해 인가 판정.

        Args:
            token_str:            Bearer 토큰 문자열 ("Bearer <jwt>" 또는 raw jwt)
            tenant_id:            대상 테넌트 ID
            required_permissions: 필요 권한 목록 (None이면 인증만 수행)

        Returns:
            PluginAuthResult

        Raises:
            PluginTokenInvalid:   토큰 형식/서명 오류
            PluginTokenExpired:   토큰 만료
            PluginTenantNotFound: 테넌트 미등록
            PluginAccessDenied:   strict=True 이고 권한 거부 시
        """
        # 1. Bearer 접두사 제거
        raw_token = token_str.removeprefix("Bearer ").strip()

        # 2. 토큰 검증
        try:
            claims = self._token_svc.verify(raw_token)
        except TokenExpiredError as exc:
            raise PluginTokenExpired(str(exc)) from exc
        except TokenValidationError as exc:
            raise PluginTokenInvalid(str(exc)) from exc

        # 3. 권한 인가
        granted: List[PluginPermission] = []
        denied:  List[PluginPermission] = []

        perms = required_permissions or []
        for perm in perms:
            role = PERMISSION_ROLE_MAP.get(perm, perm.value)
            try:
                decision: AccessDecision = self._tenant_auth.authorize(
                    claims, required_role=role, target_tenant_id=tenant_id
                )
                if decision.granted:
                    granted.append(perm)
                else:
                    denied.append(perm)
            except TenantNotFoundError as exc:
                raise PluginTenantNotFound(str(exc)) from exc
            except AccessDeniedError:
                denied.append(perm)

        result = PluginAuthResult(
            authenticated=True,
            claims=claims,
            granted_permissions=granted,
            denied_permissions=denied,
            reason="OK" if not denied else f"권한 거부: {[p.value for p in denied]}",
        )

        if self._strict and denied:
            raise PluginAccessDenied(result.reason)

        return result

    def verify_token_only(self, token_str: str) -> TokenClaims:
        """
        권한 검사 없이 토큰 서명만 검증하고 클레임 반환.

        Raises:
            PluginTokenInvalid / PluginTokenExpired
        """
        raw = token_str.removeprefix("Bearer ").strip()
        try:
            return self._token_svc.verify(raw)
        except TokenExpiredError as exc:
            raise PluginTokenExpired(str(exc)) from exc
        except TokenValidationError as exc:
            raise PluginTokenInvalid(str(exc)) from exc

    def has_permission(
        self,
        claims: TokenClaims,
        permission: PluginPermission,
        tenant_id: str,
    ) -> bool:
        """단일 권한 보유 여부 확인 (예외 발생 없이 bool 반환)."""
        role = PERMISSION_ROLE_MAP.get(permission, permission.value)
        try:
            decision = self._tenant_auth.authorize(
                claims, required_role=role, target_tenant_id=tenant_id
            )
            return decision.granted
        except Exception:
            return False
