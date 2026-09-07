# P07-I4E R1 Mode-Driven Whole-Episode Rerender — HOLD Result

Date: 2026-09-08
Classification: DEVELOPMENT / PREFORMAL / NO FORMAL COUNT DELTA
Parent authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`
Preregistration commit: `3569bca4d0a9874b6a28fb4ba3685ce71c47bae1`

## Pre-render gate
PASS before any treatment prose:
- 50/50 `LiterarySurfaceContractR1` validation;
- 50/50 play/voice principal completeness;
- 50/50 allowed mode selection;
- selected mode mutation changes provider-input hash;
- irrelevant metadata invariant;
- mode-selection SHA256 `21307a4ef5974c80e799349ac915f124c7fc500b4cb95067ff82ce337cd8b574`;
- Human anchors inspected: FALSE;
- treatment output count at pre-render gate: 0.

## Generation / repairs
First pass:
- 50 scenes / 24,645 Unicode chars;
- SHA256 `38be521f26c90c245e11c2d9a4217e3e36cd689b1e78bd9e0c97d4a6c9d0cb1e`;
- diagnostic `SURFACE_UNDER_REALIZATION`.

Repair cycle 1:
- targeted surface/action/subtext expansion;
- 50 scenes / 32,153 chars;
- SHA256 `a2a84ec79e13638f6304015605bef5bd8eefb2e318270e20abe3cef13f2f1103`.

Repair tooling note: the R1 repair assembler normalized trailing whitespace on protected scenes, contaminating byte-stability measurement even where prose content was unchanged. This is recorded as a tooling defect, not hidden.

Repair cycle 2 — final allowed cycle:
- 50 scenes / 35,018 chars;
- SHA256 `1228b2cd1c389706042b389c40ffb99212b6c2893a2de4a375ac23559a432a82`.

## Final mechanical result
PASS dimensions:
- scene count 50;
- 35k-45k broadcast length PASS;
- long dialogue duplicate ratio 0.0;
- long narrative duplicate ratio 0.0;
- procedural/control density 11.282 / 1,000 chars;
- mean non-empty line length 25.348 chars;
- forbidden engine/meta leakage 0;
- contract play/voice completeness 50/50;
- protagonist scene share 0.62;
- protagonist-group sequence ownership 0.50;
- non-protagonist-owned sequences 5;
- independent non-protagonist owner groups 2;
- source/future leakage 0.

Critical FAIL:
`DIRECT_SPEAKING_PRINCIPAL_OUTSIDE_SCENE_CONTRACT`

Five scenes contain 13 principal-speaker violations:
- S37: `오세미` direct speech although frozen scene contract principal set is 윤상철/강태욱;
- S46: `윤서진` direct speech in tenant-owned convergence contract;
- S47: `윤서진` direct speech;
- S48: `윤서진` and `최유경` direct speech;
- S49: `최유경` direct speech.

This reproduces the same class of failure previously discovered in I4C: whole-episode surface generation can widen direct-speaker scope beyond the consumed literary contract even when the contract set itself is complete.

## Verdict
Two preregistered repair cycles were exhausted before final audit. Therefore no additional prose correction is allowed in R1.

`HOLD_REDESIGN_REQUIRED__SPEAKER_AUTHORIZATION_AND_REPAIR_ASSEMBLER_GUARD_REQUIRED`

Consequences:
- Stage A blind NOT executed;
- Stage B human blind NOT executed;
- State Commit BLOCKED;
- canonical semantic carry remains `5a5a0511b726ce880d96bbd093faa73f95949e7afae49aea6cd0ca0308c24a7c`;
- no packaged promotion regression;
- no 5 Parts / 9 Packages reseal;
- P07-I4D remains Current Physical Authority;
- formal count delta 0;
- R140 delta 0.

## Next recovery requirement
A new separately preregistered recovery may proceed only if it prevents this failure *before* prose output by enforcing a direct-speaking-principal authorization guard at renderer/provider input and uses an exact-byte-preserving repair assembler. The recovery should surgically regenerate only the five failed scenes while keeping the other 45 final-R1 scenes byte-identical, then rerun the same whole-episode mechanical and blind gates without lowering thresholds.
