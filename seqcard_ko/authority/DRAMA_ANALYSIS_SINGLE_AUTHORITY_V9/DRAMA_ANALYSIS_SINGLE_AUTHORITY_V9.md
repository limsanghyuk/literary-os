# 한국 드라마 분석 단일 권위 V9

Authority ID: `DRAMA_ANALYSIS_SINGLE_AUTHORITY_V9`  
Version: `9.0.0`  
Effective date: `2026-07-23`  
Status: `ACTIVE_SINGLE_AUTHORITY`

## 0. 권위

이 문서 하나가 Stage01–04 분석의 유일한 의미·운영 권위다. `schemas/`, `tools/`, `templates/`는 실행 부속물이며 해석 권위가 아니다. V1–V8과 과거 GPT·Claude 매뉴얼·세션 기록은 `SUPERSEDED` 역사·감사 자료다. 충돌하면 V9가 우선한다.

분석의 최우선 원칙은 다음과 같다.

> 원본을 직접 읽고, 이해하고, 분석하고, 고유하게 저작한다. 형식과 도구는 그 판단을 보존하고 검증하기 위해 존재한다.

다음은 분석이 아니다.

- 기존 대상 작품의 의미문을 새 필드로 이동
- 원문 마지막 대사·지문·제작 표지를 outcome처럼 복사
- 장면 수 균등분할 Sequence
- 회차 요약을 인물·관계마다 복사
- 메타데이터에서 Stage03·04 자동 파생
- 저작 스크립트가 수동 감사 PASS를 동시에 생성
- 구조 PASS를 원문 의미 PASS로 확대

Python과 도구는 inventory, 인코딩, 장면 경계 보조, 해시, 직렬화, exact schema·FK·coverage·중복 검사, manifest·ZIP 생성에만 사용한다. SceneCard·Sequence·Arc·Edge·Payoff의 의미를 만들지 않는다.

## 1. 시작 전 SourceFormatAudit

의미 저작 전에 반드시 다음을 확인한다.

1. 원본 파일명과 실제 회차 내용
2. 인코딩·페이지·본문 누락
3. 회차 시작·끝 표제
4. 숫자 장면뿐 아니라 번호 없는 외경·전경·몽타주·인서트·회상 전환
5. 같은 원본의 중복·오명명·부분 판본
6. canonical scene ordinal과 source index/hash
7. 원본 완전성

원본 상태는 다음 중 하나다.

- `FULL_SERIES_SOURCE_LOCKED`: 전 회차·결말까지 잠김
- `PARTIAL_ARCHIVE_EPISODE_PILOT_ONLY`: 지정 회차 파일럿만 가능
- `SOURCE_COMPLETENESS_UNVERIFIED`: 회차 총수·결말 미확인, 전 시즌 작업 차단
- `SOURCE_HOLD`: 판본·회차·장면 경계를 재현할 수 없어 중단

부분 원본은 지정 회차 Stage01–03만 허용한다. Stage04·FullSeriesArc·전 시즌 PASS를 만들지 않는다.

## 2. 작품 분류

- `NEW_ANALYSIS`: 유효한 Stage01–04 없음
- `NORMAL_UPGRADE`: 기존 Stage01·02가 원문과 밀착되고 구조가 유효
- `STAGE01_PARTIAL_REAUTHOR`: 특정 장면 의미·경계 오류
- `STAGE02_PARTIAL_REAUTHOR`: 일부 Sequence 의미·경계 오류
- `STAGE02_FULL_REAUTHOR`: 고정 분할·반복 문형·미래 정보 혼입
- `STAGE03_REAUTHOR_REQUIRED`: Arc·Edge·Candidate 자동 파생 또는 복사
- `FULL_REAUTHOR_REQUIRED`: 같은 작품 기존 의미 오염이 전 계층에 침투
- `SOURCE_HOLD`: 원본 잠금 실패

