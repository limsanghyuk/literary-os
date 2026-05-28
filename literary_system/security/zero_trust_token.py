"""
literary_system.security.zero_trust_token
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V717 — ZeroTrustTokenService: HMAC-SHA256 기반 토큰 발급·검증 서비스 (ADR-178).

설계 원칙:
  - 모든 요청은 단기 서명 토큰으로 인증 (default TTL = 300 s)
  - HMAC-SHA256 서명: header.payload.signature (base64url 인코딩)
  - tenant_id 클레임 강제 포함 → 크로스-테넌트 격리 기반
  - 토큰 재사용 방지: jti (JWT-style unique ID) + nonce store
  - 만료 토큰 / 변조 토큰 → 전용 예외 발생
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
import uuid
from dataclasses import dataclass, field
from typing import Dict, Optional, Set


# ---------------------------------------------------------------------------
# 예외 계층
# ---------------------------------------------------------------------------

class TokenValidationError(Exception):
    """토큰 형식·서명 오류."""


class TokenExpiredError(TokenValidationError):
    """토큰 TTL 초과."""


# ---------------------------------------------------------------------------
# 클레임 DTO
# ---------------------------------------------------------------------------

@dataclass
class TokenClaims:
    """검증된 토큰 클레임."""
    subject: str            # 주체 (사용자 ID 또는 서비스 명)
    tenant_id: str          # 테넌트 식별자 (필수)
    issued_at: float        # Unix timestamp
    expires_at: float       # Unix timestamp
    jti: str                # 고유 토큰 ID
    roles: list = field(default_factory=list)
    extra: dict = field(default_factory=dict)

    @property
    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    @property
    def ttl_remaining(self) -> float:
        return max(0.0, self.expires_at - time.time())


# ---------------------------------------------------------------------------
# 헬퍼
# ---------------------------------------------------------------------------

def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    if padding != 4:
        s += "=" * padding
    return base64.urlsafe_b64decode(s)


def _sign(secret: bytes, message: str) -> str:
    sig = hmac.new(secret, message.encode(), hashlib.sha256).digest()
    return _b64url_encode(sig)


# ---------------------------------------------------------------------------
# 핵심 서비스
# ---------------------------------------------------------------------------

class ZeroTrustTokenService:
    """
    HMAC-SHA256 기반 Zero-Trust 토큰 서비스.

    Parameters
    ----------
    secret_key : bytes | None
        서명 비밀키. None 이면 32 바이트 랜덤 키 자동 생성.
    default_ttl : int
        기본 토큰 유효 시간 (초, 기본 300 s = 5 분).
    max_nonce_store : int
        재사용 방지 nonce 저장 한도 (메모리 보호).
    """

    ALG = "HS256"
    TOKEN_VERSION = "1"

    def __init__(
        self,
        secret_key: Optional[bytes] = None,
        default_ttl: int = 300,
        max_nonce_store: int = 10_000,
    ) -> None:
        self._secret: bytes = secret_key if secret_key is not None else os.urandom(32)
        self.default_ttl = default_ttl
        self._max_nonce_store = max_nonce_store
        self._used_jtis: Set[str] = set()  # replay-attack 방지

    # ------------------------------------------------------------------
    # 발급
    # ------------------------------------------------------------------

    def issue(
        self,
        subject: str,
        tenant_id: str,
        roles: Optional[list] = None,
        ttl: Optional[int] = None,
        extra: Optional[dict] = None,
    ) -> str:
        """
        서명된 토큰 문자열 발급.

        Returns
        -------
        str
            ``header.payload.signature`` 형식 토큰.
        """
        if not subject:
            raise ValueError("subject must not be empty")
        if not tenant_id:
            raise ValueError("tenant_id must not be empty")

        now = time.time()
        effective_ttl = ttl if ttl is not None else self.default_ttl

        header = {
            "alg": self.ALG,
            "ver": self.TOKEN_VERSION,
        }
        payload = {
            "sub": subject,
            "tid": tenant_id,
            "iat": now,
            "exp": now + effective_ttl,
            "jti": str(uuid.uuid4()),
            "roles": roles or [],
            **(extra or {}),
        }

        h_enc = _b64url_encode(json.dumps(header, separators=(",", ":")).encode())
        p_enc = _b64url_encode(json.dumps(payload, separators=(",", ":")).encode())
        signing_input = f"{h_enc}.{p_enc}"
        signature = _sign(self._secret, signing_input)

        return f"{signing_input}.{signature}"

    # ------------------------------------------------------------------
    # 검증
    # ------------------------------------------------------------------

    def verify(self, token: str) -> TokenClaims:
        """
        토큰 검증 후 TokenClaims 반환.

        Raises
        ------
        TokenExpiredError   : 만료된 토큰.
        TokenValidationError: 형식 오류 또는 서명 불일치.
        """
        try:
            parts = token.split(".")
            if len(parts) != 3:
                raise TokenValidationError("Token must have exactly 3 parts")

            h_enc, p_enc, sig_received = parts
            signing_input = f"{h_enc}.{p_enc}"

            # 서명 검증 (timing-safe)
            expected_sig = _sign(self._secret, signing_input)
            if not hmac.compare_digest(sig_received, expected_sig):
                raise TokenValidationError("Signature verification failed")

            # 헤더 파싱
            header = json.loads(_b64url_decode(h_enc))
            if header.get("alg") != self.ALG:
                raise TokenValidationError(f"Unsupported algorithm: {header.get('alg')}")

            # 페이로드 파싱
            payload = json.loads(_b64url_decode(p_enc))

        except (ValueError, KeyError, json.JSONDecodeError) as exc:
            raise TokenValidationError(f"Malformed token: {exc}") from exc

        # 만료 검사
        now = time.time()
        if now > payload["exp"]:
            raise TokenExpiredError(
                f"Token expired {now - payload['exp']:.1f}s ago"
            )

        # 필수 클레임
        for claim in ("sub", "tid", "iat", "exp", "jti"):
            if claim not in payload:
                raise TokenValidationError(f"Missing required claim: {claim}")

        # Replay-attack 방지
        jti = payload["jti"]
        if jti in self._used_jtis:
            raise TokenValidationError(f"Token already used (jti={jti})")

        # nonce store 용량 보호
        if len(self._used_jtis) >= self._max_nonce_store:
            # 가장 간단한 전략: 전체 초기화 (실운영에서는 TTL-based eviction)
            self._used_jtis.clear()
        self._used_jtis.add(jti)

        # 클레임 추출 (알려진 키 제거 후 나머지 extra)
        known = {"sub", "tid", "iat", "exp", "jti", "roles"}
        extra = {k: v for k, v in payload.items() if k not in known}

        return TokenClaims(
            subject=payload["sub"],
            tenant_id=payload["tid"],
            issued_at=payload["iat"],
            expires_at=payload["exp"],
            jti=jti,
            roles=payload.get("roles", []),
            extra=extra,
        )

    # ------------------------------------------------------------------
    # 편의 메서드
    # ------------------------------------------------------------------

    def verify_tenant(self, token: str, expected_tenant_id: str) -> TokenClaims:
        """
        토큰 검증 + 테넌트 ID 일치 확인.
        크로스-테넌트 접근 시도 → TokenValidationError.
        """
        claims = self.verify(token)
        if claims.tenant_id != expected_tenant_id:
            raise TokenValidationError(
                f"Cross-tenant access denied: "
                f"token.tenant_id={claims.tenant_id!r} != {expected_tenant_id!r}"
            )
        return claims

    def refresh(self, token: str, ttl: Optional[int] = None) -> str:
        """
        유효한 토큰을 갱신하여 새 토큰 발급 (원본 토큰 무효화).
        """
        claims = self.verify(token)
        return self.issue(
            subject=claims.subject,
            tenant_id=claims.tenant_id,
            roles=claims.roles,
            ttl=ttl,
            extra=claims.extra if claims.extra else None,
        )

    def revoke(self, token: str) -> None:
        """
        토큰 jti 를 used 목록에 강제 등록 (= 즉시 폐기).
        서명·형식 오류인 토큰은 무시.
        """
        try:
            parts = token.split(".")
            if len(parts) == 3:
                payload = json.loads(_b64url_decode(parts[1]))
                jti = payload.get("jti")
                if jti:
                    self._used_jtis.add(jti)
        except Exception:
            pass

    # ------------------------------------------------------------------
    # 상태 조회
    # ------------------------------------------------------------------

    @property
    def revoked_count(self) -> int:
        return len(self._used_jtis)
