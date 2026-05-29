#!/usr/bin/env python3
"""
tools/session_start.py — Literary OS 세션 시작 프로토콜 자동 실행기

DEV_PROTOCOL_v2.0 §1 Preflight의 Step 1(코드그래프) + Step 12(릴리즈 게이트)를
자동으로 실행하여 개발 착수 전 기준선을 확보한다.

사용법:
    python3 tools/session_start.py            # 표준 실행 (Step 1 + 12)
    python3 tools/session_start.py --full     # 전체 Step 1~12 체크리스트 출력
    python3 tools/session_start.py --gate     # Step 12만 실행 (빠른 확인)
"""

import sys
import ast
import os
import json
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).resolve().parent.parent
REPO_URL = "https://github.com/limsanghyuk/literary-os"

# ──────────────────────────────────────────────────────────────
# 색상 출력
# ──────────────────────────────────────────────────────────────
def _c(text: str, code: str) -> str:
    return f"\033[{code}m{text}\033[0m"

def ok(msg):   print(_c(f"  ✅ {msg}", "32"))
def warn(msg): print(_c(f"  ⚠️  {msg}", "33"))
def err(msg):  print(_c(f"  ❌ {msg}", "31"))
def hdr(msg):  print(_c(f"\n{'='*60}\n{msg}\n{'='*60}", "1;36"))
def sub(msg):  print(_c(f"  → {msg}", "34"))

# ──────────────────────────────────────────────────────────────
# Step 1: 코드그래프 현황 (AST 분석)
# ──────────────────────────────────────────────────────────────
def step1_code_graph() -> dict:
    hdr("STEP 1 — 코드그래프 현황 (AST)")
    SKIP = {"__pycache__", ".git", ".pytest_cache", "node_modules"}
    symbols: dict[str, str] = {}

    class Visitor(ast.NodeVisitor):
        def __init__(self, mod: str):
            self.mod = mod
            self._cls: list[str] = []

        def visit_ClassDef(self, node):
            key = f"{self.mod}.{node.name}"
            symbols[key] = "class"
            self._cls.append(node.name)
            self.generic_visit(node)
            self._cls.pop()

        def visit_FunctionDef(self, node):
            if self._cls:
                key = f"{self.mod}.{self._cls[-1]}.{node.name}"
                symbols[key] = "method"
            else:
                t = "test_fn" if node.name.startswith("test_") else "function"
                symbols[f"{self.mod}.{node.name}"] = t
            self.generic_visit(node)

        visit_AsyncFunctionDef = visit_FunctionDef

    py_files = 0
    for f in ROOT.rglob("*.py"):
        if any(s in f.parts for s in SKIP):
            continue
        try:
            mod = str(f.relative_to(ROOT)).replace(os.sep, ".").replace("/", ".")[:-3]
            Visitor(mod).visit(ast.parse(f.read_text("utf-8", errors="replace")))
            py_files += 1
        except Exception:
            pass

    classes  = sum(1 for v in symbols.values() if v == "class")
    methods  = sum(1 for v in symbols.values() if v == "method")
    funcs    = sum(1 for v in symbols.values() if v == "function")
    tests    = sum(1 for v in symbols.values() if v == "test_fn")
    mods     = len({k.split(".")[0] for k in symbols})

    print(f"  파이썬 파일: {py_files:,}")
    print(f"  모듈:        {mods:,}")
    print(f"  전체 심볼:   {len(symbols):,}")
    sub(f"클래스 {classes:,} | 메서드 {methods:,} | 함수 {funcs:,} | 테스트함수 {tests:,}")

    if classes < 100:
        warn(f"클래스 수 {classes}개 — 예상보다 적음. 파일 누락 여부 확인 필요")
    else:
        ok(f"코드그래프 정상 ({classes:,}개 클래스)")

    return {"py_files": py_files, "symbols": len(symbols), "classes": classes}


