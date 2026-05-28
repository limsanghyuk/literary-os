# Literary OS 개발 통합 프로토콜 v3.0

**버전**: 3.0  
**최초 제정**: 2026-05-28 (v3.0)  
**이전 버전**: DEV_PROTOCOL_v2.0 (v2.1까지) + PREFLIGHT_GUIDE_v1.1 → 본 문서에 완전 흡수  
**적용 대상**: Phase D V711 이후 **모든** 개발 이터레이션 (절대 필수)  
**권위 선언**: 이 문서가 유일한 개발 프로세스 권위 문서다. PREFLIGHT_GUIDE_v1.1은 폐기됨.

---

## 문서 목적과 철학 (PREFLIGHT_GUIDE 철학 계승)

이 프로토콜은 GPT의 GitNexus Development Preflight Guide 철학을 Claude 도구 체계로 구현한 것이다.

```
GitNexus의 핵심 원칙 (버전과 무관하게 영구 불변):

  1. 새 로직은 테스트 통과만으로 충분하지 않다.
  2. 새 로직은 기존 로직의 신경망 연결성을 끊지 않아야 한다.
  3. Gate와 Manifest가 새 로직을 인식해야만 다음 단계로 진행한다.
```

**버전이 올라가도 이 원칙은 바뀌지 않는다.** V636에서 적용된 원칙은 V710에서도, V1000에서도 동일하게 적용된다.

이 문서가 만들어진 이유:
- DEV_PROTOCOL v2.0: "run_preflight.py를 실행하라"만 명시, 철학·수동절차 미포함
- PREFLIGHT_GUIDE v1.1: 철학·12단계 수동절차 포함, 그러나 V463 시대 심볼로 극도로 낡음
- 두 문서가 병렬 존재 → 회사 환경에서 어떤 문서가 권위인지 불명확

**v3.0은 두 문서를 완전히 통합하여 단일 권위 문서로 기능한다.**

---

## 🚨 [RULE-0] 버전 경계 자동 Preflight 강제 집행 (절대 불변)

> **개발자가 별도로 지시하지 않아도, Claude(AI 개발 에이전트)가 자동으로 집행한다.**
> CLAUDE.md에 동일 규칙이 선언되어 있으며, 두 문서가 서로를 강제한다.

```
V(N) 개발 시작 전:
  필수 → python3 tools/run_preflight.py
  조건 → PREFLIGHT PASS 확인 후에만 구현 착수
  위반 → 구현 코드 작성 즉시 중단, Preflight 실행 후 재시작

V(N) 개발 완료 후, V(N+1) 시작 전:
  필수 → python3 tools/run_preflight.py 재실행 (변경사항 반영)
  조건 → PREFLIGHT PASS + Release Gate PASS 동시 확인
  위반 → V(N+1) 구현 착수 금지
```

### 자동 집행 조건

| 발화 패턴 | Claude 행동 |
|-----------|-------------|
| "V711 진행해", "다음 버전 시작" | Preflight 13단계 먼저 실행 → PASS 후 구현 |
| "712 해줘", "계속 개발", "이어서" | 이전 버전 Preflight PASS 여부 확인 → 미확인 시 재실행 |
| "SP-D.3 시작" 등 Phase/SP 단위 지시 | 해당 Sub-Phase 첫 버전 Preflight 먼저 실행 |
| 버전 번호 포함 모든 개발 지시 | 버전 경계 감지 → 자동 Preflight 트리거 |

### 이 규칙이 존재하는 이유

- V631~V636: DEV_PROTOCOL_v2.0이 있었으나 Preflight를 건너뜀 → SP-C.1 전체에서 연결성 검사 누락 → V666에서 고립 패키지 10개 발견
- V696~V710 (SP-D.2): Preflight를 SP-D.2 진입 시 1회만 실행, 각 버전 전 미실행 → V708 통합 테스트에서 API 불일치 7종 한꺼번에 발생
- **해결**: RULE-0을 CLAUDE.md + 이 문서 양쪽에 박아 상호 강제

---

## 전체 개발 흐름

