# R70 Stage B R2 — Live Validity PASS / Coordinator Mapping Custody Failure R1

Date: 2026-09-22

Status:
`R70_STAGE_B_R2_LIVE_VALIDITY_PASS__MAPPING_CUSTODY_FAILURE__NO_FORMAL_QUALITY_VERDICT__NO_PROMOTION`

## Live execution evidence
Developer handoff reports:
- real API calls: 24
- retries: 0
- HTTP 200: 24/24
- valid arms: 24/24
- valid pairs: 12/12
- execution bundle: PREAPI_VALIDATED R2
- bundle SHA256: `cfd1541e3eb533af209ecd1254eacf21896b3564b6f3b1a3d44ca10dd67f2503`
- frozen R2 runtime SHA256: `34476d35f365a27e7e8e773b05c2951c4febc72bde8104e29f68e1e6d754d31d`

This establishes the R2 live-provider validity boundary only.
It does NOT establish F08 surface-effect quality PASS or Level-3 restoration.

## Missing coordinator mapping
Expected original R2 hidden-mapping SHA256:
`c3340b146c3901b4e652b2b947ae76eb9a846fcbaad21a2bd17dda6b0e9cec17`

Known balance:
- Treatment=A: 6
- Treatment=B: 6

The original R2 mapping bytes are not currently available.

## Recovery investigation
The following were checked:

1. Current R70 R2 work directories:
   - no standalone mapping/coordinator/secret file.

2. PREAPI virtual work directories:
   - no standalone R2 mapping/coordinator/secret file.

3. SYNC-R68 C2:
   - C2-A+B reconstructed successfully;
   - reconstructed C2 SHA256 exactly:
     `eefd5b853ff8957925d924573c1f0531506668c27b7e4c8438104ce60779dbea`;
   - R70 R2 live bundle and virtual evidence are present;
   - R2 original hidden mapping is not present.

4. PREAPI_VALIDATED R2 execution bundle:
   - fresh inputs present;
   - paired payloads present;
   - runtime present;
   - execution seal present;
   - original hidden mapping intentionally absent.

5. Project/Library search:
   - only reports containing the committed mapping SHA were found;
   - no original mapping bytes, filename/schema/serialization or generator output was recovered.

6. GitHub:
   - public/current Hub preserves the SHA commitment and custody statements;
   - no R2 original mapping file was found.

7. Current /mnt/data:
   - all files <=2 MiB were exhaustively SHA256-compared against the target;
   - 73 small files checked;
   - exact target match: 0.

8. R1 coordinator secret:
   - exact R1 mapping is available and SHA-valid;
   - it is a prior R1 artifact and MUST NOT be reused for R2.

9. Hash-guided reconstruction:
   - the known R1 serialization family plus balanced R2 assignments did not reproduce the target R2 hash;
   - no uncommitted substitute mapping may be created.

## Root cause
The R2 mapping was sealed by hash and deliberately excluded from judge/live execution bundles, but the coordinator-private original bytes were not included in the durable custody chain that later became SYNC-R68 / Hub / Library.

Classification:
`COORDINATOR_SECRET_CUSTODY_BREAK`

This is an evidence-custody failure, not a provider-generation failure.

## Scientific consequence
Do NOT:
- invent a new mapping;
- reuse the R1 mapping;
- infer Treatment identity from output style;
- use auxiliary unblinded judgments as formal R2 evidence;
- claim the quality gate passed or failed;
- rerun the 24 live generations merely to replace the missing mapping;
- promote R70.

Formal R2 quality adjudication remains unavailable until the byte-identical original mapping is recovered.

## Current authority
- Physical Authority: **SYNC-R68**
- Active Qualified Candidate: **R69/R68/R67/R66 lineage**
- Production: **ENG:R47 / LEGACY_R53**
- R70 Stage A: PASS
- R70 Stage B R1: VALIDITY HOLD
- R70 Stage B R2 live provider validity: PASS 12/12 valid pairs
- R70 Stage B R2 formal literary quality: HOLD — MAPPING CUSTODY FAILURE

## Successor rule
If the exact original mapping is later recovered:
1. verify SHA256 equals the frozen target;
2. do not reveal it to judges;
3. create/seal J01/J02/J03 blind packets from the already-sealed 12 valid pairs;
4. seal all 3 judgments;
5. reveal mapping only after judgments;
6. apply the unchanged gate.

If the original mapping cannot be recovered, R70 R2 must remain an immutable validity-PASS / quality-unadjudicated experiment. Any new quality estimate must be a separately preregistered successor experiment with a newly sealed coordinator secret before outputs.

Status token:
`R70_R2_24_LIVE_CALLS__24_24_VALID_ARMS__12_12_VALID_PAIRS__ORIGINAL_MAPPING_BYTES_MISSING__FORMAL_QUALITY_HOLD__NO_PROMOTION`
