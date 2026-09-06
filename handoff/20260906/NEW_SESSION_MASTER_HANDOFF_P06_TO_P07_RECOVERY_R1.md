# Literary OS — New Session Master Handoff: P06 Closure → P07 Recovery R1
Date: 2026-09-06
Role: authoritative human-readable handoff for a new ChatGPT session after the current session/container interruption.
Classification: RECOVERY / PREFORMAL / DEVELOPER-HUB AUTHORITY SUPPORT

## 0. Why this handoff exists
The previous session completed substantial P07 preformal engineering/research work but did not physically propagate every meaningful change into the canonical 5-Part / 9-Package delivery after each task. This created a recovery debt: scientific observations, defect repairs, and preregistration decisions advanced faster than the developer-held binary package authority.

This document exists to prevent a new session from repeating finished investigation, silently losing repairs, or falsely treating the old physical package baseline as the current repaired engine.

The operating correction from now on is mandatory:
`Meaningful task -> result/status seal -> 5-Part/9-Package propagation -> SHA/CRC/manifest/trust-root audit -> Developer Hub update -> only then physical closure.`

If the artifact/container backend is unavailable, the task may be scientifically checkpointed but MUST remain `PHYSICAL_CLOSURE_PENDING` and the next session must finish package propagation before starting a new scientific task.

## 1. Non-negotiable current authority state
- Formal scored count: 137.
- Latest formal scored authority: R138.
- R140: 0 attempts / 0 outputs / 0 scores.
- ENG:R47 Production: immutable.
- P06: COMPLETED / PHYSICALLY CLOSED.
- P07: ACTIVE PREFORMAL / NOT COMPLETE.
- DB59 frozen reference SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- DB64 is a separate living DB and must not silently replace DB59 in this lineage.
- Current repaired 5-Part / 9-Package physical authority: DOES NOT YET EXIST.
- Developer-held previous 5-Part / 9-Package baseline: EXISTS and is the recovery starting point only.
- Official current-authority R-F CP1 live outputs / Provider Receipts: 0 / 0.
- CT nonformal live/API evidence exists separately and must not be relabeled CP1 or Formal R140.
- R140 remains HARD BLOCK.

## 2. P06 → P07 lineage: what happened
### 2.1 P06
P06 is the last phase that reached physical closure. Treat P06 as closed authority and do not reopen it merely because P07 later exposed runtime/adoption defects.

### 2.2 P07 original purpose
P07 began as the next preformal phase for preparing production-scale promotion qualification before Formal R140. Its purpose was not just to generate prose; it was to prove that the current Literary OS candidate actually consumes the researched structures/data, survives provider-boundary behavior, and can be compared fairly against immutable ENG:R47.

P07 accumulated several preformal layers:
- retrieval/database consumption validation;
- semantic planning path verification;
- surface-craft engineering validation;
- provider-boundary/fail-closed validation;
- live-parity preparation;
- eventual production-scale R140 preparation.

The problem was not that all these activities were invalid. The problem was that the preformal hierarchy became insufficiently explicit, and physical package propagation did not keep pace with scientific/engineering progress.

### 2.3 CT track position
Claude/CT performed an independent confirmatory/diagnostic track using materials handed over from GPT. CT-17 is important because it produced nonformal OpenAI Live/API evidence from a recent candidate path, but it is NOT an official R-F CP1 and NOT Formal R140.

Do NOT infer that CT01–CT17 form one formally preregistered numbered experiment series unless the underlying CT files explicitly prove that. The safe interpretation is: CT is an independent confirmatory track with multiple checks; CT-17 is a nonformal Live baseline relevant to the pre-repair engine state.

CT-17 is especially useful because it appears to have exercised recent candidate planning/surface structures while DB59 semantic retrieval was effectively absent. It is therefore a PRE-REPAIR LIVE BASELINE, not proof of the fully repaired candidate.