동일 작품의 서로 다른 lineage를 계층별로 혼합하지 않는다. 유지하려면 원문 밀착성과 참조 체계를 먼저 검증한다.

## 3. 작업 단위

의미 저작 단위는 **한 회차 전체의 순차 독해**다.

```text
EPxx 원본 전체 순차 독해
→ Stage01 SceneCard
→ 회차 전체 재검토·EpisodeMeta
→ Stage02 SequenceBlueprint
→ EpisodeArc
→ CharacterArc·RelationshipArc
→ LocalEdge·PayoffCandidate
→ 회차 경량 게이트
→ 원자적 체크포인트
→ 다음 회차
```

Q1–Q4는 언어모델이 읽지 않고 저작하는 것을 막거나 긴 원본을 안전하게 저장하기 위한 선택적 읽기 체크포인트다. 정본 필수 계층·극적 4막·고정 분할이 아니다.

계획·개발자 전달·통합감사는 최대 8회차 블록으로 구성할 수 있으나, 8회차를 동시에 의미 생성하지 않는다. 블록 종료 시 강검증하고 오류 회차만 원문으로 돌아간다.

## 4. 중단 방지와 원자적 저장

수호천사에서 52–55분 연속 실행 후 의미 감사 직전에 중단된 사례를 기준으로 다음을 강제한다.

- 20분: 체크포인트 준비 경고
- 25분: 현재 산출물·상태·checksum 원자적 저장 필수
- 30분: 체크포인트 없는 의미 작업 하드스톱
- 한 장기 실행에서 여러 회차를 연속 잠그지 않는다.

정본 파일은 다음 순서로 쓴다.

```text
<file>.tmp
→ JSON/JSONL parse
→ flush/fsync
→ 기존 파일 lineage 백업
→ atomic rename
→ SHA256
→ manifest·work_state 동기화
```

`run_journal.jsonl`은 최소 다음 이벤트를 기록한다.

`RUN_START, SOURCE_OPENED, SEMANTIC_AUTHORING_START, CHECKPOINT_PREPARED, CHECKPOINT_LOCKED, VALIDATION_START, VALIDATION_END, RUN_STOP, INTERRUPTION_DETECTED, RECOVERY_START, RECOVERY_LOCKED`

안전한 재진입 상태는 `EPISODE_CHECKPOINT_LOCKED`, `BLOCK_CHECKPOINT_LOCKED`, `FULL_SERIES_CHECKPOINT_LOCKED`뿐이다. 검증 보고서가 work_state보다 새로우면 `STALE_STATE`다. 자기 보고서가 상태를 계속 stale로 만드는 순환을 피하려고 상태 동기화 검사에서 현재 검사기 자기 파일은 제외한다.

## 5. 도구 경계

허용:

- 압축 해제·inventory·인코딩 복구
- heading·ordinal·line span·offset 탐지
- source index·SHA256
- JSON/JSONL 직렬화
- exact keyset·자료형·enum·ID·FK·coverage 검사
- count·core_dist·runtime_share·core_mix 결정론적 재계산
- 반복 골격·placeholder·장문 복사 탐지
- manifest·ZIP·CRC·fresh extraction

금지:

- SceneCard 의미·CORE 판정
- Sequence goal·obstacle·value_shift 생성
- EpisodeArc·CharacterArc·RelationshipArc 생성
- LocalEdge·PayoffCandidate 의미 판단
- CandidateDisposition 자동 판정
- CrossEpisodeEdge 승격
- FullSeriesArc 의미 생성

결정론적 교정은 correction ledger에 이전 SHA·변경 필드·이유를 기록한다. 의미 오류는 원문을 다시 읽고 새 author run으로 재저작한다.

## 6. 공통 ID와 enum

- 회차 work_id: `<work>_<NN>`
- Sequence ID: `<work>_<NN>_S<II>`
- LocalEdge ID: `<work>_e<NN><III>`
- PayoffCandidate ID: `<work>_p<NN><III>`
- CrossEpisodeEdge ID: `<work>_x<III>`

