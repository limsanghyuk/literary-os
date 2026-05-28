#!/usr/bin/env python3
"""
Literary OS Preflight Automated Runner v1.0
==========================================
DEV_PROTOCOL_v2.0 §1 Preflight 12단계를 자동 실행하고
docs/sessions/preflight_v{VERSION}.md 로그를 생성한다.

사용법:
    python3 tools/run_preflight.py                  # 현재 버전 기준
    python3 tools/run_preflight.py --version 11.38  # 특정 버전 지정
    python3 tools/run_preflight.py --strict         # 실패 시 exit(1)

출력:
    docs/sessions/preflight_v{VERSION}_{DATE}.md  (로그 파일)
    exit(0) = PASS / exit(1) = FAIL (--strict 모드)

주의:
    이 스크립트 실행 없이는 run_release_gate.py G_PREFLIGHT 검사를 통과할 수 없다.
"""

from __future__ import annotations
import ast
import json
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYS_ROOT  = REPO_ROOT / "literary_system"
TESTS_ROOT = REPO_ROOT / "tests"
GATE_FILE = SYS_ROOT / "gates" / "release_gate.py"
PYPROJECT  = REPO_ROOT / "pyproject.toml"
LOG_DIR    = REPO_ROOT / "docs" / "sessions"

SKIP = {"__pycache__", ".git", ".pytest_cache", "node_modules", "literary_os.egg-info"}

# ─── 버전 읽기 ────────────────────────────────────────────────────────────────
def _get_version() -> str:
    for line in PYPROJECT.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version") and "=" in line:
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return "unknown"

# ─── AST 심볼 수집 ────────────────────────────────────────────────────────────
def _collect_symbols() -> dict[str, str]:
    symbols: dict[str, str] = {}
    for f in REPO_ROOT.rglob("*.py"):
        if any(s in f.parts for s in SKIP):
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                symbols[node.name] = str(f.relative_to(REPO_ROOT))
            elif isinstance(node, ast.FunctionDef) and node.name.startswith("test_"):
                symbols[node.name] = str(f.relative_to(REPO_ROOT))
    return symbols

# ─── 의존성 그래프 ────────────────────────────────────────────────────────────
def _build_dep_graph() -> dict[str, set[str]]:
    deps: dict[str, set[str]] = defaultdict(set)
    for f in SYS_ROOT.rglob("*.py"):
        if any(s in f.parts for s in SKIP):
            continue
        mod = str(f.relative_to(REPO_ROOT)).replace(os.sep, ".")[:-3]
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                deps[mod].add(node.module)
    return deps

# ─── 순환 의존 탐지 ──────────────────────────────────────────────────────────
def _find_cycles(deps: dict[str, set[str]]) -> list[list[str]]:
    cycles: list[list[str]] = []
    visited: set[str] = set()

    def dfs(node: str, path: list[str], path_set: set[str]) -> None:
        if node in path_set:
            idx = path.index(node)
            cycles.append(path[idx:] + [node])
            return
        if node in visited:
            return
        visited.add(node)
        path.append(node)
        path_set.add(node)
        for nb in deps.get(node, []):
            if "literary_system" in nb:
                dfs(nb, path, path_set)
        path.pop()
        path_set.discard(node)

    for node in list(deps.keys()):
        dfs(node, [], set())
    return cycles[:10]