## 3. The major defect discovered by Claude/CT
### 3.1 A-1 — DB59 was present in evidence but not in literary semantic conditioning
The then-current C2 R39 path could read/hash DB59-derived material and produce evidence-chain activity while repeatedly ending in `NO_RETRIEVAL`. Thus donor semantics did not reliably reach the LLM semantic-planning input.

This invalidated the earlier broad claim that module/runtime coverage alone proved DB adoption completeness.

New adoption standard is mandatory:
`Value changes -> Consumer receives -> selected donor/semantic payload changes -> LLM provider input changes -> downstream behavior changes -> Receipt/Trace proves propagation.`

### 3.2 A-2 — positive DB dependency contract had been lost
A historical test asserted that changing the selected DB member should change semantic provider input. The current pre-repair suite instead contained low-confidence behavior asserting semantic input could remain equal, and no positive archive-to-`USE_RETRIEVAL` end-to-end contract closed the gap.

### 3.3 B-1 — current R11 CP1 runner did not implement successful CP1
`rf_live_parity_runner.py` intentionally HOLDed; no successful current-authority paired CP1 branch existed.

A historical P07 PRE09 runner design (`p07_pre09_live_craft_parity.py`) exists and should be restored/integrated rather than inventing a new CP1 from scratch.

### 3.4 B-2 — local regressions were not Live Provider evidence
The 181/181 regression was local/mock/TestDouble engineering evidence. It must never be relabeled Live OpenAI validation.

### 3.5 B-3 and hygiene
- Historical C2 R38/R39 manifest mismatch was corrected at the previous baseline level.
- Legacy/history dual entrypoints remain a drift risk.
- Blind Coordinator Secret must be physically separated before Formal R140.
- Build/test cache hygiene must be deterministic.

## 4. Repairs observed during the interrupted P07/RFV2 work
These repairs were observed in the working state before the container failed. They are NOT yet physically closed and MUST be freshly reverified from recovered/reconstructed bytes.

### 4.1 Retrieval contract repair
Repair direction:
- restore R37/R38-compatible work-level TF-IDF/cosine retrieval under current R0C THICK-only membership;
- analyzer `char_wb`, ngram 2–5, cosine, top-k=4;
- historical-style confidence bands: HIGH >= 0.13, MEDIUM >= 0.10 and < 0.13, LOW < 0.10 -> fallback;
- remove top1-top2 margin as a hard gate; keep margin diagnostic only;
- use bounded THICK-derived functional work profiles instead of flattening full payload prose into retrieval tags;
- separate diagnostic confidence/margin from literary semantic payload so irrelevant DB changes cannot perturb LLM input through score metadata alone;
- wire the actual verified archive path to the repaired retrieval route;
- Python literary prose generation remains 0.

### 4.2 Observed repaired-state results
- DB59 retrieval source observed: 1,097 eligible THICK members / 10,784 records.
- Six development cases observed `USE_RETRIEVAL`.
- Direct DB59 vs Frozen Retrieval Index retrieval equivalence observed: 6/6.
- CASE-01 DB59 donors observed in `SEQUENCE_PLAN` semantic provider input.
- Selected donor mutation changes semantic provider input.
- Irrelevant unselected donor mutation does not change semantic provider input.
- Nonhistorical regression observed after new dependency tests: 185/185 PASS.

Observed evidence hashes:
- Frozen Retrieval Index: `d9b50787676aa0750ba0b519b2537dedafa71807c72edef78c659ddfb6ddf419`.
- Index equivalence/tamper audit: `81ca599ead072c7da9291450573b5a2c782d14d2b3b5514e5a7b3265b155fd23`.
- CASE-01 DB59 -> semantic provider input evidence: `ab60a39cc9ce8fe30835b7b3589566f7a2281af6c49957048eb2268531d95f4f`.

These hashes are recovery observations, not substitutes for fresh verification after package reconstruction.

