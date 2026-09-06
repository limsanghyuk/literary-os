# Literary OS — P07-A RFV2 Controlled Recovery / Reimplementation Specification R1
Date: 2026-09-07
Classification: PREFORMAL ENGINEERING RECOVERY SPEC / PRERESULT FREEZE
Depends on: `P07A_INFRASTRUCTURE_DIAG_AND_RFV2_SOURCE_SURVIVAL_AUDIT_R1.md`

## 0. Purpose
Freeze the exact allowed reconstruction contract for RFV2 before any reconstructed implementation is executed or any new result is observed.

This specification exists because the complete interrupted-session RFV2 repaired source snapshot has not been located as a byte-verifiable durable GitHub artifact. It does not authorize arbitrary redesign.

## 1. Immutable authorities
- ENG:R47 Production remains immutable.
- DB59 is the frozen corpus authority: SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- DB64 must not silently substitute for DB59.
- Source cutoff for the current development validation remains the already frozen cutoff; actual/post-cutoff target material is prohibited.
- Python literary prose generation = 0.
- Formal scored count remains 137.
- RFV3 outputs remain 0.
- R140 remains HARD BLOCK.

## 2. Reconstruction identity claim
The resulting implementation must be labeled:
`CONTROLLED_RECOVERY_REIMPLEMENTATION`

It must NOT be labeled:
- byte-identical RFV2 restoration;
- recovered exact RFV2 source;
- current physical authority until package reseal/audit passes.

If an exact prior repaired source artifact is later discovered, it may replace this reconstruction path only after independent hash/checkpoint verification and an explicit authority amendment before use.

## 3. Frozen retrieval algorithm contract
### 3.1 Unit of retrieval
- work-level retrieval under the documented current THICK-only R0C membership;
- derive one bounded functional work profile per eligible work/member;
- do not flatten unbounded full THICK prose into retrieval tags.

### 3.2 Vectorization and similarity
- TF-IDF / cosine concept compatible with the R37/R38 lineage;
- analyzer: `char_wb`;
- character ngram range: 2–5;
- candidate top-k: 4.

### 3.3 Confidence bands
- HIGH: score >= 0.13;
- MEDIUM: 0.10 <= score < 0.13;
- LOW: score < 0.10 -> fallback / `NO_RETRIEVAL` according to the frozen route contract;
- top1-top2 fit margin is diagnostic only and MUST NOT be a hard accept/reject gate.

No threshold may be changed after observing development-case outcomes.

## 4. Functional profile contract
A bounded profile may contain only source-safe, already-authorized functional/structural descriptors derivable from the eligible THICK/member payload under the frozen cutoff.

The reconstruction must preserve the correction that retrieval representation is not a raw concatenation of full literary prose.

Exact field extraction must be documented from the recovered current schema before execution. If schema ambiguity prevents deterministic extraction, classify HOLD and preregister an amendment before running retrieval; do not infer fields after looking at scores.

## 5. Semantic payload separation
Selection diagnostics and literary conditioning are different objects.

Diagnostic-only values include at least:
- similarity/confidence score;
- top1-top2 margin;
- ranking diagnostics;
- audit/provenance metadata not intended as literary semantics.

These diagnostics may appear in receipts/traces but must not be allowed to alter the literary semantic conditioning payload merely because an irrelevant unselected archive member changed.

The selected donor semantic payload must include only the source-safe donor information explicitly admitted by the current semantic-planning contract.

## 6. Verified archive routing
The actual verified archive/runtime entrypoint used for the P07-A validation must call the reconstructed retrieval route.

It is insufficient that:
- a repair helper exists;
- a unit test calls the helper;
- an evidence record mentions DB59.

Adoption proof requires:
`DB59 value -> archive normalization/profile -> retrieval selection -> selected donor semantic payload -> semantic provider input -> downstream trace/receipt`.

