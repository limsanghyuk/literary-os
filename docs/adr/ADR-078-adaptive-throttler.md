# ADR-078: AdaptiveThrottler v1.0 — SLO 기반 동적 처리량 조절기

**Status**: Accepted  
**Date**: 2026-05-23  
**Version**: v10.23.0 (V618)  
**Author**: Literary OS Team  

---

## 컨텍스트

PerformanceSLOGate(V615), MemoryLeakDetector(V616), StressTester(V616), LongRunMonitor(V617)로 SP-B.4 측정 레이어가 완성되었다. 그러나 측정값을 읽어 **자동으로 처리량을 조절**하는 실행 계층이 없어, SLO 위반이 감지되어도 운영자가 수동으로 concurrency를 낮춰야 했다. 프로덕션 환경에서 P95 지연 급등 또는 메모리 초과 시 자동 제동이 필요하다.

---

## 결정

**AdaptiveThrottler v1.0**을 신설한다. 슬라이딩 윈도우 P95와 메모리 샘플을 기반으로 `threading.Semaphore`를 동적 재구성하여 동시성 상한을 자동 조절한다.

### 핵심 설계

```
ThrottleConfig
  ├── initial_concurrency: int = 4
  ├── min_concurrency: int = 1       ← 하한 안전망
  ├── max_concurrency: int = 16      ← 상한
  ├── step: int = 1                  ← 조정 단위
  ├── warn_threshold_ms: float = 1200   ← 감속 임계값
  ├── recover_threshold_ms: float = 800 ← 가속 임계값
  ├── memory_budget_mb: float|None   ← 비상 제동 임계값
  └── window_size: int = 20          ← P95 이동 평균 윈도우

조정 로직 (record() 호출마다):
  1. memory_mb > memory_budget_mb   → emergency: concurrency = min
  2. p95 ≥ warn_threshold_ms        → reduce:    concurrency -= step
  3. p95 < recover_threshold_ms     → increase:  concurrency += step
  4. 그 외                          → noop
```

### SLO 판정 기준

| 조건 | 액션 | 이유 |
|------|------|------|
| 메모리 > 예산 | emergency (min으로) | 메모리 OOM 방지가 최우선 |
| P95 ≥ warn | reduce | 지연 SLO 위반 예방 |
| P95 < recover | increase | 여유 용량 활용 |

### 선형 보간 P95

```python
idx = 0.95 * (n - 1)
lo, hi = int(idx), min(int(idx) + 1, n - 1)
p95 = data[lo] + (idx - lo) * (data[hi] - data[lo])
```
- window_size = 1: p95 = 그 값 자체
- window_size ≥ 2: 선형 보간으로 부드러운 변화

---

## 대안 검토

| 대안 | 기각 이유 |
|------|-----------|
| AIMD (additive increase / multiplicative decrease) | 구현 복잡, step 기반으로 충분 |
| 토큰 버킷 레이트 리미터 | 동시성이 아닌 초당 요청 수 제어 → 목적 불일치 |
| asyncio.Semaphore | 프로젝트가 threading 기반; 전환 비용 불필요 |
| PID 컨트롤러 | 게인 튜닝 오버헤드, 단순 임계값 방식이 더 예측 가능 |

---

## 결과 및 영향

- **신규 모듈**: `literary_system/optimization/adaptive_throttler.py` (392줄)
- **테스트**: `tests/test_v618_adaptive_throttler.py` (25 TC, ALL PASS)
- **Gate 영향**: 59/59 ALL PASS 유지
- **테스트 수**: 6,653 → 6,678 PASS

---

## 연관 ADR

- ADR-075: PerformanceSLOGate G60
- ADR-076: MemoryLeakDetector + StressTester v1.0
- ADR-077: LongRunMonitor v1.0
