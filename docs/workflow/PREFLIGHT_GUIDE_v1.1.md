# Claude-Native GitNexus Development Preflight Guide

**문서 번호**: LOS-PREFLIGHT-CLAUDE-001  
**작성일**: 2026년 5월 15일  
**버전**: 1.1 (V463 갱신 — DualSemanticScorer 경로 수정, Gate17 반영)  
**적용 대상**: V430 수정 로드맵 및 이후 모든 Literary OS 개발 단계  
**기반 문서**: GitNexus_Development_Preflight_Guide.md (GPT 방식), 개발전에 반드시 확인 사항.docx

> **v1.0 → v1.1 변경 이력**  
> - §5 `CRITICAL_SYMBOLS`: `DualSemanticScorer` 경로 `literary_system/scoring/` → `literary_system/drse/` 수정 (False Alarm 방지)  
> - §5 `CRITICAL_SYMBOLS`: `AdapterContractV2`, `CascadeOrchestrator` (V431~V436 SubPhase1 핵심 심볼) 추가  
> - §5 `CRITICAL_GATES`: Gate 17 (`_gate_subphase1_adapter_survival`) 추가  
> - Release Gate 기준: 14/14 → **15/15 PASS** (V463)

---

## 서문: GPT 방식과 Claude 방식의 차이

GPT는 GitNexus MCP/CLI 도구를 직접 호출하여 코드 그래프를 탐색한다.  
Claude는 **Read / Write / Edit / Grep / Glob / Bash / Agent** 도구 세트로 동일한 목적을 달성한다.

이 문서는 GitNexus Preflight의 **철학과 검증 목적은 100% 계승**하되,  
Claude가 실제로 실행 가능한 구체적 절차로 재해석한 공식 지침서다.

> 핵심 원칙은 동일하다.  
> 새 로직은 테스트 통과만으로 충분하지 않다.  
> 기존 로직의 신경망 연결성을 끊지 않아야 한다.  
> Gate와 Manifest가 새 로직을 인식해야만 다음 단계로 진행한다.

---

## 1. GitNexus 구조와 Claude 도구 매핑

### 1.1 GPT의 7개 주요 도구 → Claude 등가 절차

| GitNexus 도구 | 목적 | Claude 등가 절차 |
|---|---|---|
| `list_repos` | 인덱스된 저장소 확인 | `Glob("**/__init__.py")` + `Bash("ls -la")` 로 모듈 트리 파악 |
| `query` | 심볼 / 프로세스 탐색 | `Grep(pattern, glob)` 으로 심볼·함수명·클래스명 전체 검색 |
| `context` | 심볼의 360도 맥락 | `Read` 해당 파일 + `Grep` incoming 참조자 + `Grep` outgoing import |
| `impact` | 변경 blast radius 계산 | `Bash("python scripts/impact_check.py <symbol>")` — depth 1/2/3 |
| `detect_changes` | 변경이 테스트·경로에 미치는 영향 | `Grep` 테스트 파일에서 변경 심볼 참조 확인 + `Bash("pytest --collect-only -q")` |
| `cypher` | 그래프 DB raw query | `Bash("python scripts/import_graph.py <module>")` Python 의존성 그래프 |
| `rename` | 다중 파일 rename/refactor | `Edit(replace_all=True)` — 반드시 impact 분석 **후** 마지막에 수행 |

### 1.2 GPT의 16개 핵심 보조 로직 → Claude 등가 절차

