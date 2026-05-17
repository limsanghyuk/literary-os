# ADR-015: PhysicsRewardBridge — MAE → 물리 계수 배선

**상태:** 채택 (V498)
**결정자:** Chief Compiler, Chief Architect
**날짜:** 2026-05-17

## 컨텍스트

MAEOrchestrator는 씬을 평가하고 pass/fail 합의를 반환하지만,
그 결과가 PhysicsCoefficientUpdater에 도달하는 경로가 없었다 (Gap 3).

## 결정

`literary_system/nie/physics_reward_bridge.py`에 PhysicsRewardBridge를 신설.

### 핵심 설계
- **LLM-0 원칙 준수**: Bridge 내부에서 LLM 호출 절대 금지
- **R(scene) 계산**: pass_count/total + consensus_bonus(0.1)
- **Policy Gradient Lite**: advantage = R - R_baseline
  - advantage > 0: w_k += LR * advantage * (feature - w_k)
  - advantage < 0: w_k -= LR * |advantage| * (feature - w_k)
- **R_baseline EMA**: decay=0.95, init=0.50
- **LR**: LR_PHYSICS=0.01 (NILStabilityModule이 동적 조정 가능)

### ADR-006 격리 범위 명시 (Call Graph)
```
MAEOrchestrator.evaluate()   ← LLM 호출 가능 (격리 영역)
        |
        v
PhysicsRewardBridge.process()  ← LLM 호출 금지
        |
        v
PhysicsCoefficientUpdater.update_one_epoch()  ← LLM 호출 금지
        |
        v
PhysicsCoefficientStore.update()  ← LLM 호출 금지
```

## 결과
- NIL Step 5 완성
- 씬 품질 신호가 자동으로 물리 계수에 반영됨
- NILStabilityModule (V512+) 연동 준비