### 4.3 Additional defects found while repairing
- D-1: repaired retrieval algorithm existed but the real verified archive path initially still called the old route. Working-state rewire observed.
- D-2: first work-profile restoration used too much THICK full text. Working-state bounded profile correction observed.
- D-3: diagnostic confidence/margin leaked into literary semantic input. Working-state separation observed.
- D-4: Frozen Index query path repeated expensive deep verification. Working-state separation of build/audit verification vs query-time authority checks observed.
- D-5: duplicate amendment numbering branches appeared. Governance correction was documented; a new session must follow the latest checkpoint and not merge abandoned branches silently.

## 5. What is still open
### 5.1 Physical package closure — OPEN
The repaired working state has not been physically propagated into the canonical 9 packages. This is the first recovery priority.

### 5.2 Exact repaired source bytes — RECOVERY RISK
The repaired source bytes were not independently confirmed as a complete durable GitHub code snapshot before container failure.

Therefore:
- If exact repaired artifacts survive externally, verify them by hashes/checkpoints and reuse them.
- If they do not survive, reconstruct under the documented preregistration/amendment/repair contract.
- Such reconstruction must be labeled CONTROLLED RECOVERY/REIMPLEMENTATION, not byte-identical restoration.
- Do not tune thresholds/prompts/donors/rubrics to reproduce desired scores.

### 5.3 CP1 current-authority restoration — HARD OPEN
Required:
- recover historical paired CP1 runner design;
- integrate current DB59/Frozen Retrieval Index route into Engine arm;
- integrate current R-E surface-craft contract;
- integrate current R-FV provider request/response/model/hash/retry/receipt integrity;
- maintain arm symmetry and fail-closed live gating;
- run TestDouble before real OpenAI;
- reseal 9 packages again after CP1 changes runtime bytes.

### 5.4 Official R-F Live — NOT STARTED
No current-authority official CP1/R-F Live Provider Receipt exists yet.

### 5.5 Formal path after recovery
Only after current-authority preformal closure:
`R-F real paired live -> R-G freeze -> fresh formal sample -> revised R140 preregistration -> new G0 -> Formal R140`.

## 6. Developer-held previous physical baseline: exact recovery start
The developer/user currently holds the following nine previous physical baseline files. A new session should ask for all nine uploads before rebuilding current authority.

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

Canonical package accounting:
`CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2 = 9 packages`.

C2 reconstruction contract:
`C2-A || C2-B` must reconstruct previous C2 R39 SHA256
`d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`.

Previous C2 R39 observed properties:
- 311,653,716 bytes;
- 3,610 ZIP entries;
- CRC PASS;
- nested ZIP 155/155 PASS;
- runtime overlay 520 files;
- previous nonhistorical regression 181/181 PASS.

These nine files are `PREVIOUS_PHYSICAL_BASELINE`, NOT current repaired authority.

## 7. Exact new-session recovery order
### Phase 0 — read authority before touching code
Read, in order:
1. `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`
2. `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`
3. this handoff
4. `DEVELOPER_HUB_FULL_RECOVERY_RESEARCH_DOSSIER_R2.md`
5. `CLAUDE_CT_DEFECT_CLOSURE_MATRIX_R1.md`
6. latest Atomic Checkpoint
7. RFV3 preregistration

### Phase 1 — reconstruct previous physical baseline
- upload all nine developer-held baseline files;
- verify each SHA256;
- CRC/duplicate/unsafe/nested ZIP audits;
- reconstruct C2-A + C2-B and verify C2 R39 SHA;
- label the result `PREVIOUS_PHYSICAL_BASELINE`.

### Phase 2 — recover/reconstruct RFV2 repaired source
- inspect whether exact repaired artifacts survived in uploads/external checkpoints;
- if yes, verify and use exact artifacts;
- if no, controlled reconstruction under frozen repair contract;
- never silently redesign retrieval based on desired output.

