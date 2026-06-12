#!/usr/bin/env python3
"""
Preflight Nexus — GitNexus-Native 연결성·단절·영향 자동 감사 도구 (V612)

PREFLIGHT_GUIDE_v1.1.md §1.1 (context/impact/detect_changes) + §5 (Survival Matrix)를
완전 자동화한다. 매 개발 단계 진입 전 자동 실행되며 CI에서도 블로킹 게이트로 작동한다.

검사 항목:
  1. .gitnexus staleness  — 인덱스가 현재 파일 목록과 일치하는가
  2. Survival Matrix      — Phase별 핵심 심볼이 살아있는가 (V612 갱신)
  3. Orphan 탐지          — 아무도 참조하지 않는 literary_system/* 모듈
  4. 신규 모듈 연결성     — SP-B.3 신규 모듈이 기존 신경망에 연결되어 있는가
  5. 순환 의존 탐지       — 실질 순환 (lazy import 아닌 진짜 순환)

사용법:
    python tools/preflight_nexus.py              # 보고서 출력
    python tools/preflight_nexus.py --strict     # 위반 시 exit(1) [CI용]
    python tools/preflight_nexus.py --phase sp_b3 # SP-B.3 심볼만 확인
"""

from __future__ import annotations

import ast
import json
import sys
import argparse
from pathlib import Path
from collections import defaultdict
from typing import NamedTuple

REPO_ROOT   = Path(__file__).resolve().parent.parent
SYS_ROOT    = REPO_ROOT / "literary_system"
GITNEXUS_META = REPO_ROOT / ".gitnexus" / "meta.json"

SKIP = {"__pycache__", ".git", ".pytest_cache", "node_modules", "literary_os.egg-info"}

# ──────────────────────────────────────────────────────────────────────────────
# Survival Matrix — V612 갱신 (실제 경로 검증 완료)
# 새 Phase/SP 추가 시 이 딕셔너리만 갱신하면 됨
# ──────────────────────────────────────────────────────────────────────────────
SURVIVAL_MATRIX: dict[str, dict[str, str]] = {
    "core": {
        "UnifiedLLMGateway":          "literary_system/llm_bridge/",
        "TaskRouter":                 "literary_system/llm_bridge/",
        "NKGCurator":                 "literary_system/nkg/",
        "CostLedger":                 "literary_system/llm_bridge/",
        "LLMAdapterContractGate":     "literary_system/gates/",
        "RAGPipelineOrchestrator":    "literary_system/pipelines/",
        "HybridRetrieverV2":          "literary_system/rag/",
    },
    "nie": {
        "RewardModel":                "literary_system/rlhf/",
        "PPOTrainer":                 "literary_system/rlhf/",
        "CIM":                        "literary_system/nie/",
        "TemporalCIM":                "literary_system/nie/",
        "MetaLearner":                "literary_system/nie/",
        "NarrativeTensionCurve":      "literary_system/nie/",
    },
    "gig": {
        "NarrativeGraphStore":        "literary_system/graph_intelligence/",
        "NarrativeImpactAnalyzer":    "literary_system/graph_intelligence/",
        "CodeDependencyGraph":        "literary_system/graph_intelligence/",
        "PlanBuildProtocol":          "literary_system/graph_intelligence/",
        "NarrativeDebtDetector":      "literary_system/graph_intelligence/asd/",
        "StoryDoctorOrchestrator":    "literary_system/graph_intelligence/asd/",
    },
    "phase_a": {
        "SchemaRegistry":             "literary_system/db/",
        "MigrationManager":           "literary_system/db/",
        "LOSDBClient":                "literary_system/db/",
        "LOSConstitution":            "literary_system/constitution/",
        "V587ExitResult":             "literary_system/gates/",
    },
    "sp_b1": {
        "LoRADatasetBuilder":         "literary_system/finetune/",
        "LoRATrainingConfig":         "literary_system/finetune/",
        "LoRAJobRunner":              "literary_system/finetune/",
        "LoRAArtifact":               "literary_system/finetune/",
        "LoRAModelRegistry":          "literary_system/finetune/",
        "LoRAInferenceGateway":       "literary_system/finetune/",
        "ProvenanceLedger":           "literary_system/storage/",
    },
    "sp_b2": {
        "RewardModel":                "literary_system/rlhf/",
        "PPOTrainer":                 "literary_system/rlhf/",
        "ConstraintGuard":            "literary_system/rlhf/",
        "RLHFMonitor":                "literary_system/rlhf/",
        "CanaryController":           "literary_system/serving/",
        "ModelServingEndpoint":       "literary_system/serving/",
        "CanonicalBridgeV2":          "literary_system/llm_bridge/",
    },
    "sp_b3": {
        "SharedCharacterDBV2":        "literary_system/multiwork/",
        "SharedWorldDBV2":            "literary_system/multiwork/",
        "MultiWorkOrchestratorV2":    "literary_system/multiwork/",
        "MultiWorkCIMV2":             "literary_system/multiwork/",
        "MultiWorkCIM":               "literary_system/multiwork/",
        "CIMVersion":                 "literary_system/multiwork/",
        "GenreTransferV2":            "literary_system/multiwork/",
        "LoRAStackingAdapter":        "literary_system/serving/",
    },
}

