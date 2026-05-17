# ADR-030: AutoRepair 5단계 안전망

Status: Accepted

## 문제
AutoRepairExecutor가 PBP는 통과하나 추가 안전망 부재 (P6).

## 결정
SafetyAugmentedAutoRepair 5단계 안전망:
1. DryRun Validation
2. Blast Radius Check (≤ 0.70)
3. Rollback Snapshot
4. PBP Gate Pass (Gate26+27)
5. Post-Repair Gate28 Verify

모든 단계 통과 시에만 실제 수리 실행.

## 근거
P6 해소. 수리 실행의 안전성 보장.