# ─── Survival Matrix ─────────────────────────────────────────────────────────
# SURVIVAL_SYMBOLS — 기준: V710 / SP-D.2 완료 (2026-05-28)
# 새 Sub-Phase 완료 시 이 dict와 DEV_PROTOCOL_v3.0 §1 Step 8을 동시에 갱신한다.
SURVIVAL_SYMBOLS: dict[str, str] = {
    # Phase A/B 핵심
    "UnifiedLLMGateway":          "literary_system/llm_bridge/",
    "TaskRouter":                  "literary_system/llm_bridge/",
    "NKGCurator":                  "literary_system/nkg/",
    "LLMAdapterContractGate":      "literary_system/gates/",
    "LOSDBClient":                  "literary_system/db/",
    # SP-C.1 자기학습
    "LOSConstitutionV2":            "literary_system/constitution/",
    "ConstitutionWeightTracker":    "literary_system/constitution/",
    "RetrainingScheduler":          "literary_system/constitution/",
    "AutoPromotionGate":            "literary_system/gates/",
    # SP-C.2 멀티에이전트 v1
    "DirectorAgent":                "literary_system/agents/",
    "AgentCoordinator":             "literary_system/ensemble/",
    # SP-C.3 PublicSDK
    "LiteraryOSClient":             "literary_system/sdk/",
    "ReaderFeedbackCollector":      "literary_system/feedback/",
    "FeedbackToRLHFAdapter":        "literary_system/feedback/",
    # SP-D.1 Observability (V681~V695)
    "OtelSdkAdapter":               "literary_system/ops/",
    "TraceContext":                  "literary_system/ops/",
    "TraceSampler":                  "literary_system/ops/",
    "ObservabilityDashboard":        "literary_system/ops/",
    "PrometheusTraceExtension":      "literary_system/ops/",
    # SP-D.2 MultiAgent Coordination (V696~V710)
    "AgentBus":                     "literary_system/agents/",
    "AgentTask":                    "literary_system/agents/",
    "AgentCapabilityRegistry":      "literary_system/agents/",
    "AgentTaskScheduler":           "literary_system/agents/",
    "AgentCollaborationProtocol":   "literary_system/agents/",
    "AgentConflictResolver":        "literary_system/agents/",
    "AgentWorkflow":                "literary_system/agents/",
    "AgentLoadBalancer":            "literary_system/agents/",
    "AgentCircuitBreaker":          "literary_system/agents/",
    "AgentSupervisor":              "literary_system/agents/",
}

def _check_survival() -> dict[str, bool]:
    results: dict[str, bool] = {}
    for sym, path in SURVIVAL_SYMBOLS.items():
        full = REPO_ROOT / path
        found = False
        if full.exists():
            for py in full.rglob("*.py"):
                if any(s in py.parts for s in SKIP):
                    continue
                try:
                    if f"class {sym}" in py.read_text(encoding="utf-8", errors="ignore"):
                        found = True
                        break
                except Exception:
                    pass
        results[sym] = found
    return results

# ─── Orphan 탐지 ─────────────────────────────────────────────────────────────
def _find_orphans() -> list[str]:
    all_imports: set[str] = set()
    all_modules: set[str] = set()
    for f in SYS_ROOT.rglob("*.py"):
        if any(s in f.parts for s in SKIP):
            continue
        mod = str(f.relative_to(REPO_ROOT)).replace(os.sep, ".")[:-3]
        all_modules.add(mod)
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
        except Exception:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                all_imports.add(node.module)
    return [m for m in all_modules if m not in all_imports and "__init__" not in m][:20]

