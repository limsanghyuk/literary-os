# Literary OS — 통합 릴리즈 노트 (V587 ~ V589)

> **패키지 기준**: v9.4.0 (V589 SP-A.2, 2026-05-21)  
> **GitHub**: https://github.com/limsanghyuk/literary-os  
> **Phase**: A (V581~V595) — 8 sub-phase 중 2번째까지 완료

---

## 릴리즈 요약

| 버전 | 태그 | 날짜 | Gates | 핵심 내용 |
|---|---|---|---|---|
| **V587** | v9.2.0 | 2026-05-20 | 45/45 | E2EProseGate + 4계층 CI + 사용자 문서 4종 |
| **V588** | v9.3.0 | 2026-05-21 | 46/46 | QueryInterface + Qdrant docker-compose |
| **V589** | v9.4.0 | 2026-05-21 | 47/47 | BackendHealthMonitor + HybridRetrieverV2 |

---

## V587 — v9.2.0 (Gate G46, ADR-046~048)

### 목적
외부 신뢰 회복 + Gate 계층화 + 사용자 문서 완비

### 주요 변경

**SP-α 외부 신뢰 회복**
- `ci.yml` 버그 수정: 39 Gates → 45 Gates 올바르게 반영
- `tools/check_version_consistency.py` 신설: pyproject / README / MANIFEST / CHANGELOG / ci.yml / git tag 6개 파일 SSoT 자동 검증
- `.github/workflows/release.yml` 신설: v태그 push 시 자동 릴리즈

**SP-β Gate G46 + ADR-046 Gate 계층화**
- **Gate G46 (E2EProseGate)**: NIE/NIL → ASD → GIG → LOSDB → Constitution → CLI 6단계 E2E 검증
- **ADR-046**: L0(3게이트, ≤5s) / L1(7게이트, ≤30s) / L2(35게이트, ≤2m) / L3(전체 45, ≤5m) 4계층 CI
- `run_release_gate_tiered(tiers=['L0','L1'])` fast-path: **1,103ms** (10게이트)
- **ADR-047**: E2E Prose 정책
- **ADR-048**: doc consistency CI

**SP-γ 사용자 문서**
- `docs/user/quickstart.md` — 5분 빠른 시작
- `docs/user/howto.md` — 드라마 에피소드 생성 방법
- `docs/user/explanation.md` — 7-Layer 아키텍처 원리
- `docs/user/reference.md` — 45개 게이트 표 + ADR 목록 (자동 생성)
- `examples/sample_drama/generate.py` — "비와 편지" MockGateway 샘플
- `tools/gen_cli_reference.py` — reference.md 자동 재생성

### Gate G46 (E2EProseGate) — 6/6 PASS

| 체크포인트 | 결과 |
|---|---|
| NIE/NIL 컴포넌트 임포트 | PASS |
| ASD (Arc Story Doctor) 임포트 | PASS |
| GIG (Graph Intelligence Gate) | PASS |
| LOSDB Facade | PASS |
| Constitution 스코어러 | PASS |
| CLI 진입점 | PASS |

### 수치

| 항목 | V586 (9.1.0) | V587 (9.2.0) |
|---|---|---|
| Gates | 44/44 | **45/45** |
| Tests | 5,744+ | **5,760+** |
| ADR | ADR-001~045 | **ADR-001~048** |
| L0+L1 fast-path | — | **1,103ms** |
| 사용자 문서 | 없음 | **4종** |

---

## V588 — v9.3.0 (Gate G47, ADR-049)

### 목적
LOSDB QueryInterface 도메인 쿼리 레이어 + Qdrant docker-compose 구성

### 주요 변경

**literary_system/db/query_interface.py** (신규, 324줄)

```python
class QueryInterface:
    SLO_RESPONSE_SEC: float = 1.0

    def find_scenes(
        self, *, character, similar_to, graph_within_hops, episode_range, limit=10
    ) -> List[SceneResult]

    def find_characters(
        self, similar_personality: List[float], *, limit=10
    ) -> List[CharacterResult]

    def cross_backend_aggregate(
        self, *, group_by, metric="count", backends=None
    ) -> List[AggregateResult]

    def health(self) -> Dict[str, Any]
```

핵심 동작:
1. SQL 레이블 검색 (캐릭터 기반, episode_range 필터)
2. Vector 유사도 검색 (Qdrant 연동)
3. Graph 홉 검색 (hops ≤ graph_within_hops)
4. 중복 제거 → score 내림차순 → limit

**docker-compose.yml** (Qdrant 추가)
```yaml
qdrant:
  image: qdrant/qdrant:v1.7.4
  profiles: ["dev"]
  ports: ["6333:6333", "6334:6334"]
  volumes: [qdrant_storage:/qdrant/storage]
```

**결과 데이터클래스**
- `SceneResult`: scene_id, episode, label, backend, score, metadata
- `CharacterResult`: character_id, name, similarity, backend, metadata
- `AggregateResult`: group_key, metric_value, backend_counts, records

### Gate G47 (QueryInterfaceGate) — 8/8 PASS

