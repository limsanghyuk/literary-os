# Literary OS — Developer Hub Full Recovery & Research Dossier R2
Date: 2026-09-06
Role: detailed developer-facing recovery authority for a new session when the current container/artifact backend is unavailable.

## 0. Critical authority boundary
This dossier does NOT claim that the current repaired RFV2/RFV3 runtime has already been physically resealed into the canonical 5-Part / 9-Package delivery.

Current status:
- Formal scored count: 137
- Latest formal scored authority: R138
- R140: 0 attempts / 0 outputs / 0 scores
- ENG:R47 Production: immutable
- DB59 frozen reference SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- P07: active preformal / not complete
- RFV3 generation outputs: 0
- Container/artifact backend: `ClientError` / Infrastructure HOLD
- Current repaired 9-package reseal: NOT COMPLETED
- CP1 current-authority restoration: OPEN
- R140: HARD BLOCK

A new session must distinguish:
1. PREVIOUS_PHYSICAL_BASELINE = the nine files physically held by the developer/user;
2. WORKING-STATE_REPAIR_OBSERVATIONS = repairs/results observed in the failed-container session;
3. CURRENT_PHYSICAL_AUTHORITY = does not exist until the repaired bytes are rebuilt, audited, and resealed.

## 1. Developer-held previous physical baseline — exact 5 Parts / 9 Packages
The developer currently has the following physical baseline files. Verify these SHA256 values before using them.

1. CONTROL R39
   SHA256 `47fe62c8acf3401c69174c77c420be0d106703888def2ea2b073a9491b14eeeb`
2. PART-A R38
   SHA256 `9443d103de0eafd6fb063d1ba860a90e7be32d40227980d867f79808526696b1`
3. PART-B1 R10
   SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
4. PART-B2 R39
   SHA256 `f396d7fe583f6267c3b17735e690be5e50c35d48f2253ae7ea12a71779ecc920`
5. PART-C1 / C PART 1 OF 3 — Runtime Core ZIP
   SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
6. PART-C2-A / C PART 2 OF 3 — C2 Binary A
   SHA256 `6208a1513550525234b85b63103fb64a8c3bca8405a91c019df243a28b8ff975`
7. PART-C2-B / C PART 3 OF 3 — C2 Binary B
   SHA256 `eac1bb5b424c92c6ae97924d09864412b222e581d34b062e0818e4105ee89f5f`
8. PART-D1 R10
   SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
9. PART-D2 R10
   SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

Canonical accounting is exactly:
CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2 = 9 packages.

PART-C is exactly C1 + C2-A + C2-B.

### C2 reconstruction contract
Concatenate C2-A bytes followed immediately by C2-B bytes:
`C2-A || C2-B`

Expected previous C2 R39 authority SHA256:
`d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`

Previous C2 R39 properties observed before the current repair session:
- bytes: 311,653,716
- ZIP entries: 3,610
- outer CRC: PASS
- nested ZIP audit: 155/155 PASS
- runtime overlay: 520 files
- previous nonhistorical regression: 181/181 PASS

These nine hashes are PREVIOUS_PHYSICAL_BASELINE only. They do not yet include all RFV2/RFV3 working-state repairs described below.

## 2. What Claude/CT found
Primary CT evidence to upload to a new session when available:
- `CT_TO_GPT_ADDENDUM7_C2R39_VERIFICATION_AND_DEFECT_RECOMMENDATION_20260906.zip`
  reported/verified SHA256 `e661d0134af59deeb3ad6e81e62ac17881bce255ed833dcc6714b9f47542ec5f`
- `CT_TO_GPT_회신_부록7_C2R39검증_결함권고_20260906.md`
- `A E.zip` for CT nonformal live/API evidence.

### CT A-1 — DB59 retrieval did not reach LLM semantic planning
Observed pre-repair state:
- retrieval gate repeatedly returned `NO_RETRIEVAL`;
- DB59 bytes were read/hashed and appeared in evidence chains, but selected donor semantic content did not reach the LLM semantic planning input;
- R0C had actual 10,784 records / 1,097 members and recorded both arms `NO_RETRIEVAL` around confidence 0.42;
- the archive normalization hardcoded `owner_group_roles=["ANY"]`, `macro_functions=[]`, and used flattened payload text as retrieval functions, making the current scoring contract unsuitable for actual corpus use.

