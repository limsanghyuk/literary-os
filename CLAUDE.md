# Literary OS — 개발자 컨텍스트 (V710 / v12.2.0)

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

아래 패턴의 사용자 발화를 인식하면 **즉시 Preflight를 먼저 실행**:

| 발화 패턴 | Claude 행동 |
|-----------|-------------|
| "V681 진행해", "다음 버전 시작", "Phase D 시작" | Preflight 13단계 먼저 실행 → PASS 후 구현 |
| "682 해줘", "계속 진행", "이어서 개발" | 이전 버전 Preflight PASS 여부 확인 → 미확인 시 재실행 |
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

---

## 현재 상태 (V710 기준)

| 항목 | 값 |
|------|----|
| 버전 | v12.0.2 |
| 개발 이터레이션 | V710 (SP-D.2 MultiAgent Coordination 완전 종료) |
| 릴리즈 게이트 | **84/84 PASS** |
| 테스트 | **9,700 PASS** |
| 고립 패키지 | **0개** (76패키지 전체 연결) |
| Preflight 단계 | **13단계** (Step 13: G_CONNECTIVITY) |
| 최신 ADR | ADR-142 (Phase C Exit Gate G79) |
| 현재 Phase | Phase C 완전 종료 → **Phase D 진입 대기** |
| Git HEAD (main) | 1a8beba1 (V710 SP-D.2 완료) |
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
[2] pytest → generate_test_inventory.py → run_release_gate.py (84/84 PASS)
[3] GitHub: commit → push → Release 태그 → ZIP 패키징
[RULE-0] V(N+1) 시작 전 → python3 tools/run_preflight.py 재실행 → PASS 확인
[4] V(N+1) 구현 시작
```

**Preflight 13단계 소요 시간**: 약 30~60초 (자동 실행, 개발자 개입 불필요)

---

## Phase D 로드맵 (V681~V745) — 본안 v1.0

| SubPhase | 버전 | 내용 | 비고 |
|----------|------|------|------|
| SP-D.1 | V681~V700 | 장편 품질 완성 (서사 일관성 / 캐릭터 깊이 / 감정 흐름) | |
| SP-D.2 | V701~V720 | 다국어 확장 (영어/일어/중국어) | |
| SP-D.3 | V721~V740 | 상용화 완성 (API SLA / 결제 / Enterprise 계약) | |
| SP-D.4 | V741~V745 | Phase D Exit Gate → v13.0.0 | |

**Phase D 시작 발화**: "V681 시작해" / "Phase D 진행해" / "계속 개발해"  
→ Claude가 RULE-0에 따라 자동으로 Preflight 먼저 실행 후 V681 구현 착수.

---

## 주요 도구

| 도구 | 용도 |
|------|------|
| `python3 tools/run_preflight.py` | Preflight 13단계 자동 실행 (RULE-0 핵심) |
| `python3 tools/run_release_gate.py` | G_PREFLIGHT + G_CONNECTIVITY + 80 Gates |
| `python3 tools/generate_test_inventory.py` | test_inventory.json 갱신 |
| `bash tools/install_hooks.sh` | 로컬 pre-commit hook 설치 (최초 1회) |

---

## 핵심 아키텍처

```
literary_system/
├── sdk/          # PublicSDK v1.0 (SP-C.3) — online 4종 실구현
├── ensemble/     # AgentCoordinator (Director→Script→Critic→Editor)
├── agents/       # 멀티에이전트 앙상블 (SP-C.2)
├── gates/        # 80 Release Gates + SafetyRegressionGate
├── constitution/ # LOSConstitution v2 + Bayesian Opt
├── world/        # PluginRegistry + 5 genre plugins
├── governance/   # ATIAMetadataAuditor
├── ops/          # AdaptiveThrottler + LongRunMonitor + PrometheusExporter
└── ...           # 76패키지 전체 연결 (고립 0, ADR-128)
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
| V666 Integration | V666 | ADR-128 | ✅ 완료 |
| SP-C.4 경쟁흡수+배포 | V667~V680 | G72~G79 | ✅ 완료 |
| V680-AUDIT2 | v12.0.2 | G80 | ✅ Phase C 완전 종료 |
| **Phase D** | **V681~V745** | **TBD** | 🔜 **진입 대기** |
