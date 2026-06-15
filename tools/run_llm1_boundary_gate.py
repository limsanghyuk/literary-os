#!/usr/bin/env python3
"""run_llm1_boundary_gate.py — G_LLM1_BOUNDARY (ADR-214, V753)

LLM-1 경계: 외부 LLM은 critic/·adapters_live/ 에서만 허용.
corpus/·constitution/·finetune/ 에 외부 LLM 호출/임포트가 있으면 FAIL.
(주석·문자열이 아닌 실제 import/호출 라인만 검사)
사용법: python tools/run_llm1_boundary_gate.py [--json]   종료: 0 PASS / 1 FAIL
"""
from __future__ import annotations
import argparse, json, re, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
FORBIDDEN = ["corpus", "constitution", "finetune"]
PATTERNS = [
    r"^\s*import\s+openai", r"^\s*from\s+openai\b",
    r"^\s*import\s+anthropic", r"^\s*from\s+anthropic\b",
    r"\bOpenAI\s*\(", r"\bAnthropic\s*\(",
    r"api\.openai\.com/v1/(chat|responses|completions)",
    r"\bchat\.completions\.create", r"\bmessages\.create\b",
]
_RX = [re.compile(p) for p in PATTERNS]


def _strip_noncode(line: str) -> str:
    s = line.split("#", 1)[0]                       # 주석 제거
    return s


def run_g_llm1_boundary() -> dict:
    violations = []
    for d in FORBIDDEN:
        base = REPO / "literary_system" / d
        if not base.exists():
            continue
        for py in base.rglob("*.py"):
            for n, raw in enumerate(py.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
                line = _strip_noncode(raw)
                for rx in _RX:
                    if rx.search(line):
                        violations.append({"file": str(py.relative_to(REPO)), "line": n, "code": raw.strip()[:80]})
    return {"gate": "G_LLM1_BOUNDARY", "passed": not violations,
            "checked_dirs": FORBIDDEN, "violations": violations}


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--json", action="store_true")
    a = ap.parse_args()
    r = run_g_llm1_boundary()
    if a.json:
        print(json.dumps(r, ensure_ascii=False, indent=2))
    else:
        print(f"G_LLM1_BOUNDARY: {'PASS' if r['passed'] else 'FAIL'} "
              f"(검사 {r['checked_dirs']}, 위반 {len(r['violations'])}건)")
        for v in r["violations"][:10]:
            print(f"  {v['file']}:{v['line']}  {v['code']}")
    return 0 if r["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