Scientific correction:
`Module exists/called/trace exists` is no longer sufficient proof of adoption.
Required adoption standard is:
`Value changes -> Consumer receives -> selected donor/semantic payload changes -> LLM provider input changes -> downstream behavior changes -> Receipt/Trace proves propagation`.

### CT A-2 — DB dependency test inversion
Historical contract:
selected DB member change -> semantic provider input changes (`assertNotEqual`).

Current pre-repair test had been changed to a low-confidence contract in which DB changes did not change semantic input (`assertEqual`) and there was no positive archive-to-USE_RETRIEVAL end-to-end test.

### CT B-1 — CP1 paired Live runner missing
Current R11 `rf_live_parity_runner.py` had no successful CP1 branch; terminal paths HOLDed/returned 2.
Historical P07 PRE09 material contains an earlier paired runner design (`p07_pre09_live_craft_parity.py`), but it has not yet been integrated into the current RFV2/RFV3 authority.

### CT B-2 — 181 regression was not Live Provider validation
The regression suite used mocks/test doubles. This is engineering evidence only, not real OpenAI Provider evidence.

### CT B-3 — historical R38/R39 manifest drift
The old C2 R38/R39 mismatch was later corrected at the previous physical baseline level. The new issue is different: the current RFV2/RFV3 repaired state has not yet been propagated into a new 9-package physical authority.

### CT additional hygiene findings
- legacy/history entrypoint duplication remains a drift risk;
- Blind Coordinator Secret must be physically separated before Formal R140;
- regression command/history handling must be explicit;
- no secret/API key should be embedded in packages.

## 3. Working-state repairs observed in the current session
The following were observed before the local container/artifact backend failed. These are NOT yet physically closed and MUST be freshly reverified from recovered/reconstructed bytes.

### 3.1 Retrieval contract repair
Repair direction:
- restore an R37/R38-compatible work-level TF-IDF/cosine retrieval concept under current R0C THICK-only source membership;
- bounded functional work profiles instead of flattening all payload text;
- historical-style confidence bands: HIGH >= 0.13, MEDIUM >= 0.10 and < 0.13, LOW < 0.10 -> fallback;
- top1-top2 fit margin retained as diagnostic, not a hard gate;
- diagnostic confidence/margin separated from literary semantic payload;
- actual verified archive path rewired to the repaired retrieval route;
- Python literary prose generation remains 0.

Observed results:
- actual DB59 source: 1,097 eligible THICK members / 10,784 records;
- six historical development cases observed `USE_RETRIEVAL`;
- each development case selected actual donors;
- Direct DB59 vs Frozen Retrieval Index semantic retrieval equivalence: 6/6 observed;
- CASE-01 DB59 donors observed in `SEQUENCE_PLAN` provider input;
- selected donor mutation changes semantic provider input;
- irrelevant unselected donor mutation does not change semantic provider input.

Observed evidence hashes:
- Frozen Retrieval Index SHA256: `d9b50787676aa0750ba0b519b2537dedafa71807c72edef78c659ddfb6ddf419`
- index equivalence/tamper audit SHA256: `81ca599ead072c7da9291450573b5a2c782d14d2b3b5514e5a7b3265b155fd23`
- CASE-01 DB59 -> semantic provider input evidence SHA256: `ab60a39cc9ce8fe30835b7b3589566f7a2281af6c49957048eb2268531d95f4f`

Observed nonhistorical regression after RFV2 dependency tests: 185/185 PASS.

### 3.2 Additional defects discovered while repairing
D-1: repaired algorithm existed but actual verified archive path initially still called old retrieval.
Repair observed: rewired verified archive path.

D-2: first restoration concatenated too much THICK full text instead of bounded functional profile.
Repair observed: bounded THICK-derived functional work profile.

D-3: diagnostic confidence/margin leaked into LLM semantic payload so irrelevant DB changes could perturb semantic input hashes.
Repair observed: selection diagnostics kept in gate/receipt evidence, removed from literary semantic conditioning payload.

D-4: Frozen Index query path repeated deep CRC/decompression/per-payload hashing and became too slow.
Repair direction observed: deep verification at build/audit; query-time verification preserves outer/member SHA and authority binding.

D-5: duplicate amendment numbering branches appeared in the interrupted repair session.
Governance correction was documented; a new session must read the latest checkpoint and must not merge abandoned amendment branches silently.

