# V586 설계도 — LOSDBClient

## 클래스 다이어그램

```
LOSDBClientRecord(dataclass)
  id: str
  backend: BackendType
  label: str
  metadata: Dict[str, Any]

LOSDBClient
  __init__(sql=None, vector=None, graph=None)
  available_backends() -> List[BackendType]
  check_all_connections() -> Dict[str, bool]
  query_by_label(backend, label) -> List[LOSDBClientRecord]
  cross_query(backends, label) -> List[LOSDBClientRecord]
  get_backend(backend_type) -> Optional[BaseMigrationAdapter]
  schema_info() -> Dict[str, Any]
```

## 파일 위치

- `literary_system/db/losdb_client.py` (신규)
- `literary_system/db/__init__.py` (수정 — LOSDBClient, LOSDBClientRecord export)
- `literary_system/gates/release_gate.py` (수정 — G45 추가)
- `literary_system/gates/gate_registry.py` (수정 — G45 등록)
- `tests/test_v586_losdb_client.py` (신규 — 44개 테스트)
- `docs/adr/ADR-045.md` (신규)

## G45 체크포인트 (8개)

1. import LOSDBClient, LOSDBClientRecord
2. 인스턴스 생성 (어댑터 없음), available_backends()==[]
3. SQL 어댑터 1개 연결, available_backends()==[SQL]
4. Vector 어댑터 연결, query_by_label(VECTOR, label)
5. Graph 어댑터 연결, query_by_label(GRAPH, label)
6. 3개 어댑터 모두 연결, cross_query([SQL,VECTOR,GRAPH], label)
7. check_all_connections() 반환 구조 검증
8. schema_info() 반환 구조 검증