# 알려진 레거시 잔류 단절 모듈 (V328~V400, 정리 대상)
KNOWN_LEGACY_ORPHANS = {
    "literary_system/schemas/character_birth_gate_result.py",
    "literary_system/schemas/character_grid.py",
    "literary_system/schemas/commander_briefing.py",
    "literary_system/schemas/critic_decision_packet.py",
    "literary_system/schemas/final_acceptance_packet.py",
    "literary_system/schemas/format_constitution_packet.py",
    "literary_system/schemas/intent_seed_packet.py",
    "literary_system/schemas/literary_state_snapshot.py",
    "literary_system/schemas/pressure_cast_plan.py",
    "literary_system/schemas/residue_variation_plan.py",
    "literary_system/schemas/scene_digest.py",
    "literary_system/retrieval/briefing_retriever.py",
    "literary_system/retrieval/relation_retriever.py",
    "literary_system/retrieval/scene_retriever.py",
    "literary_system/adapters/project_pipeline.py",
    "literary_system/adapters/spec_designer.py",
}

# 알려진 정상 순환 (lazy import로 실제 런타임 순환 아님)
KNOWN_SAFE_CYCLES = {
    frozenset(["literary_system/gates/gate_registry.py",
               "literary_system/gates/release_gate.py"]),
    frozenset(["literary_system/gates/phase_a_exit_gate.py",
               "literary_system/gates/release_gate.py"]),
    # Phase B/C/D exit gates — lazy import (함수 내부), 런타임 순환 아님
    frozenset(["literary_system/gates/phase_b_exit_gate.py",
               "literary_system/gates/release_gate.py"]),
    frozenset(["literary_system/gates/phase_c_exit_gate.py",
               "literary_system/gates/release_gate.py"]),
    frozenset(["literary_system/gates/phase_d_exit_gate.py",
               "literary_system/gates/release_gate.py"]),
    frozenset(["literary_system/multiwork/multi_work_cim.py",
               "literary_system/multiwork/multi_work_cim_v2.py"]),
}

# SP-B.3 연결성 검증 대상
CONNECTIVITY_TARGETS = {
    "literary_system/multiwork/genre_transfer.py":             "genre_transfer",
    "literary_system/serving/lora_stacking_adapter.py":        "lora_stacking_adapter",
    "literary_system/multiwork/multi_work_cim_v2.py":          "multi_work_cim_v2",
    "literary_system/multiwork/multi_work_orchestrator_v2.py": "multi_work_orchestrator_v2",
    "literary_system/multiwork/shared_character_db_v2.py":     "shared_character_db_v2",
    "literary_system/multiwork/shared_world_db_v2.py":         "shared_world_db_v2",
    "literary_system/rlhf/reward_model.py":                    "reward_model",
    "literary_system/rlhf/ppo_trainer.py":                     "ppo_trainer",
    "literary_system/serving/canary_controller.py":            "canary_controller",
    "literary_system/llm_bridge/canonical_bridge_v2.py":       "canonical_bridge_v2",
    "literary_system/finetune/lora_inference_gateway.py":      "lora_inference_gateway",
}


class Issue(NamedTuple):
    level:  str   # CRITICAL / HIGH / MEDIUM / INFO
    check:  str
    detail: str