CORE 16종:

`ESTABLISH, ORACLE, INTRO, BOND, CONFLICT, REVERSAL, LOSS, PUNISH, REVELATION, REUNION, RELIEF, ROMANCE, PERIL, RESCUE, DESIRE, HOOK`

turn mapping:

- `RISE, BOND, PUNISH → RISE`
- `FALL, LOSS → FALL`
- `REVEAL, ORACLE, REVERSAL → REVEAL`
- `STALL, HOOK, CONFLICT → STALL`

## 7. Stage01

SceneCard exact 9키:

```text
work_id, scene_no, heading, title, intent_gist,
core, core2, skin, by
```

- `heading`: 원문 provenance와 대응
- `title`: 이 장면에서만 성립하는 고유 전환
- `intent_gist`: 욕망·압력·행동·정보·선택·변화의 핵심 해석
- `core/core2`: 전후 차이의 1차·2차 극적 기능, core2는 null 가능
- `skin`: 장소·시간·표면 행동·소품의 구체적 질감

내부적으로 행동·전략·정보 변화·선택·구조 기능·잔여 동력을 구분하지만 objective·conflict·action·outcome 같은 새 top-level 키로 정본을 확장하지 않는다. 필요하면 비정본 `analysis_notes/`에 격리한다.

PASS 조건:

- 중심 행위자와 실제 행동을 바꾸지 않음
- 다음 회차 사건을 앞당기지 않음
- 인물 없는 전환·몽타주에 억지 목표를 부여하지 않음
- title·intent·skin이 같은 문장을 반복하지 않음
- 원문 마지막 행·제작 표지를 의미 필드로 복사하지 않음
- 다른 장면에도 붙는 추상문이 아님

EpisodeMeta exact 5키:

`work_id, scene_count, core_dist, episode_function, by`

scene_count와 core_dist는 Stage01에서 결정론적으로 재계산한다.

## 8. Stage02

SequenceBlueprint exact 18키:

```text
seq_id, work_id, episode_no, seq_index,
member_scene_nos, scene_span, scene_budget,
sequence_intent, goal, obstacle, value_shift,
turn_type, turn_class, core_mix, pov_char,
place_cluster, runtime_share, by
```

불변식:

- 모든 장면 정확히 1회 포함
- 중복·누락 0
- member_scene_nos 연속·오름차순
- scene_span·scene_budget 일치
- runtime_share 합계 1.0 ± 1e-6
- sequence_count / scene_count ≥ 0.11
- 권장 0.12–0.17은 감사 신호이지 자동 실패 할당량이 아님
- core_mix는 member SceneCard의 실제 core/core2만 사용

경계는 목표 주체·목표·장애·정보/관계/권력 가치·새 행동 단위·결과 전환이 달라지는 지점에 둔다. 단일 장면 Sequence를 허용한다. 교차편집된 여러 줄거리를 “회차 소개” 같은 추상 목표로 한 Sequence에 묶지 않는다.

## 9. Stage03

EpisodeArc exact 13키:

```text
work_id, episode_no, scene_count, sequence_count,
dramatic_question, act_structure, entry_state, exit_state,
turning_point, central_conflict_axis, episode_function,
core_dist, by
```

turning_point는 `{seq_index, desc}`, act item은 `{act, seq_span, function}`이다. 모든 Sequence를 gap·overlap 없이 정확히 한 번 덮고 숫자상 4등분을 금지한다.

CharacterArc exact 8키:

`work_id, character, episode_no, state_label, state_delta, trigger_scene_no, by, evidence`

RelationshipArc exact 9키:

`work_id, char_a, char_b, episode_no, relation_state, relation_delta, trigger_scene_no, evidence, by`

실제 상태·관계 변화가 있는 대상만 기록한다. trigger 장면에서 인물이 실제 등장·발화·행동하거나 직접 통화·교신해야 한다. 고정 수량, 역순 관계쌍 중복, 동일 evidence 복사를 금지한다.

