#!/usr/bin/env python3
"""
V587: CHANGELOG.md에서 특정 버전 섹션을 추출 (GitHub Release body용).

사용법:
    python tools/extract_changelog_section.py --version 9.2.0 --output /tmp/body.md
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CHANGELOG  = REPO_ROOT / "CHANGELOG.md"


def extract_section(version: str) -> str | None:
    if not CHANGELOG.exists():
        return None
    text = CHANGELOG.read_text(encoding="utf-8")
    # ## [9.2.0] 또는 ## 9.2.0 형태 모두 지원
    pattern = rf'(## \[?{re.escape(version)}\]?.*?)(?=\n## |\Z)'
    m = re.search(pattern, text, re.DOTALL)
    return m.group(1).strip() if m else None


def main() -> int:
    parser = argparse.ArgumentParser(description="CHANGELOG 섹션 추출")
    parser.add_argument("--version", required=True, help="추출할 버전 (예: 9.2.0)")
    parser.add_argument("--output", default=None, help="출력 파일 경로 (없으면 stdout)")
    args = parser.parse_args()

    section = extract_section(args.version)
    if not section:
        print(f"No changelog entry found for version {args.version}", file=sys.stderr)
        return 1

    if args.output:
        Path(args.output).write_text(section, encoding="utf-8")
        print(f"Written to {args.output}")
    else:
        print(section)
    return 0


if __name__ == "__main__":
    sys.exit(main())
