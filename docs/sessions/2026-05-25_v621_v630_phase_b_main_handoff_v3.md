# V621~V630 통합 본안 v3.0 핸드오프 — Sonnet 4.6 연산 모드용

**작성일**: 2026-05-25
**작성 모드**: 상위 연산 모드 (Opus)
**대상**: Sonnet 4.6 저연산 개발 모드
**기준선**: v10.25.2 (V620-AUDIT2) · 60 Gates PASS · 6,728+ Tests · G61 6축 PASS
**목표**: v11.0.0 (V630) · 60 Gates · 7,228+ Tests · G61 6+1축 PASS · **Phase B 완전 종료**

---

## 🔴 0. 필수 학습 (Critical Loading) — 작업 시작 전 강제

작업 시작 전 다음 5개 파일을 **반드시** 읽고 컨텍스트에 포함하라. 누락 시 절대 코드 작성 금지.

1. **`docs/sessions/2026-05-25_v621_v630_phase_b_main_handoff_v3.md`** ← 본 문서
2. **`docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.md`** ← V621~V630 설계도 (markdown 미러)
3. **`docs/audit/2026-05-25_phase_b_audit_report.docx`** ← Phase B 종료 감사
4. **`docs/sessions/literary_os_v621_v630_phase_b_proposal_v3.docx`** ← 인간 검토용
5. **`docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.docx`** ← 인간 검토용

docx 추출 명령:

```bash
python -c "
from docx import Document
d = Document('docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.docx')
for p in d.paragraphs:
    if p.text.strip(): print(p.text)
"
```

---

## 1. 본 핸드오프의 위치

V620까지 SP-B.4 약 35~40%만 완료된 상태(60 Gates PASS, G61 6축 PASS 도달이지만 본안 v2.0 V621~V630 잔여 6건 미완료). 본 V621~V630 통합 본안 v3.0은:

- 본안 v2.0 V621~V630 잔여 항목 + V620_R 보강 12건을 통합 재설계
- **V620_R은 supersedes됨** — outputs/v620_r_patch/ 산출물은 참조용 보존, push 안 함
- V630 = Phase B 진정한 종료 = v11.0.0 + G61 6+1축 PASS

---

## 2. V620 종료 시점 정확한 상태 (감사 결과)

| 본안 v2.0 V | 본안 항목 | 허브 실측 | 상태 |
|---|---|---|---|
| V621 | SystemIntegrationTest + Helm 사전 | E2E만 (Helm 사전 부재) | ▲ 부분 |
| V622 | PerformanceOptimizer + Metrics5Axis | V614 완료 | ✅ |
| V623 | 24h + biweekly 시뮬레이션 | LongRunMonitor만 | ▲ 부분 |
| V624 | 메모리 누수 검증 | V616 완료 | ✅ |
| V625 | biweekly_train.yml + Lambda 폴백 | 부재 | ❌ |
| V626 | TrainPlane Helm 검증 | chart만 (검증 워크플로우 없음) | ▲ |
| V627 | ServePlane Helm 검증 | **deploy/helm/serve_plane/ 부재** | ❌ |
| V628 | Grafana + Prometheus | **monitoring/ 디렉터리 전무** | ❌ |
| V629 | 운영 문서 + ATIA + Branch | **모두 부재** | ❌ |
| V630 | G61 6+1축 + v11.0.0 | G61 6축 + v10.25.2 | ▲ |

→ **약 35~40% 완료**. V621~V630에서 잔여 + V620_R 보강 12건을 통합 진행 필요.

---

## 3. V620_R → V621~V630 통합 매핑

