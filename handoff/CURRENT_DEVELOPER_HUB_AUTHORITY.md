# CURRENT DEVELOPER HUB AUTHORITY
Last updated: 2026-09-07

Read this file together with `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`. Both must describe the same state.

## CURRENT LATEST RECOVERY CHECKPOINT — READ FIRST
`handoff/20260907/P07A_9OF9_BASELINE_AND_FULL_CONTEXT_RECOVERY_R1.md`
Commit: `52d7b9ecfa709deee18dbc29925d40d1fccad395`

Current Session Recovery Pointer alignment commit:
`7d01be85f014329974b9e01560eceb192827827b`

Previous checkpoints:
- `handoff/20260907/P07A_FRESH_SESSION_BASELINE_REVERIFY_B1_B2_C1_C2_R1.md` — `f5e9c97b0e32cee9de2b00773f740fbe9df7e7be`
- `handoff/20260907/P07A_CONTAINER_FAILOVER_NEW_SESSION_START_R1.md` — `89a9e1ffb140a52b90a0ef9f229e3309d52992b8`

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

Logical authority:
- CONTROL = current control / handoff / top-level authority
- A = experiment / preregistration / evaluation / governance control
- B = research authority: B1 history + B2 current recovery/research
- C = engine authority: C1 runtime core + physical C2-A/C2-B candidate engine
- D = DB59/data-learning authority: D1 operational drama bundle + D2 drama-learning master

## PREVIOUS PHYSICAL BASELINE — FRESH VERIFIED 9/9
All nine developer-supplied baseline package files have now been freshly audited in the healthy failover session:
- CONTROL R39 `47fe62c8acf3401c69174c77c420be0d106703888def2ea2b073a9491b14eeeb`
- A R38 `9443d103de0eafd6fb063d1ba860a90e7be32d40227980d867f79808526696b1`
- B1 R10 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 R39 `f396d7fe583f6267c3b17735e690be5e50c35d48f2253ae7ea12a71779ecc920`
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A `6208a1513550525234b85b63103fb64a8c3bca8405a91c019df243a28b8ff975`
- C2-B `eac1bb5b424c92c6ae97924d09864412b222e581d34b062e0818e4105ee89f5f`
- D1 R10 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 R10 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Accounting:
`9/9_COLLECTED__9/9_FRESH_VERIFIED__PREVIOUS_PHYSICAL_BASELINE_BYTE_CLOSURE_COMPLETE`

All nine are still `PREVIOUS_PHYSICAL_BASELINE`, not the current repaired authority.

## CROSS-PACKAGE INTEGRITY / REASSEMBLY — FRESH PASS
- B1+B2 Research Experiment Learning Recovery Master:
  - 77,347,512 bytes
  - SHA256 `392840526d8b7017eda6607aea37597c5e6c7df93fc1bcb951deed2de58d31b0`
  - CRC PASS; duplicate=0; unsafe=0; nested 83/83 PASS
- C2-A || C2-B previous C2 R39:
  - 311,653,716 bytes
  - SHA256 `d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`
  - 3,610 entries; CRC PASS; duplicate=0; unsafe=0; nested 155/155 PASS
  - current R11 active overlay 520 files; `.pyc=0`; `.pytest_cache=0`
- C1+C2 Narrative Engine Master:
  - 204,167,926 bytes
  - SHA256 `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649`
  - CRC PASS; nested 313/313 PASS
- D1+D2 frozen DB59:
  - 259,756,521 bytes
  - SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
  - 38,852 entries; CRC PASS; duplicate=0; unsafe=0; nested 6/6 PASS

## FRESH-SESSION INFRASTRUCTURE RESULT
The failover session remained healthy throughout B1 -> B2 -> C1 -> C2 -> D1 -> D2 auditing. Minimal OS, Python, and `/mnt/data` health probes remained successful after D1 and after D2.

The prior-session global `ClientError` did not reproduce. Fresh evidence does not support B1/B2/C1/C2/D1/D2 corruption as the cause. The exact infrastructure root cause remains unproven.

