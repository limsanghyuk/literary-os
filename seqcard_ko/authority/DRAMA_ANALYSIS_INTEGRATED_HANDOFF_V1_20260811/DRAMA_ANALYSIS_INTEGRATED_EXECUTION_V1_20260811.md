# 한국 드라마 분석 통합 실행서 V1 — Source → Stage01~04 → THICK → R5/R8

문서 ID: `DRAMA_ANALYSIS_INTEGRATED_EXECUTION_V1_20260811`  
상태: `ACTIVE_NEW_SESSION_EXECUTION_HANDOFF`  
상위 의미 권위: `DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10`  
강화 권위: `DB98_REINFORCEMENT_SINGLE_AUTHORITY_V1` + active correction  
THICK overlay: `DB98_THICK_12WORK_CANONICAL_AUTHORITY_20260811`  
R5/R8 파생 권위: `DB98_PLANNER_RUNTIME_12WORK_CANONICAL_PROFILE_V1_1_AUTHORITY_20260811`

---

## 0. 목표

새 세션이 과거 대화를 복원하지 않아도 한 작품을 선택하여 다음 작업을 정확히 수행할 수 있게 한다.

```text
원본 대본 확보/검사
→ SourceLock / SourceFormatAudit / canonical scene map
→ Stage01 SceneCard + EpisodeMeta
→ Stage02 SequenceBlueprint + EpisodeArc
→ Stage03 CharacterArc + RelationshipArc + LocalEdge + PayoffCandidate
→ Stage04 CrossEpisodeEdge + FullSeriesArc
→ CANONICAL THICK Sequence
→ PlannerInput(R5)
→ RuntimeSceneProjection(R8)
→ selfcheck / independent audit / manifest / work_state
→ integration / non-target immutability
→ ZIP / fresh extraction / 재검증
```

분석의 목적은 단순 요약 DB가 아니라, 향후 **검색·비교·학습을 통해 Episode Architect와 Sequence Architect가 기획·구상·설계할 수 있는 의미 재료**를 만드는 것이다.

---

## 1. 작품 선정 및 착수 전 권위 해결

### 1.1 작품 선정

1. 최신 DB의 작품 목록과 후보를 대조한다.
2. 이미 동일 작품이 있으면 `NEW_ANALYSIS`가 아니라 upgrade/reauthor 여부를 판정한다.
3. 전 회차와 최종회가 실제로 존재하는지 확인한다.
4. 파일명만 믿지 말고 첫/중간/최종 회차를 열어 실제 회차가 맞는지 검사한다.
5. 수정조각·삭제본·부분 PDF·중복 최종고를 분리한다.
6. 작품 장르/구조가 기존 DB에 어떤 새로운 설계 경험을 추가하는지도 선정 보고서에 기록한다. 이것은 의미 정본이 아니라 향후 학습 다양성 메타다.

### 1.2 착수 전 반드시 기록할 것

- actual supplied DB/package 이름과 SHA256
- Stage01~04 active authority ID/version
- reinforcement pointer와 active correction
- CANONICAL THICK pointer가 있으면 authority ID
- Planner/Runtime pointer가 있으면 authority ID
- source inventory
- 원본 파일 SHA256
- 추출 text SHA256
- existing work lineage / 기존 작품 hash
- 기존 SceneCard/Sequence/Arc counts
- known hold / source defect

설명할 수 없는 drift는 `HOLD_AUTHORITY_DRIFT`다.

---

## 2. 원본 대본 / SourceLock

### 2.1 최상위 원칙

**모델이 원본 대본을 직접 읽고 이해한 뒤 의미를 저작한다.**

기존 SceneCard, SequenceBlueprint, EpisodeArc, THICK, Arc, Edge는 다음 용도만 허용한다.

- 원본 위치 찾기
- 경계 확인
- 기존 정본과의 불변성 비교
- 관계/복선 후보 탐색
- 출처 후보/참조 검증
- 새 저작의 중복·복사 탐지

새 의미를 기존 의미문에서 복사해서 만들지 않는다.

### 2.2 SourceFormatAudit

회차마다 검사:

- 파일명↔실제 회차
- 인코딩/페이지/본문 누락
- 회차 시작·종료
- 삭제 장면
- 번호 없는 외경/인서트/몽타주/회상
- `38-1`, `38-2` 같은 삽입 장면
- 중복 번호·누락 번호
- source label과 canonical scene ordinal 분리
- line span / offset / source scene hash

