# ADR-079: OptimizationOrchestrator v1.0 — SP-B.4 통합 파이프라인

**날짜**: 2026-05-23  
**상태**: 승인됨  
**작성자**: Literary OS 개발팀  
**관련**: V619, SP-B.4, ADR-074~ADR-078

---

## 맥락

SP-B.4는 5개의 독립 최적화 모듈(PerformanceOptimizer, MemoryLeakDetector,
StressTester, LongRunMonitor, AdaptiveThrottler)을 통해 Literary OS의 성능·안정성을
검증한다. 각 모듈은 독립적으로 사용 가능하지만, 실제 운영 환경 투입 전 통합 검증이
필요했다. 분산된 호출 순서를 사용자가 매번 직접 조율해야 했으며, 이로 인해 단계
누락이나 순서 역전 오류가 발생할 위험이 있었다.

---

## 결정

`OptimizationOrchestrator` 클래스를 신설해 6단계 파이프라인을 단일 진입점으로 제공한다.

### 파이프라인 단계

| 단계 | 이름 | 역할 | 모듈 |
|------|------|------|------|
| 1 | BASELINE | tracemalloc 기준선 캡처 | MemoryLeakDetector |
| 2 | STRESS | 3-페이즈 SLO 스트레스 | StressTester |
| 3 | LEAK | 메모리 누수 점검 | MemoryLeakDetector |
| 4 | LONGRUN | 에포크 내구성 검증 | LongRunMonitor |
| 5 | THROTTLE | 동적 처리량 조정 실행 | AdaptiveThrottler |
| 6 | REPORT | 종합 판정 + OptimizationReport 반환 | — |

### 핵심 타입

- **`OptOrchestratorConfig`**: 모든 하위 모듈 설정을 단일 dataclass로 통합.
  헬퍼 메서드(`to_stress_config()`, `to_longrun_config()`, `to_throttle_config()`)로
  각 모듈 설정 객체를 자동 생성.
- **`StageResult`**: 단계별 `passed / duration_s / detail` 기록.
- **`OptimizationReport`**: 전체 결과 집계. `all_pass`, `failed_stages`,
  `passed_count / total_count`, `summary()`, `to_dict()` 제공.

### 명명 규칙 — G37 충돌 방지

기존 `literary_system/orchestrators/full_scene_orchestrator.py`에 `OrchestratorConfig`가
존재하므로 이 ADR 모듈은 **`OptOrchestratorConfig`** 를 사용한다.
DuplicateZero Gate(G37)에 의해 강제 검증된다.

### G32 규칙 준수

모듈 Docstring 예시에서 `print()` 대신 `_log.info()` 사용. 모든 출력은
표준 logging으로만 수행한다.

---

## 대안 검토

| 대안 | 이유 |
|------|------|
| 스크립트 수준 연결 | 재사용성 없음, 단계 누락 위험 |
| 비동기(asyncio) 파이프라인 | 모든 하위 모듈이 동기 전제 — 불일치 |
| 설정 자동 탐지 | 명시적 설정이 테스트 재현성에 유리 |

---

## 결과

- `literary_system/optimization/optimization_orchestrator.py` (392줄)
- `tests/test_v619_optimization_orchestrator.py` (25 TC, ALL PASS)
- 6678 → 6703 PASS (+25), 59/59 Gates ALL PASS
- `OptimizationOrchestrator.quick_run()` 편의 메서드 제공
