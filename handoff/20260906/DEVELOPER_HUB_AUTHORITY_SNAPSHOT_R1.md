# Literary OS — Developer Hub Authority Snapshot R1
Date: 2026-09-06
Role: current developer-facing authority snapshot while local artifact/container backend is unavailable.

## 0. Authority rule
This snapshot is a **developer hub status authority**, not a substitute for missing binary package reseal.
When physical 5-Part / 9-Package artifacts are unavailable, this document plus the current recovery pointer and atomic checkpoint define the exact recovery state. Binary execution authority requires the actual package bytes and fresh audit.

## 1. Current scientific state
- Formal scored count: **137**
- Latest formal scored authority: **R138**
- R140: **0 attempts / 0 outputs / 0 scores**
- ENG:R47 Production: **immutable**
- P07: **active preformal / not complete**
- R140: **HARD BLOCK**
- DB59 frozen reference SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- Current active preregistered comparison: **RFV3 A/B/C/D Causal Re-pretest**
- RFV3 generation outputs: **0** at current sealed checkpoint
- Current container/artifact state: **ClientError / Infrastructure HOLD**
- Current package state: **9_PACKAGE_RESEAL_PENDING_INFRASTRUCTURE**

## 2. Current authority chain
1. `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`
2. latest `SESSION_RECOVERY_START_HERE` referenced by that pointer
3. `handoff/20260906/P07_RFV3_ABCD_CAUSAL_REPRETEST_PREREG_R1.md`
   - commit `07c256a84718c0b8f4017c383c174c4bcf3a8d95`
4. `handoff/20260906/RFV3_TASK01_PREREG_AND_9PACKAGE_ATOMIC_CHECKPOINT_R1.md`
   - commit `a1e6ca0e2f84eedef3ae4ce188cecf5dc3857079`
5. `handoff/20260906/CLAUDE_CT_DEFECT_CLOSURE_MATRIX_R1.md`
   - commit `62b64b37196ee2c40b8c89d945a43030a2df86f2`

Newest checkpoint may advance **status**, but cannot create missing binary authority by text declaration.

## 3. Current canonical package accounting
Canonical delivery is exactly **5 Parts / 9 Packages**:
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

### Previous physical baseline only
The following are the last known previous physical baseline hashes. They **do not yet contain all RFV2/RFV3 pending repairs** and must never be silently called the current repaired authority.
- CONTROL R39: `47fe62c8acf3401c69174c77c420be0d106703888def2ea2b073a9491b14eeeb`
- PART-A R38: `9443d103de0eafd6fb063d1ba860a90e7be32d40227980d867f79808526696b1`
- B1 R10: `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 R39: `f396d7fe583f6267c3b17735e690be5e50c35d48f2253ae7ea12a71779ecc920`
- C1: `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A: `6208a1513550525234b85b63103fb64a8c3bca8405a91c019df243a28b8ff975`
- C2-B: `eac1bb5b424c92c6ae97924d09864412b222e581d34b062e0818e4105ee89f5f`
- D1 R10: `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 R10: `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`
- reassembled previous C2 R39: `d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`

## 4. Claude/CT defect status summary
See `CLAUDE_CT_DEFECT_CLOSURE_MATRIX_R1.md` for full detail.

### Working-state repair observed, physical closure pending
- DB59 actual retrieval and donor semantic propagation to LLM planning input;
- positive/negative DB dependency tests;
- verified archive path rewiring to repaired retrieval;
- bounded functional work profiles;
- diagnostic score separation from literary semantic payload;
- Frozen Retrieval Index authority/tamper behavior;
- nonhistorical regression observed 185/185.

### Still open / blocking
- current-authority CP1 paired runner restoration/integration;
- current-authority CP1 TestDouble validation;
- official R-F real OpenAI CP1 live run;
- fresh verification from exact resealed package bytes;
- full 5-Part / 9-Package physical reseal;
- legacy entrypoint drift cleanup and blind-secret physical separation before R140.

Therefore: **Claude/CT defects are NOT all closed.**

## 5. RFV3 preregistered comparison
A = SUMMARY ONLY
B = PRE-REPAIR ENGINE / NO_RETRIEVAL
C = RFV2 REPAIRED ENGINE / DB59 USE_RETRIEVAL
D = FULL CURRENT CANDIDATE + BIDIRECTIONAL REFINEMENT

Purpose:
- A vs B: runtime information preservation/loss
- B vs C: incremental DB59 value
- C vs D: incremental bidirectional-refinement value

No RFV3 output has been generated under the current sealed checkpoint.

## 6. Mandatory resume order after container recovery
1. run minimal container health check;
2. recover/verify exact repaired RFV2 source bytes and pending amendments/checkpoints;
3. reconstruct the previous physical 9-package baseline;
4. propagate all current repaired-state documents/code/evidence into the canonical 9 packages;
5. rebuild package manifests and Trust Root;
6. verify SHA256, outer CRC, duplicate paths, unsafe paths, nested ZIPs, C2 reassembly, and authority pointers;
7. fresh-run repaired DB59 6-case audit;
8. fresh-run direct DB59 vs Frozen Index equivalence/tamper audit;
9. fresh-run selected/unselected donor propagation tests and full nonhistorical regression;
10. restore/integrate current-authority CP1 paired runner;
11. run CP1 TestDouble/fail-closed suite;
12. reseal updated 9 packages again if CP1 implementation changes bytes;
13. only then run official R-F paired OpenAI live CP1;
14. after R-F closure: R-G Freeze -> fresh formal sample -> revised R140 preregistration -> new G0 -> Formal R140.

## 7. Required package-close audit
A package set is not current authority until all applicable checks PASS:
- expected 9 package files present;
- per-package SHA256 recorded;
- ZIP CRC PASS for ZIPs;
- duplicate path 0;
- unsafe path 0;
- nested ZIP audit PASS;
- C2-A + C2-B exact reassembly SHA PASS;
- DB59 authority reassembly/reference SHA unchanged unless explicitly and separately versioned;
- Manifest and Trust Root agree byte-for-byte with package hashes;
- Current Developer Hub and Current Session Recovery Pointer point to the same scientific/package state;
- no secret/API key embedded.

## 8. Prohibited claims while infrastructure HOLD remains
Do not claim:
- current repaired 9-package physical closure;
- current CP1 completion;
- official R-F Live Provider completion;
- R-G freeze;
- Formal R140 execution;
- production promotion.

## 9. Current final status tokens
`FORMAL_COUNT_137`
`R140_0_ATTEMPTS_0_OUTPUTS_0_SCORES`
`RFV3_TASK01_PREREGISTERED`
`RFV3_GENERATION_NOT_STARTED`
`RFV2_REPAIRED_STATE_OBSERVED_REVERIFY_FROM_BYTES_REQUIRED`
`CP1_CURRENT_AUTHORITY_RESTORATION_OPEN`
`9_PACKAGE_RESEAL_PENDING_INFRASTRUCTURE`
`R140_HARD_BLOCK`