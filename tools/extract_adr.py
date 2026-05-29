#!/usr/bin/env python3
"""
V578 — tools/extract_adr.py
ADR 자동 추출 도구 (ADR-032 retroactive automation).

git log + grep 기반으로 커밋 메시지와 소스 코드에서
ADR 참조를 자동 추출하여 docs/adr/INDEX.md 생성.

사용법:
    python tools/extract_adr.py [--output docs/adr/INDEX.md]
"""
import os
import re
import subprocess
import sys
from pathlib import Path


def extract_adr_from_git_log() -> dict:
    """git log에서 ADR-NNN 패턴 추출."""
    adr_mentions = {}
    try:
        result = subprocess.run(
            ["git", "log", "--oneline", "--all"],
            capture_output=True, text=True, cwd=Path(__file__).parent.parent
        )
        for line in result.stdout.splitlines():
            matches = re.findall(r'ADR-(\d+)', line)
            for m in matches:
                adr_id = f"ADR-{int(m):03d}"
                if adr_id not in adr_mentions:
                    adr_mentions[adr_id] = {"commit": line[:60], "sources": ["git_log"]}
    except Exception as e:
        print(f"git log 추출 실패: {e}", file=sys.stderr)
    return adr_mentions


def extract_adr_from_sources(root: Path) -> dict:
    """소스 코드와 문서에서 ADR-NNN 패턴 추출."""
    adr_mentions = {}
    search_dirs = ["literary_system", "tests", "docs"]
    for d in search_dirs:
        dir_path = root / d
        if not dir_path.exists():
            continue
        for path in dir_path.rglob("*.py"):
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                matches = re.findall(r'ADR-(\d+)', content)
                for m in matches:
                    adr_id = f"ADR-{int(m):03d}"
                    rel = str(path.relative_to(root))
                    if adr_id not in adr_mentions:
                        adr_mentions[adr_id] = {"sources": []}
                    if rel not in adr_mentions[adr_id]["sources"]:
                        adr_mentions[adr_id]["sources"].append(rel)
            except Exception:
                pass
        for path in dir_path.rglob("*.md"):
            try:
                content = path.read_text(encoding="utf-8", errors="ignore")
                matches = re.findall(r'ADR-(\d+)', content)
                for m in matches:
                    adr_id = f"ADR-{int(m):03d}"
                    rel = str(path.relative_to(root))
                    if adr_id not in adr_mentions:
                        adr_mentions[adr_id] = {"sources": []}
                    if rel not in adr_mentions[adr_id]["sources"]:
                        adr_mentions[adr_id]["sources"].append(rel)
            except Exception:
                pass
    return adr_mentions


def find_existing_adr_files(adr_dir: Path) -> dict:
    """docs/adr/ 내 ADR 파일 목록."""
    existing = {}
    if not adr_dir.exists():
        return existing
    for p in adr_dir.glob("ADR-*.md"):
        m = re.search(r'ADR-(\d+)', p.name)
        if m:
            adr_id = f"ADR-{int(m.group(1)):03d}"
            existing[adr_id] = p.name
    return existing


def generate_index(root: Path, output: Path) -> None:
    """ADR INDEX.md 생성."""
    git_adrs = extract_adr_from_git_log()
    src_adrs = extract_adr_from_sources(root)
    adr_dir = root / "docs" / "adr"
    existing = find_existing_adr_files(adr_dir)

    # 모든 ADR 집합
    all_adrs = sorted(set(git_adrs) | set(src_adrs) | set(existing))

    lines = [
        "# ADR 자동 추출 인덱스",
        "",
        "> 자동 생성: `tools/extract_adr.py` (ADR-032 retroactive automation)",
        "",
        f"총 {len(all_adrs)}개 ADR 참조 발견",
        "",
        "| ADR | 문서 파일 | 소스 참조 수 | git 커밋 |",
        "|-----|---------|------------|---------|",
    ]

    for adr_id in all_adrs:
        file_name = existing.get(adr_id, "—")
        src_count = len(src_adrs.get(adr_id, {}).get("sources", []))
        commit = git_adrs.get(adr_id, {}).get("commit", "—")[:50] if adr_id in git_adrs else "—"
        if file_name != "—":
            file_link = f"[{file_name}]({file_name})"
        else:
            file_link = "—"
        lines.append(f"| {adr_id} | {file_link} | {src_count} | {commit} |")

    lines.extend(["", "---", f"*생성 시각: V578 (2026-05-19)*"])
    output.write_text("\n".join(lines), encoding="utf-8")
    print(f"INDEX.md 생성: {output} ({len(all_adrs)}개 ADR)")


if __name__ == "__main__":
    root = Path(__file__).parent.parent
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else root / "docs" / "adr" / "INDEX.md"
    generate_index(root, output_path)
