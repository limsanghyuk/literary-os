# Literary OS — P07 New Session Handoff R3 (2026-09-05)

## 0. 이 문서의 권위와 목적

이 문서는 새 세션이 Literary OS(문학 서사 운영체계) 연구·실험을 즉시 정확하게 재개하기 위한 **Session Transition Authority(세션 전환 권위)** 이다.

- 기존 `START_HERE_P07_PREFORMAL_SESSION_CLOSE.md`는 이전 세션 종료 당시의 역사적 인계 증거로 보존한다.
- `START_HERE_P07_PREFORMAL_SESSION_CLOSE_R2.md`는 이번 세션 중간까지의 후속 교정 인계로 보존한다.
- **현재 상태 해석과 새 세션의 첫 행동 순서는 이 R3 문서를 우선한다.**
- 단, 실제 ZIP의 바이트·SHA256·CRC·내부 파일 내용에 관한 최종 판단은 반드시 새 세션의 Fresh Extraction Validation(새 추출 검증)으로 다시 확인한다.

현재 컨테이너 장애 때문에 이 문서는 GitHub(깃허브) 비상 인계 권위로 작성되었다. 장애 이후 새로운 로컬 ZIP·SHA256·PASS를 만들어냈다고 주장하지 않는다.

---

## 1. 현재 전역 상태

- P06: **COMPLETED / PHYSICALLY CLOSED(완료 / 물리 폐쇄)**.
- P07: **ACTIVE PREFORMAL(예비시험 진행 중)**. 완료라고 부르지 않는다.
- Formal scored count(정식 채점 누계): **137**.
- Latest formal scored experiment(최신 정식 채점 실험): **R138**.
- R140 formal attempt / output / score(정식 시도 / 산출 / 채점): **0 / 0 / 0**.
- ENG:R47 Production(운영 엔진): **immutable(불변)**. 수정 금지.
- DB59 frozen reference snapshot(동결 참조 스냅샷) SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- 기존 R140 6개 개발 작품은 rehearsal/repair contamination(예행·수리 오염) 때문에 **DEVELOPMENT SET ONLY(개발 표본 전용)** 이다. 정식 R140 표본으로 재사용 금지.
- P07은 현재 **본실험 전 문제 발견·보강·동등성 자격검증 단계**이다.

현재 상태 문자열:

`P07_ACTIVE_PREFORMAL__R_B_CLOSED__R_C_CLOSED_AND_PHYSICALLY_INTEGRATED__R_D_ACTIVE_NOT_CLOSED__CONTAINER_BACKEND_CLIENTERROR__FORMAL_R140_0_0_0`

---

## 2. 3단계 연구·실험 계보 — 반드시 유지

### Stage 1(1단계) — R001~R103

Scene/Sequence Control(씬·시퀀스 제어), Retrieval(검색), Boundary(경계), Episode Planning(회차 기획), Selector/Controller(선택기·제어기), Hierarchy(계층), Blueprint(설계도), Multi-Episode Rollout(다회차 전개) 등의 기본 연구계보.

중요: R001~R103을 “103개의 현재 실행 알고리즘”으로 해석하지 않는다. 과거 연구는 현재 엔진에서 다음 범주로 흡수된다.

- Adopted(채택): 실제 Runtime Module/Policy(실행체 모듈·정책)
- Conditional(조건부): 조건 만족 시만 소비
- Negative Guard(부정 관문): 실패 연구에서 얻은 금지·차단 규칙
- Metrology Only(계측 전용): 평가·진단에만 사용
- Superseded(후속 대체): 최신 연구가 우선

### Stage 2(2단계) — PRE-R104-AUX-001~068

R103과 R104 사이의 **Non-formal Engineering/Metrology Layer(비정식 공학·계측층)**.

핵심 범위:

