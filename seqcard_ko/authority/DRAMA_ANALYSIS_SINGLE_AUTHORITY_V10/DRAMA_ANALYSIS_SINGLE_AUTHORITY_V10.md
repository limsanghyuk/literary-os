# 한국 드라마 분석 단일 권위 V10

Authority ID: `DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10`  
Version: `10.0.0`  
Effective date: `2026-07-24`  
Status: `ACTIVE_SINGLE_AUTHORITY`

## 0. 권위·목적·충돌 처리

이 문서 하나가 한국 드라마 Stage01–04 분석의 유일한 의미·운영 권위다. `schemas/`, `tools/`, `templates/`, `examples/`는 실행 부속물이며 독립적인 의미 권위가 아니다. 부속물과 본문이 충돌하면 임의 해석하지 말고 `AUTHORITY_CONTRACT_DRIFT`로 중단한다.

V1–V9, 과거 GPT·Claude 매뉴얼, 세션 보고서와 작품 산출물은 역사·감사·마이그레이션 자료다. 충돌하면 V10이 우선한다.

적용 범위:

- 신규 한국 드라마 Stage01–04 분석
- 기존 작품 원문 대조 재저작·업그레이드
- 회차·블록·전 시즌 체크포인트와 중단 복구
- 독립 작품 패키지와 데이터베이스 신규 편입·교체
- 개발자 허브 인계와 새 세션 부트스트랩

최상위 원칙:

> 원본을 직접 읽고 이해한 뒤 고유하게 저작한다. 도구는 판단을 만들지 않고, 판단을 보존·검증·운반한다.

기본 정책:

- 원본 직접독해 우선
- 한 회차 전체 순차 독해
- canonical SceneCard exact 9키
- Python 의미 생성 금지
- 저작과 독립 감사 run 분리
- 부분 원본 Stage04 차단
- 사용자 승인 전 `CANONICAL` 금지

## 1. 분석의 정의와 금지 행위

드라마 분석은 장면 순서대로 원문을 읽고 다음을 구분한 뒤 정본 스키마에 압축하는 close-reading 저작이다.

1. 실제 행동
2. 말하거나 숨긴 전략
3. 새로 생기거나 변한 정보
4. 선택·거부·유예
5. 회차·시리즈 구조 기능
6. 다음 장면·시퀀스를 미는 잔여 동력

다음은 분석이 아니다.

- 대사·지문·마지막 행을 의미 필드로 복사
- 기존 대상 작품의 `title`, `intent_gist`, `action`을 새 필드로 이동
- 고유명만 바꾼 반복 문형
- 장면 수 균등분할 시퀀스
- 회차 요약을 Arc마다 복사
- 메타데이터에서 Stage03·04 자동 파생
- 저작 스크립트가 동시에 만든 “수동 감사 PASS”
- 구조 PASS를 원문 의미 PASS로 확대
- 최종회 집결·결혼식 참석·주제 유사성만으로 장거리 회수를 승격

## 2. 입력·작품 선정·SourceFormatAudit

### 2.1 필수 입력

- 정본 작품명
- 접근 가능한 모든 원본 회차 파일
- 쓰기 가능한 run 경로
- 최신 권위·manifest·validator
- 기존 작품이면 기존 lineage와 DB 위치
- DB 편입 직전 실제 최신 DB root와 작품 수

### 2.2 신규 작품 선정

신규 작품은 다음 순서로 선정한다.

1. 현재 DB 작품명·work_id와 후보 목록 대조
2. 전 회차와 최종회 존재 여부 확인
3. 마지막 회차의 실제 종결 표지 또는 서사 종결 확인
4. 회차별 파일 크기·본문 길이·장면 수 이상치 탐지
5. 중복 판본 중 완전한 최종고 선택
6. 수정 조각·추가 장면 조각·부분 PDF를 정본 본편으로 오인하지 않음
7. 제외 후보와 이유를 `NEW_WORK_SELECTION_REPORT`에 기록

