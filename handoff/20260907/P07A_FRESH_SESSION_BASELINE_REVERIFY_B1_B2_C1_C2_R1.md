# Literary OS — P07-A Fresh-Session Baseline Re-verification B1/B2/C1/C2 R1
Date: 2026-09-07
Classification: RECOVERY CHECKPOINT / NONFORMAL / PREVIOUS_PHYSICAL_BASELINE_ONLY

## 0. Purpose
Record fresh-session verification progress after failover from the unusable prior sandbox. This checkpoint does NOT declare RFV2 repaired current authority, CP1 completion, RFV3 execution, or Formal R140 execution.

## 1. Frozen scientific authority
- Formal scored count: 137
- Latest formal scored authority: R138
- R140: 0 attempts / 0 outputs / 0 scores
- ENG:R47 Production: immutable
- P06: COMPLETED / PHYSICALLY CLOSED
- P07: ACTIVE PREFORMAL / NOT COMPLETE
- DB59 frozen SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- DB64: separate Living DB; must not replace DB59
- RFV3 outputs: 0
- Current repaired 9-package physical authority: MISSING
- R140: HARD BLOCK

## 2. Fresh-session container observation
The fresh session remained healthy through the B1 -> B2 -> C1 -> C2 verification sequence. Minimal `/bin/true`, Python execution, and `/mnt/data` probes remained successful after package processing. The prior-session global `ClientError` did not reproduce after B1 or B2 and did not reproduce after C1/C2 processing.

This strengthens the boundary that B1/B2/C1/C2 package corruption is not established as the prior failure cause. It does not yet resolve D1/D2 or cumulative mount-pressure causality.

## 3. B1 / B2 fresh verification completed
### B1 R10
- bytes: 196,427,036
- SHA256: `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- outer ZIP entries: 56
- CRC: PASS
- duplicate path: 0
- unsafe path: 0
- nested ZIP: 1/1 PASS
- internal Research Master Part 1 / split chunk metadata matched `PART_MANIFEST.json`.

### B2 R39
- bytes: 254,624,595
- SHA256: `f396d7fe583f6267c3b17735e690be5e50c35d48f2253ae7ea12a71779ecc920`
- outer ZIP entries: 1,080
- CRC: PASS
- duplicate path: 0
- unsafe path: 0
- nested ZIP: 46/46 PASS
- internal Research Master Part 2 / split chunk metadata matched its manifest.

Verdict: B1 and B2 now join the fresh-verified previous baseline.

## 4. C1 / C2 fresh re-verification
### C1 Runtime Core
- bytes: 140,020,974
- SHA256: `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- outer entries: 60
- CRC: PASS
- duplicate path: 0
- unsafe path: 0
- direct nested ZIP: 3/3 PASS
- direct nested ZIP internal duplicate/unsafe checks: 0 / 0

`PART_MANIFEST.json` required package/chunk verification:
- `LITERARY_OS_RUNTIME_SOURCE_CURRENT.zip` — 18,995,643 bytes / SHA `b3873e98d8f5df44aee22c388ac9b19bf61cbdafd5f9c09cda7f06952125da55` PASS
- `LITERARY_OS_PRE_R140_NEW_SESSION_CONTINUATION_CORE_R5_20260901_SEALED.zip` — 19,237,030 bytes / SHA `94915748c34a35db3a0308a5d08b0b74be20073b95e69b7cfa07ac96317bab18` PASS
- Narrative Engine Master `part001` — 102,083,963 bytes / SHA `1ea469025d1033fc5bced3e04db9966095e006439886ded7afeb84140acc7442` PASS

### C2 physical split
C2-A:
- bytes: 155,826,858
- SHA256: `6208a1513550525234b85b63103fb64a8c3bca8405a91c019df243a28b8ff975`

C2-B:
- bytes: 155,826,858
- SHA256: `eac1bb5b424c92c6ae97924d09864412b222e581d34b062e0818e4105ee89f5f`

Reassembly `C2-A || C2-B`:
- bytes: 311,653,716
- SHA256: `d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`
- ZIP entries: 3,610
- CRC: PASS
- duplicate path: 0
- unsafe path: 0
- direct nested ZIP: 155/155 PASS
- all 155 direct nested ZIPs: duplicate 0 / unsafe 0 / read errors 0

C2 `PART_MANIFEST.json` verification:
- `LITERARY_OS_PRE_R140_ACTUAL_CORE_R5_INTEGRATION_R1_20260902_SEALED.zip` — 18,769,997 bytes / SHA `ceb06b312f9d4248b886f5ada8528e4c964e85d48a774e0b7ece2154b50b359d` PASS
- Narrative Engine Master `part002` — 102,083,963 bytes / SHA `5866dae2e4f93e5b59098c507a9d616e4f06ede09ec9598fe74f1e7a96122e7d` PASS

