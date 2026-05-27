# Phase D 본안 통합 핸드오프 v1.0 — 저연산 모드 단일 학습용

**작성일**: 2026-05-27
**기준선**: V680-AUDIT2 main HEAD `1ce229af` (v12.0.2, 80 Gates, 8,845 TC)
**선행 초안**: `literary_os_phaseD_proposal.docx` + `_blueprint.docx` (2026-05-27 Draft v1.0, 로컬 허브)
**본안 산출물 (본 push)**:
- `docs/sessions/literary_os_v681_phase_d_proposal_v1.docx` (3인 합의 본안 v1.0)
- `docs/sessions/literary_os_v681_phase_d_blueprint_v1.docx` (시스템 설계도 v1.0)
- `docs/sessions/2026-05-27_v681_phase_d_handoff_v1.md` (본 문서)

---

## ⚠️ 본 문서가 유일한 학습 대상이다

저연산 모드(Sonnet 4.6)는 다음 3개 파일만 학습하면 SP-D.1 V681부터 SP-D.4 V745까지 65 versions를 진행 가능:

1. `literary_os_v681_phase_d_proposal_v1.docx` (본안 합의)
2. `literary_os_v681_phase_d_blueprint_v1.docx` (시스템 설계도 + 코드 스켈레톤)
3. `2026-05-27_v681_phase_d_handoff_v1.md` (본 문서)

**Archive (참조 보존)**: 로컬 `C:\literary_claude\literary_os_phaseD_{proposal,blueprint}.docx` (Draft v1.0). 본안 v1.0이 모두 흡수.

---

## 1. V680-AUDIT2 GitNexus 인덱스 결과

| 축 | 값 |
|---|---|
| main HEAD | `1ce229af` (v12.0.2, V680-AUDIT2) |
| literary_system 모듈 | 571 |
| literary_system 심볼 | 6,215 |
| tests 모듈 | 333 |
| test_fn | 9,061 |
| Phase D 신규 26 모듈 경로 충돌 | **0건** |
| TD-1~3 실 코드 위치 | 확인 (benchmark.py:130 / revenue.py:103-107 / cost_control.py:74) |
| `phase_c_exit_gate.py` 별도 파일 | **❌ 누락 (D-M-13)** |
| Phase B/C 자산 | ✅ agents/, ensemble/, constitution/, finetune/ 모두 존재 |
| 가이드 | ✅ PREFLIGHT_GUIDE_v1.1 + DEV_PROTOCOL_v2.0 + PACKAGING_PROTOCOL_v1.0 |

---

## 2. Phase D 구조 (V681~V745, 65v, 4 SP)

| SP | V범위 | Gate | ADR | TC | 버전 |
|---|---|---|---|---|---|
| SP-D.1 | V681~V695 (15v) | G81~G83 | 143~155 | +300 → 9,145 | v12.1.0 |
| SP-D.2 | V696~V715 (20v) | G84~G86 | 156~175 | +700 → 9,845 | v12.2.0 |
| SP-D.3 | V716~V730 (15v) | G87~G89 | 176~190 | +600 → 10,445 | v12.3.0 |
| SP-D.4 | V731~V745 (15v) | G90~G95 | 191~210 | +1,055 → 11,500+ | v13.0.0 |

---

## 3. 본안 보강 13건 (D-M-01 ~ D-M-13)

### Architect (4건)
- D-M-01: Health Probe 2종 (liveness/readiness) — V702
- D-M-02: W3C TraceContext propagator 강제 — V688
- D-M-03: PluginLoader RestrictedPython 옵션 — V717
- D-M-04: API Gateway Envoy 호환 헤더 표준 — V705

### Compiler (4건)
- D-M-05: OpenAPI→Pydantic 자동 생성 (`datamodel-code-generator`) — V703
- D-M-06: CI 4단 분리 (unit≤5m / integration≤30m / perf≤1h / chaos nightly) — V685
- D-M-07: 의존성 잠금 (poetry 또는 uv) — V685
- D-M-08: pre-commit 4종 (mypy + bandit + ruff + black) — V687

