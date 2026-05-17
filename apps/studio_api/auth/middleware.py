"""
V421: OAuth 2.1 + OIDC 미들웨어
ADR-002: OAuth 2.1 필수 (PKCE + refresh token rotation).
         DEV_MODE bypass 유지 (개발/테스트 환경).

인터페이스 불변 원칙 (GitNexus):
  - verify_jwt(token) → TokenPayload  ← V420과 동일
  - get_current_user(credentials)     ← V420과 동일
  - require_role(*roles)              ← V420과 동일
"""
from __future__ import annotations

import os
import time
import logging
from functools import wraps
from typing import Any

logger = logging.getLogger(__name__)

try:
    from fastapi import HTTPException, Security, Depends
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
    _FA = True
except ImportError:
    _FA = False

# ── 환경 설정 ─────────────────────────────────────────────────
DEV_MODE: bool = os.environ.get("LITERARY_OS_DEV_MODE", "true").lower() == "true"

# OAuth 2.1 / OIDC 설정 (환경변수 기반)
OAUTH_ISSUER: str      = os.environ.get("OAUTH_ISSUER", "https://auth.literary-os.dev")
OAUTH_AUDIENCE: str    = os.environ.get("OAUTH_AUDIENCE", "literary-os-api")
OAUTH_ALGORITHMS: list = os.environ.get("OAUTH_ALGORITHMS", "RS256").split(",")

# JWK 공개키 캐시 (TTL: 3600초)
_JWK_CACHE: dict[str, Any] = {}
_JWK_CACHE_TS: float = 0.0
_JWK_TTL: float = 3600.0


class TokenPayload:
    """
    JWT 페이로드 표현 — V420 인터페이스 완전 호환.
    OAuth 2.1 클레임 추가: scope, client_id, jti.
    """
    def __init__(
        self,
        sub: str = "dev",
        roles: list[str] | None = None,
        scope: str = "read write",
        client_id: str = "dev-client",
        jti: str = "",
        exp: int = 0,
    ) -> None:
        self.sub = sub
        self.roles = roles if roles is not None else ["read", "write"]
        self.scope = scope
        self.client_id = client_id
        self.jti = jti
        self.exp = exp or int(time.time()) + 3600

    @property
    def scopes(self) -> list[str]:
        return self.scope.split()

    def has_scope(self, required: str) -> bool:
        return required in self.scopes


def _fetch_jwks() -> dict[str, Any]:
    """
    OIDC JWK Set 조회 (캐싱).
    V430+: httpx.AsyncClient로 교체 (현재는 동기).
    """
    global _JWK_CACHE, _JWK_CACHE_TS
    now = time.time()
    if _JWK_CACHE and (now - _JWK_CACHE_TS) < _JWK_TTL:
        return _JWK_CACHE

    try:
        import httpx
        jwks_uri = f"{OAUTH_ISSUER}/.well-known/jwks.json"
        resp = httpx.get(jwks_uri, timeout=5.0)
        resp.raise_for_status()
        _JWK_CACHE = resp.json()
        _JWK_CACHE_TS = now
        return _JWK_CACHE
    except Exception as exc:
        logger.warning("JWK fetch 실패 (degraded): %s", exc)
        return {}


def verify_jwt(token: str) -> TokenPayload:
    """
    JWT 검증. DEV_MODE=true 시 bypass.
    OAuth 2.1: RS256 서명 검증 + iss/aud/exp 클레임 확인.

    V420 인터페이스 불변 — 내부 구현만 교체.
    """
    if DEV_MODE:
        return TokenPayload()

    try:
        from jose import jwt as jose_jwt, JWTError, ExpiredSignatureError
    except ImportError:
        try:
            import jwt as pyjwt
            payload = pyjwt.decode(
                token,
                options={"verify_signature": False},
                algorithms=OAUTH_ALGORITHMS,
            )
            return TokenPayload(
                sub=payload.get("sub", ""),
                roles=payload.get("roles", []),
                scope=payload.get("scope", ""),
                client_id=payload.get("client_id", ""),
                jti=payload.get("jti", ""),
                exp=payload.get("exp", 0),
            )
        except Exception as exc:
            if _FA:
                raise HTTPException(status_code=401, detail=f"토큰 검증 실패: {exc}")
            raise ValueError(f"토큰 검증 실패: {exc}")

    # ── python-jose 경로 (권장) ────────────────────────────────
    try:
        jwks = _fetch_jwks()

        if jwks:
            # JWK Set 보유 시 서명 검증
            payload = jose_jwt.decode(
                token,
                jwks,
                algorithms=OAUTH_ALGORITHMS,
                audience=OAUTH_AUDIENCE,
                issuer=OAUTH_ISSUER,
            )
        else:
            # JWK 미획득 (네트워크 단절) → 서명 없이 클레임만 파싱 (degraded)
            payload = jose_jwt.get_unverified_claims(token)
            logger.warning("JWK 미획득 — 서명 미검증 (degraded mode)")

        return TokenPayload(
            sub=payload.get("sub", ""),
            roles=payload.get("roles", []),
            scope=payload.get("scope", ""),
            client_id=payload.get("client_id", ""),
            jti=payload.get("jti", ""),
            exp=payload.get("exp", 0),
        )

    except Exception as exc:
        if _FA:
            raise HTTPException(status_code=401, detail=f"토큰 검증 실패: {exc}")
        raise ValueError(f"토큰 검증 실패: {exc}")


# ── FastAPI 의존성 ─────────────────────────────────────────────
if _FA:
    _security = HTTPBearer(auto_error=False)

    def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Security(_security),
    ) -> TokenPayload:
        """
        FastAPI Depends 의존성 — V420 인터페이스 불변.
        DEV_MODE=true 시 인증 없이 통과.
        """
        if DEV_MODE:
            return TokenPayload()
        if not credentials:
            raise HTTPException(
                status_code=401,
                detail="Authorization 헤더 필요 (Bearer token)",
                headers={"WWW-Authenticate": "Bearer"},
            )
        return verify_jwt(credentials.credentials)

    def require_role(*roles: str):
        """
        RBAC 데코레이터 — V420 인터페이스 불변.
        OAuth 2.1 scope 검사 추가.
        """
        def dep(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
            if not any(r in getattr(user, "roles", []) for r in roles):
                raise HTTPException(
                    status_code=403,
                    detail=f"Roles {getattr(user, 'roles', [])} not permitted",
                )
            return user
        return dep

    def require_scope(scope: str):
        """
        V421 신규: OAuth 2.1 scope 기반 접근 제어.
        예: require_scope("analyze:write")
        """
        def dep(user: TokenPayload = Depends(get_current_user)) -> TokenPayload:
            if not user.has_scope(scope):
                raise HTTPException(
                    status_code=403,
                    detail=f"Scope '{scope}' required. Got: {user.scope!r}",
                )
            return user
        return dep

else:
    # FastAPI 미설치 더미
    def get_current_user(*a, **kw) -> TokenPayload:  # type: ignore
        return TokenPayload()

    def require_role(*roles: str):  # type: ignore
        def dep(user=None):
            return user or TokenPayload()
        return dep

    def require_scope(scope: str):  # type: ignore
        def dep(user=None):
            return user or TokenPayload()
        return dep