- LLM Renderer(대규모언어모델 렌더러)
- Semantic Safety(의미 안전)
- DB Consumption(데이터베이스 소비)
- Source-State(원자료 상태)
- Runtime Wiring(실행체 결선)
- Evidence Integrity(증거 무결성)
- Reproducibility(재현성)
- Inspector/Validator(검사기·검증기)

AUX 68개는 Formal Experiment Count(정식 실험 누계)에 더하지 않는다.

### Stage 3(3단계) — R104 이후

End-to-End Literary System(종단간 문학 시스템) 계보:

`Source-State(원자료 상태)`
→ `Entity/Relationship/Thread(인물·관계·트레드)`
→ `Whole Story / Long Arc(전체 이야기·장기 아크)`
→ `Episode Allocation(회차 배분)`
→ `Detailed Episode Synopsis/Plan(상세 회차 시놉시스·계획)`
→ `Ensemble/Social Ecology(앙상블·사회생태)`
→ `Event / Plot-Axis Ownership(사건·플롯축 소유권)`
→ `THICK Sequence / Boundary(심층 시퀀스·경계)`
→ `Scene Plan / Scene Contract(씬 계획·씬 계약)`
→ `Dialogue/Action/Subtext(대사·행동·서브텍스트)`
→ `Final Surface Realization(최종 표면 실현)`
→ `State Carry / Repair / Rollback(상태 이월·수리·되돌림)`.

과거 headline claim(대표 주장)보다 후속 clean revalidation(청정 재검증)을 우선한다.

---

## 3. 현재 반드시 유지해야 할 역사적 주장 경계

- R129→R134: **CONFLICTED_NOT_REPLICATED(충돌 / 청정 재현 안 됨)**.
- R48 clean replay(청정 재현): **KNOWLEDGE_ONLY(지식 효과만 확인)**.
- R39 clean replay: clean causal replication(청정 인과 재현) 기준 FAIL. 계층계획의 방향성 신호와 혼동 금지.
- R41/P01: Ensemble Effect(앙상블 효과) 재현 PASS. 단순 Tone Add-on(톤 추가)은 독립적으로 지지되지 않음.
- R42/P02: Blueprint Depth(설계도 깊이)와 Mismatch Harm(오결합 피해)은 재현. Thread Binding(트레드 결합)의 추가효과는 Consumer Fidelity(소비 충실도) 부족 때문에 Primary Claim(주요 주장)으로 채택 금지.
- R43: Detailed Episode Planning(상세 회차 계획)이 Sequence Planning(시퀀스 계획)을 개선하는 연구계보를 유지.
- R44/R37: Retrieval(검색)은 confidence/fit(신뢰도·적합도)이 충분할 때만 기능적으로 사용하고 그렇지 않으면 `NO_RETRIEVAL`.
- R45/R46: Candidate Portfolio / Critic / Selection / Branch Memory(후보군·비평·선택·분기기억)는 실제 Decision Architecture(의사결정 구조)로 취급.
- R75~R77: Social Ecology + Event Ownership(사회생태 + 사건 소유권)은 protagonist bias(주인공 편향)를 줄이고 인과 소유권을 인물·집단으로 분산하는 계보.
- R79~R82: critical responsibility/safety dimensions(핵심 책임·안전 축)은 **non-compensatory hard floors(비보상 하한선)**.
- R99~R101: long-horizon state/relationship/thread/ensemble carry, rollback, controlled novelty, whole-story orchestration(장기 상태·관계·트레드·앙상블 이월, 되돌림, 통제 신규성, 전체 이야기 조율) 계보.
- R130 / R135~R138: LLM Surface(LLM 표면실현)는 naturalness/dialogue/subtext(자연스러움·대사·서브텍스트)를 개선할 수 있으나 character voice / repetition-template resistance(인물 화법·반복/템플릿 저항)는 여전히 열린 병목.

Failed Attempt(실패 시도)는 삭제하지 않는다. 후속 PASS만 남겨 단발 성공처럼 기록하지 않는다.

---

## 4. P07의 증거 계층 — 절대 혼합 금지

