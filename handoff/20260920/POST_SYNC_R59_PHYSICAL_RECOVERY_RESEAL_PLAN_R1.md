# POST-SYNC-R59 PHYSICAL RECOVERY & RESEAL PLAN R1

Date: 2026-09-20
Status: `RECOVERY_PLAN_SEALED__CURRENT_CONTAINER_TRANSPORT_HOLD`

## Recovery objective

The developer's **last complete physical package set is SYNC-R59**.

A new session must therefore reconstruct from SYNC-R59 physical bytes, then apply the post-physical Hub Overlay that closed R62 as FAIL.

Do NOT start by pretending SYNC-R58 is the last physical package.
Do NOT discard SYNC-R59.
Do NOT treat SYNC-R59's executable Candidate as qualified.

The two axes are:

- Physical custody baseline: **SYNC-R59**
- Active qualified Candidate logic: **SYNC-R58 / ADAPTIVE_UL16**

## SYNC-R59 5 Parts / 9 Packages — recovery hashes

Mandatory read order:
`CONTROL -> A -> B1 -> B2 -> C1 -> C2-A -> C2-B -> D1 -> D2`

1. CONTROL
   - SHA256:
     `15a93e22943da557c12ba17c61301526806328df92593a83bfe9b943161e4b44`

2. Part A
   - SHA256:
     `f904affeac55ed64e110c3abf300c427b82da3d00e1324c13d882a766dedbbbf`

3. Part B1
   - byte-unchanged from prior authority
   - SHA256:
     `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`

4. Part B2 — corrected delivery transport R2
   - SHA256:
     `753db03b5c161d3c016ef95388f93e2dfe2c469d2e1eb6182429b3d16cd549e6`
   - bytes: 268,276,811
   - logical content identical to pre-correction B2
   - superseded pre-correction SHA:
     `9d9c878cc3c794740b8b0fe4c6a13f6c5fa46c6a1e6b33e7f3631679dfdee0bf`

5. Part C1
   - SHA256:
     `a2acd64e682f92082fe28868fcd6d9603901e88413d89f6cc8eac0fecee0acf8`

6. Part C2-A
   - SHA256:
     `e8c15eaaded0cf49781d8471527a9343fa85d68a7adc4aaee8f6984a8b8d4eaa`

7. Part C2-B
   - SHA256:
     `bce2bae57de48383715195427a3ca5cd476c014517760835c536553336546ee2`

8. Part D1
   - byte-unchanged DB59
   - SHA256:
     `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`

9. Part D2
   - byte-unchanged DB59
   - SHA256:
     `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

## SYNC-R59 internal bindings

Integrated runtime SHA256:
`a6a0e65460948562c2cd7146efcb207a6b02ff77403f67a6bf9049792d95d625`

Candidate overlay SHA256:
`059e10a3b2cb71acf3db8144240ebfebeeac6924daf13fdb2d1858f1a3369e41`

R62 adaptive source SHA256:
`7c150389a688b4d769b96ade341921a77b7fe86289645c0c613a035c6151a377`

C2 logical SHA256:
`ae4fbfbb53c51157890ce45c1f9bf3f5671be4f60e5eed688e5e1f7dc9f95741`

DB59 SHA256:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

## Parent qualified SYNC-R58 bindings

Active qualified runtime SHA256:
`30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`

Active qualified Candidate overlay SHA256:
`d4215a8a5075054a054d5ca60e10e5992c4139588cccaeb0dabe14281f2fd633`

R58 adaptive source SHA256:
`42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

## What changed AFTER the SYNC-R59 package bytes were created

No new Candidate runtime source bytes were accepted after SYNC-R59 physicalization.

The post-SYNC-R59 delta is research/authority metadata:

1. R62 external blind judgments J01/J02/J03 were received.
2. R62 frozen gate was computed.
3. R62 closed FAIL at 9W / 0T / 3L.
4. Three semantic applicability failures were identified:
   - C06_FACTORY_STRIKE
   - C08_MOUNTAIN_RESCUE
   - C11_MUSEUM_THEFT
5. SYNC-R59 was reclassified:
   `QUARANTINED_FAILED_RESEARCH_SNAPSHOT`
6. Active qualified Candidate remained/reverted to:
   `SYNC-R58 / ADAPTIVE_UL16`
7. Next research target became:
   `R63 = F01 Semantic Applicability + Abstention Gate`
8. Container execution entered repeated TransportTimeout, preventing a new physical reseal.

Therefore:
`POST_SYNC_R59_RUNTIME_BYTE_DELTA = NONE`
`POST_SYNC_R59_RESEARCH_AUTHORITY_DELTA = YES`

## New-session recovery sequence

### Phase 0 — health
Before large I/O:
1. test minimal command execution;
2. test /mnt/data read/write;
3. test temporary file creation;
4. inspect cgroup memory counters if available.

If minimal commands fail:
`RUNTIME_TRANSPORT_HOLD`
Do not begin physical reconstruction.

