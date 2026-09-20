# R68 — F04 Semantic Transaction Repetition Validator Preregistration R1

Date: 2026-09-20
Status: `PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0`

## Sequential identity (연속 연구 식별)
- R66 CLOSED PASS — F01 Boundary-Safe Predicate Parser (경계 안전 술어 파서)
- R67 CLOSED PASS — F07 Dual-Ledger State Carry Runtime (이중 원장 상태 이월 런타임)
- R68 CURRENT / PREREGISTERED

## Parent authority (부모 권위)
Physical Authority (물리 권위):
`SYNC-R65`

Active Qualified Candidate (활성 자격 후보):
`R67 F07 Dual-Ledger State Carry Runtime / R66 F01 lineage`

Current runtime SHA256:
`9ab625122d7b572bf781ffa8062271f085cfde2d757e42dd79a18b977d9a72b8`

Adaptive Showrunner source SHA256:
`6574449a4a0b0520db5993b1f1abe532709b19aa9a5c7dc706df24b8c1fc6b91`

Production Engine (운영 엔진):
`ENG:R47 / LEGACY_R53`

Runtime DB (런타임 DB):
`DB59 frozen`

Research DB (연구 DB):
`DB64 research-only`

## Causal target (인과 대상)
Only F04:
`Semantic Repetition Validator Gap (의미 반복 검증기 결함)`

R61 status:
`SUPPORTED`

Observed gap:
Current validator catches:
- exact obligation material duplication;
- normalized obligation pattern duplication;
- exact scene-function signature duplication;
- exact concrete-action duplication.

But current scene-function signature includes material-specific hashes and therefore can miss:
`same semantic transaction / different story material`.

No F01/F06/F07/F08 intervention is allowed.

## Research question (연구 질문)
Can a material-agnostic Semantic Transaction Signature (재료 독립 의미 거래 서명) detect mechanically repeated dramatic transactions across different story material without rejecting legitimate variation or ordinary repeated RESOLVE (해결) stages?

## Hypothesis (가설)
A scene-level validator that normalizes:
- transaction family (거래 계열);
- obligation kind/function (의무 종류/기능);
- causal role (인과 역할);
- state-delta role profile (상태 변화 역할 프로필);
- resolution/open-state role (해결/열린 상태 역할);

while excluding entity names, IDs, numbers, locations, props and other story-specific material will detect semantic repetition missed by exact/material signatures.

However:
- `RESOLVE` alone is too universal and must not count as semantic repetition;
- two uses of the same transaction family are allowed;
- the same normalized non-RESOLVE signature becomes a validator violation only at **3 or more occurrences**.

This threshold is frozen before implementation/output inspection.

## Control (대조군)
Exact current R67 qualified runtime.

Control validator behavior:
`validate_adaptive_architecture()` from SYNC-R65.

No Control mutation.

## Treatment scope (처치 범위)
Permitted changes only in:
`literary_os_runtime/adaptive_showrunner_ul16.py`

Permitted additions:
- Semantic Transaction Signature builder (의미 거래 서명 생성기);
- Semantic Repetition Group detector (의미 반복 그룹 검출기);
- report fields in Reverse Reconstruction / validation diagnostics;
- one new F04 validation issue token.

Prohibited changes:
- F01 transaction-family selection;
- R66 boundary-safe semantic parser;
- F07 State Carry runtime;
- scene generation/stage plans;
- sequence allocation;
- obligation compiler;
- concrete-action generation;
- F06 Scene Necessity;
- F08 Provider Context;
- DB authority;
- Production path.

R68 is a validator-only intervention.

## Frozen Semantic Transaction Signature (동결 의미 거래 서명)
For every non-RESOLVE scene, the Treatment computes a normalized signature from:

1. `transaction_stage`
   - PRESSURE_ESCALATION, DISCOVERY, NEGOTIATION_EXCHANGE, etc.

2. `transaction_kind_role`
   - EVENT / THREAD / RELATIONSHIP / CHARACTER / INFORMATION / SOCIAL / PAYOFF.

3. `causal_role_profile`
   Boolean/typed profile derived from the obligation:
   - has dependency/prior cause;
   - multi-owner/counterparty;
   - deferred/open pressure participation;
   - blocked/preconditioned role.

4. `state_delta_role_profile`
   Whether the obligation semantically targets:
   - information state;
   - relationship state;
   - social/institutional state;
   - physical/event state;
   - payoff/consequence state.

