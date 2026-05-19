#!/usr/bin/env python3
"""
Preflight Step 15 — Security & Hygiene CI 게이트 (V575)

다음 3가지 위생 규칙을 자동 검사한다:

  Rule-1 (CRITICAL): DEV_MODE 기본값 — os.environ.get("LITERARY_OS_DEV_MODE", "true") 는 금지.
                     반드시 "false" 여야 한다 (인증 bypass 기본 비활성화).

  Rule-2 (HIGH):     literary_system/ 내 print() 사용 금지.
                     logging 모듈을 통해서만 출력해야 한다.

  Rule-3 (MEDIUM):   bare except: 금지.
                     반드시 except Exception: 또는 구체적 예외를 명시해야 한다.

사용법:
    python tools/preflight_step15.py              # 보고서만 출력
    python tools/preflight_step15.py --strict     # 위반 발견 시 exit(1)
"""

from __future__ import annotations

import ast
import re
import sys
import argparse
from pathlib import Path
from typing import NamedTuple

REPO_ROOT     = Path(__file__).resolve().parent.parent
SYSTEM_ROOT   = REPO_ROOT / "literary_system"
APPS_ROOT     = REPO_ROOT / "apps"
MIDDLEWARE_FILE = APPS_ROOT / "studio_api" / "auth" / "middleware.py"

# ─── 결과 타입 ───────────────────────────────────────────────────────────────
class Violation(NamedTuple):
    rule:    str
    level:   str     # CRITICAL / HIGH / MEDIUM
    file:    str
    lineno:  int
    detail:  str


# ─── Rule-1: DEV_MODE 기본값 검사 ────────────────────────────────────────────
def check_devmode_default() -> list[Violation]:
    violations = []
    if not MIDDLEWARE_FILE.exists():
        return violations
    text = MIDDLEWARE_FILE.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), 1):
        # 주석 라인 제외
        if line.lstrip().startswith("#") or line.lstrip().startswith('"""') or line.lstrip().startswith("'''"):
            continue
        # 금지 패턴: os.environ.get("LITERARY_OS_DEV_MODE", "true") — 코드에서만 검사
        if re.search(r'os\.environ\.get\(["\']LITERARY_OS_DEV_MODE["\'],\s*["\']true["\']', line):
            violations.append(Violation(
                rule="Rule-1",
                level="CRITICAL",
                file=str(MIDDLEWARE_FILE.relative_to(REPO_ROOT)),
                lineno=i,
                detail=f'DEV_MODE 기본값이 "true" — 인증 bypass 위험. "false"로 변경 필요.',
            ))
    return violations


# ─── Rule-2: print() 사용 검사 ────────────────────────────────────────────────
def check_print_statements() -> list[Violation]:
    violations = []
    for py_file in SYSTEM_ROOT.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.lstrip()
            # 주석이나 독스트링 내부 제외 (단순 휴리스틱: # 로 시작하면 skip)
            if stripped.startswith("#"):
                continue
            if re.match(r'\bprint\s*\(', stripped):
                violations.append(Violation(
                    rule="Rule-2",
                    level="HIGH",
                    file=str(py_file.relative_to(REPO_ROOT)),
                    lineno=i,
                    detail=f"print() 발견 — logging.getLogger(__name__) 사용 필요.",
                ))
    return violations


# ─── Rule-3: bare except 검사 ────────────────────────────────────────────────
def check_bare_excepts() -> list[Violation]:
    violations = []
    for py_file in SYSTEM_ROOT.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text, filename=str(py_file))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if not isinstance(node, ast.ExceptHandler):
                continue
            if node.type is None:   # bare except:
                violations.append(Violation(
                    rule="Rule-3",
                    level="MEDIUM",
                    file=str(py_file.relative_to(REPO_ROOT)),
                    lineno=node.lineno,
                    detail="bare except: 발견 — except Exception: 또는 구체적 예외 명시 필요.",
                ))
    return violations


# ─── 보고서 출력 ──────────────────────────────────────────────────────────────
def print_report(violations: list[Violation]) -> None:
    by_rule: dict[str, list[Violation]] = {}
    for v in violations:
        by_rule.setdefault(v.rule, []).append(v)

    print(f"\n{'='*70}")
    print("Preflight Step 15 — Security & Hygiene (V575)")
    print(f"{'='*70}")
    print(f"  Rule-1 (CRITICAL) — DEV_MODE 기본값 : {len(by_rule.get('Rule-1', []))} 건")
    print(f"  Rule-2 (HIGH)     — print() 사용    : {len(by_rule.get('Rule-2', []))} 건")
    print(f"  Rule-3 (MEDIUM)   — bare except     : {len(by_rule.get('Rule-3', []))} 건")
    print(f"  합계                                : {len(violations)} 건")
    print()

    if not violations:
        print("  ✅ ALL CLEAR — 모든 위생 규칙 통과")
    else:
        for rule, vlist in sorted(by_rule.items()):
            print(f"  [{vlist[0].level}] {rule}:")
            for v in vlist:
                print(f"    {v.file}:{v.lineno}")
                print(f"      → {v.detail}")
            print()

    print(f"{'='*70}\n")


# ─── main ─────────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight Step 15 — Hygiene Gate")
    parser.add_argument("--strict", action="store_true",
                        help="위반 발견 시 exit(1) — CI 블로킹 모드")
    args = parser.parse_args()

    violations: list[Violation] = []
    violations += check_devmode_default()
    violations += check_print_statements()
    violations += check_bare_excepts()

    print_report(violations)

    if violations and args.strict:
        print("Preflight Step 15 FAILED (--strict 모드)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
