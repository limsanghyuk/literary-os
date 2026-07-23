# 03. 검사·판정·패키징

## 구조 계약 검사
파일·파일명·JSON 파싱, exact keyset, ID 유일성, 회차 번호, 장면 연속성, EpisodeMeta 합계, Sequence 완전 타일링, FK, 후보-disposition 1:1을 검사한다. 결과: `STRUCTURAL_CONTRACT_PASS|FAIL`.

## 기계적 의미 검사
EpisodeMeta core 분포, Sequence 마지막 장면과 turn_type, turn_class 파생, EpisodeArc act/sequence 범위와 core 분포, Stage04 합계·ID·회차 범위를 검사한다. 결과: `SEMANTIC_MECHANICAL_PASS|FAIL`.

## 원문 근거 수동 검사
장면 경계와 objective/conflict/outcome/state_change, 시퀀스 행동 단위, 인물·관계의 실제 변화, 인과와 단순 선후 구분, payoff의 setup·발전 과정, 반복 고정 수량·문구 재사용·타 작품 패턴 복제를 직접 대본과 대조한다. 결과: `SOURCE_GROUNDED_MANUAL_PASS|FAIL` 및 감사 근거.

## 블록 게이트
각 최대 8회 블록마다 위 검사를 수행하며 FAIL이면 다음 블록 진행을 금지한다.

## Fresh extraction
패키지에 권위, SourceLock, work_state, 산출물, 검사기, manifest, SHA256SUMS가 포함되어야 한다. 새 임시 경로에 해제해 절대경로나 외부 작업폴더 없이 검사하고 manifest SHA를 대조한다. 결과: `PACKAGE_FRESH_EXTRACTION_PASS|FAIL`.

네 값이 모두 PASS일 때만 `PASS_CANDIDATE_NOT_INTEGRATED`다. 정본 편입은 별도 승인 후 `INTEGRATED_CANONICAL`이며 구형 스키마·누락 파일·외부경로 의존은 `MIGRATION_REQUIRED`다.

필수 패키지 구조:
```
<work_package>/
  authority/DRAMA_ANALYSIS_SINGLE_AUTHORITY_V7/
  source_lock/current/<work_id>.source_lock.v4.json
  work_state.json
  authored/ stage02/ stage03/ stage04/ validation/
  MANIFEST.json SHA256SUMS.txt README.md
```