## 7. Frozen positive and negative causal contracts
### Positive dependency
Changing the actually selected donor/member content in an allowed controlled mutation must change the corresponding semantic provider input hash/content.

### Negative dependency
Changing an irrelevant, unselected donor/member in a controlled mutation must NOT change the literary semantic provider input, assuming the selected donor set and source-safe literary payload are otherwise unchanged.

The test must distinguish literary semantic payload from diagnostic ranking metadata.

## 8. Direct DB59 vs Frozen Retrieval Index contract
A derived Frozen Retrieval Index may be built only from the verified DB59 frozen authority and documented membership/cutoff.

Build/audit stage:
- deep source/member integrity checks;
- provenance and authority binding;
- deterministic index build contract;
- record index SHA256.

Query stage:
- preserve authority/member binding and required hashes without repeating unnecessary deep decompression verification on every query if the build/audit seal already established that invariant.

Direct DB59 and Frozen Index retrieval must be compared on the frozen development cases. Prior 6/6 equivalence is not a target and may not be forced.

## 9. Fresh mechanical validation gates
Before any RFV3 craft generation or scoring:
1. DB59 outer/frozen SHA exact.
2. Eligible membership/count freshly measured; prior 1,097 members / 10,784 records is reference only.
3. Frozen six development cases executed under the reconstructed route.
4. Retrieval decisions and donor ids/hashes recorded.
5. CASE-01 selected donor literary semantic payload reaches `SEQUENCE_PLAN` provider input when retrieval is accepted.
6. Selected-donor controlled mutation changes provider input.
7. Irrelevant-unselected controlled mutation leaves literary provider input unchanged.
8. Direct DB59 vs Frozen Index comparison executed.
9. Frozen Index outer/inner tamper cases fail closed/HOLD.
10. Source-cutoff violation = 0.
11. Python literary prose bytes = 0.
12. Full nonhistorical regression freshly executed from the exact reconstructed bytes.

Prior values such as 6/6 and 185/185 are historical observations, not pass thresholds unless an already-sealed test contract independently defines them as such.

## 10. Result handling
- If reconstruction fails to reproduce earlier behavior: record FAIL/HOLD; do not tune toward the historical result.
- If one or more development cases legitimately fall to `NO_RETRIEVAL`: record the actual result; do not lower thresholds post hoc.
- If schema/route ambiguity is discovered before results: create a preregistered amendment explaining the ambiguity and frozen resolution.
- If ambiguity is discovered after results: preserve the run and classify the affected inference INVALID/HOLD as appropriate; do not silently patch and reuse the result.

## 11. Packaging closure after validation
After mechanical validation, propagate all affected recovered/reimplemented code, tests, evidence, receipts, manifests, checkpoints, and claim-boundary documents into canonical:
`CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2`.

For each package:
- changed -> new bytes + new SHA256;
- unchanged -> prove byte-identical identity to the chosen baseline.

Required close audit:
- 9/9 present;
- per-package SHA256;
- ZIP CRC PASS where applicable;
- duplicate path 0;
- unsafe path 0;
- nested ZIP PASS;
- current C2-A || C2-B exact reconstruction;
- DB59 authority correct;
- secret/API key 0;
- Manifest + Trust Root + Developer Hub + Session Recovery Pointer agree.

Only then may the result be called `CURRENT_PHYSICAL_AUTHORITY`.

## 12. Downstream hard blocks
Until Section 11 closes:
- RFV3 generation: BLOCKED;
- CP1 current-authority integration/live: not started from this spec;
- official R-F Live: BLOCKED;
- R-G freeze: BLOCKED;
- Formal R140: HARD BLOCK.

## 13. Frozen status token
`RFV2_CONTROLLED_RECOVERY_REIMPLEMENTATION_SPEC_FROZEN_PRERESULT__NO_EXECUTION_YET__NO_RESULT_TUNING_ALLOWED__P07A_PHYSICAL_CLOSURE_REQUIRED_BEFORE_DOWNSTREAM_GENERATION`