### Phase 3 — fresh mechanical revalidation before craft generation
Required:
- DB59 SHA exact;
- 1,097/10,784 source membership as applicable;
- six development retrieval cases complete without implementation-induced universal fallback;
- CASE-01 donor semantics reach provider input;
- selected donor mutation changes semantic input;
- irrelevant unselected donor mutation does not;
- direct DB59 vs Frozen Index equivalence;
- outer/inner tamper HOLD;
- full nonhistorical regression PASS;
- source-cutoff violation 0;
- Python literary prose 0.

### Phase 4 — first current 9-package reseal
Propagate all recovered/repaired code, amendments, evidence, manifests, pointers, and claim-boundary corrections into the canonical 9-package structure.

Do not assume only C2 changes. For every package either:
- produce new bytes/new SHA, or
- prove unchanged byte identity.

Required audit:
- 9/9 present;
- SHA256 recorded;
- CRC PASS;
- duplicate path 0;
- unsafe path 0;
- nested ZIP PASS;
- C2-A + C2-B exact reconstruction;
- DB59 authority correct;
- secrets 0;
- Manifest / Trust Root / Developer Hub / Session Recovery Pointer all agree.

Only then may the repaired state be called `CURRENT_PHYSICAL_AUTHORITY`.

### Phase 5 — CP1 restoration and second reseal
Restore/integrate current-authority paired CP1, run TestDouble/fail-closed suite, then reseal/audit all affected packages again because runtime bytes changed.

### Phase 6 — official R-F Live
Only after Phase 5 physical closure, run official paired OpenAI CP1/R-F Live with identical provider/model/settings across arms and real Provider Receipts.

### Phase 7 — RFV3 causal re-pretest
RFV3 was preregistered but has 0 outputs.
Frozen arms:
- A = SUMMARY ONLY
- B = PRE-REPAIR ENGINE / NO_RETRIEVAL
- C = RFV2 REPAIRED ENGINE / DB59 USE_RETRIEVAL
- D = FULL CURRENT CANDIDATE + BIDIRECTIONAL REFINEMENT

Purpose:
- A vs B: runtime information preservation/loss;
- B vs C: incremental DB59 retrieval value;
- C vs D: incremental bidirectional refinement value.

Same work, same EP01–EP05 cutoff, actual EP06 forbidden, same surface settings/output contract, no result-informed tuning.

Whether RFV3 runs before or after official R-F Live must follow the latest sealed prereg/checkpoint. Under the current recovery checkpoint, do NOT start RFV3 generation until pending package closure is resolved.

### Phase 8 — formal path
After current-authority preformal closure and R-F closure:
`R-G Freeze -> fresh formal sample -> revised R140 preregistration -> new G0 -> Formal R140`.

## 8. CT-17 interpretation for the new session
CT-17 is valuable evidence, but use it correctly:
- nonformal;
- real OpenAI/API evidence according to CT bundle, subject to file-level reinspection when uploaded;
- not official CP1;
- not Formal R140;
- useful as pre-repair Live baseline because DB59 semantic retrieval was effectively absent;
- do not infer that all current Literary OS research modules were proven to propagate merely because a recent candidate codebase was used.

If `A E.zip` is uploaded, inspect Provider Receipts, execution logs, retrieval state, scripts, and generated scripts directly before making any detailed CT-17 claim.

## 9. P07 preformal structure to use going forward
To prevent another hierarchy collapse, manage P07 as explicit gates rather than an undifferentiated stream of “pretests”:

Gate P07-A — Authority/Package Recovery
- previous baseline verified;
- repaired source recovered/reconstructed;
- 9-package current authority physically sealed.

Gate P07-B — Retrieval/Propagation Mechanical Closure
- DB59 retrieval mechanics;
- selected/unselected donor causality;
- tamper/equivalence/regression.

Gate P07-C — Candidate Craft Causal Re-pretest
- RFV3 A/B/C/D under frozen conditions;
- diagnostic/nonformal only.

