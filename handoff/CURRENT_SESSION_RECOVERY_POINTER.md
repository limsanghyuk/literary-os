# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-15

## READ FIRST
Canonical recovery bootstrap:

`handoff/20260915/START_HERE_SYNC_R43_E1_CLOSED_E3_PREREG_R1.md`

Machine-readable current status:

`handoff/20260915/SYNC_R43_CURRENT_STATUS_R1.json`

Research evolution map:

`handoff/20260915/RESEARCH_EVOLUTION_MAP_R1.json`

Level-3 gate ledger:

`handoff/20260915/LEVEL3_ENTRY_GATE_LEDGER_R2.json`

Experiment preservation schema:

`research/20260915/EXPERIMENT_RECORD_SCHEMA_R1.md`

## PHYSICAL BASE
Last audited physical authority: **SYNC-R43**

Root SHA256:
`2722a2483d6f6417bc0de84f8d2a67fe6863d93b9c7adbef75c66bb027cd4912`

Parent authority: **SYNC-R42**

Parent root SHA256:
`921d97529a6d0c9741968b305eba18d7d1a241702a75cc036a5bca9316f2d4ef`

Required physical read order:
`CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2`

## MATURITY
`PRE_LEVEL_3__LEVEL_3_ENTRY_QUALIFICATION_IN_PROGRESS`

Level 3 has not been entered. Level 4 has not begun.

## E2
`CLOSED_PASS`
- canonical A2R35: PASS `10W/2T/0L`
- DB64 remains non-Production.

## E1
`CLOSED_PASS`
Experiment:
`P07-LEVEL3-E1-R2-FRESH-SURFACE-FORMAT-CLOSURE`

Primary panel:
- J01 GPT: Candidate `9W/1T/2L`
- J02 Claude: Candidate `11W/0T/1L`
- J03 Claude: Candidate `10W/1T/1L`
- Majority: Candidate `11W/0T/1L`
- Individual judge gates: `3/3 PASS`
- Verified Candidate critical violations: `0`

Auxiliary replication:
- GPT-family majority: `9W/1T/2L`
- Claude-family majority: `11W/0T/1L`

E1R2U08 contains one localized abstract clause. It is preserved as `MINOR_SURFACE_HYGIENE_DEFECT__NOT_VERIFIED_CRITICAL`; Candidate/judgment bytes and thresholds were not changed.

Canonical E1 closure:
`research/20260915/E1_R2_IMMUTABLE_CLOSURE_R1.json`

## E3 CURRENT STATE
Experiment:
`P07-LEVEL3-E3-FRESH-WHOLE-EPISODE-INTEGRATION-R1`

State:
`PREREGISTERED__FROZEN_INPUTS_SEALED__OUTPUTS_0`

Fresh synthetic series seed:
`해람시 긴급주거팀`

Sample instance:
- 1 episode
- 10 sequences
- 50 scenes
- >=35,000 Korean characters

These counts are experiment-sample values, not global fixed maxima.

Surface contract inherits E1:
- `(씬 설정: ...)`
- `등장인물명: (연기 가능한 지문) 대사`
- optional `(지문: ...)`
- explanatory dialogue prohibited
- abstract internal-state narration prohibited when an observable performance/action can carry the beat

E3 preregistration:
`research/20260915/E3_PREREGISTRATION_R1.json`

## RESEARCH-HISTORY RECOVERY RULE
A new session must reconstruct not only current state but evolution.
Read:
1. CURRENT_SESSION_RECOVERY_POINTER
2. current START_HERE
3. RESEARCH_EVOLUTION_MAP_R1
4. LEVEL3_ENTRY_GATE_LEDGER_R2
5. relevant individual Experiment Record / closure / preregistration
6. deeper B-package evidence when historical detail is needed

Do not erase FAIL, SUPERSEDED, HOLD, ABORTED_NOT_SCORED, infrastructure incidents, duplicate-branch quarantines, or claim boundaries.

## EXACT RESUME RULE
Do not regenerate E1.
Do not modify E1/E2 thresholds or evidence.
Do not change E3 frozen seed, surface contract or gates after output begins.

Next legal actions only:
1. execute E3 Episode Plan;
2. seal 10 Sequence Plans;
3. seal 50 Scene Contracts;
4. realize >=35,000-character broadcast episode;
5. run mechanical / semantic-continuity / surface-hygiene / state-delta validators;
6. State Commit only if all critical gates pass, otherwise Safe No-Commit;
7. immutable-close E3;
8. if PASS, proceed to E4 >=3 Episode State Carry.

## UNCHANGED SYSTEM AUTHORITIES
- Active Engine: `P07-I4H Recovery R3`
- Production: `ENG:R47`
- Formal scored total: `137`
- Latest Formal: `R138`
- Formal R140: `0/0/0`
- DB59 historical benchmark unchanged
- DB64 remains non-Production

## STATUS TOKEN
`SYNC_R43__E1_CLOSED_PASS__E2_CLOSED_PASS__E3_PREREGISTERED_FROZEN_INPUTS_OUTPUTS0__LEVEL3_NOT_ENTERED__NEXT_E3_EXECUTION`
