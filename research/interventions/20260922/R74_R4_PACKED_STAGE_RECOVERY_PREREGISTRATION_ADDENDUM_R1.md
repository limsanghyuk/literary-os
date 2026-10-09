# R74 R4 Packed-Stage Bridge Recovery Addendum R1

Date: 2026-09-23

Status:
`PREREGISTERED_RECOVERY_ADDENDUM__FINAL_PRIMARY_TREATMENT_OUTPUTS_0`

## Trigger
After the canonical R74 R3 Stage-M qualification and before any final R74 primary Treatment output, direct inspection of the unchanged R72 F05 allocator revealed that one physical Treatment scene can contain atoms from multiple source obligations whose exact-R69 semantic stages differ.

Historical R72-R5 diagnostic:
- cases inspected: 24/24
- cases containing at least one mixed-stage packed scene: 24/24
- total mixed-stage packed scenes observed: 220
- common profile: one obligation resolves while another still performs PROBE_INFORMATION / ACTIVATE_PAYOFF / other pre-resolution work.

## Defect
R74 R3 canonical projection exposes one `transaction_stage` per physical scene.

That is lossless for exact-R69 Control graphs, where one scene carries one transaction stage, but not for unchanged-F05 packed scenes. Collapsing a packed scene to one stage would either:
1. discard an obligation's stage role; or
2. assign resolution/advance protected contributions to the wrong obligation.

Classification:
`PRE_PRIMARY_MEASUREMENT_REPRESENTATION_DEFECT__F05_PACKED_MULTI_STAGE_SCENE`

This is not an F05 efficacy result.

## Frozen boundaries preserved
No change to:
- exact R69 Control;
- R72 F05 Adaptive Pressure Allocator R2;
- R68 F04 threshold, RESOLVE exclusion, signature fields, or repetition rule;
- R69 F06 protected-contribution classes N1-N5;
- R69 F06 removal / adjacent-merge rule;
- R71/F02, R67/F07, retrieval, renderer, Production, DB authority;
- canonical R74 P1-P11 thresholds;
- frozen final 24-case cohort.

## R4 narrow repair
R4 keeps R3 as a frozen dependency for all legacy/runtime cases.

For packed physical scenes only, R4 adds an arm-blind `obligation_stage_profile`:
- each source obligation retains its own ordered semantic stage role(s) inside the physical scene;
- one physical scene is never split for F06;
- if a single obligation performs ADVANCE and RESOLVE in the same physical scene, both roles are retained;
- a scene-level `transaction_stage` is a deterministic material-agnostic profile of the contained stage roles;
- N1/N3 are assigned only to obligations that resolve in that physical scene;
- N4/N5 are assigned only to obligations that perform non-resolution advance work in that physical scene;
- N2 is assigned to deferred/open pressure;
- unresolved stage provenance fails closed.

## Additional qualification gates before primary
R4 must pass the original M1-M7 plus:

M8 Packed-stage lossless projection:
- every packed atom maps to exactly one frozen source obligation;
- every packed source obligation has a nonempty stage plan;
- no physical packed scene loses any per-obligation stage role;
- historical R72-R5 Treatment diagnostics: 24/24 project with 0 unresolved packed-stage semantics.

M9 R3 backward equivalence:
- R68 frozen 16 cases: R4 legacy score output exactly equals R3 output;
- R69 frozen 16 cases: R4 legacy score output exactly equals R3 output.

Any failure => R74_MEASUREMENT_HOLD and no primary Treatment output.

## Scientific boundary
This addendum repairs only representational loss discovered before final primary Treatment execution. It does not alter the frozen F05 allocator or efficacy thresholds and does not itself qualify F05.
