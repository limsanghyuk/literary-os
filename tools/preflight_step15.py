#!/usr/bin/env python3
"""
Preflight Step 15 — 보안·위생 + GitNexus 연결성·단절·영향 통합 CI 게이트 (V612)

[최고 수석 컴파일러 × 최고 수석 아키텍처 합의안 — 2026-05-23]
────────────────────────────────────────────────────────────────────────
문제 진단:
  V575 당시 Step 15는 보안 위생(Rule 1~3)만 담당했다.
  GitNexus 연결성 검사(Survival Matrix / Orphan / Circular)는 별도 수동 도구였기 때문에
  매 단계 개발 후 연결성 단절이 자동으로 감지되지 않았고, V596~V611 기간 동안
  110개 신규 파일이 인덱스에 미반영된 채 누적되었다.

합의 해결책:
  preflight_step15.py가 Rule 4~8(연결성)을 흡수하여 단일 종합 게이트가 된다.
  ci.yml의 `python tools/preflight_step15.py --strict` 실행만으로
  위생 + 연결성 전체를 블로킹 체크한다. 별도 도구 실행 의존 제거.

검사 규칙:
  ── 위생 (Hygiene) ──────────────────────────────────────────────────
  Rule-1 (CRITICAL): DEV_MODE 기본값 "true" 금지
  Rule-2 (HIGH):     literary_system/ 내 print() 사용 금지
  Rule-3 (MEDIUM):   bare except: 금지

  ── 연결성 (Connectivity) ────────────────────────────────────────────
  Rule-4 (HIGH):     .gitnexus 인덱스 staleness — 신규 파일 미반영 시 경고
  Rule-5 (CRITICAL): Survival Matrix — Phase별 핵심 심볼 생존 확인
  Rule-6 (HIGH):     Orphan 모듈 탐지 — literary_system/* 단절 모듈
  Rule-7 (HIGH):     신규 모듈 연결성 — SP-B.3 모듈이 신경망에 연결되어 있는가
  Rule-8 (HIGH):     순환 의존 탐지 — lazy-import 아닌 실질 순환

사용법:
    python tools/preflight_step15.py              # 보고서만 출력
    python tools/preflight_step15.py --strict     # 위반 발견 시 exit(1) [CI용]
    python tools/preflight_step15.py --hygiene-only   # Rule 1~3만
    python tools/preflight_step15.py --nexus-only     # Rule 4~8만
    python tools/preflight_step15.py --phase sp_b3    # Survival Matrix 레이어 필터
"""

from __future__ import annotations

import ast
import json
import re
import sys
import argparse
from collections import defaultdict
from pathlib import Path
from typing import NamedTuple

REPO_ROOT       = Path(__file__).resolve().parent.parent
SYSTEM_ROOT     = REPO_ROOT / "literary_system"
APPS_ROOT       = REPO_ROOT / "apps"
MIDDLEWARE_FILE = APPS_ROOT / "studio_api" / "auth" / "middleware.py"
GITNEXUS_META   = REPO_ROOT / ".gitnexus" / "meta.json"

SKIP = {"__pycache__", ".git", ".pytest_cache", "node_modules", "literary_os.egg-info"}

# ─── 결과 타입 ───────────────────────────────────────────────────────────────
class Violation(NamedTuple):
    rule:   str
    level:  str    # CRITICAL / HIGH / MEDIUM
    file:   str
    lineno: int
    detail: str


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION A — 위생 규칙 (Rule 1~3)
# ══════════════════════════════════════════════════════════════════════════════

def check_devmode_default() -> list[Violation]:
    """Rule-1: DEV_MODE 기본값이 'true'이면 인증 bypass 위험."""
    violations = []
    if not MIDDLEWARE_FILE.exists():
        return violations
    text = MIDDLEWARE_FILE.read_text(encoding="utf-8")
    for i, line in enumerate(text.splitlines(), 1):
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        if re.search(r'os\.environ\.get\(["\']LITERARY_OS_DEV_MODE["\'],\s*["\']true["\']', line):
            violations.append(Violation(
                rule="Rule-1", level="CRITICAL",
                file=str(MIDDLEWARE_FILE.relative_to(REPO_ROOT)),
                lineno=i,
                detail='DEV_MODE 기본값이 "true" — 인증 bypass 위험. "false"로 변경 필요.',
            ))
    return violations


