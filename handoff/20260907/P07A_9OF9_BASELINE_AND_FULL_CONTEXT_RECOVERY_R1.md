# Literary OS — P07-A 9/9 Baseline + Full Context Recovery Checkpoint R1
Date: 2026-09-07
Classification: RECOVERY CHECKPOINT / NONFORMAL / PREVIOUS_BASELINE_BYTE_CLOSURE / CURRENT_PHYSICAL_AUTHORITY_PENDING

## 0. Purpose
Record the fresh-session completion of all nine previous physical baseline byte audits, preserve the 5-Part / 9-Package relationship contracts, and align the recovered prior-session/research context before RFV2 controlled recovery continues.

This checkpoint does NOT declare the RFV2 repaired runtime physically resealed. It does NOT declare CP1, RFV3, R-F Live, R-G, or Formal R140 complete.

## 1. Frozen scientific authority
- Formal scored count: 137
- Latest formal scored authority: R138
- R140: 0 attempts / 0 outputs / 0 scores
- ENG:R47 Production: immutable
- P06: COMPLETED / PHYSICALLY CLOSED
- P07: ACTIVE PREFORMAL / NOT COMPLETE
- Current gate: P07-A — Authority / Package Recovery
- DB59 frozen SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- DB64: separate Living DB; MUST NOT substitute for DB59 in this lineage
- RFV3 generation outputs: 0
- CP1 current-authority restoration: OPEN
- current repaired 9-package physical authority: MISSING
- R140: HARD BLOCK

## 2. Canonical 5 Parts / 9 Packages relationship
Logical Parts remain five; C2 is split physically, so delivery is nine packages:

1. CONTROL — current control/authority/handoff layer
2. A — control + experiment/preregistration/evaluation/governance layer
3. B — research authority
   - B1 = Research History Recovery Vol.1
   - B2 = Research Current Recovery Vol.2
4. C — engine authority
   - C1 = Runtime Core / production-stable runtime lineage
   - C2-A + C2-B = physical halves of Candidate Engine C2
5. D — DB59/data-learning authority
   - D1 = DB59 Drama Bundle / operational analysis side
   - D2 = Drama Learning / learning-master side

Physical accounting:
`CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2 = 9 packages`.

Cross-package reconstruction contracts freshly confirmed:
- `B1 part001 || B2 part002` -> Research Experiment Learning Recovery Master
  - bytes: 77,347,512
  - SHA256: `392840526d8b7017eda6607aea37597c5e6c7df93fc1bcb951deed2de58d31b0`
  - outer CRC PASS; duplicate=0; unsafe=0; nested ZIP 83/83 PASS
- `C2-A || C2-B` -> previous C2 R39
  - bytes: 311,653,716
  - SHA256: `d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`
  - ZIP entries 3,610; CRC PASS; nested ZIP 155/155 PASS
  - active R11 overlay 520 files; active-overlay `.pyc=0`; `.pytest_cache=0`
- `C1 NarrativeEngine part001 || C2 NarrativeEngine part002` -> Narrative Engine Master
  - bytes: 204,167,926
  - SHA256: `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649`
  - CRC PASS; nested ZIP 313/313 PASS
- `D1 DB59 part001 || D2 DB59 part002` -> frozen DB59 operational analysis authority
  - bytes: 259,756,521
  - SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
  - ZIP entries 38,852; CRC PASS; duplicate=0; unsafe=0; nested ZIP 6/6 PASS

## 3. 9/9 previous physical baseline — fresh byte verification complete
All nine previous-baseline package files have now been freshly checked from the developer-supplied bytes in the healthy failover session:

- CONTROL R39 `47fe62c8acf3401c69174c77c420be0d106703888def2ea2b073a9491b14eeeb` — VERIFIED
- A R38 `9443d103de0eafd6fb063d1ba860a90e7be32d40227980d867f79808526696b1` — VERIFIED
- B1 R10 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98` — VERIFIED
- B2 R39 `f396d7fe583f6267c3b17735e690be5e50c35d48f2253ae7ea12a71779ecc920` — VERIFIED
- C1 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518` — VERIFIED
- C2-A `6208a1513550525234b85b63103fb64a8c3bca8405a91c019df243a28b8ff975` — VERIFIED
- C2-B `eac1bb5b424c92c6ae97924d09864412b222e581d34b062e0818e4105ee89f5f` — VERIFIED
- D1 R10 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504` — VERIFIED
- D2 R10 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4` — VERIFIED

Accounting:
`9/9_COLLECTED__9/9_FRESH_VERIFIED__PREVIOUS_PHYSICAL_BASELINE_BYTE_CLOSURE_COMPLETE`.

