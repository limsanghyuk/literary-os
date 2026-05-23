# CHANGELOG — V576 (Test Fortification)

**버전**: 8.1.0  
**날짜**: 2026-05-19  
**이전 버전**: V575 (8.0.0)  
**로드맵**: V575~V580 안정화 — Week 2/7

---

## 개요

V576은 테스트 커버리지 강화 릴리즈입니다. 0% 커버리지 파일 단위 테스트를 추가하고, 릴리즈 게이트를 31→33개로 확장했습니다.

**테스트**: 5,483 → 5,529 PASS (+46)  
**게이트**: 31 → 33 Gates (G33 SchemaRoundTrip, G34 AuthRegression 신설)

---

## 변경 사항

### 1. 신규 테스트 파일 (TC-01~46, 46개 케이스)

**파일**: `tests/test_v576_coverage.py`

| 그룹 | 테스트 | 대상 모듈 |
|------|--------|----------|
| TC-01~07 | MultiWorkCore, WorkProject, WorkSession FSM | `literary_system/multiwork/multi_work_core.py` |
| TC-08~10 | MultiWorkOrchestrator (create/session/snapshot) | `literary_system/multiwork/multi_work_orchestrator.py` |
| TC-11~13 | SharedCharacterDB (add/relation/arc) | `literary_system/multiwork/shared_character_db.py` |
| TC-14~16 | SharedWorldDB (location/lore/stats) | `literary_system/multiwork/shared_world_db.py` |
| TC-17~18 | PNECore, PatternLibrary | `literary_system/predictive/pne_core.py` |
| TC-19~23 | DebtPredictor (predict/risk/prob/sklearn) | `literary_system/predictive/debt_predictor.py` |
| TC-24~26 | PreemptiveGate (instantiate/evaluate/count) | `literary_system/predictive/preemptive_gate.py` |
| TC-27~28 | FeedbackLearner (record/precision) | `literary_system/predictive/feedback_learner.py` |
| TC-29~30 | SchemaEnvelope (make_envelope/required) | `literary_system/schemas/envelope.py` |
| TC-31~32 | PacketValidator (pass/missing) | `literary_system/schemas/validator.py` |
| TC-33~35 | Definitions (PACKET_REQUIRED_FIELDS/COMMON) | `literary_system/schemas/definitions.py` |
| TC-36 | CharacterLedger fields | `literary_system/schemas/character_ledger.py` |
| TC-37~42 | AuthRegression G34 (DEV_MODE 6항목) | `apps/studio_api/auth/middleware.py` |
| TC-43~46 | SchemaRoundTrip G33 (envelope/dataclass) | 복합 |

### 2. 릴리즈 게이트 확장

**파일**: `literary_system/gates/release_gate.py`

| 게이트 | ID | 설명 |
|--------|-----|------|
| G33 | `schema_roundtrip_g33` | SchemaRoundTrip: envelope JSON 직렬화·WorkProject asdict 무결성 |
| G34 | `auth_regression_g34` | AuthRegression: DEV_MODE 기본값=false 회귀 방지 (ADR-034) |

**결과**: 33/33 Gates PASS

### 3. 버전 메타데이터

- `pyproject.toml`: `8.0.0` → `8.1.0`
- description: V576 Test Fortification 반영

---

## 검증

```
pytest: 5529 passed, 22 skipped
Release Gate: 33/33 PASS
```

---

## 다음 릴리즈 (V577)

V577: LLM Adapter Consolidation — 어댑터 계층 통합 및 중복 제거
