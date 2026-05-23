# ADR-074: PerformanceOptimizer — INT8 양자화 + KV 캐시 (SP-B.4)

**Status**: Accepted  
**Date**: 2026-05-23  
**Version**: V614 (v10.19.0)

## Context

SP-B.4 통합 최적화 단계의 첫 번째 모듈. Gate G60 (P95 ≤ 1.5초)을 달성하기 위해
추론 파이프라인에 두 가지 최적화를 적용한다.

1. **INT8 양자화**: bitsandbytes 기반 모델 가중치 압축 (메모리 50% 절감)
2. **KV 캐시**: LRU 기반 추론 결과 재사용 (중복 요청 제거)

## Decision

`literary_system/optimization/performance_optimizer.py` 신설.

### 아키텍처 (4 컴포넌트)

| 클래스 | 역할 |
|--------|------|
| `QuantizationManager` | INT8/INT4 양자화 적용 (bitsandbytes / 스텁 분기) |
| `KVCache` | LRU 캐시 (max_entries=512, TTL=300s) |
| `LatencyProfiler` | P50/P95/P99 슬라이딩 윈도우 추적 |
| `PerformanceOptimizer` | 4컴포넌트 통합 퍼사드 |

### SLO 기준값 (Gate G60 전제)

| SLO | 임계값 |
|-----|-------|
| P95 지연 | ≤ 1,500 ms |
| GPU 메모리 | ≤ 8,192 MB |
| KV 캐시 히트율 | ≥ 60% |

### CI 전략

bitsandbytes / CUDA 없는 환경에서 스텁 경로로 전환. 실 환경에서는 동일 인터페이스로 
실 양자화 적용. 25 TC 전부 스텁 경로로 GREEN.

## Consequences

- **긍정**: PerformanceOptimizer 인터페이스가 Gate G60 사전 검증 기반을 제공
- **긍정**: KVCache의 hit_rate()는 Gate G60 캐시 SLO 체크에 직결
- **중립**: bitsandbytes 미설치 환경은 스텁으로 대체 — 실 메모리 절감 미측정
- **부정**: TTL 기반 캐시 만료는 long-running 시나리오에서 cold-start 유발 가능

## Relationship

- Depends on: ADR-073 (V613 Phase B 통합 테스트)
- Enables: ADR-075 (Gate G60 — P95 ≤ 1.5초 검증)
