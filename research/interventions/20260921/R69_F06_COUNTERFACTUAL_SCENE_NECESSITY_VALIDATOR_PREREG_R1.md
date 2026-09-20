# R69 — F06 Scene Necessity Counterfactual Validator Preregistration R1

Date: 2026-09-21
Status: `PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0`

## Sequential identity (연속 연구 식별)
- R66 CLOSED PASS — F01 Boundary-Safe Predicate Parser (경계 안전 술어 파서)
- R67 CLOSED PASS — F07 Dual-Ledger State Carry Runtime (이중 원장 상태 이월 런타임)
- R68 CLOSED PASS — F04 Semantic Transaction Repetition Validator (의미 거래 반복 검증기)
- R69 CURRENT / PREREGISTERED

## Parent authority (부모 권위)
Physical Authority (물리 권위):
`SYNC-R66`

Active Qualified Candidate (활성 자격 후보):
`R68 F04 / R67 F07 / R66 F01 lineage`

Current runtime SHA256:
`af0fd4dc4ba3d7037e1d98ed8ec4177b155cae10936e8210e9e443a07ed69696`

Adaptive Showrunner source SHA256:
`c4a7ee8262378eec88fbe8fede718ced6883ae38addad1a851191f7766512806`

Production Engine (운영 엔진):
`ENG:R47 / LEGACY_R53`

Runtime DB (런타임 DB):
`DB59 frozen`

Research DB (연구 DB):
`DB64 research-only`

## Causal target (인과 대상)
Only F06:
`Scene Necessity Declarative Gap (장면 필요성 선언형 결함)`

R61 status:
`SUPPORTED`

Observed gap:
Every generated scene currently carries the same declarative field:
`merge_split_necessity = REMOVAL_MUST_WEAKEN_CAUSAL_RELATIONAL_INFORMATION_SOCIAL_OR_DEBT_PROGRESS`

Current validation checks only that this field is non-empty.

It does NOT actually test:
- scene removal;
- adjacent scene merge;
- protected semantic loss;
- obligation-resolution loss;
- deferred/open-state loss;
- factual state-delta loss.

## Research question (연구 질문)
Can a deterministic Counterfactual Scene Necessity Validator (반사실 장면 필요성 검증기) distinguish a genuinely necessary separate scene from a redundant or mergeable scene by simulating remove/merge consequences rather than trusting a declared necessity string?

## Hypothesis (가설)
A scene is necessary as a separate scene only when:
1. removing it causes at least one protected narrative loss; AND
2. no adjacent scene can absorb its protected contribution without violating transaction/state atomicity.

A scene is redundant/mergeable when:
- removal preserves all protected narrative contributions; OR
- an adjacent same-obligation scene can absorb the contribution without losing a protected atom.

## Control (대조군)
Exact current R68 qualified runtime.

No Control mutation.

## Treatment scope (처치 범위)
Validator-only change in:
`literary_os_runtime/adaptive_showrunner_ul16.py`

Permitted additions:
- protected scene-contribution extractor (보호 장면 기여 추출기);
- removal counterfactual simulator (제거 반사실 시뮬레이터);
- adjacent merge counterfactual simulator (인접 병합 반사실 시뮬레이터);
- scene necessity audit report (장면 필요성 감사 보고);
- one new F06 validation issue token.

Prohibited changes:
- scene generation;
- stage selection;
- F01 semantic selector;
- F04 repetition signature/rule;
- F07 State Carry runtime;
- sequence bundling/allocation;
- obligation compiler;
- F08 Provider Context;
- DB authority;
- Production path.

R69 must not change generated scene count or scene content. It only validates necessity.

## Protected narrative contributions (보호 서사 기여)
The validator may treat only these as protected counterfactual contributions:

### N1 — Resolution contribution (해결 기여)
A scene that uniquely resolves a due obligation contributes:
`RESOLVE_OBLIGATION:<obligation_id>`

Removing that scene is a loss.

### N2 — Deferred/open-state contribution (유예/열린 상태 기여)
A scene that uniquely registers a deferred/open pressure ID contributes:
`DEFERRED_PRESSURE:<id>`

Removing it is a loss unless another remaining scene/terminal ledger preserves the same required deferred state.

### N3 — Factual state-delta contribution (사실 상태 변화 기여)
A scene with `state_delta_required=true` contributes only non-generic final information/relationship/social state change roles supported by its obligation.

Generic pre-resolution placeholders are not protected factual deltas.

### N4 — Obligation-specific semantic advance (의무별 의미 진전)
A non-RESOLVE scene contributes:
`ADVANCE:<obligation_id>:<semantic_transaction_signature>`

This contribution is protected only if no other remaining scene for the same obligation carries the same semantic transaction signature.

This prevents scene ID uniqueness from automatically proving necessity.

### N5 — Causal bridge contribution (인과 다리 기여)
A non-RESOLVE scene may contribute:
`CAUSAL_BRIDGE:<obligation_id>:<dependency_profile>`
only when:
- the obligation has an explicit dependency/precondition; and
- no other remaining scene for the same obligation preserves the same dependency-aware semantic advance.

No lexical/material-only cue can create a causal bridge.

