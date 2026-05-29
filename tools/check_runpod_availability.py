#!/usr/bin/env python3
"""
tools/check_runpod_availability.py — V625 신규
RunPod GPU 가용성을 확인하고 상태를 stdout + exit code로 반환한다.

Exit codes:
    0  가용 GPU 존재 → 훈련 진행 가능
    1  가용 GPU 없음 또는 API 오류 → Lambda 폴백 필요
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from typing import Any, Dict, Optional


class RunPodChecker:
    """RunPod GPU 가용성 체커."""

    DEFAULT_API_BASE = "https://api.runpod.io/v1"
    DEFAULT_GPU_TYPE = "RTX_4090"
    FALLBACK_GPU_TYPES = ["A100_SXM", "RTX_3090", "A6000"]

    def __init__(
        self,
        api_key: Optional[str] = None,
        api_base: str = DEFAULT_API_BASE,
        gpu_type: str = DEFAULT_GPU_TYPE,
        dry_run: bool = False,
    ) -> None:
        self._api_key = api_key or os.environ.get("RUNPOD_API_KEY", "")
        self._api_base = api_base
        self._gpu_type = gpu_type
        self._dry_run = dry_run

    # ------------------------------------------------------------------
    # 공개 API
    # ------------------------------------------------------------------

    def check(self) -> Dict[str, Any]:
        """
        가용성 확인 후 결과 dict 반환.

        Returns:
            {
                "available": bool,
                "gpu_type": str,
                "count": int,
                "source": "api" | "dry_run" | "no_key",
                "reason": str,
            }
        """
        if self._dry_run:
            return {
                "available": True,
                "gpu_type": self._gpu_type,
                "count": 4,
                "source": "dry_run",
                "reason": "dry_run 모드 — 항상 가용",
            }

        if not self._api_key:
            return {
                "available": False,
                "gpu_type": self._gpu_type,
                "count": 0,
                "source": "no_key",
                "reason": "RUNPOD_API_KEY 환경변수 미설정",
            }

        return self._query_api()

    def is_available(self) -> bool:
        """가용 여부만 반환 (bool)."""
        return self.check()["available"]

    # ------------------------------------------------------------------
    # 내부 구현
    # ------------------------------------------------------------------

    def _query_api(self) -> Dict[str, Any]:
        """실제 RunPod API 호출."""
        try:
            import urllib.request

            req = urllib.request.Request(
                f"{self._api_base}/gpu/availability",
                headers={
                    "Authorization": f"Bearer {self._api_key}",
                    "Content-Type": "application/json",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            # API 응답에서 gpu_type별 가용 수 추출
            available_gpus = data.get("gpus", {})
            count = available_gpus.get(self._gpu_type, 0)

            if count > 0:
                return {
                    "available": True,
                    "gpu_type": self._gpu_type,
                    "count": count,
                    "source": "api",
                    "reason": f"{self._gpu_type} {count}개 가용",
                }

            # 폴백 GPU 타입 순차 확인
            for fallback in self.FALLBACK_GPU_TYPES:
                fb_count = available_gpus.get(fallback, 0)
                if fb_count > 0:
                    return {
                        "available": True,
                        "gpu_type": fallback,
                        "count": fb_count,
                        "source": "api",
                        "reason": f"폴백 {fallback} {fb_count}개 가용",
                    }

            return {
                "available": False,
                "gpu_type": self._gpu_type,
                "count": 0,
                "source": "api",
                "reason": "요청 GPU 타입 전체 소진",
            }

        except Exception as exc:  # noqa: BLE001
            return {
                "available": False,
                "gpu_type": self._gpu_type,
                "count": 0,
                "source": "api_error",
                "reason": f"API 오류: {exc}",
            }


def main() -> int:
    parser = argparse.ArgumentParser(description="RunPod GPU 가용성 확인")
    parser.add_argument("--gpu-type", default=RunPodChecker.DEFAULT_GPU_TYPE)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true", help="JSON 출력")
    args = parser.parse_args()

    checker = RunPodChecker(gpu_type=args.gpu_type, dry_run=args.dry_run)
    result = checker.check()

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        status = "✓ 가용" if result["available"] else "✗ 불가"
        print(f"[RunPod] {status} | {result['reason']}")

    return 0 if result["available"] else 1


if __name__ == "__main__":
    sys.exit(main())
