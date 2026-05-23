# CHANGELOG V616 — MemoryLeakDetector + StressTester v1.0

**버전**: v10.21.0 (V616)
**날짜**: 2026-05-23
**SP**: SP-B.4 (통합 최적화 + Exit)

## 변경 요약

| 항목 | V615 | V616 |
|------|------|------|
| 버전 | 10.20.0 | 10.21.0 |
| Tests | 6,603 | 6,628 |
| Gates | 59/59 | 59/59 |
| 신규 모듈 | — | memory_leak_detector.py, stress_tester.py |
| 테스트 파일 | — | test_v616_memory_stress.py (25 TC) |
| ADR | ADR-075 | ADR-076 |

## 신규 모듈

### literary_system/optimization/memory_leak_detector.py
- `MemorySnapshot.take()` — tracemalloc 스냅샷 캡처
- `LeakReport` — delta_bytes, is_leaking, top_allocators
- `MemoryLeakDetector` — start/stop/baseline/capture/check/diff API
- 기본 임계값: 10 MB (threshold_mb 파라미터)
- 컨텍스트 매니저 지원: `with MemoryLeakDetector() as d:`

### literary_system/optimization/stress_tester.py
- `StressConfig` — warmup/sustained/cooldown iters, SLO 임계값
- `PhaseResult` — latencies, p50/p95/p99/mean 백분위수
- `StressResult` — all_pass, slo_p95_pass, slo_p99_pass, slo_memory_pass
- `StressTester.run(fn)` — 3단계 스트레스 실행
- `StressTester.quick_stress()` — 클래스 메서드 단축 API

## 수정 사항

- `literary_system/gates/performance_slo_gate.py`
  - `__main__` 블록 `print()` → `logging` 교체 (Rule-2 해소)

## 테스트

- `tests/test_v616_memory_stress.py` — 25 TC (5개 클래스)
  - TestMemorySnapshot (4) + TestLeakReport (4) + TestMemoryLeakDetector (7)
  - TestPhaseResult (4) + TestStressTester (6)
  - **25/25 ALL PASS**

## Gate 현황

59/59 ALL PASS (G01~G60)
