# Literary OS Session Recovery / Replay Map R1

Date: 2026-09-24

## Purpose
Guarantee that a fresh session can recover all post-SYNC-R72 research without re-running completed experiments even though a newer 5-Part / 9-transport physical reseal has not yet been possible.

## Recovery model

Recovery is two-layered:

1. PHYSICAL BASE
   - Current sealed physical authority: SYNC-R72
   - 5 logical Parts / 9 transport files
   - Must be treated as immutable until a newer reseal is physically produced and verified.

2. POST-R72 RESEARCH OVERLAY
   - Durable in Developer Hub/GitHub.
   - Contains all research, experiment evidence, closure reports, preregistrations, external judge results, and next-step handoff after SYNC-R72.
   - Must be loaded on top of SYNC-R72 for current research state.

A fresh session must NOT infer that post-R72 research is absent merely because the 9 packages are still SYNC-R72.

## Current authority snapshot

Physical Authority: SYNC-R72
Active Runtime: exact R69
Runtime SHA256: 3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1
Production: ENG:R47 / LEGACY_R53
Runtime DB: DB59 frozen
Research DB: DB64-R128 research-only
Operational Level-3: SUSPENDED__REQUALIFICATION_REQUIRED
Formal latest scored: R138
Formal R140: NOT_STARTED

## Mandatory first read

handoff/20260924/START_HERE_SYNC_R72_R76_CLOSED_R77_H0_PASS_H1_NEXT_R1.md

This document is the current research bootstrap. It explicitly states that Physical remains SYNC-R72 while research has advanced beyond it.

## Post-R72 research that is already completed and MUST NOT be re-run

### R74
Closed without canonical efficacy verdict.
F05 remains NOT QUALIFIED.
Do not restart unless exact canonical R127 raw bytes become available for a preregistration-faithful replay.

### R75
DB64-R128 causal schema consumption PARTIAL PASS.
Qualified populated channels:
- EVENT 16/16
- INFORMATION 16/16
- THREAD 15/15
- OWNER/CAST 16/16
Future leakage 0.
Unpopulated channels remain unqualified.

### R76
CLOSED PASS at virtual-provider broadcast-scale absolute-quality scope.
Work: SYNTH_R76_BREAKWATER_THEATER / 방파제 극장
Surface: 35,333 chars / 9 sequences / 52 scenes
Surface SHA256: 7b35fa2418f07382b52d5e93403e3da555539e1c96747cca98e3227e5c4c3ee4

External 3-Judge result:
- J01 PASS
- J02 PASS
- J03 PASS
- pooled whole median 8.5
- pooled scene median 8.0
- confirmed critical violation 0

Canonical evidence:
research/interventions/20260924/R76_VP_B1_EXTERNAL_3JUDGE_FINAL_RESULT_R1.json
research/interventions/20260924/R76_VP_B1_EXTERNAL_3JUDGE_ADJUDICATION_REPORT_R1.md

Do not modify the judged screenplay and do not repeat R76 as though it were unfinished.

### R77-H0
Human Next-Episode Prospective Benchmark infrastructure is already preregistered and qualified.

Canonical files:
research/interventions/20260924/R77_H0_HUMAN_NEXT_EPISODE_PROSPECTIVE_BENCHMARK_PREREGISTRATION_R1.json
research/interventions/20260924/R77_H0_TYPED_EPISODE_POSITION_CONTRACT_R1.json
research/interventions/20260924/R77_H0_PAST_ONLY_CUTOFF_CONTRACT_R1.json
research/interventions/20260924/R77_H0_INFRASTRUCTURE_QUALIFICATION_RESULT_R1.json

Qualification:
- clean-runner PASS 8/8
- workflow run 35996246377
- job 107621764169
- artifact 10806297408
- artifact ZIP SHA256 71922b98a56f429edb2b5b37cd207b05a3d98c5060a64141b8357b154e4af60d
- human target accessed = false
- primary human target outputs = 0

### R77-H1
Already preregistered.
Canonical file:
research/interventions/20260924/R77_H1_THREE_POSITION_PILOT_SELECTION_AND_CONTEXT_ISOLATION_PREREG_R1.json

Exact current point:
- eligible census = 0
- selected works = 0
- candidate plans = 0
- candidate surfaces = 0
- human targets revealed = 0

Therefore the next research action is H1 eligible-work census and Past-Only cutoff package construction.
Do not repeat H0.

## Physicalization status

Canonical hold receipt:
research/interventions/20260924/POST_R76_R77H0_PHYSICALIZATION_HOLD_R1.md

Reason:
SYNC-R72 package objects exist in Project Library, but the current Project file service does not expose an authorized raw-byte materialization path into the active container.

This is a custody/access failure, not package loss and not a research failure.

No fake package bytes were created.
No new package SHA was invented.
No SYNC-R73 physical authority is claimed.

## New session recovery procedure

1. Read this file.
2. Read the START_HERE handoff.
3. Load/verify the current SYNC-R72 9 transports if raw access is available.
4. Treat SYNC-R72 as the physical base only.
5. Load the post-R72 research overlay from the canonical Hub paths above.
6. Reconstruct current research state:
   - R74 closed/no efficacy verdict
   - R75 partial pass
   - R76 closed external 3-judge pass
   - R77-H0 pass
   - R77-H1 preregistered/not started
7. Resume from R77-H1 eligible census.
8. Never reveal Human target EP02/EP06/EP13 before C and T candidate plans, >=35k surfaces, output-only reconstructions, and state ledgers are sealed.
9. When raw package custody is restored, physicalize all overlay changes into a new 5-Part / 9-transport set.
10. Only after 9/9 size/SHA/CRC/direct redownload verification may a new physical SYNC authority replace SYNC-R72.

## Expected physical delta at next reseal

Update candidates:
- CONTROL
- A
- B2
- C1
- C2-A
- C2-B

Expected byte-unchanged candidates, subject to direct verification:
- B1
- D1
- D2

## Standalone-recovery risk

If a future session has:
- no access to the SYNC-R72 9 transport files AND
- no access to the Developer Hub/GitHub overlay,

then full continuation is not possible without re-supplying one of those sources.

But with either:
A. SYNC-R72 9 transports + Developer Hub access, or
B. a future newly resealed 9-package set containing the overlay,

the research can continue without repeating completed experiments.

## Developer portability rule

Until a newer physical reseal is produced, the Developer Hub is the durable authority for post-R72 research history and experiment evidence, while SYNC-R72 remains the durable authority for physical package bytes.

This split is intentional and must be preserved in every handoff until physicalization is completed.