LocalEdge exact 12키:

```text
edge_id, work_id, edge_type,
src_episode_no, src_scene_no,
tgt_episode_no, tgt_scene_no,
gap_episodes, label, confidence, note, by
```

LocalEdge는 `edge_type=causal`, 동일 회차, gap 0, label은 target SceneCard.core다. source의 행동·정보·선택이 없다면 target이 발생하지 않거나 실질적으로 달라지는 경우만 기록한다. 단순 인접·같은 Sequence·유사 감정은 인과가 아니다.

PayoffCandidate exact 7키:

`candidate_id, work_id, episode_no, scene_no, edge_type_guess, description, by`

guess는 `plant_payoff | callback | subplot_counterpoint | resolved_here`다. 장거리 회수 가능성이 구체적인 정보·약속·소품·위협·선택만 남기며 수량 할당량은 없다.

## 10. Stage04

전 회차 Stage01–03 강검증·잠금 뒤 별도 실행한다.

```text
모든 PayoffCandidate 목록화
→ 원 장면 재개방
→ 실제 후속 장면 재개방
→ source/target 의미 대조
→ 후보별 CandidateDisposition
→ 검증된 CrossEpisodeEdge
→ FullSeriesArc 신규 종합
```

모든 후보는 다음 중 하나로 100% 처분한다.

`PROMOTED_CROSS_EDGE, RECLASSIFIED_LOCAL_OR_ADJACENT_CAUSAL, RESOLVED_WITHIN_EPISODE, REJECTED_DUPLICATE, REJECTED_INSUFFICIENT_EVIDENCE, REJECTED_SOURCE_MISMATCH`

미처리 후보 1건이라도 있으면 Stage04 실패다. 같은 결말로 여러 source가 수렴하면 원죄·물증·조사·기억처럼 독립 증거 역할인지 확인하고, 같은 의미면 중복 기각한다.

CrossEpisodeEdge는 LocalEdge와 같은 12키를 사용하되 target 회차가 source보다 뒤이고 gap은 회차 차이다. edge_type은 `callback | plant_payoff | subplot_counterpoint`다. 이전 회차 마지막 장면과 다음 회차 첫 장면 자동 브리지를 금지한다.

FullSeriesArc exact 17키:

```text
series, episodes_total, scenes_total, sequences_total,
logline, central_dramatic_question, theme_statement,
protagonist, antagonist, season_structure,
macro_turning_points, resolution, open_ending,
tone, conflict_persist, series_core_dist, by
```

counts는 실제 데이터에서 재계산하고 season_structure는 실제 서사 이동을 따르며 기계적 4분기를 금지한다.

## 11. 데이터베이스와 기존판 비교

DB는 세 등급으로 사용한다.

- Gold Semantic Reference: 검증된 특정 객체의 깊이·고유성 비교
- Structural Reference: 키·ID·FK·coverage·경로 비교
- Anti-pattern Reference: 고정 분할·복사 Arc·자동 파생·회차 간 LocalEdge·자기 감사의 반례

`SameWorkLegacyLock`을 author lock 전에 적용한다. 같은 작품의 기존 의미문은 신규 저작 전 열지 않는다. 원본 파일명·ordinal·hash만 사용할 수 있다. 신규 객체를 잠근 뒤 다음을 감사한다.

- 기존 title/intent exact match
- 기존 고정 분할 반복
- 미래 정보 혼입 재발
- Arc evidence 복사
- 후보·CrossEdge 무비판 재사용

정당한 공통 고유명·사건 용어를 제외하고 기존 의미문과 정확히 일치하면 직접 재저작으로 인정하지 않는다.

업그레이드 수용 전 같은 객체 기준으로 장면 정확성, 문장 고유성·압축성, Sequence 경계, EpisodeArc entry→exit, Arc trigger, LocalEdge 인과, 후보 처분, 원문·package 재현성을 비교한다. 신판의 레코드 수가 늘었다는 사실만으로 개선이라 하지 않고 약점도 기록한다.