전 회차가 있다고 표시돼도 특정 회차가 수정 조각뿐이면 `FULL_SERIES_SOURCE_LOCKED`가 아니다.

### 2.3 컨테이너·문서 형식 추출

PDF, HWP, TXT, DOCX 등 원본 형식은 의미 저작 전에 결정론적으로 추출한다.

허용:

- HWP OLE/본문 스트림 추출
- PDF 텍스트 추출과 페이지·표제 감사
- 인코딩 복구
- 줄바꿈·제어문자 정규화

필수 회귀검사:

- 원본 파일 SHA256
- 추출 텍스트 SHA256
- 재추출 시 동일 해시 또는 정규화 차이 설명
- 첫 회차·중간 회차·최종회 표본의 장면 표제와 본문 대조
- 추출기 변경 시 이미 잠긴 회차 source hash 회귀검사

추출기는 의미문을 만들지 않는다.

### 2.4 SourceFormatAudit 필수 항목

- 파일명과 실제 회차 내용 일치
- 인코딩·페이지·본문 누락
- 회차 시작·종료 표제
- 숫자 장면뿐 아니라 번호 없는 외경·전경·인서트·몽타주·회상 전환
- 삽입 장면(`38-1`, `38-2`)과 누락 번호
- 삭제 지시 장면과 반복 삽입 장면
- 중복·오명명·부분 판본
- canonical scene ordinal과 원문 source label 분리
- line span·offset·scene hash
- 원본 완전성

### 2.5 삭제 장면과 source label

- `삭제`, `삭제해주세요`, `편집 삭제`가 명시된 장면은 최종고 기준으로 canonical scene에서 제외한다.
- 삭제 표지는 남았지만 실제 방송·후속 인과에 필요한 장면이면 근거를 기록하고 독립 감사한다.
- 원문 번호가 빠지거나 중복돼도 `scene_no`는 1부터 N까지 연속 canonical ordinal이다.
- 원문 표제 번호·문자열은 `source_label` 또는 source index에 보존한다.
- source label을 canonical ordinal로 강제 변환하지 않는다.

### 2.6 원본 완전성 상태

- `FULL_SERIES_SOURCE_LOCKED`: 전 회차·결말 완전, 전 시즌 분석 가능
- `PARTIAL_ARCHIVE_EPISODE_PILOT_ONLY`: 지정 회차 파일럿만 가능
- `SOURCE_COMPLETENESS_UNVERIFIED`: 총수·결말 미확인, 전 시즌 릴리스 차단
- `RECOVERED_BOUNDARY_LOCKED`: 회차 표제 누락을 앞뒤 사건·원본 위치로 복원, 근거 기록
- `SOURCE_HOLD`: 판본·회차·장면 경계를 재현할 수 없어 중단

부분 원본으로 Stage04·FullSeriesArc·전체 작품 PASS를 만들지 않는다.

### 2.7 작품 분류

- `NEW_ANALYSIS`
- `NORMAL_UPGRADE`
- `STAGE01_PARTIAL_REAUTHOR`
- `STAGE02_PARTIAL_REAUTHOR`
- `STAGE02_FULL_REAUTHOR`
- `STAGE03_REAUTHOR_REQUIRED`
- `FULL_REAUTHOR_REQUIRED`
- `SOURCE_HOLD`

서로 다른 판본의 Stage를 혼합하지 않는다. 장면 ordinal 또는 source hash lineage가 다르면 작품 단위 전량 유지 또는 전량 교체한다.

## 3. 작업 단위와 순차 독해

의미 저작의 원자 단위는 **한 회차 전체**다.

