#!/usr/bin/env python3
"""
Preflight Step 13: CI 의존성 정합성 검사
tests/ 전체 import 수집 → dev extras 대조 → 불일치 리포트

사용법:
    python tools/preflight_step13.py          # 프로젝트 루트에서 실행
    python tools/preflight_step13.py --strict # 불일치 시 exit 1 (CI 모드)

Literary OS V572 | ADR-032
"""
from __future__ import annotations

import ast
import sys
import os
import argparse
from pathlib import Path
from importlib import metadata as importlib_metadata

# ─── 설정 ─────────────────────────────────────────────────────────────────────

# 자체 패키지 / 테스트 내부 참조 화이트리스트 (설치 불필요)
WHITELIST: set[str] = {
    "literary_system",
    "apps",
    "tests",
    "conftest",
    "_pytest",
    "pytest",
    # pytest 플러그인들은 pytest 설치 시 함께 포함
    "pytest_asyncio",
    "_pytest",
}

# 모듈명 → 패키지명 직접 매핑 (importlib.metadata가 못 잡는 케이스 보완)
KNOWN_ALIASES: dict[str, str] = {
    "sklearn": "scikit-learn",
    "cv2": "opencv-python",
    "PIL": "Pillow",
    "yaml": "PyYAML",
    "bs4": "beautifulsoup4",
    "dotenv": "python-dotenv",
    "googleapiclient": "google-api-python-client",
    "google.auth": "google-auth",
    "aiohttp": "aiohttp",
    "uvicorn": "uvicorn",
    "httpx": "httpx",
    "fastapi": "fastapi",
    "anthropic": "anthropic",
    "langchain": "langchain",
    "numpy": "numpy",
    "scipy": "scipy",
    "pandas": "pandas",
    "matplotlib": "matplotlib",
    "opentelemetry": "opentelemetry-sdk",
}


# ─── Phase 1: Import 수집 ──────────────────────────────────────────────────────

def collect_imports(tests_dir: Path) -> set[str]:
    """tests/ 하위 모든 .py 파일에서 최상위 패키지명 수집"""
    imports: set[str] = set()
    for py_file in tests_dir.rglob("*.py"):
        try:
            source = py_file.read_text(encoding="utf-8", errors="ignore")
            tree = ast.parse(source, filename=str(py_file))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    top = alias.name.split(".")[0]
                    imports.add(top)
            elif isinstance(node, ast.ImportFrom):
                if node.module and node.level == 0:  # 절대 임포트만
                    top = node.module.split(".")[0]
                    imports.add(top)
    return imports


# ─── Phase 2: 설치된 패키지 목록 획득 ─────────────────────────────────────────

def get_installed_modules() -> set[str]:
    """현재 환경에서 import 가능한 최상위 모듈명 집합"""
    try:
        pkgs = importlib_metadata.packages_distributions()
        return set(pkgs.keys())
    except Exception:
        return set()


# ─── Phase 3: 표준 라이브러리 모듈 목록 ───────────────────────────────────────

def get_stdlib_modules() -> set[str]:
    """Python 표준 라이브러리 모듈 이름 집합"""
    if hasattr(sys, "stdlib_module_names"):  # Python 3.10+
        return sys.stdlib_module_names  # type: ignore[return-value]
    # fallback: sys.builtin_module_names + 직접 열거
    import sysconfig
    stdlib_path = sysconfig.get_paths()["stdlib"]
    stdlib: set[str] = set(sys.builtin_module_names)
    if os.path.isdir(stdlib_path):
        for name in os.listdir(stdlib_path):
            stem = name.split(".")[0]
            if stem and not stem.startswith("_"):
                stdlib.add(stem)
    return stdlib


# ─── Phase 4: 대조 ────────────────────────────────────────────────────────────

def check_missing(
    imports: set[str],
    installed: set[str],
    stdlib: set[str],
) -> list[str]:
    """설치되지 않은 외부 패키지 목록 반환"""
    missing = []
    for mod in sorted(imports):
        if mod in WHITELIST:
            continue
        if mod in stdlib:
            continue
        if mod.startswith("_"):
            continue
        # 직접 임포트 이름으로 설치 확인
        if mod in installed:
            continue
        # 별칭 매핑 확인
        canonical = KNOWN_ALIASES.get(mod)
        if canonical:
            # 패키지명으로 재확인
            try:
                importlib_metadata.version(canonical)
                continue  # 설치됨
            except importlib_metadata.PackageNotFoundError:
                missing.append(f"{mod}  (패키지명: {canonical})")
                continue
        # 임포트 자체를 시도해서 확인
        try:
            __import__(mod)
            continue
        except ImportError:
            missing.append(mod)
        except Exception:
            continue  # import error가 아닌 경우 무시
    return missing


# ─── Main ─────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight Step 13 — CI 의존성 정합성 검사")
    parser.add_argument("--strict", action="store_true", help="불일치 시 exit 1 (CI 모드)")
    parser.add_argument("--root", default=".", help="프로젝트 루트 경로 (기본값: .)")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    tests_dir = root / "tests"

    if not tests_dir.exists():
        print(f"[STEP13] ERROR: tests/ 디렉토리를 찾을 수 없음: {tests_dir}")
        return 1

    print("[STEP13] Literary OS Preflight Step 13 시작")
    print(f"[STEP13] 검사 대상: {tests_dir}")

    # Phase 1
    imports = collect_imports(tests_dir)
    print(f"[STEP13] Phase 1 완료 — 수집된 최상위 모듈: {len(imports)}개")

    # Phase 2
    installed = get_installed_modules()
    print(f"[STEP13] Phase 2 완료 — 설치된 모듈: {len(installed)}개")

    # Phase 3
    stdlib = get_stdlib_modules()

    # Phase 4
    missing = check_missing(imports, installed, stdlib)

    if missing:
        print(f"\n[STEP13] ⚠️  미설치 외부 패키지 {len(missing)}건 발견:")
        for m in missing:
            print(f"  - {m}")
        print("\n[STEP13] 권고: pyproject.toml [project.optional-dependencies] dev 에 추가 후 재실행")
        if args.strict:
            print("[STEP13] FAIL (--strict 모드)")
            return 1
        else:
            print("[STEP13] WARNING (--strict 없이 실행 — CI에서는 반드시 --strict 사용)")
            return 0
    else:
        print("[STEP13] ✅  모든 import 의존성 정합성 확인 완료 — 불일치 0건")
        return 0


if __name__ == "__main__":
    sys.exit(main())
