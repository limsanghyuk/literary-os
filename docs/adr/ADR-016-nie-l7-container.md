# ADR-016: NIE-L7 통합 계약 — NIEContainer

**상태:** 채택 (V498)
**결정자:** Chief Architect
**날짜:** 2026-05-17

## 컨텍스트

NIE(Narrative Intelligence Engine)와 L7 Narrative Physics Engine의
관계를 명문화해야 한다.

## 결정

**NIE = L7의 자가 학습 운영 레이어.**

- L7: 8차원 텐서(SP/RU/ET/RD/AG/DL/PD/AT) 시뮬레이션 표면
- NIE: 그 텐서의 가중치(physics_coefficients + α_dim + W[i][j])를 자가 학습

`literary_system/nie/nie_l7_container.py`에 NIEContainer 신설.

### V498 구현 범위
- PhysicsRewardBridge 배선 (NIL Step 4+5)
- run_scene(): 단일 씬 처리
- get_status(): 계수 + 기준선 조회

### 미래 확장 (버전별)
- V502+: CIM 통합 (NIL Step 1+2)
- V509+: QueryIntentClassifier (NIL Step 6)
- V512+: NILStabilityModule 연동
- V515+: MetaLearner (30+ 작품 조건)

## 결과
- NIL 루프의 단일 진입점 확립
- 모듈별 점진적 활성화 가능 (NIEConfig 플래그)