| 보조 로직 | 목적 | Claude 등가 절차 |
|---|---|---|
| `index_status` | 인덱스 상태 확인 | 최근 `Read` 이력 확인 + `Bash("find . -newer LAST_RUN -name '*.py'")` |
| `stale_index_detector` | 오래된 인덱스 탐지 | `Bash("git diff --name-only HEAD~1")` 변경 파일 목록 확인 |
| `probe` | 도구 가용성 점검 | `Bash("python -c 'import literary_system; print(literary_system.__file__)'")` |
| `result_normalizer` | 분석 결과 정규화 | Bash 출력을 TodoList 항목으로 정형화하여 기록 |
| `python_fallback` | GitNexus 미설치 시 최소 분석 | `Bash("python scripts/preflight_check.py")` — 아래 §6 참조 |
| `route_map` | 도구 사용 순서 결정 | **이 문서의 §3 Preflight 12단계를 고정 순서로 사용** |
| `tool_map` | 도구-기능 대응 정의 | 위 §1.1 표를 참조 |
| `shape_check` | 그래프 결과 schema 검증 | `Bash("python -m pytest tests/ -k 'gate' --tb=short -q")` Gate 통과 확인 |
| `survival_matrix` | 과거 핵심 로직 생존 확인 | `Bash("python scripts/survival_matrix.py")` — 아래 §5 참조 |
| `concept_impact` | 개념 중심 영향 분석 | provider-zero·Gate 조건·LLM-0 원칙 관련 심볼 `Grep` |
| `change_review` | 위험 변경 분류 | Gate 테스트 실행 후 실패 항목을 release block 여부 판단 |
| `skill_generator` | 인덱스를 개발용 skill로 변환 | Memory 파일 업데이트 (`project_*.md`) |
| `wiki_generator` | 구조를 문서화 | `C:\claude\개발 문서\` 에 설계도/제안서 작성 |
| `symbol_to_branchpoint_trace` | 신규 심볼의 Gate 연결 확인 | `Grep` 신규 심볼을 Gate 파일에서 검색 |
| `branchpoint_survival` | 기존 Gate 생존 여부 판정 | `Bash("python tools/run_release_gate.py")` 전체 Gate 통과 확인 |
| `release_gate_integration` | pass / block 최종 판단 | Release Gate N/N PASS = 진행 허가, 1개라도 FAIL = 블록 |

---

## 2. 핵심 철학 (GPT 방식 100% 계승)

```
GitNexus = 코드 / 심볼 / 파일 / 테스트 영향 분석 sidecar
GraphNexus = CodeGraph + NarrativeGraph + StageLineageGraph
BranchpointLogicGraph = 핵심 분기점 로직 생존 판정 장치
Release Gate = 최종 pass / block 결정 장치
```

Claude 환경에서의 대응:

```
Claude Grep/Glob = 코드·심볼·파일 탐색 계층
Claude Bash + pytest = 테스트 영향 분석 계층
Release Gate (run_release_gate.py) = 최종 pass/block 결정 장치
Survival Matrix Script = BranchpointLogicGraph 등가
```

**변하지 않는 원칙 3가지**:

1. 새 로직은 단순히 테스트를 통과하는 것만으로 충분하지 않다
2. 새 로직은 기존 로직의 신경망 연결성을 끊지 않아야 한다
3. Gate와 Manifest가 새 로직을 인식해야만 다음 단계로 진행한다

---

## 3. Claude Preflight 12단계 프로토콜 (고정 순서)

새 Stage 또는 새 수정 작업 시작 전 **반드시 이 순서대로** 실행한다.

### Step 1. 코드베이스 현황 파악 (index_status 등가)

```bash
# 최근 변경 파일 확인
git -C /path/to/repo diff --name-only HEAD~3

# Python 파일 총 수 확인
find . -name "*.py" | wc -l

# 모듈 트리 최상위 확인
ls -la literary_system/
```

**확인 목표**: 작업 대상이 현재 코드베이스와 일치하는가

---

### Step 2. 대상 모듈 범위 확인 (list_repos 등가)

```python
# Glob 도구 사용
Glob("literary_system/**/__init__.py")
Glob("tests/**/test_*.py")
```

**확인 목표**: 작업 대상 디렉토리 구조와 테스트 파일 목록 파악

---

### Step 3. 변경 예정 심볼 탐색 (query 등가)

```python
# 변경 예정 클래스/함수를 전체 코드베이스에서 검색
Grep(pattern="class TargetClass", glob="**/*.py")
Grep(pattern="from module.path import", glob="**/*.py")
```

**확인 목표**: 변경 예정 심볼이 어디서 참조되는가

---

### Step 4. 핵심 심볼 360도 맥락 확인 (context 등가)

```python
# 해당 파일 읽기
Read("literary_system/target_module.py")

# incoming 참조자 확인 (누가 이 심볼을 import하는가)
Grep(pattern="import TargetClass", glob="**/*.py")
Grep(pattern="from target_module", glob="**/*.py")

# outgoing 의존성 확인 (이 심볼이 무엇에 의존하는가)
# 파일 상단 import 구문 확인
```

**확인 목표**: 변경이 영향을 미치는 전체 연결망 파악

---

### Step 5. 영향 범위 계산 (impact depth 1/2/3 등가)

```bash
# depth 1: 직접 참조자
grep -r "TargetClass" literary_system/ --include="*.py" -l

