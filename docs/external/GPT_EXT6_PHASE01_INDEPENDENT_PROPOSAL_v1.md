# GPT 독립 설계안 — EXT6 Phase 01 계약·이중 분석 트랙

- 문서 ID: `GPT-EXT6-PHASE01-INDEPENDENT-v1`
- 상태: `GPT_INDEPENDENT_DRAFT_LOCKED`
- 작성일: 2026-07-14
- 작성 주체: GPT 트랙
- 전달 대상: Claude 문학창작 모델 허브
- 원본 저장소: `limsanghyuk/v1700-literary-os`
- 원본 경로: `docs/proposals/GPT_EXT6_PHASE01_INDEPENDENT_PROPOSAL_v1.md`
- 원본 PR: `v1700-literary-os#73`
- 원본 blob SHA: `d1b6b7e7153e234a1714580df9eb479a4aab321b`
- 전달 목적: Claude 독립안과 비교하기 위한 GPT 측 봉인 설계안 제공
- 권위 경계: 본 문서는 제안서이며 Stage01~04 정본을 변경하거나 Stage05를 공식화하지 않는다.
- 독립성 주의: Claude 독립 초안이 아직 봉인되지 않았다면 먼저 Claude안을 봉인한 뒤 본 문서를 열람하는 것을 원칙으로 한다.

---

## 0. 결론

Phase 01의 목적은 새 문학 분석층을 곧바로 대규모 저작하는 것이 아니다. 다음 네 가지를 먼저 고정하는 것이다.

1. 기존 Stage01~04를 훼손하지 않는 EXT6 포착·파생·종합 시점
2. P0인 EntityBridge / CastPresence / CharacterLoad의 정확 계약
3. GPT와 Claude가 같은 원문을 독립 분석할 때 결과를 덮어쓰지 않는 이중 트랙 계약
4. 두 결과를 비교·판정하되 자동 평균이나 무근거 병합을 금지하는 합의 절차

최종 권고:

```text
Phase01 = 계약·식별자·포착시점·이중트랙·검증기 설계
Phase02 = 비밀의숲 P0 파일럿
Phase03 = GPT/Claude 독립 결과 비교
Phase04 = 사용자 승인 합의 계약 동결
```

---

## 1. 비타협 원칙

### 1.1 기존 분석 권위 불변

```text
SourceLock
→ Stage01 SceneCard
→ Stage02 SequenceBlueprint
→ Stage03 EpisodeArc / CharacterArc / RelationshipArc / LocalEdge / PayoffCandidate
→ Stage04 CrossEpisodeEdge / FullSeriesArc / Disposition
```

EXT6는 위 파일의 exact keyset에 임의 필드를 추가하지 않는다.

EXT6는 다음 세 권위를 분리한다.

```text
authored_*  = 원문 직접독해로 작성한 근거 substrate
derived_*   = authored substrate에서 결정론적으로 계산한 값
advisory_*  = Critic/EAT8D/Formula가 생성하는 평가·추천 신호
```

### 1.2 직접독해 의미 저작

GPT와 Claude는 각자 원문을 직접 읽는다. 한 모델의 분석 결과를 다른 모델이 원문 대신 입력으로 사용해서는 안 된다.

```text
원문 직접독해 = 필수
상대 모델 산출물 대리독해 = 금지
```

### 1.3 이중 분석 결과의 독립 보존

```text
GPT 결과 ≠ Claude 결과
```

서로 다르다는 이유로 하나를 즉시 오류로 판정하지 않는다. 사실 오류, 계약 오류, 식별자 오류, 유효한 해석 차이를 분리한다.

### 1.4 자동 병합 금지

두 모델 결과를 다음 방식으로 정본화하지 않는다.

```text
다수결
문자열 평균
단순 union
한쪽 우선 덮어쓰기
점수 높은 모델 자동 채택
```

합의본은 근거 장면 재대조와 사용자 승인 후 별도로 생성한다.

### 1.5 Python/Codex 의미 생성 금지

Python과 Codex는 다음만 담당한다.

```text
추출
경계 고정
직렬화
결정론 계산
검증
비교표 생성
패키징
해시
```

의미 필드의 최초 저작은 GPT 또는 Claude의 직접독해로만 수행한다.

---

## 2. Phase 01 범위

### 2.1 포함

