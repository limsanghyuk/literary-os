# 한국 드라마 분석 단일 권위 V8

Authority ID: `DRAMA_ANALYSIS_SINGLE_AUTHORITY_V8`  
Version: `8.0.0`  
Effective date: `2026-07-23`

## 1. 목적과 최상위 원칙

드라마 분석은 대본을 직접 읽고 장면의 행동·전략·정보 변화·선택·구조 기능·잔여 동력을 이해한 뒤 정해진 작은 스키마에 밀도 있게 압축하는 close-reading 저작 작업이다.

다음은 분석이 아니다.

- 형식만 맞춘 템플릿 치환
- 기존 대상 작품 의미문을 새 필드로 이동
- 메타데이터에서 Stage03을 자동 파생
- 대사·지문·마지막 행을 의미 필드로 복사
- 장면 수를 균등하게 나눈 Sequence
- 자동 생성된 수동 감사 PASS

Python과 도구는 원본 inventory, 인코딩, 장면 ordinal, SHA256, 직렬화, exact-schema·FK·coverage·중복 검사, manifest·ZIP 생성에만 사용한다. SceneCard·Sequence·Arc·Edge·Payoff의 의미를 생성하지 않는다.

## 2. 작품 분류

분석 전에 다음 중 하나를 판정한다.

- `NEW_ANALYSIS`: 원본은 있으나 유효한 Stage01–04가 없음
- `NORMAL_UPGRADE`: 기존 Stage01·02가 원문과 밀착되고 구조가 유효
- `STAGE02_PARTIAL_REAUTHOR`: 일부 회차의 시퀀스 의미만 오염
- `STAGE02_FULL_REAUTHOR`: 고정 분할·반복 문형·미래 정보 혼입으로 Stage02 전면 재저작
- `SOURCE_HOLD`: 판본·회차·장면 경계를 잠글 수 없음

정상 계층은 유지할 수 있으나 의미 결함 범위는 원문을 다시 읽고 새 lineage로 재저작한다. 동일 작품의 서로 다른 판본을 계층별로 혼합하지 않는다.

## 3. 작업 단위와 순서

계획·개발자 전달·통합감사는 최대 8회차 연속 블록으로 구성한다.

- 16부작: EP01–08 / EP09–16
- 20부작: EP01–08 / EP09–16 / EP17–20
- 24부작: EP01–08 / EP09–16 / EP17–24

8회차는 동시 의미 생성 단위가 아니다. 실제 저작은 한 회차씩 다음 순서로 진행한다.

```text
EPxx SourceLock 확인
→ Q1 원문 직접독해·SceneCard 저작·저장
→ Q2
→ Q3
→ Q4
→ 회차 Stage01 재검토·EpisodeMeta
→ Stage02 SequenceBlueprint
→ EpisodeArc
→ CharacterArc·RelationshipArc
→ LocalEdge·PayoffCandidate
→ 회차 경량 게이트·체크포인트
→ 다음 회차
```

회차마다 저장·JSON 파싱·키·ID·Scene coverage·명백한 반복을 경량 검사한다. 최대 8회차 블록 종료 시 원문 근거, 골격 반복, legacy contamination, trigger 참여자, 인과, 앙상블 누락을 강검증한다. 오류 회차만 원문으로 돌아간다.

장시간 실행은 45분 이내에 현재 회차 파일·상태·checksum을 영속화한다. 안전한 다음 진입 상태는 `EPISODE_CHECKPOINT_LOCKED`뿐이다.

## 4. 공통 ID와 enum

- 회차 work_id: `<작품>_<NN>`
- Sequence ID: `<작품>_<NN>_S<II>`
- LocalEdge ID: `<작품>_e<NN><III>`
- PayoffCandidate ID: `<작품>_p<NN><III>`
- CrossEpisodeEdge ID: `<작품>_x<III>`

CORE 16종:

`ESTABLISH, ORACLE, INTRO, BOND, CONFLICT, REVERSAL, LOSS, PUNISH, REVELATION, REUNION, RELIEF, ROMANCE, PERIL, RESCUE, DESIRE, HOOK`

turn mapping:

- `RISE, BOND, PUNISH → RISE`
- `FALL, LOSS → FALL`
- `REVEAL, ORACLE, REVERSAL → REVEAL`
- `STALL, HOOK, CONFLICT → STALL`

## 5. Stage01 exact contract

