"""
Literary OS — run_release_gate.py (v11.39.0, ADR-128)

G_PREFLIGHT: Preflight 로그 없으면 전체 실행 블록
G_CONNECTIVITY: 완전 고립 패키지 2버전 연속 존재 시 FAIL
"""
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYS_ROOT  = REPO_ROOT / "literary_system"
SESSIONS_DIR = REPO_ROOT / "docs" / "sessions"

sys.path.insert(0, str(REPO_ROOT))


# ── G_PREFLIGHT 검사 ─────────────────────────────────────────────────────────

def _check_preflight_log() -> dict:
    """docs/sessions/에서 최근 14일 이내 Preflight 로그 확인."""
    if not SESSIONS_DIR.exists():
        return {"pass": False, "reason": "docs/sessions/ 디렉토리 없음"}
    cutoff = datetime.now(timezone.utc) - timedelta(days=14)
    logs = sorted(SESSIONS_DIR.glob("preflight_*.md"), reverse=True)
    for log in logs:
        try:
            mtime = datetime.fromtimestamp(log.stat().st_mtime, tz=timezone.utc)
            size  = log.stat().st_size
            if mtime >= cutoff and size >= 1000:
                content = log.read_text(encoding="utf-8", errors="ignore")
                step_count = len(re.findall(r"^## Step \d+", content, re.MULTILINE))
                if step_count >= 10:
                    return {"pass": True, "log": str(log.name),
                            "steps": step_count, "size": size}
        except Exception:
            continue
    return {
        "pass": False,
        "reason": "최근 14일 내 유효한 Preflight 로그 없음",
        "hint": "python tools/run_preflight.py 실행 후 재시도",
    }


# ── G_CONNECTIVITY 검사 ──────────────────────────────────────────────────────

def _check_connectivity() -> dict:
    """literary_system/ 패키지 완전 고립 탐지 (ADR-128)."""
    packages = set(d.name for d in SYS_ROOT.iterdir()
                   if d.is_dir() and not d.name.startswith("_"))
    imported_by: dict = defaultdict(set)
    deps: dict = defaultdict(set)
    for pkg in packages:
        for pyf in (SYS_ROOT / pkg).rglob("*.py"):
            try:
                src = pyf.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for m in re.finditer(r"from literary_system\.(\w+)", src):
                t = m.group(1)
                if t in packages and t != pkg:
                    deps[pkg].add(t)
                    imported_by[t].add(pkg)

    isolated = sorted(p for p in packages if not imported_by.get(p) and not deps.get(p))

    # 이전 Preflight 로그에서 고립 이력 추적
    prev_isolated: set = set()
    if SESSIONS_DIR.exists():
        prev_logs = sorted(SESSIONS_DIR.glob("preflight_*.md"), reverse=True)
        for plog in prev_logs[1:3]:
            try:
                for line in plog.read_text(encoding="utf-8", errors="ignore").splitlines():
                    if "고립 패키지:" in line and ("❌" in line or "WARN" in line):
                        parts = line.strip().split()
                        if parts:
                            prev_isolated.add(parts[-1])
            except Exception:
                pass

    escalated = sorted(set(isolated) & prev_isolated)
    passed = len(escalated) == 0
    return {
        "pass": passed,
        "total_packages": len(packages),
        "isolated": isolated,
        "isolated_count": len(isolated),
        "escalated": escalated,
        "reason": (f"ADR-128 위반: {escalated} 2버전 연속 고립" if escalated
                   else ("경고: 1버전 고립 중" if isolated else "OK")),
    }


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main() -> None:
    print("=" * 60)
    print("Literary OS Release Gate (v11.39.0)")
    print("=" * 60)

    # ── G_PREFLIGHT 블로킹 사전 검사 ────────────────────────────────────────
    pf = _check_preflight_log()
    if not pf["pass"]:
        print("\n╔══════════════════════════════════════════════════════════╗")
        print("║       RELEASE GATE BLOCKED — G_PREFLIGHT FAIL           ║")
        print("╠══════════════════════════════════════════════════════════╣")
        print(f"║  이유: {pf.get('reason','알 수 없음')[:50]:<52}║")
        print(f"║  조치: {pf.get('hint','python tools/run_preflight.py')[:50]:<52}║")
        print("╚══════════════════════════════════════════════════════════╝\n")
        result = {
            "status": "blocked",
            "gate": "G_PREFLIGHT",
            "passed": False,
            "preflight": pf,
            "summary": "RELEASE GATE BLOCKED: Preflight 로그 필요",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)

    print(f"  G_PREFLIGHT PASS: {pf.get('log', 'OK')} ({pf.get('steps', '?')}단계)")

    # ── G_CONNECTIVITY 검사 ──────────────────────────────────────────────────
    conn = _check_connectivity()
    if conn["isolated"]:
        level = "FAIL" if conn["escalated"] else "WARN"
        print(f"  G_CONNECTIVITY {level}: 고립 {conn['isolated_count']}개"
              f" / 에스컬레이션 {len(conn['escalated'])}개")
        for p in conn["isolated"]:
            marker = "❌" if p in conn["escalated"] else "⚠️ "
            print(f"    {marker} {p}")
        if not conn["pass"]:
            result = {
                "status": "fail",
                "gate": "G_CONNECTIVITY",
                "passed": False,
                "connectivity": conn,
                "summary": f"RELEASE GATE FAIL: G_CONNECTIVITY ({conn['reason']})",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            print(json.dumps(result, ensure_ascii=False, indent=2))
            sys.exit(1)
    else:
        print(f"  G_CONNECTIVITY PASS: 전체 {conn['total_packages']}개 연결됨")

    # ── 핵심 Release Gate 실행 ───────────────────────────────────────────────
    try:
        from literary_system.gates.release_gate import run_release_gate
        gate_result = run_release_gate()
    except Exception as exc:
        gate_result = {"status": "error", "error": str(exc), "summary": f"ERROR: {exc}"}

    # ── 최종 결과 조합 ───────────────────────────────────────────────────────
    final = {
        **gate_result,
        "G_PREFLIGHT": {**pf, "pass": True},
        "G_CONNECTIVITY": conn,
        "preflight_verified": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    print(json.dumps(final, ensure_ascii=False, indent=2))
    sys.exit(0 if gate_result.get("status") == "pass" else 1)


if __name__ == "__main__":
    main()