- 공통 식별자와 provider-neutral 경로
- AnalysisRunManifest
- EntityBridgeRecord
- CastPresenceRecord
- CastCoverageLedger
- CharacterLoadRecord
- Stage 부착 시점
- Gate A/B 계약
- GPT↔Claude 비교 프로토콜
- positive fixture
- negative fixtures
- validator 요구사항
- 사용자 승인 이전 권위 상태

### 2.2 제외

- CharacterVoice 전체 저작
- MotifLedger 전체 저작
- AffectRegister 전체 저작
- ThematicStance 전체 저작
- 공식 Stage05 선언
- 300편 전체 적용
- 자동 학습 승격
- CANONICAL 승격

Phase 01에서는 P0 계약과 이중 분석 기반만 고정한다.

---

## 3. 분석 포착 시점

### 3.1 SourceLock 이후 EXT preflight

의미 분석 전에 다음을 준비한다.

- `work_slug`
- `character_key` 생성 규칙
- alias normalization policy
- EXT contract version
- provider run id
- EntityBridge staging
- 공통 SourceLock SHA256
- 전체 회차의 8~10회 블록 분할
- 각 회차 Q1→Q2→Q3→Q4 범위

### 3.2 Stage01 Q1→Q4 직접독해 직후

각 quarter에서 SceneCard를 먼저 저작한 뒤 같은 원문 범위에서 별도 sidecar로 CastPresence를 포착한다.

```text
원문 독해
→ Stage01 SceneCard 저작
→ 동일 quarter 짧은 재확인
→ CastPresence 저작
→ CastCoverage 기록
→ QuarterAudit
```

Stage01 SceneCard 9키에는 EXT 필드를 넣지 않는다.

중요:

```text
Stage01 스키마 확장 = 금지
Stage01 독해 시점의 별도 sidecar 포착 = 허용·권장
```

### 3.3 Stage02 이후

SequenceBlueprint가 확정되면 다음 계산 기반이 생긴다.

```text
present_sequence_count
시퀀스별 등장 분포
시퀀스별 초점 분포
```

다만 CharacterLoad 최종 계산은 EpisodeArc의 `act_structure`가 필요한 관계로 Stage03 이후 실행한다.

### 3.4 Stage03 이후

```text
CastPresence
+ SequenceBlueprint
+ EpisodeArc act_structure
→ CharacterLoad 결정론 계산
```

회차 잠금 전에 Gate A/B를 통과해야 한다.

정확 순서:

```text
EP01 Q1~Q4
→ Stage01
→ Stage02
→ Stage03
→ CharacterLoad compiler
→ Gate A/B
→ EP01 LOCKED_PASS
→ EP02 Q1
```

### 3.5 8~10회 블록 종료

전반부·후반부 또는 균형 분할 블록이 끝나면 개별 회차 PASS를 단순 합산하지 않는다.

```text
Stage01~03 통합검증
+ CastPresence 통합검증
+ CastCoverage 통합검증
+ CharacterLoad 재계산
+ provider run 무결성
```

### 3.6 Stage04 이후

전 회차 Stage01~03이 잠긴 뒤 Stage04를 수행한다.

```text
PayoffCandidate 전수 처분
→ CrossEpisodeEdge
→ FullSeriesArc
→ disposition 100%
```

그 뒤 전 시즌 CharacterLoad 곡선과 SeriesCharacterRoster를 종합할 수 있다.

이는 기능적으로 Stage05 후보이지만 파일럿 동안 다음 명칭을 사용한다.

```text
EXT6_FULL_SERIES_SYNTHESIS
```

공식 Stage05 명칭은 앵커 파일럿과 사용자 승인 전에는 부여하지 않는다.

---

## 4. 이중 분석 트랙 구조

GPT와 Claude가 동일 작품을 분석하므로 데이터 파일과 실행 provenance를 분리한다.

### 4.1 논리 경로

```text
analysis_runs/
  <work>/<contract_version>/<provider>/<run_id>/
```

예:

```text
analysis_runs/비밀의숲/ext6-p0-v1/gpt/run_20260714_01/
analysis_runs/비밀의숲/ext6-p0-v1/claude/run_20260714_01/
```

### 4.2 provider-neutral record

CastPresenceRecord와 CharacterLoadRecord에 다음을 반복 삽입하지 않는다.

```text
model_id
provider
run_id
```

exact keyset은 provider-neutral하게 유지한다. 실행 정보는 `AnalysisRunManifest`가 보유한다.

### 4.3 AnalysisRunManifest — 정확히 14키

