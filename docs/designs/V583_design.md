# V583 설계도 — LOSDB Phase B: MigrationEngine 통합 오케스트레이터

## 아키텍처

```
MigrationEngine
    ├── adapters: Dict[str, BaseMigrationAdapter]
    ├── execute(plan: MigrationPlan) → MigrationExecutionRecord
    └── rollback_plan(plan: MigrationPlan) → MigrationExecutionRecord

MigrationPlan
    ├── plan_id: str
    ├── migrations: List[Migration]
    ├── target_adapters: List[str]   # ["sql", "graph", "vector"]
    └── description: str

MigrationExecutionRecord
    ├── plan_id: str
    ├── executed_at: str             # ISO 8601
    ├── results: List[Dict]
    ├── success: bool
    ├── rolled_back: bool
    └── to_json() → str
```

## 파일 구조

```
literary_system/db/
├── __init__.py            (수정: MigrationEngine, MigrationPlan, MigrationExecutionRecord 추가)
├── migration_engine.py    (신규)
├── sql_real_adapter.py    (기존)
└── cli.py                 (기존 — 수정 없음)
```

## Gate G42

- ID: migration_engine_g42
- ADR: ADR-042
- Version: V583
- Layer: L1
- 검증 항목: import / execute / rollback-chain / JSON 직렬화

## 총 Gates: 41 (G1~G42, G40=db_migration, G41=sql_real_adapter, G42=migration_engine)