# ──────────────────────────────────────────────────────────────
# Step 7: LLM-0 원칙 위반 검사
# ──────────────────────────────────────────────────────────────
def step7_llm0_check() -> bool:
    hdr("STEP 7 — LLM-0 원칙 위반 검사")
    PROTECTED = ["literary_system/corpus", "literary_system/constitution", "literary_system/finetune"]
    # LLM API 직접 호출만 차단 (GPU/인프라 HTTP API는 허용)
    FORBIDDEN = [
        "openai.Client(", "openai.OpenAI(", "openai.AsyncOpenAI(",
        "anthropic.Anthropic(", "anthropic.AsyncAnthropic(",
        "from openai import", "import openai",
        "from anthropic import", "import anthropic",
        "openai.chat.completions", "anthropic.messages.create",
    ]
    violations = []
    for pkg in PROTECTED:
        pkg_path = ROOT / pkg.replace("/", os.sep)
        if not pkg_path.exists():
            continue
        for py in pkg_path.rglob("*.py"):
            text = py.read_text("utf-8", errors="replace")
            for pat in FORBIDDEN:
                if pat in text:
                    violations.append(f"{py.relative_to(ROOT)}: '{pat}'")

    if violations:
        for v in violations:
            err(f"LLM-0 위반: {v}")
        return False
    else:
        ok("LLM-0 원칙 준수 (corpus/constitution/finetune 외부 호출 없음)")
        return True


# ──────────────────────────────────────────────────────────────
# Step 12: 릴리즈 게이트 실행
# ──────────────────────────────────────────────────────────────
def step12_release_gate() -> dict:
    hdr("STEP 12 — 릴리즈 게이트 실행")
    gate_script = ROOT / "tools" / "run_release_gate.py"
    if not gate_script.exists():
        err("tools/run_release_gate.py 없음")
        return {"passed": 0, "total": 0, "ok": False}

    result = subprocess.run(
        [sys.executable, "-m", "tools.run_release_gate"],
        capture_output=True, text=True, cwd=ROOT
    )
    output = result.stdout

    try:
        data = json.loads(output)
        passed = data.get("gates_passed", 0)
        total  = data.get("gates_checked", data.get("total_gates", 0))
        status = data.get("status", "fail")
        summary = data.get("summary", f"{passed}/{total}")

        if status == "pass":
            ok(f"릴리즈 게이트 {summary}")
        else:
            err(f"릴리즈 게이트 FAIL: {summary}")
            # 실패한 게이트 목록 출력
            issues = data.get("issues", [])
            for issue in issues:
                warn(f"  FAIL: {issue}")

        return {"passed": passed, "total": total, "ok": status == "pass"}
    except json.JSONDecodeError:
        # JSON 파싱 실패 시 summary 라인 직접 검색
        for line in output.splitlines():
            if "RELEASE GATE" in line:
                ok(line.strip()) if "PASS" in line else err(line.strip())
        return {"passed": 0, "total": 0, "ok": "PASS" in output}


# ──────────────────────────────────────────────────────────────
# test_inventory 상태 확인
# ──────────────────────────────────────────────────────────────
def check_test_inventory() -> int:
    inv_path = ROOT / "tools" / "test_inventory.json"
    if not inv_path.exists():
        warn("test_inventory.json 없음 — python3 tools/generate_test_inventory.py 실행 필요")
        return 0
    try:
        data = json.loads(inv_path.read_text("utf-8"))
        count = data.get("test_count", 0)
        ok(f"test_inventory: {count:,} TC 등록됨")
        return count
    except Exception as e:
        warn(f"test_inventory 읽기 실패: {e}")
        return 0


# ──────────────────────────────────────────────────────────────
# Git 상태 확인
# ──────────────────────────────────────────────────────────────
def check_git_status():
    hdr("GIT 상태 확인")
    try:
        branch = subprocess.check_output(["git", "branch", "--show-current"],
                                          cwd=ROOT, text=True).strip()
        head   = subprocess.check_output(["git", "log", "--oneline", "-1"],
                                          cwd=ROOT, text=True).strip()
        ahead  = subprocess.check_output(["git", "status", "-sb"],
                                          cwd=ROOT, text=True).strip().split("\n")[0]
        ok(f"브랜치: {branch}")
        ok(f"HEAD:   {head}")
        sub(f"상태:   {ahead}")

        # 변경된 파일 수
        dirty = subprocess.check_output(["git", "status", "--short"],
                                         cwd=ROOT, text=True).strip()
        if dirty:
            n = len(dirty.splitlines())
            warn(f"미커밋 변경: {n}개 파일")
        else:
            ok("작업 트리 클린")
    except Exception as e:
        warn(f"git 상태 확인 실패: {e}")