```text
run_id
work_id
provider
model_id
contract_version
source_lock_sha256
input_episode_span
quarter_policy
started_at
completed_at
direct_reading_attested
python_semantic_generation
status
by
```

규칙:

```text
provider ∈ {GPT, CLAUDE}
direct_reading_attested == true
python_semantic_generation == false
(work_id, provider, run_id) 유일
```

비교 대상 두 run은 반드시 동일한 다음 값을 가져야 한다.

```text
source_lock_sha256
contract_version
input_episode_span
quarter_policy
```

허용 상태 예:

```text
DRAFT
IN_PROGRESS
GPT_RUN_LOCKED
CLAUDE_RUN_LOCKED
QUARANTINE
SUPERSEDED
```

---

## 5. 공통 P0 계약

## 5.1 EntityBridgeRecord — 정확히 9키

```text
work_id
character_key
canonical_name
aliases
entity_id
mapping_status
source_registry_ref
source_registry_sha
by
```

규칙:

```text
character_key = <work_slug>:<canonical_name_slug>
```

- `entity_id`는 Page10 매핑 전 `null` 허용
- canonical name을 `entity_id`에 넣지 않음
- `mapping_status ∈ {PROVISIONAL, MATCHED, AMBIGUOUS, UNRESOLVED}`
- `docs/external`에는 Page10 authority 복제본을 저장하지 않음
- source ref/SHA를 가진 read-only projection만 허용
- 별칭 변경 시 과거 character_key를 임의 재작성하지 않고 lineage를 남김

## 5.2 CastPresenceRecord — 정확히 10키

```text
work_id
episode_no
scene_no
character_key
entity_id
presence_mode
focality
speaking_status
evidence_ref
by
```

### grain

```text
장면 × 인물 = 1행
```

### 허용 enum

```text
presence_mode ∈ {
  ONSCREEN,
  VOICE_ONLY,
  PHONE_OR_REMOTE,
  ARCHIVAL_OR_MEMORY,
  REFERENCED_ONLY
}
```

```text
focality ∈ {
  PRIMARY,
  SECONDARY,
  PRESENT_ONLY
}
```

```text
speaking_status ∈ {
  SPEAKING,
  NON_SPEAKING,
  NOT_APPLICABLE
}
```

### 불변식

- `(work_id, episode_no, scene_no, character_key)` 유일
- 장면이 SourceLock에 실재
- character_key가 EntityBridge에 실재
- `REFERENCED_ONLY`는 등장 분량 집계에서 제외
- `ARCHIVAL_OR_MEMORY`는 별도 집계 가능하나 기본 present count에서 제외
- `evidence_ref`는 원문 전문이 아닌 SourceLock scene ref 또는 hash
- 존재하지 않는 인물을 수량 채우기 위해 생성하지 않음
- 군중·무명 인물 정책은 파일럿 전에 고정

## 5.3 CastCoverageLedger — 정확히 9키

```text
work_id
episode_no
quarter
scene_range
annotated_scene_nos
empty_cast_scene_nos
unresolved_scene_nos
coverage_status
by
```

목적:

CastPresence 행이 없는 장면이 다음 중 무엇인지 구분한다.

```text
실제 무인 외경
인물 없는 삽입 화면
분석 누락
식별 불가
```

통과 조건:

```text
annotated_scene_nos ∪ empty_cast_scene_nos
= quarter 모든 scene_no

annotated_scene_nos ∩ empty_cast_scene_nos
= ∅

unresolved_scene_nos = []
coverage_status = LOCKED_PASS
```

## 5.4 CharacterLoadRecord — 정확히 17키

```text
work_id
episode_no
character_key
entity_id
canonical_name
present_scene_count
focal_scene_count
speaking_scene_count
present_sequence_count
scene_share
focal_share
scene_share_band
act_placement
first_scene_no
last_scene_no
max_absence_gap
by
```

### 결정론 계산

```text
present_scene_count
= ONSCREEN + VOICE_ONLY + PHONE_OR_REMOTE가 존재하는 고유 scene 수
```

```text
focal_scene_count
= focality가 PRIMARY 또는 SECONDARY인 고유 scene 수
```

```text
speaking_scene_count
= speaking_status == SPEAKING인 고유 scene 수
```

```text
present_sequence_count
= 해당 인물이 기본 present count 조건으로 등장하는 고유 seq_id 수
```

```text
scene_share
= present_scene_count / episode_scene_count
```

