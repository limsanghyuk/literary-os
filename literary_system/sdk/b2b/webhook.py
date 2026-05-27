"""B2B Partner API — Webhook 이벤트 발송 (ADR-118).

Webhook 은 HTTP POST 로 파트너 엔드포인트에 이벤트를 전달한다.
HMAC-SHA256 서명으로 무결성을 보장한다.
실제 HTTP 발송은 `WebhookDeliveryAdapter` 주입으로 교체 가능하다.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import time
from dataclasses import dataclass, field
from enum import Enum
from threading import Lock
from typing import Any, Callable, Protocol


__all__ = [
    "WebhookEventType",
    "WebhookEvent",
    "WebhookEndpoint",
    "WebhookDeliveryResult",
    "WebhookManager",
    "WebhookSignatureError",
]


class WebhookEventType(str, Enum):
    SCENE_ANALYZED = "scene.analyzed"
    SCENE_GENERATED = "scene.generated"
    SCENE_REPAIRED = "scene.repaired"
    FEEDBACK_RECEIVED = "feedback.received"
    QUOTA_WARNING = "quota.warning"
    QUOTA_EXCEEDED = "quota.exceeded"


@dataclass
class WebhookEvent:
    """전송할 Webhook 이벤트."""
    event_type: WebhookEventType
    payload: dict[str, Any]
    client_id: str
    event_id: str = field(default_factory=lambda: _gen_id("evt"))
    timestamp: float = field(default_factory=time.time)
    attempt: int = 1


@dataclass
class WebhookEndpoint:
    """파트너 Webhook 수신 엔드포인트."""
    client_id: str
    url: str
    secret: str                      # HMAC 서명 시크릿
    event_types: list[WebhookEventType] = field(default_factory=list)
    is_active: bool = True
    max_retries: int = 3


@dataclass
class WebhookDeliveryResult:
    """Webhook 발송 결과."""
    event_id: str
    client_id: str
    url: str
    success: bool
    status_code: int = 0
    attempt: int = 1
    error: str = ""
    delivered_at: float = field(default_factory=time.time)


class WebhookSignatureError(Exception):
    """서명 검증 실패."""


# ── 헬퍼 ──────────────────────────────────────────────────────────────────

def _gen_id(prefix: str) -> str:
    import secrets
    return f"{prefix}_{secrets.token_hex(8)}"


def sign_payload(payload_bytes: bytes, secret: str) -> str:
    """HMAC-SHA256 서명 생성."""
    return hmac.new(secret.encode(), payload_bytes, hashlib.sha256).hexdigest()


def verify_signature(payload_bytes: bytes, secret: str, signature: str) -> bool:
    """서명 검증 (timing-safe)."""
    expected = sign_payload(payload_bytes, secret)
    return hmac.compare_digest(expected, signature)


# ── Webhook 매니저 ────────────────────────────────────────────────────────

# 발송 어댑터 프로토콜 (테스트에서 mock 주입)
class DeliveryAdapter(Protocol):
    def send(self, url: str, headers: dict, body: bytes) -> int:
        """HTTP POST 발송 후 status_code 반환."""
        ...


class _StubDeliveryAdapter:
    """테스트용 stub — 항상 200 반환."""
    def send(self, url: str, headers: dict, body: bytes) -> int:
        return 200


class WebhookManager:
    """Webhook 이벤트 라이프사이클 관리.

    - 엔드포인트 등록/해제
    - 이벤트 발송 (HMAC 서명 포함)
    - 발송 이력 보관 (최대 1,000건)
    """

    MAX_HISTORY = 1_000

    def __init__(self, adapter: DeliveryAdapter | None = None) -> None:
        self._endpoints: dict[str, WebhookEndpoint] = {}   # client_id → endpoint
        self._history: list[WebhookDeliveryResult] = []
        self._lock = Lock()
        self._adapter: DeliveryAdapter = adapter or _StubDeliveryAdapter()

    def register_endpoint(
        self,
        client_id: str,
        url: str,
        secret: str,
        event_types: list[WebhookEventType] | None = None,
    ) -> WebhookEndpoint:
        ep = WebhookEndpoint(
            client_id=client_id,
            url=url,
            secret=secret,
            event_types=event_types or list(WebhookEventType),
        )
        with self._lock:
            self._endpoints[client_id] = ep
        return ep

    def deregister_endpoint(self, client_id: str) -> bool:
        with self._lock:
            ep = self._endpoints.pop(client_id, None)
            return ep is not None

    def send_event(self, event: WebhookEvent) -> WebhookDeliveryResult | None:
        """이벤트를 파트너 엔드포인트에 발송."""
        with self._lock:
            ep = self._endpoints.get(event.client_id)

        if ep is None or not ep.is_active:
            return None
        if ep.event_types and event.event_type not in ep.event_types:
            return None

        body = json.dumps({
            "event_id": event.event_id,
            "event_type": event.event_type.value,
            "client_id": event.client_id,
            "timestamp": event.timestamp,
            "payload": event.payload,
        }, ensure_ascii=False).encode()

        signature = sign_payload(body, ep.secret)
        headers = {
            "Content-Type": "application/json",
            "X-LOS-Signature": f"sha256={signature}",
            "X-LOS-Event-ID": event.event_id,
            "X-LOS-Event-Type": event.event_type.value,
        }

        try:
            status = self._adapter.send(ep.url, headers, body)
            success = 200 <= status < 300
        except Exception as exc:
            result = WebhookDeliveryResult(
                event_id=event.event_id,
                client_id=event.client_id,
                url=ep.url,
                success=False,
                error=str(exc),
                attempt=event.attempt,
            )
        else:
            result = WebhookDeliveryResult(
                event_id=event.event_id,
                client_id=event.client_id,
                url=ep.url,
                success=success,
                status_code=status,
                attempt=event.attempt,
            )

        self._append_history(result)
        return result

    def _append_history(self, result: WebhookDeliveryResult) -> None:
        with self._lock:
            self._history.append(result)
            if len(self._history) > self.MAX_HISTORY:
                self._history = self._history[-self.MAX_HISTORY:]

    def get_history(self, client_id: str | None = None) -> list[WebhookDeliveryResult]:
        with self._lock:
            if client_id:
                return [r for r in self._history if r.client_id == client_id]
            return list(self._history)

    def endpoint_count(self) -> int:
        with self._lock:
            return len(self._endpoints)
