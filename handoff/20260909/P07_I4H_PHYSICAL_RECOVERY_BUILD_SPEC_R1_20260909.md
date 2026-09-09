# P07-I4H Physical Recovery Build Spec R1

Date: 2026-09-09
Classification: RECOVERY / PACKAGING SPECIFICATION / NO NEW RESEARCH EXECUTION

## 0. Purpose
This document freezes the exact recovery target requested by the developer after all nine Sync R6 transport files were supplied again in the current conversation.

Target scope is **research and engine recovery through P07-I4H only**. I4I remains a later preregistered/plan-frozen research unit and is not an I4H result.

No Production, formal-count, R140, OpenAI Live or human-equivalence claim is created by this recovery specification.

## 1. Logical 5-Part / physical 9-Package topology
The Literary OS delivery remains five logical Parts and nine physical transport files:

1. CONTROL -> CONTROL authority / current state / delivery manifests / handoff controls.
2. PART A -> experiment-control, preregistration, evaluation and research evidence layer.
3. PART B -> B1 + B2.
   - B1 = long-horizon Research History Recovery Vol.1.
   - B2 = current/cumulative Research Recovery Vol.2.
4. PART C -> C1 + C2.
   - C1 = stable Runtime Core / Production-lineage core.
   - C2 = development/candidate engine materialization.
   - physical C2 transport = C2-A || C2-B in that order only.
5. PART D -> D1 + D2 = DB59 two-volume physical transport.

Physical accounting:
`CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2 = 9`.

## 2. Developer-held exact parent — Sync R6
Parent authority:
`LITERARY_OS_SYNC_R6_I4H_VIRTUAL_PRETEST_20260908`

Physical active engine inside parent:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`

Frozen parent files:

1. CONTROL
`LITERARY_OS_CURRENT_CONTROL_P07_I4H_VIRTUAL_PRETEST_SYNC_R6_20260908.zip`
SHA256 `c291e9a3866de66fae625ab899139a13f1e98468a3bff0d58a11fd34553f0aa6`
bytes `108635838`, entries `1256`.

2. PART A
`LITERARY_OS_CURRENT_PART_A_P07_I4H_VIRTUAL_PRETEST_SYNC_R6_20260908.zip`
SHA256 `25eb489d07e78a3a3288e1e5029114ce791ada2ab43a8564ae9f9eed738306dd`
bytes `123051563`, entries `1332`.

3. PART B1
`LITERARY_OS_CURRENT_PART_B1_UNCHANGED_R1_20260908.zip`
SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
bytes `196427036`, entries `56`.

4. PART B2
`LITERARY_OS_CURRENT_PART_B2_P07_I4H_VIRTUAL_PRETEST_SYNC_R6_20260908.zip`
SHA256 `40de0853fd8e1e8318658d64a4e8d26cb8e88711842639aa45b87c0e4d062c02`
bytes `255155288`, entries `1277`.

5. PART C1
`LITERARY_OS_CURRENT_C1_RUNTIME_CORE_UNCHANGED_R1_20260908.zip`
SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
bytes `140020974`, entries `60`.

6. PART C2-A
`LITERARY_OS_CURRENT_C2_BINARY_A_P07_PHASE0_R3_I4H_VIRTUAL_SYNC_R6_20260908.bin`
SHA256 `b775bf65cba23ad5611b3383678765f88c1a444d25c4b49f7ccfb5a9d2438ec9`
bytes `159175515`.

7. PART C2-B
`LITERARY_OS_CURRENT_C2_BINARY_B_P07_PHASE0_R3_I4H_VIRTUAL_SYNC_R6_20260908.bin`
SHA256 `be4af1ac97467e1f090c8cd0854e14df1ffef6699ed23b0a80014f55e197e860`
bytes `159175514`.

8. PART D1
`LITERARY_OS_CURRENT_PART_D1_DB59_UNCHANGED_R1_20260908.zip`
SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
bytes `138011573`, entries `25`.

9. PART D2
`LITERARY_OS_CURRENT_PART_D2_DB59_UNCHANGED_R1_20260908.zip`
SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`
bytes `173393886`, entries `59`.

