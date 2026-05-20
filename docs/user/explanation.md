# Literary OS — 아키텍처 설명 (Explanation)

Literary OS가 왜 이런 구조로 설계되었는지 설명합니다.

---

## 핵심 설계 원칙

### 1. 7-Layer 아키텍처

Literary OS는 7개 레이어로 분리되어 있습니다. 각 레이어는 단방향 의존성을 가지며, 상위 레이어는 하위 레이어만 참조합니다.

```
L7: Orchestration (NILOrchestrator, SceneGenerationPipeline)
L6: Scene Generation (DramaEpisodeGenerator, FullSceneOrchestrator)
L5: Quality & Repair (ASD: NarrativeDebtDetector, AutoRepairExecutor)
L4: Graph Intelligence (GIG: NarrativeGraphStore, SceneChangePreGate)
L3: LLM Bridge (CanonicalLLMBridge, AnthropicAdapter, OllamaAdapter)
L2: Storage (LOSDB: SQLiteRealAdapter, VectorRealAdapter, GraphRealAdapter)
L1: Primitives (schema, NIE, physics)
```

레이어 분리 덕분에 LLM 어댑터를 바꿔도 상위 레이어 코드를 건드릴 필요가 없고, LOSDB 백엔드를 교체해도 비즈니스 로직에 영향이 없습니다.

### 2. Gate 시스템 — 릴리즈 안전망

44+1개의 Gate는 "이 기능이 실제로 동작하는가"를 코드 변경마다 검증합니다. 단위 테스트와 달리 Gate는 파이프라인 조합이 올바른지까지 확인합니다. Gate G46(E2EProseGate)은 전체 산문 생성 파이프라인이 NIE → ASD → GIG → LOSDB → Constitution → CLI 순서로 올바르게 연결되어 있는지 검증합니다.

Gate 계층화(ADR-046)는 피드백 루프 속도를 최적화합니다. 커밋 시 3게이트(1초), PR 체크 시 10게이트(1초), 릴리즈 시 45게이트 전체를 실행합니다.

### 3. NIE — 수학적 서사 공간

NIE(Narrative Interaction Engine)는 씬을 수치 공간으로 표현합니다. 각 씬은 `(감정_강도, 관계_변화, 정보_밀도, 시간_압박)` 4D 벡터로 표현되며, 씬 간 전환은 물리학의 에너지 보존처럼 연속성을 유지해야 합니다. 이로써 "갑작스러운 감정 변화"나 "정보 과부하"를 수치로 탐지할 수 있습니다.

### 4. LOSDB — 세 종류의 저장소

한국 드라마 서사는 세 종류의 데이터를 동시에 관리해야 합니다:
- **관계형(SQL)**: 캐릭터 속성, 타임라인, 사건 이력
- **벡터**: 씬 의미론적 유사도, RAG 검색
- **그래프**: 캐릭터 관계망, 인과 사슬, 복선 연결

`LOSDBClient` Facade는 세 백엔드를 단일 API로 추상화하며, `cross_query()`로 세 저장소를 동시에 질의할 수 있습니다.

### 5. ASD — 자동 수리

ASD(Automatic Story Doctor)는 서사 부채를 탐지하고 수리합니다. "부채"란 해결되지 않은 복선, 캐릭터 아크 불일치, 논리적 모순 등을 의미합니다. AutoRepairExecutor는 PlanBuildProtocol을 통해 수리 범위를 blast radius로 계산한 뒤, 최소 변경으로 부채를 해소합니다.

---

## ADR 결정 이력

주요 아키텍처 결정은 `docs/adr/` 디렉토리에 기록됩니다.

| ADR | 핵심 결정 |
|-----|-----------|
| ADR-001 | 7-Layer 아키텍처 |
| ADR-036 | Async 규율 — sync/async 혼용 금지 |
| ADR-040 | LOSDB 다중 백엔드 MigrationManager |
| ADR-045 | LOSDBClient Facade 단일 진입점 |
| ADR-046 | Gate 계층화 L0~L3 4-tier |
| ADR-047 | E2E 산문 테스트 정책 (MOCK/REAL 분리) |
| ADR-048 | 문서 정합성 CI 강제 |
