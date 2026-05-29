# ADR-077: LongRunMonitor v1.0 — 에포크 기반 장기 실행 내구성 모니터

**Status**: Accepted  
**Date**: 2026-05-23  
**Version**: v10.22.0 (V617)  
**Author**: Literary OS Team  

---

## 컨텍스트

SP-B.4 통합 최적화 단계에서 단일 스트레스 테스트(StressTester)와 단일 메모리 누수 탐지(MemoryLeakDetector)만으로는 장기 운영 환경에서의 내구성을 보장하기 어렵다. 실제 프로덕션 시스템은 수시간~수일 동안 연속 실행되며, 이 과정에서 메모리 누수가 점진적으로 누적되거나 P95 지연이 에포크마다 악화될 수 있다. 단일 실행으로는 이런 추세(trend)를 포착할 수 없다.

---

## 결정

**LongRunMonitor v1.0**을 신설한다. MemoryLeakDetector + StressTester를 epoch 단위로 반복 실행하고, 에포크별 결과를 집계하여 P95 추세와 메모리 누수 델타 추세를 추적한다.

### 핵심 설계

```
LongRunConfig
  ├── epochs: int = 3             # 반복 에포크 수
  ├── warmup_iters: int = 2       # 에포크 내 웜업 반복
  ├── sustained_iters: int = 10   # 에포크 내 지속 반복
  ├── cooldown_iters: int = 2     # 에포크 내 쿨다운 반복
  ├── target_p95_ms: float = 1500 # P95 SLO (ms)
  └── leak_threshold_mb: float = 10  # 누수 임계값 (MB)

EpochResult
  ├── epoch: int                  # 에포크 번호 (0-based)
  ├── stress: StressResult        # 해당 에포크 스트레스 결과
  ├── leak: LeakReport            # 해당 에포크 누수 리포트
  ├── duration_s: float           # 에포크 소요 시간
  └── all_pass: bool              # stress.pass AND leak.pass

LongRunReport
  ├── config: LongRunConfig
  ├── epochs: List[EpochResult]
  ├── total_duration_s: float
  ├── peak_memory_mb: float
  ├── all_pass: bool              # 전 에포크 PASS
  ├── failed_epochs: List[int]    # FAIL 에포크 번호 목록
  ├── p95_trend: List[float]      # 에포크별 P95 추세
  └── leak_delta_trend: List[float]  # 에포크별 누수 델타 추세

LongRunMonitor
  ├── run(fn, memory_sampler) → LongRunReport
  ├── run_epoch(...) → EpochResult
  ├── quick_monitor(fn, epochs=3, ...) → LongRunReport  [classmethod]
  └── summary(report) → str
```

### 에포크 격리 방식

각 에포크마다 `MemoryLeakDetector.baseline()`을 호출하여 에포크 내 누수를 독립 측정한다. 에포크 간 `sleep_between_epochs_s`로 냉각 시간을 부여할 수 있다.

### SLO 판정 기준

- **StressResult.pass**: `sustained` 페이즈 P95 ≤ `target_p95_ms`
- **LeakReport.is_leaking**: `delta_bytes > threshold_bytes` → 누수 판정
- **EpochResult.all_pass**: `stress.pass AND NOT leak.is_leaking`
- **LongRunReport.all_pass**: 전 에포크 `all_pass`

---

## 대안 검토

| 대안 | 기각 이유 |
|------|-----------|
| StressTester만 반복 실행 | 메모리 누수 추세 포착 불가 |
| 단일 장기 실행 루프 | 에포크별 격리 측정 불가, 중간 결과 미수집 |
| 외부 프로파일러(memory_profiler) | 의존성 추가, tracemalloc 이미 활용 중 |
| pytest-timeout 확장 | 단위 테스트 수준; 프로덕션 모니터링 부적합 |

---

## 결과 및 영향

- **신규 모듈**: `literary_system/optimization/long_run_monitor.py` (308줄)
- **테스트**: `tests/test_v617_long_run_monitor.py` (25 TC, ALL PASS)
- **클래스명**: `MonitorConfig` → `LongRunConfig` (G37 DuplicateZero 충돌 회피: `rlhf_monitor.py`와 중복 방지)
- **Gate 영향**: 59/59 ALL PASS 유지 (G37 DuplicateZero PASS)
- **테스트 수**: 6628 → 6653 PASS

---

## 연관 ADR

- ADR-075: PerformanceSLOGate G60 (SLO 임계값 정의)
- ADR-076: MemoryLeakDetector + StressTester v1.0
