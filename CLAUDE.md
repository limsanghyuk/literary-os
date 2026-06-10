# Literary OS — 개발자 컨텍스트 (V745 / v13.0.0)

---

## 🚨 [RULE-0] 버전 경계 자동 Preflight 강제 집행 (절대 불변 규칙)

> **이 규칙은 개발자가 별도로 지시하지 않아도 Claude가 자동으로 집행한다.**

### 규칙 본문

```
V(N) 개발 시작 전:
  → python3 tools/run_preflight.py 실행
  → PREFLIGHT PASS 확인 후에만 구현 착수
  → FAIL 시 원인 수정 후 재실행, PASS 확인 후 진행

V(N) 개발 완료 후, V(N+1) 시작 전:
  → python3 tools/run_preflight.py 재실행 (변경사항 반영 확인)
  → PREFLIGHT PASS + Release Gate PASS 확인
  → 그 이후에만 V(N+1) 구현 시작
```

### Claude 자동 집행 조건

| 발화 패턴 | Claude 행동 |
|-----------|-------------|
| "V731 진행해", "다음 버전 시작", "SP-D.4 시작" | Preflight 13단계 먼저 실행 → PASS 후 구현 |
| "732 해줘", "계속 진행", "이어서 개발" | 이전 버전 Preflight PASS 여부 확인 → 미확인 시 재실행 |
| 버전 번호가 포함된 모든 개발 지시 | 버전 경계 감지 → 자동 Preflight 트리거 |

### 위반 시 처리

- Preflight 미실행 상태에서 구현 코드 작성 **절대 금지**
- Release Gate FAIL 상태 커밋 **절대 금지**
- 위반 발생 시 즉시 중단하고 Preflight 실행 후 재시작

---

## 🔴 Phase D 절대 원칙 (불변)

| 원칙 | 내용 |
|------|------|
| **LLM-0** | `corpus/`, `constitution/`, `finetune/` 에서 외부 LLM 호출 절대 금지 |
| **LLM-1** | PROMOTED 단계 LoRA 아티팩트만 서빙 (AutoPromotionGate G62 통과 필수) |
| **DEV_MODE** | 항상 `false` 기본값 유지 (ADR-034) |
| **GPU SLO** | 재학습 최소 간격 7일, 월 최대 $200 (ADR-051) |
| **Gate FAIL** | Gate FAIL 상태 절대 커밋 금지 |
| **G_CONNECTIVITY** | 고립 패키지 2버전 연속 금지 (ADR-128) |
| **G32** | literary_system/ 내 print() 절대 금지 (sys.stdout.write 사용) |

---

## 현재 상태 (V745 기준)

| 항목 | 값 |
|------|----|
| 버전 | v13.0.0 |
| 개발 이터레이션 | V745 (Phase D 완전 종료 · Phase D Exit G95) |
| 릴리즈 게이트 | **97 등록** · Phase D Exit G95 8/8 PASS |
| 테스트 | **10,788 PASS** |
| 고립 패키지 | **0개** (85개 전체 연결, ADR-128) |
| Preflight 단계 | **13단계** (DEV_PROTOCOL_v3.0, RULE-0) |
| 최신 ADR | ADR-208 |
| 현재 Phase | Phase D 완전 종료 → **Phase E 기획 중** (검증 우선 · LLM-0→2.5) |
| 정본 진입 | docs/sessions/INDEX.md → MASTER_synthesis_priorities → home_handoff_v3 |
| GitHub | https://github.com/limsanghyuk/literary-os |

---

## 세션 시작 프로토콜 (매 세션 필수)

```bash
git pull origin main
python3 tools/run_preflight.py   # ← RULE-0 집행 시작점
```

> Preflight PASS 확인 후에만 개발 착수. 세션 시작 시 자동 실행.

---

## 개발 흐름 (DEV_PROTOCOL_v3.0 + RULE-0 통합)

```
[RULE-0] V(N) 시작 전 → python3 tools/run_preflight.py → PASS 확인
[1] 구현 (신규파일 + tests/unit/test_vNNN_*.py 33TC 이상)
[2] pytest → generate_test_inventory.py → run_release_gate.py (97 PASS)
[3] GitHub: commit → push → Release 태그 → ZIP 패키징
[RULE-0] V(N+1) 시작 전 → python3 tools/run_preflight.py 재실행 → PASS 확인
[4] V(N+1) 구현 시작
```

