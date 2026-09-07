# P07-I4F Mode Selector / Abstention / Operator Intensity Probe — Preregistration R1

Date: 2026-09-08
Classification: DEVELOPMENT / PREFORMAL / NO FORMAL COUNT DELTA

## Parent authorities
Active engine authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`
Active C2 SHA256: `1022a4144e582069a3d6ed9d234f100d0b8a3a4323b73039d1454e57f89d75e1`
Cumulative physical research authority: `CURRENT_PHYSICAL_RESEARCH_AUTHORITY__P07_I4D_ACTIVE__I4C_I4E_EVIDENCE_SYNC_R1`
Frozen DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
Formal scored count: 137 unchanged.
R140: 0 attempts / 0 outputs / 0 scores — HARD BLOCK.
Real OpenAI Live evidence eligibility: FALSE.

## Problem diagnosis
P07-I4D proved targeted efficacy of `SurfaceRealizationModeR1`, but P07-I4E R2 failed whole-episode Stage A at Treatment 6 / Control 6 / Tie 0. The next bottleneck is not additional mode strength or lower thresholds. It is Mode Selector precision, abstention (`NONE`), and operator intensity.

Past I4D/I4E outcomes may be used only as retrospective development evidence to formulate the selector. They are NOT part of the prospective scored sample.

## Hypothesis
A selector that may abstain and choose mode intensity before prose generation can preserve already-strong scenes while applying mode operators only where their expected benefit exceeds over-constraint risk.

## Research questions
1. Can a frozen pre-output selector choose `NONE`, `MODE_LOW`, or `MODE_STANDARD` such that its chosen arm is blind-best/co-best on fresh scenes?
2. Does explicit abstention protect already-strong family/community/procedural-social scenes?
3. Does intensity calibration reduce the over-application failure observed in I4E without eliminating I4D's targeted gains?
4. Is the selector decision physically consumed by the renderer/provider literary payload while irrelevant metadata remains non-causal?

## Frozen prospective sample
These scenes were not part of prior I4D/I4E Stage-A/B scoring:
`S01 / S04 / S08 / S12 / S16 / S18 / S22 / S24 / S29 / S32 / S38 / S44`.

Known-strong protected sentinels, not included in the prospective score denominator:
`S07 / S11 / S14`.

## Frozen selector decisions — before any new prose
- S01 -> `DEADLINE_KINETICS / MODE_STANDARD`
- S04 -> `TEAM_EXECUTION / MODE_LOW`
- S08 -> `NONE`
- S12 -> `NONE`
- S16 -> `STATUS_DOMINANCE / MODE_LOW`
- S18 -> `NONE`
- S22 -> `REVEAL_REVERSAL / MODE_LOW`
- S24 -> `OCCUPATIONAL_EXECUTION / MODE_STANDARD`
- S29 -> `DEADLINE_KINETICS / MODE_LOW`
- S32 -> `NONE`
- S38 -> `URGENT_COMMAND_ACTION / MODE_STANDARD`
- S44 -> `DEADLINE_KINETICS / MODE_STANDARD`

Protected sentinels:
- S07 -> `NONE`
- S11 -> `NONE`
- S14 -> `NONE`

The decisions above are frozen before variant prose generation.

## Intensity semantics
`NONE`: no `SurfaceRealizationModeR1` payload. Existing `LiterarySurfaceContractR1` only.

`MODE_LOW`: same frozen mode family, but one primary craft operator plus at most one secondary operator; action-chain mandatory beats <=3; anti-exposition/compression remain active; no extra plot fact, speaker, relationship change, or semantic invariant may be added.

`MODE_STANDARD`: full existing P07-I4D `SurfaceRealizationModeR1` payload and constraints.

Python/runtime may create routing/validation/hashes and canonical payloads only. Python literary prose generation remains 0.

## Pre-output causal/adoption gate
Before prose generation:
- selector decision validates for 15/15 scenes;
- protected sentinels choose NONE 3/3;
- selected intensity changes provider literary payload hash when mode is selected;
- NONE produces no mode payload;
- irrelevant selector metadata does not change consumed literary payload hash;
- selected scene principal-speaker completeness and semantic-invariant binding PASS;
- Human Anchor inspected = FALSE.

Failure at this gate => HOLD, no prose output.

## Tri-arm generation
For each of the 12 prospective scenes only, create three semantically equivalent variants:
1. `NONE`
2. selected mode family at `MODE_LOW`
3. selected mode family at `MODE_STANDARD`

For scenes whose frozen selector decision is NONE, the same diagnostically nearest mode family may be used to generate LOW/STANDARD counterfactual arms, but the selector decision remains NONE and may not be changed after seeing prose.

All three arms must preserve:
- exact semantic invariants;
- allowed direct-principal speaker set;
- relationship/thread state;
- episode/sequence function;
- source/future cutoff.

## Protected-scene invariance gate
S07/S11/S14 are not re-rendered. Selector must abstain 3/3 and their existing sealed scene bytes remain byte-identical. Any mutation => FAIL.

## Mechanical gates
For every generated arm:
- unauthorized principal speaker = 0;
- critical semantic/continuity violation = 0;
- source/future leakage = 0;
- forbidden meta leakage = 0;
- long exact dialogue duplicate ratio = 0;
- long narrative duplicate ratio = 0;
- procedural/control vocabulary density must not increase >20% versus the same scene's NONE arm;
- no silent speaker-set expansion.

## Blind evaluation
Create anonymous tri-arm packets after all arms are sealed. Mapping is sealed separately. Judge may not open mapping before all 12 scene judgments are written and hashed.

Primary judgment per scene: rank/select `BEST`, permit `CO-BEST/TIE` where warranted. Craft criteria: dialogue naturalness, voice specificity, subtext/physicalization, scene action, information control, pacing/economy, relationship/status motion, scene turn, and carry-forward pressure. Structural semantic fidelity is non-compensatory.

## Preregistered pass gates
A. Protected abstention: S07/S11/S14 -> NONE 3/3 and byte-identical PASS.

B. Selector co-best accuracy: frozen selected arm must be blind-best or co-best on >=8/12 prospective scenes.

C. Catastrophic mis-selection: selected arm may be strictly worst on at most 1/12 scenes.

D. Selected MODE scenes (8 scenes): selected LOW/STANDARD arm vs NONE must be win or tie on >=6/8, with outright wins >=4/8.

E. Selected NONE scenes (S08/S12/S18/S32): NONE must be best/co-best on >=3/4.

F. Intensity calibration: on the 8 selected-MODE scenes, the frozen selected intensity must be win/tie versus the opposite intensity on >=6/8.

All A-F must PASS for selector promotion eligibility.

## Promotion rule
PASS permits promotion consideration only for selector/intensity contract, validator, canonical payload, and optional bridge/wiring. Literal treatment prose is research evidence only and may not be hardcoded.

Before physical promotion, full nonhistorical regression and exact packaged-C2 fresh-materialization regression must PASS. Any meaningful PASS/HOLD result must be synchronized back into the cumulative 5 Parts / 9 Packages research authority before a subsequent research unit starts.

## Claim boundary
This experiment cannot establish whole-episode human competitiveness, external human consensus, human-writer equivalence, real OpenAI Live parity, RFV3, CP1 Live, official R-F/R-G, Production promotion, or Formal R140 closure.
