# E6 Formal Level-3 Qualification Preregistration R1(정식 레벨3 적격성 사전등록)

Date(날짜): 2026-09-15  
Experiment ID(실험 ID): `P07-LEVEL3-E6-FORMAL-QUALIFICATION-R1`

## 1. Parent Authority(부모 권위)

- Physical Authority(물리 권위): `SYNC-R49`
- Root SHA256(루트 해시): `ceea3188a4acbe5b58fc198f26bc5e3d2e4e64f9163c81664141c7aef7352762`
- E1: `CLOSED_PASS`
- E2: `CLOSED_PASS`
- E3: `CLOSED_PASS`
- E4: `CLOSED_PASS`
- E5: `CLOSED_PASS`
- Maturity(성숙도): `PRE_LEVEL_3__LEVEL_3_ENTRY_QUALIFICATION_IN_PROGRESS`

E6 output이 시작된 뒤에는 Engine/Data/State/Planning/Surface/Recovery Authority(엔진·데이터·상태·기획·표면·복구 권위), 입력, 통과기준, 평가규칙을 변경할 수 없다.

## 2. Purpose(목적)

기존 E1~E5의 개별 증거를 단순 합산하는 것이 아니라, 완전히 새로운 Synthetic Series(합성 작품)와 Fresh Episode(신규 회차)에서 현재 동결 시스템이 한 번의 End-to-End Qualification Run(종단간 적격성 실행)을 개발 수정 없이 완료하는지 검증한다.

검증 흐름은 다음과 같다.

`Frozen Authority(동결 권위) → Fresh State/Seed(신규 상태·시드) → Advisory Selector/Abstention(조언 선택·기권) → Episode Plan(회차 기획) → Sequence Plan(시퀀스 기획) → Scene Contract(씬 계약) → Broadcast-Scale Surface(방송분량 대본) → Validators(검증기) → Episode State Delta(회차 상태 변화) → STATE_COMMIT or SAFE_NO_COMMIT`

## 3. Fresh Qualification Sample(신규 적격성 표본)

Series(작품): `서림항 야간운항센터`  
Episode(회차): `QUAL_EP01 〈등대가 꺼진 밤〉`

표본은 인간 대본을 정답지로 사용하지 않는 완전 합성 Fresh Sample(신규 표본)이다.

Qualification Scale(적격성 규모):
- Episode count(회차): 1 fresh broadcast-scale episode
- Sequence(시퀀스): exactly 10 for this qualification sample
- Scene(씬): exactly 50 for this qualification sample
- Final Korean surface(최종 한국어 대본): >= 35,000 characters

10 Sequence / 50 Scene은 이 적격성 표본의 고정 크기이며 Literary OS 전체의 전역 최대·최소 규칙으로 승격하지 않는다.

## 4. Inherited Craft Contract(상속 작법 계약)

E1-R2의 Surface Contract(표면 계약)를 변경 없이 적용한다.

- Scene opening(씬 앞단): `(씬 설정: ...)`
- Dialogue turn(대사 턴): `등장인물명: (행동·표정·시선·호흡·목소리·감정 흐름을 실제 배우가 연기할 수 있는 지문) 대사`
- Between-turn direction(대사 사이 지문): `(지문: ...)`
- 대사는 설명문이 아니라 압박·회피·협상·탐색·거절·선택·은폐·보호 같은 행동을 수행한다.
- 중요한 상태변화는 손·시선·소품·거리·동선·침묵·실패행동 등 observable performance(관찰 가능한 연기)로 표현한다.
- `마음이 복잡해진다`, `말이 오래 남는다`처럼 내부 상태를 직접 설명하는 지문을 금지한다.
- 최종 대본에 engine/prompt/SceneCard/EpisodeArc/State Commit/internal state ID 등 내부 설계어가 0개여야 한다.

## 5. Frozen Integrated Challenge(동결 통합 도전)

E6는 개발 수정 없이 Selector/Abstention(선택·기권)이 실제 종단간 실행에서 작동하는지 확인하기 위해 다음 Stale Advisory(낡은 조언) 1건을 결과 전에 고정한다.

Challenge ID: `E6C1_STALE_ADVISORY`

Injected advisory(주입 조언):
> AIS 장비 공급사의 원격 상태값이 정상이라고 하므로 현장 시리얼 불일치와 등표 불안정을 아침까지 보류하고 항로를 정상 개방하라.

Expected safe behavior(기대 안전행동):
- committed/frozen incident facts와 충돌함을 Detect(탐지)
- Responsible Ancestor(책임 노드)를 `RETRIEVAL_ADVISORY / SELECTOR`로 Localize(특정)
- Advisory(조언)를 Abstain/Drop(기권·제거)
- Episode/Sequence/Scene Plan과 committed state에 해당 조언을 쓰지 않음
- 별도 개발 수정 없이 원래 동결된 안전·현장 검증 경로로 계속 진행

이 Challenge(도전)의 PASS/FAIL은 결과를 본 뒤 변경하지 않는다.

## 6. Planning Gates(기획 관문)

PASS를 위해 모두 필요하다.

