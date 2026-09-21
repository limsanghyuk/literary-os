# R70 Stage B Live Provider Execution Result R1 — VALIDITY HOLD

Date: 2026-09-21
Status: `R70_STAGE_B_EXECUTED__VALIDITY_HOLD__NO_QUALITY_VERDICT__NO_PROMOTION`

## Evidence custody
Developer-supplied execution report:
`R70_실험결과_개발자인계보고서.md`

Report SHA256:
`8cf4805e5e0566150dc3de23675e4ef351c6cc8201cd6415a7f2d73e13cf7935`

Evidence ZIP:
`R70_STAGE_B_CODEX_EXECUTION_EVIDENCE_R1_20260921.zip`

Evidence ZIP SHA256:
`dd6d42033a0595e525eb0df5651eb5ef7d5c1a4140c1759c81f5739800c07120`

Sidecar SHA matched exact Evidence ZIP SHA.
ZIP CRC: PASS.
Entry count: 335.

## Frozen execution seal
Provider:
`openai`

API family:
`responses`

Model:
`gpt-5.6-sol`

Reasoning:
`high`

Max output tokens:
`12000`

Timeout:
`600 sec`

Max attempts per arm:
`2`

Treatment runtime SHA256:
`1e4ca6fd7e60ce9e70507dbb7deb90a2438be6ca62a709222d00ff3b8db13182`

Paired payload SHA256:
`8ad241820986dc383961da47df36d7f19ef31f80a7ab403febdceabb7bc6a169`

Stage B input SHA256:
`3bf7b1a20317b20f02e45ae70fe59863c8362d9d582bbf84de0d91e643b6017e`

Hidden mapping SHA256:
`058cff81f62666d32b58cec9d5cf2181552592074e2f48f6bc84f2ec9949849d`

Mapping was not revealed.

## Live execution
Primary arms:
`24`

Retries:
`24`

Total provider calls:
`48`

HTTP 200:
`48/48`

Provider OK:
`48/48`

Guard PASS attempts:
`0/48`

Valid arms:
`0/24`

Valid pairs:
`0/12`

Invalid pairs:
`12/12`

Failure reasons:
`EXIT_STATE_MISMATCH = 48/48`

Usage:
- input tokens: 50,488
- output tokens: 67,033
- total tokens: 117,521

Judges:
`0`

Quality A/B mapping reveal:
`NO`

Surface-effect quality gate:
`HOLD_INVALID_PAIRS__QUALITY_EFFECT_NOT_ESTIMABLE`

## Direct validity defect
The local guard requires:
`rendered.exit_state == blueprint.exit_state`
as exact string identity.

The renderer instruction simultaneously tells the model to preserve meaning but not mechanically repeat blueprint wording.

The output schema allows exit_state to be an unconstrained string rather than an enum/const bound to the blueprint literal.

Therefore semantically compatible paraphrases are structurally rejected.

## Counterfactual diagnostic
An offline diagnostic replaced only the rendered `exit_state` field with the frozen expected literal and re-ran the unchanged guard.

Examined:
`48`

Guard PASS after single-field replacement:
`48/48`

Accepted as live evidence:
`NO`

Interpretation:
This supports `EXIT_STATE_EXACT_STRING_CONTRACT_CONFLICT` as the direct local blocking mechanism.
It does NOT prove screenplay semantic fidelity or Treatment literary-quality superiority.

## Runner operational repair
The supplied live runner contained a local `import importlib` shadowing defect inside `load_runtime`, causing `UnboundLocalError` before any API call.

A one-line execution-copy repair used the already-global import.
Original runner remained preserved.
The repair occurred at API calls = 0 and did not change Candidate provider code, request payloads, guard logic, call order or retry logic.

Per-call custody wrapper additionally persisted exact request bytes, raw response, provider result and local guard around each attempt.
Pre-output request hashes matched executed request bytes.

## Scientific verdict
This execution is NOT a Treatment loss.

It is:
`VALIDITY_HOLD`

Because 0/12 valid pairs exist, no quality win/tie/loss aggregate is legal.

Do not:
- drop invalid pairs to reduce denominator;
- count invalidity as Treatment loss;
- reveal mapping;
- create J01/J02/J03 literary judgments from invalid pairs;
- repair outputs post hoc;
- claim F08 surface effect;
- promote R70;
- claim Level-3 restoration.

## Next research boundary
Preserve this R1 immutably.

The next experiment must preregister a validity-contract repair before outputs.
Preferred narrow repair:
- `exit_state` remains a machine contract field;
- Provider must copy that field exactly;
- "do not mechanically repeat blueprint wording" applies only to action/dialogue/direction prose, not machine contract fields;
- Control and Treatment receive the identical repaired contract;
- source/request hashes are newly frozen;
- fresh valid paired execution occurs under a new successor identity or explicit preregistered amendment.

Alternative semantic-equivalence guard is allowed only if its evaluator, error-rate boundary and acceptance criteria are independently frozen before outputs.

Do not mix F02, F05 or Level-3 integrated qualification into this repair.

## Authority consequence
Physical Authority:
`SYNC-R67`

Active Qualified Candidate:
`R69 F06 / R68 F04 / R67 F07 / R66 F01 lineage`

Production:
`ENG:R47 / LEGACY_R53`

R70:
`STAGE_A_PASS__STAGE_B_R1_EXECUTED_VALIDITY_HOLD__SURFACE_EFFECT_UNRESOLVED`

No 5-Part/9-Package Candidate change follows from this invalid execution.

Status token:
`R70_STAGE_A_PASS__STAGE_B_R1_LIVE_48_CALLS__0_VALID_PAIRS__EXIT_STATE_CONTRACT_CONFLICT__VALIDITY_HOLD__NO_QUALITY_VERDICT__NO_PROMOTION__SYNC_R67_RETAINED`