```
┌────────────────────────────────────────────────────────────┐
│  [RULE-0] V(N) 시작 전 — 자동 집행                        │
│      python3 tools/run_preflight.py → PASS 확인            │
├────────────────────────────────────────────────────────────┤
│  [0] 세션 시작 — GitHub clone & 최신 상태 확인             │
├────────────────────────────────────────────────────────────┤
│  [1~13] PREFLIGHT 13단계 실행 (§1 참조)                    │
│      python3 tools/run_preflight.py (자동화)               │
│      또는 §1의 수동 절차 (자동화 불가 환경)                │
├────────────────────────────────────────────────────────────┤
│  [구현] §2 개발 표준 준수                                  │
│      신규 파일 → 테스트(33 TC) → __init__ 공개             │
├────────────────────────────────────────────────────────────┤
│  [검증] §3                                                 │
│      pytest → generate_test_inventory → run_release_gate   │
├────────────────────────────────────────────────────────────┤
│  [배포] §4 — commit → push → Release 태그                  │
├────────────────────────────────────────────────────────────┤
│  [패키징] §5 — ZIP + 7/7 검증 + 이전 버전 비교            │
├────────────────────────────────────────────────────────────┤
│  [메모리] §6 — project_state.md + MEMORY.md 갱신           │
├────────────────────────────────────────────────────────────┤
│  [RULE-0] V(N+1) 시작 전 — 자동 집행                      │
│      python3 tools/run_preflight.py 재실행 → PASS 확인     │
└────────────────────────────────────────────────────────────┘
```

---

## §1. PREFLIGHT 13단계

### 자동 실행 (권장)

```bash
python3 tools/run_preflight.py
# 소요 시간: 약 30~60초
# 로그: docs/sessions/preflight_v{VERSION}_{DATE}.md
```

### 수동 절차 (자동화 불가 환경 또는 스크립트 실패 시)

#### Step 1. 코드베이스 현황 파악

```bash
git diff --name-only HEAD~3      # 최근 변경 파일
find . -name "*.py" | wc -l      # Python 파일 수
ls -la literary_system/          # 모듈 트리
```

#### Step 2. 대상 모듈 범위 확인

```bash
ls literary_system/
find tests/ -name "test_*.py" | wc -l
```

#### Step 3. 변경 예정 심볼 탐색

```bash
grep -r "class TargetClass" --include="*.py" -l
grep -r "from module.path import" --include="*.py" -l
```

#### Step 4. 핵심 심볼 360도 맥락 확인

```bash
grep -r "import TargetClass" --include="*.py" -l     # incoming
head -30 literary_system/target_module.py             # outgoing
```

#### Step 5. 영향 범위 계산 (depth 1/2/3)

```bash
grep -r "TargetClass" literary_system/ --include="*.py" -l   # depth 1
grep -r "TargetClass" tests/ --include="*.py" -l              # depth 3
```

#### Step 6. 테스트 영향 분석

```bash
grep -r "TargetClass" tests/ --include="test_*.py" -l
python3 -m pytest tests/test_target.py -v --tb=short
```

#### Step 7. 핵심 개념 무결성

```bash
# LLM-0
grep -r "openai\|anthropic.messages" literary_system/corpus/ literary_system/constitution/ literary_system/finetune/ --include="*.py"
# G32
grep -rn "^[[:space:]]*print(" literary_system/ --include="*.py"
# DEV_MODE
grep -r "DEV_MODE = True" literary_system/ --include="*.py"
# 버전 일관성
grep "^version" pyproject.toml
```

#### Step 8. Survival Matrix — 핵심 심볼 생존 확인

**현재 기준 (V710 / SP-D.2 완료)**:

```bash
# Phase A/B
grep -r "class UnifiedLLMGateway" literary_system/ --include="*.py"
grep -r "class TaskRouter"         literary_system/ --include="*.py"
grep -r "class NKGCurator"         literary_system/ --include="*.py"
grep -r "class LOSDBClient"        literary_system/ --include="*.py"
# SP-C.1
grep -r "class LOSConstitutionV2"         literary_system/ --include="*.py"
grep -r "class ConstitutionWeightTracker" literary_system/ --include="*.py"
grep -r "class RetrainingScheduler"       literary_system/ --include="*.py"
# SP-C.2
grep -r "class DirectorAgent"    literary_system/ --include="*.py"
grep -r "class AgentCoordinator" literary_system/ --include="*.py"
# SP-C.3
grep -r "class LiteraryOSClient"       literary_system/ --include="*.py"
grep -r "class ReaderFeedbackCollector" literary_system/ --include="*.py"
# SP-D.1 Observability
grep -r "class OtelSdkAdapter"        literary_system/ --include="*.py"
grep -r "class TraceSampler"          literary_system/ --include="*.py"
grep -r "class ObservabilityDashboard" literary_system/ --include="*.py"
# SP-D.2 MultiAgent Coordination
grep -r "class AgentBus"            literary_system/ --include="*.py"
grep -r "class AgentWorkflow"       literary_system/ --include="*.py"
grep -r "class AgentCircuitBreaker" literary_system/ --include="*.py"
grep -r "class AgentSupervisor"     literary_system/ --include="*.py"
```

> **갱신 규칙**: 새 Sub-Phase 완료 시 이 목록과 `tools/run_preflight.py`의  
> `SURVIVAL_SYMBOLS` dict를 반드시 동시에 갱신한다.

#### Step 9. 신규 로직 Gate 연결 확인

```bash
grep "NewClass\|NewGate" literary_system/gates/release_gate.py
ls tests/unit/test_vXXX_*.py
```

#### Step 10. Schema 검증

```bash
python3 -m compileall literary_system/ -q
python3 -c "from literary_system.gates.release_gate import run_release_gate; print('OK')"
python3 -m pytest tests/ -k "gate" --tb=short -q
```

#### Step 11. 위험 변경 분류

| 위험도 | 변경 유형 | 처리 방식 |
|--------|-----------|-----------|
| 🔴 High | release_gate.py 수정, Gate 추가/삭제 | Step 1~13 전부 |
| 🟡 Medium | 기존 모듈에 메서드 추가 | Step 7~13 |
| 🟢 Low | 독립 신규 모듈, 테스트, 문서 | Step 10, 11, 13 |

#### Step 12. Release Gate 최종 판단

```bash
python3 tools/run_release_gate.py
python3 -m pytest tests/ -q --tb=short 2>&1 | tail -5
```

- Gate N/N PASS + 회귀 없음 → **진행 허가**
- 1개라도 FAIL → **Release Block**

#### Step 13. 패키지 연결성 검사 (ADR-128 G_CONNECTIVITY)

```bash
python3 -c "
import re
from pathlib import Path
from collections import defaultdict
root = Path('literary_system')
pkgs = {d.name for d in root.iterdir() if d.is_dir() and not d.name.startswith('_')}
imported_by = defaultdict(set)
deps = defaultdict(set)
for pkg in pkgs:
    for f in (root/pkg).rglob('*.py'):
        try: src = f.read_text(encoding='utf-8', errors='ignore')
        except: continue
        for m in re.finditer(r'from literary_system\.(\w+)', src):
            t = m.group(1)
            if t in pkgs and t != pkg:
                deps[pkg].add(t)
                imported_by[t].add(pkg)
isolated = [p for p in pkgs if not imported_by.get(p) and not deps.get(p)]
print('고립:', isolated if isolated else '없음 (PASS)')
"
```

---

## §2. Release Block 조건

| # | Block 조건 |
|---|------------|
| 1 | Survival Matrix FAIL (Orphan critical node) |
| 2 | run_release_gate.py FAIL |
| 3 | 신규 모듈에 테스트 없음 |
| 4 | 신규 모듈에 Gate 등록 누락 |
| 5 | LLM-0 위반 |
| 6 | G32 위반 (literary_system/ 내 print()) |
| 7 | DEV_MODE=True 잔류 |
| 8 | 버전 선언 불일치 |
| 9 | ADR-128 위반 (2버전 연속 고립 패키지) |
| 10 | Gate FAIL 상태 커밋 |