# depth 2: 참조자의 참조자
# depth 1 결과 파일들을 다시 grep

# depth 3: 테스트까지 추적
grep -r "TargetClass" tests/ --include="*.py" -l
```

**확인 목표**: 변경의 blast radius가 예상 범위 내인가

---

### Step 6. 테스트 영향 분석 (detect_changes 등가)

```bash
# 변경 대상 심볼을 참조하는 테스트 파일 확인
grep -r "TargetClass\|target_function" tests/ --include="test_*.py" -l

# 영향받는 테스트만 선택 실행
python -m pytest tests/test_target.py -v --tb=short
```

**확인 목표**: 변경 전 영향받는 테스트가 현재 PASS 상태인가

---

### Step 7. 핵심 개념 영향 분석 (concept_impact 등가)

Literary OS의 불변 개념들에 대해 반드시 확인한다:

```python
# provider-zero: TaskRouter 내 LLM 호출 없음
Grep(pattern="def route", glob="**/task_router.py")
Grep(pattern=".generate(", glob="**/task_router.py")  # 있으면 위반

# LLM-0 원칙: Gate 10 적용 심볼
Grep(pattern="LLMAdapterContractGate", glob="**/*.py")

# Gate 연결성: 새 모듈이 Gate에 연결되어 있는가
Grep(pattern="def _gate_", glob="**/release_gate.py")

# 버전 선언 일관성
Grep(pattern="version", glob="**/release_gate.py")
Grep(pattern="version", glob="**/pyproject.toml")
```

**확인 목표**: 불변 개념이 새 변경으로 훼손되지 않는가

---

### Step 8. 생존 매트릭스 확인 (survival_matrix 등가)

이전 버전에서 확립된 핵심 로직이 현재 코드베이스에 살아있는지 확인한다:

```python
# V410 핵심 로직 생존 확인
Grep(pattern="class DualSemanticScorer", glob="**/*.py")
Grep(pattern="class NarrativePhysicsSnapshotEngine", glob="**/*.py")
Grep(pattern="class EnduranceLearningBridge", glob="**/*.py")
Grep(pattern="class NarrativeMemoryStore", glob="**/*.py")
Grep(pattern="class NarrativeConductor", glob="**/*.py")

# V411 핵심 로직 생존 확인
Grep(pattern="class UnifiedLLMGateway", glob="**/*.py")
Grep(pattern="class TaskRouter", glob="**/*.py")
Grep(pattern="class NKGCurator", glob="**/*.py")
Grep(pattern="class LLMAdapterContractGate", glob="**/*.py")
```

**확인 목표**: 과거 핵심 branchpoint 로직이 orphan node가 되지 않았는가

---

### Step 9. 신규 로직의 Gate 연결 확인 (symbol_to_branchpoint_trace 등가)

```python
# 신규 모듈이 release_gate.py에 등록되어 있는가
Read("literary_system/gates/release_gate.py")

# 신규 Gate 함수가 GATES 목록에 포함되어 있는가
Grep(pattern="GATES", glob="**/release_gate.py")

# 신규 모듈에 테스트 파일이 존재하는가
Glob("tests/**/test_new_module*.py")
```

**확인 목표**: 새 로직이 Gate 체계와 테스트 체계에 연결되어 있는가

---

### Step 10. 결과 schema 검증 (shape_check 등가)

```bash
# Gate 테스트만 선택 실행
python -m pytest tests/ -k "gate" -v --tb=short

# compile 검증
python -m compileall literary_system/ -q

# import 검증
python -c "from literary_system.gates.release_gate import run_all_gates; print('OK')"
```

**확인 목표**: 분석 결과가 Gate 실행 가능한 상태인가

---

### Step 11. 위험 변경 분류 (change_review 등가)

다음 표로 변경 유형을 분류한다:

| 위험도 | 변경 유형 | 처리 방식 |
|---|---|---|
| 🔴 High | Gate 파일 수정, release_gate.py 수정, LLMBridgeInterface 수정 | Step 1~10 전부 재실행 후 진행 |
| 🟡 Medium | 기존 모듈에 새 메서드 추가, 새 어댑터 추가 | Step 7~10 확인 후 진행 |
| 🟢 Low | 테스트 파일 수정, 독립 유틸리티 추가, 문서 수정 | Step 10만 확인 후 진행 |

---

### Step 12. Release Gate 최종 판단 (release_gate_integration 등가)

```bash
# 전체 Release Gate 실행
python tools/run_release_gate.py