### 2.3 SourceLock 최소 역할

- source files inventory
- raw source SHA256
- extracted/normalized text SHA256
- canonical scene ordinal↔source label map
- line span 또는 재현 가능한 위치 참조
- source completeness state
- extraction method/version
- direct-reading attestation 상태

SourceLock는 의미 분석을 대신하지 않는다. **출처의 정체성과 재현성**을 잠근다.

---

## 3. 작업 grain과 독해 절차

### 3.1 의미 저작 원자 단위

**한 회차 전체**다.

긴 회차는 Q1→Q2→Q3→Q4 순서로 나눠 읽을 수 있지만 Q1~Q4는 attention/checkpoint 보조장치일 뿐 canonical act/sequence가 아니다.

### 3.2 최대 8회차 블록

블록은 관리·강감사 단위다. 의미 압축 단위가 아니다.

- 16부: 1–8 / 9–16
- 20부: 1–8 / 9–16 / 17–20
- 24부: 1–8 / 9–16 / 17–24

**각 회차를 독립적으로 같은 품질로 직접 읽고 저작한 뒤** 블록 강감사를 한다.

### 3.3 회차 실행 순서

```text
SourceBoundaryReview
→ 전체 원본 순차 독해
→ Stage01
→ EpisodeMeta
→ Stage02
→ EpisodeArc
→ Stage03
→ episode light selfcheck
→ independent source audit
→ atomic checkpoint
→ 다음 회차
```

전 시즌 Stage01~03가 잠긴 뒤 Stage04/FullSeriesArc를 완성한다.

---

## 4. Stage01 — SceneCard / EpisodeMeta

### 4.1 SceneCard exact 9 keys

`work_id, scene_no, heading, title, intent_gist, core, core2, skin, by`

필드 의미:

- `scene_no`: canonical ordinal, 1..N 연속
- `heading`: 원문 장면 위치와 대응
- `title`: 장면의 구체 행위/상황을 식별하는 압축명
- `intent_gist`: 장면이 왜 존재하는지, 실제로 무엇을 전진시키는지
- `core/core2`: 16 CORE enum 내 기능
- `skin`: 분위기/표면 표현
- `by`: 저작 주체

금지:

- 대사 마지막 문장 복사
- 모든 씬에 동일한 “관계가 진전된다” 골격
- source heading만 바꾼 요약
- Python이 의미·CORE를 결정

### 4.2 EpisodeMeta exact 5 keys

`work_id, scene_count, core_dist, episode_function, by`

`scene_count/core_dist`는 결정론 검산 가능하지만 `episode_function`은 회차 전체를 다시 읽고 의미적으로 저작한다.

---

## 5. Stage02 — SequenceBlueprint / EpisodeArc

### 5.1 SequenceBlueprint exact 18 keys

`seq_id, work_id, episode_no, seq_index, member_scene_nos, scene_span, scene_budget, sequence_intent, goal, obstacle, value_shift, turn_type, turn_class, core_mix, pov_char, place_cluster, runtime_share, by`

핵심:

- 시퀀스 경계는 **goal–obstacle–turn의 의미 연속성**으로 결정한다.
- 장면 수 균등분할 금지.
- `member_scene_nos`는 전 씬을 빈틈/중복 없이 타일링한다.
- `sequence_intent`는 왜 이 묶음이 하나의 서사 단위인지 말해야 한다.
- `goal`은 인물/집단의 현재 추동 목표.
- `obstacle`은 구체 저항.
- `value_shift`는 from→to의 실질 상태 이동.
- `turn_type/turn_class`는 실제 끝 전환과 일치.
- `core_mix`는 member SceneCard에서 실제 등장한 core/core2만 사용.

### 5.2 EpisodeArc exact 13 keys

`work_id, episode_no, scene_count, sequence_count, dramatic_question, act_structure, entry_state, exit_state, turning_point, central_conflict_axis, episode_function, core_dist, by`

EpisodeArc는 SceneCard/Sequence를 재서술하는 회차 요약이 아니다.

반드시 설명:

- 회차 진입 상태
- 이번 회차의 극적 질문
- 중앙 갈등축
- 주요 전환점
- 회차 종료 후 무엇이 달라졌는가

---

## 6. Stage03 / Stage04

Stage03/04 exact keyset과 enum은 **활성 V10 exact registry/authority를 그대로 따른다.** 이 통합 문서는 별도 변형 스키마를 만들지 않는다.

### 6.1 CharacterArc

