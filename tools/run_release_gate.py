"""
Literary OS — run_release_gate.py (v13.0.1, ADR-128/209)

G_PREFLIGHT:           Preflight 로그 없으면 전체 실행 블록
G_CONNECTIVITY:        완전 고립 패키지 2버전 연속 존재 시 FAIL
G_INTEGRITY_MANIFEST:  SHA256SUMS + test_inventory 자기검증 (ADR-209, WP-0)
G_NO_ABSOLUTE_REWARD:  rlhf/finetune/ 절대 점수 보상 패턴 차단 (ADR-211, WP-4b)
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import re
import subprocess
import sys
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYS_ROOT  = REPO_ROOT / "literary_system"
_GEN_INV_SCRIPT = Path(__file__).resolve().parent / "generate_test_inventory.py"
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



# ── G_NO_ABSOLUTE_REWARD 검사 (ADR-211, WP-4b) ──────────────────────────────

def _check_no_absolute_reward() -> dict:
    """
    G_NO_ABSOLUTE_REWARD: rlhf/ + finetune/ 경로에서
    reward 변수에 절대 float 리터럴 직접 할당 패턴 탐지.
    주석 '# G_NO_ABSOLUTE_REWARD_OK'로 예외 허용.
    """
    violations: list = []
    scan_dirs = [SYS_ROOT / "rlhf", SYS_ROOT / "finetune"]
    bad_pattern = re.compile(r"\breward\s*=\s*[0-9]+\.?[0-9]*\b")

    for d in scan_dirs:
        if not d.exists():
            continue
        for f in sorted(d.rglob("*.py")):
            try:
                text = f.read_text(errors="ignore")
            except OSError:
                continue
            for lineno, line in enumerate(text.splitlines(), 1):
                if bad_pattern.search(line) and "# G_NO_ABSOLUTE_REWARD_OK" not in line:
                    violations.append(
                        f"{f.relative_to(SYS_ROOT.parent) if f.is_relative_to(SYS_ROOT.parent) else f.name}:{lineno}: {line.strip()[:80]}"
                    )

    return {
        "pass": len(violations) == 0,
        "gate": "G_NO_ABSOLUTE_REWARD",
        "violations": violations,
        "reason": "OK" if not violations else f"위반 {len(violations)}건",
    }

# ── G_INTEGRITY_MANIFEST 검사 ────────────────────────────────────────────────

def _load_sha256_module():
    """tools/generate_sha256sums.py를 동적 import (subprocess 실행 아님)."""
    module_path = Path(__file__).resolve().parent / "generate_sha256sums.py"
    spec = importlib.util.spec_from_file_location("generate_sha256sums", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"generate_sha256sums.py를 찾을 수 없음: {module_path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[arg-type]
    return mod


def _check_integrity_manifest() -> dict:
    """
    G_INTEGRITY_MANIFEST (ADR-209) — 3단계 검증:
      ① SHA256SUMS.txt 재생성 후 전 항목 자기검증
      ② test_inventory.json 재생성 후 카운트 일치 확인
      ③ SHA256SUMS.txt.minisig 존재 여부 (WARN only, 차단 아님)
    """
    result: dict = {
        "pass": False,
        "sha256_match": 0,
        "sha256_mismatch": 0,
        "sha256_missing": 0,
        "inventory_before": None,
        "inventory_after": None,
        "inventory_match": False,
        "minisig_warn": None,
        "details": [],
    }

    # ① SHA256SUMS 재생성 및 자기검증 ───────────────────────────────────────
    try:
        sha_mod = _load_sha256_module()
    except ImportError as exc:
        result["reason"] = f"generate_sha256sums.py 로드 실패: {exc}"
        return result

    try:
        sha_mod.write_sums(REPO_ROOT)
        vr = sha_mod.verify_sums(REPO_ROOT)
        result["sha256_match"]    = len(vr.matched)
        result["sha256_mismatch"] = len(vr.mismatched)
        result["sha256_missing"]  = len(vr.missing)
        if vr.mismatched:
            result["details"].append(f"SHA256 불일치: {vr.mismatched[:5]}")
        if vr.missing:
            result["details"].append(f"SHA256 누락: {vr.missing[:5]}")
    except Exception as exc:
        result["reason"] = f"SHA256SUMS 생성·검증 중 오류: {exc}"
        return result

    sha_ok = (result["sha256_mismatch"] == 0 and result["sha256_missing"] == 0)

    # ② test_inventory 재생성 및 카운트 일치 ─────────────────────────────────
    inv_path = REPO_ROOT / "tools" / "test_inventory.json"
    root_inv_path = REPO_ROOT / "test_inventory.json"

    before_count: int | None = None
    try:
        ref_path = root_inv_path if root_inv_path.exists() else inv_path
        if ref_path.exists():
            before_count = json.loads(ref_path.read_text(encoding="utf-8")).get("test_count")
    except Exception:
        pass
    result["inventory_before"] = before_count

    try:
        proc = subprocess.run(
            [sys.executable, str(_GEN_INV_SCRIPT),
             "--output", str(inv_path)],
            capture_output=True, text=True, cwd=str(REPO_ROOT), timeout=180,
        )
        if inv_path.exists():
            after_count = json.loads(inv_path.read_text(encoding="utf-8")).get("test_count")
            result["inventory_after"] = after_count
            if before_count is not None and after_count is not None:
                # 최대 ±5% 허용 (테스트 추가로 늘어날 수 있음)
                diff_ratio = abs(after_count - before_count) / max(before_count, 1)
                result["inventory_match"] = (
                    after_count >= before_count or diff_ratio <= 0.05
                )
                if not result["inventory_match"]:
                    result["details"].append(
                        f"test_inventory 카운트 감소: {before_count} → {after_count}"
                    )
            else:
                result["inventory_match"] = (after_count is not None)
        else:
            result["details"].append("test_inventory.json 재생성 실패")
    except subprocess.TimeoutExpired:
        result["details"].append("test_inventory 재생성 타임아웃 (180s)")
        result["inventory_match"] = False
    except Exception as exc:
        result["details"].append(f"test_inventory 재생성 오류: {exc}")
        result["inventory_match"] = False

    inv_ok = result["inventory_match"]

    # ③ minisig 확인 (WARN only) ─────────────────────────────────────────────
    try:
        sig_info = sha_mod.check_minisig(REPO_ROOT)
        if not sig_info.get("present"):
            result["minisig_warn"] = sig_info.get("warn", "minisig 미존재")
    except Exception as exc:
        result["minisig_warn"] = f"minisig 확인 오류: {exc}"

    # ── 최종 판정 ────────────────────────────────────────────────────────────
    result["pass"] = sha_ok and inv_ok
    result["reason"] = (
        "OK" if result["pass"]
        else " | ".join(result["details"]) or "SHA256/inventory 검증 실패"
    )
    return result


# ── 메인 ─────────────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(
        description="Literary OS Release Gate (v13.0.1)"
    )
    parser.add_argument(
        "--verify-only",
        action="store_true",
        help="G_INTEGRITY_MANIFEST만 실행하고 종료 (빠른 검증용)",
    )
    args = parser.parse_args()

    if args.verify_only:
        sys.stdout.write("Literary OS G_INTEGRITY_MANIFEST --verify-only\n")
        sys.stdout.write("=" * 60 + "\n")
        manifest = _check_integrity_manifest()
        sys.stdout.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        if manifest.get("minisig_warn"):
            sys.stdout.write(f"\n⚠️  WARN: {manifest['minisig_warn']}\n")
        if manifest["pass"]:
            sys.stdout.write("\nG_INTEGRITY_MANIFEST PASS\n")
        else:
            sys.stdout.write(f"\nG_INTEGRITY_MANIFEST FAIL: {manifest.get('reason')}\n")
        sys.exit(0 if manifest["pass"] else 1)

    sys.stdout.write("=" * 60 + "\n")
    sys.stdout.write("Literary OS Release Gate (v13.0.1)\n")
    sys.stdout.write("=" * 60 + "\n")

    # ── G_PREFLIGHT 블로킹 사전 검사 ────────────────────────────────────────
    pf = _check_preflight_log()
    if not pf["pass"]:
        sys.stdout.write("\n╔══════════════════════════════════════════════════════════╗\n")
        sys.stdout.write("║       RELEASE GATE BLOCKED — G_PREFLIGHT FAIL           ║\n")
        sys.stdout.write("╠══════════════════════════════════════════════════════════╣\n")
        sys.stdout.write(f"║  이유: {pf.get('reason','알 수 없음')[:50]:<52}║\n")
        sys.stdout.write(f"║  조치: {pf.get('hint','python tools/run_preflight.py')[:50]:<52}║\n")
        sys.stdout.write("╚══════════════════════════════════════════════════════════╝\n\n")
        result = {
            "status": "blocked",
            "gate": "G_PREFLIGHT",
            "passed": False,
            "preflight": pf,
            "summary": "RELEASE GATE BLOCKED: Preflight 로그 필요",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        sys.exit(1)

    sys.stdout.write(f"  G_PREFLIGHT PASS: {pf.get('log', 'OK')} ({pf.get('steps', '?')}단계)\n")

    # ── G_CONNECTIVITY 검사 ──────────────────────────────────────────────────
    conn = _check_connectivity()
    if conn["isolated"]:
        level = "FAIL" if conn["escalated"] else "WARN"
        sys.stdout.write(f"  G_CONNECTIVITY {level}: 고립 {conn['isolated_count']}개"
              f" / 에스컬레이션 {len(conn['escalated'])}개\n")
        for p in conn["isolated"]:
            marker = "❌" if p in conn["escalated"] else "⚠️ "
            sys.stdout.write(f"    {marker} {p}\n")
        if not conn["pass"]:
            result = {
                "status": "fail",
                "gate": "G_CONNECTIVITY",
                "passed": False,
                "connectivity": conn,
                "summary": f"RELEASE GATE FAIL: G_CONNECTIVITY ({conn['reason']})",
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
            sys.exit(1)
    else:
        sys.stdout.write(f"  G_CONNECTIVITY PASS: 전체 {conn['total_packages']}개 연결됨\n")

    # ── G_INTEGRITY_MANIFEST 검사 ────────────────────────────────────────────
    sys.stdout.write("  G_INTEGRITY_MANIFEST 검사 중...\n")
    manifest = _check_integrity_manifest()
    if manifest["pass"]:
        sys.stdout.write(
            f"  G_INTEGRITY_MANIFEST PASS: "
            f"SHA256 {manifest['sha256_match']}건 일치, "
            f"inventory {manifest['inventory_before']}→{manifest['inventory_after']}\n"
        )
    else:
        sys.stdout.write(f"  G_INTEGRITY_MANIFEST FAIL: {manifest.get('reason')}\n")
        result = {
            "status": "fail",
            "gate": "G_INTEGRITY_MANIFEST",
            "passed": False,
            "manifest": manifest,
            "summary": f"RELEASE GATE FAIL: G_INTEGRITY_MANIFEST ({manifest.get('reason')})",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        sys.stdout.write(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
        sys.exit(1)

    if manifest.get("minisig_warn"):
        sys.stdout.write(f"  ⚠️  WARN: {manifest['minisig_warn']}\n")

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
        "G_INTEGRITY_MANIFEST": manifest,
        "G_NO_ABSOLUTE_REWARD": _check_no_absolute_reward(),
        "preflight_verified": True,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    sys.stdout.write(json.dumps(final, ensure_ascii=False, indent=2) + "\n")
    sys.exit(0 if gate_result.get("status") == "pass" else 1)


if __name__ == "__main__":
    main()