P07에서는 아래 네 층을 분리한다.

### A. Concept Application(개념 적용)
ChatGPT가 R001~R138의 연구 원리를 이해하고 대화/추론 안에서 직접 적용한 결과.

- 연구원리의 가능성·설계 타당성을 볼 수 있다.
- **실제 엔진 구현 증거가 아니다.**

### B. Virtual / Local Engine Rehearsal(가상·로컬 엔진 예행)
Container(컨테이너)에서 실제 Python Runtime(파이썬 실행체), DB59, Schema(스키마), Retrieval(검색), Guard(관문), State Carry(상태 이월), Hash/Receipt(해시·영수증)를 실행하는 공학 증거.

- Mechanical/Structural Evidence(기계·구조 증거)이다.
- 실제 Provider LLM(제공자 LLM)을 호출하지 않았다면 Live Craft Evidence(실제 작법 증거)가 아니다.

### C. Live Provider Engine Execution(실제 제공자 엔진 실행)
동결된 Candidate Engine(후보 엔진)이 실제 OpenAI API(오픈AI API)의 Provider/Model/Settings(제공자·모델·설정)으로 Planning/Rendering(기획·렌더링)을 호출하고 Provider Receipt(제공자 영수증)를 남기는 단계.

### D. Formal Controlled Evaluation(정식 통제 평가)
Fresh Sample(새 표본), Preregistration(사전등록), Blind(맹검), Control/Treatment(대조군·처치군), Frozen Threshold(동결 임계값), 독립 Judge(심사자)를 만족하는 R140 같은 정식 실험.

**A ≠ B ≠ C ≠ D.**

R48의 `Concept Prompt > ENG:R47 Runtime` 결과는 “연구원리를 대화에서 잘 적용하는 것”과 “그 원리가 실제 Runtime Consumer(실행체 소비자)를 통해 전달되는 것”이 다르다는 직접 경고로 유지한다.

---

## 5. P07 Parity Doctrine(동등성 원칙)

최종 목표는 동일한 문장 바이트를 재현하는 것이 아니다. 다음 세 층의 Parity(동등성)를 검증한다.

### 5.1 Mechanical / Trace Parity(기계·추적 동등성)
동일해야 하거나 추적 가능해야 하는 것:

- Source Cutoff(원자료 절단점)
- DB59 Snapshot(스냅샷)
- Runtime Tree(실행체 트리)
- Prompt Serialization(지시문 직렬화)
- Research Policy Hash(연구정책 해시)
- Schema / Stage Order(스키마·단계 순서)
- Retrieval Policy(검색 정책)
- Guard / Threshold(관문·임계값)
- Consumer Input Contract(소비자 입력계약)

### 5.2 Consumer Parity(소비 동등성)
“필드가 존재한다”만으로 PASS하지 않는다.

필수 증거 사슬:

`Value(값)` → `Consumer(소비자)` → `Behavior Change(행동 변화)` → `Downstream Propagation(하류 전파)` → `Receipt/Trace(영수증·추적)`.

### 5.3 Behavioral / Craft Parity(행동·작법 동등성)
같은 Provider/Model/Settings에서 구조·인과·앙상블·화법·서브텍스트·반복·템플릿 저항 등 품질의 방향성이 크게 붕괴하지 않아야 한다.

Provider Receipt 없는 Shadow/Concept 결과를 Live Parity의 대체물로 사용 금지.

---

## 6. LLM과 Python의 역할 경계

### LLM(대규모언어모델)이 소유

`Whole Series Plan(전체 시리즈 계획)`
→ `Long Arc(장기 아크)`
→ `Episode Allocation(회차 배분)`
→ `Detailed Episode Synopsis/Plan(상세 회차 시놉시스·계획)`
→ `Ensemble/Social Ecology(앙상블·사회생태)`
→ `Thread/Relationship(트레드·관계)`
→ `Event/Plot-Axis Ownership(사건·플롯축 소유권)`
→ `THICK Sequence/Boundary(심층 시퀀스·경계)`
→ `Scene Plan/Contract(씬 계획·계약)`
→ `Dialogue/Action/Subtext(대사·행동·서브텍스트)`
→ `Final Surface Realization(최종 표면실현)`.