# ─── 메인 실행 ───────────────────────────────────────────────────────────────
def run_preflight(version: str | None = None, strict: bool = False) -> bool:
    ver = version or _get_version()
    date_str = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    dt_str   = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    log_path = LOG_DIR / f"preflight_v{ver}_{date_str}.md"
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    lines: list[str] = []
    issues: list[str] = []
    warnings: list[str] = []

    def log(s: str = "") -> None:
        lines.append(s)
        print(s)

    log(f"# Preflight 12단계 실행 로그")
    log(f"**버전**: v{ver}  |  **실행일시**: {dt_str}  |  **실행자**: run_preflight.py v1.0")
    log(f"**근거**: DEV_PROTOCOL_v3.0 §1 (PREFLIGHT_GUIDE_v1.1 흡수 통합본)")
    log()

    # ── Step 1: 코드베이스 현황 ──────────────────────────────────────────────
    log("## Step 1. 코드베이스 현황 (index_status 등가)")
    t0 = time.time()
    py_files = [f for f in REPO_ROOT.rglob("*.py") if not any(s in f.parts for s in SKIP)]
    symbols = _collect_symbols()
    classes = {k: v for k, v in symbols.items() if not k.startswith("test_")}
    tests   = {k: v for k, v in symbols.items() if k.startswith("test_")}
    r = subprocess.run(["git", "-C", str(REPO_ROOT), "diff", "--name-only", "HEAD~3"],
                       capture_output=True, text=True)
    recent_changes = [l for l in r.stdout.splitlines() if l.endswith(".py")]
    log(f"- Python 파일: {len(py_files):,}개")
    log(f"- 심볼(클래스): {len(classes):,}개")
    log(f"- 테스트 함수: {len(tests):,}개")
    log(f"- 최근 변경 py 파일 (HEAD~3): {len(recent_changes)}개")
    for f in recent_changes[:10]:
        log(f"  - {f}")
    log(f"- 소요: {time.time()-t0:.2f}s")
    log()

    # ── Step 2: 모듈 범위 확인 ───────────────────────────────────────────────
    log("## Step 2. 모듈 범위 (list_repos 등가)")
    top_dirs = sorted({str(f.relative_to(REPO_ROOT)).split(os.sep)[1]
                       for f in SYS_ROOT.rglob("*.py")
                       if not any(s in f.parts for s in SKIP)})
    log(f"- literary_system/ 서브패키지: {len(top_dirs)}개")
    for d in top_dirs:
        count = len(list((SYS_ROOT / d).rglob("*.py")))
        log(f"  - {d}/ ({count}파일)")
    test_files = list(TESTS_ROOT.rglob("test_*.py"))
    log(f"- 테스트 파일: {len(test_files)}개")
    log()

    # ── Step 3: 변경 예정 심볼 탐색 ─────────────────────────────────────────
    log("## Step 3. 변경 예정 심볼 탐색 (query 등가)")
    log("- 현재 Phase D SP-D.3+ 진입 예정: 신규 모듈 존재 여부 스캔")
    candidate_dirs = [SYS_ROOT / d for d in ["agents", "ops", "gates", "serving", "sdk"]]
    for cdir in candidate_dirs:
        if cdir.exists():
            py_count = len(list(cdir.rglob("*.py")))
            log(f"  - {cdir.name}/: {py_count}개 파일")
    log()

    # ── Step 4: 핵심 심볼 맥락 확인 (360도) ─────────────────────────────────
    log("## Step 4. 핵심 심볼 360도 맥락 (context 등가)")
    key_symbols = ["LiteraryOSClient", "AgentCoordinator", "LOSConstitutionV2", "B2BPartnerGate"]
    for sym in key_symbols:
        incoming = [str(f.relative_to(REPO_ROOT)) for f in REPO_ROOT.rglob("*.py")
                    if not any(s in f.parts for s in SKIP)
                    and sym in f.read_text(encoding="utf-8", errors="ignore")
                    and f"class {sym}" not in f.read_text(encoding="utf-8", errors="ignore")]
        log(f"  - {sym}: {len(incoming)}개 참조")
        for ref in incoming[:3]:
            log(f"      → {ref}")
    log()

    # ── Step 5: 영향 범위 계산 ───────────────────────────────────────────────
    log("## Step 5. 영향 범위 (impact depth 1/2/3 등가)")
    deps = _build_dep_graph()
    sp_c3_modules = ["literary_system.sdk", "literary_system.feedback",
                     "literary_system.serving", "literary_system.gates"]
    for mod in sp_c3_modules:
        depth1 = [k for k, v in deps.items() if any(mod in dep for dep in v)]
        log(f"  - {mod}: depth-1 참조자 {len(depth1)}개")
    log()

    # ── Step 6: 테스트 영향 분석 ─────────────────────────────────────────────
    log("## Step 6. 테스트 영향 분석 (detect_changes 등가)")
    sp_c3_test_files = [f for f in TESTS_ROOT.rglob("test_v6[5-9]*.py")]
    log(f"- SP-C.3 테스트 파일: {len(sp_c3_test_files)}개")
    for f in sorted(sp_c3_test_files):
        log(f"  - {f.name}")
    # 테스트 실행 (빠른 연기 확인)
    r2 = subprocess.run(
        ["python3", "-m", "pytest", "--collect-only", "-q",
         str(TESTS_ROOT / "unit"), "--tb=no"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    collect_lines = [l for l in r2.stdout.splitlines() if "test session starts" not in l]
    test_count = next((l for l in collect_lines if "selected" in l or "test" in l.lower()), "")
    log(f"- pytest --collect-only: {test_count.strip()}")
    log()

    # ── Step 7: 핵심 개념 무결성 ─────────────────────────────────────────────
    log("## Step 7. 핵심 개념 무결성 (concept_impact 등가)")

    # LLM-0: corpus/constitution/finetune 내 외부 LLM 호출 확인
    llm0_violations: list[str] = []
    for target_dir in ["corpus", "constitution", "finetune"]:
        tdir = SYS_ROOT / target_dir
        if not tdir.exists():
            continue
        for py in tdir.rglob("*.py"):
            content = py.read_text(encoding="utf-8", errors="ignore")
            if "openai.ChatCompletion" in content or "anthropic.messages.create" in content:
                llm0_violations.append(str(py.relative_to(REPO_ROOT)))
    log(f"  - LLM-0 위반: {len(llm0_violations)}건 {'→ ' + str(llm0_violations) if llm0_violations else '✓ 없음'}")

    # G32: print() / bare except in literary_system/
    g32_violations: list[str] = []
    for py in SYS_ROOT.rglob("*.py"):
        if any(s in py.parts for s in SKIP):
            continue
        content = py.read_text(encoding="utf-8", errors="ignore")
        lines_data = content.splitlines()
        for i, line in enumerate(lines_data, 1):
            stripped = line.strip()
            if (stripped.startswith("print(") and
                    not stripped.startswith("#") and
                    not stripped.startswith('"""') and
                    "_cli_demo" not in "".join(lines_data[max(0,i-20):i])):
                g32_violations.append(f"{py.relative_to(REPO_ROOT)}:{i}")
            if stripped == "except:":
                g32_violations.append(f"{py.relative_to(REPO_ROOT)}:{i} (bare except)")
    if g32_violations:
        issues.extend([f"G32 위반: {v}" for v in g32_violations[:5]])
        log(f"  - G32 위반: {len(g32_violations)}건")
        for v in g32_violations[:5]:
            log(f"    ❌ {v}")
    else:
        log(f"  - G32 위반: ✓ 없음")

    # DEV_MODE 확인
    # literary_system/ 내에서만 DEV_MODE=True 검사 (tools/ 스크립트 자체 제외)
    devmode = [str(f.relative_to(REPO_ROOT)) for f in SYS_ROOT.rglob("*.py")
               if not any(s in f.parts for s in SKIP)
               and "DEV_MODE = True" in f.read_text(encoding="utf-8", errors="ignore")]
    log(f"  - DEV_MODE=True 파일: {len(devmode)}건 {'→ ' + str(devmode) if devmode else '✓ 없음'}")
    if devmode:
        issues.extend([f"DEV_MODE=True: {v}" for v in devmode])

    # 버전 일관성
    ver_in_pyproject = ver
    gate_content = GATE_FILE.read_text(encoding="utf-8") if GATE_FILE.exists() else ""
    log(f"  - pyproject.toml 버전: {ver_in_pyproject}")
    log()

    # ── Step 8: Survival Matrix ───────────────────────────────────────────────
    log("## Step 8. Survival Matrix (핵심 심볼 생존 확인)")
    survival = _check_survival()
    dead = [sym for sym, alive in survival.items() if not alive]
    alive_count = sum(1 for v in survival.values() if v)
    log(f"  - 검사 심볼: {len(survival)}개  |  생존: {alive_count}개  |  사망: {len(dead)}개")
    for sym, alive in survival.items():
        status = "✅ ALIVE" if alive else "❌ DEAD"
        log(f"  {status}  {sym}")
    if dead:
        issues.extend([f"DEAD 심볼: {s}" for s in dead])
    log()

    # ── Step 9: 신규 로직 Gate 연결 ──────────────────────────────────────────
    log("## Step 9. Gate 연결성 (symbol_to_branchpoint_trace 등가)")
    # SP-D.2 완료 기준 핵심 Gate 연결 확인
    key_gates = ["AgentCoordinationGate", "MultiAgentPolicyGate",
                 "ObservabilityFoundationGate", "PreFlightFixGate",
                 "StaticTypeSafetyGate"]
    gate_content_str = gate_content
    for sym in key_gates:
        in_gate = sym in gate_content_str
        log(f"  {'✅' if in_gate else '⚠️ '} {sym}: {'release_gate.py 연결됨' if in_gate else 'release_gate.py 미연결 (독립 게이트)'}")
        if not in_gate:
            warnings.append(f"Gate 미연결(독립 운영): {sym}")
    log()

    # ── Step 10: Schema 검증 ─────────────────────────────────────────────────
    log("## Step 10. Schema 검증 (shape_check 등가)")
    r3 = subprocess.run(
        ["python3", "-m", "compileall", str(SYS_ROOT), "-q"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    compile_ok = r3.returncode == 0
    log(f"  - compileall literary_system/: {'✅ OK' if compile_ok else '❌ FAIL'}")
    if not compile_ok:
        issues.append(f"컴파일 오류: {r3.stderr[:200]}")

    r4 = subprocess.run(
        ["python3", "-c", "from literary_system.gates.release_gate import run_release_gate; print('OK')"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )
    import_ok = "OK" in r4.stdout
    log(f"  - release_gate import: {'✅ OK' if import_ok else '❌ FAIL — ' + r4.stderr[:100]}")
    if not import_ok:
        issues.append(f"release_gate import 오류")
    log()

    # ── Step 11: 위험 분류 ───────────────────────────────────────────────────
    log("## Step 11. 위험 변경 분류 (change_review 등가)")
    log("  - 신규 Gate 추가 또는 release_gate.py 수정: 🔴 High → Step 1~13 전부 재실행")
    log("  - 기존 모듈에 메서드/클래스 추가: 🟡 Medium → Step 7~13")
    log("  - 독립 신규 모듈, 테스트, 문서 수정: 🟢 Low → Step 10, 11, 13")
    log()

    # ── Step 12: Release Gate 최종 ───────────────────────────────────────────
    log("## Step 12. Release Gate 최종 판단 (release_gate_integration 등가)")
    # release_gate.py 직접 호출 (run_release_gate.py는 G_PREFLIGHT 순환 참조 방지)
    r5 = subprocess.run(
        ["python3", "-c",
         "import sys, json; sys.path.insert(0, '.'); "
         "from literary_system.gates.release_gate import run_release_gate; "
         "r=run_release_gate(); print(r['summary'])"],
        capture_output=True, text=True, cwd=REPO_ROOT, timeout=180
    )
    gate_ok = "RELEASE GATE PASS" in r5.stdout
    summary_line = r5.stdout.strip().splitlines()[-1] if r5.stdout.strip() else "실행 실패"
    log(f"  - {summary_line}")
    if not gate_ok:
        issues.append("Release Gate FAIL (상세: tools/run_release_gate.py 직접 실행 확인)")
    log()


    # ── Step 13: Connectivity Check (ADR-128) ───────────────────────────────
    log("## Step 13. 패키지 연결성 검사 (ADR-128 G_CONNECTIVITY)")
    import ast as _ast, re as _re
    from collections import defaultdict as _dd

    _ls_root = SYS_ROOT
    _pkgs = set(d.name for d in _ls_root.iterdir()
                if d.is_dir() and not d.name.startswith("_"))
    _deps: dict = _dd(set)
    _imported_by: dict = _dd(set)

    for _pkg in _pkgs:
        for _pyf in (_ls_root / _pkg).rglob("*.py"):
            try:
                _src = _pyf.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for _m in _re.finditer(r"from literary_system\.(\w+)", _src):
                _t = _m.group(1)
                if _t in _pkgs and _t != _pkg:
                    _deps[_pkg].add(_t)
                    _imported_by[_t].add(_pkg)

    _isolated = sorted(p for p in _pkgs
                       if not _imported_by.get(p) and not _deps.get(p))

    # 이전 Preflight 로그에서 고립 패키지 이력 추적 (2버전 연속 = FAIL)
    _sessions_dir = REPO_ROOT / "docs" / "sessions"
    _prev_isolated: set = set()
    if _sessions_dir.exists():
        _prev_logs = sorted(_sessions_dir.glob("preflight_*.md"), reverse=True)
        for _plog in _prev_logs[1:3]:  # 바로 전 1~2개 로그
            try:
                _ptxt = _plog.read_text(encoding="utf-8", errors="ignore")
                for _line in _ptxt.splitlines():
                    if "고립 패키지:" in _line and "❌" in _line:
                        _pname = _line.strip().split()[-1]
                        _prev_isolated.add(_pname)
            except Exception:
                pass

    _escalated = sorted(set(_isolated) & _prev_isolated)

    if _isolated:
        for _ip in _isolated:
            log(f"  ⚠️  WARN: {_ip} — 완전 고립 (←0, →0). 2버전 내 연결 필요 (ADR-128)")
            warnings.append(f"고립 패키지: {_ip}")
        if _escalated:
            for _ep in _escalated:
                log(f"  ❌ FAIL: {_ep} — 2버전 연속 고립. 즉시 연결 필요 (ADR-128)")
                issues.append(f"ADR-128 위반: {_ep} 패키지 2버전 연속 고립")
        log(f"  총 {len(_isolated)}개 고립, {len(_escalated)}개 에스컬레이션")
    else:
        log(f"  ✅ G_CONNECTIVITY PASS — 완전 고립 패키지 0개 ({len(_pkgs)}개 전체 연결됨)")
    log()

    # ── 순환 의존 ────────────────────────────────────────────────────────────
    log("## 부록. 순환 의존 탐지")
    cycles = _find_cycles(deps)
    log(f"  - 실질 순환: {len(cycles)}개")
    for c in cycles[:3]:
        log(f"  ⚠️  {' → '.join(p.split('.')[-1] for p in c)}")
    if cycles:
        warnings.extend([f"순환 의존: {c}" for c in cycles[:3]])
    log()

    # ── 최종 판정 ────────────────────────────────────────────────────────────
    log("---")
    log("## 최종 판정")
    if issues:
        log(f"### ❌ PREFLIGHT FAIL — {len(issues)}건 해소 필요")
        for i, iss in enumerate(issues, 1):
            log(f"  {i}. {iss}")
        passed = False
    else:
        log(f"### ✅ PREFLIGHT PASS — 개발 진행 허가")
        passed = True

    if warnings:
        log(f"\n**경고 (블록 아님)**: {len(warnings)}건")
        for w in warnings:
            log(f"  - {w}")

    log()
    log(f"**실행 완료**: {datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')}")
    log(f"**로그 파일**: {log_path.relative_to(REPO_ROOT)}")

    # 로그 파일 저장
    log_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"\n[Preflight] 로그 저장: {log_path}")

    if strict and not passed:
        sys.exit(1)

    return passed


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Literary OS Preflight Runner v1.0")
    parser.add_argument("--version", help="버전 지정 (기본: pyproject.toml 자동 읽기)")
    parser.add_argument("--strict", action="store_true", help="FAIL 시 exit(1)")
    args = parser.parse_args()
    run_preflight(version=args.version, strict=args.strict)