### Principal (5건)
- D-M-09: **TD-1 P99 정정** — 초안 '최솟값 편향' → 실제 '최댓값 편향'. `statistics.quantiles` 도입 — V681
- D-M-10: 호환성 매트릭스 (9,061 test_fn 분산 모드 동일 결과) — V702 G84
- D-M-11: **G91 Disaster Recovery Gate 신설** (백업/복원 RPO ≤ 1h) — V741~V743
- D-M-12: Phase E KEDA + ArgoCD manifest 사전 정의 — V740
- D-M-13: **phase_c_exit_gate.py 신설** (V681-PRE) — Phase C Exit 정합 wrapper

---

## 4. 저연산 모드 작업 순서

### 4.1 V681-PRE — 필수 선결 작업 (D-M-13)

```bash
cd /path/to/literary-os
git pull origin main   # 1ce229af 또는 이후

# 1. 환경 점검
python tools/gitnexus_analyze.py
# → 571 모듈 / 6,215 심볼 확인

# 2. D-M-13: phase_c_exit_gate.py 신설
git checkout -b fix/v681-pre-phase-c-exit-gate
```

`literary_system/gates/phase_c_exit_gate.py` 작성. 본안 설계도 §1.1 코드 스켈레톤 그대로.

```bash
pytest tests/gates/test_phase_c_exit_gate.py -v
git commit -m "V681-PRE: phase_c_exit_gate.py 신설 (D-M-13, Phase C Exit 정합)"
git push origin fix/v681-pre-phase-c-exit-gate
```

### 4.2 V681 — TD-1 P99 정정 (D-M-09)

```bash
git checkout main && git pull
git checkout -b dev/v681-td1-p99-percentile
```

`literary_system/enterprise/benchmark.py`에 `percentile` 함수 추가 (NIST R-7 method). 130행의 `sorted[int(n×0.99)]`를 `percentile(elapsed_list, 0.99)`로 교체. 본안 설계도 §1.2 코드 그대로.

```bash
pytest tests/unit/test_v681_benchmark_p99.py -v
git commit -m "V681 SP-D.1: TD-1 P99 정정 (statistics.quantiles, D-M-09 ADR-143)"
```

### 4.3 V682~V687 — TD-2/3 + mypy strict + CI + 의존성 + pre-commit

본안 설계도 §1.3~1.7 코드 스켈레톤 그대로. 각 V버전:
- V682: TD-2 `is_contiguous` (revenue.py)
- V683: TD-3 `is_blocking` → `gate_passed` 연결 (cost_control.py)
- V684: G81 Pre-flight Fix Gate (≥30 TC)
- V685: poetry 도입 + CI 4단 분리 (D-M-06/07)
- V685~V686: mypy strict literary_system/ 전체
- V687: G82 + pre-commit 4종 (D-M-08)

### 4.4 V688~V690 — Observability

- V688: OTel SDK + W3C TraceContext (D-M-02)
- V689: Prometheus `/metrics`
- V690: G83 (≥20 TC)

### 4.5 SP-D.2 (V696~V715) — Distributed Runtime + API Gateway

본안 설계도 §2 그대로. 주요 본안 보강:
- V702: G84에 **Health Probe 2종 (D-M-01) + 호환성 매트릭스 (D-M-10)** 흡수
- V703: **OpenAPI→Pydantic 자동 (D-M-05)** + **Envoy 호환 헤더 (D-M-04)**

### 4.6 SP-D.3 (V716~V730) — Plugin + Zero-Trust + Chaos

본안 설계도 §3 그대로. 주요 본안 보강:
- V717: **PluginLoader RestrictedPython 옵션 (D-M-03)**

### 4.7 SP-D.4 (V731~V745) — FL + DR + Exit

본안 설계도 §4 그대로. 주요 본안 보강:
- V740: **Phase E manifest (Helm + KEDA + ArgoCD) 사전 정의 (D-M-12)**
- V741~V743: **G91 Disaster Recovery Gate 신설 (D-M-11)** — RPO ≤ 1h

---

## 5. Gate 15건 + G91 후보 (16건)