### Python/code(파이썬·코드)가 소유

Bridge/Orchestration/State/Retrieval/Evidence/Validation/Risk Blocking/Commit/Rollback/Lossless Serialization(연결·오케스트레이션·상태·검색·증거·검증·위험차단·채택·되돌림·무손실 직렬화).

Hard Rule(강제 규칙):

`PYTHON_LITERARY_PROSE_GENERATION_BYTES = 0`

Python은 `PASS / HOLD / REPLAN / RERENDER`를 결정할 수 있으나 문학 문장을 대신 다시 쓰면 안 된다.

---

## 7. 이번 세션에서 완료된 물리 권위 복구

이전 세션 말미의 전체 역사 재감사에서 “CP0 이후 바로 API Credential → CP1 Craft Parity”라는 해석이 철회되었지만, 당시 Container `ClientError` 때문에 5파트·8패키지에 물리 편입하지 못했다.

이번 세션 초반 정상 Container에서 그 Session-Close Delta(세션 종료 변경분)를 복구하고, 기존 CP0 자료는 역사 증거로 보존한 채 상위 Current Authority(현재 권위)를 추가하여 재봉인했다.

그 뒤 R-B, R-C를 순차적으로 진행했다.

---

## 8. R-B Narrative Architecture Closure(서사구조 폐쇄) — CLOSED

R-B의 목표:

1. Social Ecology Graph(사회생태 그래프): groups, memberships, group relations, obligations, pressures, resources/information.
2. Event / Plot-Axis Ownership(사건·플롯축 소유권)을 first-class runtime contract(1급 실행계약)로 사용.
3. Detailed Episode Synopsis(상세 회차 시놉시스)를 generic `EPISODE_PLAN` alias(일반 회차계획 별칭)가 아닌 별도 LLM 계획층으로 사용.
4. THICK Sequence + Boundary(심층 시퀀스·경계)의 goal, obstacle, value shift, turn type, POV, cast function, event/info/relationship/thread movements, entry/exit state, runtime share를 하류가 실제 소비.
5. Consumer Fidelity Gate(소비 충실도 관문)로 Parent→Child→Renderer(상위→하위→렌더러) 소비를 추적.

### R-B 중 발견·수리한 패키징 문제

CP0 Active Snapshot(활성 스냅샷)을 만들 때 `tools/`가 복사되지 않아 테스트 보조 실행파일 5개가 빠져 있었다.

- 소스 유실이 아니었다.
- C2 내부 과거 중첩 봉인본의 `CANDIDATE_SOURCE/tools`에 원본이 존재했다.
- 새 파일을 발명하지 않고 원본 바이트를 복원했다.
- 역사 보존용 구형 테스트는 현행 회귀 범위와 분리했다.

마지막 정상 검증:

- R-B 신규 시험: **7/7 PASS**
- 현행 비역사 회귀시험: **128/128 PASS**

R-B는 CLOSED(폐쇄)로 유지한다.

---

## 9. R-C Decision Architecture Closure(의사결정구조 폐쇄) — CLOSED

R-C에서 닫은 구조:

`LLM Candidate Portfolio(LLM 후보군)`
→ `LLM Plan Critic(LLM 계획 비평)`
→ `R82 Non-compensatory Safety Gate(R82 비보상 안전하한)`
→ `Primary / Backup Selection(주·백업 선택)`
→ `THICK Sequence downstream consumption(THICK 시퀀스 하류 소비)`.

주요 수리:

- Python이 `event_family`, `responsibility`, `global_value`를 창작적으로 결정하는 경로를 최신 역할경계에 맞게 정리.
- `owner_axis_id`, `primary_group`가 실제 R-B Event Axis / Group ID에 존재하는지 Referential Integrity(참조 무결성) 검증.
- Primary Plan(주 계획)이 단순 handoff hash(인계 해시)로 끝나지 않고 실제 THICK Sequence 요청 입력을 변경함을 증명.
- Safety(안전)는 정확한 `PASS`만 통과. 미정의 토큰은 HOLD.
- Decision Receipt(결정 영수증)에 raw safety result와 allowed-context hash를 결합.

마지막 정상 검증:

- R-C 신규 시험: **15/15 PASS**
- 현행 비역사 회귀시험: **143/143 PASS**

R-C는 **CLOSED AND PHYSICALLY INTEGRATED(폐쇄·물리 편입 완료)** 로 유지한다.

---

## 10. 마지막 물리 5파트·8패키지 권위 — R-C 시점

새 세션은 개발자가 전달하는 실제 파일을 우선 사용하고 Fresh Validation(새 검증)해야 한다.

### 변경 대상 / 최신 Revision(개정)

1. CONTROL: `LITERARY_OS_MANDATORY_CONTINUATION_SET_CONTROL_R31_P07_RC_DECISION_ARCHITECTURE_CLOSED_AUTHORITY_20260905_SEALED.zip`
2. PART-A: `LITERARY_OS_MANDATORY_CONTINUATION_PART-A_CONTROL_AND_EXPERIMENT_R30_P07_RC_DECISION_ARCHITECTURE_CLOSED_20260905_SEALED.zip`
3. PART-B2: `LITERARY_OS_MANDATORY_CONTINUATION_PART-B2_RESEARCH_CURRENT_RECOVERY_VOL2_R31_P07_RC_DECISION_ARCHITECTURE_CLOSED_20260905_SEALED.zip`
4. PART-C2: `LITERARY_OS_MANDATORY_CONTINUATION_PART-C2_ENGINE_MASTER_VOL2_CANDIDATE_R30_P07_RC_DECISION_ARCHITECTURE_CLOSED_20260905_SEALED.zip`

### Byte-unchanged(바이트 불변) 역사/운영/DB 패키지

5. PART-B1 R10 — SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
6. PART-C1 R10 — SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
7. PART-D1 R10 — SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
8. PART-D2 R10 — SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

중요: R-C 시점 변경 4패키지의 SHA256은 새 세션에서 실제 전달 바이트로 다시 계산한다. 이 R3 문서는 장애 이후 새 해시를 추정하거나 만들어내지 않는다.

---

## 11. R-D Long-Horizon Closure(장기전개 폐쇄) — ACTIVE / NOT CLOSED

R-D는 **완료 선언 금지**.

목표:

### RD1 — Canonical Long-Horizon Carry(정본 장기 이월)
Character / Relationship / Thread뿐 아니라 Group / Membership / Group Relation / Plot Axis(인물·관계·트레드·집단·소속·집단관계·플롯축)를 회차 간 이월.

### RD2 — Authorized Novelty(승인 신규성)
단순 quota(할당량)가 아니라 role gap(역할 공백)이 있을 때만 신규성을 허용하고, Character/Relationship/Thread/Ecology 레지스트리에 원자적으로 등록.

### RD3 — Narrative-State Rollback(서사 상태 되돌림)
Production Authority Rollback(운영 권위 되돌림)과 별개인 생성 중 Narrative State Snapshot → exact rollback → resume(서사상태 스냅샷 → 정확 복구 → 재개).

### RD4 — Controlled Replan(통제 재기획)
재기획해도 Series Anchor(시리즈 앵커)와 R-C Primary Plan(주 계획)을 무단 변경하지 못하도록 제한.

### RD5 — Synthetic EP06→EP07→EP08 Continuation Probe(합성 3회차 연속 탐침)
실제 parent-state hash(부모 상태 해시)를 다음 회차가 소비하며 State/Relationship/Thread/Group Carry(상태·관계·트레드·집단 이월), closure pressure(종결 압력), rollback, authorized novelty를 검사.

