# R66 — F01 Boundary-Safe Predicate Parser Gate Preregistration R1

Date: 2026-09-20
Status: `PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0`

## Sequential identity
- R62 CLOSED FAIL — diversification without semantic applicability
- R63 CLOSED FAIL — lexical license false positives
- R64 CLOSED FAIL — field-typed lexical polysemy
- R65 CLOSED FAIL — sense rules with unbounded substring collision
- R66 CURRENT / PREREGISTERED

## Parent authority
Physical authority:
`SYNC-R63`

Trust root:
`94697514918cff9091132fb6adafeb75dadf195c4be5e6e2c51861d561ba3916`

Active qualified Candidate / Control:
`SYNC-R58 / ADAPTIVE_UL16`

Exact Control source SHA256:
`42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

R65 failed source SHA256:
`7bfaa77ddff10406cd7a710daafe88262de57732898c86eb61796b8ad5718dd6`

Production:
`ENG:R47 / LEGACY_R53`

Runtime DB:
`DB59 frozen`

Research DB:
`DB64 research-only`

## Causal target
Only F01 transaction-family semantic applicability.

R66 repairs only:
`TARGETED_SENSE_DISAMBIGUATION_IS_NOT_BOUNDARY_SAFE_SEMANTIC_PARSING`

No F04/F06/F07/F08 intervention.

## Research question
Can F01 family licensing become safe enough for blind qualification if every positive lexical cue is boundary-safe and subordinate to an explicit predicate/argument contract, while ambiguous or unsupported evidence fails closed to exact R58?

## Hypothesis
The R65 failure class will be removed when:
1. positive lexical atoms are matched only at valid token/morpheme/phrase boundaries;
2. compound phrases are resolved before generic lexical atoms;
3. lexical evidence cannot by itself establish causal roles;
4. required predicate arguments and structural prerequisites remain mandatory;
5. uncertainty abstains to exact R58.

Frozen fallback:
`NO_BOUNDARY_SAFE_POSITIVE_EVIDENCE / MISSING_ARGUMENT / MISSING_CAUSAL_SUPPORT / AMBIGUOUS_SENSE -> ABSTAIN -> EXACT R58 BASELINE`

## Control
Exact SYNC-R58 behavior, immutable.

## Treatment lineage
Treatment may reuse:
- R62 family proposal generator;
- R63 exact-R58 fallback architecture;
- R64 field provenance;
- R65 compound/sense predicates.

Treatment may change only:
- lexical boundary parser;
- phrase/token/morpheme normalization used for positive semantic evidence;
- predicate argument extraction needed to consume the boundary-safe evidence;
- deterministic evidence receipts.

Treatment must NOT change:
- obligation compiler/schema semantics;
- due/deferred definitions;
- dependency graph semantics;
- sequence bundling;
- resolution semantics;
- F04/F06/F07/F08;
- DB authority;
- Provider model/prompt;
- Production path.

## Boundary-safe parsing doctrine

### B1 — No raw substring evidence
No positive semantic license may use Python-style unbounded `needle in text` logic for lexical atoms.

The failure `시한` inside `표시한다` must be impossible by construction.

### B2 — Phrase boundaries
Multi-word/multi-syllable phrases may be recognized only when:
- they form an explicit normalized phrase boundary; or
- they are a whitelisted compound whose whole compound has the intended sense.

### B3 — Korean lexical atoms
For Korean positive lexical atoms:
- exact whitespace/punctuation token;
- or explicitly enumerated inflectional stem + allowed grammatical suffix boundary;
- never arbitrary internal substring.

Examples:
- `시한`, `시한이`, `시한을`, `시한까지` may count as DEADLINE;
- `표시한다` must not count as `시한`;
- `막다`, `막았다`, `막는` may support BLOCK only when the lexical verb is the token/morpheme, while `막차` must not.

### B4 — English lexical atoms
Use alphanumeric word boundaries. Substrings inside unrelated words are not evidence.

### B5 — Compound-first sense
Specific compounds override generic atoms:
- 표면/도장/바닥/벽면/천장/외장/내장/코팅/목재 + 마감 => FINISHING_PROCESS
- 제출/접수/원고 + 마감, 마감 시각/시간/기한, 마감까지 => DEADLINE
- 호스/배관/유압/기압/수압/공기압/압력계 => PHYSICAL_PRESSURE
- 사회적/시간 + 압박, 선택지 축소, 제재/통제 강화 => DRAMATIC_OR_SOCIAL_PRESSURE

### B6 — Lexical evidence is supporting evidence, not causal proof
A token/phrase can propose or support a predicate, but ACCEPT still requires the family-specific predicate arguments and structural support.

## Family predicate contracts
R65 family contracts remain frozen, with the following parser requirement added to every positive lexical cue:
`BOUNDARY_SAFE = TRUE`.

### MISINTERPRETATION
Require:
`EXISTING_FALSE_BELIEF(holder, proposition)`
from eligible information/relationship state.

### COST_BEARING_CHOICE
Require:
`CHOOSE(actor, alternatives)` + `BEAR_COST(actor,cost)`.

### PHYSICAL_RISK_FAILURE
Require:
`PHYSICAL_FAILURE_OR_RISK_REALIZATION(entity,event)`.
Successful mitigation is not failure.

### NEGOTIATION_EXCHANGE
Require:
`COUNTERPARTY(a,b)` + `CONDITIONAL_EXCHANGE(a,b,term)`.

### RELATIONSHIP_BOUNDARY_CHANGE
Require:
`RELATIONSHIP_BOUNDARY_DELTA(a,b,type)`.

### WITHHELD_INFORMATION_MOVE
Require:
`INTENTIONAL_WITHHOLD(actor,information)`.

### DISCOVERY
Require:
`NEW_FACT_ESTABLISHED(source,fact)`.

### SOCIAL_INSTITUTIONAL_PRESSURE
Require:
`INSTITUTIONAL_CONSTRAINT(authority,target,rule/process)`.

### PARTIAL_CONSEQUENCE
Require structural prior cause + current consequence.

### COUNTERMOVE
Require structural prior opposing move + explicit response action.
Obstacle words alone never license.

### FAILED_ATTEMPT
Require attempt + supported failure.

### PRESSURE_ESCALATION
Require sense-resolved dramatic/social/deadline pressure + escalation.
Physical pressure/process-finishing senses are excluded.

## Known-failure regression set
Regression-only, never primary qualification:
- R62 C06 COST_BEARING_CHOICE mismatch
- R62 C08 PHYSICAL_RISK_FAILURE mismatch
- R62 C11 MISINTERPRETATION mismatch
- R63 hose physical pressure false PRESSURE_ESCALATION
- R63 막차 false COUNTERMOVE
- R63 successful mitigation false PHYSICAL_RISK_FAILURE
- R64 표면 마감 false deadline PRESSURE_ESCALATION
- R65 표시한다 containing 시한 false deadline PRESSURE_ESCALATION

All eight must be blocked or semantically replaced before source freeze.

## Pre-primary gates
Before source freeze:
1. exact R58 Control source verified;
2. R66 diff confined to F01 boundary parser/predicate evidence + diagnostics/tests;
3. known-failure 8/8 PASS;
4. R58B regression PASS;
5. R63 fresh-set regression PASS;
6. R64 fresh-set regression PASS;
7. R65 fresh-set regression PASS;
8. whole runtime compile PASS;
9. due exactly-once PASS;
10. deferred/blocked preservation PASS;
11. duplicate concrete action = 0;
12. no DB/Provider/Production mutation.

Any failure => HOLD before source freeze.

## Source freeze
After all pre-primary gates:
- hash Treatment source;
- seal canonical diff and receipts;
- no source tuning after freeze.

## Fresh R66 primary set
Only AFTER source freeze:
create exactly 12 new synthetic paired cases.

Requirements:
- no reuse of R62/R63/R64/R65 stories;
- no oracle-only tags;
- include boundary-collision traps;
- include compound/sense ambiguity;
- include positive-license cases;
- include abstention-demanding cases;
- include causal/dependency and open/deferred cases;
- exact R58 Control validation before Treatment execution.

Seal fresh inputs before Treatment run.

## Fresh selector-safety gate
Both arms:
- 12/12 architecture validation;
- due exactly-once;
- deferred/blocked preservation;
- no duplicate concrete action.

Treatment:
- every ACCEPT has predicate/argument receipt;
- every positive lexical cue used by a receipt is boundary-safe;
- family causal prerequisites are independently supported;
- no unsupported event/state invention;
- ambiguous evidence -> exact R58 fallback.

Any clear violation:
`R66 CLOSED FAIL BEFORE BLIND`.

## External blind gate
Only after mechanical/safety PASS.

Seal paired outputs and hidden mappings before dispatch.

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

Valid unfavorable result is immutable.

## Claim boundary
PASS establishes only:
`F01_BOUNDARY_SAFE_PREDICATE_PARSER_GATE = QUALIFIED_AT_PLANNING/SCENE-CONTRACT_LEVEL`

No F04/F06/F07/F08 closure, full screenplay-surface claim or Production promotion.

Status token:
`R66_PREREGISTERED__F01_BOUNDARY_SAFE_PREDICATE_ONLY__PARENT_SYNC_R63__CONTROL_SYNC_R58_IMMUTABLE__R62_R65_REGRESSION_ONLY__OUTPUTS_0`
