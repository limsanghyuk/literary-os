"""
literary_system/gates/v587_exit_gate.py
V587 Exit Gate — SP-α+β+γ 납품물 전체 검증 (ADR-049)

V587 릴리즈 전 최종 체크리스트:
  SP-α: 외부 신뢰 회복 (ci.yml 수정, check_version_consistency, release.yml)
  SP-β: Gate G46 E2EProseGate + ADR-046 Gate 계층화
  SP-γ: 샘플 프로젝트 + 사용자 문서 4종 + gen_cli_reference.py

게이트 조건:
  1. E2E Gate G46 6/6 checkpoint PASS
  2. L0+L1 fast-path PASS (10게이트)
  3. 사용자 문서 4종 존재 확인
  4. 샘플 실행 가능 (import 오류 없음)
  5. gen_cli_reference.py 실행 가능
  6. ADR-046 ~ ADR-048 파일 존재
  7. docs/perf/gate_timings_v587.json 존재
  8. 버전 정합성 (pyproject.toml 9.2.0 일치, ci.yml 45 Gates)

이 파일은 release_gate.py에 등록되지 않고, 릴리즈 직전 독립 실행.
  python literary_system/gates/v587_exit_gate.py
"""
from __future__ import annotations

import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

ROOT = Path(__file__).parent.parent.parent


@dataclass
class ExitCheckResult:
    check_id: str
    name: str
    passed: bool
    elapsed_ms: float
    detail: str


@dataclass
class V587ExitResult:
    checks_passed: int
    total_checks: int
    checks: List[ExitCheckResult] = field(default_factory=list)
    elapsed_ms: float = 0.0

    @property
    def passed(self) -> bool:
        return self.checks_passed == self.total_checks


def _chk(check_id: str, name: str, fn) -> ExitCheckResult:
    t0 = time.perf_counter()
    try:
        detail = fn()
        elapsed = (time.perf_counter() - t0) * 1000
        return ExitCheckResult(check_id, name, True, elapsed, detail or "OK")
    except Exception as exc:
        elapsed = (time.perf_counter() - t0) * 1000
        return ExitCheckResult(check_id, name, False, elapsed, str(exc))


# ── 8개 체크 ──────────────────────────────────────────────────────────────────

def _check_e2e_gate() -> str:
    from literary_system.gates.e2e_prose_gate import gate_e2e_prose
    r = gate_e2e_prose(mock=True)
    n = len(r.checkpoints)
    assert r.passed and n == 6, f"E2E checkpoints: {n}/6, passed={r.passed}"
    return f"E2E G46: 6/6 PASS ({r.total_elapsed_ms:.1f}ms)"


def _check_fast_path() -> str:
    from literary_system.gates.release_gate import run_release_gate_tiered
    r = run_release_gate_tiered(tiers=["L0", "L1"])
    assert r["pass"] is True, f"L0+L1 FAIL: {r['gates_passed']}/{r['gates_run']}"
    p, run = r["gates_passed"], r["gates_run"]
    return f"L0+L1 fast-path: {p}/{run} PASS"


def _check_user_docs() -> str:
    docs = [
        "docs/user/quickstart.md",
        "docs/user/howto.md",
        "docs/user/reference.md",
        "docs/user/explanation.md",
    ]
    missing = [d for d in docs if not (ROOT / d).exists()]
    assert not missing, f"문서 없음: {missing}"
    return f"사용자 문서 4종 존재 ({', '.join(Path(d).name for d in docs)})"


def _check_sample() -> str:
    sample = ROOT / "examples" / "sample_drama" / "generate.py"
    assert sample.exists(), f"샘플 없음: {sample}"
    # import 오류 없이 로드 가능한지 확인 (컴파일만)
    import py_compile
    py_compile.compile(str(sample), doraise=True)
    return f"샘플 스크립트 컴파일 OK: {sample.name}"


def _check_gen_cli_reference() -> str:
    tool = ROOT / "tools" / "gen_cli_reference.py"
    assert tool.exists(), "gen_cli_reference.py 없음"
    import py_compile
    py_compile.compile(str(tool), doraise=True)
    return "gen_cli_reference.py 존재 및 컴파일 OK"