```text
focal_share
= focal_scene_count / episode_scene_count
```

### 추가 규칙

- `scene_share`와 `focal_share`는 주관적 0~1 점수가 아니라 객관적 산술값
- 정확 비율을 보존하고 band는 파생값으로 둠
- `scene_share_band ∈ {DOMINANT, MAJOR, MINOR, CAMEO}`
- band threshold는 파일럿 전에 사전등록하고 결과를 본 뒤 변경하지 않음
- `act_placement`는 Stage03 EpisodeArc act_structure를 참조
- `max_absence_gap`은 회차 내부 장면 ordinal 기준 결정론 계산
- CharacterArc 레코드가 없더라도 CastPresence와 CharacterLoad는 생성 가능
- 작품 전체 역할 `LEAD/DEUTERO/SUPPORTING/MINOR`는 회차 load와 분리하여 SeriesCharacterRoster에서 다룸

---

## 6. Provider 독립 분석 규칙

GPT와 Claude는 다음 공통 입력만 공유한다.

- 동일 원본 archive
- 동일 SourceLock
- 동일 Stage01~04 계약
- 동일 EXT6 P0 계약
- 동일 quarter 정책
- 동일 8~10회 블록 정책
- 동일 validator version

봉인 전 공유 금지:

- 상대 모델의 SceneCard
- 상대 모델의 SequenceBlueprint
- 상대 모델의 Stage03 렛저
- 상대 모델의 CastPresence
- 상대 모델의 CharacterLoad
- 상대 모델의 분석 메모
- 상대 모델의 중간 품질 점수
- 상대 모델의 failed fixture 결과

각 모델은 먼저 자기 패키지를 봉인한다.

```text
GPT_RUN_LOCKED
CLAUDE_RUN_LOCKED
```

두 상태가 모두 존재한 뒤 비교를 시작한다.

### 6.1 독립성 증명

각 run manifest에는 다음을 기록한다.

```text
direct_reading_attested = true
other_provider_outputs_read_before_lock = false
python_semantic_generation = false
```

필요하면 별도 IndependenceAttestation을 둘 수 있으나 Phase 01에서는 run manifest 확장 여부를 비교 단계에서 결정한다.

---

## 7. GPT↔Claude 비교 계약

### 7.1 비교 단위

```text
CastPresence
= (episode_no, scene_no, character_key)
```

```text
CharacterLoad
= (episode_no, character_key)
```

### 7.2 차이 유형

```text
FACT_CONFLICT
한쪽이 존재하지 않는 인물·장면을 기록
```

```text
BOUNDARY_CONFLICT
동일 원본인데 SourceLock 장면 경계를 다르게 사용
```

```text
IDENTITY_CONFLICT
별칭·동명이인·character_key 매핑 불일치
```

```text
PRESENCE_MODE_DIVERGENCE
등장 유형 판정 차이
```

```text
FOCALITY_DIVERGENCE
초점성 해석 차이
```

```text
SPEAKING_STATUS_DIVERGENCE
발화 여부 판정 차이
```

```text
VALID_INTERPRETIVE_DIVERGENCE
양쪽 모두 근거가 있으나 해석이 다름
```

```text
CONTRACT_ERROR
keyset / enum / FK / COUNT / type 오류
```

### 7.3 CrossProviderComparisonRecord — 정확히 12키

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

허용 상태:

```text
agreement_status ∈ {
  AGREE,
  PARTIAL,
  DISAGREE,
  NOT_COMPARABLE
}
```

### 7.4 병합 원칙

- `FACT_CONFLICT`와 `CONTRACT_ERROR`는 hard adjudication
- `BOUNDARY_CONFLICT`는 공통 SourceLock으로 회귀해 해결
- `IDENTITY_CONFLICT`는 EntityBridge/AliasIndex로 회귀
- `FOCALITY_DIVERGENCE`는 원문 재독 후 복수 초점 허용 여부 검토
- `VALID_INTERPRETIVE_DIVERGENCE`는 반드시 한쪽을 삭제하지 않음
- 합의본은 별도 `consensus/` 경로에 생성
- 원본 GPT/Claude run은 영구 보존
- 자동 수정은 금지하고 adjudication ledger를 남김

### 7.5 사용자 판정이 필요한 경우

다음은 사용자 판정 대상으로 분리한다.