| V620_R | 보강 | v3.0 V버전 흡수 |
|---|---|---|
| R0 | AGENTS.md 자동 학습 강제 | **V621-PRE** (사전 작업) |
| R1 | AgentEnvelope (P-IF-01) | **V621** SP-B.2 retrofit |
| R2 | ReaderFeedbackIngest (P-IF-03) | **V621** SP-B.2 retrofit |
| R3 | OpenAPI SemVer (P-IF-04) | **V621** SP-B.2 retrofit |
| R4 | G61 C7축 verify_interfaces_trace | **V630** G61 6+1축 |
| R5a | conflict_policy 5종 | **V622** SP-B.3 retrofit |
| R5b | workload_profile | **V622** SP-B.3 retrofit |
| R5c | adv_seeds 5종 | **V622** SP-B.3 retrofit (RewardModel) |
| R5d-1 | biweekly_train.yml | **V625** |
| R5d-2 | Branch Protection | **V629** |
| R6-1 | ATIA mini-audit | **V629** |
| R6-2 | v11.0.0 + Tests 7,000+ | **V630** |

---

## 4. V621~V630 진행 순서 (5주, 11 PATCH 묶음)

### V621-PRE — 자동 학습 강제 (사전 작업, 0.5일)

**목적**: V620_R 실패 원인(handoff .md.docx 오류 + AGENTS.md 학습 강제 부재) 재발 방지.

체크리스트:
- [ ] `AGENTS.md` 상단에 '🔴 필수 학습' 블록 추가:
  ```markdown
  1. docs/sessions/2026-05-25_v621_v630_phase_b_main_handoff_v3.md
  2. docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.md
  3. docs/audit/2026-05-25_phase_b_audit_report.docx
  ```
- [ ] `tools/preflight_step15.py`에 `verify_v3_handoff()` 추가
- [ ] +5 TC
- [ ] commit: `V621-PRE: 자동 학습 강제 (R0 흡수)`

---

### V621 — SP-B.2 retrofit (P-IF 3건, 1주)

**목적**: AgentEnvelope (P-IF-01) + ReaderFeedbackIngest (P-IF-03) + OpenAPI SemVer (P-IF-04) 3건 동시 부착.
**ADR**: ADR-088 + ADR-PC-IF 초안

체크리스트:
- [ ] `literary_system/llm_bridge/canonical_bridge_v2.py` 확장:
  - `AgentRole` Enum (SCENE_WRITER/CRITIC/EDITOR/HISTORIAN/READER_VOICE)
  - `AgentEnvelope` dataclass
  - `RoutingPolicy` 4축화 (+ `agent_routing: Dict`)
  - `CanonicalBridgeV2.generate()` 하위 호환 (str | AgentEnvelope)
- [ ] `literary_system/multiwork/reader_feedback_ingest.py` 신규:
  - `ReaderFeedback` frozen dataclass + `__post_init__` 검증
  - `RewardSignalAdapter` Protocol
  - `ReaderFeedbackIngest` — Phase B는 NotImplementedError
  - `is_phase_c_active()` 메소드
- [ ] `literary_system/serving/model_serving_endpoint.py` 확장:
  - `SEMVER_MAJOR/MINOR/PATCH` + `SEMVER` 상수
  - `/openapi.yaml` GET 엔드포인트
  - `/api_version` GET 엔드포인트
- [ ] `tools/detect_openapi_breaking.py` + `tools/export_openapi.py` 신규
- [ ] `.github/workflows/openapi_diff.yml` 신규 (warn-only 1주 → fail mode)
- [ ] ADR-088 작성 + ADR-PC-IF 초안 작성
- [ ] +60 TC + G56/G57 회귀 0건 검증
- [ ] commit: `V621: SP-B.2 retrofit P-IF 3건 (ADR-088, P-IF-01/03/04)`

코드 스켈레톤: blueprint_v3 §2 (또는 .md §2)

---

### V622 — SP-B.3 retrofit (3건, 1주)

**목적**: conflict_policy 5종 + workload_profile + adv_seeds 5종.
**ADR**: ADR-089

체크리스트:
- [ ] `shared_character_db_v2.py` 확장:
  - `ConflictPolicy` Enum (RENAME/MERGE/FORK/BLOCK/ESCALATE)
  - `ConflictPriority` (has_copyright_holder/appearance_count_neg/first_appearance_date)
  - `ResolutionResult` dataclass
  - `SharedCharacterDBV2.__init__` `default_policy=ESCALATE` 옵션
  - `SharedCharacterDBV2.resolve()` 메소드
