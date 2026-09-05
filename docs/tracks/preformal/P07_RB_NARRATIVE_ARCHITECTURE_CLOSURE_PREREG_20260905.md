# P07 R-B Narrative Architecture Closure(서사구조 폐쇄) — Preregistration(사전등록)

Date(일자): 2026-09-05  
Status(상태): `PREREGISTERED_LOCKED__NONFORMAL_MECHANICAL_SENTINEL`  
Formal Experiment Count(정식 실험 수): **137 unchanged(변화 없음)**  
R140 Formal attempt/output/score(정식 시도/출력/점수): **0 / 0 / 0**

## 1. Purpose(목적)
본 시험의 목적은 Live Craft Parity(실시간 작법 동등성) 이전에 Narrative Architecture Consumption(서사구조 실제 소비)이 하나의 LLM→Runtime→LLM(LLM→실행체→LLM) 소비사슬로 기계적으로 닫히는지 검증하는 것이다.

우선 폐쇄 대상은 다음 다섯 축이다.

1. Social Ecology Graph(사회생태 그래프)
2. Event Ownership(사건 소유권)
3. Group Membership(집단 소속)
4. Detailed Episode Synopsis(상세 회차 시놉시스)
5. THICK Sequence/Boundary(심층 시퀀스·경계)

## 2. Research Question(연구질문)
LLM-1(상위 의미 설계 제공자)이 만든 다섯 Narrative Architecture(서사구조) 축이 Runtime IR(실행체 중간표현)에서 참조 무결성을 유지한 채 소비되고, 이후 LLM-2 Surface Provider Packet(표면실현 제공자 패킷)에 실제 제약·근거로 전달되는가?

## 3. Hypothesis(가설)
다섯 구조축이 모두 활성화된 경우에만 Runtime(실행체)은 `ALLOW_PROVIDER_RENDER(제공자 렌더 허용)`을 반환한다. 각 축을 독립적으로 변경하면 downstream provider packet digest(하류 제공자 패킷 다이제스트)가 달라져야 하며, 필수 축 삭제·참조 파손은 `HOLD_ARCHITECTURE_CONTRACT(서사구조 계약 보류)`로 Fail Closed(실패 폐쇄)되어야 한다.

## 4. Scope(범위)
이 시험은 Test Double(시험 모사)을 사용하는 NONFORMAL(비정식) Mechanical Sentinel(기계 감시시험)이다.

증명 가능:
- 구조축의 실제 Runtime 소비 여부
- Parent→Child(부모→자식) 참조 무결성
- 다섯 축 각각의 downstream 영향
- Python(파이썬)이 최종 문학문장을 쓰지 않는 구조

증명 불가:
- 실제 Provider LLM(제공자 LLM)의 작법 품질
- Character Voice(인물 화법) 우위
- Human Writer Parity(인간 작가 동등성)
- PRE-R140 Production Promotion(운영 승격)

## 5. Frozen Chain(동결 소비사슬)
`Source Seed(원자료 모사)`
→ `LLM-1 Architecture Provider(상위 서사구조 LLM)`
→ `Narrative Architecture Contract Validator(서사구조 계약 검증기)`
→ `Narrative Architecture IR(서사구조 중간표현)`
→ `LLM-2 Surface Provider Packet(표면실현 LLM 패킷)`
→ `LLM-2 Test Double Consumption Receipt(표면실현 시험 모사 소비 영수증)`

Python(파이썬)은 구조 검증·참조 연결·해시·패킷 조립만 수행한다. Python sentence repair(파이썬 문장 수선)와 Python-authored prose(파이썬 저작 문장)는 금지한다.

## 6. Required Contract(필수 계약)
### Social Ecology Graph(사회생태 그래프)
- characters(인물)
- groups(집단)
- relationships(관계)

### Group Membership(집단 소속)
- character_id(인물 ID)
- group_id(집단 ID)
- role(역할)
- obligation(의무)

### Event Ownership(사건 소유권)
- event_id(사건 ID)
- owner_id(소유 인물)
- affected_group_ids(영향 집단)
- pressure(압력)

### Detailed Episode Synopsis(상세 회차 시놉시스)
- episode_goal(회차 목표)
- beats(회차 비트)
- 각 beat(비트)의 event_ids(사건 ID)

### THICK Sequence/Boundary(심층 시퀀스·경계)
- sequence_id(시퀀스 ID)
- synopsis_beat_ids(시놉시스 비트 ID)
- event_ids(사건 ID)
- participants(참여 인물)
- group_ids(집단 ID)
- boundary.value_shift(가치 이동)
- boundary.turn_type(전환 유형)
- boundary.exit_pressure(종료 압력)

## 7. Locked Gates(동결 통과기준)
G1 Complete Five-Layer Presence(5개 층 완전 존재): 5/5 구조축이 Runtime IR(실행체 중간표현)에 존재.

G2 Reference Integrity(참조 무결성): Event→Owner, Membership→Group, Synopsis→Event, Sequence→Synopsis/Event/Character/Group 참조가 모두 유효.

G3 Downstream Consumption(하류 실제 소비): 5/5 구조축이 LLM-2 Provider Packet(제공자 패킷)에 명시적으로 포함.

G4 Independent Perturbation Propagation(독립 변조 전파): 각 구조축을 하나씩 변경한 5개 Mutation(변조) 모두 downstream packet digest(하류 패킷 다이제스트)를 변경.

G5 Fail-Closed Missing Layer(필수 층 결손 실패폐쇄): 각 필수 구조축 삭제 시 `HOLD_ARCHITECTURE_CONTRACT`.

G6 Broken Reference Hold(참조 파손 보류): 존재하지 않는 event/group/character/beat 참조는 `HOLD_ARCHITECTURE_CONTRACT`.

G7 No Python Surface Authorship(파이썬 표면문장 저작 금지): `surface_text_authored_by_python == false`, `provider_generation_required == true`.

G8 LLM→Runtime→LLM Receipt Chain(LLM→실행체→LLM 영수증 사슬): Phase-1 output digest(1단계 출력 다이제스트), Runtime IR digest(실행체 중간표현 다이제스트), Phase-2 packet digest(2단계 패킷 다이제스트), Phase-2 consumption receipt(2단계 소비 영수증)가 연속 기록.

## 8. Verdict(판정)
G1–G8 전부 PASS(통과) 시:
`PASS_NONFORMAL_MECHANICAL_ARCHITECTURE_CLOSURE_SENTINEL`

하나라도 실패 시:
`FAIL_NONFORMAL_MECHANICAL_ARCHITECTURE_CLOSURE_SENTINEL`

## 9. Attempt Accounting(시도 회계)
- scored_attempt_index(채점 시도 번호): 없음 — NONFORMAL(비정식)
- total_attempts(전체 시도 수): 각 CI(지속적 통합) 실행마다 기록
- repair_criterion(수선 기준): 사전등록 이후 결과를 보고 통과기준을 변경하지 않는다. 코드 결함 수정 시 새 commit(커밋)으로 이력 보존.

## 10. Authority Boundary(권위 경계)
이 브랜치는 Production/Main(운영/메인)과 PRE-R140 Formal Candidate Authority(정식 후보 권위)를 변경하지 않는다. 현재 로컬 CAAS Backend(실행 백엔드)의 ClientError(클라이언트 오류)를 우회하기 위한 별도 실험 경로이며, 성공 결과는 PRE-R140 후보의 실제 live provider 실행을 대체하지 않는다.
