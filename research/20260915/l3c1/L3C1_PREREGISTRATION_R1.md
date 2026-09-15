# L3C1 Cross-Domain Four-Episode Endurance Preregistration R1(레벨3 안정화 교차도메인 4회차 내구성 사전등록)

Date(날짜): 2026-09-15  
Experiment ID(실험 ID): `P07-LEVEL3-POSTENTRY-L3C1-CROSSDOMAIN-4EP-ENDURANCE-R1`

## Parent Authority(부모 권위)
- Physical Authority(물리 권위): `SYNC-R52`
- Root SHA256(루트 해시): `62d2cec1a47e557a342dcedeb6eb63a7c18f1336f756b3b38bf0df7b7079a359`
- Maturity(성숙도): `LEVEL_3_ENTERED`
- Level 4: NOT STARTED

## Purpose(목적)
Level-3 진입 직후 동결된 R52 시스템이 완전히 새로운 의료전원 도메인에서 개발 수정 없이 4개의 방송규모 회차를 연속 운용할 수 있는지 검증한다.

## Hypothesis(가설)
R52 시스템은 4개의 35,000자 이상 회차를 연속 생성·검증하고, EPn의 Committed State(반영 상태)를 EPn+1의 정확한 부모로 소비하며, Character/Relationship/Ensemble/Social Ecology/Event/Plot Ownership/Open Debt(인물·관계·앙상블·사회생태·사건·플롯소유권·미결부채)를 무단 리셋하지 않는다.

## Frozen Sample(동결 표본)
Series(작품): `은하고개 광역응급전원센터`

- END_EP01 `빈 병상이 있다고 뜬 밤`
- END_EP02 `열세 번째 구급차`
- END_EP03 `꺼진 링크의 주인`
- END_EP04 `새벽 네 시의 네트워크`

Human answer key(인간 정답대본): 없음.

## Scale(규모)
각 회차:
- exactly 9 Sequence(시퀀스)
- exactly 45 Scene(씬)
- final Korean surface(최종 한국어 대본) >= 35,000 characters

이 9/45는 L3C1 표본의 고정 크기일 뿐 Literary OS 전체 규칙으로 승격하지 않는다.

## Execution Order(실행 순서)
`EP01 Plan → Surface → Validators → Commit or Safe No-Commit → exact committed EP01 state → EP02 → EP03 → EP04`

Critical Failure(중대 실패)가 한 회차라도 발생하면 그 회차에서 Immutable FAIL(불변 실패) + SAFE_NO_COMMIT(안전 미반영)하고 뒤 회차는 실행하지 않는다.

## Critical Gates(중대 관문)
1. Scale: 각 회차 >=35,000자 / 9 Sequence / 45 Scene.
2. Surface: Dialogue Format Error(대사형식 오류)=0, Missing Scene Opening(씬 시작 누락)=0.
3. Boundary: internal state field/enum/snake_case/assignment/meta leakage=0.
4. Parent Hash Chain: EP02 parent=EP01 committed-state hash, EP03 parent=EP02, EP04 parent=EP03.
5. Event Immutability(사건 불변성): 이전 committed event는 successor event ledger의 monotonic subset이어야 한다.
6. Relationship Carry(관계 이월): 명시적 사건 없이 과거 관계상태로 리셋하지 않는다.
7. Debt Accounting(부채 회계): 상속된 open thread는 CONSUMED / TRANSFORMED / RESOLVED / EXPLICITLY CARRIED 중 하나여야 한다.
8. Ensemble Ownership(앙상블 소유권): 안전한 전원 결정에는 Team Lead + Field Medical + Bed/System + Patient/Transport coordination이 모두 필요하다.
9. No Lone Hero(단독영웅 금지).
10. Commit Guard(반영 관문): 모든 해당 회차 검증 PASS 전 State Commit 금지.
11. No Development Change(개발수정 금지): EP01 Scientific Output(과학 출력)이 시작된 뒤 generator/validator/threshold를 변경하지 않는다.

## PASS
EP01~EP04가 모두 PASS + STATE_COMMIT이고 정확한 parent-hash chain과 모든 critical gate가 PASS.

Verdict token(판정 토큰):
`PASS__L3C1_CROSSDOMAIN_4EP_ENDURANCE_CLOSED`

## FAIL
첫 과학적 critical failure 발생 시:
`FAIL__L3C1_CROSSDOMAIN_4EP_ENDURANCE__SAFE_NO_COMMIT`

## HOLD
Runtime/Container Infrastructure Failure(런타임·컨테이너 인프라 실패)가 Scientific Verdict(과학 판정) 전에 발생하면:
`HOLD__INFRASTRUCTURE__RESUME_FROM_LAST_SEALED_BOUNDARY`

## Claim Boundary(주장 경계)
PASS는 Level-3 post-entry endurance evidence(레벨3 진입 후 내구성 증거)를 강화할 뿐이다. Level 4를 시작하지 않으며 Production Engine `ENG:R47`, DB64 Production 상태, Formal R140에는 변화를 주지 않는다.

## Pre-output State(출력 전 상태)
- EP01 outputs: 0
- EP02 outputs: 0
- EP03 outputs: 0
- EP04 outputs: 0
- State Commits: 0
- Scientific verdict: none

Additional hard gate(추가 필수 관문): Fresh Seed와 Preregistration의 SHA256 봉인 전 Scientific Output을 생성하지 않는다.
