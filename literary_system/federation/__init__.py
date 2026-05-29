"""literary_system.federation — Federated Learning PoC (SP-D.4, V732+)

패키지 구조:
  fl_types.py        — FLRound, FLClientState, FLGlobalModel 스키마
  fl_coordinator.py  — FLCoordinator 오케스트레이터
  fedavg.py          — FedAvg 집계 알고리즘 (V734)
  fl_client.py       — FLClient 로컬 훈련 시뮬레이터 (V734)
  fl_privacy.py      — DifferentialPrivacyNoise (V734)
  fl_orchestrator.py — FLOrchestrator E2E (V736)
"""