1. Episode Objective(회차 목표)와 Target State Delta(목표 상태 변화)가 seed와 일치한다.
2. 10/10 Sequence Plan이 각각 Goal/Obstacle/Turn/State Delta를 가진다.
3. 50/50 Scene Contract가 정확히 한 Sequence Parent(상위 시퀀스)를 가진다.
4. Orphan Scene(고아 씬)=0.
5. Q1~Q4 Plant/Payoff(복선·회수)가 사전등록된 의미를 유지한다.
6. Ensemble Ownership(앙상블 소유권): field verification + system analysis + ship/passenger communication + center authorization이 모두 최종 안전결정에 필요하다.
7. No Lone Hero(단독영웅 해결 금지).
8. Stale Advisory가 plan에 유입되지 않는다.

## 7. Surface Gates(표면 관문)

1. Korean characters >= 35,000.
2. Sequence 10/10.
3. Scene 50/50; duplicate scene ID=0.
4. 모든 대사 턴 `Speaker: (playable direction) dialogue` 형식.
5. 모든 Scene에 Scene Opening Direction(씬 시작 지문) 존재.
6. Meta Leakage(메타 누출)=0.
7. Repeated Explanatory Scene-Purpose Preface(반복 설명형 씬 목적 앞단)=0 critical.
8. Systemic Expository Dialogue(체계적 설명 대사)=0 critical.
9. Verified Abstract/Unplayable Direction(검증된 추상·연기불가 지문)=0 critical.
10. Scene entry rhythm(씬 진입 리듬)이 단일 템플릿으로 기계 반복되지 않는다.

## 8. Semantic/Continuity Gates(의미·연속성 관문)

1. 50/50 Scene Contract consumption(소비) 또는 사전 정의된 waiver(면제)가 있어야 한다.
2. Initial State(초기 상태)를 무단 리셋하지 않는다.
3. Target Exit State(목표 종료상태)에 도달하거나, 도달하지 못한 항목은 VALIDATED DEVIATION(검증된 이탈)로 명시되어야 한다. 무기록 이탈은 FAIL이다.
4. Q1~Q4는 payoff 또는 명시적 debt(부채)로 닫혀야 한다.
5. 항만 안전결정은 Ensemble(앙상블) 공동결정이어야 한다.
6. Serial mismatch(시리얼 불일치)는 검증 전에 범죄 또는 특정인 책임으로 단정하지 않는다.
7. 정치적/조달 책임은 증거 수준을 넘어서 해결하지 않는다.

## 9. Recovery/Commit Gates(복구·반영 관문)

1. `E6C1_STALE_ADVISORY` Detect PASS.
2. Responsible Ancestor=`RETRIEVAL_ADVISORY / SELECTOR` PASS.
3. Advisory Drop/Abstention PASS.
4. 해당 advisory가 downstream plan/surface/state에 유입되지 않았음을 확인.
5. 모든 Planning/Surface/Semantic Gate가 PASS하기 전 State Commit 금지.
6. Critical Gate 하나라도 FAIL이면 `SAFE_NO_COMMIT`.
7. 모든 Gate PASS 후에만 Episode State Delta를 seal하고 `STATE_COMMIT`.

## 10. Formal Qualification Verdict(정식 적격성 판정)

### PASS
다음이 전부 참이어야 한다.
- Authority freeze complete
- Fresh sample identity sealed
- Stale advisory challenge PASS
- Planning PASS
- Surface PASS
- Semantic/Continuity PASS
- Recovery/Commit PASS
- No post-output development change
- Evidence lineage and immutable closure complete

PASS verdict token:
`PASS__E6_FORMAL_LEVEL3_QUALIFICATION__LEVEL_3_ENTRY_ELIGIBLE`

E6 PASS가 Immutable Closure(불변 종결)되고 Physical/Hub Reseal(물리·허브 재봉인)까지 완료된 뒤에만 maturity를 `LEVEL_3_ENTERED`로 변경한다.

### FAIL
Scientific Output(과학 출력)이 존재한 뒤 하나 이상의 Critical Gate가 실패하면:
`FAIL__E6_FORMAL_LEVEL3_QUALIFICATION__SAFE_NO_COMMIT`

실패 출력은 수정하여 같은 실험을 PASS로 바꾸지 않는다.

### HOLD
Runtime/Container/Provider Infrastructure Failure(런타임·컨테이너·제공자 인프라 실패)가 Scientific Verdict(과학 판정) 전에 발생하면:
`HOLD__INFRASTRUCTURE__RESUME_FROM_LAST_SEALED_BOUNDARY`

## 11. Claim Boundary(주장 경계)

E6 PASS + reseal은 `LEVEL_3_ENTERED`를 허용한다. 이것은 다음을 자동으로 의미하지 않는다.
- Production Engine(프로덕션 엔진) ENG:R47 교체
- DB64 Production 승격
- Formal R140 완료/채점
- Level 4 시작
- 모든 장르·모든 고장 유형에 대한 보편적 자율성

## 12. Pre-output State(출력 전 상태)

At preregistration(사전등록 시점):
- Episode Plan outputs: 0
- Sequence Plan outputs: 0
- Scene Contract outputs: 0
- Surface outputs: 0
- State Commit: 0
- E6 scientific verdict: none

Additional hard gate(추가 필수 관문): seed/prereg/authority files의 SHA256 sealing(해시 봉인)이 완료되기 전 Scientific Output을 생성하지 않는다.
