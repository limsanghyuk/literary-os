#!/usr/bin/env python3
"""
V587 ADR-048: 버전·문서 정합 검사 — 6파일 SSoT 검증

pyproject.toml의 version 및 Gate 수가
README / CHANGELOG / MANIFEST / ci.yml / git tag
모두와 일치하는지 검사한다.

사용법:
    python tools/check_version_consistency.py              # 보고서만
    python tools/check_version_consistency.py --strict     # 불일치 시 exit(1)
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
PYPROJECT  = REPO_ROOT / "pyproject.toml"
README     = REPO_ROOT / "README.md"
CHANGELOG  = REPO_ROOT / "CHANGELOG.md"
MANIFEST   = REPO_ROOT / "MANIFEST.md"
CI_YML     = REPO_ROOT / ".github" / "workflows" / "ci.yml"


# ── 버전 추출 헬퍼 ────────────────────────────────────────────────────────────

def get_pyproject_version() -> str:
    text = PYPROJECT.read_text(encoding="utf-8")
    m = re.search(r'^version\s*=\s*"([^"]+)"', text, re.MULTILINE)
    return m.group(1) if m else "N/A"


def get_gate_count_live() -> int:
    """literary_system.gates.release_gate에서 실제 등록된 Gate 수 반환."""
    try:
        sys.path.insert(0, str(REPO_ROOT))
        from literary_system.gates.release_gate import run_release_gate
        r = run_release_gate()
        return r.get("total_gates", 0)
    except Exception:
        return 0


def get_latest_git_tag() -> str:
    try:
        result = subprocess.run(
            ["git", "describe", "--tags", "--abbrev=0"],
            capture_output=True, text=True, cwd=str(REPO_ROOT)
        )
        tag = result.stdout.strip()
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


def get_readme_gate_count() -> str:
    """README 뱃지에서 Gate 수 추출. 형식: release%20gates-NN%2FNN"""
    if not README.exists():
        return "N/A"
    text = README.read_text(encoding="utf-8")
    m = re.search(r'release%20gates-(\d+)%2F(\d+)', text)
    if m:
        return m.group(1)  # "passed/total" 중 total
    # 대안 형식: gates-44/44
    m2 = re.search(r'gates-(\d+)/(\d+)', text)
    return m2.group(2) if m2 else "N/A"


def get_changelog_version() -> str:
    """CHANGELOG.md의 최상단 ## [X.Y.Z] 버전 추출."""
    if not CHANGELOG.exists():
        return "N/A"
    text = CHANGELOG.read_text(encoding="utf-8")
    m = re.search(r'^## \[?(\d+\.\d+\.\d+)\]?', text, re.MULTILINE)
    return m.group(1) if m else "N/A"


def get_manifest_version() -> str:
    """MANIFEST.md의 Version: X.Y.Z 추출."""
    if not MANIFEST.exists():
        return "N/A"
    text = MANIFEST.read_text(encoding="utf-8")
    m = re.search(r'버전:\s*(\d+\.\d+\.\d+)', text)
    if not m:
        m = re.search(r'[Vv]ersion:\s*(\d+\.\d+\.\d+)', text)
    return m.group(1) if m else "N/A"


def get_ci_gate_count() -> str:
    """ci.yml Release Gate 잡 이름에서 Gate 수 추출."""
    if not CI_YML.exists():
        return "N/A"
    text = CI_YML.read_text(encoding="utf-8")
    m = re.search(r'Release Gate[^(]*\((\d+) Gates', text)
    return m.group(1) if m else "N/A"


def get_current_branch() -> str:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            capture_output=True, text=True, cwd=str(REPO_ROOT)
        )
        return result.stdout.strip()
    except Exception:
        return "unknown"


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="V587 ADR-048: 6파일 버전·Gate 정합 검사")
    parser.add_argument("--strict", action="store_true", help="불일치 시 exit(1)")
    parser.add_argument("--no-live-gate", action="store_true", help="live Gate 수 측정 생략 (빠른 모드)")
    args = parser.parse_args()

    pyproject_ver  = get_pyproject_version()
    git_tag_ver    = get_latest_git_tag()
    readme_ver     = get_readme_version()
    changelog_ver  = get_changelog_version()
    manifest_ver   = get_manifest_version()
    ci_gate_str    = get_ci_gate_count()
    readme_gate    = get_readme_gate_count()

    live_gate_count = 0 if args.no_live_gate else get_gate_count_live()
    live_gate_str  = str(live_gate_count) if live_gate_count else "SKIP"

    print(f"\n{'='*65}")
    print("  Literary OS — Version & Gate Consistency Check  (ADR-048)")
    print(f"{'='*65}")
    print(f"  [SSoT]  pyproject.toml version : {pyproject_ver}")
    print(f"  [SSoT]  live gate count         : {live_gate_str}")
    print(f"  -------------------------------------------------------")
    print(f"  git latest tag                  : {git_tag_ver}")
    print(f"  README version badge            : {readme_ver}")
    print(f"  README gate badge               : {readme_gate}")
    print(f"  CHANGELOG latest                : {changelog_ver}")
    print(f"  MANIFEST version                : {manifest_ver}")
    print(f"  ci.yml gate count               : {ci_gate_str}")

    # ── 브랜치 판별 ──────────────────────────────────────────────────────────
    github_head_ref = os.environ.get("GITHUB_HEAD_REF", "")
    github_ref      = os.environ.get("GITHUB_REF", "")
    current_branch  = get_current_branch()
    is_pr  = bool(github_head_ref) or "/pull/" in github_ref
    is_main = (current_branch in ("main", "master") and not is_pr)

    # ── 불일치 검사 ──────────────────────────────────────────────────────────
    mismatches: list[str] = []
    warnings:   list[str] = []

    # 1. 버전 일치
    for label, val in [
        ("README badge",    readme_ver),
        ("CHANGELOG",       changelog_ver),
        ("MANIFEST",        manifest_ver),
    ]:
        if val != "N/A" and val != pyproject_ver:
            mismatches.append(f"pyproject({pyproject_ver}) ≠ {label}({val})")

    # 2. git tag — main 브랜치에서만 강제
    if git_tag_ver != "N/A" and git_tag_ver != pyproject_ver:
        if is_main:
            mismatches.append(f"pyproject({pyproject_ver}) ≠ git tag({git_tag_ver})")
        else:
            branch_display = github_head_ref or current_branch
            warnings.append(f"git tag 미생성 (feature 브랜치={branch_display}) — main 머지 후 태그 생성 예정")

    # 3. Gate 수 일치
    if live_gate_str != "SKIP":
        if readme_gate != "N/A" and readme_gate != live_gate_str:
            mismatches.append(f"live gate({live_gate_str}) ≠ README gate badge({readme_gate})")
        if ci_gate_str != "N/A" and ci_gate_str != live_gate_str:
            mismatches.append(f"live gate({live_gate_str}) ≠ ci.yml({ci_gate_str})")

    # ── 결과 출력 ─────────────────────────────────────────────────────────────
    print(f"{'='*65}")
    if warnings:
        print("  ⚠️  경고:")
        for w in warnings:
            print(f"    → {w}")
    if not mismatches:
        print("  ✅  ALL CONSISTENT")
    else:
        print("  ❌  불일치 항목:")
        for ms in mismatches:
            print(f"    → {ms}")
    print(f"{'='*65}\n")

    if mismatches and args.strict:
        print("Version/Gate consistency FAILED (--strict mode)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