```text
EPxx SourceBoundaryReview
→ 원본 전체 순차 독해
→ Stage01 SceneCard
→ 회차 전체 재검토·EpisodeMeta
→ Stage02 SequenceBlueprint
→ EpisodeArc
→ CharacterArc·RelationshipArc
→ LocalEdge·PayoffCandidate
→ 회차 경량 게이트
→ 독립 원문 감사
→ 원자적 체크포인트
→ 다음 회차
```

앞 회차가 `EPISODE_CHECKPOINT_LOCKED`가 아니면 다음 회차를 잠그지 않는다.

Q1–Q4는 선택적 읽기·저장 보조장치다. 정본 필수 산출물이나 극적 4막이 아니다.

최대 8회차 블록은 계획·전달·통합감사 단위다. 동시 의미 생성 단위가 아니다.

- 16부작: EP01–08 / EP09–16
- 20부작: EP01–08 / EP09–16 / EP17–20
- 24부작: EP01–08 / EP09–16 / EP17–24

## 4. 중단 방지·원자적 저장·진행 보고

### 4.1 시간 계약

- 20분: 체크포인트 준비
- 25분: 산출물·상태·checksum 저장 필수
- 30분: 체크포인트 없는 의미 작업 하드스톱
- 한 장기 실행에서 여러 회차를 잠그지 않음

### 4.2 원자적 쓰기

```text
<file>.tmp
→ JSON/JSONL parse
→ flush/fsync
→ 기존 파일 lineage 백업
→ atomic rename
→ SHA256
→ manifest·work_state 동기화
```

### 4.3 진행 보고

사용자에게 회차 완료·감사 오류·교정·체크포인트 상태를 중간 보고한다. “독해 중”, “저작 완료”, “파일 저장 완료”, “독립 감사 PASS”를 구분한다. 파일이 없으면 완료로 보고하지 않는다.

### 4.4 RunJournal 이벤트

`RUN_START, SOURCE_OPENED, SOURCE_BOUNDARY_LOCKED, SEMANTIC_AUTHORING_START, AUTHOR_LOCKED, AUDIT_START, AUDIT_END, CHECKPOINT_PREPARED, CHECKPOINT_LOCKED, VALIDATION_START, VALIDATION_END, RUN_STOP, INTERRUPTION_DETECTED, RECOVERY_START, RECOVERY_LOCKED`

필수 필드: `timestamp, run_id, event, work_id, episode_no, stage, artifact_sha256, next_action`.

### 4.5 중단 복구

1. 프로세스·수정시각·`.tmp` 조사
2. JSON/JSONL parse와 SHA 확인
3. `work_state`와 검증 보고서 선후 비교
4. 최신 정상 `CHECKPOINT_LOCKED`로 후퇴
5. 저장되지 않은 사용자 보고를 무효화
6. 독립 감사 미완료면 구조 PASS만 보존
7. 복구 원장과 다음 안전 포인터 기록

안전 재진입 상태: `EPISODE_CHECKPOINT_LOCKED`, `BLOCK_CHECKPOINT_LOCKED`, `FULL_SERIES_CHECKPOINT_LOCKED`.

## 5. 도구와 언어모델의 경계

### 허용

- 압축 해제·inventory·인코딩 복구
- HWP/PDF/DOCX 본문 추출
- heading·source label·ordinal·line span·offset 탐지
- source index·SHA256
- JSON/JSONL 직렬화
- exact keyset·자료형·enum·ID·FK·coverage 검사
- count·core_dist·runtime_share·core_mix 재계산
- 반복 골격·placeholder·장문 복사 탐지
- manifest·ZIP·CRC·fresh extraction

### 금지

- SceneCard 의미·CORE 생성
- Sequence 의미 생성
- EpisodeArc·CharacterArc·RelationshipArc 의미 생성
- LocalEdge·PayoffCandidate 판단
- CandidateDisposition·CrossEpisodeEdge 자동 판정
- FullSeriesArc 의미 생성

결정론적 교정은 correction ledger에 이전 SHA·수정 필드·이유를 기록한다. 의미 오류는 원문을 다시 읽고 새 author run으로 재저작한다.

