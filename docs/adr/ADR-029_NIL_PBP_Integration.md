# ADR-029: NIL × PlanBuildProtocol 통합 정책

Status: Accepted

## 문제
NILOrchestrator와 PlanBuildProtocol이 독립 실행 (P4).
NIL 루프에서 생성된 씬 변경이 PBP Gate26/27을 우회.

## 결정
NIL Step 5(씬 생성 확정) 이후 PBP를 필수 통과 게이트로 삽입.
- NIL → SceneChangePreGate(Gate26) → Gate27 → 씬 확정
- 실패 시 NIL Step 4로 롤백

## 근거
P4 해소. NIL과 GIG 파이프라인 완전 통합.