## CURRENT RECOVERY / RFV2 BOUNDARY
The known interrupted-session RFV2 repaired-state evidence hashes were searched across the currently supplied baseline package text/code surfaces and were not located:
- `d9b50787676aa0750ba0b519b2537dedafa71807c72edef78c659ddfb6ddf419`
- `81ca599ead072c7da9291450573b5a2c782d14d2b3b5514e5a7b3265b155fd23`
- `ab60a39cc9ce8fe30835b7b3589566f7a2281af6c49957048eb2268531d95f4f`

Historical PRE09 paired-live code and current R11 CP0/HOLD code survive, but the exact interrupted-session RFV2 repaired implementation does not have byte-verifiable survival support from the supplied baseline packages.

Current C2 is PRE-RFV2 previous baseline and MUST NOT be relabeled as the repaired engine.

Current RFV2 recovery mode:
`CONTROLLED_RECOVERY_REIMPLEMENTATION`
unless an exact repaired artifact is later independently hash/checkpoint verified.

Frozen recovery authorities:
- `handoff/20260907/P07A_INFRASTRUCTURE_DIAG_AND_RFV2_SOURCE_SURVIVAL_AUDIT_R1.md` — `9513b92ba171bd4cdc0371c1688f751f3fc09aa9`
- `handoff/20260907/P07A_RFV2_CONTROLLED_RECOVERY_REIMPLEMENTATION_SPEC_R1.md` — `c2c38fc55508ee874777e5752ed984f938fe60bb`

Frozen essentials:
- R37/R38-compatible work-level TF-IDF/cosine
- analyzer `char_wb`; ngram 2-5; top-k 4
- HIGH >= 0.13; MEDIUM >= 0.10 and < 0.13; LOW < 0.10 -> fallback
- top1-top2 margin diagnostic only
- bounded THICK-derived functional profiles
- diagnostic confidence/margin separated from literary semantic payload
- verified archive actual path consumes repaired retrieval route
- selected-donor positive dependency
- irrelevant-unselected invariance
- Direct DB59 vs Frozen Index equivalence/tamper validation
- source-cutoff enforcement
- Python literary prose generation = 0
- no result-informed tuning

Historical 6/6 and 185/185 are observations to reverify, not targets.

## RECOVERED RESEARCH / EXPERIMENT INTERPRETATION
Prior-session conversation records, Research Master / Experiment Registry material, historical-validation packages, Full Recovery Dossier, Claude/CT defect matrix, and RFV3 preregistration have been aligned under temporal supersession.

Current high-level evolution:
`Scene/Sequence -> Retrieval/Boundary -> Episode Planning -> Selector/Controller/Thread -> Hierarchy/Blueprint/Multi-Episode -> DB Semantic Consumption -> Entity/Relationship -> Ensemble/Social Ecology -> Series/Episode/Sequence/Scene -> Broadcast Scale -> Surface/Renderer/Voice -> External Generalization/Clean Replication/Metrology`.

Key current claim boundaries:
- R41/P01: Ensemble effect replicated; tonal increment not supported.
- R42/P02: Blueprint depth + mismatch harm replicated; Thread Binding incremental primary gate failed due treatment implementation limits.
- R103/P03: iterated clean engineering revalidation PASS; failed attempts preserved.
- R121/P04: broadcast-scale iterated clean revalidation PASS; failed attempts preserved.
- R129-R132: strong internal signals only; do not generalize directly.
- R133: external blind cross-work generalization FAIL.
- R134: R129 clean replay failed; R129 lineage = `CONFLICTED_NOT_REPLICATED`.
- R135: linked external relative renderer effect supported only; not newly formal-scored; voice bottleneck remains.
- R136-R138: remaining surface/oral/voice bottleneck progressively localized; R138 latest formal scored.
- R139: external evaluation/metrology protocol failure; CLOSED_NOT_SCORED; no content-effect inference.

P-phase interpretation:
- P0 = pre-R140 inspector/self-description/reproducibility engineering repair; count delta 0.
- P01 = R41 clean historical validation.
- P02 = R42 clean historical validation.
- P03 = R103 clean historical validation.
- P04 = R121 clean historical validation.
- P05 = R135 linked external closure; count delta 0.
- P06 = Frozen Reference + Living DB governance; physically closed; DB59 remains this lineage's frozen authority.
- P07 = active preformal qualification/recovery; not complete.

