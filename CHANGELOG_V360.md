# Literary OS V360 — CHANGELOG

## V360 신규 컴포넌트

### NKG 확장 (schema.py / graph_store.py)
- NKGNodeType에 CONFLICT_CLUSTER, NARRATIVE_PROCESS 추가
- NKGEdgeType에 STEP_IN_NARRATIVE, IN_CLUSTER, CLUSTER_LINK, CONTRACT_LINK 추가
- SemanticModelState / ConflictType enum 신규
- ConflictClusterNode / NarrativeProcessNode dataclass 신규
- make_cluster_id / make_process_id 헬퍼 함수
- V350 레거시 alias 완전 유지 (NKGSceneNode, NKGCharacterNode 등)

### CharacterClusterDetector (Leiden 알고리즘)
- 외부 의존성 없는 순수 Python 구현
- Phase1 Local Moving + Phase2 Refinement (고립 노드 재배치)
- ClusterResult dataclass: clusters, cluster_edges, partition, modularity, duration_ms
- NKGGraphStore에 IN_CLUSTER 엣지 자동 병합

### NKGProcessDetector (BFS 씬 흐름 탐지)
- max_depth=8, min_chain=3
- 진입 씬(in-degree=0) 탐색 → BFS 체인 구성
- tension_arc 계산 → tension≥0.7 시 ForeshadowNode(is_candidate=True) 추가
- STEP_IN_NARRATIVE 엣지 자동 생성

### DKGStalenessTrackerV2
- OrderedDict LRU 캐시 (max_size=500)
- register / check_stale / mark_dirty_if_stale / stats()
- _incremental_saves 카운터
- alias: DKGStalenessTracker, NKGStalenessTracker

### NKGSemanticModel (3단계 상태 머신)
- WRITE → RECONCILE → FROZEN
- guard_write(): FROZEN 시 SemanticModelFrozenError
- reconcile(): 중복 CharacterNode 병합, ReconcileReport 반환
- freeze(): 불변 잠금 + snapshot
- assert_frozen(): GR-04 FROZEN 필수 검증

### NKGChangeDetector
- snapshot_all(): 전체 노드 해시 스냅샷
- scan_changes(): changed_ids / unchanged_ids / new_ids
- rename_dry_run(): GR-02/05 지원

### NKG-GUARDRAILS (5규칙)
- GR-01: 공유 노드 영향 분석 필수
- GR-02: 이름 변경 dry-run 필수
- GR-03: Blast Radius ≤ 30%
- GR-04: 의미 모델 FROZEN 필수
- GR-05: 다중 씬 편집 감지
- run_all(): raise_on_violation 옵션

### BlastRadiusCalculator v2
- DKG + NKG 통합
- upstream / downstream BFS 방향 분리
- blast_ratio = (upstream+downstream) / total_nodes

### PlanBuildGate v2
- WorkDeclaration dataclass (10개 필드)
- GateResult: passed, checks, violations, blast
- 보존 파일 검사 + GUARDRAILS 5규칙 통합

### NarrativeScopeResolver
- 장르 플러그인 아키텍처 (PluginRegistry)
- 내장 5종: literary / noir / fantasy / romance / historical
- StyleDirective: genre_id, pov, scene_rhythm, emotional_amp

### NKGSearchEngine (BM25 + Vector RRF)
- BM25Index: k1=1.5, b=0.75
- LightVectorIndex: 64-dim 해시 임베딩
- RRF 융합: K=60
- search_scenes / search_characters / search_clusters / search_processes / search_foreshadow

### ContractBridge v1
- SceneIntent 6종: REVEAL/CONCEAL/FORESHADOW/TURN/ESTABLISH/RESOLVE
- SceneIntentIR 공유 IR
- cross_validate(): intent/tension/budget 충돌 감지
- validate_all(): 전체 씬 일괄 검증
- consensus_ir: 일관 시 평균값 합의 IR 생성

### DKGPipeline v2 (7단계 오케스트레이터)
- INIT → GRAPH → COMMUNITIES → PROCESSES → PLAN → BUILD → VERIFY
- DKGPhaseResult: phase, success, duration_ms, metadata, error, nodes_added, edges_added
- run_full(): 전 단계 순차 실행
- phase_results(): 단계별 결과 조회
- V350 레거시 스텁 유지: DKGInitPhase, DKGGraphPhase, DKGPlanPhase, DKGBuildPhase, DKGVerifyPhase

## 테스트 현황 (V360)
- 총 1500 PASS, 2 SKIPPED
- 테스트 파일 18종 (9종 핵심 + 9종 보강)

## V350 → V360 레거시 호환
- NKGSceneNode, NKGCharacterNode, NKGForeshadowNode alias 유지
- DKGStalenessTracker alias 유지
- conftest.py collect_ignore로 V329/V340 레거시 테스트 격리