# 전체 테스트 실행
python -m pytest tests/ -q --tb=short 2>&1 | tail -5
```

**판단 기준**:
- Gate N/N PASS + 테스트 회귀 없음 → **진행 허가**
- Gate 1개라도 FAIL → **Release Block — 원인 해소 후 재실행**
- 신규 테스트 FAIL → **Release Block — 테스트 수정 또는 구현 수정**

---

## 4. V430 수정 로드맵 전용 Preflight 체크리스트

V430의 6개 우선순위 수정 전 다음 항목을 확인한다.

### 수정 전 공통 확인

```python
# 현재 release gate 버전 확인
Grep(pattern='version.*=.*"V', glob="**/release_gate.py")

# 현재 pyproject.toml 버전 확인
Grep(pattern="^version", glob="**/pyproject.toml")

# 현재 README 버전 언급 확인
Grep(pattern="V4[0-9][0-9]", glob="**/README*.md")

# 절대경로 테스트 존재 확인
Grep(pattern="/sessions/", glob="tests/**/*.py")

# pytest cache 파일 존재 확인
Bash("find . -name '.pytest_cache' -type d")
```

### 수정별 사전 영향 분석

**우선순위 1 — 버전 단일 소스화**:
```python
# 버전을 참조하는 모든 파일 확인
Grep(pattern="V3[0-9][0-9]|V4[0-9][0-9]", glob="**/*.py", output_mode="files_with_matches")
Grep(pattern="V3[0-9][0-9]|V4[0-9][0-9]", glob="**/*.md", output_mode="files_with_matches")
Grep(pattern="V3[0-9][0-9]|V4[0-9][0-9]", glob="**/*.toml", output_mode="files_with_matches")
```

**우선순위 2 — Gate 9 (Studio API Gate) 설계**:
```python
# Studio API 계층 구조 파악
Glob("apps/studio_api/**/*.py")

# 기존 Gate 함수 패턴 확인
Read("literary_system/gates/release_gate.py")

# Gate 9 예비 슬롯 확인
Grep(pattern="Gate 9|gate_9|예비", glob="**/*.py")
```

**우선순위 3 — CostLedger 비용 계산 완성**:
```python
# CostLedger 현재 구현 확인
Read("literary_system/llm_bridge/cost_ledger.py")

# estimated_cost_usd 사용처 확인
Grep(pattern="estimated_cost_usd", glob="**/*.py")

# V412 이월 주석 확인
Grep(pattern="V412", glob="**/*.py")
```

**우선순위 4 — 절대경로 테스트 수정**:
```python
# 절대경로 테스트 전체 목록
Grep(pattern="/sessions/|/home/|/Users/", glob="tests/**/*.py", output_mode="files_with_matches")

# Path.cwd() 또는 Path(__file__) 사용 패턴 확인 (참고용)
Grep(pattern="Path\(__file__\)|Path\.cwd\(\)", glob="tests/**/*.py")
```

**우선순위 5 — OTel 테스트 조건부 skip**:
```python
# OTel 관련 테스트 파일 확인
Grep(pattern="opentelemetry|_OTEL", glob="tests/**/*.py", output_mode="files_with_matches")

# 현재 requirements 파일 확인
Glob("requirements*.txt")
```

**우선순위 6 — clean ZIP 재패키징**:
```bash
# pytest cache 파일 확인
find . -name "*.pytest_cache*" -o -name ".pytest_cache" | head -20

# __pycache__ 확인
find . -name "__pycache__" -type d | wc -l

