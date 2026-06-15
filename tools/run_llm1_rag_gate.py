#!/usr/bin/env python3
"""run_llm1_rag_gate.py — G_LLM1_RAG (ADR-216, V756)
모든 critic 호출이 RAG 컨텍스트를 강제하는지 검증.
사용: python tools/run_llm1_rag_gate.py [--json]   종료: 0 PASS / 1 FAIL"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from literary_system.critic.base import CriticContext
from literary_system.critic.ensemble import CriticEnsemble


def run_g_llm1_rag() -> dict:
    checks = {}
    # ① CriticContext가 빈 rag_refs 거부
    try:
        CriticContext(rag_refs=[]); checks["ctx_rejects_empty"] = False
    except ValueError:
        checks["ctx_rejects_empty"] = True
    # ② ensemble이 RAG 없는 컨텍스트(비CriticContext) 거부
    class _Bad: rag_refs = []
    try:
        CriticEnsemble(llm=lambda p: "WINNER: A").evaluate("a", "b", _Bad())
        checks["ensemble_requires_rag"] = False
    except ValueError:
        checks["ensemble_requires_rag"] = True
    # ③ 정상 RAG 컨텍스트는 동작
    try:
        CriticEnsemble(llm=lambda p: "WINNER: A").evaluate("긴 텍스트", "짧", CriticContext(rag_refs=["r"]))
        checks["valid_rag_works"] = True
    except Exception:
        checks["valid_rag_works"] = False
    return {"gate": "G_LLM1_RAG", "passed": all(checks.values()), "checks": checks}


def main() -> int:
    ap = argparse.ArgumentParser(); ap.add_argument("--json", action="store_true"); a = ap.parse_args()
    r = run_g_llm1_rag()
    print(json.dumps(r, ensure_ascii=False, indent=2) if a.json
          else f"G_LLM1_RAG: {'PASS' if r['passed'] else 'FAIL'} {r['checks']}")
    return 0 if r["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
