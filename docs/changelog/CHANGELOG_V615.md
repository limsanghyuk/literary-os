# CHANGELOG — V615 (v10.20.0)

**날짜**: 2026-05-23
**베이스**: V614 (v10.19.0, commit 9d4ac762)

## 신규 모듈

### `literary_system/gates/performance_slo_gate.py` — PerformanceSLOGate v1.0
- Gate G60: 10-Checkpoint SLO 검증 게이트
- CP-1~CP-3: 모듈 임포트, KVCache LRU, INT8/INT4 양자화
- CP-4~CP-7: LatencyProfiler P95, GPUMonitor, PerfSLOReport 구조/타입
- CP-8~CP-10: P95 ≤ 1500ms, GPU ≤ 8192MB, CacheHit ≥ 60% SLO 구조 검증
- `run_g60_gate()` module-level runner (release_gate.py 호출 인터페이스)

## 테스트

### `tests/test_v615_performance_slo_gate.py` — 20 TC ALL PASS
- TestConstants (3 TC): SLO 임계값 상수
- TestCheckpointResult (3 TC): 데이터 클래스
- TestG60GateResult (5 TC): G60 결과 구조
- TestGateCheckpoints (7 TC): 개별 CP 검증
- TestRunG60Gate (2 TC): 통합 실행

## Gate 변경

- `literary_system/gates/release_gate.py`: Gate G60 등록 (59번째 Gate)
- 59/59 ALL PASS

## 문서

- `docs/adr/ADR-075-performance-slo-gate.md`: Gate G60 설계 결정

## 수치 변화

| 항목     | V614      | V615      |
|--------|-----------|-----------|
| 버전     | v10.19.0  | v10.20.0  |
| Gates   | 58        | 59        |
| Tests   | 6,583     | 6,603     |
| ADR     | ADR-074   | ADR-075   |
