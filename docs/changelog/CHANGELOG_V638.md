# CHANGELOG V638 — literary-os v11.8.0

**릴리즈**: 2026-05-26  
**테마**: SP-C.1 — ContaminationDetector (훈련 데이터 오염 탐지기, ADR-080)  
**이전 버전**: V637 (v11.7.0, ADR-079, ConstitutionEvalV2)

---

## 신규 파일

### literary_system/constitution/contamination_detector.py (406줄)
- **ContaminationFlag**: dataclass — flag_id, severity, detail
- **ContaminationReport**: dataclass — report_id(UUID4), detected_at, dataset_id, sample_count, flags, contaminated, contamination_rate, detector_id, note
  - `summary()` → 1줄 요약 문자열
  - `to_dict()` / `from_dict()` 직렬화
- **ContaminationDetector**: LOSDB JSONL append-only 영속화
  - `scan(dataset_id, sample_count, ...)` → ContaminationReport
  - `batch_scan(items, ...)` → List[ContaminationReport]
  - `history()` / `last_report()` / `contaminated_reports()` / `contamination_rate()` / `reports_by_dataset()` / `count()` / `clear()`
  - 메모리 모드(`:memory:`) + 파일 모드(JSONL append)
- **탐지 유형 4종**: LABEL_NOISE / NEAR_DUPLICATE / DISTRIBUTION_SHIFT / POISON_PATTERN
- **임계값 상수**: LABEL_NOISE_THRESHOLD=0.05, NEAR_DUPLICATE_THRESHOLD=0.10, DISTRIBUTION_SHIFT_THRESHOLD=2.0, POISON_THRESHOLD=0.01
- **LLM-0 원칙 완전 준수**

## 수정/신규 파일
- `literary_system/constitution/contamination_detector.py` (신규)
- `literary_system/constitution/__init__.py` (ContaminationDetector API 공개)
- `docs/adr/ADR-080.md` (신규)
- `docs/changelog/CHANGELOG_V638.md` (본 파일)
- `manifests/MANIFEST_V638.md` (신규)
- `pyproject.toml` — 11.7.0 → 11.8.0
- `tools/test_inventory.json` — 7,478 TC

## 신규 TC (+33)
- `tests/unit/test_v638_contamination_detector.py` — TC-01~33, 33/33 PASS

## DEV_PROTOCOL_v2.0 준수
- Preflight 12단계 정식 적용 (Step 1~12 완료)
- 중복 클래스 없음 확인 (ContaminationDetector)
- LLM-0 위반 0건
- 핵심 클래스 생존 매트릭스 8/8 ✅

## 버전 범프
- `pyproject.toml`: 11.7.0 → **11.8.0**

## V637 기준선
V637 (v11.7.0, 61 Gates, 7,445 Tests, ADR-079)
