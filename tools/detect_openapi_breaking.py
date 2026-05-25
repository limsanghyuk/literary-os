#!/usr/bin/env python3
"""tools/detect_openapi_breaking.py

OpenAPI SemVer 브레이킹 체인지 탐지 도구 (P-IF-04, V621, ADR-088).

역할:
    현재 SEMVER_MAJOR와 기준 SEMVER_MAJOR를 비교하여
    메이저 버전 변경(=브레이킹 체인지) 여부를 감지한다.
    CI (.github/workflows/openapi_diff.yml) 에서 호출.

사용법:
    python tools/detect_openapi_breaking.py [--baseline MAJOR]
    
    기본 baseline: 1 (v1.x.x 기준)
    
    반환코드:
        0 — 브레이킹 체인지 없음 (메이저 버전 동일)
        1 — 브레이킹 체인지 탐지 (메이저 버전 변경)
        2 — 오류
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(
        description="OpenAPI 브레이킹 체인지 탐지 (P-IF-04, ADR-088)"
    )
    parser.add_argument(
        "--baseline",
        type=int,
        default=1,
        help="기준 메이저 버전 (기본: 1)",
    )
    parser.add_argument(
        "--warn-only",
        action="store_true",
        help="브레이킹 탐지 시 경고만 출력 (exit 0). CI 관대 모드.",
    )
    args = parser.parse_args()

    try:
        from literary_system.serving.model_serving_endpoint import (
            SEMVER_MAJOR,
            SEMVER,
        )
    except ImportError as e:
        print(f"[ERROR] model_serving_endpoint 임포트 실패: {e}", file=sys.stderr)
        return 2

    print(f"현재 API SemVer : {SEMVER}")
    print(f"기준 Major      : {args.baseline}")
    print(f"현재 Major      : {SEMVER_MAJOR}")

    if SEMVER_MAJOR != args.baseline:
        msg = (
            f"[BREAKING] 메이저 버전 변경 감지: "
            f"{args.baseline}.x → {SEMVER_MAJOR}.x — "
            "브레이킹 체인지로 간주합니다."
        )
        if args.warn_only:
            print(f"[WARN] {msg}")
            return 0
        print(f"[FAIL] {msg}", file=sys.stderr)
        return 1

    print(f"[OK] 브레이킹 체인지 없음 (Major={SEMVER_MAJOR})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
