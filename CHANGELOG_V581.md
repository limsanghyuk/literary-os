# CHANGELOG — V581 (v8.6.0)

## 개요

LOSDB Phase A 첫 단계: SchemaRegistry + Multi-backend MigrationManager 구현 (ADR-040)

## 신규 모듈

### literary_system/db/ (신규 서브패키지)

| 파일 | 설명 |
|------|------|
| `schema_registry.py` | SchemaRegistry — SQL/Graph/Vector 3-백엔드 스키마 버전 단일 진실 원천 |
| `migration_manager.py` | MigrationManager + 3-어댑터(SQL/Graph/Vector) — MOCK 기본, REAL은 V596+ |
| `__init__.py` | 서브패키지 공개 API |

## 새 Gate

| Gate | ID | 설명 |
|------|----|------|
| G40 | `db_migration_g40` | SchemaRegistry + MigrationManager 생존 검증 (ADR-040) |

## ADR

- **ADR-040**: Multi-backend MigrationManager (LOSDB 기반 레이어 v1.0)

## 테스트

- `tests/test_v581_db_migration.py` — 35개 신규 단위 테스트 (전부 PASS)

## 버그 수정

- `tests/test_v575_hygiene.py` — CI YAML 잡명 오류 수정 (`preflight-step15:` → `preflight:`)

## 버전

- `pyproject.toml`: 8.5.0 → 8.6.0
- Release Gate: 38/38 → **39/39 PASS**
- 총 테스트: 5529+ → **5564+** (35 추가)
