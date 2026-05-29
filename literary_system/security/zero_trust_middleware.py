"""
literary_system.security.zero_trust_middleware
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V719 — ZeroTrustMiddleware: 요청 인터셉터 — 토큰 검증 + 테넌트 인가 (ADR-180).

설계 원칙:
  - 모든 요청에 Bearer 토큰 필수 (Authorization 헤더)
  - ZeroTrustTokenService.verify() → TokenClaims
  - TenantAuthority.authorize() → AccessDecision
  - 감사 로그 레코드(ZeroTrustAuditEntry) 즉시 기록
  - 통과(PASS) / 거부(DENY) 이벤트 훅 지원
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .zero_trust_token import (
    ZeroTrustTokenService,
    TokenClaims,
    TokenValidationError,
    TokenExpiredError,
)
from .tenant_authority import (
    TenantAuthority,
    AccessDecision,
    TenantNotFoundError,
)


# ---------------------------------------------------------------------------
# 감사 엔트리
# ---------------------------------------------------------------------------

@dataclass
class ZeroTrustAuditEntry:
    """미들웨어 처리 결과 감사 레코드."""
    timestamp: float
    request_id: str
    outcome: str          # "PASS" | "DENY"
    reason: str
    subject: Optional[str] = None
    tenant_id: Optional[str] = None
    required_role: Optional[str] = None
    path: Optional[str] = None


# ---------------------------------------------------------------------------
# 요청/응답 DTO
# ---------------------------------------------------------------------------

@dataclass
class ZTRequest:
    """미들웨어가 처리하는 요청 표현."""
    request_id: str
    authorization: Optional[str] = None   # "Bearer <token>"
    path: str = "/"
    headers: Dict[str, str] = field(default_factory=dict)
    meta: Dict = field(default_factory=dict)

    def bearer_token(self) -> Optional[str]:
        auth = self.authorization or self.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
        return None


@dataclass
class ZTResponse:
    """미들웨어 처리 결과."""
    allowed: bool
    claims: Optional[TokenClaims] = None
    decision: Optional[AccessDecision] = None
    status_code: int = 200
    reason: str = "OK"


# ---------------------------------------------------------------------------
# ZeroTrustMiddleware
# ---------------------------------------------------------------------------

class ZeroTrustMiddleware:
    """
    Zero-Trust 요청 인터셉터.

    Parameters
    ----------
    token_service  : ZeroTrustTokenService — 토큰 서명 검증기
    authority      : TenantAuthority       — 테넌트 권한 관리자
    required_role  : str | None            — 전역 필수 역할 (None 이면 역할 검사 생략)
    audit_log      : list | None           — 감사 로그 버퍼 (None 이면 내부 생성)
    """

    def __init__(
        self,
        token_service: ZeroTrustTokenService,
        authority: TenantAuthority,
        required_role: Optional[str] = None,
        audit_log: Optional[List[ZeroTrustAuditEntry]] = None,
    ) -> None:
        self._svc = token_service
        self._auth = authority
        self._required_role = required_role
        self._audit: List[ZeroTrustAuditEntry] = audit_log if audit_log is not None else []
        self._pass_hooks: List[Callable[[ZeroTrustAuditEntry], None]] = []
        self._deny_hooks: List[Callable[[ZeroTrustAuditEntry], None]] = []

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def process(self, request: ZTRequest) -> ZTResponse:
        """
        요청 처리 메인 진입점.

        Returns
        -------
        ZTResponse(allowed=True)  — 통과
        ZTResponse(allowed=False) — 거부 (status_code 401 / 403)
        """
        token_str = request.bearer_token()

        # 1. 토큰 없음 → 401
        if not token_str:
            return self._deny(request, 401, "Missing Bearer token")

        # 2. 토큰 검증
        try:
            claims = self._svc.verify(token_str)
        except TokenExpiredError as exc:
            return self._deny(request, 401, f"Token expired: {exc}", subject=None)
        except TokenValidationError as exc:
            return self._deny(request, 401, f"Token invalid: {exc}", subject=None)

        # 3. 테넌트 인가
        decision = self._auth.authorize(
            claims,
            required_role=self._required_role,
        )
        if not decision.granted:
            return self._deny(
                request,
                403,
                decision.reason,
                subject=claims.subject,
                tenant_id=claims.tenant_id,
            )

        # 4. PASS
        entry = self._log(
            request_id=request.request_id,
            outcome="PASS",
            reason="Access granted",
            subject=claims.subject,
            tenant_id=claims.tenant_id,
            path=request.path,
        )
        for hook in self._pass_hooks:
            hook(entry)

        return ZTResponse(
            allowed=True,
            claims=claims,
            decision=decision,
            status_code=200,
            reason="OK",
        )

    # ------------------------------------------------------------------
    # 훅 등록
    # ------------------------------------------------------------------

    def on_pass(self, fn: Callable[[ZeroTrustAuditEntry], None]) -> None:
        self._pass_hooks.append(fn)

    def on_deny(self, fn: Callable[[ZeroTrustAuditEntry], None]) -> None:
        self._deny_hooks.append(fn)

    # ------------------------------------------------------------------
    # 감사 로그 조회
    # ------------------------------------------------------------------

    @property
    def audit_log(self) -> List[ZeroTrustAuditEntry]:
        return list(self._audit)

    @property
    def audit_count(self) -> int:
        return len(self._audit)

    def pass_count(self) -> int:
        return sum(1 for e in self._audit if e.outcome == "PASS")

    def deny_count(self) -> int:
        return sum(1 for e in self._audit if e.outcome == "DENY")

    # ------------------------------------------------------------------
    # 내부 헬퍼
    # ------------------------------------------------------------------

    def _deny(
        self,
        request: ZTRequest,
        status_code: int,
        reason: str,
        subject: Optional[str] = None,
        tenant_id: Optional[str] = None,
    ) -> ZTResponse:
        entry = self._log(
            request_id=request.request_id,
            outcome="DENY",
            reason=reason,
            subject=subject,
            tenant_id=tenant_id,
            path=request.path,
        )
        for hook in self._deny_hooks:
            hook(entry)
        return ZTResponse(
            allowed=False,
            status_code=status_code,
            reason=reason,
        )

    def _log(
        self,
        request_id: str,
        outcome: str,
        reason: str,
        subject: Optional[str],
        tenant_id: Optional[str],
        path: Optional[str],
    ) -> ZeroTrustAuditEntry:
        entry = ZeroTrustAuditEntry(
            timestamp=time.time(),
            request_id=request_id,
            outcome=outcome,
            reason=reason,
            subject=subject,
            tenant_id=tenant_id,
            required_role=self._required_role,
            path=path,
        )
        self._audit.append(entry)
        return entry