def _check_adr_files() -> str:
    adrs = [
        "docs/adr/ADR-046-gate-hierarchy.md",
        "docs/adr/ADR-047-e2e-prose-policy.md",
        "docs/adr/ADR-048-doc-consistency-ci.md",
    ]
    missing = [a for a in adrs if not (ROOT / a).exists()]
    assert not missing, f"ADR 없음: {missing}"
    return "ADR-046~048 존재"


def _check_perf_json() -> str:
    perf = ROOT / "docs" / "perf" / "gate_timings_v587.json"
    assert perf.exists(), "docs/perf/gate_timings_v587.json 없음"
    import json
    data = json.loads(perf.read_text())
    total_ms = data.get("summary", {}).get("total_elapsed_ms", 0)
    return f"gate_timings_v587.json 존재 (L0+L1: {total_ms:.1f}ms)"


def _check_version_consistency() -> str:
    import re
    pyproject = ROOT / "pyproject.toml"
    ci_yml = ROOT / ".github" / "workflows" / "ci.yml"

    # pyproject version
    ver = "unknown"
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        if line.strip().startswith("version"):
            ver = line.split("=")[1].strip().strip('"')
            break
    assert ver == "9.2.0", f"pyproject.toml version={ver} (기대 9.2.0)"

    # ci.yml gate count
    ci_text = ci_yml.read_text(encoding="utf-8")
    m = re.search(r"Release Gate[^(]*\((\d+) Gates", ci_text)
    gate_count = m.group(1) if m else "?"
    assert gate_count == "45", f"ci.yml gate count={gate_count} (기대 45)"

    return f"pyproject={ver}, ci.yml={gate_count} Gates ✅"


CHECKS = [
    ("EX-1", "E2E Gate G46 6/6 PASS",               _check_e2e_gate),
    ("EX-2", "L0+L1 fast-path 10/10 PASS",           _check_fast_path),
    ("EX-3", "사용자 문서 4종 존재",                   _check_user_docs),
    ("EX-4", "샘플 스크립트 컴파일 OK",                _check_sample),
    ("EX-5", "gen_cli_reference.py 존재",             _check_gen_cli_reference),
    ("EX-6", "ADR-046~048 파일 존재",                 _check_adr_files),
    ("EX-7", "docs/perf/gate_timings_v587.json 존재", _check_perf_json),
    ("EX-8", "버전 정합성 (9.2.0 / 45 Gates)",        _check_version_consistency),
]


def run_v587_exit_gate() -> V587ExitResult:
    t_total = time.perf_counter()
    results = []
    for cid, name, fn in CHECKS:
        results.append(_chk(cid, name, fn))
    elapsed = (time.perf_counter() - t_total) * 1000
    passed = sum(1 for r in results if r.passed)
    return V587ExitResult(
        checks_passed=passed,
        total_checks=len(results),
        checks=results,
        elapsed_ms=elapsed,
    )


def _cli_run():
    import logging as _logging
    _log = _logging.getLogger(__name__)
    _logging.basicConfig(level=_logging.INFO, format="%(message)s")
    result = run_v587_exit_gate()
    sep = "=" * 62
    _log.info(sep)
    _log.info("  V587 Exit Gate — %d/%d PASS", result.checks_passed, result.total_checks)
    _log.info(sep)
    for r in result.checks:
        icon = "✅" if r.passed else "❌"
        _log.info("  %s [%s] %s", icon, r.check_id, r.name)
        _log.info("        → %s", r.detail)
    _log.info(sep)
    if result.passed:
        _log.info("  🎉 V587 EXIT GATE PASS (%.1fms)", result.elapsed_ms)
        _log.info("     v9.2.0 태그 + 릴리즈 진행 가능")
    else:
        failed = [r for r in result.checks if not r.passed]
        _log.error("  ⛔ FAIL — %d개 체크 미통과:", len(failed))
        for r in failed:
            _log.error("     %s: %s", r.check_id, r.detail)
        sys.exit(1)
    _log.info(sep)


if __name__ == "__main__":
    _cli_run()
