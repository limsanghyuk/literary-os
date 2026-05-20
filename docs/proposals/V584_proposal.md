# V584 개발 제안서 — VectorRealAdapter (LOSDB Phase B 2단계)

**버전**: 8.9.0  
**날짜**: 2026-05-20  
**상태**: 합의 완료  
**작성자**: CSA · CSC · CSPE 3인 전문가 합의  

---

## 1. 배경

V581에서 LOSDB Phase A(Mock 어댑터 3종)를, V582에서 SQLiteRealAdapter(sql 레이어 REAL 구현)를,
V583에서 MigrationEngine(통합 오케스트레이터)을 완성했다.

LOSDB 3-layer 구조:

```
Vector Layer  →  [V581: VectorMockAdapter] → [V584: VectorRealAdapter ← 현재]
Graph  Layer  →  [V581: GraphMockAdapter ] → [V585: GraphRealAdapter  ]
SQL    Layer  →  [V581: SQLMockAdapter   ] → [V582: SQLiteRealAdapter ✅]
```

V584의 목표는 **vector 레이어의 REAL 구현**이다.

---

## 2. 핵심 요구사항

### 2.1 기능 요구사항

- `upsert(id, vector, metadata)` — 벡터 + 메타데이터 삽입/갱신
- `search(query_vector, top_k, metric)` — 유사도 검색 (코사인/L2)
- `delete(id)` — 벡터 삭제
- `get(id)` — 단건 조회
- `rollback()` — 마지막 apply() 이전 상태로 복원
- `apply(migration)` — Migration.vector_ops 처리
- `JSON 영속화` — 파일 기반 저장/복원

### 2.2 비기능 요구사항

- **LLM-0 원칙 엄수**: 외부 LLM 호출 0건
- **numpy-optional**: numpy 없이도 순수 Python fallback으로 동작
- **stdlib 우선**: 핵심 로직은 stdlib만 사용 (json, math, os)
- **DEV_MODE 기본값 "false"** 유지 (ADR-034)
- **하위 호환성**: Migration 데이터클래스 변경 시 기존 테스트 파손 없음

---

## 3. 제안 구현

### 3.1 파일 구조

```
literary_system/db/
  vector_real_adapter.py     # VectorRealAdapter (신규)
  migration_manager.py       # Migration.vector_ops 필드 추가
  __init__.py                # VectorRealAdapter export 추가
```

### 3.2 VectorRealAdapter 인터페이스

```python
@dataclass
class VectorRecord:
    id: str
    vector: List[float]
    metadata: Dict[str, Any] = field(default_factory=dict)

class VectorRealAdapter(BaseMigrationAdapter):
    def __init__(self, dim: int, path: Optional[str] = None, metric: str = "cosine")
    def upsert(self, id: str, vector: List[float], metadata: Optional[Dict] = None) -> None
    def search(self, query: List[float], top_k: int = 10, metric: Optional[str] = None) -> List[Tuple[str, float]]
    def delete(self, id: str) -> bool
    def get(self, id: str) -> Optional[VectorRecord]
    def count(self) -> int
    def save(self) -> None          # JSON 파일 저장
    def load(self) -> None          # JSON 파일 복원
    def apply(self, migration: Migration) -> MigrationResult
    def rollback(self) -> MigrationResult
```

### 3.3 Migration.vector_ops 확장

```python
@dataclass
class Migration:
    migration_id: str
    description: str
    sql: str = ""
    vector_ops: Optional[List[Dict[str, Any]]] = None  # 신규 (기본값 None)
    rollback_sql: str = ""
    version: str = "1.0.0"
```

---

## 4. Gate G43

**이름**: `vector_real_adapter_g43`  
**ADR**: ADR-043  
**Layer**: L1  
**체크포인트** (7개):
1. import OK
2. VectorRealAdapter 생성 OK (dim, path, metric)
3. upsert + search OK (cosine + L2)
4. 코사인 유사도 정확도 (동일 벡터 1.0, 수직 0.0)
5. JSON 영속화/복원 OK
6. rollback (apply 전 상태 복원) OK
7. numpy-optional fallback OK

---

## 5. 리스크 및 대응

| 리스크 | 대응 |
|--------|------|
| numpy CI 미설치 | 순수 Python fallback 구현 (math.sqrt + dot product) |
| Migration 하위 호환성 파손 | vector_ops 기본값 None 강제 |
| 파일 경로 traversal | os.path.abspath() 정규화 |
| 정밀도 차이 (Python vs numpy) | 허용 오차 1e-6 이내 |

---

## 6. 버전 정보

- **현재**: V583 8.8.0
- **목표**: V584 8.9.0
- **태그**: v8.9.0-V584
- **브랜치**: 584-vector-real-adapter