def check_print_statements() -> list[Violation]:
    """Rule-2: literary_system/ 내 print() 사용 금지 (logging 사용 필수)."""
    violations = []
    for py_file in SYSTEM_ROOT.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        for i, line in enumerate(text.splitlines(), 1):
            stripped = line.lstrip()
            if stripped.startswith("#"):
                continue
            if re.match(r'\bprint\s*\(', stripped):
                violations.append(Violation(
                    rule="Rule-2", level="HIGH",
                    file=str(py_file.relative_to(REPO_ROOT)),
                    lineno=i,
                    detail="print() 발견 — logging.getLogger(__name__) 사용 필요.",
                ))
    return violations


def check_bare_excepts() -> list[Violation]:
    """Rule-3: bare except: 금지."""
    violations = []
    for py_file in SYSTEM_ROOT.rglob("*.py"):
        text = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text, filename=str(py_file))
        except SyntaxError:
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                violations.append(Violation(
                    rule="Rule-3", level="MEDIUM",
                    file=str(py_file.relative_to(REPO_ROOT)),
                    lineno=node.lineno,
                    detail="bare except: 발견 — except Exception: 또는 구체적 예외 명시 필요.",
                ))
    return violations


# ══════════════════════════════════════════════════════════════════════════════
#  SECTION B — 연결성 규칙 (Rule 4~8)
#  [최고 수석 컴파일러 × 최고 수석 아키텍처 합의 신설 V612]
# ══════════════════════════════════════════════════════════════════════════════

# Survival Matrix — V612 갱신 (실제 경로 46/46 검증 완료)
# 새 Phase/SP 추가 시 이 딕셔너리만 갱신. 각 레이어별 핵심 심볼 + 실제 경로.
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

# 알려진 레거시 단절 모듈 (V328~V400, SP-B.4 정리 대상)
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

# 알려진 정상 순환 (lazy import / TYPE_CHECKING 블록, 런타임 순환 아님)
KNOWN_SAFE_CYCLES = {
    frozenset(["literary_system/gates/gate_registry.py",
               "literary_system/gates/release_gate.py"]),
    frozenset(["literary_system/gates/phase_a_exit_gate.py",
               "literary_system/gates/release_gate.py"]),
    frozenset(["literary_system/multiwork/multi_work_cim.py",
               "literary_system/multiwork/multi_work_cim_v2.py"]),
}

# 연결성 검증 대상 (SP-B.3 신규 모듈 — 최소 1개 호출자 필요)
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


# 연결성 공용 헬퍼
def _collect_py_files() -> dict[str, Path]:
    files: dict[str, Path] = {}
    for f in sorted(REPO_ROOT.rglob("*.py")):
        if any(s in f.parts for s in SKIP):
            continue
        files[str(f.relative_to(REPO_ROOT))] = f
    return files


def _parse_imports(fpath: Path) -> set[str]:
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


def check_nexus_staleness() -> list[Violation]:
    """Rule-4: .gitnexus 인덱스가 현재 파일 목록과 일치하는가."""
    if not GITNEXUS_META.exists():
        return [Violation("Rule-4", "HIGH", ".gitnexus/meta.json", 0,
                          ".gitnexus/meta.json 없음 — `git-nexus index` 재실행 필요")]
    try:
        with open(GITNEXUS_META) as f:
            meta = json.load(f)
    except Exception as e:
        return [Violation("Rule-4", "HIGH", ".gitnexus/meta.json", 0,
                          f"meta.json 파싱 실패: {e}")]
    indexed = set(meta.get("fileHashes", {}).keys())
    current = set(_collect_py_files())
    new_cnt = len(current - indexed)
    commit  = meta.get("lastCommit", "?")[:8]
    if new_cnt:
        return [Violation("Rule-4", "HIGH", ".gitnexus/meta.json", 0,
                          f"인덱스 stale (commit {commit}) — 신규 파일 {new_cnt}개 미반영. "
                          f"`git-nexus index` 재실행 필요")]
    return []


def check_survival_matrix(phase_filter: str | None = None) -> list[Violation]:
    """Rule-5: Phase별 핵심 심볼이 살아있는가."""
    violations: list[Violation] = []
    layers = {k: v for k, v in SURVIVAL_MATRIX.items()
              if not phase_filter or phase_filter.lower() in k}
    for layer, symbols in layers.items():
        for cls, rel_path in symbols.items():
            full = REPO_ROOT / rel_path
            found = False
            if full.exists():
                for p in full.rglob("*.py"):
                    if any(s in p.parts for s in SKIP):
                        continue
                    try:
                        if f"class {cls}" in p.read_text(encoding="utf-8", errors="ignore"):
                            found = True
                            break
                    except Exception:
                        pass
            if not found:
                violations.append(Violation(
                    rule="Rule-5", level="CRITICAL",
                    file=rel_path, lineno=0,
                    detail=f"[{layer}] {cls} DEAD — 경로 {rel_path} 에서 클래스 미발견",
                ))
    return violations


