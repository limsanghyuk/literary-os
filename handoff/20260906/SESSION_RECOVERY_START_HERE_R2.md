# Literary OS — Session Recovery START HERE R2
Date: 2026-09-06
Purpose: exact recovery authority for a new ChatGPT/developer session when current binary package reseal is blocked by infrastructure.
Supersedes: `SESSION_RECOVERY_START_HERE_R1.md` for current status.

## 0. Current status at a glance
- Formal scored count: **137**
- Latest formal scored authority: **R138**
- R140: **0 attempts / 0 outputs / 0 scores**
- ENG:R47 Production: **immutable**
- P07: **active preformal / not complete**
- DB59 frozen SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- RFV3 A/B/C/D: **preregistered, no generation outputs yet**
- Local artifact/container backend: **ClientError / Infrastructure HOLD**
- Current repaired 5-Part / 9-Package physical reseal: **NOT COMPLETED**
- CP1 current-authority restoration: **OPEN**
- R140: **HARD BLOCK**

## 1. Read these authorities in order
1. `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`
2. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
3. `handoff/20260906/DEVELOPER_HUB_AUTHORITY_SNAPSHOT_R1.md`
   - commit `934e10d4dd2deeed5ffcd34f5c543e4e93307e99`
4. `handoff/20260906/CLAUDE_CT_DEFECT_CLOSURE_MATRIX_R1.md`
   - commit `62b64b37196ee2c40b8c89d945a43030a2df86f2`
5. `handoff/20260906/P07_RFV3_ABCD_CAUSAL_REPRETEST_PREREG_R1.md`
   - commit `07c256a84718c0b8f4017c383c174c4bcf3a8d95`
6. `handoff/20260906/RFV3_TASK01_PREREG_AND_9PACKAGE_ATOMIC_CHECKPOINT_R1.md`
   - commit `a1e6ca0e2f84eedef3ae4ce188cecf5dc3857079`

## 2. Scientific correction that must not be lost
Previous runtime/module coverage was overinterpreted as DB adoption completeness. Claude/CT showed that DB59 retrieval repeatedly produced `NO_RETRIEVAL`; DB bytes could be read and hashed without donor semantic content reaching the LLM.

Current adoption standard:
`Value change -> Consumer receives -> selected donor/semantic payload changes -> LLM provider input changes -> downstream behavior changes -> Receipt/Trace proves it.`

The previous DB-adoption-completeness claim is withdrawn. Previous RFV provider-boundary mock/local evidence remains valid only within its engineering claim boundary.

## 3. Claude/CT defect closure summary
### Working-state repair observed, but package reseal/fresh byte verification still pending
- DB59 actual retrieval and semantic donor propagation;
- archive-to-retrieval-to-`SEQUENCE_PLAN` positive path;
- selected donor mutation changes semantic input;
- irrelevant unselected donor mutation does not;
- actual verified archive path rewired to repaired retrieval;
- bounded functional work-profile retrieval;
- diagnostic confidence/margin separated from literary semantic payload;
- Frozen Retrieval Index equivalence/tamper behavior;
- nonhistorical regression observed at 185/185.

Observed recovery values to reverify from exact bytes:
- actual retrieval source: 1,097 THICK members / 10,784 records;
- six development cases: `USE_RETRIEVAL` observed;
- Frozen Retrieval Index SHA256: `d9b50787676aa0750ba0b519b2537dedafa71807c72edef78c659ddfb6ddf419`;
- index equivalence/tamper audit SHA256: `81ca599ead072c7da9291450573b5a2c782d14d2b3b5514e5a7b3265b155fd23`;
- CASE-01 propagation evidence SHA256: `ab60a39cc9ce8fe30835b7b3589566f7a2281af6c49957048eb2268531d95f4f`.

### Still open
- current-authority CP1 paired runner restoration/integration;
- current-authority CP1 TestDouble validation;
- official R-F paired OpenAI CP1 live execution;
- physical 5-Part / 9-Package reseal with all repaired bytes;
- fresh regression/retrieval/equivalence/tamper verification from those exact package bytes;
- legacy dual-entrypoint drift cleanup;
- blind-secret physical separation before Formal R140.

Therefore Claude/CT defects are **NOT all closed**.