| ID | 검증 내용 | 결과 |
|---|---|---|
| QI-1 | QueryInterface 임포트 | PASS |
| QI-2 | 데이터클래스 3종 존재 | PASS |
| QI-3 | no_client → find_scenes 빈 결과 | PASS |
| QI-4 | no_client → find_characters 빈 결과 | PASS |
| QI-5 | no_client → cross_backend_aggregate 빈 결과 | PASS |
| QI-6 | health() status == "no_client" | PASS |
| QI-7 | SLO_RESPONSE_SEC == 1.0 | PASS |
| QI-8 | LLM-0 원칙 (외부 LLM 호출 없음) | PASS |

### 수치

| 항목 | V587 (9.2.0) | V588 (9.3.0) |
|---|---|---|
| Gates | 45/45 | **46/46** |
| 신규 테스트 | — | **+30** (TC01~TC30) |
| ADR | ADR-001~048 | **ADR-001~049** |
| QueryInterface | 없음 | **구현 완료** |
| Qdrant docker | 없음 | **profiles:dev 추가** |

---

## V589 — v9.4.0 (Gate G48, ADR-050)

### 목적
DB 백엔드 부분 가용성(Partial Availability) 대응 + HybridRetrieverV2 폴백

### 주요 변경

**literary_system/db/health_monitor.py** (신규, 213줄)

```python
class AvailabilityState(str, Enum):
    FULL             = "FULL"           # 전체 정상
    PARTIAL_DEGRADED = "PARTIAL_DEGRADED"  # 일부 장애 (≥2 가용)
    CRITICAL         = "CRITICAL"       # 1개만 가용
    OFFLINE          = "OFFLINE"        # 전체 장애

class BackendCircuitState(str, Enum):
    CLOSED    = "CLOSED"    # 정상 운전
    OPEN      = "OPEN"      # 차단
    HALF_OPEN = "HALF_OPEN" # 복구 프로브

class BackendHealthMonitor:
    PING_INTERVAL_SEC: float = 30.0

    def register(backend, ping_fn=None)
    def check(backend) -> BackendCircuitState
    def check_all() -> Dict[BackendType, BackendCircuitState]
    def get_available_backends() -> List[BackendType]
    def overall_state() -> AvailabilityState
    def health_report() -> Dict[str, Any]
    def force_open(backend)   # 테스트용
    def force_closed(backend) # 테스트용
```

Circuit Breaker 동작:
```
CLOSED → (연속 3회 실패) → OPEN → (60s 경과) → HALF_OPEN → (성공) → CLOSED
```

**T1~T4 시나리오 (Gate G48 기준)**

| 시나리오 | 가용 백엔드 | AvailabilityState | QueryInterface 동작 |
|---|---|---|---|
| T1 | 3/3 | FULL | 전체 쿼리 정상 |
| T2 | 2/3 | PARTIAL_DEGRADED | 장애 백엔드 스킵 |
| T3 | 1/3 | CRITICAL | SQL 전용 쿼리 |
| T4 | 0/3 | OFFLINE | 빈 결과 반환 |

**QueryInterface 통합**
- `health_monitor` 파라미터 추가 (선택적, None이면 전체 허용)
- `_get_available_backends()` — monitor 있으면 가용 백엔드만 필터링
- VECTOR OPEN 시 `find_characters()` 즉시 빈 결과 (SLO 1.0s 보호)

**HybridRetrieverV2** (literary_system/rag/hybrid_retriever.py 추가)
- 기존 V438 HybridRetriever 완전 보존
- health_monitor 주입, VECTOR OPEN 시 BM25 단독 폴백
- `source="bm25_fallback"` 명시

### Gate G48 (PartialAvailabilityGate) — 10/10 PASS

| ID | 검증 내용 | 결과 |
|---|---|---|
| PA-1 | BackendHealthMonitor 임포트 | PASS |
| PA-2 | AvailabilityState 4종 확인 | PASS |
| PA-3 | BackendCircuitState 3종 확인 | PASS |
| PA-4 | 빈 모니터 → OFFLINE | PASS |
| PA-5 | T1: 3 backends → FULL | PASS |
| PA-6 | T2: 1 OPEN → PARTIAL_DEGRADED | PASS |
| PA-7 | T3: 2 OPEN → CRITICAL | PASS |
| PA-8 | T4: 3 OPEN → OFFLINE | PASS |
| PA-9 | QueryInterface health_monitor 파라미터 존재 | PASS |
| PA-10 | LLM-0 원칙 준수 | PASS |

### 수치

| 항목 | V588 (9.3.0) | V589 (9.4.0) |
|---|---|---|
| Gates | 46/46 | **47/47** |
| 신규 테스트 | — | **+25** (T1~T4) |
| ADR | ADR-001~049 | **ADR-001~050** |
| BackendHealthMonitor | 없음 | **구현 완료** |
| HybridRetrieverV2 | 없음 | **구현 완료** |

---

## 통합 수치 비교 (V586 기준선 → V589)

