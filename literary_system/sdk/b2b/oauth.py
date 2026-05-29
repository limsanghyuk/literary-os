"""B2B Partner API — OAuth 2.1 Client Credentials 인증 (ADR-118).

실제 토큰 서버 없이도 동작하는 in-memory stub 구현.
프로덕션에서는 `TokenStore`를 외부 Redis/DB로 교체한다.
"""
from __future__ import annotations

import hashlib
import hmac
import secrets
import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Optional


__all__ = [
    "OAuthClient",
    "AccessToken",
    "TokenStore",
    "OAuth21Manager",
    "OAuthError",
    "InvalidClientError",
    "InvalidTokenError",
    "ExpiredTokenError",
]

# ── 예외 ──────────────────────────────────────────────────────────────────

class OAuthError(Exception):
    """OAuth 2.1 기본 예외."""
    def __init__(self, msg: str, error_code: str = "oauth_error") -> None:
        super().__init__(msg)
        self.error_code = error_code


class InvalidClientError(OAuthError):
    def __init__(self) -> None:
        super().__init__("Invalid client credentials", "invalid_client")


class InvalidTokenError(OAuthError):
    def __init__(self) -> None:
        super().__init__("Invalid access token", "invalid_token")


class ExpiredTokenError(OAuthError):
    def __init__(self) -> None:
        super().__init__("Access token has expired", "token_expired")


# ── 데이터 모델 ────────────────────────────────────────────────────────────

@dataclass
class OAuthClient:
    """등록된 B2B 파트너 클라이언트."""
    client_id: str
    client_secret_hash: str          # SHA-256 해시 (평문 저장 금지)
    partner_name: str
    scopes: list[str] = field(default_factory=lambda: ["analyze", "repair", "predict", "generate"])
    rpm_limit: int = 1000
    is_active: bool = True

    @staticmethod
    def hash_secret(secret: str) -> str:
        return hashlib.sha256(secret.encode()).hexdigest()

    def verify_secret(self, secret: str) -> bool:
        return hmac.compare_digest(
            self.client_secret_hash,
            self.hash_secret(secret),
        )


@dataclass
class AccessToken:
    """발급된 액세스 토큰."""
    token: str
    client_id: str
    scopes: list[str]
    issued_at: float = field(default_factory=time.monotonic)
    expires_in: int = 3600           # 1시간

    @property
    def is_expired(self) -> bool:
        return time.monotonic() - self.issued_at > self.expires_in

    @property
    def expires_at_epoch(self) -> float:
        return self.issued_at + self.expires_in


# ── 토큰 저장소 (in-memory) ────────────────────────────────────────────────

class TokenStore:
    """액세스 토큰 인메모리 저장소."""

    def __init__(self) -> None:
        self._tokens: dict[str, AccessToken] = {}
        self._lock = Lock()

    def save(self, token: AccessToken) -> None:
        with self._lock:
            self._tokens[token.token] = token

    def get(self, token_str: str) -> Optional[AccessToken]:
        with self._lock:
            return self._tokens.get(token_str)

    def revoke(self, token_str: str) -> bool:
        with self._lock:
            return self._tokens.pop(token_str, None) is not None

    def purge_expired(self) -> int:
        """만료 토큰 정리 후 삭제 수 반환."""
        with self._lock:
            expired = [k for k, v in self._tokens.items() if v.is_expired]
            for k in expired:
                del self._tokens[k]
            return len(expired)

    def count(self) -> int:
        with self._lock:
            return len(self._tokens)


# ── OAuth 2.1 매니저 ──────────────────────────────────────────────────────

class OAuth21Manager:
    """OAuth 2.1 Client Credentials Flow 관리자.

    - `register_client()`: B2B 파트너 등록
    - `issue_token()`: client_credentials grant → AccessToken
    - `validate_token()`: 요청당 토큰 검증
    - `revoke_token()`: 토큰 폐기
    """

    GRANT_TYPE = "client_credentials"

    def __init__(self, token_ttl: int = 3600) -> None:
        self._clients: dict[str, OAuthClient] = {}
        self._store = TokenStore()
        self._token_ttl = token_ttl
        self._lock = Lock()

    def register_client(
        self,
        partner_name: str,
        scopes: list[str] | None = None,
        rpm_limit: int = 1000,
    ) -> tuple[str, str]:
        """신규 B2B 파트너 등록 → (client_id, client_secret) 반환.

        client_secret은 이 시점에만 노출되며 이후 해시만 저장된다.
        """
        client_id = "cid_" + secrets.token_urlsafe(16)
        client_secret = secrets.token_urlsafe(32)
        secret_hash = OAuthClient.hash_secret(client_secret)

        client = OAuthClient(
            client_id=client_id,
            client_secret_hash=secret_hash,
            partner_name=partner_name,
            scopes=scopes or ["analyze", "repair", "predict", "generate"],
            rpm_limit=rpm_limit,
        )
        with self._lock:
            self._clients[client_id] = client

        return client_id, client_secret

    def issue_token(
        self,
        client_id: str,
        client_secret: str,
        grant_type: str = "client_credentials",
        requested_scopes: list[str] | None = None,
    ) -> AccessToken:
        """Client Credentials grant → AccessToken 발급."""
        if grant_type != self.GRANT_TYPE:
            raise OAuthError(f"Unsupported grant_type: {grant_type}", "unsupported_grant_type")

        with self._lock:
            client = self._clients.get(client_id)

        if client is None or not client.is_active:
            raise InvalidClientError()
        if not client.verify_secret(client_secret):
            raise InvalidClientError()

        # 요청 스코프가 허용 범위 내인지 확인
        scopes = requested_scopes or client.scopes
        invalid = set(scopes) - set(client.scopes)
        if invalid:
            raise OAuthError(f"Requested scopes not allowed: {invalid}", "invalid_scope")

        token_str = "los_" + secrets.token_urlsafe(32)
        token = AccessToken(
            token=token_str,
            client_id=client_id,
            scopes=scopes,
            expires_in=self._token_ttl,
        )
        self._store.save(token)
        return token

    def validate_token(self, token_str: str, required_scope: str | None = None) -> AccessToken:
        """토큰 유효성 검증. 실패 시 예외 발생."""
        token = self._store.get(token_str)
        if token is None:
            raise InvalidTokenError()
        if token.is_expired:
            self._store.revoke(token_str)
            raise ExpiredTokenError()
        if required_scope and required_scope not in token.scopes:
            raise OAuthError(f"Token lacks required scope: {required_scope}", "insufficient_scope")
        return token

    def revoke_token(self, token_str: str) -> bool:
        return self._store.revoke(token_str)

    def get_client(self, client_id: str) -> Optional[OAuthClient]:
        with self._lock:
            return self._clients.get(client_id)

    def deactivate_client(self, client_id: str) -> bool:
        with self._lock:
            client = self._clients.get(client_id)
            if client:
                client.is_active = False
                return True
            return False

    def purge_expired_tokens(self) -> int:
        return self._store.purge_expired()

    @property
    def active_token_count(self) -> int:
        return self._store.count()