# ──────────────────────────────────────────────────────────────────────────────
def collect_py_files() -> dict[str, Path]:
    files = {}
    for f in sorted(REPO_ROOT.rglob("*.py")):
        if any(s in f.parts for s in SKIP):
            continue
        rel = str(f.relative_to(REPO_ROOT))
        files[rel] = f
    return files


def parse_imports(fpath: Path) -> set[str]:
    try:
        src  = fpath.read_text(encoding="utf-8", errors="ignore")
        tree = ast.parse(src)
    except SyntaxError:
        return set()
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.add(alias.name)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module)
    return imports


# ──────────────────────────────────────────────────────────────────────────────
# 검사 1: .gitnexus staleness
# ──────────────────────────────────────────────────────────────────────────────
def check_staleness() -> list[Issue]:
    if not GITNEXUS_META.exists():
        return [Issue("HIGH", "staleness",
                      ".gitnexus/meta.json 없음 — `git-nexus index` 재실행 필요")]
    with open(GITNEXUS_META) as f:
        meta = json.load(f)
    indexed = set(meta.get("fileHashes", {}).keys())
    current = set(collect_py_files())
    new_cnt = len(current - indexed)
    commit  = meta.get("lastCommit", "?")[:8]
    if new_cnt:
        return [Issue("HIGH", "staleness",
                      f"인덱스 stale (commit {commit}) — 신규 파일 {new_cnt}개 미반영. "
                      f"`git-nexus index` 재실행 필요")]
    return [Issue("INFO", "staleness", f"인덱스 최신 (commit {commit})")]


# ──────────────────────────────────────────────────────────────────────────────
# 검사 2: Survival Matrix
# ──────────────────────────────────────────────────────────────────────────────
def check_survival(phase_filter: str | None) -> list[Issue]:
    issues: list[Issue] = []
    layers = {k: v for k, v in SURVIVAL_MATRIX.items()
              if not phase_filter or phase_filter.lower() in k}
    for layer, symbols in layers.items():
        for cls, path in symbols.items():
            full = REPO_ROOT / path
            found = any(
                f"class {cls}" in p.read_text(encoding="utf-8", errors="ignore")
                for p in full.rglob("*.py")
                if not any(s in p.parts for s in SKIP)
            ) if full.exists() else False
            if not found:
                issues.append(Issue("CRITICAL", "survival",
                                    f"[{layer}] {cls} DEAD — {path}"))
    return issues


# ──────────────────────────────────────────────────────────────────────────────
# 검사 3: Orphan 모듈
# ──────────────────────────────────────────────────────────────────────────────
def check_orphans() -> list[Issue]:
    py_files = collect_py_files()
    all_imports: set[str] = set()
    for fpath in py_files.values():
        all_imports.update(parse_imports(fpath))

    ls_mods = [r for r in py_files
               if r.startswith("literary_system/") and not r.endswith("__init__.py")]

    orphans, legacy = [], []
    for rel in ls_mods:
        mod   = rel.replace("/", ".").replace(".py", "")
        short = mod.split(".")[-1]
        pkg   = ".".join(mod.split(".")[:-1])
        if not (mod in all_imports or short in all_imports or pkg in all_imports):
            (legacy if rel in KNOWN_LEGACY_ORPHANS else orphans).append(rel)

    issues = [Issue("HIGH", "orphan", f"신규 단절 모듈: {o}") for o in orphans]
    if legacy:
        issues.append(Issue("MEDIUM", "orphan",
                            f"레거시 잔류 단절 {len(legacy)}개 (schemas/retrieval/adapters) "
                            f"— SP-B.4에서 정리 권장"))
    return issues


# ──────────────────────────────────────────────────────────────────────────────
# 검사 4: 신규 모듈 연결성
# ──────────────────────────────────────────────────────────────────────────────
def check_connectivity() -> list[Issue]:
    py_files = collect_py_files()
    file_imports = {r: parse_imports(f) for r, f in py_files.items()}
    issues: list[Issue] = []
    for fpath, short in CONNECTIVITY_TARGETS.items():
        if fpath not in py_files:
            issues.append(Issue("CRITICAL", "connectivity", f"파일 없음: {fpath}"))
            continue
        callers = [r for r, imps in file_imports.items()
                   if r != fpath and any(short in i for i in imps)]
        if not callers:
            issues.append(Issue("HIGH", "connectivity",
                                f"단절 위험: {fpath.split('/')[-1]} — 참조 모듈 0개"))
    return issues