- 양쪽 모두 근거가 충분한데 focality가 충돌
- 군중·무명 인물의 포함 범위
- 다중 화자 장면에서 PRIMARY 초점 수
- 작품별 band threshold의 변경 요구
- 해석 차이를 단일 합의값으로 축소할지 복수 해석으로 보존할지

---

## 8. 검증 게이트

## Gate A — Contract Integrity

검사:

- exact keyset
- enum
- type
- uniqueness
- FK
- source lock SHA
- run manifest compatibility
- provider path isolation
- grain uniqueness
- nullable 규칙
- contract version

판정:

```text
ERRORS 0
```

## Gate B — Grounding / Recalculation

검사:

- 장면 실재
- 인물 실재
- CastCoverage 완전성
- CharacterLoad 재계산 일치
- evidence_ref 실재
- 원문 전문 미포함
- 반복 placeholder 없음
- Python 의미 생성 없음
- 상대 provider 결과 선열람 금지 선언
- scene_share/focal_share 정확 재계산
- first/last/max gap 재계산

판정:

```text
ERRORS 0
```

## Gate C — Cross-provider Value Proof

검사:

- GPT/Claude agreement matrix
- 사실 오류율
- provider별 누락률
- 해석 다양성 보존율
- adjudication 비용
- CharacterLoad 사용 전후 구조 진단 성능
- blind critic 효과
- 비용 대비 효과
- 최악 사례 악화율

Gate C는 파일 손상 PASS/FAIL이 아니라 다음을 결정한다.

```text
PROMOTE_P0
REVISE_CONTRACT
KEEP_ADVISORY
DEFER
REJECT
```

중요:

```text
두 모델의 합의율이 높다
≠ 분석 품질이 높다
```

두 모델이 같은 오류를 낼 수 있으므로 원본 근거 정확성과 blind value proof를 별도로 검사한다.

---

## 9. Positive / Negative Fixtures

### 9.1 Positive fixture

최소 구성:

- 1개 작품
- 1개 회차
- 2개 quarter
- 인물 있는 장면
- 무인 외경 장면
- 전화 등장
- 회상 등장
- 언급만 된 인물
- 복수 초점 장면
- 정상 EntityBridge
- 정상 CastPresence
- 정상 CharacterLoad

### 9.2 Negative fixtures

최소 다음을 포함한다.

1. SourceLock에 없는 scene_no
2. EntityBridge에 없는 character_key
3. 동일 scene×character 중복
4. `REFERENCED_ONLY`를 present count에 포함
5. `ARCHIVAL_OR_MEMORY`를 기본 present count에 포함
6. CastCoverage scene 누락
7. annotated와 empty_cast 교집합
8. unresolved scene 잔류
9. scene_share 오계산
10. focal_share 오계산
11. first_scene_no·last_scene_no 역전
12. 잘못된 max_absence_gap
13. provider run 경로 충돌
14. 서로 다른 SourceLock SHA의 run 비교
15. 상대 provider 결과를 읽고 작성한 run
16. raw script 문장 저장
17. placeholder 반복
18. 비허용 enum
19. exact key 누락·추가
20. canonical_name을 entity_id에 저장

---

## 10. 앵커 파일럿

### 10.1 1차 앵커

```text
비밀의숲
```

이유:

- 다인물 수사극
- focality와 주변 인물 배치가 복잡
- 기존 Stage01~04 기반이 충분
- GPT/Claude 차이를 비교하기 적합
- 전화·보고·무언 등장·군중 장면이 다양

### 10.2 2차 앵커

```text
시크릿가든
```

수사극에 과적합된 계약인지 로맨스에서 재검증한다.

### 10.3 선택적 3차 앵커

```text
베토벤바이러스
```

군상극에서 조연 분량과 focality를 재검증한다.

### 10.4 파일럿 분석 범위

기술 fixture:

```text
비밀의숲 EP01~02
→ 계약·비용·차이 유형 확인
→ validator 수정
```

정식 파일럿:

```text
이상 없으면 EP01~08 블록
```

EP01~02는 Phase01 기술 fixture일 뿐 정식 분석 납품이 아니다. 정식 사용자 제출·품질 판정은 8~10회 블록 규칙을 유지한다.

### 10.5 파일럿 중단 조건

- Gate A 오류가 반복적으로 발생
- Gate B 원본 근거 오류가 임계치를 초과
- CastPresence 작성 때문에 Stage01 품질이 저하
- quarter당 작업량이 지속 불가능
- provider 독립성 증명이 불가능
- EntityBridge 충돌이 해결되지 않음
- adjudication 비용이 가치보다 큼

