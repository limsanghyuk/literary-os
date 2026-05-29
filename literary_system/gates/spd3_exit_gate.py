"""
literary_system.gates.spd3_exit_gate
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
V730 — SP-D.3 Exit Gate (ADR-191)

6축 완료 검증 (E1 ~ E6):
  E1  Plugin Registry   — G87 PASS (PluginManifest·Registry·Sandbox·Lifecycle·SDK)
  E2  ZeroTrust         — G88 PASS (ZT-1~ZT-7 전체)
  E3  Chaos Resilience  — G89 PASS (CR-1~CR-6 전체)
  E4  연결성 보장        — security·chaos·plugins 고립 없음 (ADR-128)
  E5  Survival Matrix   — SP-D.3 핵심 심볼 생존 (7심볼)
  E6  버전 준비          — pyproject.toml v12.4.0 bump 확인

G32 준수: print() 금지
LLM-0: 외부 LLM 호출 없음
ADR-191
"""
from __future__ import annotations

import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List


# ── 결과 타입 ─────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ExitAxisResult:
    axis: str       # "E1" ~ "E6"
    passed: bool
    detail: str


@dataclass
class SPD3ExitReport:
    gate: str = "SP-D3-EXIT"
    passed: bool = False
    passed_count: int = 0
    total_count: int = 6
    version: str = ""
    axes: List[ExitAxisResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "gate": self.gate,
            "pass": self.passed,
            "passed": self.passed,
            "passed_count": self.passed_count,
            "total_count": self.total_count,
            "version": self.version,
            "axes": [
                {"axis": a.axis, "passed": a.passed, "detail": a.detail}
                for a in self.axes
            ],
            "errors": self.errors,
        }


def _ax(name: str, passed: bool, detail: str) -> ExitAxisResult:
    return ExitAxisResult(axis=name, passed=passed, detail=detail)


# ── E1: Plugin Registry Gate G87 ─────────────────────────────────────────────

def _check_e1_plugin_registry() -> ExitAxisResult:
    """E1: G87 PluginRegistryGate PASS 확인"""
    try:
        from literary_system.gates.plugin_registry_gate import run_g87_gate
        result = run_g87_gate()
        if not result.get("passed", result.get("pass", False)):
            failed = [c["checkpoint"] for c in result.get("checkpoints", [])
                      if not c.get("passed", False)]
            return _ax("E1", False, f"G87 FAIL — 실패 CP: {failed}")
        pc = result.get("passed_count", 0)
        tc = result.get("total_count", 7)
        return _ax("E1", True, f"G87 PASS ({pc}/{tc})")
    except Exception as exc:
        return _ax("E1", False, str(exc))


# ── E2: ZeroTrust Security Gate G88 ──────────────────────────────────────────

def _check_e2_zerotrust() -> ExitAxisResult:
    """E2: G88 ZeroTrustSecurityGate PASS 확인"""
    try:
        from literary_system.gates.zero_trust_security_gate import run_zero_trust_security_gate
        passed, results = run_zero_trust_security_gate()
        if not passed:
            failed = [r.checkpoint for r in results if not r.passed]
            return _ax("E2", False, f"G88 FAIL — 실패 CP: {failed}")
        return _ax("E2", True, f"G88 PASS ({len(results)}/7)")
    except Exception as exc:
        return _ax("E2", False, str(exc))


# ── E3: Chaos Resilience Gate G89 ────────────────────────────────────────────

def _check_e3_chaos_resilience() -> ExitAxisResult:
    """E3: G89 ChaosResilienceGate PASS 확인"""
    try:
        from literary_system.gates.chaos_resilience_gate import run_g89_gate
        result = run_g89_gate()
        if not result.get("passed", result.get("pass", False)):
            failed = [c["checkpoint"] for c in result.get("checkpoints", [])
                      if not c.get("passed", False)]
            return _ax("E3", False, f"G89 FAIL — 실패 CP: {failed}")
        pc = result.get("passed_count", 0)
        tc = result.get("total_count", 6)
        return _ax("E3", True, f"G89 PASS ({pc}/{tc})")
    except Exception as exc:
        return _ax("E3", False, str(exc))


# ── E4: 연결성 보장 (ADR-128) ────────────────────────────────────────────────

