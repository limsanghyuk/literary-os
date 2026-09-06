# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-06

Always read this file first when resuming Literary OS work in a new ChatGPT session.
Then read `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`. The two pointers must agree.

## Full developer recovery + research dossier
`handoff/20260906/DEVELOPER_HUB_FULL_RECOVERY_RESEARCH_DOSSIER_R2.md`
Commit: `889037274af31ec287bd846d9afaa769dae4f172`

This is the detailed recovery document for:
- Claude/CT defects, repairs and remaining defects;
- exact developer-held previous 5-Part / 9-Package hashes;
- C2 reconstruction;
- controlled recovery if exact repaired source bytes do not survive;
- RFV2 and RFV3 research purpose/content/method;
- CP1 restoration requirements;
- package rebuild/audit order.

## Current recovery authority
START HERE:
`handoff/20260906/SESSION_RECOVERY_START_HERE_R2.md`
Commit: `3c45263d38a469d7bac216d24fce0d2c1649380e`

Developer Hub authority:
`handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
Current alignment commit: `aae87de332b5e6588d78108b20ac5032c226d99f`

Developer authority snapshot:
`handoff/20260906/DEVELOPER_HUB_AUTHORITY_SNAPSHOT_R1.md`
Commit: `934e10d4dd2deeed5ffcd34f5c543e4e93307e99`

Claude/CT defect matrix:
`handoff/20260906/CLAUDE_CT_DEFECT_CLOSURE_MATRIX_R1.md`
Commit: `62b64b37196ee2c40b8c89d945a43030a2df86f2`

Current RFV3 preregistration:
`handoff/20260906/P07_RFV3_ABCD_CAUSAL_REPRETEST_PREREG_R1.md`
Commit: `07c256a84718c0b8f4017c383c174c4bcf3a8d95`

Current latest atomic checkpoint:
`handoff/20260906/AUTHORITY_ALIGNMENT_AND_CONTAINER_HOLD_CHECKPOINT_R1.md`
Commit: `d8cf30d509508fd2502a0f26b2378e9e6eefb678`

Historical predecessor checkpoint:
`handoff/20260906/RFV3_TASK01_PREREG_AND_9PACKAGE_ATOMIC_CHECKPOINT_R1.md`
Commit: `a1e6ca0e2f84eedef3ae4ce188cecf5dc3857079`

## Current status
`AUTHORITY_DOCS_ALIGNED__DEVELOPER_HUB_ALIGNED__CONTAINER_CLIENTERROR_HOLD__9_PACKAGE_RESEAL_PENDING__CLAUDE_DEFECTS_PARTIALLY_REPAIRED_NOT_FULLY_CLOSED`

Formal scored count: 137
R140: 0 attempts / 0 outputs / 0 scores
Production: ENG:R47 immutable
DB59 frozen SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
RFV3 generation outputs: 0
Claude/CT defects: PARTIALLY REPAIRED / NOT FULLY CLOSED
CP1 current-authority restoration: OPEN
Current repaired 9-package reseal: NOT COMPLETED
R140: HARD BLOCK

## Developer-held previous physical baseline
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

These are PREVIOUS_PHYSICAL_BASELINE only and do not include all current pending RFV2/RFV3 repairs.

## Mandatory resume rule
The FIRST action after container recovery is physical 5-Part / 9-Package reconstruction and audit from the exact recovered/reconstructed repaired authority bytes. Do not begin RFV3 generation or R-F Live before this pending package closure is resolved.

Canonical package accounting:
CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2 = 9 packages.

## Important supporting uploads for a new session
If available, provide:
- all nine previous physical baseline package files listed above;
- `CT_TO_GPT_ADDENDUM7_C2R39_VERIFICATION_AND_DEFECT_RECOMMENDATION_20260906.zip`;
- `CT_TO_GPT_회신_부록7_C2R39검증_결함권고_20260906.md`;
- `A E.zip` for CT live/API evidence review;
- any RFV2 repair source/evidence artifacts that survived outside the failed container.

If exact repaired source bytes are unavailable, follow the controlled reconstruction procedure in `DEVELOPER_HUB_FULL_RECOVERY_RESEARCH_DOSSIER_R2.md`; do not claim byte-identical recovery.
