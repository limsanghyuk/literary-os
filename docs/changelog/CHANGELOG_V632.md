# CHANGELOG — V632 (v11.2.0)

**날짜**: 2026-05-26  
**기준선**: V631 (v11.1.0) · 60/60 Gates · 7,246 Tests  
**테마**: SP-C.1 — ConstitutionWeightTracker LOSDB 영속화 + 비파괴 롤백

---

## 신규 파일

### `literary_system/constitution/constitution_weight_tracker.py` (신규)
- **ConstitutionWeightTracker**: LOSDB JSONL 영속화 기반 가중치 버전 관리
  - `save(weights, note)` → version_id 반환
  - `load_latest()` → 최신 ConstitutionWeights 반환
  - `rollback(version_id)` → 비파괴 롤백 (이력 보존)
  - `history()` → 전체 WeightRecord 리스트 (시간순)
  - `latest_record()`, `count()`, `clear()` 보조 메서드
  - 메모리 모드 (`:memory:`) 지원 — 테스트용 파일 I/O 없음
- **WeightRecord** (frozen dataclass)
  - version_id (UUID4), timestamp (ISO-8601 UTC)
  - weights (ConstitutionWeights 스냅샷)
  - entropy (Shannon H(w) bits — 자동 계산)
  - note (저장 이유)
  - `to_dict()` / `from_dict()` 직렬화 지원

### `docs/adr/ADR-099.md` (신규)
- ConstitutionWeightTracker JSONL Append-only 설계 결정
- 비파괴 롤백 채택 이유
- 파일 모드 vs 메모리 모드 비교

### `tests/unit/test_v632_constitution_weight_tracker.py` (신규, +33 TC)
- TC-01~05: save / load_latest 기본
- TC-06~10: history 조회
- TC-11~16: 비파괴 rollback
- TC-17~20: 파일 모드 영속화
- TC-21~24: Shannon 엔트로피 자동 기록
- TC-25~28: count / latest_record / clear
- TC-29~33: 공개 API 및 통합 시나리오

## 수정 파일

### `literary_system/constitution/__init__.py`
- `ConstitutionWeightTracker`, `WeightRecord` 추가 export
- 모듈 docstring: ADR-099 추가

### `literary_system/gates/release_gate.py`
- version: "V631" → "V632"
- docstring 갱신

### `pyproject.toml`
- version: 11.1.0 → 11.2.0

### `tools/test_inventory.json`
- test_count: 7,246 → 7,279 (+33 TC)
- source_hash 재생성

---

## 핵심 지표

| 항목 | V631 | V632 |
|------|------|------|
| 버전 | v11.1.0 | v11.2.0 |
| Gates | 60/60 PASS | 60/60 PASS |
| Tests | 7,246 | 7,279 (+33) |
| ADR | ADR-098 | ADR-099 |

## 다음: V633 — PatternLibraryV2 (압축+랭킹) / ADR-100