### R-D에서 장애 전 발견한 실제 문제

1. 기존 장기상태 컴파일러가 Character/Relationship/Thread는 이월하지만 Group/Ecology를 충분히 이월하지 않음.
2. 기존 `execute_rollback()`은 Production Authority용이며 Narrative-State Rollback과 목적이 다름.
3. Novelty Admission(신규성 승인)이 선언한 다중 레지스트리와 실제 Canonical Carry(정본 이월)의 물리 등록이 불완전함.
4. Snapshot/Commit Hash(스냅샷·채택 해시)와 다음 Episode Entry(회차 진입)의 hash domain(해시 영역)이 `last_state_hash` 자기참조 때문에 달라질 위험 발견.
5. 그래서 canonical hash domain(정본 해시 영역)을 하나로 통일하고 다음을 직접 검사하는 방향으로 수정 중이었음.
   - `EP06 commit == EP07 parent`
   - `EP07 commit == EP08 parent`
6. Closed/Final Thread(폐쇄·최종 트레드) 무단 재개 BLOCK.
7. Future-source(미래 원자료) 사용 BLOCK.
8. Series Anchor / R-C Primary Plan 무단 변경 BLOCK.
9. 잘못된 rollback target hash BLOCK.
10. rollback 뒤 동일 EP07 요청을 재구축하면 clean-run request hash와 동일해야 함.
11. Python 문학생성 0 유지.

### 마지막 알려진 정상 실행점

Container 장애 전에 다음 실행 결과가 보고되었다.

- R-D 신규 시험: **17/17 PASS**
- 현행 비역사 회귀시험: **160/160 PASS**

그러나 이것은 **R-D 폐쇄 증거가 아니다.**

남아 있던 마지막 Preseal(봉인 전) 작업:

- Character/Relationship/Thread/Membership/Group 간 dangling reference(고아 참조) 결함주입
- Referential Integrity(참조 무결성) Fail-closed 시험
- 독립 Preseal Audit(봉인 전 감사)
- Fresh Extraction Re-run(새 추출 재실행)
- R-D 개별 봉인
- CONTROL/A/B2/C2 편입 및 8패키지 재봉인

따라서 새 세션은 **R-D를 처음부터 새 실험처럼 만들지 말고, R-C 물리 Authority를 Fresh Validate한 뒤 R-D ACTIVE Checkpoint(진행 중간점)를 재구성하여 남은 참조무결성부터 재검증**해야 한다.

---

## 12. Container / Python Backend 장애

이번 세션 초반과 R-B/R-C/R-D 초기에는 Container(컨테이너)가 정상 작동했다.

### Last Known Good(마지막 정상 구간)

R-D 17/17 + 현행 160/160 실행 및 State Hash Domain 문제 조사·보강 시점.

### First Known Bad(최초 확인된 장애 구간)

개발자가 “3단계 연구 전체, 이전 세션 대화, 권위 반영 여부, Concept↔Virtual↔Live API Parity를 다시 전수 재감사하라”고 지시한 이후의 새 Container/Python 호출에서 `caas.internal.errors.ClientError` 확인.

이후 최소 명령도 연속 실패:

- `/bin/echo`
- `true`
- `pwd`
- Python 최소 실행

따라서 현재 분류:

`CONTAINER_EXECUTION_BACKEND_CLIENTERROR__MINIMAL_COMMANDS_FAIL__ENGINE_FAILURE_NOT_ESTABLISHED`

이 장애를 특정 Literary OS 코드 실패로 기록하지 않는다.

새 세션에서는 **첫 번째 기술 행동으로 Container와 Python의 최소 생존검사**를 한다.

---

## 13. OpenAI Developers(오픈AI 개발자) 설치 목적 — Container 복구용이 아님

이전 세션에서 설치·연결한 OpenAI Developers(오픈AI 개발자) 계층은 현재 ChatGPT CAAS Container를 재시작하기 위한 것이 아니다.