## 12. 검증

회차 경량 게이트:

- JSON/JSONL parse
- exact keyset·자료형·enum
- Scene ordinal·source index
- EpisodeMeta count
- Sequence coverage·partition·runtime·turn mapping·core_mix
- ID·FK
- placeholder·명백한 exact duplicate
- work_state·next pointer·checksum

블록 강게이트:

- 원본 SHA·scene hash
- title·intent exact duplicate
- 고유명·장소·CORE 마스킹 골격 반복
- legacy semantic exact match
- Character/Relationship trigger participant
- LocalEdge 실제 인과 및 고위험 전수 감사
- 앙상블 실제 변화 누락
- 미래 회차 정보 혼입
- 보고서와 machine verdict 일치

작품 전체 게이트:

- 전 회차 Stage01–03 잠금
- 후보 disposition 100%
- 자동 회차 경계 bridge 0
- CrossEdge source/target·target core
- FullSeriesArc counts·season span
- manifest·SHA256SUMS
- ZIP CRC
- 새 위치 fresh extraction 후 같은 validator 재실행

최종 네 축:

- `STRUCTURAL_CONTRACT_PASS`
- `SEMANTIC_MECHANICAL_PASS`
- `SOURCE_GROUNDED_MANUAL_PASS`
- `PACKAGE_FRESH_EXTRACTION_PASS`

네 축 모두 PASS일 때만 `PASS_CANDIDATE`, 사용자 명시 승인 뒤에만 `CANONICAL`이다.

## 13. 저작·감사 분리

`author_run_id != audit_run_id`

저작 스크립트는 author attestation까지만 만들 수 있다. 독립 감사자는 원문을 재개방하고 source range, 장면 coverage, 고위험 장면, Sequence 경계, EpisodeArc, trigger·edge, 실패·교정을 기록한다. 감사자가 원문을 열지 않았거나 저작 실행이 자동 PASS를 만들었으면 `SOURCE_GROUNDED_MANUAL_PASS`는 무효다.

의미 오류를 발견하면 구조 PASS는 보존할 수 있으나 의미 PASS는 철회하고 종속 계층을 새 author run으로 재저작한다.

## 14. 상태·계보

허용 상태:

`DRAFT, SOURCE_HOLD, SOURCE_PARTIAL_PILOT_ONLY, AUTHOR_LOCKED_AUDIT_PENDING, EPISODE_CHECKPOINT_LOCKED, BLOCK_CHECKPOINT_LOCKED, QUARANTINE, PASS_CANDIDATE, PASS_CANDIDATE_AFTER_SEMANTIC_CORRECTION, CANONICAL, SUPERSEDED`

실패본을 삭제·덮어쓰지 않는다. `parent_run_id, supersedes, superseded_by`, 실패 이유, 복구 지점을 기록한다.

## 15. 패키지·DB·허브

독립 작품 패키지는 SourceLock, source index, author attestations, semantic audits, Stage01–04, validation, lineage, tools, FINAL_MANIFEST, SHA256SUMS, work_state를 포함한다. 원문 대본·장문 대사·embedding·비밀키는 배포 ZIP과 허브에 넣지 않는다.

DB 편입은 staging에서 작품 전체 lineage를 배치하고 동일 작품 구판을 백업한 뒤 계층 혼합 없이 전량 교체 또는 전량 유지한다. 실제 DB root와 작품 수를 먼저 확인하고 전역 ID·count·index·전체 validator·ZIP CRC·fresh extraction을 수행한다.

허브에는 권위 문서, schema·validator, SourceLock metadata, record counts, validation·lineage·handoff, 패키지 SHA만 적재한다. 원본과 raw 의미 JSONL 전체는 적재하지 않는다.

## 16. 새 작품 권위 수용 파일럿

권위 개정 즉시 전 작품을 분석하지 않는다.