# ──────────────────────────────────────────────────────────────
# 최근 세션 파일 확인
# ──────────────────────────────────────────────────────────────
def check_recent_sessions():
    hdr("최근 세션 기록 확인")
    sessions_dir = ROOT / "docs" / "sessions"
    if not sessions_dir.exists():
        warn("docs/sessions/ 없음")
        return
    md_files = sorted(sessions_dir.glob("*.md"), key=lambda f: f.stat().st_mtime, reverse=True)
    if md_files:
        latest = md_files[0]
        ok(f"최근 세션: {latest.name}")
        sub(f"경로: docs/sessions/{latest.name}")
    else:
        warn("세션 기록 없음")


# ──────────────────────────────────────────────────────────────
# 전체 Preflight 체크리스트 출력
# ──────────────────────────────────────────────────────────────
def print_full_checklist():
    hdr("PREFLIGHT 12단계 체크리스트 (DEV_PROTOCOL_v2.0 §1)")
    checklist = [
        ("Step 1",  "코드그래프 현황 — 모듈/심볼 수 확인"),
        ("Step 2",  "브랜치/HEAD 확인"),
        ("Step 3",  "변경 예정 심볼 importer 목록 파악"),
        ("Step 4",  "LLM-0 원칙 1차 점검"),
        ("Step 5",  "depth-1/2/3 영향 계산"),
        ("Step 6",  "CHANGELOG 상태 확인"),
        ("Step 7",  "LLM-0 위반 패턴 grep"),
        ("Step 8",  "생존 매트릭스 — SP-C 핵심 클래스 존재 확인"),
        ("Step 9",  "Gate 연결 계보 확인 (신규 Gate → release_gate)"),
        ("Step 10", "__init__.py 공개 API 스키마 확인"),
        ("Step 11", "위험도 분류 (🔴High/🟡Medium/🟢Low)"),
        ("Step 12", "python3 tools/run_release_gate.py — PASS 확인"),
    ]
    for step, desc in checklist:
        print(f"  [ ] {step}: {desc}")
    print()
    print("  ⚠️  Step 12 FAIL 시 개발 착수 금지")
    print("  📄 전체 상세: docs/workflow/PREFLIGHT_GUIDE_v1.1.md")


# ──────────────────────────────────────────────────────────────
# 메인
# ──────────────────────────────────────────────────────────────
def main():
    parser = argparse.ArgumentParser(description="Literary OS 세션 시작 프로토콜")
    parser.add_argument("--full", action="store_true", help="전체 Preflight 체크리스트 출력")
    parser.add_argument("--gate", action="store_true", help="Step 12 릴리즈 게이트만 실행")
    args = parser.parse_args()

    print(_c(f"""
╔══════════════════════════════════════════════════════════════╗
║       Literary OS — 세션 시작 프로토콜 (DEV_PROTOCOL_v2.0)  ║
║       {datetime.now().strftime('%Y-%m-%d %H:%M')}   Literary OS 개발 세션                    ║
╚══════════════════════════════════════════════════════════════╝
""", "1;35"))

    if args.full:
        print_full_checklist()
        return

    if args.gate:
        gate = step12_release_gate()
        sys.exit(0 if gate["ok"] else 1)

    # 표준 실행: Step 1 + git + 세션 + Step 7 + Step 12
    check_git_status()
    check_recent_sessions()
    graph = step1_code_graph()
    llm0_ok = step7_llm0_check()
    tc_count = check_test_inventory()
    gate = step12_release_gate()

    # 최종 요약
    hdr("세션 시작 요약")
    print(f"  코드그래프:    {graph['classes']:,} 클래스 / {graph['symbols']:,} 심볼")
    print(f"  LLM-0 준수:   {'✅' if llm0_ok else '❌'}")
    print(f"  TC 등록:       {tc_count:,}")
    print(f"  릴리즈 게이트: {gate['passed']}/{gate['total']} {'✅ PASS' if gate['ok'] else '❌ FAIL'}")
    print()

    if not gate["ok"]:
        err("릴리즈 게이트 FAIL — 개발 착수 전 Gate 수정 필수")
        print()
        print("  수정 후 재실행: python3 tools/session_start.py")
        sys.exit(1)
    else:
        ok("세션 시작 기준선 확보 완료 — 개발 착수 가능")
        print()
        print(_c("  📋 Preflight 전체 체크리스트: python3 tools/session_start.py --full", "34"))
        print(_c("  📄 상세 가이드: docs/workflow/DEV_PROTOCOL_v2.0.md", "34"))
        print()


if __name__ == "__main__":
    main()
