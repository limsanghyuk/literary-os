# CHANGELOG — V732~V733 (v12.5.2)

## Summary
ADR-158~170 소급 작성 완료 + federation/ 패키지 + FL PoC 기반 구축

## ADRs 소급 (V732)
- **ADR-158**: SP-D.2 개시 아키텍처
- **ADR-159**: AgentMessage + AgentTask 스키마
- **ADR-160**: CapabilityRegistry
- **ADR-161**: CollaborationProtocol
- **ADR-162**: ConflictResolver
- **ADR-163**: TaskScheduler
- **ADR-164**: AgentWorkflow
- **ADR-165**: AgentSupervisor
- **ADR-166**: agents/LoadBalancer
- **ADR-167**: agents/CircuitBreaker
- **ADR-168**: G84 Agent Coordination Gate
- **ADR-169**: G85 Agent Workflow Gate
- **ADR-170**: SP-D.2 통합 테스트 스위트
- **ADR-194**: FLCoordinator — 연합 학습 조율자 기초

## New Modules (V732)
- `literary_system/federation/__init__.py`
- `literary_system/federation/fl_types.py` — FLClientState, FLGlobalModel, FLRound
- `literary_system/federation/fl_coordinator.py` — FLCoordinator

## New Modules (V733)
- `literary_system/federation/fedavg.py` — FedAvgAggregator 스텁
- **ADR-195**: FedAvg 집계 알고리즘 스텁

## Tests
- test_v732_fl_coordinator.py: 50 TC PASS
- test_v733_fedavg_stub.py: 30 TC PASS
- 누적 TC: 10,344 + 80 = 10,424

## DEFECT 진행
- DEFECT-3: ADR-158~170 소급 완료 (13개 ADR)