## 6. 공통 ID·enum

- 회차 work_id: `<work>_<NN>`
- Sequence ID: `<work>_<NN>_S<II>`
- LocalEdge ID: `<work>_e<NN><III>`
- PayoffCandidate ID: `<work>_p<NN><III>`
- CrossEpisodeEdge ID: `<work>_x<III>`

CORE 16종:

`ESTABLISH, ORACLE, INTRO, BOND, CONFLICT, REVERSAL, LOSS, PUNISH, REVELATION, REUNION, RELIEF, ROMANCE, PERIL, RESCUE, DESIRE, HOOK`

Sequence turn mapping:

- `RISE, BOND, PUNISH → RISE`
- `FALL, LOSS → FALL`
- `REVEAL, ORACLE, REVERSAL → REVEAL`
- `STALL, HOOK, CONFLICT → STALL`

## 7. Stage01 — SceneCard·EpisodeMeta

### SceneCard exact 9키

```text
work_id, scene_no, heading, title, intent_gist,
core, core2, skin, by
```

- `heading`: 원문 provenance와 대응
- `title`: 이 장면만의 고유 전환
- `intent_gist`: 욕망·압력·행동·정보·선택·변화의 해석
- `core/core2`: 1차·2차 극적 기능, core2 null 가능
- `skin`: 장소·시간·표면 행동·소품의 구체성

품질 규칙:

- 중심 행위자와 행동을 틀리지 않음
- 결과·다음 회차 사건을 앞당기지 않음
- 무성 전환에 억지 목표를 부여하지 않음
- 원문 마지막 행·제작 표지를 결과처럼 복사하지 않음
- title·intent·skin 상호 반복 금지
- 다른 장면에도 붙는 추상문 금지

EpisodeMeta exact 5키:

```text
work_id, scene_count, core_dist, episode_function, by
```

`scene_count`, `core_dist`는 Stage01에서 결정론적으로 재계산한다.

## 8. Stage02 — SequenceBlueprint

exact 18키:

```text
seq_id, work_id, episode_no, seq_index,
member_scene_nos, scene_span, scene_budget,
sequence_intent, goal, obstacle, value_shift,
turn_type, turn_class, core_mix, pov_char,
place_cluster, runtime_share, by
```

불변식:

- 모든 장면 정확히 한 시퀀스 포함
- 중복·누락 0
- member_scene_nos 연속·오름차순
- scene_span·scene_budget 일치
- runtime_share 합계 1.0 ± 1e-6
- sequence_count / scene_count ≥ 0.11
- core_mix는 실제 member SceneCard core/core2만 사용

경계 기준:

- 목표 주체·목표 변화
- 장애의 성격 변화
- 정보·관계·권력 가치 변화
- 새 행동 단위 시작
- 전환 결과 완료

밀도 하한을 맞추기 위한 기계 분절은 금지한다. 하한 미달 시 원문에서 실제 독립 행동 단위를 다시 찾는다.

## 9. Stage03 — 회차 의미 렛저

### 9.1 EpisodeArc exact 13키

```text
work_id, episode_no, scene_count, sequence_count,
dramatic_question, act_structure, entry_state, exit_state,
turning_point, central_conflict_axis, episode_function,
core_dist, by
```

모든 Sequence를 gap·overlap 없이 덮고, 숫자상 4등분을 금지한다.

### 9.2 CharacterArc exact 8키

```text
work_id, character, episode_no, state_label,
state_delta, trigger_scene_no, by, evidence
```

실제 상태 변화가 있는 인물만 기록한다. trigger 장면에 해당 인물이 실제 등장·발화·행동해야 한다.

### 9.3 RelationshipArc exact 9키

```text
work_id, char_a, char_b, episode_no, relation_state,
relation_delta, trigger_scene_no, evidence, by
```

관계 엔터티 규칙:

