# P07 I4K DEBUG AND ERROR-PREVENTION GATE R1
Date: 2026-09-11

## PURPOSE
Block recurrence of the operational, governance, masking, scale, provenance, and recovery errors observed during I4K-5R2/R3/R4 work before they can contaminate a scored experiment.

## A. ACTOR-VISIBLE EXPRESSION HYGIENE — SHARED BASELINE
This rule applies equally to Control and Treatment and is NOT a Treatment-only feature.

1. Facial expression is stageable information, not an emotion label.
2. Prefer visible face/eye/mouth/breath/posture changes over direct emotion naming.
3. Emotion flow should be shown as observable progression: gaze breaks or locks, blink rate changes, jaw/lip tension, breath catches or lengthens, facial muscles release or harden, shoulders/neck/hands change tension, body distance changes, object handling changes, speech timing changes, silence/hesitation/interruption appears.
4. Avoid explanatory stage directions such as '슬퍼한다', '분노한다', '불안해한다', '감동한다' when a playable visible cue can carry the same dramatic information.
5. Direct emotion naming is allowed only when required for production safety/clarity or when no observable performance cue can preserve the licensed scene fact without ambiguity.
6. Do not prescribe microscopic facial choreography line by line. Use the minimum set of actor-playable cues needed to expose the turn and the emotional transition.
7. Do not have dialogue verbalize what stage direction already makes legible.
8. Emotional continuity must follow the scene's licensed cause/turn/exit state; no new backstory or motive may be invented to justify expression.

## B. ERROR TAXONOMY AND HARD BLOCKS

### G0 Runtime/Container Gate
BLOCK if memory.current >= 3.2 GiB of a 4 GiB cgroup, oom/oom_kill > 0, disk free < 8 GiB, or large archive extraction/join is unnecessary.
Required action: release page cache without deleting files; use streaming/selective reads; never run concurrent large decompressions.

### G1 Authority/Pointer Gate
BLOCK if CURRENT_* pointers disagree with the latest canonical result/physical closure, or if a new session resumes from a stale checkpoint.
Required action: compare main HEAD, canonical score/result commits, physical closure, and five CURRENT pointers before generation/scoring.

### G2 Preregistration Immutability Gate
BLOCK any renderer/intervention/threshold change after an experiment has produced outputs when the prereg forbids such change.
If a user requirement materially changes the renderer after outputs: close current experiment PRE-RENDER/PRE-SCORE as appropriate and start a new experiment ID with fresh upstream material.

### G3 Provenance Gate
BLOCK if workflow run_id/job_id/source commit/artifact digest are inconsistent or mixed across executions.
Use superseding receipt rather than overwriting historical evidence.

### G4 Scale Gate
Before Treatment generation, measure Control source/materialized length mechanically. Before masking, both arms must be >=35,000 body chars, 50 scenes, and relative gap <=10%.
Under-scale drafts remain PRE-SEAL and cannot consume an attempt unless both arms were sealed for admission under the prereg attempt rule.

### G5 Semantic/Continuity Gate
BLOCK masking if any event/scene/sequence/decision-owner/future-thread mutation exists, shared semantics are lost, or critical continuity violations >0.

### G6 Mask Leakage Gate
BLOCK scoring if masked packet exposes CONTROL/TREATMENT labels, source hashes, mapping, file names, unequal byte-length hints, or intervention-only metadata.
Mapping artifact must remain separate and unopened until all score packets are sealed.

### G7 Duplicate-Score Gate
Before any scoring, search main for an existing score seal/final result for the same experiment+attempt+mask. If one exists, STOP. Never rescore, average, or replace it after recovery.

### G8 Sidecar/Physical Seal Gate
After any append to CONTROL/A/B2, recompute actual outer SHA and canonical transport root. BLOCK promotion if manifest/closure/root sidecars predate the final bytes.
Preserve stale sidecars as historical superseded evidence.

### G9 Independent-Judge Gate
For independent confirmation, generation agent cannot provide the authoritative quality score. Judges receive only leak-resistant masked packets and frozen scoring contract; each judge packet must include provider/execution identity and receipts.

## C. EXECUTION ORDER
Runtime health -> Authority/pointer consistency -> Prereg/requirement consistency -> Fresh upstream -> Sequence/scene semantics -> Source render -> Scale/hygiene -> Semantic/continuity -> Freeze -> Mask leakage audit -> Score existence audit -> Independent scoring -> Mapping open -> Result seal -> Physical propagation -> Pointer sync.

## STATUS
This document is a project-level debugging and execution-safety gate. It does not by itself promote Active Engine, Production, DB, Formal count, or R140.