Parent C2 reassembly:
- order C2-A then C2-B;
- bytes `318351029`;
- entries `3765`;
- SHA256 `9878aac8532e9f1eb6b16ef4c84bcfe6be90b58a49ecf0f6afaabe993fad3be7`;
- CRC PASS / duplicate paths 0 / unsafe paths 0.

DB59 reassembly:
- bytes `259756521`;
- SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

Final delivered Sync R6 audit identity:
`LITERARY_OS_SYNC_R6_I4H_FINAL_PHYSICAL_AUDIT_R1_20260908.json`
SHA256 `94e808f6fa7c760662d0d02d1625046d23a9198afcc28bd3ab18c15453b37360`.

## 3. Current supplied-byte status in this conversation
All nine parent transport files have now been supplied by the developer in the current conversation.

Earlier in the current session, before the runtime transport layer became unstable, exact byte checks completed for:
- CONTROL -> expected Sync R6 SHA matched, CRC PASS, duplicate 0, unsafe 0;
- PART A -> expected Sync R6 SHA matched, CRC PASS, duplicate 0, unsafe 0.

Subsequent attempts to access B1/B2/C1/C2-A/C2-B/D1/D2, and later even `echo`, `stat`, `getsize`, failed at the execution transport layer with `TransportTimeoutError` before trustworthy byte operations could complete.

Therefore correct classification is:
`ALL_9_PARENT_FILES_SUPPLIED__DIRECT_RUNTIME_BYTE_VERIFICATION_COMPLETED_2_OF_9__EXECUTION_TRANSPORT_TIMEOUT_BLOCKS_REMAINING_7`.

This is not evidence of file corruption.

## 4. Previous-dialogue / Hub cross-validation verdict
The earlier conversation history contained session-local I4H/I4I progress claims made during container instability. Those claims were later explicitly withdrawn from authority and the developer-held Sync R6/I4D state was restored.

The valid durable post-correction Hub lineage is a new chain:
- I4H R1 -> HOLD before generation due source/input contamination;
- I4H R2 -> HOLD before selector due durable Control seal multiplicity/transport corruption;
- I4H R3 -> PASS stronger-virtual prospective craft signal;
- I4H R4 -> PASS fresh source-free masked physical replication;
- I4H Runtime Promotion Qualification -> PASS;
- I4I -> preregistered / plan frozen only; no Control/Treatment/score output.

Thus withdrawn session-local claims are not reused as experimental evidence.

## 5. I4H research state to recover
### R1
Commit `7588b62dca3f956cacf4fa58a7df6c6815dd5d46`.
Status:
`HOLD_PREGENERATION_INPUT_CONTAMINATION__NO_CRAFT_CLAIM__NO_PROMOTION`.

### R2
Commit `4687b5f38a2e233b0e57fa236bd080149ceaed26`.
Status:
`HOLD_PRESELECTOR_CONTROL_MULTIPLICITY_AND_DURABLE_SEAL_CORRUPTION__NO_CRAFT_CLAIM__NO_PROMOTION`.

### R3
Method closure commit `17e33163a519edb68bcc80c4970ebb255d4b0c51`.
- 18/18 scene hashes PASS;
- ABSTAIN identity 12/12;
- critical failures 0;
- 6 STANDARD interventions;
- Treatment wins 6 / Control wins 0 / ties 0;
- mean delta +0.5851666667;
- harmful rate 0.
Classification remains Development/Preformal same-model evidence.

### R4
Result commit `16773b5ad9a97ca709f0476d227c4a04fa60909d`.
- n=21 = ABSTAIN7 / LOW7 / STANDARD7;
- 14 interventions;
- Treatment wins 7 / Control wins 0 / ties 7;
- nonloss 1.0;
- harmful 0;
- overall mean delta +0.3269928571;
- STANDARD 7/7 wins, mean +0.4269857143;
- LOW nonloss 7/7, mean +0.227, voice loss 0.