Important claim boundary:
These are still `PREVIOUS_PHYSICAL_BASELINE`. They are NOT the current repaired RFV2 physical authority.

## 4. D1/D2 isolated failover result
The fresh-session isolation sequence remained healthy through D1 and D2.

D1:
- bytes 138,011,573
- SHA exact to expected baseline
- 25 top-level entries
- top-level CRC PASS
- duplicate path 0
- unsafe path 0
- nested ZIP 1/1 PASS
- post-D1 `/bin/true`, Python, `/mnt/data` probe PASS

D2:
- bytes 173,393,886
- SHA exact to expected baseline
- 59 top-level entries
- top-level CRC PASS
- duplicate path 0
- unsafe path 0
- nested ZIP 1/1 PASS
- post-D2 `/bin/true`, Python, `/mnt/data` probe PASS

Therefore the prior-session `ClientError` did not reproduce after B1, B2, C1, C2, D1, or D2 processing in this failover session. No supplied package is supported as the corrupt cause from the fresh audits. The exact platform/root cause remains unproven.

## 5. Exact RFV2 repaired-source survival audit after all nine files were available
The nine supplied baseline packages were searched for the known interrupted-session RFV2 repaired-state evidence hashes:
- Frozen Retrieval Index: `d9b50787676aa0750ba0b519b2537dedafa71807c72edef78c659ddfb6ddf419`
- Index equivalence/tamper audit: `81ca599ead072c7da9291450573b5a2c782d14d2b3b5514e5a7b3265b155fd23`
- CASE-01 DB59 -> semantic provider input evidence: `ab60a39cc9ce8fe30835b7b3589566f7a2281af6c49957048eb2268531d95f4f`

Exact-string hits in the supplied package text/code surfaces: 0 / 0 / 0.

Historical/current retrieval code and PRE09 paired-live artifacts are present, including `p07_pre09_live_craft_parity.py` and current `rf_live_parity_runner.py`, but this does not establish survival of the exact interrupted-session RFV2 repaired implementation.

The current C2 previous baseline remains pre-RFV2 with the old retrieval behavior, so it MUST NOT be relabeled as the repaired engine.

Current recovery mode therefore remains:
`CONTROLLED_RECOVERY_REIMPLEMENTATION`
unless an exact interrupted-session artifact is later independently found and hash/checkpoint verified.

No result-informed tuning toward historical 6/6 or 185/185 is allowed.

## 6. Prior-session conversation and research-context recovery
The two prior-session conversation records plus the current pasted recovery synthesis were reread and aligned with the durable Developer Hub / Recovery Dossier.

Temporal supersession rule:
- Older session states and “next task” statements are historical snapshots only.
- Later checkpoints, defect audits, clean revalidations, and current pointers supersede earlier headlines where they conflict.
- Failure attempts remain part of provenance and are not deleted.

Recovered high-level research evolution:
1. Scene/Sequence control
2. Retrieval scale/depth and boundary
3. Episode planning / selector-controller / thread-closure state
4. Hierarchy, blueprint, multi-episode rollout
5. DB semantic consumption and entity/relationship state
6. Ensemble/social ecology
7. Series -> Episode -> Sequence -> Scene hierarchy
8. Broadcast-scale realization
9. Surface craft / renderer / voice
10. External generalization, clean replication, and metrology closure

Critical current interpretation examples:
- R41/P01: Ensemble causal ownership effect cleanly reproduced; tonal add-on did not.
- R42/P02: Blueprint depth and mismatch harm reproduced; incremental Thread Binding primary gate failed because implementation fidelity was insufficient.
- R103/P03: iterated clean engineering revalidation PASS after preserving failed attempts and adding thread-consumer/texture guards.
- R121/P04: broadcast-scale clean revalidation PASS after three preserved failures and a fourth passing run.
- R129-R132: strong internal same-session signals, but not sufficient for generalization.
- R133: external blind cross-work generalization FAIL.
- R134: clean replay failed to replicate the R129 scene-architecture effect; R129 lineage is `CONFLICTED_NOT_REPLICATED`.
- R135: linked external closure supports a relative renderer improvement only; it is not newly counted formal evidence and does not close voice bottleneck.
- R136-R138: surface/oral/voice work progressively localized the remaining spoken-Korean and character-voice bottleneck; R138 remains latest formal scored authority.
- R139: external evaluation protocol/metrology failure; closed not scored; content-effect inference not allowed.