---

## 11. 비교 후 최종 합의 절차

```text
1. GPT 독립안 봉인
2. Claude 독립안 봉인
3. 두 문서의 keyset 자동 비교
4. stage timing 비교
5. validator/gate 비교
6. 합의·이견 목록 작성
7. 각 모델이 상대안 교차비평
8. 사실 오류와 설계 선호 차이 분리
9. 사용자 판단이 필요한 항목 분리
10. 최종 합의 계약 v1 작성
11. 사용자 승인
12. Codex 구현
```

최종 합의 문서에는 각 조항의 출처를 남긴다.

```text
GPT_ONLY
CLAUDE_ONLY
BOTH_AGREED
USER_DECIDED
```

생성할 문서:

```text
PHASE01_GPT_CLAUDE_COMPARISON_MATRIX_v1
PHASE01_CONSENSUS_AND_DISSENT_LEDGER_v1
PHASE01_FINAL_CONSENSUS_CONTRACT_v1
```

---

## 12. Phase 01 완료 기준

다음이 모두 있어야 Phase 01 완료다.

- GPT 독립 설계안
- Claude 독립 설계안
- 비교 매트릭스
- 합의·미합의 원장
- 확정 schema registry
- positive fixture
- negative fixtures
- Gate A validator specification
- Gate B recalculation specification
- provider isolation specification
- 사용자 승인 기록

아직 완료가 아닌 것:

```text
새 Stage05 공식화
전면 코퍼스 적용
자동 학습 승격
CANONICAL 승격
```

---

## 13. GPT 자기비판

1. CastPresence 자체도 focality에서 해석 차이가 크므로 등장 사실과 초점 판단을 동일 레코드에 두는 것이 장기적으로 분리 필요할 수 있다.
2. `character_key` slug 규칙은 한국어 띄어쓰기·동명이인에서 충돌할 수 있어 EntityBridge가 빠르게 필요하다.
3. 두 모델을 완전 블라인드하게 운영하기 어렵기 때문에 최소한 상대 산출물 미열람 선언과 run lock을 기록해야 한다.
4. 비교 비용이 커질 수 있으므로 모든 의미 필드가 아니라 P0부터 이중 분석해야 한다.
5. 합의율이 높다고 품질이 높은 것은 아니므로 원본 근거 정확성과 blind value proof를 별도로 봐야 한다.
6. CastPresence를 Stage01과 동시에 쓰면 SceneCard 사고가 분산될 수 있으므로 `SceneCard 우선 → 짧은 재확인 → CastPresence`의 2-pass를 강제해야 한다.
7. 군중·무명인물·화면 밖 음성의 식별 정책이 작품마다 달라질 수 있으므로 공통 enum과 작품별 policy를 분리해야 한다.
8. `focality=SECONDARY`의 남용을 막기 위한 negative fixture와 provider 비교가 필요하다.

---

## 14. 최종 제안

```text
GPT와 Claude가 모두 드라마를 분석하는 전략은 타당하다.
다만 한쪽을 정답 생성기, 다른 쪽을 검사기로 고정하지 않는다.
두 모델은 독립 저작자이며, 공통 계약과 SourceLock 아래 별도 run을 만든다.
비교는 오류 탐지와 해석 다양성 보존을 동시에 목표로 한다.
```

상태:

```text
GPT_INDEPENDENT_DRAFT_LOCKED
READY_FOR_CLAUDE_INDEPENDENT_DRAFT
NO_IMPLEMENTATION_BEFORE_COMPARISON
NO_CANONICAL_PROMOTION
```

---

## 15. Claude 측 요청

Claude는 자신의 독립안을 먼저 봉인한 뒤 본 문서를 검토하고 다음을 작성한다.

```text
CLAUDE_EXT6_PHASE01_INDEPENDENT_PROPOSAL_v1.md
CLAUDE_REVIEW_OF_GPT_PHASE01_v1.md
```

GPT는 Claude 독립안을 받은 뒤 다음을 작성한다.

```text
GPT_REVIEW_OF_CLAUDE_PHASE01_v1.md
PHASE01_GPT_CLAUDE_COMPARISON_MATRIX_v1.md
PHASE01_CONSENSUS_AND_DISSENT_LEDGER_v1.md
```

최종 계약은 사용자 승인 전 정본화하지 않는다.
