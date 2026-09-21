# R70 Stage B R2 — Exit-State Machine-Contract Repair Preregistration R1

Date: 2026-09-21
Status: `PREREGISTERED__OUTPUTS_0__R70_R1_PRESERVED_VALIDITY_HOLD`

## Parent evidence
R70 Stage B R1 is immutable:
`R70_STAGE_B_EXECUTED__VALIDITY_HOLD__NO_QUALITY_VERDICT__NO_PROMOTION`

R1 result commit:
`6e45acd4c93038447a29ce977248634d8fd22760`

R1 live execution:
- 48 provider calls
- HTTP 200: 48/48
- Provider OK: 48/48
- valid arms: 0/24
- valid pairs: 0/12
- failure reason: EXIT_STATE_MISMATCH 48/48
- judges: 0
- mapping reveal: NO

R1 must not be reinterpreted as quality loss or quality pass.

## Causal target
Only:
`STAGE_B_VALIDITY_CONTRACT__EXIT_STATE_MACHINE_FIELD`

This is not a new F08 treatment change.

## Research question
Can the R70 Stage B provider validity boundary be repaired so that the machine contract field `exit_state` is exact and deterministic without constraining the literary realization fields, while keeping Control/Treatment context differences unchanged?

## Diagnosis frozen before R2 implementation
R1 local guard requires:
`scene_render.exit_state == scene_blueprint.exit_state`

but R1:
- output JSON Schema allowed any string for `exit_state`;
- renderer instructions said not to repeat blueprint wording mechanically.

Offline counterfactual:
- 48/48 invalid R1 attempts pass the unchanged local guard when only `exit_state` is replaced with the frozen expected literal.
- This is diagnostic only and does not validate literary quality.

## R2 repair hypothesis
If `exit_state` is treated as a machine contract field rather than free prose, then:
- the provider output schema should allow exactly one value, the frozen blueprint exit_state;
- instructions should explicitly require verbatim copy for `exit_state`;
- the non-mechanical-repetition rule should apply only to action/dialogue/subtext prose;
- the existing exact-match local guard should remain unchanged.

This should eliminate the known contract contradiction without changing the literary Control/Treatment comparison.

## Frozen repair method
Allowed changes ONLY in:
`literary_os_runtime/provider_backed_renderer.py`

Required changes:
1. In `build_scene_render_payload`, create a per-scene output schema whose `exit_state` is:
   `{"type":"string","enum":[scene_blueprint.exit_state]}`
2. In `OpenAIResponsesProvider.build_request`, use the payload's frozen `output_schema` rather than the global generic schema.
3. In `build_renderer_instructions`, state:
   - exit_state is a machine-contract field;
   - copy it exactly from scene_blueprint.exit_state;
   - do not paraphrase it;
   - the anti-mechanical-copy rule applies only to action/dialogue/subtext prose.
4. Keep `evaluate_render_contract_locally` exact exit-state comparison unchanged.

OpenAI Structured Outputs supports enum-constrained JSON Schema values; R2 uses a single-value enum rather than semantic-equivalence inference.

## Prohibited changes
- Authorized Provider Context content or filtering;
- R70 Treatment context;
- R69 Control context;
- F01/F04/F06/F07 logic;
- Scene Blueprint semantics;
- Scene Contract semantics;
- Texture Contract;
- local exact exit-state guard;
- model-quality thresholds;
- judge rubric;
- hidden mapping after it is frozen;
- Production path;
- DB.

## Deterministic pre-freeze gates
R2-A1. R1 frozen runtime reproduces the 48/48 EXIT_STATE_MISMATCH diagnosis from sealed evidence.
R2-A2. Dynamic output schema has exactly one allowed exit_state value equal to blueprint.exit_state.
R2-A3. Provider request uses the dynamic payload output_schema.
R2-A4. Instructions separate machine-field exact copy from prose non-mechanical rendering.
R2-A5. Local guard remains AST-identical in exit-state comparison behavior.
R2-A6. Control/Treatment context functions remain unchanged from R70 R1.
R2-A7. R66 F01 regression PASS.
R2-A8. R67 F07 regression PASS.
R2-A9. R68 F04 regression PASS.
R2-A10. R69 F06 regression PASS.
R2-A11. R70 Stage A authorized-context regression PASS.
R2-A12. Runtime compile PASS.
R2-A13. Code Boundary Audit PASS.

## Source freeze
Only after R2-A1..A13 PASS:
- freeze R2 runtime/source;
- freeze canonical diff;
- no later repair tuning.

## Fresh R2 Stage B cases
Create exactly 12 new synthetic paired scene cases only AFTER R2 source freeze.

Do not reuse R1 Stage B scene cases for the primary R2 literary-effect estimate.

The fresh 12 cases must cover the same F08 context-effect dimensions:
- character-specific voice;
- relationship status pressure;
- information asymmetry;
- social/group context;
- institutional context where authorized;
- multi-cast ensemble;
- planner-only exclusion;
- empty/weak-context control conditions.

Control and Treatment must share exact:
- Scene Blueprint;
- Scene Contract;
- Texture Contract;
- model/settings;
- output schema;
- retry policy.

Only Provider Context differs.

## R2 live execution
Before any live output, seal exact:
- model;
- reasoning effort;
- max output tokens;
- timeout;
- retry count;
- frozen runtime SHA;
- fresh input SHA;
- paired payload SHA;
- hidden A/B mapping hash;
- request hashes.

Credential remains environment/secret-manager only.

## Validity gate
R2 literary evaluation begins only if:
- valid arms = 24/24;
- valid pairs = 12/12;
- all accepted attempts are real provider calls with provenance;
- no fallback/template output;
- all request hashes match frozen requests.

If 12/12 valid pairs are not obtained under the frozen retry rule:
`R70_STAGE_B_R2_VALIDITY_HOLD`
and no literary A/B verdict is computed.

## Blind quality evaluation
Only after 12/12 valid pairs:
- seal outputs;
- create independent J01/J02/J03 packets;
- mapping hidden;
- judges independent;
- mapping reveal only after all valid judgments are sealed.

Axes and critical violations remain exactly R70 R1 preregistration.

## Quality gate — unchanged
Treatment:
- wins >= 7/12
- wins + ties >= 10/12
- losses <= 2/12
- confirmed critical violations = 0

## Final interpretation
R2 validity repair PASS + quality gate PASS may close:
`F08_AUTHORIZED_PROVIDER_CONTEXT_WITH_SURFACE_EFFECT = QUALIFIED`

R2 does not itself establish Level-3 restoration.

## Authority boundary
Until full R2 closes PASS:
- Physical Authority = SYNC-R67
- Active Qualified Candidate = R69/R68/R67/R66 lineage
- Production = ENG:R47 / LEGACY_R53
- no Candidate physical promotion
- no R71

Status token:
`R70_STAGE_B_R2_PREREGISTERED__EXIT_STATE_MACHINE_CONTRACT_ONLY__FRESH_12_AFTER_SOURCE_FREEZE__R1_VALIDITY_HOLD_PRESERVED__OUTPUTS_0`
