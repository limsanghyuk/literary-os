# R64 — F01 Typed Semantic-Role License Gate Preregistration R1

Date: 2026-09-20
Status: `PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0`

## Sequential state
- R62 CLOSED FAIL — diversification without reliable applicability/abstention
- R63 CLOSED FAIL — pre-blind semantic-safety gate
- R64 CURRENT / PREREGISTERED

## Parent authority
Physical parent:
`SYNC-R61`

Active qualified Control:
`SYNC-R58 / ADAPTIVE_UL16`

Control adaptive source SHA256:
`42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

R63 failed research source SHA256:
`7236eba306305269b06f9924c617139ecca038a5c6697891bac770a07913b7dd`

Production:
`ENG:R47 / LEGACY_R53`

Runtime DB:
`DB59 frozen`

Research DB:
`DB64 research-only`

## Causal target
Only F01 transaction-family applicability.

R64 does NOT reopen F04/F06/F07/F08.

## R63 failure to repair
R63 used a separate license gate, but its evidence extraction remained lexical and partially correlated with the proposal mechanism.

Known fresh failures:
1. physical hose pressure -> false dramatic PRESSURE_ESCALATION;
2. substring 막 in 막차 -> false COUNTERMOVE.

Scientific diagnosis:
`LEXICAL_LICENSE_IS_NOT_SEMANTIC_LICENSE`

## Research question
Can F01 diversification qualify safely if family admission is based on typed, field-provenanced semantic-role evidence rather than raw aggregate text/substrings, while uncertainty falls back exactly to R58?

## Hypothesis
A transaction family is safe enough to admit only when its required semantic role is supported by an eligible structured field and causal relation. Generic obstacle/setting words and substring collisions must never constitute sufficient license.

Fallback:
`MISSING / AMBIGUOUS / WRONG-SOURCE EVIDENCE -> ABSTAIN -> EXACT R58 BASELINE`

## Control
Exact SYNC-R58 behavior, immutable.

## Treatment lineage
R64 may reuse the R62 proposal generator and R63 fail-closed fallback architecture only.

Permitted changes:
- replace R63 lexical license evidence extraction;
- construct typed evidence records from existing obligation fields;
- require family-specific typed evidence;
- expose deterministic evidence provenance and rejection reason;
- preserve exact R58 fallback.

Prohibited changes:
- obligation compilation/schema semantics;
- due/deferred definitions;
- dependency graph semantics;
- sequence bundling;
- resolution semantics;
- F04 repetition validator;
- F06 necessity;
- F07 State Carry runtime;
- F08 Provider context;
- DB authority;
- Provider prompts/models;
- Production path.

No new input-only oracle tags may be added to fresh synthetic cases merely to make R64 succeed.

## Typed Semantic Evidence Record
Every ACCEPT must be explainable as one or more records:

`{role, source_field, actor_or_owner_support, dependency_support, polarity, certainty, evidence_class}`

Allowed source fields:
- kind
- visible_action
- information_delta
- relationship_delta
- social_delta
- depends_on
- owners
- group_refs
- payoff_ref
- event_ref
- statement only for narrow obligation-purpose evidence when explicitly allowed below

The generic obstacle field is NOT a positive semantic license for:
- PRESSURE_ESCALATION
- COUNTERMOVE
- COST_BEARING_CHOICE
- MISINTERPRETATION
- NEGOTIATION_EXCHANGE

Obstacle may only act as contradiction/risk context unless a family contract explicitly permits it.

Substring matches inside unrelated words are never evidence.
Where lexical cues remain necessary, matching must use normalized token/phrase boundaries.

## Source-separation rule
Proposal generation and license validation may inspect overlapping obligations, but an ACCEPT may not be justified solely by the same weak aggregate lexical cue that generated the proposal.

For each ACCEPT the license receipt must state:
- proposal family;
- required role;
- source field(s);
- structural corroboration;
- reason code.

If no eligible independent/typed evidence exists:
ABSTAIN.

## Family contracts

### MISINTERPRETATION
Required role:
`EXISTING_FALSE_BELIEF`

Eligible positive source:
- information_delta or relationship_delta only.

Must describe an already-existing mistaken interpretation/belief that this obligation must dramatize.

Disallowed:
- uncertainty;
- verification need;
- sensor error alone;
- statement/obstacle generic words;
- negated warnings such as “do not misread.”

### COST_BEARING_CHOICE
Required roles:
`CHOICE` + `ACTOR_BEARING_COST`

Eligible positive sources:
- visible_action;
- relationship_delta for a relational sacrifice;
- statement only if it explicitly requires the actor to choose and bear the cost.

Obstacle cost alone is not evidence.

### PHYSICAL_RISK_FAILURE
Required roles:
`PHYSICAL_ACTION` + `REQUIRED_FAILURE_OR_RISK_REALIZATION`

Eligible positive source:
- visible_action primarily;
- event_ref / depends_on as causal corroboration.

Physical danger in setting/obstacle alone is insufficient.

### NEGOTIATION_EXCHANGE
Required roles:
`COUNTERPARTY` + `CONDITIONAL_EXCHANGE`

Eligible positive sources:
- relationship_delta;
- social_delta;
- visible_action;
plus owners >= 2 or equivalent counterparty support.

### RELATIONSHIP_BOUNDARY_CHANGE
Required:
- relationship_delta non-empty and semantically about access/distance/trust/contact/cooperation/refusal;
- relationship target support.

### WITHHELD_INFORMATION_MOVE
Required:
`INTENTIONAL_WITHHOLDING`

Eligible source:
- information_delta plus actor/owner support;
- visible_action corroboration if available.

Missing/unavailable information is not intentional withholding.

### DISCOVERY
Required:
`NEW_FACT_REVEAL`

Eligible source:
- information_delta describing a fact newly established/revealed.
Verification of an already-known proposition does not count.

### SOCIAL_INSTITUTIONAL_PRESSURE
Required:
`INSTITUTIONAL_MECHANISM`

Eligible source:
- social_delta;
plus group_refs or explicit authority/process structure.

### PARTIAL_CONSEQUENCE
Required:
`PRIOR_CAUSE` + `CURRENT_CONSEQUENCE`

Eligible structural support:
- depends_on / payoff_ref / event_ref;
plus visible_action or statement requiring the consequence now.

### COUNTERMOVE
Required:
`IDENTIFIABLE_PRIOR_OPPOSING_MOVE` + `RESPONSE_ACTION`

Required structural support:
- depends_on non-empty;
- at least one counterparty/owner relation where applicable;
- visible_action or statement explicitly represents the response.

Obstacle lexical material alone is prohibited.
A substring such as 막 within 막차 can never license COUNTERMOVE.

### FAILED_ATTEMPT
Required:
`ATTEMPT_ACTION` + `SUPPORTED_FAILURE`

Eligible source:
- visible_action.
Statement may corroborate intended failure but may not invent it.

### PRESSURE_ESCALATION
Required:
`DRAMATIC_OR_SOCIAL_PRESSURE_DELTA`

Eligible positive source:
- social_delta;
- relationship_delta;
- statement only when it explicitly describes tightening deadline/constraint/social pressure as the dramatic transaction.

Disallowed:
- physical fluid/air/electrical/mechanical pressure;
- obstacle-only pressure words;
- generic “pressure” without typed dramatic target.

## Polarity / contradiction gate
Even a positive candidate role is rejected if:
- evidence is negated;
- obligation explicitly requires the thread/state to remain open and the family would prematurely settle it;
- the role belongs to a different semantic domain;
- the family requires a new event/state not present in the obligation;
- the only support is ambiguous lexical overlap.

## Known-failure regression set
Regression-only; never count toward primary qualification:
- R62 C06 wrong COST_BEARING_CHOICE
- R62 C08 wrong PHYSICAL_RISK_FAILURE
- R62 C11 wrong MISINTERPRETATION
- R63 airport hose-pressure false PRESSURE_ESCALATION
- R63 subway 막차 false COUNTERMOVE

These five must all be blocked or semantically replaced before fresh primary execution.

## Implementation gates
Before source freeze:
1. exact Control source verified;
2. R64 diff confined to F01 license/evidence path + diagnostics/tests;
3. 5/5 named known-failure regressions PASS;
4. R58B regression PASS;
5. whole runtime compile PASS;
6. due exactly-once / deferred / blocked preservation PASS;
7. no DB/Provider/Production mutation.

## Source freeze
Treatment source must be hashed and Hub-sealed before any R64 fresh primary cases are generated.

No source tuning after fresh-case creation.

## Fresh primary design
After source freeze, create 12 new materially evaluable paired cases.

Requirements:
- no reuse of R62/R63 story material;
- no oracle-only tags;
- multiple obligation kinds/functions;
- both clearly licensed and abstention-demanding opportunities;
- semantic-domain ambiguity counterexamples;
- causal/dependency cases;
- all cases validate under exact R58 Control before Treatment is run.

## Fresh mechanical / selector-safety gate
Both arms:
- 12/12 architecture validation;
- due exactly-once;
- deferred preservation;
- blocked preservation;
- no duplicate concrete action.

Treatment:
- every ACCEPT has typed provenance receipt;
- every ACCEPT satisfies its family contract;
- no unsupported event/state invention;
- all ambiguous or wrong-source evidence abstains to exact R58.

Any clear violation:
`R64 CLOSED FAIL BEFORE BLIND`

## External blind gate
Only after mechanical/safety PASS.

Seal paired outputs and hidden mappings before dispatch.
Independent judges must not see lineage, mapping or known failures.

Evaluate:
- transaction specificity;
- causal coherence;
- resistance/choice/cost;
- non-mechanical progression;
- necessity;
- obligation fidelity;
- semantic applicability;
- unsupported novelty / premature-resolution risk.

Frozen aggregate gate:
- Treatment wins >= 7/12;
- wins + ties >= 10/12;
- losses <= 2/12;
- zero critical state/obligation-fidelity violations.

Valid unfavorable result is immutable.

## Selector safety override
R64 FAIL even with a favorable blind aggregate if:
- a family is accepted without required typed evidence;
- semantic-domain polysemy supplies the only license;
- substring collision supplies the only license;
- an ACCEPT invents a false belief, bargain, countermove, cost-bearing choice, failure, institutional constraint, pressure trajectory, or new fact.

## Claim boundary
PASS establishes only:
`F01_TYPED_SEMANTIC_ROLE_LICENSE_GATE = QUALIFIED_AT_PLANNING/SCENE-CONTRACT_LEVEL`

No claim for F04/F06/F07/F08, full screenplay surface, Candidate promotion to Production, or Production promotion.

Status token:
`R64_PREREGISTERED__F01_TYPED_ROLE_LICENSE_ONLY__PARENT_SYNC_R61__CONTROL_SYNC_R58_IMMUTABLE__KNOWN_R62_R63_FAILURES_REGRESSION_ONLY__OUTPUTS_0`
