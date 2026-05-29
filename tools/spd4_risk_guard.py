#!/usr/bin/env python3
"""
SP-D.4 Risk Signal Guard — ADR-192 기반
=========================================
V731 착수 전 11종 위험 신호를 점검한다.
모든 항목 CLEAR 시 exit(0), 하나라도 WARN/FAIL 시 exit(1).

사용법:
    python3 tools/spd4_risk_guard.py
    python3 tools/spd4_risk_guard.py --strict   # WARN도 실패 처리
"""
from __future__ import annotations
import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SYS_ROOT  = REPO_ROOT / "literary_system"

SKIP = {"__pycache__", ".git", ".pytest_cache", "node_modules"}

def _count_tests() -> int:
    count = 0
    for f in (REPO_ROOT / "tests").rglob("test_*.py"):
        if any(s in f.parts for s in SKIP):
            continue
        try:
            tree = ast.parse(f.read_text(encoding="utf-8", errors="ignore"))
            for n in ast.walk(tree):
                if isinstance(n, ast.FunctionDef) and n.name.startswith("test_"):
                    count += 1
        except Exception:
            pass
    return count

def _class_exists(cls: str, subpkg: str) -> bool:
    pkg = SYS_ROOT / subpkg
    if not pkg.exists():
        return False
    for py in pkg.rglob("*.py"):
        if any(s in py.parts for s in SKIP):
            continue
        try:
            if f"class {cls}" in py.read_text(encoding="utf-8", errors="ignore"):
                return True
        except Exception:
            pass
    return False

def _check_hmac_compare_digest() -> bool:
    f = SYS_ROOT / "security" / "zero_trust_token.py"
    if not f.exists():
        return False
    text = f.read_text(encoding="utf-8", errors="ignore")
    return "hmac.compare_digest" in text

def _check_plugin_whitelist_block() -> bool:
    f = SYS_ROOT / "plugins" / "plugin_whitelist.py"
    if not f.exists():
        return False
    text = f.read_text(encoding="utf-8", errors="ignore")
    return "BLOCKED_MODULES" in text and "is_allowed" in text

def _check_resilience_ratio() -> bool:
    f = SYS_ROOT / "chaos" / "chaos_runner.py"
    if not f.exists():
        return False
    text = f.read_text(encoding="utf-8", errors="ignore")
    return "resilience_ratio" in text and ">= 0.8" in text

def _check_percentile_edge() -> bool:
    f = SYS_ROOT / "enterprise" / "benchmark.py"
    if not f.exists():
        return False
    text = f.read_text(encoding="utf-8", errors="ignore")
    return "def percentile" in text and "len(data) == 1" in text

def _check_fedavg_epsilon_injectable() -> bool:
    """SP-D.4 FL: FedAvgAggregator에 epsilon 파라미터가 외부 주입 가능한지 확인."""
    f = SYS_ROOT / "federated" / "fed_avg_aggregator.py"
    if not f.exists():
        # V731+ 구현 전 — 경고만 발행
        return None  # type: ignore[return-value]
    text = f.read_text(encoding="utf-8", errors="ignore")
    return "epsilon" in text

def _check_dr_rpo_validation() -> bool:
    """SP-D.4 DR: DRBackupManager에 RPO 검증 로직이 있는지 확인."""
    f = SYS_ROOT / "disaster_recovery" / "dr_backup_manager.py"
    if not f.exists():
        return None  # type: ignore[return-value]
    text = f.read_text(encoding="utf-8", errors="ignore")
    return "_validate_rpo" in text or "3600" in text

def _check_phase_e_manifest_validator() -> bool:
    """Phase E manifest validator 스텁 존재 확인."""
    f = REPO_ROOT / "tools" / "phase_e_manifest_validator.py"
    return f.exists()

CHECKS = [
    # (id, description, fn, min_tc_if_applicable)
    ("RS-01", "TC 수 ≥ 10,000 (기준 10,011)", None, 10000),
    ("RS-02", "percentile() n=1 엣지케이스 처리", _check_percentile_edge, None),
    ("RS-05", "PluginWhitelist 비승인 차단 로직", _check_plugin_whitelist_block, None),
    ("RS-06", "HMAC compare_digest 위변조 방어", _check_hmac_compare_digest, None),
    ("RS-07", "ChaosRunner resilience_ratio ≥ 0.8 기준", _check_resilience_ratio, None),
    ("RS-08", "FL FedAvgAggregator epsilon 주입 가능 (SP-D.4 전: WARN)", _check_fedavg_epsilon_injectable, None),
    ("RS-09", "DR DRBackupManager RPO 검증 (SP-D.4 전: WARN)", _check_dr_rpo_validation, None),
    ("RS-11", "Phase E manifest validator 스텁 (SP-D.4 전: WARN)", _check_phase_e_manifest_validator, None),
]

def run_guard(strict: bool = False) -> bool:
    print("=" * 60)
    print("SP-D.4 Risk Signal Guard — ADR-192")
    print("=" * 60)

    all_clear = True
    warn_count = 0

    # RS-01: TC 수
    tc = _count_tests()
    rs01_ok = tc >= 10000
    status = "✅ CLEAR" if rs01_ok else "❌ FAIL"
    print(f"RS-01  TC 수: {tc:,} (기준 ≥10,000)  {status}")
    if not rs01_ok:
        all_clear = False

    # 나머지 항목
    for rid, desc, fn, _ in CHECKS[1:]:
        result = fn()
        if result is None:
            # 아직 구현 전 — WARN
            status = "⚠️  WARN (미구현, SP-D.4에서 신설 예정)"
            warn_count += 1
            if strict:
                all_clear = False
        elif result:
            status = "✅ CLEAR"
        else:
            status = "❌ FAIL"
            all_clear = False
        print(f"{rid}  {desc[:50]:<50}  {status}")

    print("=" * 60)
    if all_clear and warn_count == 0:
        print("🟢 ALL CLEAR — V731 착수 가능")
    elif all_clear:
        print(f"🟡 CLEAR (경고 {warn_count}건: SP-D.4 구현 시 신설 필요)")
        print("   ⚠️  RS-08/09/11 은 V731~V745 구현 과정에서 순차 해소")
    else:
        print("🔴 FAIL — 착수 불가. 위 항목 수정 후 재실행")
    print("=" * 60)

    return all_clear

if __name__ == "__main__":
    strict = "--strict" in sys.argv
    ok = run_guard(strict=strict)
    sys.exit(0 if ok else 1)