## 7. P0/P01-P07 understanding
- P0: pre-R140 inspector/self-description/reproducibility engineering repair; formal count delta 0.
- P01: clean R41 historical validation — Ensemble replicated; tonal increment not supported.
- P02: clean R42 replay — blueprint depth + mismatch harm replicated; Thread Binding incremental treatment implementation-limited; primary rule FAIL.
- P03: R103 clean historical validation — full-episode completeness/thread consumer/texture guard PASS after iterated failures.
- P04: R121 clean historical validation — broadcast-scale closure/adaptive expansion/thread consumer PASS after iterated failures.
- P05: R135 linked external closure — relative renderer effect supported; voice bottleneck remains open; not counted formal.
- P06: Frozen Reference + Living Database governance physically closed; DB59 frozen for this lineage; malformed/language-quality successor repair candidates do not overwrite DB59 authority.
- P07: active preformal qualification/recovery phase; currently NOT complete.

## 8. Current adoption doctrine
The project no longer accepts module presence or trace presence as proof of semantic adoption.

Mandatory adoption chain:
`Value changes -> Consumer receives -> selected donor/semantic payload changes -> LLM provider input changes -> downstream behavior changes -> Receipt/Trace proves propagation`.

Also fixed:
- `File exists != Implemented`
- `Field exists != Consumed`
- `Function called != Adopted`
- `Validator PASS != Literary/Semantic Quality PASS`
- Python/runtime performs orchestration, state, retrieval, validation, receipts, fail-close, replan and commit/rollback; literary surface creation belongs to LLM/provider generation.
- `PYTHON_LITERARY_SURFACE_BYTES = 0` remains mandatory.

## 9. RFV2 and RFV3 current understanding
RFV2 working-state repair observations are recovery evidence, not current physical authority.
Frozen controlled-recovery contract includes:
- work-level THICK-only retrieval
- TF-IDF/cosine, analyzer `char_wb`, ngram 2-5, top-k 4
- HIGH >=0.13; MEDIUM >=0.10; LOW <0.10 -> fallback
- top1-top2 margin diagnostic only
- bounded THICK-derived functional profiles
- diagnostic score/margin separate from literary semantic payload
- actual verified archive path consumes repaired retrieval route
- selected-donor positive dependency
- irrelevant-unselected invariance
- Direct DB59 vs Frozen Index equivalence/tamper checks
- source cutoff enforcement
- Python prose 0
- no result-informed tuning

RFV3 preregistration remains output-zero and frozen:
- A = SUMMARY ONLY
- B = PRE-REPAIR ENGINE / NO_RETRIEVAL
- C = RFV2 REPAIRED ENGINE / DB59 USE_RETRIEVAL
- D = C + BIDIRECTIONAL REFINEMENT

Causal questions:
- A vs B: runtime information preservation/loss
- B vs C: incremental DB59 retrieval craft value
- C vs D: incremental bidirectional refinement value

RFV3 must not begin before current recovery/physical closure requirements are satisfied.

## 10. Mandatory next order
1. Treat 9/9 previous baseline audit as complete.
2. Preserve `CONTROLLED_RECOVERY_REIMPLEMENTATION` unless exact repaired RFV2 bytes are independently verified.
3. Reimplement/recover RFV2 strictly under the frozen preresult contract.
4. Freshly validate DB59 authority/membership, six development cases, CASE-01 propagation, selected/unselected donor causality, Direct DB59 vs Frozen Index equivalence, outer/inner tamper HOLD, source leak=0, Python prose=0, and full nonhistorical regression.
5. Preserve FAIL/HOLD without result-informed retuning.
6. Propagate verified recovered state into canonical 5 Parts / 9 Packages.
7. Every package: changed -> new SHA; unchanged -> byte-identical proof.
8. Rebuild Manifest + Trust Root; audit SHA/CRC/duplicate/unsafe/nested/C2/DB59/secret=0.
9. Physically deliver all nine current packages.
10. Only then declare `CURRENT_PHYSICAL_AUTHORITY`.
11. After that, proceed to retrieval/propagation closure, RFV3, CP1 current-authority integration, official R-F paired Live, R-G freeze/readiness, and finally Formal R140 under the latest sealed sequence.

## 11. Status token
`P07A_9_OF_9_PREVIOUS_BASELINE_FRESH_VERIFIED__D1_D2_DB59_REASSEMBLY_EXACT__PRIOR_CLIENTERROR_NOT_REPRODUCED__FULL_CONTEXT_RECOVERY_ALIGNED__RFV2_EXACT_REPAIRED_SOURCE_NOT_LOCATED__CONTROLLED_RECOVERY_REIMPLEMENTATION_REMAINS_REQUIRED__CURRENT_PHYSICAL_AUTHORITY_MISSING__R140_HARD_BLOCK`
