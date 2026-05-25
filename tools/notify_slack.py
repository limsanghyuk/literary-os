#!/usr/bin/env python3
"""
tools/notify_slack.py — V625 신규
Slack Incoming Webhook을 통해 운영 채널에 알림을 전송한다.

Usage:
    python tools/notify_slack.py --msg "Training cycle done"
    python tools/notify_slack.py --channel "#losdb-ops" --msg "RunPod 부족"
    python tools/notify_slack.py --msg "..." --dry-run   # 실제 전송 없이 검증
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional


class SlackNotifier:
    """Slack Incoming Webhook 알림 전송기."""

    DEFAULT_CHANNEL = "#losdb-ops"
    DEFAULT_USERNAME = "Literary OS CI"
    DEFAULT_ICON = ":books:"

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        channel: str = DEFAULT_CHANNEL,
        username: str = DEFAULT_USERNAME,
        icon_emoji: str = DEFAULT_ICON,
        dry_run: bool = False,
    ) -> None:
        self._webhook_url = webhook_url or os.environ.get("SLACK_WEBHOOK_URL", "")
        self._channel = channel
        self._username = username
        self._icon_emoji = icon_emoji
        self._dry_run = dry_run

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def send(self, msg: str, level: str = "info") -> Dict[str, Any]:
        """
        메시지 전송.

        Args:
            msg:   전송할 메시지
            level: "info" | "warn" | "error" — 아이콘/색상 결정

        Returns:
            {"sent": bool, "source": str, "reason": str}
        """
        icon = {"info": ":white_check_mark:", "warn": ":warning:", "error": ":x:"}.get(
            level, ":books:"
        )
        payload = {
            "channel": self._channel,
            "username": self._username,
            "icon_emoji": self._icon_emoji,
            "text": f"{icon} *[Literary OS]* {msg}",
        }

        if self._dry_run:
            return {
                "sent": False,
                "source": "dry_run",
                "reason": f"dry_run — 전송 스킵: {msg[:60]}",
                "payload": payload,
            }

        if not self._webhook_url:
            return {
                "sent": False,
                "source": "no_webhook",
                "reason": "SLACK_WEBHOOK_URL 미설정 — 알림 스킵",
            }

        return self._post(payload)

    def notify_training_start(self, backend: str, run_type: str) -> Dict[str, Any]:
        """훈련 시작 알림."""
        return self.send(f"훈련 시작 — backend={backend}, type={run_type}", level="info")

    def notify_training_done(self, backend: str, elapsed_min: float) -> Dict[str, Any]:
        """훈련 완료 알림."""
        return self.send(
            f"훈련 완료 — backend={backend}, 소요={elapsed_min:.1f}분", level="info"
        )

    def notify_fallback(self, reason: str, fallback_backend: str) -> Dict[str, Any]:
        """폴백 전환 알림."""
        return self.send(
            f"폴백 전환 — {reason} → {fallback_backend}", level="warn"
        )

    def notify_error(self, error: str) -> Dict[str, Any]:
        """오류 알림."""
        return self.send(f"오류 발생 — {error[:200]}", level="error")

    # ------------------------------------------------------------------
    # 내부 구현
    # ------------------------------------------------------------------

    def _post(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        try:
            import urllib.request

            data = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                self._webhook_url,
                data=data,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                body = resp.read().decode()

            if resp.status == 200 and body == "ok":
                return {"sent": True, "source": "webhook", "reason": "전송 성공"}
            return {
                "sent": False,
                "source": "webhook",
                "reason": f"Slack 응답 오류: {resp.status} {body}",
            }

        except Exception as exc:  # noqa: BLE001
            return {
                "sent": False,
                "source": "webhook_error",
                "reason": f"전송 실패: {exc}",
            }


def main() -> int:
    parser = argparse.ArgumentParser(description="Slack 알림 전송")
    parser.add_argument("--channel", default=SlackNotifier.DEFAULT_CHANNEL)
    parser.add_argument("--msg", required=True)
    parser.add_argument("--level", default="info", choices=["info", "warn", "error"])
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    notifier = SlackNotifier(channel=args.channel, dry_run=args.dry_run)
    result = notifier.send(args.msg, level=args.level)

    status = "전송됨" if result["sent"] else f"스킵 ({result['reason']})"
    print(f"[Slack] {status}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