5. `resolution_role`
   - PRE_RESOLUTION_ADVANCE only for the F04 comparison set.

Excluded from the signature:
- obligation ID;
- character/entity names;
- group names;
- event/payoff IDs;
- numbers;
- location nouns;
- prop nouns;
- literal statement text;
- literal concrete action text.

The signature must therefore remain the same when only story material changes but the dramatic transaction role is the same.

## Frozen repetition rule (동결 반복 규칙)
A F04 semantic repetition violation exists when:
- the scene is non-RESOLVE;
- the same normalized semantic transaction signature appears **>= 3 times** in one episode scene graph.

Allowed:
- 1 occurrence;
- 2 occurrences;
- any number of RESOLVE scenes;
- same transaction family with a different normalized causal/state role profile.

Violation issue token:
`SEMANTIC_TRANSACTION_REPEAT_GE3`

Diagnostics must expose:
- signature;
- occurrence count;
- scene IDs;
- transaction stages;
- obligation IDs.

## Pre-primary deterministic gates (사전 1차 결정론적 게이트)
Before Treatment source freeze:

### G1 — Material-variant clone detection
Three scenes with different names/props/locations but the same semantic transaction signature:
Treatment flags; Control may miss.

### G2 — Two-occurrence tolerance
Two semantically identical non-RESOLVE transactions:
Treatment does NOT fail.

### G3 — RESOLVE exclusion
Three or more RESOLVE scenes:
Treatment does NOT flag F04.

### G4 — Role differentiation
Same transaction family used three times with materially different causal/state role profiles:
Treatment does NOT falsely merge distinct signatures.

### G5 — Existing exact duplicate gates preserved
Existing material/pattern/function/action duplicate checks remain unchanged.

### G6 — R66 F01 regression
Known R62-R65 F01 regressions remain PASS.
R66 fresh transaction decisions remain bit-identical.

### G7 — R67 F07 regression
Dual-Ledger State Carry Runtime behavior remains unchanged.
R67 fresh 12-case qualification behavior remains PASS.

### G8 — Runtime integrity
Whole runtime compile PASS.
No Production/DB mutation.
Code Boundary Audit confirms validator-only change.

Any gate failure => HOLD before source freeze.

## Source freeze (소스 동결)
Only after G1-G8 PASS:
- hash Treatment source;
- seal canonical diff;
- seal deterministic gate receipts;
- no tuning after freeze.

## Fresh primary qualification set (신규 주요 자격시험 세트)
Only after Treatment source freeze:
create **16 new synthetic scene-graph cases**:
- 8 positive semantic-repeat cases;
- 8 negative-control cases.

Positive cases must include:
- same semantic transaction under different characters;
- different locations;
- different props;
- different literal statements/actions;
- same normalized role repeated >=3.

Negative controls must include:
- only two repetitions;
- repeated RESOLVE only;
- same family but distinct state-role profiles;
- same family but distinct causal roles;
- dense episode with legitimate family reuse;
- mixed relationship/information/social roles.

Fresh inputs are sealed before Treatment execution.

## Primary qualification gates (주요 자격 기준)
R68 PASS requires:
- positive detection = **8/8**;
- negative-control correct non-detection = **8/8**;
- false positive = **0/8** negatives;
- false negative = **0/8** positives;
- R66 F01 regression PASS;
- R67 F07 regression PASS;
- existing exact duplicate validators unchanged.

No external blind quality evaluation is required for the primary R68 claim because R68 qualifies a deterministic validation predicate, not screenplay-style preference.

## Claim boundary (주장 경계)
PASS establishes only:
`F04_SEMANTIC_TRANSACTION_REPETITION_VALIDATOR = QUALIFIED_AT_SCENE_GRAPH_VALIDATION_LEVEL`

It does NOT establish:
- F06 Scene Necessity closure;
- F08 Provider Context closure;
- full screenplay-surface anti-repetition quality;
- dialogue/surface repetition closure;
- Production promotion.

## Physicalization rule (물리화 규칙)
If R68 closes PASS and Candidate runtime changes:
- create a new 5-Part / 9-Package Physical Authority (물리 권위);
- preserve exact R67 runtime as Qualified Parent (자격 부모);
- preserve R66/R58 fallback lineage;
- Production remains unchanged.

Status token:
`R68_PREREGISTERED__F04_SEMANTIC_TRANSACTION_VALIDATOR_ONLY__PARENT_SYNC_R65__CONTROL_R67_IMMUTABLE__OUTPUTS_0`