인물×회차의 **상태와 변화**를 기록한다. 단순 등장 빈도나 사건 요약이 아니다.

### 6.2 RelationshipArc

관계쌍×회차의 관계 상태와 변화. 복합 인물 묶음을 하나의 relation entity로 만들지 않는다.

### 6.3 LocalEdge

동일 회차 내부 causal edge만.

- `src_episode_no == tgt_episode_no`
- `gap_episodes == 0`

회차를 넘는 bridge를 LocalEdge로 넣지 않는다.

### 6.4 PayoffCandidate / Stage04 CrossEpisodeEdge

후보와 확정 장거리 연결을 구분한다.

- 최종회 집결/결혼식 참여/주제 유사성만으로 payoff 승격 금지
- 실제 plant→escalation/callback→payoff/reveal의 증거를 원문으로 확인
- 후보 100%를 처분한 뒤 Stage04를 잠근다.

### 6.5 FullSeriesArc

전 회차 의미층이 잠긴 뒤 fan-in한다. 전체 시즌의 질문·주제·주인공/대립축·거시 전환·해결을 저작한다.

---

## 7. THICK Sequence — 시퀀스를 기획 가능한 의미 단위로 강화

### 7.1 목적

기존 SequenceBlueprint가 경계/목표/장애/turn을 담는다면 THICK는 downstream planner가 실제로 소비할 수 있도록 **인물 압력·구체 사건·정보 이동·장기 연결·장면별 기능**을 보존한다.

### 7.2 exact top-level 14 keys

`schema, work_id, episode_no, seq_id, seq_index, member_scene_nos, cast, event, info_shift, plant_payoff, scene_notes, evidence_refs, source_hashes, by`

중첩 exact keysets는 `THICK_SEQUENCE_EXACT_SCHEMA_CONTRACT_V1_0_1_FINAL_20260811.json`을 따른다.

### 7.3 authoring 순서

1. **INBOUND** — 이전 장면/시퀀스에서 무엇이 들어오는지 파악
2. `cast[]` — 등장인물 명단이 아니라 sequence-specific desire/function
3. `event` — 실제 causal chain + 핵심 상호작용 + irreversible turn/gain/loss를 구체화
4. `info_shift[]` — 누가 무엇을 믿고/알고/접근할 수 있었으며 어떻게 바뀌는지
5. `plant_payoff[]` — source-supported thread만. 거짓 link 금지
6. `scene_notes[]` — 모든 member scene 정확히 1회, 1~8 functional propositions
7. **OUTBOUND** — 다음 장면/시퀀스가 무엇을 상속하는지 확인

### 7.4 2026-08-11 품질 앵커

CANONICAL 12작 main diversity:

- 경성스캔들 0.799
- 결혼못하는남자 0.779
- 공주가돌아왔다 0.766
- 내이름은김삼순 0.761
- 내여자친구는구미호 0.759
- 난폭한로맨스 0.749
- 강남엄마따라잡기 0.826
- 너의목소리가들려 0.814
- 개와늑대의시간 0.816
- 101번째프로포즈 0.782
- 가을동화 0.758
- 궁 0.783

운영상 main diversity floor는 0.748이며, auxiliary 지표는 **진단용**이다. 특히 info diversity 0.70 같은 값을 hard gate로 오해해 정상 의미를 점수 맞춤 재작성하지 않는다.

### 7.5 금지된 가짜 THICK

- `event`를 Stage02 `sequence_intent` 그대로 복사
- `scene_notes`를 Stage01 `intent_gist` 그대로 전량 복사
- `cast.desire_or_function`을 scene note/sequence summary 재기술
- `info_shift`를 정보 변화 없이 scene summary로 채움
- 모든 시퀀스에 같은 generic phrase

`궁` 초기 후보에서 이러한 문제가 실제로 발견되어 후보가 폐기되고 직접독해 재저작되었다. **구조 valid ≠ semantic independent authorship**다.

---

## 8. PlannerInput(R5) — 회차 기획 경계 packet

R5는 N화 정답 요약이 아니다.

> **N화를 설계하기 직전 N-1까지 확정된 상태와 미해결 장기 부담을 전달한다.**

### exact top-level 14 keys

`schema, work_id, episode_no, previous_exit_state, character_states, relationship_states, unresolved_payoffs, active_causal_threads, remaining_episode_count, subplot_debt, character_debt, world_constraints, target_refs, source_hashes`

### EP01

- previous_exit_state=null
- states/threads/debt arrays empty

