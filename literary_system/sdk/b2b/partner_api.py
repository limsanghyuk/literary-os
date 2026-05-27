"""B2B Partner API 통합 레이어 (ADR-118).

OAuth 2.1 + Webhook + RPM 제한을 결합한 B2B 파트너 전용 API.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from threading import Lock
from typing import Any

from literary_system.sdk.b2b.oauth import (
    AccessToken,
    OAuth21Manager,
    OAuthClient,
)
from literary_system.sdk.b2b.webhook import (
    WebhookEvent,
    WebhookEventType,
    WebhookManager,
)
from literary_system.sdk import LiteraryOSClient, SDKConfig

__all__ = ["PartnerAPIConfig", "B2BPartnerAPI", "PartnerQuotaError"]


@dataclass
class PartnerAPIConfig:
    """B2B Partner API 설정."""
    default_rpm: int = 1_000
    token_ttl: int = 3_600
    offline_mode: bool = True


class PartnerQuotaError(Exception):
    """파트너 RPM 한도 초과."""
    def __init__(self, client_id: str, limit: int) -> None:
        super().__init__(f"Partner {client_id} exceeded {limit} RPM")
        self.client_id = client_id
        self.limit = limit


class _PartnerRateLimiter:
    """파트너별 독립 슬라이딩 윈도우 RPM 제한기."""

    def __init__(self) -> None:
        self._windows: dict[str, list[float]] = {}
        self._lock = Lock()

    def check(self, client_id: str, limit: int) -> bool:
        if limit == 0:
            return True
        now = time.monotonic()
        with self._lock:
            ts = self._windows.setdefault(client_id, [])
            self._windows[client_id] = [t for t in ts if now - t < 60.0]
            if len(self._windows[client_id]) >= limit:
                return False
            self._windows[client_id].append(now)
            return True

    def current_count(self, client_id: str) -> int:
        now = time.monotonic()
        with self._lock:
            ts = self._windows.get(client_id, [])
            return sum(1 for t in ts if now - t < 60.0)


class B2BPartnerAPI:
    """B2B 파트너 전용 API — OAuth 2.1 + Webhook + 1,000 RPM.

    사용 흐름:
        1. ``register_partner()`` — 파트너 등록 → (client_id, secret)
        2. ``issue_token()`` — 토큰 발급
        3. ``call_analyze()`` / ``call_generate()`` 등 — 인증된 API 호출
        4. ``register_webhook()`` — Webhook 이벤트 수신 등록
    """

    def __init__(self, config: PartnerAPIConfig | None = None) -> None:
        self._config = config or PartnerAPIConfig()
        self._oauth = OAuth21Manager(token_ttl=self._config.token_ttl)
        self._webhook = WebhookManager()
        self._limiter = _PartnerRateLimiter()
        self._sdk = LiteraryOSClient(SDKConfig(offline_mode=self._config.offline_mode, max_rpm=0))

    # ── 파트너 관리 ─────────────────────────────────────────────────────

    def register_partner(
        self,
        partner_name: str,
        scopes: list[str] | None = None,
        rpm_limit: int | None = None,
    ) -> tuple[str, str]:
        """신규 B2B 파트너 등록.

        Returns
        -------
        (client_id, client_secret)  — secret은 최초 발급 시에만 표시됨
        """
        return self._oauth.register_client(
            partner_name=partner_name,
            scopes=scopes,
            rpm_limit=rpm_limit or self._config.default_rpm,
        )

    def deactivate_partner(self, client_id: str) -> bool:
        return self._oauth.deactivate_client(client_id)

    # ── 인증 ────────────────────────────────────────────────────────────

    def issue_token(
        self,
        client_id: str,
        client_secret: str,
        grant_type: str = "client_credentials",
        requested_scopes: list[str] | None = None,
    ) -> AccessToken:
        return self._oauth.issue_token(client_id, client_secret, grant_type, requested_scopes)

    def validate_token(self, token: str, scope: str | None = None) -> AccessToken:
        return self._oauth.validate_token(token, scope)

    # ── API 호출 (인증 필수) ─────────────────────────────────────────────

    def call_analyze(self, token: str, text: str, context: str = "") -> dict[str, Any]:
        at = self.validate_token(token, "analyze")
        self._enforce_rpm(at.client_id)
        result = self._sdk.analyze(text, context)
        self._fire_webhook(at.client_id, WebhookEventType.SCENE_ANALYZED, {"word_count": result.word_count})
        return {
            "quality": {"overall": result.quality.overall},
            "issues": result.issues,
            "passed": result.passed,
        }

    def call_generate(
        self,
        token: str,
        title: str,
        characters: list[str],
        setting: str,
        conflict: str,
        tone: str = "dramatic",
    ) -> dict[str, Any]:
        at = self.validate_token(token, "generate")
        self._enforce_rpm(at.client_id)
        result = self._sdk.generate(title, characters, setting, conflict, tone)
        self._fire_webhook(at.client_id, WebhookEventType.SCENE_GENERATED, {"quality": result.quality.overall})
        return {
            "scene_text": result.scene_text,
            "quality": result.quality.overall,
            "passed_critic": result.passed_critic,
        }

    def call_repair(
        self,
        token: str,
        text: str,
        issues: list[str],
        target_score: float = 0.75,
    ) -> dict[str, Any]:
        at = self.validate_token(token, "repair")
        self._enforce_rpm(at.client_id)
        result = self._sdk.repair(text, issues, target_score)
        self._fire_webhook(at.client_id, WebhookEventType.SCENE_REPAIRED, {"improved": result.improved})
        return {
            "repaired_text": result.repaired_text,
            "score_before": result.score_before,
            "score_after": result.score_after,
            "improved": result.improved,
        }

    def call_predict(self, token: str, context: str, n: int = 3) -> dict[str, Any]:
        at = self.validate_token(token, "predict")
        self._enforce_rpm(at.client_id)
        result = self._sdk.predict(context, n)
        return {
            "predictions": [
                {"rank": p.rank, "synopsis": p.synopsis, "probability": p.probability}
                for p in result.predictions
            ]
        }

    # ── Webhook ─────────────────────────────────────────────────────────

    def register_webhook(
        self,
        client_id: str,
        url: str,
        secret: str,
        event_types: list[str] | None = None,
    ) -> bool:
        types = [WebhookEventType(t) for t in (event_types or [])] if event_types else None
        self._webhook.register_endpoint(client_id, url, secret, types)
        return True

    def revoke_token(self, token: str) -> bool:
        return self._oauth.revoke_token(token)

    # ── 내부 ─────────────────────────────────────────────────────────────

    def _enforce_rpm(self, client_id: str) -> None:
        client = self._oauth.get_client(client_id)
        limit = client.rpm_limit if client else self._config.default_rpm
        if not self._limiter.check(client_id, limit):
            raise PartnerQuotaError(client_id, limit)

    def _fire_webhook(
        self,
        client_id: str,
        event_type: WebhookEventType,
        payload: dict[str, Any],
    ) -> None:
        event = WebhookEvent(
            event_type=event_type,
            payload=payload,
            client_id=client_id,
        )
        self._webhook.send_event(event)

    def rpm_current(self, client_id: str) -> int:
        return self._limiter.current_count(client_id)

    def webhook_history(self, client_id: str) -> list:
        return self._webhook.get_history(client_id)
