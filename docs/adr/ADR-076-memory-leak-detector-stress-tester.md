# ADR-076: MemoryLeakDetector + StressTester v1.0 (SP-B.4)

**날짜**: 2026-05-23
**상태**: 승인됨
**버전**: v10.21.0 (V616)
**관련**: ADR-074(PerformanceOptimizer), ADR-075(PerformanceSLOGate G60)

---

## 컨텍스트

SP-B.4 통합 최적화 단계(V613~V630)에서 Gate G60이 P95/GPU/CacheHit SLO를 단시간 측정한다.
그러나 24h 장기 실행 시나리오에서의 메모리 누수 탐지와 반복 부하 하에서의 레이턴시
안정성 검증은 단독 Gate 체크포인트로 충분하지 않다.

V616은 두 개의 독립 유틸리티 모듈을 도입한다:

1. **MemoryLeakDetector** — tracemalloc 기반 메모리 누수 탐지
2. **StressTester** — warm-up / sustained / cooldown 3단계 SLO 스트레스 프레임워크

---

## 결정

### MemoryLeakDetector v1.0

| 구성 요소 | 설명 |
|-----------|------|
| `MemorySnapshot` | `tracemalloc.take_snapshot()` 래퍼 — total_bytes + top_allocators |
| `LeakReport` | baseline vs current diff 결과 — delta_bytes, is_leaking, top_n 할당자 |
| `MemoryLeakDetector` | `start/stop/baseline/capture/check/diff` 공개 API |
| 기본 임계값 | 10 MB (threshold_mb 파라미터로 조정 가능) |
| 컨텍스트 매니저 | `with MemoryLeakDetector() as d:` 패턴 지원 |

**누수 판정 기준**:
```
is_leaking = (current_bytes - baseline_bytes) > threshold_bytes
```

### StressTester v1.0

| 구성 요소 | 설명 |
|-----------|------|
| `StressConfig` | warmup/sustained/cooldown iters, target_p95_ms, target_p99_ms, target_memory_mb |
| `PhaseResult` | 단일 페이즈 latencies, p50/p95/p99/mean, success_rate |
| `StressResult` | 3단계 집계 — all_pass, slo_p95_pass, slo_p99_pass, slo_memory_pass |
| `StressTester` | `run(fn)`, `run_phase(phase, fn, iters)`, `quick_stress()` 클래스 메서드 |

**SLO 판정 기준** (sustained 단계 기준):
```
slo_p95_pass   = sustained.p95_ms ≤ config.target_p95_ms
slo_p99_pass   = sustained.p99_ms ≤ config.target_p99_ms (옵션)
slo_memory_pass = peak_memory_mb ≤ config.target_memory_mb (옵션)
```

**백분위수 계산**: 선형 보간 (`_percentile` 함수) — numpy 의존성 없음.

---

## 설계 원칙

1. **tracemalloc 선택 이유**: Python 표준 라이브러리, 외부 의존성 없음.
   `memory_profiler`, `objgraph` 등 서드파티 대비 설치 부담 없음.

2. **3단계 구조 (warm-up → sustained → cooldown)**:
   - warm-up: JIT/캐시 준비 — SLO 판정 제외
   - sustained: 실제 부하 측정 — SLO 판정 기준
   - cooldown: 자원 반환 확인 — SLO 판정 제외

3. **오류 격리**: `run_phase`는 예외를 error 카운트로 흡수 — 테스트 중단 없음.

4. **결합 가능 설계**: `MemoryLeakDetector` + `StressTester`는 독립적이며
   `memory_sampler` 콜백으로 통합 사용 가능.

---

## 결과

### 긍정적

- 24h 장기 실행 시나리오에서 메모리 누수 조기 발견 가능
- warm-up 제거로 콜드 스타트 레이턴시가 SLO 판정을 왜곡하지 않음
- numpy/psutil 등 추가 의존성 없음

### 부정적 / 트레이드오프

- tracemalloc은 C 확장 모듈 내 할당을 추적하지 못함
  → C 레이어 누수는 별도 도구(Valgrind 등) 필요
- StressTester는 실제 운영 부하 패턴(동시성 등)을 재현하지 않음
  → 동시성 스트레스는 V623~V625에서 asyncio + threading 확장 예정

---

## 관련 파일

- `literary_system/optimization/memory_leak_detector.py` (V616 신규)
- `literary_system/optimization/stress_tester.py` (V616 신규)
- `tests/test_v616_memory_stress.py` — 25 TC
- `docs/adr/ADR-074-performance-optimizer.md`
- `docs/adr/ADR-075-performance-slo-gate.md`