Status:
`PASS_PHYSICAL_REPLICATION__I4H_DEVELOPMENT_PROMOTION_CANDIDATE`.

## 6. I4H runtime to recover
Preregistration commit:
`ac7202ac7743252ac1bb8b0ac50cb84287b7dfcd`.

Qualification result commit:
`8fa611b801118ecf2b703cf1f41288c6a7e84bcc`.

Runtime sources durable on Hub:
1. `handoff/20260909/P07_I4H_RUNTIME_PROMOTION_DELTA_R1/literary_os_runtime/i4h_intervention_policy.py`
   recorded content SHA256 `cb643e1cee8e47dfafafb87db1f335abc7203d25ac016b774678f2266cd94684`.
2. `.../i4h_runtime_renderer.py`
   recorded content SHA256 `94f766c23c45a22fc8655a56f89908cf38db384af9c8046042b474a1085a76ed`.
3. `.../i4h_episode_render_wiring.py`
   recorded content SHA256 `7f2f1b50ec9239ca5ca364b3863f28418aba2baf248fea31ca9178a7be33b741`.

Qualification record:
- 42/42 new tests PASS;
- 26/26 old targeted PASS;
- 255/255 full nonhistorical regression PASS = parent 213 + new 42;
- parent I4D runtime files 5/5 byte-identical;
- critical failure accepts 0;
- Python literary prose generation false.

Target active-development authority after successful physical recovery:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_R1`.

Production remains `ENG:R47`.
Formal count remains `137`.
Latest formal authority remains `R138`.
Formal R140 remains `0/0/0`.
OpenAI Live qualification remains NOT established.

## 7. Exact package change map for I4H-only recovery
The target is functionally the I4H active-runtime closure previously represented by session-internal Sync R8, but rebuilt directly from the actual developer-held Sync R6 parents.

### MUST REBUILD / CHANGE
- CONTROL
- PART A
- PART B2
- PART C2-A / C2-B after recombining parent C2 and applying the I4H runtime/qualification overlay

### MUST REMAIN BYTE-IDENTICAL TO SYNC R6
- PART B1
- PART C1
- PART D1
- PART D2

No DB59 mutation is allowed.
No C1 mutation is allowed.
The five frozen parent I4D files recorded by the qualification result must remain byte-identical.

## 8. Reference old internal I4H physical closure
The old session-internal I4H physical build is useful only as a reconstruction reference, not as a developer-held parent.

Reference label:
`LITERARY_OS_SYNC_R8_I4H_RUNTIME_PROMOTION_20260909`.

Reference package hashes:
- CONTROL `ddee74d5c5ebd5fcc83e3138a3f649d98114ef9d6c9ed45e17e09818b26b856c`
- A `f8d50abe9fec7580b1f2c37d41ccbe35ec71cba28eecf40b3c894148f396d76b`
- B1 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 `c80b2f389846e56250f9fd856dd3e7c4e25183da8cee9228d686046bd2e74248`
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A `d06d40bbf5aacebfffb94969b8640674809d818eee727bd82987e7e1d70919a4`
- C2-B `493c5b9368f7310b17d8e66a6f883c13caa8ff93ec40c9ae79c9ace24cb9f2bf`
- D1 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`.

Reference combined C2:
- bytes `318364190`;
- entries `3771`;
- SHA256 `eb49afacc0ef0377fc619e33c01603fe69ffcdc7d242a041a5a1d2c26c0d3ef0`.

Reference package-set material SHA256:
`4e93e545c670d9672b4c4a8e943df9d4a02702a1de707916cb6274d0a145712d`.

These old hashes are not required targets for a new cumulative rebuild because ZIP metadata/order may differ. Semantic/member identity and fresh full audits control the new build.