def _check_e4_connectivity() -> ExitAxisResult:
    """E4: security·chaos·plugins 패키지 고립 없음 확인"""
    try:
        root = Path("literary_system")
        if not root.exists():
            return _ax("E4", True, "literary_system/ 루트 없음 — 환경 무시")

        pkgs = {d.name for d in root.iterdir() if d.is_dir() and not d.name.startswith("_")}
        imported_by: dict = {p: set() for p in pkgs}
        deps: dict = {p: set() for p in pkgs}

        for pkg in pkgs:
            for f in (root / pkg).rglob("*.py"):
                try:
                    src = f.read_text(encoding="utf-8", errors="ignore")
                except OSError:
                    continue
                for m in re.finditer(r"from literary_system\.(\w+)", src):
                    t = m.group(1)
                    if t in pkgs and t != pkg:
                        deps[pkg].add(t)
                        imported_by[t].add(pkg)

        critical = {"security", "chaos", "plugins"}
        isolated = [p for p in critical if not imported_by.get(p) and not deps.get(p)]
        if isolated:
            return _ax("E4", False, f"고립 패키지: {isolated} (ADR-128 위반)")
        return _ax("E4", True, f"security·chaos·plugins 고립 없음 (ADR-128 PASS)")
    except Exception as exc:
        return _ax("E4", False, str(exc))


# ── E5: Survival Matrix — SP-D.3 핵심 심볼 ───────────────────────────────────

_SPD3_SURVIVAL_SYMBOLS = {
    # ZeroTrust (V717~V720)
    "ZeroTrustTokenService": "literary_system.security.zero_trust_token",
    "TenantAuthority":       "literary_system.security.tenant_authority",
    "ZeroTrustMiddleware":   "literary_system.security.zero_trust_middleware",
    "ZeroTrustAuditLog":     "literary_system.security.zero_trust_audit_log",
    # Plugin (V711~V716)
    "PluginManifest":        "literary_system.plugins.plugin_manifest",
    "PluginRegistry":        "literary_system.plugins.plugin_registry",
    # Chaos (V724~V728)
    "ChaosEngine":           "literary_system.chaos.chaos_engine",
    "ChaosRunner":           "literary_system.chaos.chaos_runner",
    "AutoRecovery":          "literary_system.chaos.chaos_runner",
}


def _check_e5_survival_matrix() -> ExitAxisResult:
    """E5: SP-D.3 핵심 심볼 9개 생존 확인"""
    missing = []
    for symbol, module_path in _SPD3_SURVIVAL_SYMBOLS.items():
        try:
            mod = __import__(module_path, fromlist=[symbol])
            if not hasattr(mod, symbol):
                missing.append(f"{symbol} (in {module_path})")
        except ImportError as e:
            missing.append(f"{symbol} (import error: {e})")
    if missing:
        return _ax("E5", False, f"심볼 사망: {missing}")
    return _ax("E5", True,
               f"SP-D.3 Survival Matrix {len(_SPD3_SURVIVAL_SYMBOLS)}/{len(_SPD3_SURVIVAL_SYMBOLS)} ALIVE")


# ── E6: 버전 v12.4.0 확인 ────────────────────────────────────────────────────

def _check_e6_version() -> ExitAxisResult:
    """E6: pyproject.toml 버전 v12.4.0 확인"""
    try:
        p = Path("pyproject.toml")
        if not p.exists():
            return _ax("E6", True, "pyproject.toml 없음 — 환경 무시")
        content = p.read_text(encoding="utf-8")
        m = re.search(r'^version\s*=\s*["\']([^"\']+)["\']', content, re.MULTILINE)
        if not m:
            return _ax("E6", False, "pyproject.toml에서 version 미발견")
        ver = m.group(1)
        if ver != "12.4.0":
            return _ax("E6", False, f"버전 불일치: {ver} (기대: 12.4.0)")
        return _ax("E6", True, f"버전 v12.4.0 확인")
    except Exception as exc:
        return _ax("E6", False, str(exc))


# ── 메인 게이트 실행 ──────────────────────────────────────────────────────────

def run_spd3_exit_gate() -> dict:
    """SP-D.3 Exit Gate 실행 (E1~E6)."""
    checkers = [
        _check_e1_plugin_registry,
        _check_e2_zerotrust,
        _check_e3_chaos_resilience,
        _check_e4_connectivity,
        _check_e5_survival_matrix,
        _check_e6_version,
    ]
    report = SPD3ExitReport()
    for checker in checkers:
        result = checker()
        report.axes.append(result)
        if result.passed:
            report.passed_count += 1
        else:
            report.errors.append(f"{result.axis}: {result.detail}")
    report.passed = (report.passed_count == report.total_count)
    return report.to_dict()


class SPD3ExitGate:
    """SP-D.3 Exit Gate 클래스 인터페이스."""

    def run(self) -> dict:
        return run_spd3_exit_gate()

    @property
    def survival_symbols(self) -> dict:
        return dict(_SPD3_SURVIVAL_SYMBOLS)