SceneCard는 exact 9키다.

```text
work_id, scene_no, heading, title, intent_gist,
core, core2, skin, by
```

- `heading`: 원문 장면 provenance와 대응
- `title`: 장면 고유 전환을 짧게 압축
- `intent_gist`: 인물의 욕망·압력·행동·변화를 해석한 고유 문장
- `core/core2`: 1차·2차 극적 기능. core2는 null 가능
- `skin`: 장소·시간·표면 행동의 구체적 질감

분석자는 내부적으로 실제 행동, 전략, 정보 변화, 선택·거부·유예, 회차 기능, 후속 동력을 구분하지만 이를 objective·conflict·action·outcome 같은 새 top-level 키로 정본에 추가하지 않는다. 필요하면 비정본 `analysis_notes/` sidecar로 격리한다.

EpisodeMeta exact 5키:

```text
work_id, scene_count, core_dist, episode_function, by
```

`core_dist`는 모든 core와 non-null core2를 재집계한다.

## 6. Stage02 exact contract

SequenceBlueprint exact 18키:

```text
seq_id, work_id, episode_no, seq_index,
member_scene_nos, scene_span, scene_budget,
sequence_intent, goal, obstacle, value_shift,
turn_type, turn_class, core_mix, pov_char,
place_cluster, runtime_share, by
```

불변식:

- 모든 scene_no가 정확히 한 Sequence에 포함
- 중복·누락 0
- member_scene_nos 연속·오름차순
- scene_span·scene_budget 일치
- runtime_share 합계 1.0
- sequence_count / scene_count ≥ 0.11
- core_mix는 member SceneCard의 실제 core/core2만 사용

Sequence 경계는 목표 주체·목표·장애·정보/관계/권력 가치·새 행동 단위·전환 완료가 달라지는 지점에 둔다. 장면 수 균등분할을 금지한다.

## 7. Stage03 exact contract

EpisodeArc exact 13키:

```text
work_id, episode_no, scene_count, sequence_count,
dramatic_question, act_structure, entry_state, exit_state,
turning_point, central_conflict_axis, episode_function,
core_dist, by
```

- turning_point: `{seq_index, desc}`
- act_structure item: `{act, seq_span, function}`
- act가 모든 Sequence를 gap·overlap 없이 정확히 한 번 덮는다.

CharacterArc exact 8키:

```text
work_id, character, episode_no, state_label,
state_delta, trigger_scene_no, by, evidence
```

RelationshipArc exact 9키:

```text
work_id, char_a, char_b, episode_no, relation_state,
relation_delta, trigger_scene_no, evidence, by
```

CharacterArc는 실제 상태 변화가 있는 인물만, RelationshipArc는 신뢰·권력·정보·의존·적대 조건이 실제로 이동한 관계만 작성한다. trigger 장면에서 인물 참여를 확인한다. 회차별 고정 수량과 evidence 복사를 금지한다.

LocalEdge exact 12키:

```text
edge_id, work_id, edge_type,
src_episode_no, src_scene_no,
tgt_episode_no, tgt_scene_no,
gap_episodes, label, confidence, note, by
```

LocalEdge는 `edge_type=causal`, 동일 회차, `gap_episodes=0`, `label=target SceneCard.core`다. source가 없다면 target이 발생하지 않거나 실질적으로 달라지는 경우만 기록한다. 단순 인접·같은 시퀀스·유사 감정은 인과가 아니다.

PayoffCandidate exact 7키:

```text
candidate_id, work_id, episode_no, scene_no,
edge_type_guess, description, by
```

edge_type_guess는 `plant_payoff | callback | subplot_counterpoint | resolved_here`다. 장거리 회수 가능성이 구체적인 정보·약속·소품·위협·선택만 남긴다.

## 8. Stage04

모든 회차 Stage01–03 강검증 뒤 별도 fan-in으로 실행한다.

```text
모든 PayoffCandidate 목록화
→ 원 장면 재확인
→ 후속 실제 장면 재확인
→ 후보별 disposition
→ 검증된 CrossEpisodeEdge
→ FullSeriesArc 신규 종합
```

모든 후보는 반드시 다음 중 하나로 처분한다.

`PROMOTED_CROSS_EDGE, RECLASSIFIED_LOCAL_OR_ADJACENT_CAUSAL, RESOLVED_WITHIN_EPISODE, REJECTED_DUPLICATE, REJECTED_INSUFFICIENT_EVIDENCE, REJECTED_SOURCE_MISMATCH`