# 현재 패키징 스크립트 확인
ls tools/packaging* scripts/pack* 2>/dev/null
```

---

## 5. Survival Matrix 스크립트 (Python Fallback)

GitNexus가 없을 때 Claude가 실행하는 최소 생존 매트릭스 검증 스크립트.  
개발 전 `Bash`로 실행하거나 인라인으로 확인한다.

> **⚠️ 경로 주의 (v1.1 수정)**: `DualSemanticScorer` 는 `literary_system/scoring/` 에 없다.  
> 실제 위치는 `literary_system/drse/drse_engine.py` 이다. 이전 가이드의 경로는 오기였다.

```python
#!/usr/bin/env python3
"""
Literary OS Survival Matrix — Claude-Native Python Fallback
GitNexus 미설치 환경에서 핵심 로직 생존 여부 확인
버전: v1.1 (V463) — DualSemanticScorer 경로 수정 + SubPhase1 심볼 추가
"""
import os, ast, sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# 반드시 생존해야 하는 핵심 심볼 목록
CRITICAL_SYMBOLS = {
    # V410 계보
    "DualSemanticScorer":            "literary_system/drse/",         # ← 수정: scoring/ → drse/
    "NarrativePhysicsSnapshotEngine":"literary_system/physics/",
    "EnduranceLearningBridge":       "literary_system/learning/",
    "NarrativeMemoryStore":          "literary_system/memory/",
    "NarrativeConductor":            "literary_system/orchestrators/",
    # V411 추가
    "LLMContext":                    "literary_system/llm_bridge/",
    "OpenAICompatibleAdapter":       "literary_system/llm_bridge/",
    "TaskRouter":                    "literary_system/llm_bridge/routing/",
    "ProviderHealthMonitor":         "literary_system/llm_bridge/health/",
    "UnifiedLLMGateway":             "literary_system/llm_bridge/gateway/",
    "NKGCurator":                    "literary_system/nkg/",
    "CostLedger":                    "literary_system/llm_bridge/",
    "LLMAdapterContractGate":        "literary_system/gates/",
    # V431~V436 SubPhase1 추가
    "AdapterContractV2":             "literary_system/llm_bridge/",
    "CascadeOrchestrator":           "literary_system/llm_bridge/",
}

# 반드시 생존해야 하는 Gate 함수 목록
CRITICAL_GATES = [
    "_gate_drse_quality",
    "_gate_physics_snapshot",
    "_gate_endurance_bridge",
    "_gate_memory_store",
    "_gate_conductor_integration",
    "_gate_nkg_connectivity",
    "_gate_pipeline_survival",
    "_gate_llm_adapter_contract",
    "_gate_subphase1_adapter_survival",   # V463 신설 Gate 17
]

def check_symbol_survival():
    results = {}
    for symbol, search_path in CRITICAL_SYMBOLS.items():
        full_path = REPO_ROOT / search_path
        found = False
        if full_path.exists():
            for py_file in full_path.rglob("*.py"):
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                if f"class {symbol}" in content:
                    found = True
                    break
        results[symbol] = found
    return results

def check_gate_survival():
    gate_file = REPO_ROOT / "literary_system/gates/release_gate.py"
    if not gate_file.exists():
        return {g: False for g in CRITICAL_GATES}
    content = gate_file.read_text(encoding="utf-8", errors="ignore")
    return {g: g in content for g in CRITICAL_GATES}

def check_concept_integrity():
    """provider-zero, LLM-0, Gate 연결성 개념 검증"""
    task_router = REPO_ROOT / "literary_system/llm_bridge/routing/task_router.py"
    issues = []
    if task_router.exists():
        content = task_router.read_text(encoding="utf-8", errors="ignore")
        if ".generate(" in content and "def route" in content:
            issues.append("⚠️  LLM-0 위반 가능성: TaskRouter.route()에 .generate() 호출 감지")
    return issues

if __name__ == "__main__":
    print("=" * 60)
    print("Literary OS Survival Matrix — Claude-Native Preflight")
    print("버전: v1.1 (V463) — Gate 15/15 기준")
    print("=" * 60)

    symbol_results = check_symbol_survival()
    gate_results = check_gate_survival()
    concept_issues = check_concept_integrity()

    print("\n[핵심 심볼 생존 여부]")
    all_symbols_alive = True
    for sym, alive in symbol_results.items():
        status = "✓ ALIVE" if alive else "✗ DEAD (orphan)"
        print(f"  {status:<20} {sym}")
        if not alive:
            all_symbols_alive = False

    print("\n[Gate 함수 생존 여부]")
    all_gates_alive = True
    for gate, alive in gate_results.items():
        status = "✓ ALIVE" if alive else "✗ DEAD (broken gate edge)"
        print(f"  {status:<20} {gate}")
        if not alive:
            all_gates_alive = False

    print("\n[개념 무결성 검사]")
    if concept_issues:
        for issue in concept_issues:
            print(f"  {issue}")
    else:
        print("  ✓ 이상 없음")

    print("\n[최종 판정]")
    if all_symbols_alive and all_gates_alive and not concept_issues:
        print("  ✓ PREFLIGHT PASS — 개발 진행 허가")
        sys.exit(0)
    else:
        print("  ✗ PREFLIGHT FAIL — 아래 항목 해소 후 재실행")
        if not all_symbols_alive:
            print("    → Orphan critical node 존재")
        if not all_gates_alive:
            print("    → Broken gate edge 존재")
        if concept_issues:
            print("    → 개념 무결성 위반")
        sys.exit(1)