### EP02+

- previous_exit_state: N-1 EpisodeArc
- character_states: N-1 CharacterArc 인물별 최종 상태
- relationship_states: N-1 RelationshipArc 관계쌍별 최종 상태
- unresolved_payoffs/active threads: N-1까지 실제 등장한 thread history만
- 마지막 상태가 PAYOFF면 닫힘
- subplot_debt/character_debt: 실제 열린 부담이 있으면 채운다
- 미래 회차의 답을 debt에 쓰지 않는다

권장 bounded context: unresolved ≤24, subplot debt ≤8.

### BLIND/FUTURE LEAK 원칙

`episode_no=N` 자체는 누수가 아니다. 누수 판정은 **source_episode/through_episode/available_through_episode/참조 실제 내용**이 planning boundary N-1을 넘는지를 검사해야 한다.

대상 회차 `target_refs`가 canonical target 파일을 가리키는 것은 offline 평가/검증에서는 허용될 수 있으나, **Blind Forward generation input에서는 해당 target ref를 따라 읽지 못하도록 접근 차단**해야 한다.

---

## 9. RuntimeSceneProjection(R8)

R8은 독립 의미 저작층이 아니다.

> CANONICAL THICK + 같은 회차 R5를 Scene 하나가 소비할 수 있도록 deterministic projection한다.

### exact top-level 15 keys

`schema, work_id, episode_no, scene_no, seq_id, characters, primary_pov, secondary_pov, character_states, relationship_states, event_context, info_context, plant_payoff_context, functional_propositions, source_refs`

### exact parity

- SceneCard scene 1개당 R8 정확히 1개
- `event_context == THICK.event`
- `sequence_function == THICK.cast.desire_or_function`
- info/payoff는 scene membership filter
- functional_propositions == 해당 THICK scene note
- source_refs는 THICK evidence 보존

R8에서 새 사건·감정·정보를 창작하면 FAIL.

---

## 10. Provenance — 여섯 hash와 SOURCE evidence

THICK record마다 최소 여섯 provenance hash를 유지한다.

- `baseline_artifact_sha256`
- `source_text_sha256`
- `scene_card_file_sha256`
- `sequence_blueprint_file_sha256`
- `episode_arc_file_sha256`
- `source_lock_sha256`

SOURCE evidence는 deterministic line addressing이 가능한 경우 `:Lx-Ly`까지 해석 가능해야 한다.

R5 provenance는 planning boundary source를 식별한다.

R8 provenance는 **현재 THICK revision hash + exact scene coverage**가 핵심이다.

---

## 11. Selfcheck와 독립 감사

### episode light selfcheck

- exact schema
- source/scene/seq FK
- scene coverage
- 의미문 generic/repetition
- 인물별 function specificity
- info before/after consistency
- plant/payoff direction
- adjacent sequence handoff

### block strong audit (≤8 episodes)

- 모든 episode selfcheck 재검산
- Stage01~04 hash immutability
- cross-episode info continuity
- work-level thread continuity
- proposition grain distribution
- evidence density
- boilerplate scan
- R5 future leak/debt carry-over
- R8 scene coverage/parity

### independent audit

저작 run과 감사 run을 분리한다. 저작 스크립트가 자기 산출물에 “semantic PASS”를 자동 부여하지 않는다.

---

## 12. manifest / work_state / checkpoint

`manifest`는 **현재 활성 산출물의 사실과 hash**를 말한다.

`work_state`는 **어디까지 완료됐고 다음에 무엇을 해야 하는지**를 말한다.

최소 기록:

- work_id
- authority ids/versions
- baseline/package hash
- source/sourceLock hash
- last completed episode/block
- stage status
- THICK hashes
- R5/R8 hashes
- structural/selfcheck results
- semantic audit results
- provenance status
- non-target immutability status
- holds/warnings
- exact next_action
- updated_at

파일 timestamp나 채팅 기억보다 work_state/checkpoint가 우선한다.

---

## 13. 품질 균질화

품질은 “전 회차 schema PASS”가 아니라 **기준 회차와 같은 직접독해·의미 밀도·출처 밀도**를 유지해야 한다.

다음은 hard/strong review 신호다.

- 3회 연속 장면의 ≥90%가 functional proposition 정확히 1개뿐
- reference episode 이후 evidence density 급락
- cast function이 여러 인물에 동일 문장
- event 길이/구조가 전 회차 동일 skeleton
- info_shift가 감정 변화 또는 summary로 대체
- thread_id가 회차마다 무의미하게 새로 생김
- R5 unresolved/debt가 장기 작품 전 시즌 기계적으로 empty
- Stage01/02 텍스트 exact-copy 비율이 비정상적으로 높음