CrossEpisodeEdge는 LocalEdge와 같은 12키를 사용하되 `tgt_episode_no > src_episode_no`, gap은 회차 차이, edge_type은 `callback | plant_payoff | subplot_counterpoint`다. 이전 회차 마지막 장면과 다음 회차 첫 장면을 자동 연결하지 않는다.

FullSeriesArc exact 17키:

```text
series, episodes_total, scenes_total, sequences_total,
logline, central_dramatic_question, theme_statement,
protagonist, antagonist, season_structure,
macro_turning_points, resolution, open_ending,
tone, conflict_persist, series_core_dist, by
```

## 9. 데이터베이스 참조 정책

데이터베이스는 세 등급으로 사용한다.

- Gold Semantic Reference: 검증된 특정 객체의 분석 깊이·고유성 비교
- Structural Reference: 키·ID·FK·coverage·경로 비교
- Anti-pattern Reference: 고정 분할·복사형 Arc·자동 파생·회차 간 LocalEdge·자동 감사의 반례

대상 작품의 기존 분석은 새 저작 완료 전 의미 입력으로 열지 않는다. 새 객체를 잠근 뒤 누락·불일치·legacy contamination 감사에만 사용한다. 새 title·intent_gist·Sequence 의미문이 기존 판본과 정확히 일치하면 직접 재저작으로 인정하지 않는다.

## 10. 검증과 상태

회차 경량 게이트:

- JSON/JSONL parse
- exact keyset·자료형·enum
- Scene ordinal
- Sequence coverage·partition·runtime·turn mapping
- ID·FK
- placeholder와 명백한 exact duplicate
- 체크포인트와 다음 포인터

8회차 블록 강게이트:

- 원본 SHA·scene hash·QuarterAudit 4건/회차
- title·intent exact duplicate
- 고유명·장소·CORE를 마스킹한 골격 반복
- legacy semantic exact match
- Character/Relationship trigger participant
- LocalEdge 실제 인과 감사
- 앙상블 변화 누락
- 보고서와 validator 판정 일치

작품 전체 게이트:

- 전 회차 Stage01–03 잠금
- PayoffCandidate 미처리 0
- 자동 회차 경계 CrossEdge 0
- FullSeriesArc count·span
- manifest·SHA256SUMS
- ZIP CRC와 fresh extraction 재검사

최종 판정 축:

- `STRUCTURAL_CONTRACT_PASS`
- `SEMANTIC_MECHANICAL_PASS`
- `SOURCE_GROUNDED_MANUAL_PASS`
- `PACKAGE_FRESH_EXTRACTION_PASS`

네 축이 모두 PASS일 때만 `PASS_CANDIDATE`; 사용자 명시 승인 뒤에만 `CANONICAL`이다.

저작과 감사를 같은 실행이 동시에 PASS로 만들 수 없다. `author_run_id`와 `audit_run_id`를 분리하고 감사에서 원문 재개방·범위·실패 객체를 기록한다.

## 11. 패키지·계보·허브 경계

실패본을 삭제하거나 덮어쓰지 않고 `QUARANTINE`, `SUPERSEDED`, parent/supersedes 관계를 기록한다. 독립 작품 ZIP은 source lock, quarter audits, Stage01–04, validation, lineage, manifest, SHA256SUMS를 포함하고 원문 대본·장문 대사·embedding·비밀키는 포함하지 않는다.

허브에는 권위 문서, schema·validator, SourceLock metadata, record counts, validation·lineage·handoff를 적재할 수 있다. 원문 대본과 raw 의미 JSONL 전체는 적재하지 않는다.

## 12. 새 세션 실행 지시

```text
V8을 실행 계약으로 사용하라.
대상 작품의 원본과 기존 분석을 분리하고 작품 유형을 판정하라.
계획은 8회차 블록으로 세우되 실제 저작은 회차별 Q1→Q4로 진행하라.
SceneCard는 exact 9키로 작성하고 Python으로 의미를 만들지 마라.
같은 작품의 기존 의미문은 새 저작을 잠근 뒤에만 비교하라.
회차 경량 게이트와 체크포인트 후 다음 회차로 이동하라.
8회차 블록 종료 시 강검증하고 전 회차 Stage01–03 잠금 뒤 Stage04를 수행하라.
```