```

---

## 6. Release Block 조건 (GPT 방식 완전 계승)

다음 중 하나라도 발생하면 **즉시 Release Block** 처리한다.

| # | Block 조건 | Claude 감지 방법 |
|---|---|---|
| 1 | Orphan critical node 발생 | Survival Matrix FAIL |
| 2 | Broken gate edge 발생 | `run_release_gate.py` FAIL |
| 3 | 신규 critical source에 테스트 없음 | `Glob("tests/**/test_new_module*.py")` 빈 결과 |
| 4 | 신규 critical source에 Manifest 없음 | Gate 등록 누락 |
| 5 | Branchpoint lineage 단절 | Step 8 생존 매트릭스 FAIL |
| 6 | LLM-0 위반 (TaskRouter에 generate() 호출) | Concept integrity check FAIL |
| 7 | Gate가 새 로직을 인식하지 못함 | Gate N/N 에서 N 미갱신 |
| 8 | Repo doctor가 active stage를 미인식 | README / pyproject version 불일치 |
| 9 | ZIP 내부 절대경로 포함 | `Grep("/sessions/", "tests/**/*.py")` |
| 10 | Cache 파일이 clean ZIP에 포함 | `find . -name "__pycache__"` 존재 |
| 11 | 버전 선언이 3개 이상 파일에서 불일치 | Step 7 버전 일관성 검사 FAIL |
| 12 | CostLedger가 항상 0.0 반환 (미완성 상태) | V412 이월 표시 확인 — 스텁임을 명시 |

---

## 7. Claude 개발 전 지시문 (표준 형식)

새 Stage 또는 수정 작업 시작 시 **이 지시문을 내부 점검 기준으로 고정**한다.

```
개발 전 Claude-Native GitNexus Preflight Protocol을 수행한다.

1. Grep/Glob으로 변경 대상 심볼의 전체 참조 연결망을 파악한다.
2. Survival Matrix로 과거 핵심 로직(V410~V411)이 살아있음을 확인한다.
3. 변경 예정 항목의 위험도를 분류하고 (High/Medium/Low) 해당 단계를 실행한다.
4. provider-zero·LLM-0·Gate 연결성 개념이 훼손되지 않음을 확인한다.
5. 구현 완료 후 run_release_gate.py를 실행하여 N/N PASS를 확인한다.
6. Gate FAIL 또는 Orphan node 발생 시 Release Block으로 처리하고 원인을 해소한다.
7. 버전 선언은 pyproject.toml 단일 소스 기준으로 일관성을 유지한다.

새 로직이 테스트를 통과하더라도 Gate 체계에 연결되지 않으면 완성이 아니다.
```

---

## 8. V430 수정 로드맵 실행 순서 (Preflight 적용)

각 수정 착수 전 §3의 12단계 중 해당 위험도 구간을 실행한다.

| 우선순위 | 수정 항목 | 위험도 | 실행 단계 |
|---|---|---|---|
| 1 | pyproject.toml 단일 버전 소스화 | 🔴 High | Step 1~12 전부 |
| 2 | Studio API Gate 11 설계 (Gate 9 채움) | 🔴 High | Step 1~12 전부 |
| 3 | CostLedger 비용 계산 완성 | 🟡 Medium | Step 3~12 |
| 4 | 절대경로 테스트 수정 | 🟢 Low | Step 6, 10, 12 |
| 5 | OTel 테스트 조건부 skip | 🟢 Low | Step 6, 10, 12 |
| 6 | clean ZIP 재패키징 | 🟢 Low | Step 10, 12 |

---

## 9. 최종 요약

```
Claude-Native GitNexus Preflight =
  Grep/Glob (탐색 계층)
  + Bash/pytest (분석·검증 계층)
  + Survival Matrix Script (생존 판정 계층)
  + run_release_gate.py (최종 pass/block 계층)
```

**현재 기준선 (V463)**: Release Gate **15/15 PASS**

**모든 Literary OS 개발은 이 Preflight를 통과한 후에만 시작한다.**

---

*본 문서는 GPT의 GitNexus Development Preflight Guide를 Claude 도구 체계로 재해석한 공식 지침서이다.  
Literary OS V430 수정 로드맵 및 이후 모든 단계에 적용한다.*