## 9. Exact C2 delta count and missing-body recovery defect
Sync R6 parent C2 has `3765` entries.
The old internal I4H closure C2 had `3771` entries.
Therefore I4H runtime promotion added exactly **6 C2 members**.

The durable Hub evidence is structurally consistent with the six-member overlay:
1. `literary_os_runtime/i4h_intervention_policy.py`
2. `literary_os_runtime/i4h_runtime_renderer.py`
3. `literary_os_runtime/i4h_episode_render_wiring.py`
4. `tests/test_p07_i4h_runtime_promotion.py`
5. runtime-promotion qualification preregistration evidence
6. runtime-promotion qualification result evidence

However, current Hub/File Library searches recover the test file's recorded identity only:
- bytes `15130`;
- SHA256 `9b7ef43744dfe094b2b1d1ec850c8712ba38a1f450a11c689ff43215f01fbf7a`;
while the exact test-body source is not currently discoverable as a durable Hub file.

Therefore:
`EXACT_OLD_SYNC_R8_C2_REPRODUCTION = HOLD_MISSING_TEST_BODY`.

Do NOT invent a replacement test body and call it byte-identical.
Do NOT claim the original 42/42 qualification was rerun unless the exact test body is recovered or a separately preregistered recovery qualification suite is executed and labeled as new recovery evidence.

This defect does not erase the existing durable qualification result; it limits exact physical reproducibility.

## 10. I4H evidence range
Git compare from Sync R6 handoff commit `6a6239f0e74257c48532bcf100aa24405b23fa1e` through I4H physical closure commit `2af29e335789aee7b72461d3bac3323cb79d6805` is 43 commits ahead and adds the durable R1/R2/R3/R4 evidence, runtime sources, runtime qualification records and authority closure metadata.

Post-`2af29e...` I4I plan-freeze files are a later research unit and must not be mistaken for I4H experimental outputs.

## 11. Required physical audit before developer delivery
A recovered I4H 5-Part / 9-Package set must not be delivered as PASS until all are proven:

1. all 9 parent Sync R6 files readable and parent hashes match;
2. all parent ZIPs CRC PASS, duplicate path 0, unsafe path 0;
3. parent C2-A+B reassembles to frozen Sync R6 C2;
4. B1/C1/D1/D2 output bytes equal exact parent bytes;
5. CONTROL/A/B2 contain cumulative valid I4H research/authority evidence without duplicate member paths;
6. rebuilt C2 contains exact frozen I4D parent material plus only authorized I4H runtime/qualification overlay;
7. DB59 D1+D2 reconstruction remains frozen SHA;
8. secret scan PASS;
9. active authority pointer changes to I4H only after package-level PASS;
10. Production remains ENG:R47;
11. formal scored count remains 137;
12. R140 remains 0/0/0;
13. final nine-file delivery manifest and package-set material SHA are generated;
14. final physical audit is generated and independently reopenable.

## 12. Current execution blocker
All nine parent files are supplied, but the current execution transport currently returns `TransportTimeoutError` even for minimal `echo/stat/getsize` calls across container/private-Python/user-visible-Python paths.

Because trustworthy binary mutation and SHA/CRC computation are impossible while that execution layer is unavailable, no physical package may be falsely claimed as rebuilt in this state.

Correct current status:
`I4H_RECOVERY_SPEC_COMPLETE__ALL_9_SYNC_R6_PARENTS_SUPPLIED__2_OF_9_DIRECT_BYTE_VERIFIED_BEFORE_RUNTIME_FAILURE__I4H_RESEARCH_LINEAGE_CROSS_VALIDATED__I4H_RUNTIME_DELTA_DURABLE_EXCEPT_EXACT_TEST_BODY__PHYSICAL_REBUILD_BLOCKED_BY_EXECUTION_TRANSPORT_TIMEOUT__NO_FALSE_PACKAGE_CLAIM`.