- `char_a`, `char_b`는 각각 단일 canonical 인물이다.
- `A·B`, `A/B`, `두친모`, `팀원들` 같은 복합 가상 인물을 금지한다.
- 별칭은 `ENTITY_ALIAS_REGISTRY`에서 canonical 이름으로 정규화한다.
- 양쪽 인물이 같은 장면에서 상호작용하거나 직접 통화·교신해야 한다.
- `(A,B)`와 `(B,A)` 중복 금지.
- 실제 변화 수만 기록하며 회차별 고정 수량을 유지하지 않는다.

### 9.4 LocalEdge exact 12키

```text
edge_id, work_id, edge_type,
src_episode_no, src_scene_no,
tgt_episode_no, tgt_scene_no,
gap_episodes, label, confidence, note, by
```

- `edge_type=causal`
- 동일 회차
- `gap_episodes=0`
- `label=target SceneCard.core`

반사실 질문: source가 없었다면 target이 발생하지 않거나 실질적으로 달라지는가? 단순 인접·정서 연속·같은 시퀀스는 인과가 아니다.

### 9.5 PayoffCandidate exact 7키

```text
candidate_id, work_id, episode_no, scene_no,
edge_type_guess, description, by
```

허용 guess: `plant_payoff | callback | subplot_counterpoint | resolved_here`. 구체적 정보·약속·소품·위협·선택만 남긴다.

## 10. Stage04 — 전 시즌 fan-in

전 회차 Stage01–03 강검증·잠금 뒤 별도 실행한다.

```text
후보 목록화
→ 원 장면 확인
→ 후속 실제 장면 확인
→ source/target 의미 대조
→ 후보별 disposition
→ 검증된 CrossEpisodeEdge
→ FullSeriesArc 신규 종합
```

### 10.1 CandidateDisposition

- `PROMOTED_CROSS_EDGE`
- `RECLASSIFIED_LOCAL_OR_ADJACENT_CAUSAL`
- `RESOLVED_WITHIN_EPISODE`
- `REJECTED_DUPLICATE`
- `REJECTED_INSUFFICIENT_EVIDENCE`
- `REJECTED_SOURCE_MISMATCH`

미처리 후보 1건이면 실패다.

### 10.2 승격 테스트

다음 네 질문을 모두 통과해야 `PROMOTED_CROSS_EDGE`다.

1. source에 구체적 정보·선택·소품·약속이 있는가?
2. target이 그 요소를 실제로 회수·변형·대조하는가?
3. 단순 시간 경과·인접·주제 유사성이 아닌가?
4. 동일 의미의 대표 후보가 이미 승격되지 않았는가?

다음은 단독 근거로 승격할 수 없다.

- 최종 결혼식·장례식·행사에 함께 참석
- 모든 인물이 한 장면에 모임
- 사랑·가족·성장 같은 일반 주제 반복
- source 이후 계속 등장했다는 사실
- 미래 상상 장면을 실제 해결로 오인

### 10.3 edge type 판정

- `plant_payoff`: source가 후속 사건을 설치하고 target이 회수
- `callback`: 의미·대사·행동이 변형 반복되어 이전 장면을 환기
- `subplot_counterpoint`: 다른 줄거리·미래상·공간 배치가 주축과 구조적으로 대조

인과가 아닌 반복을 `plant_payoff`로 과장하지 않는다.

### 10.4 CrossEpisodeEdge

LocalEdge와 같은 12키. `tgt_episode_no > src_episode_no`, gap은 회차 차이, label은 target core. 자동 회차 경계 bridge 금지.

### 10.5 FullSeriesArc exact 17키

```text
series, episodes_total, scenes_total, sequences_total,
logline, central_dramatic_question, theme_statement,
protagonist, antagonist, season_structure,
macro_turning_points, resolution, open_ending,
tone, conflict_persist, series_core_dist, by
```