Gate P07-D — CP1 Current-Authority Integration
- paired runner restored;
- TestDouble/fail-closed;
- second 9-package reseal.

Gate P07-E — Official R-F Paired Live
- real OpenAI Provider Receipts;
- identical provider/model/settings;
- no relabeling of CT or mocks.

Gate P07-F — R-G Freeze / Formal Readiness
- candidate freeze;
- fresh formal sample;
- revised R140 prereg;
- G0.

Gate P07-G — Formal R140
- only after all prior gates.

These gate labels are a recovery management structure for future sessions; they do not retroactively rename historical experiments or increase formal count.

## 10. Mandatory per-task packaging rule from this point forward
Every meaningful task must end with one of exactly two states:

### `PHYSICALLY_CLOSED`
- result/status sealed;
- changed bytes propagated to all affected packages;
- unchanged packages proven byte-identical;
- 9-package audit complete;
- Developer Hub/Session Pointer updated.

### `SCIENTIFIC_CHECKPOINT_ONLY__PHYSICAL_CLOSURE_PENDING`
Use only when infrastructure prevents package reconstruction.
Must record:
- what changed;
- exact evidence/hashes known;
- what was not verified;
- formal/R140 counters;
- package propagation debt;
- next mandatory action.

Do not begin the next scientific task while a previous completed task remains physically unpropagated unless an explicit sealed exception says why.

## 11. Files the user should upload into the next session
Minimum for executable recovery:
1. all nine developer-held previous physical baseline packages;
2. `CT_TO_GPT_ADDENDUM7_C2R39_VERIFICATION_AND_DEFECT_RECOMMENDATION_20260906.zip`;
3. corresponding CT Markdown;
4. `A E.zip` if CT-17 comparison is needed;
5. any RFV2 repaired source/evidence artifacts that survived outside the failed container;
6. this handoff or GitHub path/commit;
7. latest Developer Hub/Session Recovery pointers if connector access is unavailable.

## 12. Hard prohibitions for the new session
- Do not call previous 9-package baseline the current repaired authority.
- Do not claim Claude/CT defects are fully closed.
- Do not call local/mock regression Live Provider evidence.
- Do not relabel CT-17 as CP1.
- Do not start Formal R140.
- Do not mutate ENG:R47 Production.
- Do not silently substitute DB64 for DB59.
- Do not use actual EP06/post-cutoff source as answer key.
- Do not tune repaired retrieval to desired craft outcomes.
- Do not increment formal count during preformal recovery.

## 13. Current final status tokens
`P06_COMPLETED_PHYSICALLY_CLOSED`
`P07_ACTIVE_PREFORMAL_NOT_COMPLETE`
`FORMAL_COUNT_137`
`R140_0_ATTEMPTS_0_OUTPUTS_0_SCORES`
`DB59_FROZEN_AUTHORITY`
`CLAUDE_CT_DEFECTS_PARTIALLY_REPAIRED_NOT_FULLY_CLOSED`
`RFV2_REPAIRED_STATE_OBSERVED_REVERIFY_FROM_BYTES_REQUIRED`
`RFV3_PREREGISTERED_0_OUTPUTS`
`CP1_CURRENT_AUTHORITY_RESTORATION_OPEN`
`CURRENT_REPAIRED_9_PACKAGE_AUTHORITY_MISSING`
`CONTAINER_CLIENTERROR_INFRASTRUCTURE_HOLD`
`R140_HARD_BLOCK`

## 14. First instruction to the next ChatGPT session
Do not generate new drama output first.
First recover the developer-held nine physical baseline packages, re-establish the repaired current authority under the frozen RFV2 contracts, run fresh mechanical validation, and physically reseal the current 5-Part / 9-Package set. Then restore CP1 and continue the P07 gate sequence. Preserve all claim boundaries and counters exactly unless a later sealed artifact proves otherwise.