### Phase 1 — verify SYNC-R59
1. ingest all 9 developer-held packages;
2. verify all 9 transport SHA256 values above;
3. verify B2 uses corrected R2 SHA, not superseded SHA;
4. ZIP/CRC audit all ZIP transports;
5. check duplicate/unsafe/encrypted entries;
6. reassemble C2-A + C2-B;
7. verify C2 logical SHA;
8. locate and verify:
   - integrated runtime;
   - R62 Candidate overlay;
   - R62 adaptive source;
   - DB59.

Any mismatch:
`AUTHORITY_BYTES_UNAVAILABLE_HOLD`

### Phase 2 — apply Hub Overlay
Load, in order:
1. `handoff/20260920/SESSION_R59_R62_RESEARCH_EXPERIMENT_LEDGER_R1.md`
2. `handoff/20260920/R62_EXTERNAL_JUDGE_CUSTODY_RESULT_MATRIX_R1.md`
3. `research/interventions/20260920/R62_F01_STAGE_GRAMMAR_DIVERSIFICATION_EXTERNAL_BLIND_RESULT_R1.md`
4. current authority/handoff/recovery/next pointers.

Set:
- last physical baseline = SYNC-R59
- SYNC-R59 scientific status = QUARANTINED
- active qualified Candidate = SYNC-R58
- R63 = NOT_STARTED / NEXT

Do not mutate judge results.

### Phase 3 — create a recovery-alignment physical successor BEFORE new research
Before R63 code changes, physically align the package set to the post-R62 authority state.

The successor ID is **not assigned in this document**. Assign the next SYNC ID only when actual reseal begins.

Required package semantics:

#### CONTROL
Add:
- new START HERE
- session research ledger R59-R62
- R62 final external-blind result
- R62 judge custody matrix
- quarantine decision
- active-qualified-vs-last-physical distinction
- runtime incident
- exact next research pointer

#### Part A
Add:
- R59 result
- R60 result and ledger references
- R61 causal map
- R62 prereg / implementation result / final blind result
- R62 failure analysis
- next R63 hypothesis

#### Part B1
Expected byte-unchanged unless an actual dependency audit proves otherwise.

#### Part B2
Add the current handoff/recovery research metadata.
Preserve logical content.
Keep transport under the attachment boundary.

#### Part C1
This is the most important authority decision.

A recovery-alignment successor must not silently execute the failed R62 Candidate as current qualified runtime.

Preferred representation:
- active runtime binding = exact qualified SYNC-R58 runtime;
- preserve SYNC-R59/R62 runtime + overlay + source under explicit quarantined research-evidence paths;
- no silent deletion of failed research bytes.

The exact container paths must be documented in the successor manifest.

#### Part C2-A / C2-B
Rebuild from the recovery-aligned C2 logical archive.
Verify:
- active runtime binding points to exact SYNC-R58 bytes;
- quarantined SYNC-R59/R62 evidence remains present but non-active;
- C2 logical SHA newly sealed;
- split SHA values newly sealed.

#### Part D1 / D2
DB59 remains byte-unchanged unless a real dependency audit proves otherwise.

### Phase 4 — physical audit
Require:
- 9/9 transport hashes
- ZIP CRC PASS
- C2 logical reassembly PASS
- active runtime SHA exactly SYNC-R58
- quarantined R62 evidence present
- DB59 exact hash
- no secret/API key leakage
- manifest/trust-root consistency
- developer downloadability check, especially B2 < 256 MiB attachment threshold.

### Phase 5 — deliver 5 Parts / 9 Packages
Only after Phase 4 PASS:
- declare the new recovery-alignment physical authority;
- provide all 9 package download links to developer;
- update Hub pointers to the new physical authority.

### Phase 6 — only then begin R63
R63 is not yet started.

R63 Control:
exact qualified SYNC-R58 behavior.

R63 Treatment lineage:
may reuse the quarantined R62 diversification implementation as research source, but only under a new preregistered applicability/abstention repair.
It must not inherit R62 qualification.

## Why this order matters

The developer currently owns SYNC-R59 physically.
The Hub owns the post-package scientific verdict.

Recovery is therefore:

`SYNC-R59 PHYSICAL BYTES`
+
`POST-R59 HUB RESEARCH/AUTHORITY OVERLAY`
->
`RECOVERY-ALIGNED 9-PACKAGE SUCCESSOR`
->
`R63`

not:

`pretend last physical set was SYNC-R58`

and not:

`continue R63 while current physical package metadata still says R62 external blind pending`.

## Current blocker
Current session container status:
`RUNTIME_TRANSPORT_HOLD`

This plan is intentionally written so a fresh healthy session can perform the physical rebuild without relying on current-session memory.

Status token:
`POST_SYNC_R59_RECOVERY_PLAN_R1__R59_LAST_PHYSICAL__POST_R59_RUNTIME_DELTA_NONE__R62_FAIL_OVERLAY_REQUIRED__ALIGN_PACKAGES_BEFORE_R63`