---

## SP-D.3 완료 현황 (V711~V730)

| 구성 | 버전 | Gate | 상태 |
|------|------|------|------|
| Plugin Registry | V711~V716 | G87 (PR-1~PR-7) | ✅ PASS |
| ZeroTrust Security | V717~V725 | G88 (ZT-1~ZT-7) | ✅ PASS |
| Auth Bridge | V721~V723 | — | ✅ PASS |
| Chaos Engineering | V724~V728 | — | ✅ PASS |
| G89 ChaosResilience | V729 | G89 (CR-1~CR-6) | ✅ PASS |
| SP-D.3 Exit Gate | V730 | E1~E6 | ✅ PASS |

## 다음 단계: SP-D.4 (V731~)

**SP-D.4 시작 발화**: "V731 시작해" / "SP-D.4 진행해" / "계속 개발해"  
→ Claude가 RULE-0에 따라 자동으로 Preflight 먼저 실행 후 V731 구현 착수.

---

## 주요 도구

| 도구 | 용도 |
|------|------|
| `python3 tools/run_preflight.py` | Preflight 13단계 자동 실행 (RULE-0 핵심, DEV_PROTOCOL_v3.0) |
| `python3 tools/run_release_gate.py` | G_PREFLIGHT + G_CONNECTIVITY + 97 Gates |
| `python3 tools/generate_test_inventory.py` | test_inventory.json 갱신 |
| `bash tools/install_hooks.sh` | 로컬 pre-commit hook 설치 (최초 1회) |

---

## 핵심 아키텍처

```
literary_system/
├── sdk/          # PublicSDK v1.0 (SP-C.3) — online 4종 실구현
├── ensemble/     # AgentCoordinator (Director→Script→Critic→Editor)
├── agents/       # MultiAgent Coordination (SP-D.2: Bus/Workflow/CB/Supervisor)
├── plugins/      # Plugin Registry + Sandbox + Lifecycle + Auth (SP-D.3)
├── security/     # ZeroTrust 4종 + PluginAuthAdapter (SP-D.3)
├── chaos/        # Chaos Engineering 5종: Engine/Injector/Scenario/CB/Runner (SP-D.3)
├── gates/        # 88 Release Gates (G01~G89 + SP-D3-EXIT)
├── ops/          # Observability: OtelSdkAdapter + TraceSampler + Dashboard (SP-D.1)
├── constitution/ # LOSConstitution v2 + Bayesian Opt
├── world/        # PluginRegistry + 5 genre plugins
├── governance/   # ATIAMetadataAuditor
└── ...           # 83개 패키지 전체 연결 (고립 0, ADR-128)
```

---

## Phase 전체 진행 현황

| Phase | 버전 | Gates | 상태 |
|-------|------|-------|------|
| Phase 6 (MultiWork) | V546~V571 | G25~G31 | ✅ 완료 |
| SP-A | V587~V595 | G46~G52 | ✅ 완료 |
| SP-B | V596~V630 | G53~G61 | ✅ 완료 |
| SP-C.1 자기학습 | V631~V640 | G62~G63 | ✅ 완료 |
| SP-C.2 멀티에이전트 | V641~V655 | G64~G67 | ✅ 완료 |
| SP-C.3 PublicSDK | V656~V665 | G68~G71 | ✅ 완료 |
| SP-C.4 경쟁흡수+배포 | V666~V680 | G72~G80 | ✅ 완료 |
| SP-D.1 Observability | V681~V695 | G81~G83 | ✅ 완료 |
| SP-D.2 MultiAgent Coord | V696~V710 | G84~G85 | ✅ 완료 |
| **SP-D.3 Plugin+ZT+Chaos** | **V711~V730** | **G87~G89** | **✅ 완료** |
| **SP-D.4** | **V731~** | **TBD** | **🔜 진입 대기** |

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **literary-os** (41586 symbols, 68256 relationships, 242 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/literary-os/context` | Codebase overview, check index freshness |
| `gitnexus://repo/literary-os/clusters` | All functional areas |
| `gitnexus://repo/literary-os/processes` | All execution flows |
| `gitnexus://repo/literary-os/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