1. 기존 DB에 없는 작품 선택
2. SourceFormatAudit·SourceLock
3. 원본 완전성 판정
4. EP01 전체 직접독해
5. Stage01–03 저작
6. 별도 audit run 원문 재감사
7. 구조·의미·package fresh extraction
8. 실패 시 권위 또는 저작 절차 교정
9. EP01 PASS 뒤에만 후속 회차 확대

부분 원본이라면 파일럿 성공과 전 시즌 분석 가능성을 구분한다.

## 17. 새 세션 부트스트랩

새 세션은 프로젝트 전체를 전수 조사하지 않는다.

1. 이 V9 마스터 문서를 읽는다.
2. AUTHORITY_MANIFEST와 validator 상태를 확인한다.
3. 대상 원본 inventory와 최신 work_state/DB 상태만 읽는다.
4. SourceFormatAudit와 작품 분류를 수행한다.
5. 같은 작품 기존 의미문을 author lock 전 차단한다.
6. EP01 원본 전체를 순서대로 직접 읽는다.
7. Stage01→02→03을 완결하고 25분 이내 체크포인트한다.
8. 독립 audit run으로 원문을 다시 연다.
9. 블록 강검증 후에만 다음 블록·Stage04로 간다.

복사용 시작 지시문:

```text
DRAMA_ANALYSIS_SINGLE_AUTHORITY_V9.md를 유일 실행 계약으로 사용하라.
대상 작품의 원본 inventory와 SourceFormatAudit를 먼저 수행하고 원본 완전성 상태를 판정하라.
같은 작품의 기존 의미 데이터는 author lock 전 열지 마라.
한 회차 전체를 처음부터 끝까지 직접 읽은 뒤 Stage01→Stage02→Stage03을 완결하라.
Q1–Q4는 필요할 때만 읽기 체크포인트로 사용하고 정본 필수 산출물로 만들지 마라.
Python으로 의미를 생성하지 마라.
20분 경고, 25분 원자적 체크포인트, 30분 무저장 하드스톱을 지켜라.
저작과 독립 감사를 다른 run_id로 수행하라.
부분 원본은 지정 회차 파일럿만 허용하고 Stage04·FullSeriesArc를 만들지 마라.
모든 검증과 fresh extraction을 통과한 뒤 PASS_CANDIDATE로 보고하라.
```

## 18. 수호천사 실전 acceptance 반례

- 기존 `intent_gist`를 새 action으로 555/556 재사용: 직접 재저작 아님
- 저작 스크립트가 556건 수동 감사 PASS 동시 생성: 독립 감사 아님
- EP06에 EP07 기차 승차 결과 혼입: 구조 검사만으로 발견 불가
- 고정 8장면 Sequence: 행동 단위 아님
- 제작 표지를 outcome처럼 복사: 의미 필드 아님
- 52–55분 연속 실행 후 의미 감사 중단: 25분 체크포인트 필요
- 부분 staging을 전체 DB로 오인: 실제 DB root와 작품 수를 먼저 확인
- CandidateDisposition의 candidate_id 반복을 전역 ID 중복으로 오판: 참조키와 엔터티 ID 규칙 분리

이 반례는 문서의 실제 acceptance test다.

## 19. 최종 판정

새 세션이 올바르게 작동했다는 증거는 자신감이나 장문의 보고서가 아니라 다음이다.

- 직접 읽은 원본 범위
- 고유 SceneCard와 실제 Sequence 경계
- 변화가 있는 인물·관계만 기록한 Stage03
- 독립 원문 감사
- 중단 복구 가능한 원자적 체크포인트
- errors 0, blocking warnings 0
- manifest·SHA·ZIP CRC·fresh extraction
- 정확한 상태와 다음 진입점

> 원본을 직접 읽고, 이해하고, 분석하고, 고유하게 저작한다. 형식과 도구는 그 판단을 보존하고 검증하기 위해 존재한다.