- [ ] `multi_work_orchestrator_v2.py` 확장:
  - `WorkloadProfile` Enum (SINGLE/DUAL/TRIPLE)
  - `SLOByProfile` (3000/5000/8000ms)
  - `detect_profile()` + `slo_for_current()`
- [ ] `reward_model.py` 확장:
  - `AdvSeed` dataclass + `ADV_SEEDS_REQUIRED` 5종
  - `score_with_adv_seeds()` — 5건 차단 검증
- [ ] ADR-089 작성
- [ ] +60 TC + G58/G59 회귀 0건
- [ ] commit: `V622: SP-B.3 retrofit conflict+workload+adv_seeds (ADR-089)`

---

### V623 — SystemIntegrationTest + Helm 사전 검증 (3일)

**ADR**: ADR-090

체크리스트:
- [ ] `tests/integration/test_system_integration.py` 확장 (V621/V622 통합 E2E)
- [ ] Helm lint + dry-run 사전 검증 함수 (`helm lint deploy/helm/train_plane`)
- [ ] ADR-090 작성
- [ ] +30 TC
- [ ] commit: `V623: SystemIntegration + Helm 사전 검증 (ADR-090)`

---

### V624 — 24h 장기 시나리오 + 메모리 회귀 (3일)

**ADR**: ADR-091

체크리스트:
- [ ] `tests/integration/test_v624_24h_scenario.py` 신규 — LongRunMonitor + MemoryLeakDetector 통합
- [ ] `.github/workflows/long_run_24h.yml` (수동 트리거 + 매주 일요일 자정)
- [ ] 메모리 누수 baseline + 시간당 ≤10MB 성장 assertion
- [ ] ADR-091 작성
- [ ] +30 TC
- [ ] commit: `V624: 24h 시나리오 + 메모리 회귀 (ADR-091)`

---

### V625 — biweekly_train + Lambda 폴백 + 자동 복구 (1주)

**ADR**: ADR-092

체크리스트:
- [ ] `.github/workflows/biweekly_train.yml` 신규 (cron '0 17 1,15 * *' = 매월 1·15일 02:00 KST)
- [ ] `tools/check_runpod_availability.py` 신규
- [ ] `tools/notify_slack.py` 신규
- [ ] RunPod 부족 시 Lambda H100 자동 전환 + Slack 알림
- [ ] dry_run 모드 기본 + 실 학습은 운영자 수동
- [ ] ADR-092 작성
- [ ] +50 TC
- [ ] commit: `V625: biweekly_train + Lambda 폴백 (ADR-092)`

---

### V626 — TrainPlane Helm 검증 (3일)

**ADR**: ADR-093

체크리스트:
- [ ] `.github/workflows/helm_train_plane.yml`: helm lint + kubeval + dry-run
- [ ] `tests/test_v626_helm_train.py`
- [ ] ADR-093 작성
- [ ] +30 TC
- [ ] commit: `V626: TrainPlane Helm 검증 (ADR-093)`

---

### V627 — ServePlane Helm 신설 + 검증 (1주)

**ADR**: ADR-094

체크리스트:
- [ ] `deploy/helm/serve_plane/Chart.yaml` (appVersion: 10.25.2 → v11.0.0)
- [ ] `deploy/helm/serve_plane/templates/{deployment,ingress,service,configmap}.yaml`
- [ ] Ingress에 /generate + **/openapi.yaml** + /model_card + /api_version 모두 라우팅 (V621 retrofit 결과 노출)
- [ ] readinessProbe + livenessProbe (/health)
- [ ] `.github/workflows/helm_serve_plane.yml`
- [ ] `tests/test_v627_helm_serve.py`
- [ ] ADR-094 작성
- [ ] +50 TC
- [ ] commit: `V627: ServePlane Helm 신설 + 검증 (ADR-094)`

---

### V628 — Grafana + Prometheus dashboard (3일)

**ADR**: ADR-095

