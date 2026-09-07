# P07-I4C R1 Whole-Episode Rerender — HOLD Result

Date: 2026-09-08
Classification: DEVELOPMENT / PREFORMAL / NO FORMAL COUNT DELTA
Parent authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I4B_LITERARY_SURFACE_CONTRACT_R1`
Preregistration commit: `3a7fe485aa9a64eb54dec9d9f215ff9f0b2fd542`

## Verdict
`HOLD_REDESIGN_REQUIRED`

No Stage A blind, no Stage B blind, no State Commit, and no physical promotion were executed after the blocking defect was confirmed.

## Final sealed treatment before HOLD
- 50 scenes
- 35,454 Unicode characters
- SHA256 `c7865bfd3fe0c5925fcad429cf8c115f52fe689e6af7075db50bec75e4fe089e`
- repair cycles used: 2 / maximum 2
- exact long dialogue duplication: 0.0
- exact long narrative duplication: 0.0
- procedural/control vocabulary density: approximately 5.98 / 1,000 Unicode characters
- mean non-empty line length: approximately 25.78 Unicode characters
- protagonist scene share: 0.64
- protagonist-group sequence ownership: 0.50
- non-protagonist-owned sequences: 5
- non-protagonist owner groups: 2

## Repair minimality
Cycle 1 changed exactly:
`S03/S07/S08/S09/S18/S19/S28/S29/S38/S41`.

Cycle 2 changed exactly:
`S04/S09/S15/S17/S30/S31/S41/S42/S46/S47/S48/S49`.

Protected other scenes remained byte-stable across each cycle.

## Blocking defect
Whole-episode contract audit found one critical speaking-principal completeness failure:
- scene `S14`;
- speaker `박정숙`;
- `박정숙` speaks in the exact P07-I3 control and in the I4C final surface;
- but `S14.character_play_state` omitted `박정숙`.

This is not an unauthorized-surface-speaker invention: `박정숙` already existed and spoke in the frozen control. The failure is instead that the consumed `LiterarySurfaceContractR1` did not carry a required play-state record for an existing speaking principal.

Because `character_play_state` is part of the consumed literary provider payload, adding it after treatment sealing would create a new provider-input payload and would invalidate any claim that the existing 35,454-character surface was generated from that corrected contract.

The preregistered maximum of two repair cycles had already been exhausted. Therefore the threshold was not weakened and no third repair was performed.

## State rule
Final status is HOLD, so State Commit is prohibited.
The prior canonical semantic carry remains unchanged:
`5a5a0511b726ce880d96bbd093faa73f95949e7afae49aea6cd0ca0308c24a7c`.

No new canonical state carry is created from I4C R1.

## Blind rule
Stage A and Stage B were not executed because the mechanical/contract gate did not close. Their results therefore remain unknown rather than inferred from the text.

## Physical authority
No I4C R1 5 Parts / 9 Packages promotion is allowed.
Current Physical Authority remains P07-I4B.

## Root cause
`LiterarySurfaceContractR1` validation checked required top-level fields and semantic invariant binding, but did not enforce **speaking-principal completeness**: every frozen/allowed direct-speaking principal in the Scene Plan must have corresponding `character_play_state` and `voice_state` entries before provider input can be accepted.

## Required recovery
A new separately preregistered recovery experiment must add a pre-render fail-closed speaker-completeness guard before any new 50-scene treatment is generated. The guard must run before prose output, not after it. No R1 blind result may be reused because R1 blind was never executed.

Formal scored count remains 137. R140 remains 0/0/0 HARD BLOCK. Real OpenAI Live evidence eligibility remains FALSE.