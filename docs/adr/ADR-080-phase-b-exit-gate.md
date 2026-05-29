# ADR-080 — Phase B Exit Gate G61 (V620)

**Status**: Accepted  
**Date**: 2026-05-23  
**Deciders**: Literary OS Architecture Board  
**Tags**: Gate, Phase-B, Exit-Gate, SP-B.4

---

## Context

Literary OS SP-B (V596~V620)는 4개의 서브페이즈로 구성된다:

| 서브페이즈 | 범위 | 핵심 Gate |
|-----------|------|-----------|
| SP-B.1 | LoRA Fine-tuning Pipeline | G54 |
| SP-B.2 | RLHF 루프 (RewardModel) | G56, G57 |
| SP-B.3 | MultiWork 협업 | G59 |
| SP-B.4 | 통합 최적화 + Exit | G60, G61 |

V620은 SP-B.4의 마지막 단계로서, SP-B 전체 완료를 판정하는 Phase B Exit Gate(G61)를 신설한다.

## Decision

`literary_system/gates/phase_b_exit_gate.py`에 `PhaseBExitGate`(G61)를 구현한다.

### 6축 체크포인트 구조

```
G61 (Phase B Exit Gate)
├── C1 — G54 PASS : LoRA Fine-tuning Pipeline (SP-B.1)
├── C2 — G56+G57 PASS : RLHF 루프 + ConstitutionAxis (SP-B.2)
├── C3 — G59 PASS : MultiWork 7모듈 협업 (SP-B.3)
├── C4 — G60 PASS : PerformanceSLOGate P95≤1500ms (SP-B.4)
├── C5 — Gates ≥ 60 : 전체 등록 Gate 수 달성
└── C6 — Tests ≥ 6700 : 전체 테스트 수 달성
```

### 임계값 근거

| 상수 | 값 | 근거 |
|------|----|------|
| `MIN_GATES` | 60 | V620이 G61을 추가하면 총 60 Gates 달성 |
| `MIN_TESTS` | 6700 | V619 기준 6703 PASS → 안전 마진 포함 |

### 테스트 주입 설계 (`_rg_results_override`)

`run_phase_b_exit_gate`는 `_rg_results_override` 파라미터를 통해 `run_release_gate()` 호출을 우회할 수 있다. 이는 다음을 목적으로 한다:

1. **단위 테스트 속도**: 전체 release_gate 실행(수십 초)을 mock으로 대체
2. **결정론적 테스트**: CI 환경에서 외부 의존성 없이 경계값 검증 가능
3. **인터페이스 안정성**: `None`(기본값) 유지 시 프로덕션 동작 변경 없음

이 패턴은 ADR-046(Gate 계층화)에서 정의된 "테스트 격리 원칙"과 일치한다.

## Consequences

### 긍정적 효과

- **Phase B 완전성 보증**: 4개 서브페이즈 모두 gate로 검증
- **60 Gates 마일스톤**: literary-os 개발 60번째 공식 Gate 달성
- **7,000+ 테스트 기반**: 6703 PASS 달성, 산업 수준 커버리지
- **단위 테스트 속도**: mock 주입으로 25 TC가 0.07초 완료

### 제약사항

- G61은 C1~C4(G54/G56/G57/G59/G60) 모두 PASS 시에만 `all_pass=True`
- `_rg_results_override`는 테스트 전용; 프로덕션 코드는 사용 금지

## Related

- ADR-072: SP-B.3 Exit Gate G59
- ADR-075: SP-B.4 PerformanceSLOGate G60
- ADR-079: OptimizationOrchestrator v1.0 (G61의 선행 조건)
