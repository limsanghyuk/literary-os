# ADR 자동 추출 인덱스

> 자동 생성: `tools/extract_adr.py` (ADR-032 retroactive automation)
> **V582 업데이트**: ADR-041 문서 파일 반영

총 41개 ADR 참조 발견

| ADR | 문서 파일 | 소스 참조 수 | git 커밋 |
|-----|---------|------------|---------|
| ADR-001 | — | 5 | — |
| ADR-002 | — | 4 | — |
| ADR-003 | — | 4 | — |
| ADR-004 | — | 7 | — |
| ADR-005 | — | 7 | — |
| ADR-006 | — | 13 | — |
| ADR-007 | — | 13 | — |
| ADR-008 | — | 24 | — |
| ADR-009 | — | 9 | — |
| ADR-010 | — | 6 | — |
| ADR-011 | — | 12 | — |
| ADR-012 | — | 6 | — |
| ADR-013 | — | 4 | — |
| ADR-014 | [ADR-014_scene_necessity.md](ADR-014_scene_necessity.md) | 15 | — |
| ADR-015 | [ADR-015-physics-reward-bridge.md](ADR-015-physics-reward-bridge.md) | 24 | — |
| ADR-016 | [ADR-016-nie-l7-container.md](ADR-016-nie-l7-container.md) | 15 | — |
| ADR-017 | [ADR-017-mae-agents-isolation.md](ADR-017-mae-agents-isolation.md) | 15 | — |
| ADR-018 | [ADR-018-character-influence-matrix.md](ADR-018-character-influence-matrix.md) | 12 | — |
| ADR-019 | [ADR-019-nil-stability.md](ADR-019-nil-stability.md) | 9 | — |
| ADR-020 | [ADR-020-meta-learner.md](ADR-020-meta-learner.md) | 11 | — |
| ADR-021 | [ADR-021-temporal-cim.md](ADR-021-temporal-cim.md) | 7 | — |
| ADR-022 | [ADR-022-tideal-learner.md](ADR-022-tideal-learner.md) | 9 | — |
| ADR-023 | [ADR-023-narrative-graph-intelligence.md](ADR-023-narrative-graph-intelligence.md) | 5 | — |
| ADR-024 | [ADR-024-code-dependency-graph.md](ADR-024-code-dependency-graph.md) | 4 | — |
| ADR-025 | [ADR-025-plan-build-gate-calibration.md](ADR-025-plan-build-gate-calibration.md) | 3 | — |
| ADR-026 | [ADR-026-autonomous-story-doctor.md](ADR-026-autonomous-story-doctor.md) | 3 | — |
| ADR-027 | [ADR-027_CIM_NarrativeGraph_Sync.md](ADR-027_CIM_NarrativeGraph_Sync.md) | 5 | — |
| ADR-028 | [ADR-028_Gate_Hierarchy_L1_L4.md](ADR-028_Gate_Hierarchy_L1_L4.md) | 7 | — |
| ADR-029 | [ADR-029_NIL_PBP_Integration.md](ADR-029_NIL_PBP_Integration.md) | 3 | — |
| ADR-030 | [ADR-030_Safety_5Step_AutoRepair.md](ADR-030_Safety_5Step_AutoRepair.md) | 5 | — |
| ADR-031 | [ADR-031_LLM0_Static_Gate.md](ADR-031_LLM0_Static_Gate.md) | 8 | — |
| ADR-032 | [ADR-032.md](ADR-032.md) | 6 | — |
| ADR-033 | [ADR-033.md](ADR-033.md) | 4 | — |
| ADR-034 | [ADR-034.md](ADR-034.md) | 8 | — |
| ADR-035 | [ADR-035.md](ADR-035.md) | 15 | — |
| ADR-036 | [ADR-036.md](ADR-036.md) | 3 | V580 |
| ADR-037 | — | 1 | — |
| ADR-038 | — | 1 | — |
| ADR-039 | [ADR-039.md](ADR-039.md) | 3 | V580 |
| ADR-040 | [ADR-040.md](ADR-040.md) | 8 | V581 |
| ADR-041 | [ADR-041.md](ADR-041.md) | 6 | V582 |
| ADR-042 | [ADR-042.md](ADR-042.md) | 5 | V583 |

---
*생성 시각: V578 (2026-05-19) / V583 업데이트: 2026-05-20*

| ADR-043 | V584 | VectorRealAdapter — numpy-optional 벡터 스토어 (LOSDB Phase B) || ADR-044 | V585 | GraphRealAdapter — Neo4j/NetworkX 그래프 백엔드 (LOSDB Phase C) |
| ADR-045 | V586 | LOSDBClient Facade — 단일 진입점 + cross_query API |
| ADR-046 | [ADR-046-gate-hierarchy.md](ADR-046-gate-hierarchy.md) | 5 | V587 |
| ADR-047 | [ADR-047-e2e-prose-policy.md](ADR-047-e2e-prose-policy.md) | 5 | V587 |
| ADR-048 | [ADR-048-doc-consistency-ci.md](ADR-048-doc-consistency-ci.md) | 4 | V587 |
| ADR-056 | V596 | LoRA Dataset Format + ProvenanceLedger + DatasetRegistry + DSR 30-day SLA |
| ADR-057 | V597 | LoRA 학습 설정 + GPU 격리 정책 (rank=16, 격주 학습, TrainPlane Helm) |
| ADR-060 | Fine-tuning Pipeline Gate G54 + 베이스 모델 3종 적합성 | V600 | Accepted |
| ADR-061 | V601 | RewardModel v1.0 — Constitution 5축 → 스칼라 R(scene) + 적대적 시드 |
| ADR-062 | V602 | RLHFDatasetBuilder v1.0 — (씬, 보상) JSONL 8B/3B 듀얼 |
| ADR-063 | V603 | PPOTrainer + ConstraintGuard (KL≤0.05, GAE λ=0.95 γ=0.99) |
| ADR-064 | V604 | RLHFMonitor v1.0 — 슬라이딩 윈도우 이동평균 + 자동 롤백 트리거 |
| ADR-065 | V605 | CanaryController v1.0 — 4단계 5/25/50/100% 카나리 롤아웃 |
| ADR-066 | V606 | CanonicalBridgeV2 + Gate G56/G57 (SP-B.2 완료) |
| ADR-067 | V607 | SharedCharacterDB v2.0 + SharedWorldDB v2.0 (SP-B.3 시작) |
| ADR-068 | V608 | MultiWorkOrchestratorV2 v2.0 — 프로젝트 체크포인트 + 충돌 탐지 + RLHF 보상 통합 (SP-B.3) |
| ADR-069 | MultiWorkCIMV2 설계 결정 | V609 | Accepted |
| ADR-070 | MultiWorkCIM v2.0 — 팩토리 패턴 + 업그레이드 유틸리티 | V610 | Accepted |
- [ADR-193](ADR-193.md) — G86 API Completeness Gate 신설 (V731, DEFECT-2 수정)

- [ADR-209](ADR-209.md) — G_INTEGRITY_MANIFEST: SHA256 자기검증 + 테스트 인벤토리 상시화 (V746, WP-0)

- [ADR-249](ADR-249.md) — SP-E.10 졸업: per-token loop-C 5/5 ADOPT → Phase E Exit v14.0.0 (V793, 2026-06-24)
