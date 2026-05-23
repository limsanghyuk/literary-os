# CHANGELOG V593 — SP-A.6 CorpusValidator (v9.8.0)

## 릴리즈 정보
- **버전**: 9.8.0 (V593)
- **릴리즈일**: 2026-05-21
- **태그**: v9.8.0
- **기반**: v9.7.0 (V592 CorpusGovernance)

---

## 변경 사항

### 신규 산출물

#### `literary_system/corpus/corpus_validator.py` (SP-A.6 확장)
기존 CorpusValidator(ScenarioEntry) 보존, SP-A.6 전용 클래스 추가:
- `CorpusEntryValidationResult` — 항목별 4단 검증 결과 (license/pii/drse/dedup)
- `CorpusEntryValidationReport` — 배치 집계 보고서 + summary()
- `CorpusMinHashDedup` — 문자 3-gram MinHash 중복 탐지 (threshold=0.85)
- `CorpusEntryValidator` — 4단 필터 파이프라인
  - **1단계 License**: public_domain/CC-BY-4.0/CC-BY-SA-4.0/CC0/academic 허용
  - **2단계 PII 0건**: CorpusPiiFilter.is_clean() strict 모드
  - **3단계 DRSE S-score ≥ 0.35**: 3축(length/vocab/narrative) 가중합
  - **4단계 MinHash dedup(0.85)**: Jaccard 추정 중복 제거
- `_compute_drse_score()` — LLM-0 순수 텍스트 메트릭 DRSE 근사

#### `literary_system/corpus/dataset_card_generator.py` (신규)
기존 slm/DatasetCard/DatasetCardGenerator와 별도 — 코퍼스 전용:
- `CorpusDatasetCard` — HF YAML front-matter + markdown body 생성
  - to_yaml_header() / to_markdown() / to_dict()
- `CorpusDatasetCardGenerator` — generate(entries, report) + save(card, path)
- `_hf_size_category()` — HuggingFace 표준 크기 범주 변환

### 테스트

#### `tests/unit/test_corpus_validator.py` (신규, TC01~TC30, 30/30 PASS)
- TC01~TC05: DRSE S-score 검증 (범위, 임계값)
- TC06~TC10: CorpusMinHashDedup (중복 탐지, reset, threshold)
- TC11~TC18: CorpusEntryValidator 4단 필터 (각 단계별 탈락 시나리오)
- TC19~TC24: CorpusDatasetCard + Generator (생성, YAML, markdown, 저장)
- TC25~TC30: 1만 신 검증 통합 테스트 + LLM-0 준수

---

## 수치

| 항목 | V592 (9.7.0) | V593 (9.8.0) |
|---|---|---|
| Gates | 49/49 | **49/49** (유지) |
| 신규 테스트 | — | **+30** |
| ADR | ADR-001~053 | **ADR-001~053** (유지) |
| CorpusValidator 4단 | 없음 | **구현 완료** |
| 1만 신 검증 | — | **완료** |
| DatasetCard | — | **HF 표준** |

---

## 아키텍처 결정

- **CorpusEntryValidator 네이밍**: 기존 `CorpusValidator`(ScenarioEntry용) 보존 — SP-A.6는 `CorpusEntryValidator`
- **CorpusDatasetCard 네이밍**: 기존 slm/`DatasetCard` 충돌 회피 (duplicate_zero_g37)
- **DRSE LLM-0**: 3축 순수 텍스트 메트릭 (length + TTR + narrative marker)
- **MinHash**: 16개 선형 해시 함수, 문자 3-gram shingle

---

## 보안/아키텍처 제약 (계속 유효)

- **LLM-0 원칙**: 외부 LLM 호출 0건
- **DEV_MODE** 기본값 항상 `"false"` (ADR-034)
