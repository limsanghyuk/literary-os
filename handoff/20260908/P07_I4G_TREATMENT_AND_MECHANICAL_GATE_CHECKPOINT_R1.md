# P07-I4G Treatment + Mechanical Gate — Checkpoint R1

Date: 2026-09-08
Classification: DEVELOPMENT PREFORMAL / INTERRUPTION-SAFE CHECKPOINT

Preregistration commit: `dff1c990d72eff1b8f8acf228d856aa212eebe64`.
Sample seal commit: `ae8ec6bc1bb6eb10f5eea96259809e3799a05f54`.
Pre-output gate commit: `c6ad1f137a78fa91868b3871803cb2964e6020f6`.

## Exact Treatment seal
Frozen scenes: `S02/S06/S09/S13/S17/S23/S26/S27/S31/S36/S42/S47`.
Treatment bundle SHA256: `f73b093fc7c37fa5dccee805fa2b091588e3cf421fd9c8e69ff9f55bb6d47f15`.
Treatment scene count: 12.
Total Treatment characters: 7,540.
Treatment is now locked; no further prose edits are permitted before or during Blind evaluation.
Human Anchor inspected: FALSE.

Generation seal file SHA256: `7267cacf0f3d0667e5c90b1c49347de7e79f3b999a903dc475110c8c631cbc64`.

## Mechanical gate — PASS
Final mechanical gate JSON SHA256:
`dc7cb01999ca0ee21f92a80e88d0bd88ae865ac1acb50073c5ae8e64473cbe1d`

PASS:
- unauthorized principal speaker = 0;
- critical semantic/continuity sentinel failures = 0;
- source/future leakage = 0;
- internal/meta leakage = 0;
- long exact duplicates = 0;
- malformed Korean sentinel hits = 0;
- non-playable psychological narration not worse than Control;
- explanatory-dialogue density lower than Control;
- playable/filmable direction coverage higher than Control.

Diagnostic metrics:
- explanatory-dialogue flagged rate: Control 0.12637 -> Treatment 0.00735;
- non-playable psychological narration rate: Control 0.04598 -> Treatment 0.0;
- playable-direction line coverage: Control 0.91954 -> Treatment 0.92818;
- direction character share: Control 0.46745 -> Treatment 0.67106.

Audit-note correction before final gate: initial speaker audit falsely parsed `02:13` as a speaker and treated S31 `주민` as a new principal. The final audit corrects the parser and applies the preregistered `unauthorized principal speaker` rule; the S31 local resident role already exists in the frozen Control scene. Treatment bytes were not changed.

## Next exact action
Build a 12-pair anonymous Control-vs-Treatment Stage-A blind packet. Seal left/right mapping separately. Write and hash all 12 judgments before mapping reveal.

Stage-A gate remains unchanged: Treatment wins >=8/12; losses <=3/12; win+tie >=10/12; no critical violation.

If interrupted, resume from this exact Treatment seal and mechanical gate. Do not regenerate or edit Treatment scenes.