| 항목 | V586 기준 | V587 | V588 | **V589 (현재)** |
|---|---|---|---|---|
| 버전 | 9.1.0 | 9.2.0 | 9.3.0 | **9.4.0** |
| Gates | 44/44 | 45/45 | 46/46 | **47/47** |
| ADR | ADR-001~045 | ADR-001~048 | ADR-001~049 | **ADR-001~050** |
| Tests | 5,744+ | 5,760+ | 5,760+(+30) | **5,760+(+55)** |
| LOSDB 레이어 | Facade | Facade | QueryInterface | **+ HealthMonitor** |
| CI | 4-tier | 4-tier | 4-tier | **4-tier** |

---

## 아키텍처 현황 (V589 기준)

```
[Literary OS v9.4.0 LOSDB Stack]

┌─────────────────────────────────────────────┐
│  HybridRetrieverV2 (V589)                   │
│  ├─ BM25Retriever (V438)                    │
│  ├─ DenseRetriever → QdrantBridge (V437)    │
│  └─ BackendHealthMonitor 폴백              │
└─────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────┐
│  QueryInterface (V588)                      │
│  ├─ find_scenes()  SLO 1.0s               │
│  ├─ find_characters()                       │
│  ├─ cross_backend_aggregate()               │
│  └─ health_monitor 폴백 (V589)            │
└─────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────┐
│  LOSDBClient Facade (V586)                  │
│  ├─ SQL  → SQLiteRealAdapter (V582)         │
│  ├─ Vector → VectorRealAdapter (V584)       │
│  └─ Graph  → GraphRealAdapter  (V585)       │
└─────────────────────────────────────────────┘
             ↓
┌─────────────────────────────────────────────┐
│  BackendHealthMonitor (V589)                │
│  ├─ SQL Circuit:    CLOSED/OPEN/HALF_OPEN   │
│  ├─ Vector Circuit: CLOSED/OPEN/HALF_OPEN   │
│  └─ Graph Circuit:  CLOSED/OPEN/HALF_OPEN   │
└─────────────────────────────────────────────┘
```

---

## 신규 ADR 목록 (V587~V589)

| ADR | 제목 | 버전 | Gate |
|---|---|---|---|
| ADR-046 | Gate 계층화 (L0/L1/L2/L3) | V587 | G46 |
| ADR-047 | E2E Prose 정책 | V587 | G46 |
| ADR-048 | doc consistency CI | V587 | G46 |
| ADR-049 | LOSDB QueryInterface | V588 | G47 |
| ADR-050 | BackendHealthMonitor / PartialAvailability | V589 | G48 |

---

## Gate 전체 현황 (G1~G48)

| 계층 | 범위 | 대표 Gate | SLO |
|---|---|---|---|
| L0 | G1~G3 | 핵심 계약 | ≤5s |
| L1 | G4~G10 | DB/LLM Bridge | ≤30s |
| L2 | G11~G45 | 전체 기능 | ≤2m |
| **L1 신규** | **G46~G48** | **E2E/QueryInterface/HealthMonitor** | **≤30s** |

---

## 불변 제약 사항

| 원칙 | 내용 |
|---|---|
| **LLM-0** | `graph_intelligence/`, `predictive/`, `corpus/`, `multiwork/` — 외부 LLM 호출 0건 |
| **DEV_MODE** | 기본값 항상 `"false"` (ADR-034) |
| **Preflight** | 15단계 체크리스트 — 모든 버전 진입 전 필수 |
| **SLO** | QueryInterface 응답 < 1.0s (ADR-049 C1) |
| **GPU 비용** | soft $90 / hard $120 / emergency $150 (M-10) |

---

## 다음 단계 — Phase A 잔여

| SP | 버전 | 내용 | Gate | ADR |
|---|---|---|---|---|
| ✅ A.1 | V588 | QueryInterface + Qdrant | G47 | ADR-049 |
| ✅ A.2 | V589 | BackendHealthMonitor | G48 | ADR-050 |
| ⬜ A.3 | V590 | GPU Adapter (RunPod/LambdaLabs/HFAutoTrain) | G49 | ADR-051 |
| ⬜ A.4 | V591 | EquivalenceTester (MOCK↔REAL 5축) | G50 | ADR-052 |
| ⬜ A.5 | V592 | 코퍼스 협약/폴백 + 5천 신 입수 | — | — |
| ⬜ A.6 | V593 | CorpusValidator + 1만 신 검증 | — | ADR-053 |
| ⬜ A.7 | V594 | LOSConstitution v1.0 | G51 | ADR-054 |
| ⬜ A.8 | V595 | Minimal-CLI v0.1 + Phase A Exit | G52 | ADR-055 |

Phase A 완료 조건 (Gate G52 6축):
- C1: QueryInterface SQL+Vector+Graph < 1초
- C2: BackendHealthMonitor T1~T4 100% PASS
- C3: GPU Adapter 1회 dry-run ≥ 1 epoch
- C4: EquivalenceTester 5축 ≥ 0.95 PASS rate
- C5: 코퍼스 ≥ 1만 신 + Provenance 100%
- C6: CLI Beta 5명 80%+ 5분 내 generate