자동 지표는 **review/localization**을 위한 것이다. 숫자 맞춤 의미 재작성 금지.

---

## 14. Invalidation / downstream closure

다음이 변경되면 R5/R8을 현재로 사용하지 않는다.

- EpisodeArc
- CharacterArc / RelationshipArc
- THICK/plant_payoff history
- sequence membership
- SceneCard membership

상태를 `REGEN_REQUIRED`로 내리고 재생성한다.

완료 invariant:

`THICK_PASS + SOURCE_PASS + MANIFEST_MATCH + DOWNSTREAM_CLOSURE_PASS + AUTHORITY_POINTER_PASS + FRESH_EXTRACTION_PASS`

THICK를 고쳤는데 옛 Runtime이 active면 `STALE_RUNTIME`이며 작품 완료가 아니다.

---

## 15. 작품 완료 및 DB 통합

1. 대상 작품 모든 회차 Stage01~04 완료
2. 모든 THICK sequence 완료
3. episode light audits PASS
4. block strong audits PASS
5. source/provenance audit PASS
6. R5 V1.1 생성·future leak/debt PASS
7. R8 생성·1:1/parity PASS
8. work_state/manifest 갱신
9. 대상 외 파일 hash 동결 비교
10. staging DB append/replace
11. ZIP 생성
12. 별도 디렉터리 fresh extraction
13. portable validator 재실행
14. schema/provenance/coverage/hash 모두 PASS
15. active authority 절차에 따라 PASS_CANDIDATE 또는 CANONICAL 상태 지정

기존 작품의 일부 계층만 다른 판본에서 가져와 혼합하지 않는다. 장면 ordinal/source hash lineage가 다르면 작품 단위 전량 유지 또는 전량 교체한다.

---

## 16. 새 작품과 기존 작품 보강의 차이

### 신규 작품

`SourceLock → Stage01→02→03→04 → THICK → R5/R8 → package/integration`

### 기존 Stage01~04 작품에 THICK/R5/R8 추가

Stage01~04를 보호 baseline으로 고정하고 **원본을 다시 직접 읽어 THICK 의미를 저작**한다. R5/R8 때문에 core Stage를 바꾸지 않는다.

### 기존 THICK 품질 보강

실패 필드만 원본 재독해 후 부분 재저작할 수 있으나, manifest/hashes와 downstream invalidation을 반드시 갱신한다.

---

## 17. 현재 12작 CANONICAL reference set

이 12작은 새 작품 품질 비교의 **참고 앵커**다. 새 작품 의미를 복제하기 위한 템플릿이 아니다.

`경성스캔들, 결혼못하는남자, 공주가돌아왔다, 내이름은김삼순, 내여자친구는구미호, 난폭한로맨스, 강남엄마따라잡기, 너의목소리가들려, 개와늑대의시간, 101번째프로포즈, 가을동화, 궁`

CANONICAL THICK: 1,795 sequence records.  
R5/R8: 12/12 works, 203 episodes, 12,979 runtime scene records.

---

## 18. 새로운 세션에서 바로 실행할 최소 명령

> `DRAMA_ANALYSIS_CURRENT_INTEGRATED_POINTER.json`을 먼저 읽고 Stage01~04 V10, DB98 reinforcement pointer, CANONICAL THICK pointer, Planner/Runtime pointer의 권위 관계를 확인하라. 대상 작품을 정한 뒤 원본 inventory와 SourceLock을 잠그고 한 회차 전체를 Q1→Q4 순서로 직접 독해하라. Stage01~04를 exact schema로 저작하고 회차마다 light selfcheck/독립 원문 감사를 수행하라. 전 시즌 Stage01~04가 잠기면 모든 인간 sequence를 원본으로 재독해하여 THICK를 저작하라. THICK는 cast/event/info_shift/plant_payoff/scene_notes를 독립 의미로 저작하고 six-hash provenance 및 SOURCE line refs를 보존하라. 이후 PlannerInput V1.1을 N-1 boundary만으로 만들고 future leak/debt를 검사한 뒤 Runtime V1을 THICK에서 deterministic projection하라. manifest/work_state를 갱신하고 non-target immutability와 fresh extraction validator를 모두 통과하기 전에는 완료를 선언하지 마라.`
