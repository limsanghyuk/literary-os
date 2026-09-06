# CURRENT DEVELOPER HUB AUTHORITY
Last updated: 2026-09-07

Read this file together with `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`.
Both pointers must describe the same scientific and package state.

## CURRENT LATEST RECOVERY CHECKPOINT — READ FIRST
`handoff/20260907/P07A_INFRASTRUCTURE_DIAG_AND_RFV2_SOURCE_SURVIVAL_AUDIT_R1.md`
Commit: `9513b92ba171bd4cdc0371c1688f751f3fc09aa9`

Current prere-result reconstruction contract:
`handoff/20260907/P07A_RFV2_CONTROLLED_RECOVERY_REIMPLEMENTATION_SPEC_R1.md`
Commit: `c2c38fc55508ee874777e5752ed984f938fe60bb`

The latest checkpoint establishes:
- all 9 previous physical baseline packages are supplied;
- CONTROL / A / C1 / C2-A / C2-B were freshly verified before the recurrent infrastructure failure;
- `C2-A || C2-B` reconstructed the expected previous C2 R39 SHA;
- B1 / B2 / D1 / D2 remain fresh-byte-verification pending because all available local execution paths return `ClientError`;
- the recurrent failure is classified as local execution/artifact `INFRASTRUCTURE_HOLD`, not experiment failure and not evidence of package corruption;
- durable GitHub tree/code/commit searches preserve RFV2 repair documents and evidence references but did not locate a complete byte-verifiable interrupted-session RFV2 repaired implementation snapshot;
- byte-identical RFV2 restoration is therefore not supportable from currently located durable GitHub artifacts;
- unless an exact external/package artifact is later independently verified, the recovery path is `CONTROLLED_RECOVERY_REIMPLEMENTATION` under the frozen 2026-09-07 prere-result specification;
- current repaired 9-package physical authority still does not exist.

Current baseline accounting:
`9/9 COLLECTED__5/9 PREVIOUSLY FRESH-VERIFIED__4/9 FRESH-VERIFY_PENDING_INFRASTRUCTURE`

## Recovery predecessor
`handoff/20260907/P07A_LATEST_STATE_RECOVERY_RESUME_CHECKPOINT_R1.md`
Commit: `dcf5749a5042fae6bea35f6f93a335f33f7e0ad2`

## MASTER NEW-SESSION HANDOFF — P06→P07 CONTINUITY
`handoff/20260906/NEW_SESSION_MASTER_HANDOFF_P06_TO_P07_RECOVERY_R1.md`
Commit: `147dc8f7e476b7d5a1f565343b7fe7e685d2e81c`

## Full developer recovery + research dossier
`handoff/20260906/DEVELOPER_HUB_FULL_RECOVERY_RESEARCH_DOSSIER_R2.md`
Commit: `889037274af31ec287bd846d9afaa769dae4f172`

## Claude/CT defect closure matrix
`handoff/20260906/CLAUDE_CT_DEFECT_CLOSURE_MATRIX_R1.md`
Commit: `62b64b37196ee2c40b8c89d945a43030a2df86f2`

## RFV3 preregistration
`handoff/20260906/P07_RFV3_ABCD_CAUSAL_REPRETEST_PREREG_R1.md`
Commit: `07c256a84718c0b8f4017c383c174c4bcf3a8d95`
RFV3 remains preregistered with generation outputs = 0 and MUST NOT start before P07-A physical recovery closure.

## Historical recovery authorities
`handoff/20260906/SESSION_RECOVERY_START_HERE_R2.md`
Commit: `3c45263d38a469d7bac216d24fce0d2c1649380e`

`handoff/20260906/DEVELOPER_HUB_AUTHORITY_SNAPSHOT_R1.md`
Commit: `934e10d4dd2deeed5ffcd34f5c543e4e93307e99`

`handoff/20260906/AUTHORITY_ALIGNMENT_AND_CONTAINER_HOLD_CHECKPOINT_R1.md`
Commit: `d8cf30d509508fd2502a0f26b2378e9e6eefb678`

