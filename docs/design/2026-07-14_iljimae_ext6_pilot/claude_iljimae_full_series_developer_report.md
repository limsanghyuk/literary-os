# Claude EXT6 Phase1 — 돌아온일지매 전체 24화 원본 직접독해 run

- Run ID: `claude_20260714_iljimae_full_01`
- 배경: GPT가 돌아온일지매 전체 회차를 분석 중이라는 사용자 통보를 받고, Claude측도 ep01 파일럿에서 전체 24화로 확장(GPT 비교용, blind).
- 원본 직접독해: **TRUE** (24화 전량, 8병렬 서브에이전트가 각 화 원문을 직접 읽고 저작 — 요약/발췌 아님)
- GPT 산출물 열람: **FALSE**
- Canonical: **FALSE**

## 결과 수량 (전체 24화 합계)

| 산출물 | 수량 |
|---|---|
| Stage01 SceneCard | 1,387씬 (전 화 결번·중복 0) |
| EntityBridge | 260명(작품 전체 유니크 인물, ep01~24 통합) |
| CastPresence | 3,193행 |
| CastCoverageLedger | 24개(화별) |
| SourceSceneAlignment | 1,387행(23/24화 물리헤딩-SceneCard 개수 정확히 일치 → ONE_TO_ONE 자동정렬 100%. 21화만 65씬 vs 63개 물리헤딩 탐지로 2씬 불일치 — 원본 자체의 결번/서브번호(5,36,38~40,45 결번 + 7-1/10-1/17-1 등 다수 서브넘버링) 때문이며, 해당 2씬은 `VERIFIED_MANUAL_REVIEWED`로 표시하고 오프셋은 미확보 상태로 투명하게 남김) |
| CharacterLoad | 728행(화별×인물) |

## 저작 방식

1. ep01은 이전 턴에 별도로(단독) 완료.
2. ep02~24(23화)는 8개 서브에이전트에 3화씩 병렬 배정, 각자 원문을 직접 읽고 SceneCard+CastPresence를 동시 저작 → Write 후 스스로 Read로 재검증하도록 지시.
3. 중앙(오케스트레이터)에서 전 24화를 대상으로 스키마 검증 스크립트 재실행 — 1차 검증에서 3건의 결함을 발견해 직접 수정:
   - **12화**: 서브에이전트가 스펙을 어기고 `scene_no`를 `"1-1"`, `"27-1"` 같은 문자열 서브번호로 남김 → 순서 보존하며 1~48 정수로 재채번, CastPresence의 scene_no 참조도 동일 매핑으로 동기화.
   - **5화·14화**: 월희가 같은 씬에서 ONSCREEN(육성 등장)과 VOICE_ONLY(내레이터 "책녀" 보이스오버)로 동시에 발화해 (scene_no, character_key) grain이 2행으로 중복됨(스키마는 1행만 허용) → ONSCREEN을 우선해 1행으로 병합, 두 근거 문장을 evidence_ref에 결합, speaking_status는 둘 중 하나라도 SPEAKING이면 SPEAKING으로 채택.
4. EntityBridge는 24화 CastPresence 전체에서 등장한 유니크 character_key를 취합해 재구성(260명). ep01 파일럿 때 만든 별칭(일지매↔복면남, 월희↔책녀)은 유지, 나머지는 신규 인물이라 별칭 없이 PROVISIONAL로 등재.
5. CastCoverageLedger·SourceSceneAlignment·CharacterLoad는 전량 오케스트레이터가 결정론적 스크립트로 직접 산출(서브에이전트에 위임하지 않음 — 병렬 에이전트가 이 3종을 개별 산출하면 상호 정합성이 깨지기 쉽기 때문).

## 검증 결과

- exact_keyset / enum / grain_uniqueness / foreign_keys / coverage_union / source_alignment_coverage / character_load_recomputation: **전 24화 ERRORS 0**
- 발견·수정된 결함(투명 기록): 위 §저작방식 3번의 3건(12화 서브번호, 5·14화 grain 중복) — 모두 재저작 없이 정정만으로 해소.

## 한계·근사치 투명 기록

- **CharacterLoad의 `act_placement`/`present_sequence_count`**: 이 작품은 Stage02(SequenceBlueprint+EpisodeArc)가 없어 정식 액트 구조·시퀀스 경계가 없다. 화별 씬수를 4등분한 근사 액트("설정/전개/심화/회말전환")와, 연속 5씬을 1개 가상 시퀀스로 묶는 균등 구간화를 사용했다. `by="derived_deterministic_pilot"`로 정식 파생과 구분 표기. **ep01은 이전 턴에 수작업 시퀀스 경계를 썼으나, 이번에 전 화 일관성을 위해 동일한 균등 구간화 방식으로 재계산해 덮어썼다**(이전 커밋 대비 ep01의 present_sequence_count/act_placement 값이 달라짐 — 24화 통일 기준 적용에 따른 의도된 변경).
- **21화 씬 2개**(원본 물리헤딩 탐지 실패분)는 SourceSceneAlignment의 char offset이 비어있다(`VERIFIED_MANUAL_REVIEWED`, 향후 수동 재대조 필요).
- **인물 레지스트리 260명 중 다수는 "사내1", "군관2", "포졸3" 같은 회차 내부 전용 라벨**이다. 동일 라벨이 여러 화에 걸쳐 재사용됐어도 실제로는 화마다 다른 배우/역할일 가능성이 있다 — Bridge의 `mapping_status=PROVISIONAL`이 이 불확실성을 정확히 반영한다. entity_id 실매핑 전까지 이 라벨들을 "동일 인물"로 간주하지 말 것.
- 실명 배역(일지매·월희·백매·구자명·배선달·차돌·걸치·열공·김자점 등 시즌 전체 재등장 주요 인물)은 8개 서브에이전트가 공유 로스터 문서를 참조해 화 간 이름 일관성을 유지했다.

## 권위 경계

- Stage02(SequenceBlueprint+EpisodeArc)·Stage04(FullSeriesArc)·구식 Stage03(LocalEdge 등)은 미저작 — 45편 완주 코퍼스에 미편입.
- GPT의 동일 작품 결과물을 열람하지 않은 상태에서 봉인 — 추후 GPT 결과물 수령 시 전체 24화 규모의 blind 비교(κ 산정) 가능.
- 정본 승격 아님, 사용자 승인 전까지 유지.

---
_by: Claude(Opus) · 근거: 사용자 제공 원본 24화 텍스트 직접독해(8병렬 서브에이전트 + 중앙 검증) · 2026-07-14_