| Gate | V | 이름 | 최소 TC |
|---|---|---|---|
| G81 | V684 | Pre-flight Fix | ≥30 |
| G82 | V687 | Static Type Safety | ≥15 |
| G83 | V690 | Observability Foundation | ≥20 |
| G84 | V702 | Distributed Runtime + Health Probe + 호환성 매트릭스 | ≥40 |
| G85 | V707 | API Gateway Auth | ≥25 |
| G86 | V711 | API Completeness | ≥50 |
| G87 | V720 | Plugin Registry | ≥30 |
| G88 | V725 | Zero-Trust Security | ≥30 |
| G89 | V729 | Chaos Resilience | ≥25 |
| G90 | V737 | FL PoC | ≥30 |
| **G91 (본안)** | **V743** | **Disaster Recovery (D-M-11)** | **≥20** |
| G92~G94 | V738~V744 | SP-D.4 보조 | ≥30 |
| G95 | V745 | Phase D Exit 8축 | ≥30 |

---

## 6. 매 V버전 commit 전 의무 (DEV_PROTOCOL_v2.0 + PACKAGING_PROTOCOL_v1.0)

```bash
# 1. Preflight (PREFLIGHT_GUIDE_v1.1)
python tools/gitnexus_analyze.py
python tools/preflight_nexus.py

# 2. pre-commit (D-M-08)
pre-commit run --all-files
# → mypy strict + bandit + ruff + black 4종

# 3. CI 4단 (D-M-06)
# 로컬: unit_ci 먼저 실행
pytest tests/unit -x --timeout=30

# 4. Release Gate
python -c "from literary_system.gates.release_gate import run_release_gate; print(run_release_gate()['summary'])"

# 5. 패키지 검증 (PACKAGING_PROTOCOL_v1.0, 릴리즈 commit만)
# zip 파일 수 1,200 기준 ± 50
```

---

## 7. 위험 신호 — 상위 모드 보고 사유

| 신호 | 의미 |
|---|---|
| PASS 8,845 → 8,840 미만 후퇴 | 회귀 발생 |
| TD-1 percentile TC가 n=1/2 엣지 케이스 FAIL | D-M-09 알고리즘 재검토 |
| mypy strict 적용 시 100+ error | TypeVar/Protocol 도입 검토 |
| Agent 분산 RTT > 50ms (G84) | LiteraryBus 또는 ProcessPool 재설계 |
| Plugin 비승인 차단 실패 1건 | G87 Whitelist 정책 재점검 |
| HMAC 토큰 위·변조 검증 실패 1건 | G88 즉시 중단 + 보안 감사 |
| Chaos 자동 복구 < 3/5 | 분산 런타임 안정성 재검토 |
| FL PoC delta 수렴 안 됨 (10라운드 초과) | FedAvg 알고리즘 또는 epsilon 조정 |
| DR RPO > 1h | G91 백업 빈도 재조정 |
| 9,061 test_fn 분산 모드 차이 1건 이상 | D-M-10 호환성 회귀 |
| Phase E manifest validate 실패 | D-M-12 Helm/KEDA spec 재검토 |

---

## 8. SC-1 ~ SC-8 성공 기준 (Phase D Exit G95 8축)

| # | 기준 | 측정 | 목표 |
|---|---|---|---|
| SC-1 | G95 PASS | release_gate.py G95 | PASS (100%) |
| SC-2 | TC 통과 | pytest 전체 | ≥ 11,500, 0 FAIL |
| SC-3 | mypy strict | mypy --strict literary_system/ | 0 error |
| SC-4 | API P99 | 부하 테스트 | ≤ 200ms |
| SC-5 | 테넌트 격리 | Cross-tenant TC | 100% 차단 |
| SC-6 | Plugin 비승인 | 비허가 등록 시도 TC | 100% 차단 |
| SC-7 | Chaos 복구 | 5종 시나리오 | ≥ 4/5 |
| SC-8 | ADR | ADR-143~210 | 68건 완성 |

---

## 9. 메타데이터

- **문서 ID**: LOS-PHASE-D-PROPOSAL-FINAL-HANDOFF-V1-2026-05-27
- **선행 초안**: `C:\literary_claude\literary_os_phaseD_proposal.docx` + `_blueprint.docx` (Draft v1.0, 로컬만)
- **본 push HEAD**: 작성 직후 푸시 → 별도 보고
- **로컬 작업 경로**: `C:\literary_claude\claude` (회사)
- **유효 기간**: Phase D 종료(V745)까지. V746 Phase E 진입 시 별도 핸드오프 발행