## Current scientific/package state
- Formal scored count: 137
- Latest formal scored authority: R138
- R140: 0 attempts / 0 outputs / 0 scores
- ENG:R47 Production: immutable
- P06: COMPLETED / PHYSICALLY CLOSED
- P07: ACTIVE PREFORMAL / NOT COMPLETE
- Current priority: P07-A Authority / Package Recovery
- DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- DB64: separate Living DB; MUST NOT silently replace DB59 in this lineage
- RFV2 working repair: historically observed; exact durable repaired source snapshot not located in current GitHub audit
- RFV2 recovery mode: `CONTROLLED_RECOVERY_REIMPLEMENTATION` unless an exact artifact is later independently verified
- RFV3 outputs: 0
- Local execution/artifact paths: recurrent `ClientError` / Infrastructure HOLD
- Canonical package structure: CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2
- Previous baseline collection: 9/9 collected
- Previous baseline fresh verification: 5/9 complete; B1/B2/D1/D2 pending infrastructure
- Current repaired 9-package physical reseal: NOT COMPLETED
- Claude/CT defects: PARTIALLY REPAIRED / NOT FULLY CLOSED
- CP1 current-authority restoration: OPEN
- R140: HARD BLOCK

## Developer-held previous physical baseline
These values are PREVIOUS_PHYSICAL_BASELINE only:
- CONTROL R39 `47fe62c8acf3401c69174c77c420be0d106703888def2ea2b073a9491b14eeeb`
- PART-A R38 `9443d103de0eafd6fb063d1ba860a90e7be32d40227980d867f79808526696b1`
- B1 R10 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 R39 `f396d7fe583f6267c3b17735e690be5e50c35d48f2253ae7ea12a71779ecc920`
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A `6208a1513550525234b85b63103fb64a8c3bca8405a91c019df243a28b8ff975`
- C2-B `eac1bb5b424c92c6ae97924d09864412b222e581d34b062e0818e4105ee89f5f`
- D1 R10 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 R10 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`
- C2-A || C2-B previous reconstructed C2 R39 `d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`

These are not current repaired authority.

## Frozen controlled-recovery contract
The current prere-result spec freezes:
- work-level R37/R38-compatible TF-IDF/cosine concept;
- `char_wb`, ngram 2–5, top-k=4;
- HIGH >= 0.13; MEDIUM >= 0.10 and < 0.13; LOW < 0.10 -> fallback;
- top1-top2 margin diagnostic only;
- bounded THICK-derived functional profiles;
- diagnostic confidence/margin separated from literary semantic payload;
- actual verified archive path must consume the repaired retrieval route;
- positive selected-donor dependency and negative irrelevant-unselected invariance;
- Direct DB59 vs Frozen Index and tamper/fail-closed validation;
- Python literary prose generation = 0;
- no result-informed threshold/prompt/donor/rubric tuning.

Historical 6/6 and 185/185 values are observations to reverify, not reconstruction targets.

## Mandatory next actions
1. Recover a healthy binary/container execution path.
2. Fresh-verify B1/B2/D1/D2 SHA256 and ZIP audits.
3. Reconfirm C2 reassembly from the current supplied bytes.
4. Inspect packages for any exact RFV2 repaired artifact; if one is found, verify its hash/checkpoint before changing recovery mode.
5. Verify DB59 SHA and frozen membership/cutoff.
6. Execute the frozen controlled RFV2 recovery/reimplementation contract.
7. Fresh-run retrieval/propagation/equivalence/tamper/source-cutoff/Python-prose/full-regression validation and preserve FAIL/HOLD without retuning.
8. Propagate the verified repaired state into all 9 packages; each package must be new-SHA changed or proven byte-identical unchanged.
9. Rebuild Manifest + Trust Root and align them with this Hub and the Session Recovery Pointer.
10. Only after all physical audits PASS may the result be called `CURRENT_PHYSICAL_AUTHORITY`.
11. CP1 integration/TestDouble and subsequent second reseal come only after P07-A closure; official R-F Live and Formal R140 remain blocked.

## Current final status token
`P07A_INFRASTRUCTURE_DIAG_COMPLETE__9_BASELINE_COLLECTED__5_FRESH_VERIFIED__4_FRESH_VERIFY_PENDING_CLIENTERROR__RFV2_DURABLE_GITHUB_EXACT_SOURCE_NOT_LOCATED__CONTROLLED_RECOVERY_REIMPLEMENTATION_SPEC_FROZEN__CURRENT_REPAIRED_9PACKAGE_MISSING__R140_HARD_BLOCK`
