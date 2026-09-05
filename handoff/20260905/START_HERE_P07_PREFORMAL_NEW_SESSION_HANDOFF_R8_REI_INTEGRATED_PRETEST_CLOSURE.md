# Literary OS — P07 New Session Handoff R8 — R-EI Integrated Pretest Physical Closure (2026-09-05)

## Current authority
`R8_REI_INTEGRATED_PRETEST_PHYSICAL_CLOSURE`

- P06: COMPLETED / PHYSICALLY CLOSED.
- P07: ACTIVE PREFORMAL / NOT COMPLETE.
- Formal scored count: 137; latest formal scored: R138.
- R140 formal attempt/output/score: 0/0/0.
- ENG:R47 Production: IMMUTABLE.
- DB59 frozen SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- DB64 remains a separate 98-work Living Analysis Database and must not silently replace DB59.
- R-B Narrative Architecture: CLOSED.
- R-C Decision Architecture: CLOSED.
- R-D Long-Horizon: PHYSICALLY CLOSED.
- R-E Surface Craft: PHYSICALLY CLOSED as Virtual/Local Engineering evidence.
- R-EI End-to-End Integrated Pretest: **PHYSICALLY CLOSED as Virtual/Local Engineering evidence**.

## Why R-EI was needed
R-B~R-E had each passed their own closure, but the integrated pretest found a real remaining wiring gap: individually valid R-B/R-C contracts were not guaranteed to change the verified downstream Sequence/Scene provider-request path. Verified bidirectional refinement, post-render R-E auditing, and R-D evidence-bound state handoff also needed explicit main-path integration.

## Preregistration and attempts
- Preregistration SHA256 `2202e4db49481522185f70b46a6cc2ee972a8e0c14edd31bf5bbc9fd655e2628`.
- Attempt 1: 4 PASS / 5 FAIL / 4 ERROR — preserved.
- Attempt 2 amendment SHA256 `1b94bf6c66fb05f709dabc28bb5f59fe614890cfd57db0ee0a57c6c5af1988a8`.
- Attempt 2: 20/21 PASS — one R82 test-semantics error preserved.
- Attempt 3 amendment SHA256 `ec844229ce06f24bad46cc990c98a0418e42d5d4ce35254fc14df81a5193d3f0`.
- Attempt 3: 21/21 PASS.
- Preseal coverage addendum SHA256 `b74c9aa90e22e71c909035fd9da11eae29fa9d58d5aa4833c91605ab98a1844f`.
- Preseal failure injection: 5/5 PASS.
- Current non-historical regression: 175/175 PASS.
- Final integrated + preseal suite: 26/26 PASS.

## Engine changes adopted
Runtime semantic change is intentionally narrow:
- `literary_os_runtime/p07_pre09_verified_closed_loop.py`

It now binds R-B architecture and R-C decision contracts into actual verified Sequence/Scene provider inputs, checks parent-contract consistency, supports verified minimum-responsible-ancestor bidirectional refinement and same-chain re-lowering, wires R-E post-render surface audits, and binds R-D state handoff to verified planning evidence.

Infrastructure-only addition:
- `tools/session_checkpoint_guard.py`

Python literary prose generation remains 0. ENG:R47 is unchanged.

## Operational ClientError diagnosis and mitigation
Repeated minimal container/python calls intermittently returned `ClientError`, then identical/minimal calls later succeeded without engine/package repair. Local health evidence does **not** support resource exhaustion: disk usage ~33%, inode usage ~1%, memory available ~4.5 GiB at measurement time, and open-file soft limit 16,384. Exact CAAS orchestration/tool-gateway logs are not visible from the sandbox, so the server-side root cause cannot be proven here.

Classification:
`INTERMITTENT_TOOL_GATEWAY_OR_SESSION_BACKEND_FAILURE__LOCAL_RESOURCE_EXHAUSTION_NOT_SUPPORTED__ROOT_CAUSE_NOT_OBSERVABLE`

Mandatory mitigation now adopted:
1. `ClientError` alone never changes experiment PASS/FAIL state.
2. Atomic Health Snapshot + Checkpoint Manifest after prereg/attempt/repair/preseal/package stages.
3. Verify size/SHA256/ZIP CRC immediately after large write or upload.
4. Stage new artifacts on new paths; never mutate prior authority in place.
5. On `ClientError`: minimal health check -> verify last checkpoint -> resume only interrupted stage.
6. Never promote a truncated upload to authority.

Fresh R8 C2 checkpoint verification: 510/510 PASS.

## Current 5-part / 8-package authority
1. CONTROL R36 SHA256 `c743bb7c3e5125eaadf0fb65e6369339250fe1d4946e743f8ec9491e3c018d35`
2. A R35 SHA256 `e603c4c2df06d7447aa30b7fa240cae2e8fa1ef1b777bc27a6ba2afc109f2cc1`
3. B1 R10 unchanged SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
4. B2 R36 SHA256 `8328f261cf0f639e4f0704de8343a3535b3a77499850ebadabf64b8c5a2155f1`
5. C1 R10 unchanged SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
6. C2 R35 SHA256 `07a1f029a88661e2498a4aeaf0706e6e280a62d142189e332b1135582d8d0526`
7. D1 R10 unchanged SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
8. D2 R10 unchanged SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Cross-audit:
- 8/8 outer ZIP SHA/CRC/JSON/Python/path checks PASS.
- 277/277 nested ZIP CRC PASS.
- R8 common root: 36 files byte-identical across CONTROL/A/B2/C2.
- Fresh R8 C2 overlay: 112 Python files, syntax errors 0.
- Fresh R8 C2 execution: 175/175 regression + 26/26 R-EI suite PASS.
- B1+B2 Research Master reassembly PASS SHA256 `392840526d8b7017eda6607aea37597c5e6c7df93fc1bcb951deed2de58d31b0`.
- C1+C2 Narrative Engine Master reassembly PASS SHA256 `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649`.
- D1+D2 DB59 reassembly PASS frozen SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

## Evidence boundary
`Concept Application` != `Virtual/Local Engine Rehearsal` != `Live Provider Engine Execution` != `Formal Controlled Evaluation`.

R-EI is local engineering closure only. It is not Live OpenAI Provider parity, does not increment formal count, and does not establish Formal R140 success or production promotion.

## Next mandatory stage
Proceed to **R-F Live Reference-vs-Actual Engine Craft Parity** only after:
1. secure OpenAI API credential gate,
2. freezing the exact R8 candidate used for live execution,
3. same Provider/Model/Settings for Reference and Engine arms,
4. actual Provider Receipts preserved,
5. failures preserved without hidden repair.

After R-F only: R-G freeze -> fresh formal sample -> revised R140 preregistration -> new G0 -> Formal R140.