---

## §3. 구현 표준

### 버전 명명
| 항목 | 규칙 |
|------|------|
| 버전 번호 | `vMAJOR.MINOR.PATCH` (pyproject.toml 단일 소스) |
| V번호 | 개발 이터레이션 번호 |
| CHANGELOG | `docs/changelog/CHANGELOG_VXXX.md` |

### 테스트 표준
- 파일명: `tests/unit/test_vXXX_[기능명].py`
- TC 수: **최소 33개** (TC01~TC33)
- LLM-0: 테스트 내 외부 LLM 호출 절대 금지

### Phase D 절대 원칙 (불변)

| 원칙 | 내용 |
|------|------|
| **LLM-0** | corpus/, constitution/, finetune/ 에서 외부 LLM 호출 절대 금지 |
| **LLM-1** | PROMOTED 단계 모델만 서빙 |
| **DEV_MODE** | 항상 false 기본값 유지 (ADR-034) |
| **GPU SLO** | 재학습 최소 7일, 월 최대 $200 (ADR-051) |
| **G_CONNECTIVITY** | 고립 패키지 2버전 연속 금지 (ADR-128) |
| **G32** | literary_system/ 내 print() 절대 금지 (sys.stdout.write 사용) |

---

## §4. 검증

```bash
python3 -m pytest tests/ -q --tb=short 2>&1 | tail -5
python3 tools/generate_test_inventory.py
python3 tools/run_release_gate.py
```

## §5. GitHub 배포

```bash
git add -A
git commit -m "V{N}: [핵심 변경 1줄] (ADR-XXX, v{SEMVER})"
git push origin main
git tag v{SEMVER} && git push origin v{SEMVER}
```

## §6. ZIP 패키징

```bash
zip -r literary-os-vXXX.zip . --exclude ".git/*" --exclude "*/__pycache__/*" --exclude "*.pyc" -q
# 7/7 검증: 파일수≥1200, .gitignore, .github/≥4, .git없음, __pycache__없음, pyproject.toml, tests/≥100
```

## §7. 메모리 업데이트

```
[ ] memory/project_vXXX_state.md 작성
[ ] memory/MEMORY.md 인덱스 갱신
[ ] 이전 버전 항목에 ※구버전 표시
```

---

## §8. SURVIVAL_SYMBOLS 갱신 규칙

`tools/run_preflight.py`의 `SURVIVAL_SYMBOLS` dict와 §1 Step 8의 심볼 목록은  
**반드시 동기화**되어야 한다. 새 Sub-Phase 완료 시 양쪽을 동시에 갱신한다.

**현재 기준 (V710 / SP-D.2 완료)**:

| 계층 | 심볼 | 위치 |
|------|------|------|
| Phase A/B | UnifiedLLMGateway, TaskRouter, NKGCurator, LOSDBClient | llm_bridge/, nkg/, db/ |
| SP-C.1 | LOSConstitutionV2, ConstitutionWeightTracker, RetrainingScheduler | constitution/ |
| SP-C.2 | DirectorAgent, AgentCoordinator | agents/, ensemble/ |
| SP-C.3 | LiteraryOSClient, ReaderFeedbackCollector | sdk/, feedback/ |
| SP-D.1 | OtelSdkAdapter, TraceSampler, ObservabilityDashboard | ops/ |
| SP-D.2 | AgentBus, AgentWorkflow, AgentCircuitBreaker, AgentSupervisor | agents/ |

---

## §9. 버전 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|-----------|
| v1.0 | 2026-05-15 | PREFLIGHT_GUIDE_v1.1 최초 제정 (V463, 12단계) |
| v2.0 | 2026-05-26 | DEV_PROTOCOL_v2.0 — Preflight 필수화 |
| v2.1 | 2026-05-27 | RULE-0 추가 — 버전 경계 자동 Preflight 강제 집행 |
| **v3.0** | **2026-05-28** | **PREFLIGHT_GUIDE_v1.1 완전 흡수. 심볼 V710 기준 갱신. 12→13단계 통일. 단일 권위 문서 선언.** |
