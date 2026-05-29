# V584 설계도 — VectorRealAdapter

**버전**: 8.9.0  
**날짜**: 2026-05-20  

---

## 1. 아키텍처

```
literary_system/db/
├── migration_manager.py          # Migration.vector_ops 필드 추가
├── vector_real_adapter.py        # VectorRealAdapter (신규)
│   ├── VectorRecord              # dataclass (id, vector, metadata)
│   ├── _cosine_similarity()      # numpy-optional 유사도 계산
│   ├── _l2_distance()            # numpy-optional L2 거리
│   └── VectorRealAdapter         # BaseMigrationAdapter 구현
└── __init__.py                   # VectorRealAdapter export
```

---

## 2. 데이터 흐름

```
upsert(id, vector, metadata)
  → _validate_dim(vector)
  → _store[id] = VectorRecord(id, vector, metadata)
  → _snapshot = copy(_store)  # rollback 용 스냅샷

search(query, top_k, metric)
  → 전체 _store 순회
  → metric == "cosine": _cosine_similarity(query, v)
  → metric == "l2":    _l2_distance(query, v)
  → heapq.nlargest(top_k, scores)  # top_k 반환

apply(migration)
  → migration.vector_ops가 None → 빈 성공 반환
  → vector_ops 순회:
    op=="upsert"  → self.upsert(...)
    op=="delete"  → self.delete(...)
    op=="save"    → self.save()
  → MigrationResult(success=True, ...)

rollback()
  → _store = _snapshot 복원
  → MigrationResult(success=True, rolled_back=True, ...)
```

---

## 3. numpy-optional 유사도

```python
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

def _cosine_similarity(a: List[float], b: List[float]) -> float:
    if HAS_NUMPY:
        va, vb = np.array(a), np.array(b)
        denom = np.linalg.norm(va) * np.linalg.norm(vb)
        return float(np.dot(va, vb) / denom) if denom > 1e-10 else 0.0
    else:
        dot = sum(x*y for x,y in zip(a,b))
        na = math.sqrt(sum(x*x for x in a))
        nb = math.sqrt(sum(x*x for x in b))
        return dot / (na * nb) if na * nb > 1e-10 else 0.0
```

---

## 4. JSON 영속화 포맷

```json
{
  "dim": 128,
  "metric": "cosine",
  "records": {
    "id_001": {
      "id": "id_001",
      "vector": [0.1, 0.2, ...],
      "metadata": {"source": "doc1"}
    }
  }
}
```

---

## 5. Migration.vector_ops 포맷

```python
migration = Migration(
    migration_id="V584_vec_001",
    description="초기 벡터 데이터 삽입",
    sql="",
    vector_ops=[
        {"op": "upsert", "id": "v1", "vector": [0.1, 0.2], "metadata": {}},
        {"op": "delete", "id": "v_old"},
        {"op": "save"},
    ]
)
```

---

## 6. Gate G43 체크포인트 상세

```python
def _gate_vector_real_adapter_g43():
    # 1) import
    from literary_system.db.vector_real_adapter import VectorRealAdapter, VectorRecord

    # 2) 생성
    adapter = VectorRealAdapter(dim=4)

    # 3) upsert + search
    adapter.upsert("v1", [1.0, 0.0, 0.0, 0.0])
    adapter.upsert("v2", [0.0, 1.0, 0.0, 0.0])
    results = adapter.search([1.0, 0.0, 0.0, 0.0], top_k=1)
    assert results[0][0] == "v1"

    # 4) 코사인 정확도
    r = adapter.search([1.0, 0.0, 0.0, 0.0], top_k=1)
    assert abs(r[0][1] - 1.0) < 1e-6   # 동일 벡터

    # 5) JSON 영속화
    import tempfile, os
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        path = f.name
    adapter2 = VectorRealAdapter(dim=4, path=path)
    adapter2.upsert("x1", [1.0, 0.0, 0.0, 0.0])
    adapter2.save()
    adapter3 = VectorRealAdapter(dim=4, path=path)
    adapter3.load()
    assert adapter3.get("x1") is not None
    os.unlink(path)

    # 6) rollback
    adapter4 = VectorRealAdapter(dim=4)
    adapter4.upsert("r1", [1.0, 0.0, 0.0, 0.0])
    from literary_system.db.migration_manager import Migration
    m = Migration("rb_test", "rollback test", vector_ops=[
        {"op": "upsert", "id": "r2", "vector": [0.0, 1.0, 0.0, 0.0]}
    ])
    adapter4.apply(m)
    adapter4.rollback()
    assert adapter4.get("r2") is None

    # 7) numpy-optional (import 가능 여부와 무관하게 결과 동일)
    from literary_system.db.vector_real_adapter import _cosine_similarity
    score = _cosine_similarity([1.0, 0.0], [1.0, 0.0])
    assert abs(score - 1.0) < 1e-6

    return {"passed": True}
```

---

## 7. 테스트 파일

`tests/test_v584_vector_real_adapter.py` — TC01~TC40 (40개)

주요 TC 분류:
- TC01~TC05: VectorRealAdapter 생성 + 기본 동작
- TC06~TC12: upsert / get / delete / count
- TC13~TC20: search (cosine, L2, top_k, 엣지케이스)
- TC21~TC26: JSON 영속화 / 복원
- TC27~TC31: apply(vector_ops) 통합
- TC32~TC34: rollback
- TC35~TC37: GATE_REGISTRY G43 속성
- TC38~TC40: Gate 카운트 (GATES==42, REGISTRY==42, total_gates==42)

---

## 8. 버전 범프 체크리스트

- [ ] `pyproject.toml`: 8.8.0 → 8.9.0
- [ ] `README.md`: badge 8.9.0
- [ ] `literary_system/db/__init__.py`: VectorRealAdapter export
- [ ] `literary_system/db/migration_manager.py`: vector_ops 필드 추가
- [ ] `literary_system/gates/release_gate.py`: G43 추가
- [ ] `literary_system/gates/gate_registry.py`: vector_real_adapter_g43 등록
- [ ] `docs/adr/ADR-043.md`
- [ ] `docs/adr/INDEX.md`: ADR-043 추가
- [ ] `docs/changelog/CHANGELOG_V584.md`
- [ ] `CHANGELOG_V584.md`
- [ ] `SESSION_INIT.md` 업데이트