def check_orphan_modules() -> list[Violation]:
    """Rule-6: literary_system/* 에서 아무도 import 하지 않는 단절 모듈 탐지."""
    py_files   = _collect_py_files()
    all_imports: set[str] = set()
    for fpath in py_files.values():
        all_imports.update(_parse_imports(fpath))

    ls_mods = [r for r in py_files
               if r.startswith("literary_system/") and not r.endswith("__init__.py")]

    violations: list[Violation] = []
    legacy_count = 0
    for rel in ls_mods:
        mod   = rel.replace("/", ".").replace(".py", "")
        short = mod.split(".")[-1]
        pkg   = ".".join(mod.split(".")[:-1])
        if mod in all_imports or short in all_imports or pkg in all_imports:
            continue
        if rel in KNOWN_LEGACY_ORPHANS:
            legacy_count += 1
            continue
        violations.append(Violation(
            rule="Rule-6", level="HIGH",
            file=rel, lineno=0,
            detail="신규 단절 모듈 — 아무도 import 하지 않음 (연결성 없음)",
        ))

    if legacy_count:
        violations.append(Violation(
            rule="Rule-6", level="MEDIUM",
            file="literary_system/schemas+retrieval+adapters", lineno=0,
            detail=f"레거시 단절 모듈 {legacy_count}개 (V328~V400) — SP-B.4에서 정리 권장",
        ))
    return violations


def check_module_connectivity() -> list[Violation]:
    """Rule-7: CONNECTIVITY_TARGETS 신규 모듈이 기존 신경망에 연결되어 있는가."""
    py_files     = _collect_py_files()
    file_imports = {r: _parse_imports(f) for r, f in py_files.items()}
    violations: list[Violation] = []

    for fpath, short in CONNECTIVITY_TARGETS.items():
        if fpath not in py_files:
            violations.append(Violation(
                rule="Rule-7", level="CRITICAL",
                file=fpath, lineno=0,
                detail="파일 없음 — CONNECTIVITY_TARGETS에 등록되었으나 실제 파일 미존재",
            ))
            continue
        callers = [r for r, imps in file_imports.items()
                   if r != fpath and any(short in i for i in imps)]
        if not callers:
            violations.append(Violation(
                rule="Rule-7", level="HIGH",
                file=fpath, lineno=0,
                detail=f"단절 위험: {fpath.split('/')[-1]} — 참조 모듈 0개 (신경망 미연결)",
            ))
    return violations


def check_circular_imports() -> list[Violation]:
    """Rule-8: literary_system 내 실질 순환 의존 (알려진 lazy-import 정상 순환 제외)."""
    py_files     = _collect_py_files()
    file_imports = {r: _parse_imports(f) for r, f in py_files.items()}
    ls_mods      = [r for r in py_files if r.startswith("literary_system/")]
    seen: set[frozenset] = set()
    violations: list[Violation] = []

    for rel in ls_mods:
        my_imps = file_imports.get(rel, set())
        for other in ls_mods:
            if other == rel:
                continue
            other_short = other.replace("/", ".").replace(".py", "").split(".")[-1]
            other_mod   = other.replace("/", ".").replace(".py", "")
            if not any(other_short in i or other_mod in i for i in my_imps):
                continue
            other_imps = file_imports.get(other, set())
            my_short   = rel.replace("/", ".").replace(".py", "").split(".")[-1]
            my_mod     = rel.replace("/", ".").replace(".py", "")
            if not any(my_short in i or my_mod in i for i in other_imps):
                continue
            pair = frozenset([rel, other])
            if pair in seen or pair in KNOWN_SAFE_CYCLES:
                continue
            seen.add(pair)
            violations.append(Violation(
                rule="Rule-8", level="HIGH",
                file=rel, lineno=0,
                detail=(f"순환 의존: {rel.split('/')[-1]} ↔ {other.split('/')[-1]} "
                        f"— KNOWN_SAFE_CYCLES에 등록하거나 lazy import로 해소 필요"),
            ))
    return violations


# ══════════════════════════════════════════════════════════════════════════════
#  보고서 출력
# ══════════════════════════════════════════════════════════════════════════════

