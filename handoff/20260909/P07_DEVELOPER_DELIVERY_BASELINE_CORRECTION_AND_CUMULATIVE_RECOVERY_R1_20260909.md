# P07 Developer-Delivery Baseline Correction & Cumulative Recovery R1

Date: 2026-09-09
Classification: AUTHORITY CORRECTION / CUMULATIVE RECOVERY

## 1. Correction
The developer has NOT received any complete replacement 5-Part / 9-Package set produced during this section after the initial uploaded package set.

Therefore the last actual **developer-held physical package authority** is the package set supplied by the developer at the beginning of this section:

`LITERARY_OS_SYNC_R6_I4H_VIRTUAL_PRETEST_20260908`

Logical structure: 5 Parts / 9 transport files.

The historical Sync R7 and Sync R8 package labels produced inside this ChatGPT session are **session-internal packaging/reconstruction checkpoints**. They were not handed back to the developer as all nine transport files and therefore MUST NOT be described as developer-held physical authority.

## 2. Exact developer-held physical baseline
Source authority document:
`handoff/20260908/START_HERE_P07_SYNC_R6_PHYSICAL_AUTHORITY_NEW_SESSION_HANDOFF_R1.md`

The nine developer-held parent files and expected SHA256 values are:

1. CONTROL `LITERARY_OS_CURRENT_CONTROL_P07_I4H_VIRTUAL_PRETEST_SYNC_R6_20260908.zip`
   `c291e9a3866de66fae625ab899139a13f1e98468a3bff0d58a11fd34553f0aa6`
2. PART A `LITERARY_OS_CURRENT_PART_A_P07_I4H_VIRTUAL_PRETEST_SYNC_R6_20260908.zip`
   `25eb489d07e78a3a3288e1e5029114ce791ada2ab43a8564ae9f9eed738306dd`
3. PART B1 `LITERARY_OS_CURRENT_PART_B1_UNCHANGED_R1_20260908.zip`
   `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
4. PART B2 `LITERARY_OS_CURRENT_PART_B2_P07_I4H_VIRTUAL_PRETEST_SYNC_R6_20260908.zip`
   `40de0853fd8e1e8318658d64a4e8d26cb8e88711842639aa45b87c0e4d062c02`
5. PART C1 `LITERARY_OS_CURRENT_C1_RUNTIME_CORE_UNCHANGED_R1_20260908.zip`
   `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
6. PART C2-A `LITERARY_OS_CURRENT_C2_BINARY_A_P07_PHASE0_R3_I4H_VIRTUAL_SYNC_R6_20260908.bin`
   `b775bf65cba23ad5611b3383678765f88c1a444d25c4b49f7ccfb5a9d2438ec9`
7. PART C2-B `LITERARY_OS_CURRENT_C2_BINARY_B_P07_PHASE0_R3_I4H_VIRTUAL_SYNC_R6_20260908.bin`
   `be4af1ac97467e1f090c8cd0854e14df1ffef6699ed23b0a80014f55e197e860`
8. PART D1 `LITERARY_OS_CURRENT_PART_D1_DB59_UNCHANGED_R1_20260908.zip`
   `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
9. PART D2 `LITERARY_OS_CURRENT_PART_D2_DB59_UNCHANGED_R1_20260908.zip`
   `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Developer-held combined C2 baseline:
- bytes `318351029`
- entries `3765`
- SHA256 `9878aac8532e9f1eb6b16ef4c84bcfe6be90b58a49ecf0f6afaabe993fad3be7`
- CRC PASS