### C1 + C2 cross-package Narrative Engine Master reassembly
`part001 || part002` produced:
- 204,167,926 bytes
- SHA256 `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649`
- reconstructed ZIP entries: 4,683
- CRC: PASS
- duplicate path: 0
- unsafe path: 0
- direct nested ZIP: 313/313 PASS

This matches the embedded mandatory physical-resolution authority exactly.

## 5. Current-overlay hygiene boundary
The reassembled C2 contains historical P07-PRE09 development snapshots that include cache artifacts. However the actual current candidate subtree:
`CURRENT_R11_RFV_ACTIVE_DEVELOPMENT_OVERLAY/`
contains exactly 520 files and has:
- `.pyc`: 0
- `.pytest_cache`: 0

Therefore historical cache presence elsewhere in the archive must not be mislabeled as current R11 overlay contamination.

## 6. Important semantic-recovery analysis from current R11 baseline
The inspected C2 bytes confirm that this package is the PRE-RFV2-repair baseline, not the later observed repaired working state.

Observed in `CURRENT_R11_RFV_ACTIVE_DEVELOPMENT_OVERLAY/`:
- `retrieval_candidate_spine.py` uses the old confidence gate defaults `confidence_threshold=0.60` and `margin_threshold=0.03`, with weak margin acting as a hard `NO_RETRIEVAL` condition.
- `database_consumption.py::archive_payloads_to_retrieval_records` flattens verified payload text values into retrieval `functions` and retains full payload / `thick_core`, matching the later D-2 defect boundary.
- `semantic_orchestration.py::run_verified_hierarchical_semantic_planning` calls the old gate with 0.60 / 0.03 on the actual verified archive route.
- `tools/rf_live_parity_runner.py` intentionally hard-stops CP1 and returns HOLD / exit 2 after CP0; successful current-authority CP1 is not implemented in this baseline.
- the historical `P07_PRE09_LIVE_PARITY_CP0_R1/p07_pre09_live_craft_parity.py` does contain an earlier paired Reference/Engine live-runner design, consistent with the current recovery plan to restore/integrate rather than invent CP1 from scratch.

The three interrupted-session RFV2 repaired-state evidence hashes were NOT located in C1/C2:
- `d9b50787676aa0750ba0b519b2537dedafa71807c72edef78c659ddfb6ddf419`
- `81ca599ead072c7da9291450573b5a2c782d14d2b3b5514e5a7b3265b155fd23`
- `ab60a39cc9ce8fe30835b7b3589566f7a2281af6c49957048eb2268531d95f4f`

Therefore C1/C2 do not support switching recovery mode to byte-identical RFV2 restoration. `CONTROLLED_RECOVERY_REIMPLEMENTATION` remains authoritative unless an exact artifact is later independently verified.

## 7. Supersession boundary
Embedded C2 R11 handoff text states that its then-current 8-package R-FV package propagation was physically sealed. That statement is historical within the baseline and is superseded by later Claude/CT defect discovery plus the current 5-Part / 9-Package recovery authority.

The baseline C2 must therefore be treated as:
`PREVIOUS_PHYSICAL_BASELINE`
not as:
`CURRENT_RF_V2_REPAIRED_PHYSICAL_AUTHORITY`.

## 8. Updated baseline accounting
Canonical physical packages:
`CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2`

Fresh verified in the healthy failover session / preserved prior fresh verification:
`CONTROL / A / B1 / B2 / C1 / C2-A / C2-B`

Accounting:
`9/9 baseline collected`
`7/9 fresh verified`
`D1/D2 fresh verification pending`

All verified packages remain previous physical baseline only.

## 9. Next mandatory action
Continue the isolation protocol with:
1. D1 only -> SHA/CRC/duplicate/unsafe/nested audit -> health probe.
2. D2 -> same audit -> health probe.
3. Complete 9/9 previous-baseline verification.
4. Inspect D packages for any exact surviving RFV2 repaired artifact before controlled reimplementation.
5. If none is verified, execute the already frozen RFV2 Controlled Recovery / Reimplementation specification without result-informed tuning.

Until P07-A physical closure:
- RFV3 generation: BLOCKED
- CP1 Live: BLOCKED
- official R-F: BLOCKED
- R-G freeze: BLOCKED
- Formal R140: HARD BLOCK

## 10. Status token
`P07A_FRESH_FAILOVER_CONTAINER_HEALTHY__B1_B2_FRESH_VERIFIED__C1_C2_REVERIFIED__C2_REASSEMBLY_PASS__NARRATIVE_ENGINE_MASTER_REASSEMBLY_PASS__7_OF_9_FRESH_VERIFIED__D1_D2_PENDING__RFV2_EXACT_REPAIRED_ARTIFACT_NOT_FOUND_IN_B1_B2_C1_C2__CONTROLLED_RECOVERY_REIMPLEMENTATION_REMAINS__CURRENT_PHYSICAL_AUTHORITY_MISSING__R140_HARD_BLOCK`
