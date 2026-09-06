# CURRENT DEVELOPER HUB AUTHORITY
Last updated: 2026-09-07

Read this file together with `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`. Both must describe the same state.

## CURRENT LATEST RECOVERY CHECKPOINT — READ FIRST
`handoff/20260907/P07A_CONTAINER_FAILOVER_NEW_SESSION_START_R1.md`
Commit: `89a9e1ffb140a52b90a0ef9f229e3309d52992b8`

Current Session Recovery Pointer alignment commit:
`06f47cda27c6ee35ed60f335cab496c77ec607ce`

### Container diagnosis
The interrupted session is not usable for physical package generation:
- minimal OS/container command fails with `ClientError` before file I/O;
- private Python fails;
- user-visible Python fails.

Therefore Part-D corruption is NOT established. The first recurrent failure was already observed when B1/B2 verification began, before D1/D2 fresh-byte processing. Part-D may correlate with a high-load attachment/mount phase, but any cumulative-resource/mount-pressure explanation remains a hypothesis until isolated in a healthy fresh session.

Current required operational action:
`FRESH_SESSION_CONTAINER_FAILOVER`

The new session must health-check the sandbox before any large upload, then mount/audit B1 -> B2 -> D1 -> D2 sequentially.

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

C2 reconstruction:
`C2-A || C2-B`

Previous C2 R39 expected SHA256:
`d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`

## PREVIOUS PHYSICAL BASELINE
All nine baseline files were supplied in the interrupted conversation.
Fresh verified before sandbox failure:
- CONTROL R39 `47fe62c8acf3401c69174c77c420be0d106703888def2ea2b073a9491b14eeeb`
- A R38 `9443d103de0eafd6fb063d1ba860a90e7be32d40227980d867f79808526696b1`
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A `6208a1513550525234b85b63103fb64a8c3bca8405a91c019df243a28b8ff975`
- C2-B `eac1bb5b424c92c6ae97924d09864412b222e581d34b062e0818e4105ee89f5f`
- C2-A || C2-B reconstruction matched expected previous C2 R39 SHA.

Fresh verification still required in a healthy sandbox:
- B1 R10 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 R39 `f396d7fe583f6267c3b17735e690be5e50c35d48f2253ae7ea12a71779ecc920`
- D1 R10 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 R10 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

All nine remain `PREVIOUS_PHYSICAL_BASELINE` only and are not current repaired authority.

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

## MANDATORY FRESH-SESSION EXECUTION ORDER
1. Start fresh session and read both current pointers plus the failover checkpoint.
2. Before any package upload: minimal OS probe, Python probe, `/mnt/data` probe.
3. If unhealthy, abandon that session before upload.
4. If healthy: B1 only -> SHA/CRC/duplicate/unsafe/nested audit -> health probe.
5. B2 -> audit -> health probe.
6. D1 only -> audit -> health probe.
7. D2 -> audit -> health probe.
8. If the container fails immediately after a specific mount, record the boundary but do not call that package corrupt until independently audited in another healthy session.
9. Reconfirm C2 reconstruction if C2-A/C2-B are remounted.
10. Complete 9/9 baseline audit.
11. Execute frozen RFV2 controlled recovery and fresh DB59 mechanical validation.
12. Propagate verified state into all 9 packages; changed -> new SHA, unchanged -> byte-identical proof.
13. Rebuild Manifest + Trust Root and audit SHA/CRC/duplicate/unsafe/nested/C2/DB59/secret=0.
14. Physically deliver all current 9 packages to the developer.
15. Only then declare `CURRENT_PHYSICAL_AUTHORITY`.

Until physical closure, RFV3 generation, CP1 Live, official R-F, R-G freeze, and Formal R140 remain blocked.

## CURRENT STATUS TOKEN
`CURRENT_SESSION_CONTAINER_UNUSABLE__PART_D_NOT_PROVEN_CAUSAL__FRESH_SESSION_FAILOVER_REQUIRED_FOR_PHYSICAL_PACKAGE_RECOVERY__9_BASELINE_COLLECTED__5_FRESH_VERIFIED__4_FRESH_VERIFY_PENDING__CONTROLLED_RECOVERY_SPEC_FROZEN__CURRENT_PHYSICAL_AUTHORITY_MISSING__R140_HARD_BLOCK`