목적:

- Candidate Engine(후보 엔진)을 실제 OpenAI API(오픈AI API)에 연결
- 안전한 `OPENAI_API_KEY` Credential Gate(자격증명 관문) 사용
- 실제 Provider/Model/Settings로 Planning/Rendering 실행
- Provider Receipt(제공자 영수증) 수집
- Virtual/Local Engine Result(가상·로컬 엔진 결과)와 Live Provider Result(실제 제공자 결과)의 Parity(동등성) 검증

API Key(에이피아이 키)는 ChatGPT 대화에 입력하지 않는다. Environment Variable(환경변수) 또는 Secret Manager(비밀 저장소) 같은 안전한 경로를 사용한다.

---

## 14. P07 이후 정확한 순서

### 이미 완료

- R-A Historical Re-audit(역사 재감사): COMPLETE.
- R-B Narrative Architecture Closure(서사구조 폐쇄): CLOSED.
- R-C Decision Architecture Closure(의사결정구조 폐쇄): CLOSED / PHYSICALLY INTEGRATED.

### 현재

- **R-D Long-Horizon Closure(장기전개 폐쇄): ACTIVE / NOT CLOSED.**

### 이후 순서

1. R-D 완전 폐쇄
2. R-E Surface Craft Closure(표면작법 폐쇄)
   - Character Voice(인물 화법)
   - Masked-speaker Attribution(화자가림 식별)
   - Subtext/Physicalization(서브텍스트·행동화)
   - Long-form Repetition/Template Guard(장기 반복·템플릿 관문)
3. R-F Live Reference-vs-Actual Engine Craft Parity(실시간 참조 대 실제 엔진 작법 동등성)
   - same Provider/Model/Settings(동일 제공자·모델·설정)
   - actual Provider Receipt(실제 제공자 영수증)
4. R-G Preformal Freeze(예비시험 동결)
   - Code / Prompt / Threshold / Retrieval / Renderer Policy Freeze(코드·지시문·임계값·검색·렌더러 정책 동결)
5. Fresh Deterministic Formal Sample(새 결정론적 정식 표본)
6. Revised R140 Preregistration(수정 R140 사전등록)
7. New G0 Physical Seal(새 G0 물리 봉인)
8. Formal R140(정식 R140)

R-D/R-E가 닫히기 전에 R-F로 건너뛰지 않는다. P07이 완전히 동결되기 전에 Formal R140을 시작하지 않는다.

---

## 15. 새 세션의 정확한 첫 실행 절차

새 세션은 다음 순서로 진행한다.

### Step 1 — GitHub Handoff(깃허브 인계) 읽기

브랜치:

`handoff/p07-preformal-session-close-20260905`

읽기 순서:

1. `handoff/20260905/CURRENT_HANDOFF_POINTER.md`
2. **이 문서 `START_HERE_P07_PREFORMAL_NEW_SESSION_HANDOFF_R3.md`**
3. 필요 시 R2, R1 역사 인계 문서

### Step 2 — Backend Health Check(백엔드 생존검사)

최소 Container 명령과 Python 실행을 먼저 확인한다.

실패하면 새 실험 실행·봉인·SHA 생성 금지.

### Step 3 — 5파트·8패키지 Fresh Validation(새 검증)

개발자가 전달한 R-C 최신 세트를 실제 바이트로 검증:

- outer ZIP SHA256
- CRC
- internal manifest
- nested archive integrity
- immutable B1/C1/D1/D2 byte identity
- CONTROL/A/B2/C2 current authority consistency
- DB59 SHA
- Formal count 137
- R140 0/0/0
- ENG:R47 immutable

### Step 4 — Evidence/Parity Doctrine(증거·동등성 원칙) 권위 반영 확인

Concept / Virtual / Live Provider / Formal Evidence가 혼합되지 않았는지 확인.

