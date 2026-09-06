# RFV3 Task 01 — Preregistration / Atomic 5-Part 9-Package Checkpoint R1
Date: 2026-09-06

Status: `RFV3_TASK01_PREREGISTERED__LOCAL_ARTIFACT_BACKEND_HOLD__9_PACKAGE_RESEAL_PENDING_INFRASTRUCTURE`

## Scientific state preserved
- Formal scored count: 137
- R140: 0 attempts / 0 outputs / 0 scores
- ENG:R47 immutable
- DB59 frozen SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- Previous RFV Provider-boundary evidence retained.
- Previous DB-adoption-completeness claim withdrawn.
- RFV2 repaired state to be reverified before RFV3 generation: actual DB59 1097 members / 10784 records; six development cases `USE_RETRIEVAL`; selected donor changes semantic input; irrelevant unselected donor does not; current nonhistorical regression previously observed 185/185.

## Task 01 output
New preregistration:
`handoff/20260906/P07_RFV3_ABCD_CAUSAL_REPRETEST_PREREG_R1.md`
GitHub commit: `07c256a84718c0b8f4017c383c174c4bcf3a8d95`

Frozen comparison:
A SUMMARY ONLY
B PRE-REPAIR ENGINE / NO_RETRIEVAL
C RFV2 REPAIRED ENGINE / DB59 USE_RETRIEVAL
D FULL CURRENT CANDIDATE + BIDIRECTIONAL REFINEMENT

## Mandatory 5-Part / 9-Package authority structure
1 CONTROL
2 A
3 B1
4 B2
5 C1
6 C2-A
7 C2-B
8 D1
9 D2

Every completed scientific task must propagate changed authority state into these nine packages before the following task is considered physically closed.

## Infrastructure interruption
At Task 01 close, the local artifact/container backend returned `ClientError` even for minimal health calls. This is Infrastructure UNKNOWN/HOLD, not experiment FAIL. Binary ZIP packages cannot be truthfully rebuilt or CRC-checked while the backend is unavailable.

Therefore:
- no package SHA is fabricated;
- no Current Pointer is advanced to claim physical 9-package closure;
- this GitHub checkpoint is the durable external recovery point;
- packaging is the first required action when the local artifact backend returns.

## Resume rule
1. Minimal health check.
2. Verify latest 9-package inputs and current RFV2 candidate bytes.
3. Materialize Task 01 preregistration into common authority roots.
4. Rebuild/refresh the canonical 5-part / 9-package set.
5. SHA256 + outer CRC + duplicate/unsafe path + nested ZIP audit.
6. Only after 9-package Task 01 physical closure, run RFV3 V1 A/B/C/D virtual semantic generation.

No formal output exists at this checkpoint.