체크리스트:
- [ ] `monitoring/prometheus/scrape_config.yml` (model-serving + rlhf-monitor 대상)
- [ ] `monitoring/grafana/dashboards/cost_slo.json` (Daily GPU Cost / 월 SLO $120 / Cost per Scene)
- [ ] `monitoring/grafana/dashboards/krippendorff_alpha.json` (α by Cycle / drift >0.1 alert)
- [ ] `monitoring/grafana/dashboards/gpu_util.json` + `p95_latency.json`
- [ ] dashboard JSON schema 검증 테스트
- [ ] ADR-095 작성
- [ ] +30 TC
- [ ] commit: `V628: Grafana + Prometheus dashboard (ADR-095)`

---

### V629 — 운영 문서 (Diataxis 4) + ATIA mini-audit + Branch Protection (1주)

**ADR**: ADR-096

체크리스트:
- [ ] `docs/operations/tutorial/` 3 문서 (first LoRA training / RLHF cycle / MultiWork 3works)
- [ ] `docs/operations/how_to/` 3 문서 (add LoRA / debug KL / recover Canary)
- [ ] `docs/operations/reference/` 3 문서 (API v1.0.0 / LoRA 3-tag / adv_seeds 5종)
- [ ] `docs/operations/explanation/` 3 문서 (architecture / G61 6+1축 / P-IF traces)
- [ ] `tools/atia_mini_audit.py` 신규:
  - REQUIRED_ATIA_FIELDS 7건 (scene_id/work_id/created_at/sha256/source_corpus/license/pii_scrub_version)
  - 100건 무작위 + sha256 chain 재계산
- [ ] 실 감리 1회 실행 (`python tools/atia_mini_audit.py corpus/`) — 100/100 PASS 강제
- [ ] **GitHub Settings → Branches → Add rule for main** (UI 작업):
  - Required approving reviews: 1
  - Required status checks: ci/ruff, ci/pytest, ci/release_gate, openapi_diff, helm_train_plane, helm_serve_plane, atia_mini_audit
  - Require linear history: ON
  - Restrict push: limsanghyuk only
- [ ] `tests/test_branch_protect_status.py` (Branch Protection 상태 API 검증)
- [ ] ADR-096 작성
- [ ] +60 TC
- [ ] commit: `V629: 운영 문서 + ATIA + Branch Protection (ADR-096)`

---

### V630 — G61 6+1축 + v11.0.0 GitHub Release (3일)

**ADR**: ADR-097 (supersedes ADR-080)

체크리스트:
- [ ] `literary_system/gates/phase_b_exit_gate.py` 확장:
  - `P_IF_TRACE_REQUIRED` 5건 (V621 retrofit 결과 검증)
  - `verify_interfaces_trace()` 함수
  - `PhaseBExitGate.AXES` 6→7축 (C7 추가)
  - C6 임계 6,700 → 7,000 강화
  - `evaluate()` 메소드에 `C7_Interfaces_Trace` 체크
- [ ] `pyproject.toml` version `10.25.2` → `11.0.0` + description 갱신
- [ ] `README.md` badge 4종 갱신 (version/tests/gates/G61)
- [ ] `live_core_manifest.json` + `MANIFEST.md` 갱신
- [ ] `docs/changelog/CHANGELOG_V630.md` 작성 (v11.0.0)
- [ ] `docs/changelog/INDEX.md` 갱신
- [ ] ATIA mini-audit 100건 0 mismatch 최종 확인 (V629 결과 재실행)
- [ ] 최종 검증:
  ```bash
  pytest tests/ -q                              # 7,228+ PASS
  python literary_system/gates/release_gate.py  # 60/60 PASS
  python -c "from literary_system.gates.phase_b_exit_gate import PhaseBExitGate; ..."  # 6+1축 PASS
  ```
- [ ] ADR-097 작성 (ADR-080 supersedes 명시)
- [ ] commit: `V630: G61 6+1축 + v11.0.0 — Phase B Complete (ADR-097)`
- [ ] tag + release:
  ```bash
  git tag -a v11.0.0 -m "Phase B Complete — V630 (G61 6+1축)"
  git push origin v11.0.0
  gh release create v11.0.0 \
    --title "v11.0.0 — Phase B Complete (V630)" \
    --notes-file docs/changelog/CHANGELOG_V630.md
  ```