## 4. What is NOT yet finished
### 4.1 CP1 current-authority restoration — HARD OPEN
Required action:
- recover historical paired CP1 runner design;
- integrate it with current repaired DB59/Frozen Retrieval Index path;
- integrate current R-E surface craft contract;
- integrate current R-FV request/response/model/hash/retry/receipt integrity contract;
- preserve Reference and Engine arm symmetry;
- no live call without explicit credential/allow-live gates.

Required local/TestDouble checks before real Live:
- exactly two arms;
- same OpenAI Responses API model/settings across arms;
- expected semantic stages per arm;
- Engine arm proves DB59 donor propagation;
- no-key -> HOLD, live calls 0;
- no explicit allow-live -> HOLD, live calls 0;
- returned model mismatch -> BLOCK/HOLD;
- request/response hash mismatch -> BLOCK/HOLD;
- malformed/refusal/429/5xx/timeout handled under current R-FV contract;
- failed attempts never become trusted Provider Receipts;
- Python literary prose bytes = 0.

Official R-F CP1 live outputs / Provider Receipts remain 0.
CT nonformal live/API evidence is separate and must not be relabeled CP1.

### 4.2 Physical 5-Part / 9-Package reseal — HARD OPEN
No current repaired package set exists yet.
All nine previous files remain previous baseline only.

### 4.3 Fresh verification from exact resealed bytes — HARD OPEN
After reseal, rerun:
- DB59 6-case retrieval audit;
- Direct DB59 vs Frozen Index equivalence;
- Frozen Index outer/inner tamper HOLD tests;
- selected/unselected donor propagation tests;
- full nonhistorical regression;
- package CRC/duplicate/unsafe/nested ZIP audits;
- C2-A || C2-B reconstruction;
- Manifest/Trust Root consistency.

### 4.4 Hygiene before Formal R140
- legacy entrypoint/history drift cleanup or hard quarantine;
- physical separation of blind Coordinator Secret from execution runtime;
- current-authority CP1 + official R-F Live closure;
- R-G freeze;
- fresh formal sample;
- revised R140 preregistration;
- new G0 physical seal.

## 5. Exact package recovery procedure for a new session
The new session MUST do this before new scientific generation if packaging remains pending.

### Phase P0 — collect developer-held files
Ask the developer/user to upload all nine previous physical baseline files listed in Section 1.
Also upload CT Addendum 7 and any RFV2 repair artifacts/checkpoints that survived outside the failed container.

### Phase P1 — verify previous baseline
1. SHA256 each of the nine files against Section 1.
2. For ZIP packages: outer CRC PASS, duplicate paths 0, unsafe paths 0.
3. Concatenate C2-A then C2-B.
4. Verify reconstructed C2 SHA256 = `d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`.
5. Verify reconstructed C2 ZIP structure and prior overlay baseline.
6. Label these files `PREVIOUS_PHYSICAL_BASELINE`; do not call them repaired authority.

### Phase P2 — recover/reconstruct RFV2 repaired source
Critical limitation: the current session's repaired source bytes have NOT been independently confirmed as a complete durable GitHub code snapshot. Therefore a new session must NOT claim byte-identical repaired-code recovery unless those exact source artifacts are recovered from surviving external files.

If exact repaired source artifacts survive, verify their hashes/checkpoints and use them.
If they do not survive, reconstruct the repair under the documented preregistration/amendment contracts and treat this as a controlled recovery/reimplementation, not byte-identical restoration.

Required repair behavior is Section 3, not an arbitrary redesign.
No result-informed threshold/prompt/donor/rubric tuning is allowed.

