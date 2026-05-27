# Literary OS — 개발자 컨텍스트 (V666 / v11.39.0)

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
| "V667 진행해", "다음 버전 시작", "SP-C.4 시작" | Preflight 13단계 먼저 실행 → PASS 후 구현 |
| "668 해줘", "계속 진행", "이어서 개발" | 이전 버전 Preflight PASS 여부 확인 → 미확인 시 재실행 |
| 버전 번호가 포함된 모든 개발 지시 | 버전 경계 감지 → 자동 Preflight 트리거 |

### 위반 시 처리

- Preflight 미실행 상태에서 구현 코드 작성 **절대 금지**
- Release Gate FAIL 상태 커밋 **절대 금지**
- 위반 발생 시 즉시 중단하고 Preflight 실행 후 재시작

---

## 🔴 Phase C 절대 원칙 (불변)

| 원칙 | 내용 |
|------|------|
| **LLM-0** | `corpus/`, `constitution/`, `finetune/` 에서 외부 LLM 호출 절대 금지 |
| **LLM-1** | PROMOTED 단계 LoRA 아티팩트만 서빙 (AutoPromotionGate G62 통과 필수) |
| **DEV_MODE** | 항상 `false` 기본값 유지 (ADR-034) |
| **GPU SLO** | 재학습 최소 간격 7일, 월 최대 $200 (ADR-051) |
| **Gate FAIL** | Gate FAIL 상태 절대 커밋 금지 |
| **G_CONNECTIVITY** | 고립 패키지 2버전 연속 금지 (ADR-128) |

---

## 현재 상태 (V666 기준)

| 항목 | 값 |
|------|----|
| 버전 | v11.39.0 |
| 개발 이터레이션 | V666 (Integration) |
| 릴리즈 게이트 | **66/66 PASS** |
| 테스트 | **8,418 PASS** |
| 고립 패키지 | **0개** (76패키지 전체 연결) |
| Preflight 단계 | **13단계** (Step 13: G_CONNECTIVITY) |
| 현재 Phase | Phase C SP-C.3 완료 → **SP-C.4 진입 대기** |
| Git HEAD (main) | b60f7507 |
| GitHub | https://github.com/limsanghyuk/literary-os |

---

## 세션 시작 프로토콜 (매 세션 필수)

```bash
git pull origin main
python3 tools/run_preflight.py   # ← RULE-0 집행 시작점
```

> Preflight PASS 확인 후에만 개발 착수. 세션 시작 시 자동 실행.

---

## 개발 흐름 (DEV_PROTOCOL_v2.0 + RULE-0 통합)

```
[RULE-0] V(N) 시작 전 → python3 tools/run_preflight.py → PASS 확인
[1] 구현 (신규파일 + tests/unit/test_vNNN_*.py 33TC 이상)
[2] pytest → generate_test_inventory.py → run_release_gate.py (66/66 PASS)
[3] GitHub: commit → push → Release 태그 → ZIP 패키징
[RULE-0] V(N+1) 시작 전 → python3 tools/run_preflight.py 재실행 → PASS 확인
[4] V(N+1) 구현 시작
```

**Preflight 13단계 소요 시간**: 약 30~60초 (자동 실행, 개발자 개입 불필요)

---

## SP-C.4 로드맵 (V667~V680)

| 버전 | 내용 | Gate |
|------|------|------|
| V667 | 경쟁 흡수: NovelAI 분석 | G72-1 |
| V668 | 경쟁 흡수: Sudowrite 분석 | G72-2 |
| V669 | 경쟁 흡수: Novelcrafter 분석 | G72-3 |
| V670 | 경쟁 흡수: NolanAI 분석 | G72-4 |
| V671 | 경쟁 흡수: Jenova 분석 + G72 통합 | G72 |
| V672 | DistillationExportPipeline v0.1 | ADR-095 |
| V673 | Enterprise SLO Gate | G73 |
| V674 | Revenue Gate | G74 |
| V680 | Phase C Exit Gate → v12.0.0 | G75 |

**SP-C.4 시작 발화**: "V667 시작해" / "SP-C.4 진행해" / "계속 개발해"  
→ Claude가 RULE-0에 따라 자동으로 Preflight 먼저 실행 후 V667 구현 착수.

---

## 주요 도구

| 도구 | 용도 |
|------|------|
| `python3 tools/run_preflight.py` | Preflight 13단계 자동 실행 (RULE-0 핵심) |
| `python3 tools/run_release_gate.py` | G_PREFLIGHT + G_CONNECTIVITY + 66 Gates |
| `python3 tools/generate_test_inventory.py` | test_inventory.json 갱신 |
| `bash tools/install_hooks.sh` | 로컬 pre-commit hook 설치 (최초 1회) |

---

## 핵심 아키텍처

```
literary_system/
├── sdk/          # PublicSDK (SP-C.3) — online 4종 실구현
├── ensemble/     # AgentCoordinator (Director→Script→Critic→Editor)
├── gates/        # 66 Release Gates + SafetyRegressionGate (V666)
├── constitution/ # LOSConstitution v2 + Bayesian Opt
├── world/        # PluginRegistry + 5 genre plugins (V666 통합)
├── governance/   # ATIAMetadataAuditor (V666 통합)
├── ops/          # AdaptiveThrottler + LongRunMonitor + APIReferenceGenerator (V666)
└── ...           # 76패키지 전체 연결 (고립 0, ADR-128)
```

---

## Phase C 전체 진행 현황

| SubPhase | 버전 | Gates | 상태 |
|----------|------|-------|------|
| SP-C.1 자기학습 | V631~V640 | G62~G63 | ✅ 완료 |
| SP-C.2 멀티에이전트 | V641~V655 | G64~G67 | ✅ 완료 |
| SP-C.3 PublicSDK | V656~V665 | G68~G71 | ✅ 완료 |
| V666 Integration | V666 | ADR-128 | ✅ 완료 |
| **SP-C.4 경쟁흡수+배포** | **V667~V680** | **G72~G75** | 🔜 진입 대기 |
