# CHANGELOG — V736 & V737

**날짜**: 2026-05-29  
**버전**: v12.5.6  
**서브페이즈**: SP-D.4 (Phase D, V731~V745)  
**게이트**: G90 FL Gate (5/5 PASS)

---

## V736 — FLOrchestrator E2E 파이프라인

### 신규 모듈

| 파일 | 설명 |
|------|------|
| `literary_system/federation/fl_orchestrator.py` | `FLRunResult` + `FLOrchestrator` — FL E2E 오케스트레이터 |

### 핵심 API

- `FLOrchestrator(clients, max_rounds, dp_epsilon, dp_delta, use_privacy)` — 컴포넌트 자동 초기화
- `run_federation() → FLRunResult` — 전체 FL 루프 (start_round → train → privatize → aggregate → finalize)
- `FLRunResult`: total_rounds, converged, final_global_loss, loss_trend, privacy_budget

### 테스트

- `tests/unit/test_v736_fl_orchestrator.py`: 40 TC — 40/40 PASS

### ADR

- **ADR-198**: FLOrchestrator 아키텍처 결정

---

## V737 — G90 FL Gate

### 신규 모듈

| 파일 | 설명 |
|------|------|
| `literary_system/gates/fl_gate.py` | G90 FL Gate — FL-1~FL-5 5축 자동 검사 |

### Gate 검사 결과

| ID | 설명 | 결과 |
|----|------|------|
| FL-1 | 최소 클라이언트 등록 (≥2) | ✅ PASS |
| FL-2 | FedAvg 가중 평균 정확성 | ✅ PASS |
| FL-3 | DP 프라이버시 예산 접근 가능 | ✅ PASS |
| FL-4 | 수렴 감지 동작 | ✅ PASS |
| FL-5 | E2E 파이프라인 정상 완료 | ✅ PASS |

**G90: 5/5 PASS — APPROVED**

### 테스트

- `tests/unit/test_v737_fl_gate.py`: 30 TC — 30/30 PASS

### ADR

- **ADR-199**: G90 FL Gate 아키텍처 결정

---

## 누적 TC 현황

| 버전 | 추가 TC | 누적 (단위 테스트) |
|------|---------|------------------|
| V731 | +50 | 3893 |
| V732~V733 | +80 | 3973 |
| V734 | +50 | 4023 |
| V735 | +40 | 4063 |
| V736 | +40 | 4103 |
| V737 | +30 | 4133 |

**현재 통과**: 4,133 / 4,158 (25개 기존 실패 — pre-existing, non-regression)

---

## 다음 단계

- **V738~V740**: Phase E manifest 사전 정의 (D-M-12)
- **V741~V743**: G91 Disaster Recovery Gate (BackupManager, DR-1~DR-5, RPO≤1h)