### Phase P3 — rebuild Frozen Retrieval Index from DB59
1. Verify DB59 SHA256 = `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
2. Use the frozen source cutoff/membership rules.
3. Build the bounded functional retrieval index.
4. Record new index SHA and provenance.
5. Do not silently substitute DB64 or another DB.

### Phase P4 — reverify RFV2 mechanically
Before craft generation:
- six development cases must complete retrieval without implementation-induced universal fallback;
- CASE-01 donor semantic payload must reach provider input;
- selected donor mutation changes input;
- irrelevant unselected donor does not;
- source cutoff violations 0;
- tamper tests HOLD;
- full nonhistorical regression PASS.

If the reconstructed implementation does not reproduce the observed repair behavior, classify FAIL/HOLD and preserve it. Do not tune against desired outcomes.

### Phase P5 — propagate current state into 9 packages
Determine which package members actually change; do not assume only C2 changes.
Rebuild all nine delivery artifacts or otherwise prove unchanged-byte-identity for any unchanged package.
PART-C remains exactly C1 + C2-A + C2-B.

Required audits:
- 9/9 expected artifacts present;
- per-package SHA256;
- CRC PASS;
- duplicate 0;
- unsafe path 0;
- nested ZIP PASS;
- C2-A + C2-B exact current C2 authority reconstruction;
- DB59 authority unchanged unless separately versioned;
- no secrets;
- Manifest, Trust Root, Current Developer Hub and Current Session Recovery Pointer all agree.

Only after this can the repaired state be called CURRENT_PHYSICAL_AUTHORITY.

### Phase P6 — CP1 integration and second reseal
CP1 implementation changes runtime bytes. Therefore after CP1 current-authority integration/TestDouble verification, rebuild/reseal the 9 packages AGAIN and audit them again before official R-F Live.

## 6. Recent research and experiment program — purpose/content/method
### RFV2 — Retrieval/Propagation Recovery Re-pretest
Purpose:
Repair the discovery that DB59 was being read and hashed but was not reliably changing the LLM semantic planning input.

Core research questions:
1. Can actual DB59 records reach `USE_RETRIEVAL` under a justified retrieval contract?
2. Can selected donor changes causally change semantic provider input?
3. Can irrelevant unselected DB changes remain causally inert?
4. Can retrieval remain source-safe and tamper-evident?
5. Can the entire repaired route pass regression without Python literary prose generation?

Method:
- freeze source/DB authority before repair;
- repair retrieval feature construction/route wiring under documented amendments;
- use actual DB59 1,097-member/10,784-record source;
- compare direct DB59 and a frozen derived retrieval index;
- run positive and negative donor-dependency tests;
- keep scoring diagnostics outside literary semantic payload;
- run tamper/fail-closed tests;
- run full nonhistorical regression;
- no formal count increment.

Observed working-state result:
mechanical DB59 -> selected donor -> LLM semantic input propagation was observed, but physical package closure was not completed because the container failed.

### RFV3 — A/B/C/D Causal Re-pretest
Authoritative preregistration:
`handoff/20260906/P07_RFV3_ABCD_CAUSAL_REPRETEST_PREREG_R1.md`
commit `07c256a84718c0b8f4017c383c174c4bcf3a8d95`.

Purpose:
Resolve why direct SUMMARY prompting sometimes outperformed the pre-repair engine and separate the incremental effects of runtime mediation, repaired DB59 retrieval, and bidirectional refinement.

Frozen arms:
A — SUMMARY ONLY
B — PRE-REPAIR ENGINE / NO_RETRIEVAL
C — RFV2 REPAIRED ENGINE / DB59 USE_RETRIEVAL
D — FULL CURRENT CANDIDATE + BIDIRECTIONAL REFINEMENT

Primary causal comparisons:
- A vs B: runtime information preservation/loss;
- B vs C: incremental craft value of actual DB59 retrieval;
- C vs D: incremental value of bidirectional hierarchy refinement.

Common controls:
- same work;
- EP01–EP05 only;
- actual EP06 forbidden;
- same target fresh synthetic EP06;
- same surface realization contract/settings;
- same scene/output length contract;
- no arm-specific fallback;
- no result-informed tuning;
- Python literary prose = 0.

Primary development case:
CASE-01 `101번째프로포즈`, because CT-17 gives a historical pre-repair Live baseline and R-F fixtures already exist. This is diagnostic/nonformal and not a future Formal R140 sample.

Phases:
V1 — A/B/C/D virtual/local semantic planning with exact input hashes, retrieval decisions, donor ids/hashes, hierarchy receipts, final semantic plans.
V2 — same-size surface realization sample for all arms, with blinded craft evaluation.
If a full broadcast-scale virtual render is available without Python prose, generate equal-size full-episode outputs separately; never mix full-episode and three-scene scores.

Required mechanical checks before craft scoring:
- A: no retrieval;
- B: NO_RETRIEVAL and no DB59 donor semantic content;
- C: USE_RETRIEVAL and proven donor propagation;
- D: all C evidence plus traceable bidirectional refinement or explicit NO_REFINEMENT_TRIGGERED;
- source leak 0;
- surface settings equal;
- required receipt fields fail closed.

Craft axes:
- Causal/Continuity Fidelity
- Episode Architecture
- Ensemble/Ecology
- Dialogue/Scene Craft
- Character Voice Differentiation
- Subtext/Physicalization
- Pacing/Line Economy
- Repetition/Template Resistance
- Unsupported Invention/Future-source Discipline

Interpretation:
- if B < A and C > B: evidence supports runtime information loss plus retrieval recovery;
- if C <= B: mechanical retrieval works but no incremental craft value demonstrated on the case;
- if D > C with fidelity non-regression and real refinement trace: evidence supports incremental refinement value;
- single-case result cannot promote Production.

Current RFV3 state:
preregistered; generation outputs = 0; blocked on pending 9-package physical closure/infrastructure recovery.

### R-F CP1 — next real Live prerequisite
Purpose:
First current-authority paired OpenAI Live smoke before Formal R140.

Reference and Engine arms must use identical Provider/model/settings. Engine must prove current repaired DB59 consumption. Actual Provider Receipts, request/response hashes, model identity, retry ledger and trusted transcript integrity are mandatory.

CP1 is NOT Formal R140 and must not increment the formal experiment count.

### Formal R140 — still future and blocked
Purpose:
Production-scale Promotion Qualification comparing immutable ENG:R47 Production with the fully integrated frozen PRE-R140 candidate as end-to-end systems.

Entry prerequisites:
current-authority preformal repair closure -> CP1/R-F real paired Live closure -> R-G Freeze -> fresh deterministic formal sample -> revised R140 preregistration -> new G0 -> Formal R140.

Do not start R140 directly.

## 7. CT nonformal Live/API evidence boundary
`A E.zip` appears to contain CT nonformal OpenAI Live execution evidence from a pre-repair/no-effective-DB-retrieval condition. It is useful as a PRE-REPAIR LIVE BASELINE after file-level receipt/log/output verification.

It is NOT:
- current R-F CP1;
- Formal R140;
- proof of current repaired DB59 value.

It can be used to contextualize RFV3 A/B/C/D comparisons, not as a substitute for them.

## 8. Authority synchronization rule
The following must always agree:
- `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
- `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`
- latest START_HERE
- latest Atomic Checkpoint
- Delivery Manifest
- Trust Root
- actual 9 package hashes.

