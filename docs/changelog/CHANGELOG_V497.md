# Literary OS CHANGELOG — V492~V497 (Phase 2 SubPhase 3)

릴리즈 날짜: 2026-05-16
버전: 4.9.2
이전 버전: V491 (4.9.1)

---

## 신규 기능 (V492~V497)

### V492 — TraceQualityFilterSP3
- `literary_system/slm/trace_quality_filter_sp3.py` 신설
- `SP3Record` — dict 기반 레코드 타입 (from_dict / to_dict)
- `DedupReport` — MinHash 중복 제거 상세 보고
- `SP3FilterResult` — 필터링 결과 (split: train/val/test)
- `TraceQualityFilterSP3.run()` — 6단계 파이프라인
  1. dict → SP3Record 변환
  2. 품질 점수 필터 (min_quality_score)
  3. 티어/opt-in/라이선스 필터 (ADR-008)
  4. PII 마스킹 (인라인 정규식 4패턴)
  5. MinHash 중복 제거 (64 permutations, shingle_size=3)
  6. Stratified train/val/test 분할
- `export_jsonl()` — JSONL 직렬화 지원

### V493 — PIIScrubberSP3
- `literary_system/slm/pii_scrubber_sp3.py` 신설
- 한국어 PII 패턴 10종: 주민번호, 전화번호, 일반전화, 계좌번호, 사업자번호, 우편번호, 이메일, 여권번호, 신용카드, IP주소
- `ScrubDetailSP3` — 단일 레코드 스크럽 결과 (is_clean / total_removed / summary)
- `DatasetScrubReport` — 데이터셋 레벨 통계 (scrub_rate / category_totals)
- `PIIScrubberSP3.scrub()` — 단일 텍스트 PII 제거
- `PIIScrubberSP3.scrub_batch()` — 리스트 일괄 스크럽
- `PIIScrubberSP3.scrub_dataset()` — dict 레코드 데이터셋 레벨 처리
- 한국 이름 패턴 (scrub_names=True 옵션)
- active_categories 선택적 활성화 지원

### V494 — DatasetCardGenerator
- `literary_system/slm/dataset_card_generator.py` 신설
- `DatasetStats` — 통계 요약 (텍스트 길이, 품질, 티어 분포, PII/dedup 카운트)
- `DatasetCard` — HuggingFace DatasetCard 호환
  - `to_yaml_header()` — YAML front-matter 생성
  - `to_markdown()` — 전체 마크다운 카드
  - `to_dict()` — JSON 직렬화
- `DatasetCardGenerator` — 설정 가능한 생성기
  - 기본 언어: ko, 기본 라이선스: cc-by-sa-4.0
  - `generate(train, val, test, pii_scrubbed, dedup_removed) → DatasetCard`
  - `save(card, output_dir) → {"markdown": ..., "json": ...}`
- ADR-008 준수: 라이선스·출처 의무 기재

### V495 — SyntheticAugmentorSP3
- `literary_system/slm/synthetic_augmentor_sp3.py` 신설
- 3종 전략: paraphrase / back_translation / style_transfer
- `AugmentedRecord` — synthetic=True 플래그 의무 부착 (ADR-008)
- `AugmentResultSP3` — total_count / success_rate / all_records() / summary()
- `SyntheticAugmentorSP3.augment()`:
  - `strategy` 단일 전략 / None 시 라운드로빈
  - `target_count` 목표 레코드 수 기반 생성
- `select_candidates()` — min_quality 기반 증강 후보 선택
- 실 LLM 어댑터 주입 지원 (실패 시 Mock 폴백)
- seed 기반 결정적(deterministic) 동작

### V496 — SP3 테스트 4종 (V492~V495 대상)
- `tests/test_v492_trace_quality_filter_sp3.py` — 21 tests
  - TestSP3Record (3), TestMinHash (3), TestTraceQualityFilterSP3 (15)
- `tests/test_v493_pii_scrubber_sp3.py` — 40 tests
  - TestScrubDetailSP3 (5), TestDatasetScrubReport (3), TestKoreanPIIPatterns (9),
    TestPIIScrubberSP3 (12), TestScrubDataset (9), TestActiveCategoryFilter (2)
- `tests/test_v494_dataset_card_generator.py` — 40 tests
  - TestDatasetStats (4), TestDatasetCard (11), TestDatasetCardGenerator (14),
    TestDatasetCardGeneratorSave (6)
- `tests/test_v495_synthetic_augmentor_sp3.py` — 38 tests
  - TestAugmentedRecord (6), TestAugmentResultSP3 (6), TestSupportedStrategies (5),
    TestAugmentBasic (6), TestAugmentSingleStrategy (5), TestAugmentTargetCount (6),
    TestSelectCandidates (5), TestLLMAdapterInjection (2), TestDeterminism (2)

### V497 — Gate 24 + 통합 릴리즈
- `literary_system/gates/gate24_slm_sp3.py` 신설
  - SP3 4개 모듈 33개 심볼 검증
  - ADR-008 준수 3항목 검증 (PII stats / license field / synthetic flag)
- `literary_system/gates/release_gate.py` 업데이트
  - Gate 24 등록: `("slm_sp3_integration", "SP3 SLM 수출 레이어 생존 (Gate 24)", ...)`
  - 총 게이트: 22개 (Gate 24까지)
  - version → V497
- `pyproject.toml`: 4.9.2
- 5개 통합 테스트 V497 allowlist 추가

---

## 버그 수정

| ID | 내용 |
|----|------|
| BF-V497-01 | pii_scrubber_sp3.py 한국 이름 정규식 따옴표 오류 수정 (`\b"` → `\b'`) |
| BF-V497-02 | test_v493: active_categories count 9→10 (전화번호/일반전화 독립 카운트) |

---

## ADR 준수 상태

| ADR | 내용 | 상태 |
|-----|------|------|
| ADR-008 | Data Hygiene — PII+quality+opt-in+license 4단계 필터 | ✅ Gate 24 검증 |
| ADR-008 | synthetic=True 플래그 의무 부착 | ✅ Gate 24 검증 |
| ADR-008 | DatasetCard 라이선스 필드 의무 기재 | ✅ Gate 24 검증 |

---

## 테스트 현황

| 항목 | 수치 |
|------|------|
| 전체 PASS | 4,808 |
| SKIP | 20 |
| FAIL | 0 |
| 신규 테스트 (SP3) | 139 |
| 전체 게이트 | 22/22 PASS |
