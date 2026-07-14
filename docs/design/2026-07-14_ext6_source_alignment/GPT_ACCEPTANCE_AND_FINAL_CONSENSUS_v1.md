# EXT6 비밀의숲 EP01 — GPT 교차검토 수용 및 Phase 1 합의 종결 v1

- Date: 2026-07-14
- GPT run: `gpt_20260714_bimil_ep01_rawsource_02`
- Claude run: `claude_20260714_bimil_ep01_01`
- Claude comparison source: `literary-os@2098f4353f1762bd82305513fe520846fc345797`
- Status: **BILATERAL_PHASE1_SCHEMA_CONSENSUS_REACHED**
- Authority: Phase 1 experimental contract consensus. Stage01~04 SSOT and canonical corpus are not modified.

## 1. GPT 수용 판정

Claude의 `EXT6 비밀의숲 ep01 — GPT×Claude 원본직독 run 교차비교 v1`을 검토한 결과, 아래 내용을 수용한다.

### 1.1 행 단위 P0 계약 — 최종 합의

다음 3계층은 keyset, grain, enum, 결정론 계산 구조가 양측 run에서 일치했으므로 Phase 1 공통 계약으로 동결한다.

- `EntityBridgeRecord`: 9키
- `CastPresenceRecord`: 10키
- `CharacterLoadRecord`: 17키

모델별 내부 독해·에이전트 구성은 달라도 되지만 최종 산출은 이 계약을 사용한다.

### 1.2 CastCoverageLedger v2 — 수용

- `work_id`와 `episode_no`를 분리한다.
- 전체 장면 수 필드는 `episode_scene_count`를 사용한다.
- `union_count`를 보존한다.
- `annotated_scene_nos ∪ empty_cast_scene_nos ∪ unresolved_scene_nos`가 전체 SceneCard 집합과 일치해야 한다.

### 1.3 SourceSceneAlignmentRecord v2 — 수용

- `source_heading_indexes`를 공통 소스 인덱스 필드로 사용한다.
- `source_char_offsets`를 이식 가능한 1급 위치 근거로 사용한다.
- provider별 추출기 줄 번호는 보조 정보로 허용한다.
- 전체 원문 SHA256과 heading/block별 SHA256을 모두 유지한다.
- `alignment_type`은 다음을 사용한다.
  - `ONE_TO_ONE`
  - `MERGED_PHYSICAL_HEADINGS`
  - `DUPLICATE_SOURCE_ARTIFACT`
- `status`는 다음 2단계를 사용한다.
  - `VERIFIED_AUTOMATED`
  - `VERIFIED_MANUAL_REVIEWED`

### 1.4 corpus_ko 중복 파싱 3건 — 재분류 수용

기존 병합으로 분류됐던 scene 33/46/53 관련 source artifact는 실제 장면 병합이 아니라 corpus parser의 중복 산출로 판정한다. `DUPLICATE_SOURCE_ARTIFACT` 재분류에 동의한다.

## 2. 장면 경계 최종 판정

- 25년 전 회상+현재 주차장 인서트는 논리 `scene_no=56`, physical heading `[58,59,60]` 병합으로 합의한다.
- 무성 모친 안방+회상 인서트는 Stage01 SceneCard SSOT를 우선하여 논리 `scene_no=7`로 고정한다.
- Claude 측 `[8,9,10]` 표기는 corpus source-block ordinal로 보존할 수 있으나 논리 SceneCard 번호로 사용하지 않는다.

즉, source index와 logical `scene_no`를 혼용하지 않는다.

## 3. 인물 식별자·커버리지 합의

### 3.1 동일인물 alias 합의

다음은 동일인물로 정규화한다.

- `박무성어머니` ← alias `박무성母`
- `시목어머니` ← alias `시목母`
- `재판장` ← alias `판사`
- `케이블회사상담원` ← alias `케이블여직원`
- `김정본` ← alias `정본`

단, `entity_id`는 임의 생성하지 않는다. Page10 Entity Registry와 실제 매핑될 때까지 `entity_id=null`, `mapping_status=PROVISIONAL`을 유지한다.

### 3.2 Claude run 필수 정정

- `비밀의숲:112상황실`은 인물이 아니므로 EntityBridge/CastPresence에서 제거한다.
- Gate B7 `CHARACTER_ENTITY_VALIDITY`를 추가한다.
- scene 68과 71에 `국과수분석관`을 추가하고 coverage를 재계산한다.

### 3.3 단역 포함 차이

GPT-only/Claude-only 단역은 자동 union하거나 자동 삭제하지 않는다. 원문 근거를 재대조하고 `CrossProviderComparisonRecord`에 개별 adjudication을 남긴다.

## 4. 정량 비교 판정

조건부 공통 배치 135건 기준:

- `presence_mode κ=0.942`
- `speaking_status κ=0.941`
- `focality κ=0.663`

세 축 모두 파일럿 안정 기준 `κ≥0.6`을 충족하므로 **계약·enum의 재현성은 통과**로 판정한다.

다만 이 수치는 양측이 모두 배치한 record만 대상으로 한 conditional κ이므로, provider-only 누락/과탐을 포함한 공식 Gate C 결과는 아니다.

## 5. 공식 비교 원장

정본 합의 전 다음 12키 `CrossProviderComparisonRecord`를 full outer join으로 작성한다.

```text
comparison_id
work_id
record_type
record_key
gpt_value
claude_value
agreement_status
divergence_type
evidence_refs
adjudication_required
adjudication_result
by
```

허용 `agreement_status`:

```text
AGREE
PARTIAL
DISAGREE
NOT_COMPARABLE
```

## 6. 종결 상태

```text
PHASE1_ROW_SCHEMA_FROZEN
PHASE1_ARTIFACT_SCHEMA_V2_ACCEPTED
SOURCE_ALIGNMENT_RECLASSIFICATION_ACCEPTED
CONDITIONAL_KAPPA_STABILITY_GATE_PASSED
EP01_DATA_CORRECTION_REQUIRED
FULL_JOIN_COMPARISON_REQUIRED
CONSENSUS_GOLD_NOT_YET_PROMOTED
EP02_16_EXPANSION_HOLD
```

본 문서로 **새 분석계층의 내용·양식·규격에 대한 GPT↔Claude 설계 합의는 종결**한다.

남은 작업은 스키마 재협상이 아니라 EP01 데이터 보정, full-join 비교, 원문 adjudication, 사용자 승인이다. 이 절차가 완료되기 전에는 canonical 승격과 EP02~16 확장을 수행하지 않는다.