Text pointers may advance status, but may NEVER manufacture missing binary authority.

## 9. Immediate resume order for the next new session
1. Read `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`.
2. Read `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`.
3. Read this dossier and `CLAUDE_CT_DEFECT_CLOSURE_MATRIX_R1.md`.
4. Confirm Formal count 137 and R140 0/0/0 unless a later sealed checkpoint proves otherwise.
5. Obtain the developer-held nine previous baseline files and CT evidence packages.
6. Verify all previous baseline hashes and reconstruct C2.
7. Recover exact repaired RFV2 source artifacts if they survived; otherwise perform controlled reconstruction under the documented repair contract and label it as reconstruction.
8. Freshly reproduce RFV2 mechanical evidence.
9. Rebuild and audit the current 5-Part / 9-Package physical authority.
10. Only then continue CP1 integration/TestDouble work.
11. Reseal 9 packages after CP1 code changes.
12. Run official R-F OpenAI paired Live only after those package and credential gates pass.
13. Continue to R-G and later Formal R140 only under the existing sequence.

## 10. Final status tokens
`FORMAL_COUNT_137`
`R140_0_ATTEMPTS_0_OUTPUTS_0_SCORES`
`CLAUDE_CT_DEFECTS_PARTIALLY_REPAIRED_NOT_FULLY_CLOSED`
`RFV2_WORKING_REPAIR_OBSERVED__FRESH_REVERIFY_REQUIRED`
`RFV3_PREREGISTERED__OUTPUTS_0`
`CP1_CURRENT_AUTHORITY_RESTORATION_OPEN`
`PREVIOUS_9_PACKAGE_BASELINE_AVAILABLE_TO_DEVELOPER`
`CURRENT_REPAIRED_9_PACKAGE_RESEAL_PENDING_INFRASTRUCTURE`
`R140_HARD_BLOCK`
