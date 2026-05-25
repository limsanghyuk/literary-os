#!/usr/bin/env python3
"""tools/export_openapi.py

OpenAPI 스키마를 YAML/JSON으로 내보내는 유틸리티 (P-IF-04, V621).

사용법:
    python tools/export_openapi.py [--format yaml|json] [--output PATH]
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))


def main() -> int:
    parser = argparse.ArgumentParser(description="OpenAPI 스키마 내보내기")
    parser.add_argument("--format", choices=["yaml", "json"], default="json")
    parser.add_argument("--output", default=None, help="출력 파일 경로 (기본: stdout)")
    args = parser.parse_args()

    from literary_system.serving.model_serving_endpoint import get_openapi_schema

    schema = get_openapi_schema()

    if args.format == "yaml":
        try:
            import yaml
            content = yaml.safe_dump(schema, allow_unicode=True)
        except ImportError:
            content = json.dumps(schema, ensure_ascii=False, indent=2)
    else:
        content = json.dumps(schema, ensure_ascii=False, indent=2)

    if args.output:
        Path(args.output).write_text(content, encoding="utf-8")
        print(f"[OK] 내보내기 완료: {args.output}")
    else:
        print(content)
    return 0


if __name__ == "__main__":
    sys.exit(main())