- [ ] 상위 연산 모드(Opus) 호출: "Phase C (V631~) 본안 v3.0 작성 요청"

---

## 5. 의존성 그래프

```
V621-PRE (사전, 0.5일)
  └→ V621 SP-B.2 retrofit (1주) ──────┐
       └→ V622 SP-B.3 retrofit (1주) ─┤
            └→ V623 E2E + Helm 사전 (3일)
                 └→ V624 24h + 메모리 (3일)
                      └→ V625 biweekly (1주)
                           ├→ V626 TrainPlane Helm (3일)
                           └→ V627 ServePlane Helm (1주)
                                └→ V628 dashboard (3일)
                                     └→ V629 운영문서+ATIA+Branch (1주)
                                          └→ V630 G61 6+1축 + v11.0.0 (3일)
                                               └→ Phase C 본안 v3.0 작성 트리거
```

병렬 가능: V623/V624 (다른 파일) / V626/V627 (다른 chart) / V627/V628 (다른 영역). 본 일정은 직렬 기준, 병렬 시 4주 단축 가능.

**필수 순차**: V621/V622 retrofit → V630 (C7 검증은 V621 표면 통과 후만 PASS).

---

## 6. Tests 누적 (V620 6,728 → V630 7,228+)

| V버전 | TC + |
|---|---|
| V621-PRE | +5 |
| V621 | +60 |
| V622 | +60 |
| V623 | +30 |
| V624 | +30 |
| V625 | +50 |
| V626 | +30 |
| V627 | +50 |
| V628 | +30 |
| V629 | +60 |
| V630 | +50 + 회귀 +45 |
| **누적** | **+500** |

V620 6,728 + 500 = **7,228+** (v11.0.0 기준).

---

## 7. ADR 11건 (ADR-088~097 + ADR-PC-IF)

| ADR | V버전 | 제목 |
|---|---|---|
| ADR-088 | V621 | SP-B.2 retrofit (AgentEnvelope + ReaderFeedbackIngest + OpenAPI SemVer) |
| ADR-089 | V622 | SP-B.3 retrofit (conflict_policy + workload_profile + adv_seeds) |
| ADR-090 | V623 | System Integration + Helm 사전 검증 정책 |
| ADR-091 | V624 | 24h 장기 시나리오 + 메모리 회귀 자동화 |
| ADR-092 | V625 | biweekly_train + Lambda 폴백 + 자동 복구 |
| ADR-093 | V626 | TrainPlane Helm 검증 정책 |
| ADR-094 | V627 | ServePlane Helm 신설 + 검증 정책 |
| ADR-095 | V628 | Grafana + Prometheus dashboard 표준 |
| ADR-096 | V629 | 운영 문서(Diataxis) + ATIA mini-audit + Branch Protection |
| ADR-097 | V630 | Phase B Exit Gate G61 6+1축 + v11.0.0 (supersedes ADR-080) |
| ADR-PC-IF | V621/V630 | Phase C/D 인터페이스 트레이스 통합 |

---

## 8. 위험 신호 — 상위 모드 호출 조건

- **PASS 6,728 → 6,720 미만 후퇴** (any V)
- **V621 retrofit이 V606 G56/G57 회귀 ≥1건** (가장 위험 — 기존 모듈 수정)
- **V622 conflict_policy retrofit이 SharedCharacterDBV2 기존 사용 코드 깨뜨림**
- **V625 biweekly_train.yml dry_run 5회 연속 실패**
- **V627 ServePlane Helm Ingress가 V605 ModelServing 라우팅 충돌**
- **V629 ATIA mini-audit 100건 중 sha256 mismatch ≥1건**
- **V629 Branch Protection 적용 후 PR 흐름 차단 (false positive)**
- **V630 verify_interfaces_trace() 실패** — V621 retrofit 중 누락
- **V630 Tests 7,000 미달 (-50 이상)**

위 신호 발견 시 즉시 작업 중단 + 상위 모드 호출.

---

## 9. 첫 명령 시퀀스 (Sonnet 4.6 즉시 실행 가능)