Mandatory adoption doctrine:
`Value changes -> Consumer receives -> selected donor/semantic payload changes -> LLM provider input changes -> downstream behavior changes -> Receipt/Trace proves propagation`.

Therefore:
- File exists != Implemented
- Field exists != Consumed
- Function called != Adopted
- Validator PASS != Literary/Semantic Quality PASS
- Python literary prose bytes = 0

## RFV3 PREREGISTRATION — STILL ZERO OUTPUTS
Authority: `handoff/20260906/P07_RFV3_ABCD_CAUSAL_REPRETEST_PREREG_R1.md` commit `07c256a84718c0b8f4017c383c174c4bcf3a8d95`.

Frozen arms:
- A = SUMMARY ONLY
- B = PRE-REPAIR ENGINE / NO_RETRIEVAL
- C = RFV2 REPAIRED ENGINE / DB59 USE_RETRIEVAL
- D = C + BIDIRECTIONAL REFINEMENT

Causal questions:
- A vs B = runtime information preservation/loss
- B vs C = incremental DB59 retrieval craft value
- C vs D = incremental bidirectional refinement value

RFV3 generation remains blocked until recovery prerequisites are satisfied.

## CONTINUITY AUTHORITIES
- Master P06->P07 Handoff: `handoff/20260906/NEW_SESSION_MASTER_HANDOFF_P06_TO_P07_RECOVERY_R1.md` — `147dc8f7e476b7d5a1f565343b7fe7e685d2e81c`
- Full Recovery Research Dossier: `handoff/20260906/DEVELOPER_HUB_FULL_RECOVERY_RESEARCH_DOSSIER_R2.md` — `889037274af31ec287bd846d9afaa769dae4f172`
- Claude/CT Defect Matrix: `handoff/20260906/CLAUDE_CT_DEFECT_CLOSURE_MATRIX_R1.md` — `62b64b37196ee2c40b8c89d945a43030a2df86f2`
- RFV3 Preregistration: `handoff/20260906/P07_RFV3_ABCD_CAUSAL_REPRETEST_PREREG_R1.md` — `07c256a84718c0b8f4017c383c174c4bcf3a8d95`

## MANDATORY NEXT EXECUTION ORDER
1. Previous physical baseline verification is COMPLETE 9/9.
2. Recover/reimplement RFV2 strictly under the frozen preresult controlled-recovery contract.
3. Freshly validate DB59 authority/membership, six development cases, CASE-01 propagation, selected/unselected donor causality, Direct DB59 vs Frozen Index equivalence, outer/inner tamper HOLD, source leak=0, Python prose=0, and full nonhistorical regression.
4. Preserve FAIL/HOLD without result-informed tuning.
5. Propagate verified recovered state into all 9 packages; changed -> new SHA, unchanged -> byte-identical proof.
6. Rebuild Manifest + Trust Root; audit SHA/CRC/duplicate/unsafe/nested/C2/DB59/secret=0.
7. Physically deliver all nine current packages.
8. Only then declare `CURRENT_PHYSICAL_AUTHORITY`.
9. Then continue retrieval/propagation mechanical closure, RFV3 causal re-pretest, CP1 current-authority integration, official R-F paired Live, R-G freeze/formal readiness, and Formal R140 according to the latest sealed sequence.

Until prerequisite closure, RFV3 generation, CP1 Live, official R-F, R-G, and Formal R140 remain blocked.

## CURRENT STATUS TOKEN
`P07A_9_OF_9_PREVIOUS_BASELINE_FRESH_VERIFIED__D1_D2_DB59_REASSEMBLY_EXACT__PRIOR_CLIENTERROR_NOT_REPRODUCED__FULL_CONTEXT_RECOVERY_ALIGNED__RFV2_EXACT_REPAIRED_SOURCE_NOT_LOCATED__CONTROLLED_RECOVERY_REIMPLEMENTATION_REQUIRED__CURRENT_PHYSICAL_AUTHORITY_MISSING__R140_HARD_BLOCK`
