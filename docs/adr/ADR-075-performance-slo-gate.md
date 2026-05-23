# ADR-075 — Gate G60: PerformanceSLOGate v1.0

| 항목       | 내용                          |
|----------|------------------------------|
| **상태**   | Accepted                     |
| **날짜**   | 2026-05-23                   |
| **버전**   | V615 (v10.20.0)              |
| **작성자** | Literary OS Claude           |

## 배경 (Context)

SP-B.4 통합 최적화 서브페이즈의 핵심 목표는 프로덕션 SLO를 계측하고 CI에서
자동으로 검증하는 것이다. V614에서 `PerformanceOptimizer v1.0`
(KV캐시 LRU + INT8/INT4 양자화 + 레이턴시 프로파일러 + GPU 모니터 + PerfSLOReport)
가 구현됐으나, 이를 Gate 로 연결하는 레이어가 부재했다.

## 결정 (Decision)

`literary_system/gates/performance_slo_gate.py` — **Gate G60 (PerformanceSLOGate v1.0)**
을 신설한다.

### 10-Checkpoint 구조

| CP   | 검증 항목                             | 실패 시 영향    |
|------|--------------------------------------|----------------|
| CP-1 | 모듈 임포트 + 7클래스 존재 확인         | 즉시 실패       |
| CP-2 | KVCache LRU (max_entries, hit_rate)  | 캐시 회귀       |
| CP-3 | INT8/INT4 양자화 적용 + 메모리 절감률   | 양자화 회귀     |
| CP-4 | LatencyProfiler P95 계산 정확도       | SLO 측정 오류   |
| CP-5 | GPUMemoryMonitor.stats() 키 집합      | GPU 모니터 회귀 |
| CP-6 | PerfSLOReport 구조 (9개 필드)         | 보고서 회귀     |
| CP-7 | PerfSLOReport 필드 타입 검증          | 타입 안전성     |
| CP-8 | P95 SLO ≤ 1500ms 구조 검증           | 레이턴시 SLO    |
| CP-9 | GPU SLO ≤ 8192MB 구조 검증           | 메모리 SLO      |
| CP-10| CacheHit SLO ≥ 60% 구조 검증        | 캐시 SLO        |

### SLO 임계값

```python
P95_SLO_MS    = 1500.0   # P95 레이턴시 ≤ 1.5초
GPU_SLO_MB    = 8192.0   # GPU 메모리 ≤ 8192MB
CACHE_HIT_SLO = 0.60     # KV 캐시 히트율 ≥ 60%
```

## 이유 (Rationale)

- **SLO 자동 회귀 차단**: CI에서 매 커밋마다 G60을 실행해 SLO 위반을 조기에 감지한다.
- **10-CP 구조**: SP-B.3의 G58/G59 패턴을 계승해 일관된 Gate 설계를 유지한다.
- **인터페이스 기반 검증**: 실제 PerformanceOptimizer API를 호출해 통합 회귀를 방지한다.
- **no-data 통과 정책**: 트래픽 없는 스테이징 환경에서도 CI가 통과되도록 설계했다.

## 결과 (Consequences)

### 긍정
- Gate 총수: 58 → 59 (G60 신설)
- SLO 회귀 자동 차단: 레이턴시/GPU/캐시 3축 모두 CI 보호 대상
- test_v615_performance_slo_gate.py 20 TC 추가 (6583 → 6603)

### 부정
- Gate G60은 PerformanceOptimizer 실 임포트를 요구하므로
  인터페이스 변경 시 Gate도 함께 수정 필요.

## 관련 ADR

- ADR-074 — PerformanceOptimizer v1.0 (V614)
- ADR-072 — SP-B.3 Exit Gate G59 (V612)