season_structure는 실제 서사 이동에 따라 작성하고 기계적 분기를 금지한다.

## 11. 기존판·SameWorkLegacyLock·품질 비교

대상 작품 기존 의미문은 author lock 전 열지 않는다. 원본·ordinal·파일명·해시만 사용할 수 있다.

새 객체 잠금 뒤 감사:

- 기존 title/intent exact match
- 고정 시퀀스 경계 반복
- 미래 정보 혼입 재발
- Arc evidence 복사
- 후보·CrossEdge 무비판 재사용

교체 수용 전 같은 객체 기준으로 비교한다.

- 장면 의미 정확성
- 문장 고유성·압축성
- 시퀀스 경계
- EpisodeArc entry→exit
- Arc trigger
- LocalEdge 인과
- 후보 처분 추적성
- 원문·package 재현성
- 신판의 약점

레코드 수 증가만으로 품질 향상이라 하지 않는다.

## 12. 검증 체계

### 회차 경량 게이트

- JSON/JSONL parse
- exact keyset·자료형·enum
- Scene ordinal·source index
- EpisodeMeta count·core_dist
- Sequence coverage·partition·runtime·turn mapping·core_mix
- ID·FK
- placeholder·exact duplicate
- work_state·next pointer·checksum

### 블록 강게이트

- 원본 파일 SHA·추출 텍스트 SHA·scene hash
- SourceFormatAudit anomaly 처리 완료
- title·intent exact duplicate
- 고유명·장소·CORE 마스킹 골격 반복
- legacy semantic exact match
- Character/Relationship trigger participant
- 복합 관계 엔터티·별칭 미정규화 0
- LocalEdge 실제 인과와 target core
- 앙상블 변화 누락
- 미래 회차 정보 혼입
- author/audit run 분리
- 보고서와 machine verdict 일치

### 작품 전체 게이트

- 전 회차 Stage01–03 잠금
- 후보 disposition 100%
- 자동 회차 경계 bridge 0
- CrossEdge source/target·target core·유형 감사
- 과승격 표본과 대표 후보 중복 감사
- FullSeriesArc counts·season span
- manifest·SHA256SUMS
- ZIP CRC·UTF-8 파일명·경로 호환
- 새 위치 fresh extraction 후 동일 validator 재실행

### 최종 네 축

- `STRUCTURAL_CONTRACT_PASS`
- `SEMANTIC_MECHANICAL_PASS`
- `SOURCE_GROUNDED_MANUAL_PASS`
- `PACKAGE_FRESH_EXTRACTION_PASS`

네 축 모두 PASS일 때만 `PASS_CANDIDATE`, 사용자 명시 승인 뒤에만 `CANONICAL`이다.

## 13. 저작·감사 분리

`author_run_id != audit_run_id`.

저작 스크립트는 author attestation만 만들 수 있다. 독립 감사자는 원문을 재개방하고 다음을 기록한다.

- source range와 scene coverage
- 고위험 장면
- Sequence 경계
- EpisodeArc
- trigger·edge
- 별칭·관계 엔터티
- 실패와 교정
- verdict

감사자가 원문을 열지 않았거나 저작 실행이 자동 PASS를 만들면 수동 의미 PASS는 무효다.

## 14. 상태·계보

허용 상태:

`DRAFT, SOURCE_HOLD, SOURCE_PARTIAL_PILOT_ONLY, AUTHOR_LOCKED_AUDIT_PENDING, EPISODE_CHECKPOINT_LOCKED, BLOCK_CHECKPOINT_LOCKED, FULL_SERIES_CHECKPOINT_LOCKED, QUARANTINE, PASS_CANDIDATE, PASS_CANDIDATE_AFTER_SEMANTIC_CORRECTION, CANONICAL, SUPERSEDED`

실패본은 삭제·덮어쓰지 않는다. `parent_run_id, supersedes, superseded_by`, 실패 이유와 복구 지점을 기록한다.

