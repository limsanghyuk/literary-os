# R65 — F01 Sense-Disambiguated Semantic Predicate Gate Preregistration R1

Date: 2026-09-20
Status: `PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0`

## Sequential identity
- R62 CLOSED FAIL — diversification without semantic applicability
- R63 CLOSED FAIL — lexical license false positives
- R64 CLOSED FAIL — typed-field lexical polysemy
- R65 CURRENT / PREREGISTERED

## Parent authority
Physical authority:
`SYNC-R62`

Trust root:
`c9acf57e92663f03c3231b45601dcef622e6bc8ff9cd18876874eaa1bff18b68`

Active qualified Candidate / Control:
`SYNC-R58 / ADAPTIVE_UL16`

Exact Control source SHA256:
`42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

R64 failed source SHA256:
`5118b1c728e4dcd94e00aaa719fe3682c9571537a2f59e79b83d3b9120bcbf42`

Production:
`ENG:R47 / LEGACY_R53`

Runtime DB:
`DB59 frozen`

Research DB:
`DB64 research-only`

## Causal target
Only F01 transaction-family applicability.

R65 repairs only:
`FIELD_TYPED_LEXICAL_EVIDENCE_IS_STILL_NOT_SENSE_DISAMBIGUATED_SEMANTICS`

No F04/F06/F07/F08 intervention.

## Research question
Can F01 diversified transaction families be safely admitted when family licensing is based on sense-disambiguated semantic predicates and causal arguments rather than token stems or field membership alone?

## Hypothesis
A family should be ACCEPTED only when:
1. a semantic predicate with the correct sense is established;
2. its required argument roles are present;
3. its causal preconditions are independently supported;
4. no contradictory/open-state condition exists.

Otherwise:
`AMBIGUOUS / WRONG SENSE / MISSING ARGUMENT / MISSING CAUSE -> ABSTAIN -> EXACT R58 BASELINE`

## Control
Exact SYNC-R58 behavior. Immutable.

## Treatment lineage
Treatment may reuse:
- R62 candidate-family proposal generator;
- R63 exact R58 fallback architecture;
- R64 typed source-field provenance.

Treatment may change only:
- semantic predicate construction;
- sense disambiguation;
- argument-role extraction;
- family-specific semantic predicate checks;
- deterministic evidence receipts.

Prohibited changes:
- obligation compiler/schema semantics;
- due/deferred definitions;
- dependency graph semantics;
- sequence bundling;
- resolution semantics;
- F04/F06/F07/F08;
- DB authority;
- Provider prompt/model;
- Production path.

## Sense-disambiguation principles

### P1 — Compound-first interpretation
Before token-level licensing, detect compound/domain phrases.

Examples:
- `표면 마감`, `도장 마감`, `바닥 마감`, `마감 작업` -> FINISHING_PROCESS, not DEADLINE.
- `원고 마감`, `제출 마감`, `마감 시각`, `마감까지` -> DEADLINE.
- `호스 압력`, `수압`, `기압`, `유압`, `압력계` -> PHYSICAL_PRESSURE.
- `사회적 압박`, `시간 압박`, `압박을 받다`, `선택지를 좁히다` -> DRAMATIC/SOCIAL_PRESSURE.

A more specific compound sense overrides a generic token sense.

### P2 — Predicate + argument requirement
A lexical item cannot license a family alone.
The evaluator must derive a predicate and its required arguments.

Examples:
- COUNTERMOVE requires `OPPOSING_MOVE(actor, target/action)` + `RESPONSE_ACTION(responder, prior_move)`.
- COST_BEARING_CHOICE requires `CHOOSE(actor, alternatives)` + `BEAR_COST(actor, cost)`.
- NEGOTIATION_EXCHANGE requires `COUNTERPARTY(a,b)` + `CONDITIONAL_EXCHANGE(a,b,item_or_term)`.
- PHYSICAL_RISK_FAILURE requires `PHYSICAL_FAILURE_OR_RISK(event/object)` + transaction relevance.
- PRESSURE_ESCALATION requires `DRAMATIC_PRESSURE(target, source_or_deadline)` + `ESCALATE(delta)`.

### P3 — Independent causal corroboration
Where a family presupposes a prior event/action, license must not be justified by the same lexical phrase that generated the proposal.

### P4 — Negation / success semantics
Successful mitigation is not failure.
Warnings against misinterpretation are not existing false beliefs.
Absence of information is not intentional withholding.

### P5 — Fail closed
If the sense cannot be resolved confidently from existing fields:
ABSTAIN to exact R58 precursor.

No invention is allowed to make the family fit.

## Family predicate contracts

### MISINTERPRETATION
Require:
`EXISTING_FALSE_BELIEF(holder, proposition)`
from information_delta or relationship_delta.
Mere uncertainty / verification / negated warning -> reject.

### COST_BEARING_CHOICE
Require:
`CHOOSE(actor, alternatives)`
AND
`BEAR_COST(actor, cost)`.
Cost must belong to the choice transaction, not obstacle background.

### PHYSICAL_RISK_FAILURE
Require:
`PHYSICAL_FAILURE_OR_RISK_REALIZATION(entity,event)`
from visible_action/statement plus causal relevance.
A successful corrective action without required failure -> reject.

### NEGOTIATION_EXCHANGE
Require:
`COUNTERPARTY(a,b)`
AND
`CONDITIONAL_EXCHANGE(a,b,term)`.

### RELATIONSHIP_BOUNDARY_CHANGE
Require:
`RELATIONSHIP_BOUNDARY_DELTA(a,b,type)`.

### WITHHELD_INFORMATION_MOVE
Require:
`INTENTIONAL_WITHHOLD(actor,information)`.

### DISCOVERY
Require:
`NEW_FACT_ESTABLISHED(actor/evidence,fact)`.
Simple verification of an already-stated proposition -> reject.

### SOCIAL_INSTITUTIONAL_PRESSURE
Require:
`INSTITUTIONAL_CONSTRAINT(authority,target,rule/process)`.

### PARTIAL_CONSEQUENCE
Require:
`CAUSE(prior,current_consequence)`
with structural dependency/payoff/event support.

### COUNTERMOVE
Require:
`OPPOSING_MOVE(prior_actor, prior_action)`
AND
`RESPONSE_ACTION(current_actor, prior_action)`.
Substring/obstacle-only evidence is prohibited.

### FAILED_ATTEMPT
Require:
`ATTEMPT(actor,goal)`
AND
`FAIL(attempt)`.

### PRESSURE_ESCALATION
Require:
`DRAMATIC_OR_SOCIAL_PRESSURE(target,source)`
AND
`ESCALATE(pressure)`.

Explicitly excluded senses:
- physical/mechanical/fluid/electrical pressure;
- surface/paint/floor finishing when interpreting `마감`;
- any process noun compound that is not a time deadline.

## Known-failure regression set
Regression-only and never primary:
- R62 C06 COST_BEARING_CHOICE mismatch
- R62 C08 PHYSICAL_RISK_FAILURE mismatch
- R62 C11 MISINTERPRETATION mismatch
- R63 hose `압력` false PRESSURE_ESCALATION
- R63 `막차` false COUNTERMOVE
- R63 successful mitigation false PHYSICAL_RISK_FAILURE
- R64 `표면 마감` false deadline/pressure escalation

All seven must be blocked or semantically replaced before source freeze.

## Pre-primary implementation gates
1. exact R58 Control source verified;
2. diff confined to F01 sense/predicate path + diagnostics/tests;
3. known-failure 7/7 PASS;
4. R58B regression PASS;
5. R63 fresh set regression PASS;
6. R64 fresh set regression PASS;
7. whole runtime compile PASS;
8. due exactly-once PASS;
9. deferred/blocked preservation PASS;
10. duplicate concrete action = 0;
11. no DB/Provider/Production mutation.

Any failure => HOLD before source freeze.

## Source freeze
After all pre-primary gates:
- hash Treatment source;
- seal canonical diff and regression receipts;
- prohibit tuning after freeze.

## Fresh R65 primary set
Only AFTER source freeze:
create exactly 12 new synthetic paired cases.

Requirements:
- no reuse of R62/R63/R64 stories;
- no oracle-only tags;
- include sense-polysemy counterexamples;
- include compounds whose surface token has multiple meanings;
- include positive licensed cases;
- include abstention-demanding cases;
- include causal/dependency and open/deferred cases;
- exact R58 Control validation before Treatment execution.

Seal inputs before Treatment run.

## Fresh selector-safety gate
Both arms:
- 12/12 validation;
- due exactly-once;
- deferred/blocked preservation;
- no duplicate concrete action.

Treatment:
- every ACCEPT has explicit predicate/argument receipt;
- every accepted predicate uses the correct sense;
- family causal preconditions are structurally supported;
- no unsupported state/event invention;
- ambiguous sense -> exact R58 fallback.

Any clear violation:
`R65 CLOSED FAIL BEFORE BLIND`.

## External blind gate
Only after mechanical/safety PASS.

Seal paired outputs and hidden mappings first.

Independent blind judges evaluate:
- transaction specificity;
- causal coherence;
- resistance/choice/cost;
- non-mechanical progression;
- necessity;
- obligation fidelity;
- semantic applicability;
- unsupported novelty/premature-resolution risk.

Frozen aggregate:
- Treatment wins >= 7/12;
- wins + ties >= 10/12;
- losses <= 2/12;
- zero critical state/obligation-fidelity violations.

A valid unfavorable result is immutable.

## Claim boundary
PASS establishes only:
`F01_SENSE_DISAMBIGUATED_SEMANTIC_PREDICATE_GATE = QUALIFIED_AT_PLANNING/SCENE-CONTRACT_LEVEL`

No F04/F06/F07/F08 closure, full screenplay-surface claim or Production promotion.

Status token:
`R65_PREREGISTERED__F01_SENSE_DISAMBIGUATED_PREDICATE_ONLY__PARENT_SYNC_R62__CONTROL_SYNC_R58_IMMUTABLE__R62_R63_R64_REGRESSION_ONLY__OUTPUTS_0`