```bash
# 환경 확인
cd /path/to/literary-os
git pull origin main
git log --oneline -3   # f51d036 (V620-AUDIT2) 또는 그 이후 확인

# 필수 학습 파일 5종 존재 확인
ls docs/sessions/2026-05-25_v621_v630_phase_b_main_handoff_v3.md
ls docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.md
ls docs/audit/2026-05-25_phase_b_audit_report.docx
ls docs/sessions/literary_os_v621_v630_phase_b_proposal_v3.docx
ls docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.docx

# docx 추출 (필요 시)
python -c "
from docx import Document
d = Document('docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.docx')
for p in d.paragraphs:
    if p.text.strip(): print(p.text)
" | head -200

# 진입 전 점검
python tools/check_version_consistency.py     # v10.25.2 확인
pytest tests/ -q                              # 6,728+ PASS
python literary_system/gates/release_gate.py  # 60/60 PASS

# V621-PRE 진입
git checkout -b dev/v621-pre-handoff-load
# AGENTS.md 편집 (상단 '필수 학습' 블록 추가)
# tools/preflight_step15.py 편집 + 테스트 추가
pytest tests/unit/test_v3_handoff_verification.py -v
git add -A
git commit -m "V621-PRE: 자동 학습 강제 (R0 흡수)"
git push origin dev/v621-pre-handoff-load
# PR open, 머지

# V621 진입
git checkout main && git pull
git checkout -b dev/v621-sp-b2-retrofit
# canonical_bridge_v2.py + reader_feedback_ingest.py + model_serving_endpoint.py 작성
# (blueprint_v3.md §2 코드 스켈레톤 참조)
pytest tests/unit/test_v621_*.py -v           # 60 TC PASS
pytest tests/unit/test_v606_*.py -v           # G56/G57 회귀 0건
git add -A
git commit -m "V621: SP-B.2 retrofit P-IF 3건 (ADR-088, P-IF-01/03/04)"
git push origin dev/v621-sp-b2-retrofit

# ... V622 ~ V630 순차 진행 (위 체크리스트 참조)
```

---

## 10. V630 종료 후 Phase C 진입 준비

V630 종료 + v11.0.0 release 완료 후:

1. 메모리 업데이트: `project_v630_phase_b_complete.md` 신규 (이전 `project_v620_state.md` supersedes)
2. KoreanDrama-Suite-v1 (LoRA 8B+3B + RLHF + 5만 신 + 3작품 통합) HuggingFace 비공개 등록
3. 상위 연산 모드 호출 (Opus): "Phase C (V631~) 본안 v3.0 작성 요청. V630 완료 + P-IF-01~05 트레이스 활성 전제 (V621 retrofit 결과)"
4. 별도 세션에서 `docs/sessions/literary_os_v631_phase_c_blueprint_v3.docx` + `.md` 작성

---

## 11. 사용자가 GitHub에 push할 파일 (5개)

