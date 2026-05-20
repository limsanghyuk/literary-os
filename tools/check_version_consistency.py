#!/usr/bin/env python3
"""
H-05: 버전 정합 검사 — pyproject.toml ↔ git tag ↔ README

pyproject.toml의 version과 최신 git tag, README 배지가
모두 일치하는지 검사한다.

사용법:
    python tools/check_version_consistency.py              # 보고서만
    python tools/check_version_consistency.py --strict     # 불일치 시 exit(1)
"""
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT  = Path(__file__).resolve().parent.parent
PYPROJECT  = REPO_ROOT / "pyproject.toml"
README     = REPO_ROOT / "README.md"


def get_pyproject_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return m.group(1) if m else "N/A"


def get_latest_git_tag() -> str:
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, cwd=str(REPO_ROOT)
        )
        tag = result.stdout.strip()
        # Extract semver part: v8.0.0-V575 → 8.0.0
        m = re.match(r"v?(\d+\.\d+\.\d+)", tag)
        return m.group(1) if m else tag
    except Exception:
        return "N/A"


def get_readme_version() -> str:
    if not README.exists():
        return "N/A"
    text = README.read_text(encoding="utf-8")
    m = re.search(r'version-(\d+\.\d+\.\d+)-blue', text)
    return m.group(1) if m else "N/A"

def get_current_branch() -> str:
    """현재 git 브랜치 이름 반환."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT)
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"




def main() -> int:
    parser = argparse.ArgumentParser(description="버전 정합 검사")
    parser.add_argument("--strict", action="store_true")
    args = parser.parse_args()

    pyproject_ver = get_pyproject_version()
    git_tag_ver   = get_latest_git_tag()
    readme_ver    = get_readme_version()

    print(f"\n{'='*60}")
    print("Version Consistency Check")
    print(f"{'='*60}")
    print(f"  pyproject.toml : {pyproject_ver}")
    print(f"  git latest tag : {git_tag_ver}")
    print(f"  README badge   : {readme_ver}")

    mismatches = []
    current_branch = get_current_branch()
    # GitHub Actions PR 환경: GITHUB_HEAD_REF가 설정되면 feature 브랜치
    import os as _os
    github_head_ref = _os.environ.get("GITHUB_HEAD_REF", "")
    github_ref = _os.environ.get("GITHUB_REF", "")
    is_pr = bool(github_head_ref) or "/pull/" in github_ref
    is_main = (current_branch in ("main", "master") and not is_pr)
    if git_tag_ver != "N/A" and pyproject_ver != git_tag_ver:
        if is_main:
            mismatches.append(f"pyproject({pyproject_ver}) ≠ git tag({git_tag_ver})")
        else:
            branch_display = github_head_ref or current_branch
            print(f"  ⚠️  git tag 미생성 (feature 브랜치={branch_display}) — main 머지 후 태그 생성 예정")
    if readme_ver != "N/A" and pyproject_ver != readme_ver:
        mismatches.append(f"pyproject({pyproject_ver}) ≠ README badge({readme_ver})")

    print()
    if not mismatches:
        print("  ✅ ALL CONSISTENT")
    else:
        print("  ❌ 불일치:")
        for m in mismatches:
            print(f"    → {m}")
    print(f"{'='*60}\n")

    if mismatches and args.strict:
        print("Version consistency FAILED (--strict)")
        return 1
    return 0




if __name__ == "__main__":
    sys.exit(main())