def print_report(violations: list[Violation], hygiene_only: bool, nexus_only: bool) -> None:
    by_rule: dict[str, list[Violation]] = defaultdict(list)
    for v in violations:
        by_rule[v.rule].append(v)

    n_crit = sum(1 for v in violations if v.level == "CRITICAL")
    n_high = sum(1 for v in violations if v.level == "HIGH")
    n_med  = sum(1 for v in violations if v.level == "MEDIUM")

    print(f"\n{'='*72}")
    print("  Preflight Step 15 v2.0 — 보안·위생 + 연결성 종합 CI 게이트 (V612)")
    print(f"{'='*72}")
    print(f"  CRITICAL: {n_crit:>3}건   HIGH: {n_high:>3}건   MEDIUM: {n_med:>3}건   합계: {len(violations)}건")
    print()

    HYGIENE_RULES = {
        "Rule-1": ("CRITICAL", "DEV_MODE 기본값"),
        "Rule-2": ("HIGH",     "print() 사용"),
        "Rule-3": ("MEDIUM",   "bare except:"),
    }
    NEXUS_RULES = {
        "Rule-4": ("HIGH",     ".gitnexus staleness"),
        "Rule-5": ("CRITICAL", "Survival Matrix (핵심 심볼 생존)"),
        "Rule-6": ("HIGH",     "Orphan 모듈 (단절 탐지)"),
        "Rule-7": ("HIGH",     "신규 모듈 연결성"),
        "Rule-8": ("HIGH",     "순환 의존 (실질)"),
    }

    if not nexus_only:
        print("  ── 위생 (Hygiene) ──────────────────────────────────────────────────")
        for rule, (lvl, label) in HYGIENE_RULES.items():
            cnt   = len(by_rule.get(rule, []))
            icon  = "OK" if cnt == 0 else "NG"
            print(f"  [{icon}] {rule} ({lvl}) -- {label}: {cnt}건")
            for v in by_rule.get(rule, []):
                print(f"        {v.file}:{v.lineno}")
                print(f"        -> {v.detail}")

    if not hygiene_only:
        print()
        print("  ── 연결성 (Connectivity) ─────────────────────────────────────────────")
        for rule, (lvl, label) in NEXUS_RULES.items():
            items = by_rule.get(rule, [])
            cnt   = len(items)
            has_block = any(v.level in ("CRITICAL", "HIGH") for v in items)
            icon  = "OK" if cnt == 0 else "NG"
            print(f"  [{icon}] {rule} ({lvl}) -- {label}: {cnt}건")
            for v in items:
                sev = "[CRITICAL]" if v.level == "CRITICAL" else ("[HIGH]" if v.level == "HIGH" else "[MEDIUM]")
                print(f"        {sev} {v.file}")
                print(f"        -> {v.detail}")

    print()
    # Rule-4 (staleness)는 경고 전용
    block = any(v.level in ("CRITICAL", "HIGH") for v in violations
                if v.rule != "Rule-4")
    if not violations:
        print("  [PASS] PREFLIGHT STEP 15 ALL CLEAR -- 개발 진행 허가")
    elif block:
        print("  [FAIL] PREFLIGHT STEP 15 FAIL -- 상기 CRITICAL/HIGH 항목 해소 후 재실행")
    else:
        print("  [WARN] PREFLIGHT STEP 15 WARN -- MEDIUM 경고. 개발 진행 가능하나 정리 권장")
    print(f"{'='*72}\n")


# ══════════════════════════════════════════════════════════════════════════════
#  main
# ══════════════════════════════════════════════════════════════════════════════

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Preflight Step 15 v2.0 -- 보안·위생 + 연결성 종합 CI 게이트"
    )
    parser.add_argument("--strict",       action="store_true",
                        help="CRITICAL/HIGH 위반 발견 시 exit(1) -- CI 블로킹 모드")
    parser.add_argument("--hygiene-only", action="store_true",
                        help="Rule 1~3 (위생)만 실행")
    parser.add_argument("--nexus-only",   action="store_true",
                        help="Rule 4~8 (연결성)만 실행")
    parser.add_argument("--phase",        default=None,
                        help="Survival Matrix 레이어 필터 (예: sp_b3, core, nie)")
    args = parser.parse_args()

    violations: list[Violation] = []

    # Section A: 위생
    if not args.nexus_only:
        violations += check_devmode_default()
        violations += check_print_statements()
        violations += check_bare_excepts()

    # Section B: 연결성
    if not args.hygiene_only:
        violations += check_nexus_staleness()
        violations += check_survival_matrix(args.phase)
        violations += check_orphan_modules()
        violations += check_module_connectivity()
        violations += check_circular_imports()

    print_report(violations, args.hygiene_only, args.nexus_only)

    # Rule-4 (staleness)는 경고만 — CI 블로킹에서 제외 (gitnexus 미설치 환경 대응)
    has_block = any(v.level in ("CRITICAL", "HIGH") for v in violations
                    if v.rule != "Rule-4")
    if args.strict and has_block:
        print("Preflight Step 15 FAILED (--strict mode)")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
