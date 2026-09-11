# P07-I4K-5R2 Attempt 2 Multipart Execution Note R1

Date: 2026-09-11
Experiment: `P07-I4K-5R2-FRESH-SURFACE-HYGIENE-REPAIR-REPLICATION`
Parent prereg commit: `4f1e72851ef3d986679fcf4da33d660f18012cf1`
Shared upstream seal commit: `8875555c31ce62db20eb1471b249d33fe2023a59`
Attempt 1 mechanical result: Control 24,285 chars / Treatment 24,265 chars / 50 scenes each / relative gap 0.0824% / forbidden internal-meta literals 0 / CH-SQ ids 0 / exact long duplicate 0. Attempt 1 is under-scale and therefore remains provisional and unscored.

## Root cause being repaired
The preregistered 760-900 mean scene-body character target was only guidance. Attempt 1 was generated as one monolithic 50-scene emission, and compression accumulated across the long output: measured mean scene-body scale was ~486 chars rather than the planned 760-900 range. The scientific threshold did not fail because of a changed hypothesis; the execution procedure failed to realize the already-frozen representation budget.

## Attempt 2 execution-only procedure
This note does not change any scientific threshold, hypothesis, arm definition, scene/event/sequence semantics, or decision rule.

1. The sealed 50-scene architecture remains byte-identical and authoritative.
2. Each arm is authored as ten ordered sequence transport segments, five scenes per segment, to prevent long-output compression.
3. Each segment must stay inside the already-sealed five scene semantics for its sequence. No new event, new scene, new sequence, new decision owner, or new future-thread mutation may be added.
4. Deepening is restricted to the preregistered allowed classes: scene-local situation direction, performer physical action, subtext-bearing interaction, and consequence realization.
5. The preregistered 760-900 mean scene-body character target remains guidance, not a new hard per-scene gate. The authoring target for a five-scene transport is therefore approximately 3,800-4,500 body characters solely as an execution allocation derived from the existing guidance.
6. No quality scores, pairwise preference, or arm-effect judgment may be inspected while writing or mechanically admitting Attempt 2.
7. After all 20 sequence transports exist, deterministic tooling must calculate the logical concatenated whole-episode body length, exact scene ids/counts, arm gap, internal/meta token leakage, CH/SQ ids, and exact long mechanical duplicates.
8. Only the original preregistered final gates decide admission: >=35,000 metadata-excluded screenplay-body characters per arm, <=10% arm gap, 50 exact scene ids, hygiene/integrity PASS. If Attempt 2 misses those gates, it stays provisional and Attempt 3 may be used under the original bounded-attempt rule.
9. If Attempt 2 passes, its ten ordered segments per arm become the physical transport representation of one logical whole-episode render. A manifest will fix segment order and hashes before masking.

## Governance
- This is an execution/transport correction, not a post-output threshold change.
- Attempt 1 remains preserved exactly; it is not edited or extended.
- No score, mask, or unblind exists at this point.
- Active Engine remains `P07-I4H Recovery R3`; Production `ENG:R47`; DB59; Formal scored count 137; Formal R140 `0/0/0`.

Status: `ATTEMPT2_EXECUTION_PROCEDURE_FROZEN__ORIGINAL_GATES_UNCHANGED__NO_ATTEMPT2_OUTPUT_AT_THIS_SEAL`