### Step 5 — R-D 재개

R-D의 기존 미봉인 작업을 그대로 정식 결과로 신뢰하지 말고, R-C 물리 Authority에서 R-D Development Overlay(개발 오버레이)를 재구성한다.

우선 순위:

1. Canonical State Referential Integrity(정본 상태 참조 무결성)
2. dangling relationship/thread/membership/group/axis 결함주입
3. `EP06 commit == EP07 parent`, `EP07 commit == EP08 parent`
4. rollback exact-resume
5. authorized novelty atomic registration
6. Fresh 17/17 계열 시험 재실행
7. 전체 현행 regression(회귀) 재실행
8. Preseal Audit
9. Fresh Extraction Validation
10. R-D 개별 봉인
11. 5파트·8패키지 편입·재봉인

그 뒤에만 R-D CLOSED 선언.

---

## 16. 새 세션에서 절대 하지 말아야 할 것

- R-D를 이미 완료했다고 선언하지 말 것.
- 17/17·160/160을 Formal Evidence로 사용하지 말 것.
- Container `ClientError`를 Engine Failure로 기록하지 말 것.
- Concept Prompt 또는 ChatGPT 직접 적용 결과를 Live API Result로 부르지 말 것.
- Provider Receipt 없는 결과를 OpenAI API 실행 증거로 부르지 말 것.
- 기존 6개 개발작품을 Formal R140 표본으로 재사용하지 말 것.
- ENG:R47 Production을 수정하지 말 것.
- DB59 frozen reference snapshot을 임의 변경하지 말 것.
- Python이 문학적 문장을 작성·수정하도록 만들지 말 것.
- 실패·수리 Attempt를 삭제하지 말 것.
- 패키지 실제 바이트를 확인하지 않고 SHA256을 추정하지 말 것.

---

## 17. 현재 GitHub 비상 인계 계보

Repository(저장소): `limsanghyuk/literary-os`

Branch(브랜치): `handoff/p07-preformal-session-close-20260905`

역사 계보:

- 최초 Session Close Handoff 커밋: `09c95c9b41bb49ba943bdeb365f1841f647d32b4`
- R2 상세 인계 추가 커밋: `a7c035487ff5b00c9caaa3b462e28da1990c5954`
- R2 Current Pointer 추가 커밋: `919f44ad3d487af1456070eb5b735042edfd0f11`
- 이 R3 문서가 추가된 이후 Current Pointer는 R3를 가리키도록 갱신해야 한다.

---

## 18. 최종 인계 판정

새 세션이 받아야 할 정확한 상태:

`THREE_STAGE_RESEARCH_LINEAGE_ACTIVE`
`__HISTORICAL_CLAIM_BOUNDARIES_PRESERVED`
`__CONCEPT_VIRTUAL_LIVE_FORMAL_EVIDENCE_SEPARATED`
`__R_B_NARRATIVE_ARCHITECTURE_CLOSED`
`__R_C_DECISION_ARCHITECTURE_CLOSED_AND_PHYSICALLY_INTEGRATED`
`__R_D_LONG_HORIZON_ACTIVE_NOT_CLOSED`
`__LAST_KNOWN_GOOD_R_D_17_OF_17_AND_CURRENT_REGRESSION_160_OF_160_PRESEAL_ONLY`
`__FINAL_REFERENTIAL_INTEGRITY_AND_FRESH_REVALIDATION_REQUIRED`
`__CONTAINER_BACKEND_CLIENTERROR_AT_SESSION_TRANSITION`
`__FORMAL_COUNT_137`
`__R140_0_0_0`
`__ENG_R47_IMMUTABLE`
`__DB59_FROZEN`

**다음 세션의 목적은 새로운 연구를 처음부터 시작하는 것이 아니라, R-C 물리 권위를 Fresh Validate(새 검증)하고 R-D의 미완성 장기전개 폐쇄를 과학적으로 재개하여 물리 봉인까지 닫는 것이다.**
