#!/usr/bin/env python3
"""tools/generate_sha256sums.py — V745 SP-E.0 (TD-E0-1)

저장소 파일 SHA-256 매니페스트(SHA256SUMS.txt)를 재생성한다.
릴리즈 자기검증용. 막판 패치 후 반드시 재실행하여 매니페스트 stale 방지.
형식: "<sha256>  <relpath>" (coreutils sha256sum 호환), 경로 정렬.
"""
from __future__ import annotations
import hashlib
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "SHA256SUMS.txt"
EXCLUDE_DIRS = {".git", "__pycache__", ".pytest_cache", ".mypy_cache", "literary_os.egg-info"}
EXCLUDE_FILES = {"SHA256SUMS.txt", "SHA256SUMS.txt.sig"}


def _iter_files():
    for p in sorted(REPO.rglob("*")):
        if not p.is_file():
            continue
        rel = p.relative_to(REPO)
        if any(part in EXCLUDE_DIRS for part in rel.parts):
            continue
        if p.suffix == ".pyc":
            continue
        if rel.as_posix() in EXCLUDE_FILES:
            continue
        yield rel


def main() -> int:
    lines = []
    for rel in _iter_files():
        digest = hashlib.sha256((REPO / rel).read_bytes()).hexdigest()
        lines.append(f"{digest}  {rel.as_posix()}")
    OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    sys.stdout.write(f"[generate_sha256sums] {len(lines)} files -> {OUT.name}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
