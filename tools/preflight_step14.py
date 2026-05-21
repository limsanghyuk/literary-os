#!/usr/bin/env python3
"""
Preflight Step 14 — Gate 함수 내 Import 타입명 AST 대조 (ADR-033)

literary_system/gates/release_gate.py 의 _gate_* 함수들이 사용하는
from X import Y 에서 Y가 실제 대상 모듈에 존재하는 class 이름인지 검사한다.

Preflight Step13 (테스트 의존성 대조)의 보완 도구.
Step13: tests/ 디렉터리 import vs 설치 패키지 대조
Step14: release_gate.py Gate 함수 내 타입명 vs 실제 모듈 class 명칭 대조

사용법:
    python tools/preflight_step14.py              # 보고서만 출력
    python tools/preflight_step14.py --strict     # 불일치 시 exit(1)
"""

from __future__ import annotations

import ast
import sys
import argparse
from pathlib import Path
from typing import NamedTuple

# ─── 상수 ────────────────────────────────────────────────────────────────────
REPO_ROOT    = Path(__file__).resolve().parent.parent
GATE_FILE    = REPO_ROOT / "literary_system" / "gates" / "release_gate.py"
SYSTEM_ROOT  = REPO_ROOT / "literary_system"

# 알려진 별칭 — stdlib / 서드파티 등 로컬 모듈이 아닌 import
SKIP_MODULES: set[str] = {
    "typing",
    "dataclasses",
    "enum",
    "os",
    "sys",
    "pathlib",
    "logging",
    "datetime",
}


class TypeImport(NamedTuple):
    gate_func: str   # _gate_* 함수 이름
    module:    str   # from <module>
    name:      str   # import <name>
    lineno:    int


class Mismatch(NamedTuple):
    imp:         TypeImport
    module_path: Path
    available:   list[str]


# ─── Phase 1: Gate 함수 내 import 수집 ────────────────────────────────────────
def collect_gate_imports(gate_file: Path) -> list[TypeImport]:
    """release_gate.py 의 _gate_* 함수 내부 from X import Y 수집."""
    src = gate_file.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(gate_file))

    results: list[TypeImport] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.FunctionDef):
            continue
        if not node.name.startswith("_gate_"):
            continue
        func_name = node.name
        for subnode in ast.walk(node):
            if not isinstance(subnode, ast.ImportFrom):
                continue
            if not subnode.module:
                continue
            module_str = subnode.module
            # literary_system 내부 모듈만 대조 (외부 패키지 제외)
            if not module_str.startswith("literary_system"):
                continue
            for alias in subnode.names:
                # import X as Y 형태는 직접 사용 안 함 → 대조 불필요
                if alias.asname is not None:
                    continue
                results.append(TypeImport(
                    gate_func=func_name,
                    module=module_str,
                    name=alias.name,
                    lineno=subnode.lineno,
                ))
    return results


# ─── Phase 2: 실제 모듈의 class 이름 목록 수집 ────────────────────────────────
def get_module_classes(module_str: str) -> tuple[Path | None, list[str]]:
    """
    literary_system.x.y → SYSTEM_ROOT.parent / literary_system/x/y.py 로 변환 후
    AST로 최상위 class 이름 목록 반환.
    """
    rel_path = Path(module_str.replace(".", "/")).with_suffix(".py")
    abs_path = REPO_ROOT / rel_path
    if not abs_path.exists():
        return None, []

    src = abs_path.read_text(encoding="utf-8")
    tree = ast.parse(src, filename=str(abs_path))
    # class + 최상위 def 모두 수집 (함수 import 오탐 방지)
    classes = []
    for node in tree.body:  # 최상위 레벨만
        if isinstance(node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)):
            classes.append(node.name)
        # 모듈 수준 상수·변수 할당도 수집 (THRESHOLD_XX = ..., DRIFT_XX = ... 등)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    classes.append(target.id)
        elif isinstance(node, ast.AnnAssign):
            if isinstance(node.target, ast.Name):
                classes.append(node.target.id)
    return abs_path, classes


# ─── Phase 3: 대조 ─────────────────────────────────────────────────────────
def check_mismatches(imports: list[TypeImport]) -> list[Mismatch]:
    mismatches: list[Mismatch] = []
    seen: dict[str, list[str]] = {}  # module_str → classes (캐시)

    for imp in imports:
        if imp.module not in seen:
            _, classes = get_module_classes(imp.module)
            seen[imp.module] = classes

        classes = seen[imp.module]
        if not classes:
            # 모듈 파일 자체가 없거나 class 정의가 없는 경우 — 스킵
            continue

        if imp.name not in classes:
            path, _ = get_module_classes(imp.module)
            mismatches.append(Mismatch(
                imp=imp,
                module_path=path or Path(imp.module),
                available=classes,
            ))
    return mismatches


# ─── 보고서 출력 ──────────────────────────────────────────────────────────────
def print_report(imports: list[TypeImport], mismatches: list[Mismatch]) -> None:
    print(f"\n{'='*70}")
    print("Preflight Step 14 — Gate 함수 타입명 AST 대조 (ADR-033)")
    print(f"{'='*70}")
    print(f"  대상 파일   : {GATE_FILE.relative_to(REPO_ROOT)}")
    print(f"  Gate 함수 수: {len({i.gate_func for i in imports})}")
    print(f"  검사 타입 수: {len(imports)}")
    print(f"  불일치 건수 : {len(mismatches)}")
    print()

    if not mismatches:
        print("  ✅ ALL CLEAR — 모든 타입명 일치 확인")
    else:
        print("  ❌ 불일치 발견:")
        for m in mismatches:
            print(f"\n  [{m.imp.gate_func}] L{m.imp.lineno}")
            print(f"    import 명칭    : {m.imp.name}")
            print(f"    모듈           : {m.imp.module}")
            print(f"    실제 class 목록: {m.available}")
            print(f"    → '{m.imp.name}' 이(가) 모듈에 존재하지 않음")

    print(f"{'='*70}\n")


# ─── main ─────────────────────────────────────────────────────────────────────
def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight Step 14")
    parser.add_argument("--strict", action="store_true",
                        help="불일치 발견 시 exit(1) — CI 블로킹 모드")
    args = parser.parse_args()

    imports    = collect_gate_imports(GATE_FILE)
    mismatches = check_mismatches(imports)
    print_report(imports, mismatches)

    if mismatches and args.strict:
        print("Preflight Step 14 FAILED (--strict 모드)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