```bash
cd /path/to/literary-os

mkdir -p docs/audit
mkdir -p docs/sessions

# 5개 파일 복사 (outputs/v621_v630_v3/ + outputs/phase_b_v2/ → repo)
cp "<outputs>/v621_v630_v3/literary_os_v621_v630_phase_b_proposal_v3.docx" docs/sessions/
cp "<outputs>/v621_v630_v3/literary_os_v621_v630_phase_b_blueprint_v3.docx" docs/sessions/
cp "<outputs>/v621_v630_v3/literary_os_v621_v630_phase_b_blueprint_v3.md" docs/sessions/
cp "<outputs>/v621_v630_v3/2026-05-25_v621_v630_phase_b_main_handoff_v3.md" docs/sessions/
cp "<outputs>/phase_b_v2/2026-05-25_phase_b_audit_report.docx" docs/audit/

# 키 누설 검증 (필수)
git add docs/sessions/literary_os_v621_v630_phase_b_*.docx \
        docs/sessions/literary_os_v621_v630_phase_b_blueprint_v3.md \
        docs/sessions/2026-05-25_v621_v630_phase_b_main_handoff_v3.md \
        docs/audit/2026-05-25_phase_b_audit_report.docx

git diff --staged | grep -E "ghp_|sk-ant-|sk-proj-|AIza" || echo "✓ 키 누설 0건"

git commit -m "Add V621~V630 통합 본안 v3.0 — SP-B.4 완성 + V620_R 보강 통합 (5주, 11 versions)

배경:
- V620 종료 시점 SP-B.4 약 35~40%만 완료 (감사 결과)
- V620_R PATCH 시도는 V버전 통합으로 supersedes
- 본안 v2.0 V621~V630 잔여 6건 + V620_R 보강 12건 통합

V621~V630 진행 (11 PATCH):
- V621-PRE 자동 학습 강제 (R0 흡수)
- V621 SP-B.2 retrofit (P-IF 3건, ADR-088)
- V622 SP-B.3 retrofit (conflict+workload+adv, ADR-089)
- V623 E2E + Helm 사전 (ADR-090)
- V624 24h + 메모리 회귀 (ADR-091)
- V625 biweekly + Lambda 폴백 (ADR-092)
- V626 TrainPlane Helm 검증 (ADR-093)
- V627 ServePlane Helm 신설 (ADR-094)
- V628 Grafana + Prometheus (ADR-095)
- V629 운영문서 + ATIA + Branch Protection (ADR-096)
- V630 G61 6+1축 + v11.0.0 (ADR-097, supersedes ADR-080)

목표: v11.0.0 / 60 Gates / G61 6+1축 / 7,228+ Tests / Phase B 완전 종료"

git push origin main
```

---

## 12. 메타데이터

- **문서 ID**: LOS-V621-V630-HANDOFF-V3-2026-05-25
- **유효 기간**: V630 종료(v11.0.0)까지. Phase C 진입 시 별도 핸드오프
- **선행 문서**:
  - `2026-05-25_phase_b_audit_report.docx` (Phase B 종료 감사)
  - `literary_os_v601_v630_phase_b_blueprint_v2.docx` (본안 v2.0, commit f16c5c8)
- **supersedes**:
  - V620_R 산출물 4종 (outputs/v620_r_patch/, 참조용 보존, push 안 함)
  - `2026-05-22_v601_v630_phase_b_main_handoff_v2.md.docx` (잘못된 확장자, V621-PRE에서 git rm)
- **후속 문서**: `2026-XX-XX_v631_phase_c_handoff_v3.md` (V630 종료 후 발행)

---

## 13. v2.0 → V620_R → v3.0 진화 요약

| 영역 | v2.0 (commit f16c5c8) | V620_R (supersedes) | **v3.0 (본 문서)** |
|---|---|---|---|
| V버전 수 | V601~V630 (30v) | V620_R0~R6 PATCH | **V621-PRE + V621~V630 (11)** |
| SP-B.4 완료 시점 | V630 | (V620 시점 + R PATCH) | **V630** |
| G61 축 | 6+1축 | 6+1축 (R4) | **6+1축 (V630)** |
| AgentEnvelope | V610 사전 표면 (누락) | R1 PATCH | **V621 retrofit** |
| ReaderFeedbackIngest | V620 사전 표면 (누락) | R2 PATCH | **V621 retrofit** |
| OpenAPI SemVer | V605 사전 표면 (누락) | R3 PATCH | **V621 retrofit** |
| conflict_policy | V611 5종 (누락) | R5a PATCH | **V622 retrofit** |
| workload_profile | V613 1/2/3 SLO (누락) | R5b PATCH | **V622 retrofit** |
| adv_seeds | V606 5종 (누락) | R5c PATCH | **V622 retrofit** |
| biweekly_train | V625 YAML (누락) | R5d PATCH | **V625** |
| Branch Protection | V629 (누락) | R5d PATCH | **V629** |
| ATIA mini-audit | V629/매 SP (누락) | R6 PATCH | **V629** |
| v11.0.0 | V630 | R6 | **V630** |
| Tests | 7,000+ | 7,028+ | **7,228+** |

---

— V621~V630 통합 본안 v3.0 핸드오프 (Final) | Sonnet 4.6 작업 지시서 | 2026-05-25 —