Developer-held physical active engine inside this baseline:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`

Production remains `ENG:R47`.
DB59 frozen SHA256 remains:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
Formal scored count remains `137`; latest formal authority `R138`; Formal R140 remains `0/0/0`.

## 3. Post-delivery work that IS durable on the Hub
The following work was performed after the developer-held Sync R6 baseline. It is durable on GitHub and may be cumulatively integrated into the next physical package set, but it does not become developer-held physical authority until all nine resulting files are delivered and audited.

### I4H prospective craft line
- R1: pre-generation source/input contamination HOLD; no valid craft output.
- R2: preselector control multiplicity / transport corruption HOLD; no valid selector/treatment/evaluation result.
- R3: stronger-virtual craft signal PASS; Method Audit Closure commit `17e33163a519edb68bcc80c4970ebb255d4b0c51`.
- R4: fresh source-free masked replication PASS; result commit `16773b5ad9a97ca709f0476d227c4a04fa60909d`.
  - 21 scenes = ABSTAIN7 / LOW7 / STANDARD7.
  - interventions: Treatment7 / Control0 / Tie7.
  - nonloss 100%; harmful 0%; overall mean delta +0.32699.
  - STANDARD 7/7 wins, mean +0.42699.
  - LOW relational-subtext 7/7 nonloss ties, all paired deltas positive, mean +0.227, voice loss 0.

### I4H Runtime Promotion Implementation / Qualification
Preregistration:
`ac7202ac7743252ac1bb8b0ac50cb84287b7dfcd`

Qualification result:
`8fa611b801118ecf2b703cf1f41288c6a7e84bcc`

Qualification evidence:
- new I4H tests 42/42 PASS;
- old targeted tests 26/26 PASS;
- full nonhistorical regression 255/255 PASS = parent 213 + new 42;
- parent I4D files 5/5 byte-identical;
- critical failure accepts 0;
- Python authors no literary prose.

Durable runtime source files are stored at:
- `handoff/20260909/P07_I4H_RUNTIME_PROMOTION_DELTA_R1/literary_os_runtime/i4h_intervention_policy.py`
- `handoff/20260909/P07_I4H_RUNTIME_PROMOTION_DELTA_R1/literary_os_runtime/i4h_runtime_renderer.py`
- `handoff/20260909/P07_I4H_RUNTIME_PROMOTION_DELTA_R1/literary_os_runtime/i4h_episode_render_wiring.py`

The qualification result also records the exact runtime/test content SHA256 values, including `tests/test_p07_i4h_runtime_promotion.py`.

Correct authority interpretation:
`P07-I4H = HUB-QUALIFIED NEXT-PHYSICAL-AUTHORITY CANDIDATE`, not yet developer-held physical authority.

### I4I whole-episode research unit
Preregistration commit:
`e4bb3a9571db87c7553b183c8a39c3bdb498a143`

Frozen common plan:
- Series State + Episode Synopsis `623a57f04684c3729b2a12e117db9fc8982c0bd2`
- 11-Sequence Plan `234cda5bca761002a6b4d01a988cb0ce345e2426`
- SC01-SC56 Scene Plan `72109d52d69ba5aacafde3e5a6e660bd587c45a1`
- Complete Plan Freeze Manifest `ba658c7ede8de40bac6e4aaabdc325115ce8a82e`
- Plan Freeze Checkpoint `b4ec59a91a894f05131a19167db49c41776cf3a3`

I4I exact state:
- source-free series/episode plan frozen;
- 11 sequences / 56 scenes;
- Control outputs 0;
- selector decisions 0;
- Treatment outputs 0;
- scores 0;
- no I4I PASS/HOLD/FAIL claim.

### Packaging/runtime blocker
Checkpoint commit:
`3e9ae77479b163d00dff2aa2084d45d59fdb2b56`

Both minimal container and Python filesystem packaging probes returned `ClientError`. No further research execution is allowed until the accumulated Hub state is physically synchronized.

## 4. Cumulative reconstruction rule — build directly from developer-held Sync R6
A fresh session MUST NOT require the developer to possess the session-internal Sync R7 or Sync R8 nine-file sets.

The next developer deliverable shall be built cumulatively from:
1. exact developer-held Sync R6 nine files listed in Section 2;
2. this GitHub Hub and all durable post-Sync-R6 evidence/code listed above;
3. a healthy writable runtime.

No previous chat text is required once this Hub is read.

The next package identifier remains planned as `Sync R9` to preserve internal research chronology, but its **physical parent input** is developer-held Sync R6 plus cumulative Hub deltas.

## 5. Required cumulative transport changes for next developer deliverable
Because post-Sync-R6 work includes both research evidence and a qualified I4H runtime implementation, the next physical package cannot use the earlier 'only CONTROL/A/B2 change' map.

The cumulative next package must change/rebuild:
- CONTROL — current authority/delivery/recovery metadata;
- PART A — cumulative R3/R4 + runtime qualification + I4I prereg/plan-freeze evidence;
- PART B2 — cumulative research/recovery/master evidence;
- PART C2-A / C2-B — rebuilt from the Sync R6 combined C2 with the qualified I4H runtime overlay, qualification evidence, test/pointer/closure metadata, then re-split into two transport binaries.

Must remain byte-identical to the developer-held Sync R6 baseline unless an audit finds a packaging-only manifest dependency requiring otherwise:
- PART B1;
- PART C1;
- PART D1;
- PART D2.

DB59 must remain byte-identical and reconstruct to the frozen SHA256 above.

C1 / parent I4D runtime core must remain unchanged.

## 6. Required physical-build procedure in a healthy runtime
1. Mount the exact developer-held Sync R6 9 files.
2. Verify all nine outer SHA256 values against Section 2.
3. Verify ZIP CRC, duplicate path = 0 and unsafe path = 0.
4. Rejoin developer-held C2-A+B and verify parent combined C2 SHA `9878aac...3be7`, bytes 318351029, entries 3765.
5. Recover the durable I4H runtime source/test/qualification artifacts from GitHub.
6. Build a new combined C2 as an append-only/additive overlay over the exact Sync R6 C2; do not mutate the five frozen parent I4D files.
7. Run the full I4H qualification/regression again in the rebuilt materialization. Required result: 42/42 new, 26/26 targeted, 255/255 full or higher with no new failures.
8. Split the rebuilt combined C2 into two transport parts and record fresh outer SHA256 values.
9. Build new CONTROL/A/B2 with cumulative post-Sync-R6 research and I4I plan-freeze evidence.
10. Copy B1/C1/D1/D2 byte-identically from the developer-held baseline.
11. Validate DB59 D1+D2 reconstruction against frozen SHA.
12. Audit all nine resulting files: outer SHA, CRC, duplicate=0, unsafe=0, internal manifests, C2 reconstruction, DB59 reconstruction.
13. Compute package-set material SHA256 and final physical-audit SHA256.
14. Only after all nine physical files exist and PASS, deliver all nine to the developer.
15. Only after developer delivery may Hub mark the new package and P07-I4H as developer-held physical authority.
16. Only then may I4I Control generation resume.

## 7. Claim boundary
Current developer-held physical authority remains Sync R6 / P07-I4D.

Supported Hub state:
- I4H craft research has R3/R4 PASS signals under stated Development/Preformal limits;
- I4H runtime implementation has passed the recorded qualification/regression in the session workspace and its source/evidence are durable on GitHub;
- I4I is preregistered and its 11/56 common plan is durable/frozen;
- cumulative reconstruction into the next physical 5-Part / 9-Package is possible from exact Sync R6 + Hub when a healthy runtime is available.

Not supported until physical rebuild and delivery:
- developer-held Sync R7 authority;
- developer-held Sync R8 authority;
- developer-held Active I4H physical authority;
- I4I execution/result;
- Production change;
- formal-count change;
- R140 start;
- OpenAI Live qualification.

## STATUS TOKEN
`DEVELOPER_HELD_PHYSICAL_BASELINE_SYNC_R6_I4D__POST_DELIVERY_I4H_R3_R4_AND_RUNTIME_QUAL_DURABLE_ON_HUB__I4H_NEXT_PHYSICAL_CANDIDATE__I4I_PLAN_11SEQ_56SCENE_FROZEN__CONTROL_0__CUMULATIVE_SYNC_R9_REBUILD_FROM_SYNC_R6_PLUS_HUB_REQUIRED__RESEARCH_FROZEN`