## 4. Current RFV3 preregistered A/B/C/D experiment
A = SUMMARY ONLY
B = PRE-REPAIR ENGINE / NO_RETRIEVAL
C = RFV2 REPAIRED ENGINE / DB59 USE_RETRIEVAL
D = FULL CURRENT CANDIDATE + BIDIRECTIONAL REFINEMENT

Purpose:
- A vs B: runtime information preservation/loss;
- B vs C: incremental DB59 retrieval value;
- C vs D: incremental bidirectional-refinement value.

No RFV3 generation outputs exist at this authority checkpoint.
Do not begin generation until pending package propagation is resolved or a newer checkpoint explicitly records why infrastructure still prevents it.

## 5. Canonical package structure
Exactly 5 Parts / 9 Packages:
1. CONTROL
2. PART-A
3. PART-B1
4. PART-B2
5. PART-C1
6. PART-C2-A
7. PART-C2-B
8. PART-D1
9. PART-D2

PART-C is exactly C1 + C2-A + C2-B.
C2-A || C2-B must reconstruct the declared C2 authority byte-for-byte.

The hashes in `DEVELOPER_HUB_AUTHORITY_SNAPSHOT_R1.md` are **PREVIOUS_PHYSICAL_BASELINE** only. They do not certify the current RFV2/RFV3 repaired authority.

## 6. Container/infrastructure rule
If minimal container health commands fail with `ClientError`:
- classify Infrastructure HOLD, not experiment FAIL;
- do not fabricate binary package SHAs;
- do not claim 9-package physical closure;
- do not advance Formal count;
- update recovery/developer hub checkpoints externally;
- package rebuilding/auditing is the first action after recovery.

## 7. Mandatory first actions after infrastructure recovery
1. minimal health check;
2. verify/recover exact repaired RFV2 source bytes and all amendments/checkpoints;
3. recover the previous physical 9-package baseline;
4. propagate every repaired-state code/doc/evidence change into the 9 packages;
5. regenerate Manifest and Trust Root;
6. verify per-package SHA256, ZIP CRC, duplicate paths, unsafe paths, nested ZIPs, C2 reassembly, DB59 authority, and no secrets;
7. fresh-run DB59 six-case retrieval audit;
8. fresh-run direct-vs-index equivalence/tamper audit;
9. fresh-run selected/unselected donor dependency tests and complete nonhistorical regression;
10. restore/integrate current-authority CP1 paired runner;
11. run CP1 TestDouble/fail-closed suite;
12. if CP1 changes bytes, immediately reseal/audit the 9 packages again;
13. only then execute official R-F real OpenAI paired CP1;
14. R-F closure -> R-G Freeze -> fresh formal sample -> revised R140 preregistration -> new G0 -> Formal R140.

## 8. Supporting CT evidence for a new session
If available, upload:
- `CT_TO_GPT_ADDENDUM7_C2R39_VERIFICATION_AND_DEFECT_RECOMMENDATION_20260906.zip`
- `CT_TO_GPT_회신_부록7_C2R39검증_결함권고_20260906.md`
- `A E.zip`

Treat CT-17 as nonformal pre-repair Live baseline only after file-level verification. It is not official CP1 and not Formal R140.

## 9. Closure rule from now on
Every meaningful task must close as:
`Preregister/Checkpoint -> Execute -> Verify -> Seal Result -> Propagate to 9 Packages -> SHA/CRC/Manifest/Trust Root Audit -> Update Developer Hub + Recovery Pointer -> Developer Delivery`.

If binary propagation is impossible, the task remains physically OPEN/HOLD even if engineering observations exist.

## 10. Current final status tokens
`FORMAL_COUNT_137`
`R140_0_ATTEMPTS_0_OUTPUTS_0_SCORES`
`RFV3_TASK01_PREREGISTERED`
`RFV3_GENERATION_NOT_STARTED`
`RFV2_REPAIRED_STATE_OBSERVED_REVERIFY_FROM_BYTES_REQUIRED`
`CLAUDE_CT_DEFECTS_PARTIALLY_REPAIRED_NOT_FULLY_CLOSED`
`CP1_CURRENT_AUTHORITY_RESTORATION_OPEN`
`9_PACKAGE_RESEAL_PENDING_INFRASTRUCTURE`
`R140_HARD_BLOCK`