## 15. 패키지·ZIP 호환·DB·허브

### 15.1 독립 작품 패키지

```text
README.md
source_lock/
source_index/
author_attestations/
semantic_audits/
authored/
authored_seq/
authored_arc/
authored_chararc/
authored_relarc/
authored_edges/
validation/
lineage/
tools/
FINAL_MANIFEST.json
SHA256SUMS.txt
work_state.json
```

원본 대본·장문 대사·embedding·비밀키는 넣지 않는다.

### 15.2 ZIP 이식성 계약

- 표준 UTF-8 filename flag 사용
- 최상위 폴더명은 짧은 ASCII 권장
- Windows 추출을 고려해 내부 최장 경로 180자 이하 권장, 220자 초과 차단
- symlink·device file 금지
- ZIP 엔트리 경로 traversal(`..`, 절대경로) 금지
- `source_index`와 validator 누락 금지
- 실행 비트에 의존하지 않고 `python tools/validator.py`로 실행 가능
- CRC 검사만으로 끝내지 않고 새 빈 경로에 전량 해제
- 해제 후 파일 수·크기·SHA256SUMS·portable validator 재검사

### 15.3 DB 편입 분기

먼저 실제 DB root와 작품 수를 확인한다.

신규 작품 (`mode=ADD_NEW_WORK`):

1. 기존 파일명·work_id 존재 0 확인
2. 기존 작품 파일 덮어쓰기 0
3. 새 lineage만 추가
4. 새 버전 index 생성, 구 index 보존

기존 작품 교체:

1. 구판 전체 백업
2. 계층 혼합 금지
3. 작품 단위 전량 교체 또는 전량 유지

공통:

- 전역 ID·count·index 재집계
- 전체 JSON/JSONL parse
- 삽입 파일 hash 대조
- 전체 DB validator
- ZIP CRC·UTF-8·경로·fresh extraction

### 15.4 허브 경계

허브에는 권위 문서, schema·validator, SourceLock metadata, 수량, 검증, lineage, handoff, 패키지 SHA만 적재한다. 원본과 raw 의미 JSONL 전체는 적재하지 않는다.

## 16. 새 작품 권위 수용 검증

권위 개정 후 다음을 수행한다.

1. DB에 없는 완전 원본 작품 후보 조사
2. 불완전 후보 제외 이유 기록
3. SourceFormatAudit·SourceLock
4. EP01 전체 직접독해와 Stage01–03
5. 별도 audit run
6. 구조·의미·fresh extraction
7. 오류 시 권위·도구·절차 교정
8. EP01 PASS 뒤 블록 확대
9. 전 시즌 완료 후 Stage04·DB 신규 편입

수호천사는 기존판 재저작 검증, 〈눈이 부시게〉는 부분 원본 fail-closed 검증, 〈질투의 화신〉은 신규 24부작 전 시즌·Stage04·DB 신규 편입 검증 역할을 한다.

## 17. 새 세션 부트스트랩

새 세션은 프로젝트 전체를 전수 조사하지 않는다.

```text
1. DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10.md를 읽는다.
2. AUTHORITY_MANIFEST.json과 validator hash를 확인한다.
3. NEW_SESSION_BOOTSTRAP.md의 체크리스트를 실행한다.
4. 대상 원본 inventory와 최신 work_state/DB 상태만 읽는다.
5. SourceFormatAudit·작품 분류·SameWorkLegacyLock을 수행한다.
6. EP01 전체를 순서대로 직접 읽고 Stage01→02→03을 완결한다.
7. 25분 이내 원자적 체크포인트한다.
8. 별도 audit run에서 원문을 다시 연다.
9. 블록 강검증 뒤 다음 블록으로 간다.
10. 전 회차 잠금 뒤 Stage04와 패키지·DB 게이트를 수행한다.
```

복사용 시작 지시문:

```text
DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10.md를 유일 실행 계약으로 사용하라.
원본 inventory와 SourceFormatAudit를 먼저 수행하고 완전성 상태를 판정하라.
HWP/PDF 추출 결과는 원본 SHA·추출 SHA·장면 표제 표본으로 회귀검사하라.
삭제 장면, 번호 없는 물리 장면, 삽입 장면, 누락 번호를 source label과 canonical ordinal로 분리하라.
같은 작품의 기존 의미 데이터는 author lock 전 열지 마라.
한 회차 전체를 처음부터 끝까지 직접 읽은 뒤 Stage01→Stage02→Stage03을 완결하라.
Python으로 의미를 생성하지 마라.
20분 준비, 25분 원자 저장, 30분 무저장 하드스톱을 지켜라.
저작과 독립 감사를 서로 다른 run_id로 수행하라.
RelationshipArc에는 단일 canonical 인물만 사용하고 복합 가상 인물을 만들지 마라.
Stage04에서 최종회 집결·주제 유사성만으로 CrossEdge를 승격하지 마라.
UTF-8·Windows 경로 호환 ZIP을 실제 새 경로에 전량 해제해 검증하라.
네 검증축을 모두 통과한 뒤 PASS_CANDIDATE로 보고하라.
```

## 18. 실전 반례와 교훈

### 수호천사

- 기존 의미문 555/556 재사용
- 저작 스크립트의 자기 감사
- EP06에 EP07 기차 승차 결과 혼입
- 고정 8장면 시퀀스
- 52–55분 연속 실행 중단
- 부분 staging을 전체 DB로 오인

### 눈이 부시게

- 숫자 장면만 탐지해 번호 없는 물리 장면 8개 누락
- 부분 원본인데 전 시즌 작업을 시도할 위험

### 질투의 화신

- 완전 원본 후보 선정 중 수정 조각·최종회 누락 작품 제외 필요
- HWP 추출 회귀검사 필요
- 삽입 장면·삭제 장면·누락 번호 처리
- source label과 canonical ordinal 분리
- 복합 관계 엔터티와 별칭 정규화
- 시퀀스 밀도 하한을 기계 분절로 맞추지 않음
- 최종 결혼식 참석을 장거리 회수로 과승격한 엣지 철회
- 수동 ZIP 메타데이터로 한글 파일명이 깨진 문제
- Windows 경로 길이로 DB ZIP 해제 실패 가능성
- 신규 작품 DB 편입과 기존 작품 교체 절차를 구분

이 반례들은 V10의 실제 acceptance tests다.

## 19. 개발자 인계 계약

개발자는 다음 순서로 읽는다.

1. `README.md`
2. `DRAMA_ANALYSIS_SINGLE_AUTHORITY_V10.md`
3. `NEW_SESSION_BOOTSTRAP.md`
4. `OPERATIONS_RUNBOOK.md`
5. `AUTHORITY_MANIFEST.json`
6. `schemas/`와 `tools/`
7. `DEVELOPER_HANDOFF.md`

변경은 마스터 문서 → schema/tool → manifest → acceptance pilot 순으로 수행한다. 도구만 먼저 바꾸지 않는다.

## 20. 최종 판정 기준

올바른 분석은 장문의 자신감이 아니라 다음으로 증명한다.

- 직접 읽은 원본 범위
- 재현 가능한 SourceLock과 canonical scene map
- 고유 SceneCard와 실제 Sequence 경계
- 실제 변화만 기록한 Stage03
- 독립 원문 감사
- 후보 100% 처분과 보수적인 CrossEdge
- 중단 복구 가능한 체크포인트
- errors 0, blocking warnings 0
- manifest·SHA·ZIP CRC·UTF-8·fresh extraction
- 정확한 상태와 다음 진입점

> 원본을 직접 읽고 이해한 뒤 고유하게 저작한다. 도구는 판단을 만들지 않고, 판단을 보존·검증·운반한다.