# ──────────────────────────────────────────────────────────────────────────────
# 검사 5: 실질 순환 의존 (알려진 lazy-import 정상 순환 제외)
# ──────────────────────────────────────────────────────────────────────────────
def check_circular() -> list[Issue]:
    py_files = collect_py_files()
    file_imports = {r: parse_imports(f) for r, f in py_files.items()}
    ls_mods = [r for r in py_files if r.startswith("literary_system/")]
    seen: set[frozenset] = set()
    issues: list[Issue] = []
    for rel in ls_mods:
        my_imps = file_imports.get(rel, set())
        for other in ls_mods:
            if other == rel:
                continue
            other_short = other.replace("/", ".").replace(".py", "").split(".")[-1]
            other_mod   = other.replace("/", ".").replace(".py", "")
            if any(other_short in i or other_mod in i for i in my_imps):
                other_imps  = file_imports.get(other, set())
                my_short    = rel.replace("/", ".").replace(".py", "").split(".")[-1]
                my_mod      = rel.replace("/", ".").replace(".py", "")
                if any(my_short in i or my_mod in i for i in other_imps):
                    pair = frozenset([rel, other])
                    if pair not in seen and pair not in KNOWN_SAFE_CYCLES:
                        seen.add(pair)
                        issues.append(Issue("HIGH", "circular",
                                            f"순환 의존: {rel.split('/')[-1]} ↔ {other.split('/')[-1]}"))
    return issues


# ──────────────────────────────────────────────────────────────────────────────
def print_report(issues: list[Issue]) -> None:
    by_check  = defaultdict(list)
    for iss in issues:
        by_check[iss.check].append(iss)

    n_crit = sum(1 for i in issues if i.level == "CRITICAL")
    n_high = sum(1 for i in issues if i.level == "HIGH")
    n_med  = sum(1 for i in issues if i.level == "MEDIUM")

    print(f"\n{'='*65}")
    print(f"  Preflight Nexus v2.0 — GitNexus 연결성·단절·영향 감사 (V612)")
    print(f"{'='*65}")
    print(f"  CRITICAL: {n_crit:>3}건   HIGH: {n_high:>3}건   MEDIUM: {n_med:>3}건")
    print()

    labels = [
        ("staleness",    "[1] .gitnexus 인덱스 상태"),
        ("survival",     "[2] Survival Matrix (핵심 심볼 생존)"),
        ("orphan",       "[3] Orphan 모듈 (단절 탐지)"),
        ("connectivity", "[4] 신규 모듈 연결성"),
        ("circular",     "[5] 순환 의존 (실질)"),
    ]
    ICONS = {"CRITICAL": "💀", "HIGH": "⚠", "MEDIUM": "ℹ", "INFO": "✅"}

    for key, label in labels:
        items = by_check.get(key, [])
        has_problem = any(i.level in ("CRITICAL", "HIGH") for i in items)
        prefix = "❌" if has_problem else ("⚠" if any(i.level == "MEDIUM" for i in items) else "✅")
        if not items:
            print(f"  ✅ {label} — 이상 없음")
        else:
            print(f"\n  {prefix} {label}")
            for iss in items:
                print(f"    {ICONS.get(iss.level,'?')} [{iss.level}] {iss.detail}")

    print()
    block = any(i.level in ("CRITICAL", "HIGH") for i in issues
                if i.check != "staleness")
    if not block:
        print("  ✅ PREFLIGHT NEXUS PASS — 개발 진행 허가")
    else:
        print("  ❌ PREFLIGHT NEXUS FAIL — 상기 항목 해소 후 재실행")
    print(f"{'='*65}\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--phase",  default=None,
                        help="Survival Matrix 레이어 필터 (예: sp_b3, core, nie)")
    args = parser.parse_args()

    issues: list[Issue] = []
    issues += check_staleness()
    issues += check_survival(args.phase)
    issues += check_orphans()
    issues += check_connectivity()
    issues += check_circular()

    print_report(issues)

    has_block = any(i.level in ("CRITICAL", "HIGH") for i in issues
                    if i.check != "staleness")
    return 1 if (args.strict and has_block) else 0


if __name__ == "__main__":
    sys.exit(main())