## Removal counterfactual (제거 반사실)
For each scene S:
1. remove S from a deep-copied scene graph;
2. recompute protected contribution coverage;
3. recompute due resolution count;
4. recompute deferred/open preservation;
5. compare factual state-delta coverage;
6. compare obligation-specific semantic advance coverage.

`removal_loss = true` only if at least one protected contribution is lost.

## Adjacent merge counterfactual (인접 병합 반사실)
A scene may be mergeable only into its immediate previous or next scene.

Merge is considered lossless only when:
- both scenes are in the same sequence;
- they address the same transaction obligation ID set;
- neither merge would create two distinct resolution events;
- deferred-pressure sets are union-compatible;
- factual state-delta roles do not conflict;
- the current scene's semantic advance signature is already represented by the neighbor OR can be represented without requiring two different transaction stages in one scene.

Frozen atomicity rule:
**two distinct transaction stages cannot be treated as one lossless scene.**

Therefore a same-obligation duplicate/same-signature pair may be mergeable; distinct transaction-stage progression is not automatically mergeable.

## Frozen necessity verdict (동결 필요성 판정)
For each scene:

`NECESSARY_SEPARATE_SCENE`
iff
- removal_loss = true; AND
- no lossless adjacent merge exists.

`REDUNDANT_OR_MERGEABLE_SCENE`
iff
- removal_loss = false; OR
- a lossless adjacent merge exists.

New validation issue token:
`COUNTERFACTUAL_SCENE_NOT_NECESSARY`

Diagnostics expose:
- scene_id;
- removal_loss boolean;
- lost protected contributions;
- mergeable_with previous/next scene IDs;
- reason codes.

## Pre-primary deterministic gates (사전 1차 결정론적 게이트)

### G1 — Same-obligation duplicate advance
Two adjacent non-RESOLVE scenes with:
- same obligation;
- same semantic transaction signature;
- distinct literal action/material;
must yield at least one redundant/mergeable scene.

### G2 — Unique resolution protected
Removing the only resolving scene for a due obligation must produce a loss.

### G3 — Unique deferred pressure protected
Removing the only scene/exit carrier of a required deferred pressure must produce a loss.

### G4 — Unique factual delta protected
A resolving scene carrying the only factual information/relationship/social delta must produce a loss.

### G5 — Distinct-stage atomicity
Two adjacent scenes for the same obligation but different transaction stages are not losslessly mergeable merely because the obligation ID is shared.

### G6 — Cross-obligation family reuse
Same semantic transaction signature on different obligation IDs does not by itself make either scene removable.

### G7 — F04 regression
R68 Semantic Repetition Validator behavior remains unchanged.

### G8 — F01/F07 regression
R66 F01 and R67 F07 qualified behavior remains unchanged.

### G9 — Runtime integrity
Whole runtime compile PASS.
Code Boundary Audit confirms validator-only change.
No DB/Production mutation.

Any failure => HOLD before source freeze.

## Source freeze (소스 동결)
Only after G1-G9 PASS:
- hash Treatment runtime/source;
- seal canonical diff and deterministic gate receipts;
- no rule/threshold tuning after freeze.

## Fresh primary qualification set (신규 주요 자격시험 세트)
Only after Treatment source freeze:
create exactly **16 new synthetic scene-graph cases**:
- 8 REDUNDANT_OR_MERGEABLE positives;
- 8 NECESSARY_SEPARATE_SCENE negatives.

Positive set must include:
- adjacent same-obligation duplicate semantic advance;
- duplicate advance with different characters/props/actions;
- lossless merge with same stage/signature;
- redundant non-resolve scene where removal preserves all protected contributions.

Necessary controls must include:
- unique resolution;
- unique deferred pressure;
- unique factual information delta;
- unique factual relationship delta;
- unique factual social delta;
- explicit dependency bridge;
- distinct-stage progression;
- same family across different obligation IDs.

Fresh inputs are sealed before Treatment execution.

## Primary qualification gates (주요 자격 기준)
R69 PASS requires:
- redundant/mergeable detection = **8/8**;
- necessary-scene correct protection = **8/8**;
- false positive against necessary controls = **0/8**;
- false negative against redundant positives = **0/8**;
- R68 F04 regression PASS;
- R67 F07 regression PASS;
- R66 F01 regression PASS;
- existing generation outputs unchanged.

No external blind is required for the primary R69 claim because R69 qualifies a deterministic scene-graph counterfactual validator, not stylistic preference.

## Claim boundary (주장 경계)
PASS establishes only:
`F06_COUNTERFACTUAL_SCENE_NECESSITY_VALIDATOR = QUALIFIED_AT_SCENE_GRAPH_VALIDATION_LEVEL`

It does NOT establish:
- screenplay-surface scene necessity after free-form Provider realization;
- F08 Provider Context closure;
- dialogue-level economy;
- Production promotion.

## Physicalization rule (물리화 규칙)
If R69 closes PASS and Candidate runtime changes:
- create a new 5-Part / 9-Package Physical Authority;
- preserve exact R68 runtime as Qualified Parent;
- preserve R67/R66/R58 lineage;
- Production remains unchanged.

Status token:
`R69_PREREGISTERED__F06_COUNTERFACTUAL_SCENE_NECESSITY_VALIDATOR_ONLY__PARENT_SYNC_R66__CONTROL_R68_IMMUTABLE__OUTPUTS_0`
