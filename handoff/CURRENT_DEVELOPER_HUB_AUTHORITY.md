# CURRENT DEVELOPER HUB AUTHORITY
Last updated: 2026-09-07

Read this file together with `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`. Both must describe the same state.

## CURRENT LATEST RECOVERY CHECKPOINT — READ FIRST
`handoff/20260907/P07A_FRESH_SESSION_BASELINE_REVERIFY_B1_B2_C1_C2_R1.md`
Commit: `f5e9c97b0e32cee9de2b00773f740fbe9df7e7be`

Current Session Recovery Pointer alignment commit:
`6b8269cfa232daffca1f9fb00f8257928eb1681c`

Previous failover checkpoint:
`handoff/20260907/P07A_CONTAINER_FAILOVER_NEW_SESSION_START_R1.md`
Commit: `89a9e1ffb140a52b90a0ef9f229e3309d52992b8`

### Fresh-session infrastructure result
The failover session remained healthy through sequential B1 -> B2 -> C1 -> C2 processing. Minimal OS `/bin/true`, Python, and `/mnt/data` probes remained successful after package processing. The prior-session global `ClientError` did not reproduce after these packages.

Therefore B1/B2/C1/C2 package corruption is not supported by the fresh audits. D1/D2 and cumulative mount/resource-pressure causality remain to be isolated.

## CURRENT SCIENTIFIC AUTHORITY
- Formal scored count: 137
- Latest formal scored authority: R138
- R140: 0 attempts / 0 outputs / 0 scores
- ENG:R47 Production: immutable
- P06: COMPLETED / PHYSICALLY CLOSED
- P07: ACTIVE PREFORMAL / NOT COMPLETE
- Current priority: P07-A — Authority / Package Recovery
- DB59 frozen SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- DB64: separate Living DB; MUST NOT silently replace DB59
- RFV3 outputs: 0
- Claude/CT defects: PARTIALLY REPAIRED / NOT FULLY CLOSED
- CP1 current-authority restoration: OPEN
- current repaired 9-package physical authority: MISSING
- R140: HARD BLOCK

## CANONICAL 5-PART / 9-PACKAGE STRUCTURE
`CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2`

Logical Parts:
- CONTROL = control/authority layer
- A = control + experiment layer
- B = B1 research-history + B2 current-recovery layer
- C = C1 runtime core + C2 candidate engine; physical C2 is split into C2-A/C2-B
- D = D1 DB59 drama bundle + D2 DB59 drama learning layer

## PREVIOUS PHYSICAL BASELINE — FRESH VERIFIED 7/9
Fresh verified / reverified:
- CONTROL R39 `47fe62c8acf3401c69174c77c420be0d106703888def2ea2b073a9491b14eeeb`
- A R38 `9443d103de0eafd6fb063d1ba860a90e7be32d40227980d867f79808526696b1`
- B1 R10 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 R39 `f396d7fe583f6267c3b17735e690be5e50c35d48f2253ae7ea12a71779ecc920`
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A `6208a1513550525234b85b63103fb64a8c3bca8405a91c019df243a28b8ff975`
- C2-B `eac1bb5b424c92c6ae97924d09864412b222e581d34b062e0818e4105ee89f5f`

C2 reconstruction:
`C2-A || C2-B`
- bytes 311,653,716
- SHA256 `d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`
- 3,610 entries / CRC PASS / duplicate 0 / unsafe 0 / direct nested ZIP 155/155 PASS

C1/C2 Narrative Engine Master split reassembly:
- bytes 204,167,926
- SHA256 `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649`
- 4,683 entries / CRC PASS / duplicate 0 / unsafe 0 / direct nested ZIP 313/313 PASS

Fresh verification still required:
- D1 R10 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 R10 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Accounting:
`9/9 baseline collected`
`7/9 fresh verified`
`D1/D2 fresh verification pending`

All nine remain `PREVIOUS_PHYSICAL_BASELINE` only and are not current repaired authority.

## C1/C2 RECOVERY ANALYSIS
The current candidate subtree inside C2:
`CURRENT_R11_RFV_ACTIVE_DEVELOPMENT_OVERLAY/`
contains exactly 520 files with `.pyc=0` and `.pytest_cache=0`. Cache artifacts exist only in historical P07-PRE09 snapshots elsewhere in the archive and must not be conflated with current-overlay contamination.

The fresh code inspection confirms this R11 package is PRE-RFV2-repair baseline:
- current retrieval gate defaults are confidence 0.60 / margin 0.03, with the margin still acting as a hard `NO_RETRIEVAL` gate;
- verified archive normalization flattens payload text and retains broad payload/thick-core material;
- the actual verified archive route consumes that old retrieval gate;
- current `rf_live_parity_runner.py` intentionally stops at CP0 and HOLDs CP1;
- a historical P07 PRE09 paired Reference/Engine live-runner implementation survives as a recovery design source.

