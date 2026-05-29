#!/usr/bin/env python3
"""
generate_test_inventory.py — pytest 수집 결과를 JSON으로 저장.

Phase A Exit Gate EA-6가 subprocess pytest를 직접 실행하는 대신
이 파일이 생성한 인벤토리를 읽도록 변경 (P1-3 fix).

사용법:
    python tools/generate_test_inventory.py
    python tools/generate_test_inventory.py --output tools/test_inventory.json
"""
from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUTPUT = REPO_ROOT / "tools" / "test_inventory.json"


def collect_tests(test_dir: str = "tests") -> int:
    """pytest --collect-only 실행 후 수집된 테스트 수 반환."""
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", "--collect-only", "-q", test_dir,
],  # e2e 포함 — 전체 수집
        capture_output=True, text=True,
        cwd=str(REPO_ROOT), timeout=120,
    )
    for line in (proc.stdout + proc.stderr).splitlines():
        line = line.strip()
        if "collected" in line or "selected" in line:
            import re
            m = re.search(r"(\d+)\s+(?:test[s]?\s+)?collected", line)
            if m:
                return int(m.group(1))
    # 폴백: 출력 전체에서 숫자 찾기
    import re
    m = re.search(r"(\d+)\s+(?:tests?\s+)?collected", proc.stdout + proc.stderr)
    return int(m.group(1)) if m else 0


def source_hash() -> str:
    """literary_system/ 소스 파일 SHA256 해시 (변경 감지용)."""
    h = hashlib.sha256()
    for f in sorted((REPO_ROOT / "literary_system").rglob("*.py")):
        h.update(f.read_bytes())
    return h.hexdigest()[:16]


def main() -> int:
    parser = argparse.ArgumentParser(description="테스트 인벤토리 생성")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT))
    parser.add_argument("--test-dir", default="tests")
    args = parser.parse_args()

    print("[generate_test_inventory] pytest 수집 중...", flush=True)
    count = collect_tests(args.test_dir)
    src_hash = source_hash()
    now = datetime.now(timezone.utc).isoformat()

    import subprocess as sp
    pytest_ver = sp.run(
        [sys.executable, "-m", "pytest", "--version"],
        capture_output=True, text=True
    ).stdout.strip()

    inventory = {
        "test_count": count,
        "generated_at": now,
        "pytest_version": pytest_ver,
        "source_hash": src_hash,
        "generator": "tools/generate_test_inventory.py",
    }

    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[generate_test_inventory] 완료: {count} tests → {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
