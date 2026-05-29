# Literary OS V497 Hotfix — 무결성 점검 4건 수정

릴리즈 날짜: 2026-05-16
버전: 4.9.2 (V497-HF)
트리거: v497_sp3_proof_report.svg 110항목 점검 결과 반영

---

## 수정 내역

### Bug B1 — PIIScrubberSP3 신용카드 패턴 우선순위 오류 (즉시 수정)
**파일**: `literary_system/slm/pii_scrubber_sp3.py`

**원인**: `_PATTERNS` 딕셔너리에서 `계좌번호` 패턴(`\d{3,6}-\d{2,6}-\d{4,9}`)이
`신용카드` 패턴(`(?:\d{4}[-\s]){3}\d{4}`)보다 먼저 적용되어
`1234-5678-9012-3456`이 `[계좌번호]6`으로 잘못 마스킹.

**수정**: `_PATTERNS` 처리 순서 재배치 — 국제 PII(이메일/여권/신용카드/IP) → 한국 PII(주민/전화/사업자) → 계좌번호 → 우편번호 순으로 변경.
신용카드 정규식도 `[-\s]` → `[-\s]{3}\d{4}` 로 4-4-4-4 패턴 명확화.

**검증**: `scrub("카드번호: 1234-5678-9012-3456")` → `[카드번호]` ✅

---

### Bug B2 — test_low_similarity_miss 비결정론적 실패 (테스트 격리 수정)
**파일**: `tests/test_v454_semantic_cache_redis.py`

**원인**: `perfect_embed()`가 해시 기반 벡터를 생성하므로 "Python programming tutorial"과
"스파게티 요리 레시피"가 우연히 높은 코사인 유사도를 가질 수 있음.
격리 실행 시 FAIL, 전체 실행 시 통과하는 비결정론적 동작.

**수정**: `test_low_similarity_miss`에 명시적 직교 벡터 반환 `isolated_embed` 사용.
저장 텍스트 → `[1.0, 0.0, 0.0, 0.0]`, 조회 텍스트 → `[0.0, 1.0, 0.0, 0.0]` (코사인=0.0).

**검증**: 격리 실행 / 전체 실행 모두 PASS ✅

---

### Design Gap G1 — DatasetCardGenerator 독점 라이선스 미차단 (ADR-008 강화)
**파일**: `literary_system/slm/dataset_card_generator.py`

**원인**: `generate(license="proprietary")`로 DatasetCard가 생성됨.
ADR-008은 CC_BY/CC_BY_SA/PUBLIC_DOMAIN 계열만 허용.

**수정**:
- `ALLOWED_LICENSES` 클래스 상수 추가 (12개 허용 라이선스 명시)
- `generate()` 진입 시 `self._license not in ALLOWED_LICENSES` → `ValueError` 발생
- 오류 메시지에 `ADR-008 위반` 명시

**신규 테스트** (test_v494_dataset_card_generator.py):
- `test_generate_proprietary_license_raises` ✅
- `test_generate_all_rights_reserved_raises` ✅
- `test_generate_internal_license_allowed` ✅

**검증**: `DatasetCardGenerator(license="proprietary").generate()` → `ValueError: ADR-008 위반` ✅

---

### Design Gap G2 — Gate24 반환 키 명세 불일치 (문서 통일)
**파일**: `literary_system/gates/gate24_slm_sp3.py`

**원인**: `run_gate24()` 반환 딕셔너리에 `symbols_checked` / `symbols_passed` 키 없음.
실제로는 `symbols_verified`(리스트) + `count`(정수)만 존재.

**수정**: `_gate_slm_sp3_survival()` 반환에 `symbols_checked` + `symbols_passed` 추가.
모두 `count`와 동일한 값을 갖는 별칭으로 명세 통일.

**신규 테스트** (tests/test_v497_gate24_contract.py — 7개):
- `test_gate24_has_symbols_checked` ✅
- `test_gate24_has_symbols_passed` ✅
- `test_run_gate24_passes` / `test_gate24_adr008_checks` 외 5개 ✅

---

### 기타 수정
**파일**: `pyproject.toml`
- `description`: `"Literary OS V483 — SP1~SP5 Full Build"` → `"Literary OS V497 — Phase2 SP1~SP3 Full Build (RAG+SLM Export Layer)"`

---

## 테스트 결과

| 항목 | V497 원본 | V497-HF |
|------|-----------|---------|
| PASS | 4,808 | **4,818** |
| FAIL | 0 (격리 시 1) | **0** |
| SKIP | 20 | 20 |
| 신규 테스트 | — | **+10** |
| Release Gate | 22/22 | 22/22 |

---

## 수정 파일 목록

| 파일 | 수정 내용 |
|------|-----------|
| `literary_system/slm/pii_scrubber_sp3.py` | B1: 신용카드 패턴 우선순위 수정 |
| `literary_system/slm/dataset_card_generator.py` | G1: ADR-008 라이선스 검증 추가 |
| `literary_system/gates/gate24_slm_sp3.py` | G2: symbols_checked/symbols_passed 키 추가 |
| `tests/test_v454_semantic_cache_redis.py` | B2: 격리 embed_fn으로 교체 |
| `tests/test_v494_dataset_card_generator.py` | G1: 라이선스 검증 테스트 3개 추가 |
| `tests/test_v497_gate24_contract.py` | G2: Gate24 계약 테스트 7개 신설 |
| `pyproject.toml` | description V497 반영 |
