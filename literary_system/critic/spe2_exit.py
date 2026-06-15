"""
critic/spe2_exit.py — SP-E.2 Exit Gate (V761, ADR-221) = Phase E.2 LLM-1 Critic 완료 판정.

5 LLM-1 게이트(BOUNDARY/RAG/ALIGNMENT/SAFETY/COST) + critic 코어 7모듈 + ADR 연속을
통합 검증. 전 항목 PASS → Phase E.2 종료, Phase E.3(UI) 진입 가능.
"""
from __future__ import annotations
import importlib.util
from pathlib import Path
from typing import Dict, List

_REPO = Path(__file__).resolve().parents[2]


def _tool(fn_file: str, fn: str):
    spec = importlib.util.spec_from_file_location("_t", _REPO / "tools" / fn_file)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return getattr(m, fn)


def run_spe2_exit() -> Dict:
    cps: List[Dict] = []
    def add(name, ok, detail=""):
        cps.append({"name": name, "passed": bool(ok), "detail": str(detail)})

    # SC-1~3: tools 게이트
    b = _tool("run_llm1_boundary_gate.py", "run_g_llm1_boundary")()
    add("SC-1 G_LLM1_BOUNDARY", b["passed"], f"위반 {len(b['violations'])}건")
    r = _tool("run_llm1_rag_gate.py", "run_g_llm1_rag")()
    add("SC-2 G_LLM1_RAG", r["passed"], r["checks"])
    a = _tool("run_llm1_alignment_gate.py", "run_g_llm1_alignment")()
    add("SC-3 G_LLM1_ALIGNMENT", a["passed"], f"일치율 {a['agreement_rate']} (min 0.80)")

    # SC-4~5: critic-side
    from literary_system.critic.corpus_gate import CorpusGate
    from literary_system.critic.llm1_metrics import LLM1Metrics
    s = CorpusGate().check(205)
    add("SC-4 G_LLM1_SAFETY", s["passed"], f"corpus {s['n_works']}≥{s['min']}")
    c = LLM1Metrics().check_budget()
    add("SC-5 G_LLM1_COST", c["passed"], f"${c['total_usd']}≤${c['hard']}")

    # SC-6: critic 코어 7모듈 import 가능
    mods = ["base", "llm_critics", "ensemble", "alignment_monitor",
            "corpus_gate", "llm1_metrics", "arbitration"]
    try:
        for mod in mods:
            __import__(f"literary_system.critic.{mod}")
        add("SC-6 critic 코어 7모듈", True, f"{len(mods)}모듈")
    except Exception as e:
        add("SC-6 critic 코어 7모듈", False, str(e))

    # SC-7: ADR 214~220 연속 존재
    adrs = [n for n in range(214, 221) if not (_REPO / "docs/adr" / f"ADR-{n}.md").exists()]
    add("SC-7 ADR-214~220 연속", not adrs, "누락 없음" if not adrs else f"누락 {adrs}")

    passed = all(cp["passed"] for cp in cps)
    return {"gate": "SP-E2-EXIT", "phase": "E.2 LLM-1 Critic",
            "passed": passed, "checkpoints": cps,
            "n_pass": sum(cp["passed"] for cp in cps), "n_total": len(cps)}