The known interrupted-session RFV2 repaired-state evidence hashes were not located in B1/B2/C1/C2. Therefore these packages do not support byte-identical RFV2 restoration.

Embedded R11 package text that described its then-current 8-package R-FV physical seal is historical baseline evidence and is superseded by the later Claude/CT defect findings and the current 5-Part / 9-Package recovery authority.

## RFV2 RECOVERY AUTHORITY
Durable-source audit:
`handoff/20260907/P07A_INFRASTRUCTURE_DIAG_AND_RFV2_SOURCE_SURVIVAL_AUDIT_R1.md`
Commit: `9513b92ba171bd4cdc0371c1688f751f3fc09aa9`

Preresult controlled-recovery specification:
`handoff/20260907/P07A_RFV2_CONTROLLED_RECOVERY_REIMPLEMENTATION_SPEC_R1.md`
Commit: `c2c38fc55508ee874777e5752ed984f938fe60bb`

Current RFV2 recovery mode:
`CONTROLLED_RECOVERY_REIMPLEMENTATION`
unless an exact interrupted-session repaired artifact is later independently hash/checkpoint verified.

Frozen essentials:
- R37/R38-compatible work-level TF-IDF/cosine concept
- analyzer `char_wb`, ngram 2–5, top-k 4
- HIGH >= 0.13; MEDIUM >= 0.10 and < 0.13; LOW < 0.10 -> fallback
- top1-top2 margin diagnostic only
- bounded THICK-derived functional profiles
- diagnostic confidence/margin separated from literary semantic payload
- actual verified archive path must consume repaired retrieval route
- selected-donor positive dependency
- irrelevant-unselected invariance
- Direct DB59 vs Frozen Index equivalence/tamper validation
- Python literary prose generation = 0
- no result-informed tuning

Historical 6/6 and 185/185 are observations to reverify, not targets.

## CONTINUITY AUTHORITIES
- Master P06->P07 Handoff: `handoff/20260906/NEW_SESSION_MASTER_HANDOFF_P06_TO_P07_RECOVERY_R1.md` commit `147dc8f7e476b7d5a1f565343b7fe7e685d2e81c`
- Full Recovery Research Dossier: `handoff/20260906/DEVELOPER_HUB_FULL_RECOVERY_RESEARCH_DOSSIER_R2.md` commit `889037274af31ec287bd846d9afaa769dae4f172`
- Claude/CT Defect Matrix: `handoff/20260906/CLAUDE_CT_DEFECT_CLOSURE_MATRIX_R1.md` commit `62b64b37196ee2c40b8c89d945a43030a2df86f2`
- RFV3 Preregistration: `handoff/20260906/P07_RFV3_ABCD_CAUSAL_REPRETEST_PREREG_R1.md` commit `07c256a84718c0b8f4017c383c174c4bcf3a8d95`

## MANDATORY NEXT EXECUTION ORDER
1. D1 only -> SHA/CRC/duplicate/unsafe/nested audit -> health probe.
2. D2 -> same audit -> health probe.
3. Complete 9/9 previous-baseline byte verification.
4. Inspect D1/D2 for any exact surviving RFV2 repaired artifact; independently verify before changing recovery mode.
5. If no exact artifact is verified, execute the frozen RFV2 controlled recovery / reimplementation contract.
6. Fresh DB59 retrieval/propagation/equivalence/tamper/regression validation.
7. Propagate verified repaired state into all 9 packages; changed -> new SHA, unchanged -> byte-identical proof.
8. Rebuild Manifest + Trust Root and audit SHA/CRC/duplicate/unsafe/nested/C2/DB59/secret=0.
9. Physically deliver all current 9 packages to the developer.
10. Only then declare `CURRENT_PHYSICAL_AUTHORITY`.

Until physical closure, RFV3 generation, CP1 Live, official R-F, R-G freeze, and Formal R140 remain blocked.

## CURRENT STATUS TOKEN
`P07A_FRESH_FAILOVER_CONTAINER_HEALTHY__9_BASELINE_COLLECTED__7_FRESH_VERIFIED__D1_D2_PENDING__B1_B2_C1_C2_PACKAGE_CORRUPTION_NOT_SUPPORTED__C2_AND_NARRATIVE_ENGINE_MASTER_REASSEMBLY_PASS__RFV2_EXACT_REPAIRED_ARTIFACT_NOT_FOUND_IN_B1_B2_C1_C2__CONTROLLED_RECOVERY_REIMPLEMENTATION_REMAINS__CURRENT_PHYSICAL_AUTHORITY_MISSING__R140_HARD_BLOCK`
