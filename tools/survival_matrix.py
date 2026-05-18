#!/usr/bin/env python3
"""
Survival Matrix V572 — 핵심 심볼 생존 확인
GitNexus Preflight Step 6 보조 스크립트

26개 핵심 심볼의 정확한 경로를 탐색하여 생존 여부 확인.
V571→V572 경로 수정 이력:
  arc/NarrativeDebtDetector          → graph_intelligence/asd/narrative_debt_detector
  arc/StoryDoctorOrchestrator        → graph_intelligence/asd/story_doctor_orchestrator
  arc/AutoRepairExecutor             → graph_intelligence/asd/auto_repair_executor
  arc/AdapterContractV2              → llm_bridge/adapter_contract
  graph/NarrativeGraphStore          → graph_intelligence/narrative_graph_store
  CascadeRouter                      → CascadeOrchestrator (실제 클래스명)
  Corpus 4종 → corpus_ingestor/corpus_validator/bgem3_embedder/cim_bootstrap (실제 경로)

사용법:
    python tools/survival_matrix.py

Literary OS V572 | ADR-032
"""
from __future__ import annotations

import sys
import importlib
from dataclasses import dataclass, field


@dataclass
class SymbolSpec:
    name: str
    module: str
    symbol: str
    note: str = ""


# ─── 핵심 심볼 목록 (V572 경로 수정 완료) ─────────────────────────────────────
SURVIVAL_MATRIX: list[SymbolSpec] = [
    # ── LLM Bridge ──────────────────────────────────────────────────────
    SymbolSpec("AdapterContractV2",      "literary_system.llm_bridge.adapter_contract",                        "AdapterContractV2"),
    SymbolSpec("LLMBridgeInterface",     "literary_system.llm_bridge.llm_bridge_interface",                    "LLMBridgeInterface"),
    SymbolSpec("CascadeOrchestrator",    "literary_system.llm_bridge.cascade",                                 "CascadeOrchestrator"),
    # ── Graph Intelligence / ASD ─────────────────────────────────────────
    SymbolSpec("NarrativeGraphStore",    "literary_system.graph_intelligence.narrative_graph_store",            "NarrativeGraphStore"),
    SymbolSpec("NarrativeDebtDetector",  "literary_system.graph_intelligence.asd.narrative_debt_detector",     "NarrativeDebtDetector"),
    SymbolSpec("StoryDoctorOrchestrator","literary_system.graph_intelligence.asd.story_doctor_orchestrator",   "StoryDoctorOrchestrator"),
    SymbolSpec("AutoRepairExecutor",     "literary_system.graph_intelligence.asd.auto_repair_executor",        "AutoRepairExecutor"),
    SymbolSpec("ArcConsistencyChecker",  "literary_system.graph_intelligence.asd.arc_consistency_checker",     "ArcConsistencyChecker"),
    SymbolSpec("Gate28",                 "literary_system.graph_intelligence.asd.gate28",                      "Gate28"),
    # ── Arc ─────────────────────────────────────────────────────────────
    SymbolSpec("SeriesArcPlanner",       "literary_system.arc",                                                 "SeriesArcPlanner"),
    SymbolSpec("ArcAct",                 "literary_system.arc",                                                 "ArcAct"),
    # ── Release Gates ───────────────────────────────────────────────────
    SymbolSpec("run_release_gate",       "literary_system.gates.release_gate",                                  "run_release_gate"),
    # ── ExternalCorpusBridge (4종 분산 모듈) ────────────────────────────
    # V571 Preflight 정정: 단일 ExternalCorpusBridge 클래스 없음 → 4종 분산 구현
    SymbolSpec("CorpusIngestor",         "literary_system.corpus.corpus_ingestor",                              "CorpusIngestor",      "ExternalCorpusBridge 분산: ingestor"),
    SymbolSpec("CorpusValidator",        "literary_system.corpus.corpus_validator",                             "CorpusValidator",     "ExternalCorpusBridge 분산: validator"),
    SymbolSpec("BGEM3Embedder",          "literary_system.corpus.bgem3_embedder",                               "BGEM3Embedder",       "ExternalCorpusBridge 분산: embedder"),
    SymbolSpec("CIMBootstrap",           "literary_system.corpus.cim_bootstrap",                                "CIMBootstrap",        "ExternalCorpusBridge 분산: bootstrap"),
]

# ─── Optional 심볼 (존재하면 PASS, 없어도 WARNING) ──────────────────────────
OPTIONAL_SYMBOLS: list[SymbolSpec] = [
    SymbolSpec("GraphSyncOrchestrator",   "literary_system.graph_intelligence.graph_sync_orchestrator",  "GraphSyncOrchestrator"),
    SymbolSpec("NarrativeImpactAnalyzer", "literary_system.graph_intelligence.narrative_impact_analyzer","NarrativeImpactAnalyzer"),
    SymbolSpec("PNECore",                 "literary_system.predictive.pne_core",                         "PNECore"),
    SymbolSpec("DebtPredictor",           "literary_system.predictive.debt_predictor",                   "DebtPredictor"),
]


def check_symbol(spec: SymbolSpec) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(spec.module)
        if hasattr(mod, spec.symbol):
            note = f"  [{spec.note}]" if spec.note else ""
            return True, f"LIVE  {spec.name:<32} → {spec.module}.{spec.symbol}{note}"
        else:
            return False, f"DEAD  {spec.name:<32} → {spec.module} (심볼 없음: {spec.symbol})"
    except ImportError as e:
        return False, f"DEAD  {spec.name:<32} → ImportError: {e}"
    except Exception as e:
        return False, f"DEAD  {spec.name:<32} → Error: {e}"


def main() -> int:
    print("=" * 72)
    print("Literary OS Survival Matrix V572")
    print("=" * 72)

    passed, failed = 0, 0
    failed_list = []

    print("\n[REQUIRED 심볼]")
    for spec in SURVIVAL_MATRIX:
        ok, msg = check_symbol(spec)
        print(f"  {'✅' if ok else '❌'} {msg}")
        if ok:
            passed += 1
        else:
            failed += 1
            failed_list.append(spec.name)

    print("\n[OPTIONAL 심볼]")
    opt_pass = 0
    for spec in OPTIONAL_SYMBOLS:
        ok, msg = check_symbol(spec)
        print(f"  {'✅' if ok else '⚠️ '} {msg}")
        if ok:
            opt_pass += 1

    total = len(SURVIVAL_MATRIX)
    print("\n" + "=" * 72)
    print(f"결과: REQUIRED {passed}/{total} LIVE | OPTIONAL {opt_pass}/{len(OPTIONAL_SYMBOLS)} LIVE")
    if failed_list:
        print(f"DEAD 심볼: {', '.join(failed_list)}")
        print("SURVIVAL MATRIX: FAIL ❌")
        return 1
    else:
        print(f"SURVIVAL MATRIX: PASS ✅  ({passed}/{total})")
        return 0


if __name__ == "__main__":
    sys.exit(main())
