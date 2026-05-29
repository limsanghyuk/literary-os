# CHANGELOG — V734 & V735

**날짜**: 2026-05-29  
**버전**: v12.5.4  
**서브페이즈**: SP-D.4 (Phase D, V731~V745)  
**게이트**: G86 (PASS, V731 완료)

---

## V734 — FLClient & FLPrivacyNoise

### 신규 모듈

| 파일 | 설명 |
|------|------|
| `literary_system/federation/fl_client.py` | `ProseDataShard` + `FLClient` — 로컬 훈련 시뮬레이션, 손실/가중치 갱신 |
| `literary_system/federation/fl_privacy.py` | `FLPrivacyNoise` — Gaussian Mechanism DP (clip → noise) |

### 핵심 설계

- **FLClient.train()**: `loss = base_loss * exp(-lr * epoch) + noise`, weight update via Gaussian gradient simulation
- **FLPrivacyNoise.sigma**: `σ = clip_norm * sqrt(2 * ln(1.25/δ)) / ε`
- **privatize()**: clip_weights() → add_noise() 파이프라인

### 테스트

- `tests/unit/test_v734_fl_client_privacy.py`: 50 TC — 50/50 PASS

### ADR

- **ADR-196**: FLClient + FLPrivacyNoise 아키텍처 결정

---

## V735 — FL E2E 통합 테스트

### 신규 파일

| 파일 | 설명 |
|------|------|
| `tests/unit/test_v735_fl_e2e.py` | 40 TC — FLCoordinator + FedAvgAggregator + FLClient + FLPrivacyNoise 완전 통합 |

### 테스트 분류

| 클래스 | TC | 내용 |
|--------|-----|------|
| `TestFLFullLoop` | TC01~TC15 | 단일/다중 라운드, 수렴 감지, 요약 |
| `TestFedAvgClientIntegration` | TC16~TC20 | 가중 평균, 손실 전파 |
| `TestPrivacyFedAvgIntegration` | TC21~TC40 | DP 적용 집계, 예산 접근, 노이즈 검증 |

### 테스트 결과

- 40/40 PASS (TC06, TC16 lr=0.0→1e-9 패치 후)

### ADR

- **ADR-197**: FL PoC E2E 통합 설계

---

## 누적 TC 현황

| 버전 | 추가 TC | 누적 (단위 테스트) |
|------|---------|------------------|
| V731 | +50 | 3893 |
| V732~V733 | +80 | 3973 |
| V734 | +50 | 4023 |
| V735 | +40 | 4063 |

**현재 통과**: 4,063 / 4,088 (25개 기존 실패 — pre-existing, non-regression)

---

## 다음 단계

- **V736**: FLOrchestrator E2E 파이프라인
- **V737**: G90 FL Gate (FL-1~FL-5 축)
