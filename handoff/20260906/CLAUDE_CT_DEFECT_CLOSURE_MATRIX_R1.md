# Literary OS — Claude/CT Defect Closure Matrix R1
Date: 2026-09-06
Classification: CURRENT ENGINEERING STATUS / NONFORMAL

This document answers one question only: which Claude/CT defects are actually repaired, which are only observed repaired in an unresealed working state, and which remain open.

## Global status
- Formal scored count: 137
- R140: 0 attempts / 0 outputs / 0 scores
- ENG:R47 Production: immutable
- DB59 frozen reference SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- Current physical 5-Part / 9-Package reseal after RFV2/RFV3 changes: **NOT COMPLETED**
- Current local artifact/container state: **ClientError / Infrastructure HOLD**
- Therefore no working-tree repair below is considered physically closed until the repaired bytes are rebuilt into the canonical 9 packages and re-audited.

## A-1 — DB59 retrieval gate / DB -> LLM semantic propagation
CT finding: actual DB59 retrieval repeatedly fell to `NO_RETRIEVAL`, so DB bytes were read/hashed but selected donor semantics did not reach LLM planning input.

Current status: **ENGINEERING REPAIR OBSERVED / PHYSICAL CLOSURE PENDING**

Observed repaired-state evidence before backend failure:
- actual retrieval source: 1,097 eligible THICK members / 10,784 records;
- six historical development cases observed `USE_RETRIEVAL`;
- Direct DB59 vs Frozen Retrieval Index: 6/6 retrieval equivalence observed;
- CASE-01 DB59 donors observed in `SEQUENCE_PLAN` semantic provider input;
- selected donor mutation changes semantic provider input;
- irrelevant unselected donor mutation does not change semantic provider input;
- Frozen Retrieval Index SHA256 observed: `d9b50787676aa0750ba0b519b2537dedafa71807c72edef78c659ddfb6ddf419`;
- index equivalence/tamper audit SHA256 observed: `81ca599ead072c7da9291450573b5a2c782d14d2b3b5514e5a7b3265b155fd23`;
- CASE-01 propagation evidence SHA256 observed: `ab60a39cc9ce8fe30835b7b3589566f7a2281af6c49957048eb2268531d95f4f`.

Repair notes:
- restored an R37/R38-compatible work-level TF-IDF/cosine retrieval concept under current THICK-only R0C membership;
- confidence bands restored to historical-style HIGH >=0.13 / MEDIUM >=0.10 / LOW <0.10 fallback;
- top1-top2 margin retained as diagnostic, not hard gate;
- diagnostic confidence/margin are separated from literary semantic payload so irrelevant DB changes do not perturb LLM semantic input merely through global scoring metadata;
- actual verified archive path was rewired to the repaired retrieval route;
- bounded THICK-derived functional work profiles were used instead of flattening all payload text as retrieval tags.

Required before closure:
1. recover exact repaired source bytes;
2. fresh-run 6-case DB59 audit;
3. fresh-run direct-vs-index equivalence/tamper audit;
4. fresh-run CASE-01 provider-input propagation;
5. rebuild 9 packages and re-audit.

Verdict: **NOT YET PHYSICALLY CLOSED**.

## A-2 — DB dependency test inversion (`assertNotEqual` -> `assertEqual`)
CT finding: the old core contract “selected DB member change changes semantic input” had been superseded by a current test asserting low-confidence DB changes do not change semantic input; no end-to-end positive archive retrieval test existed.

Current status: **ENGINEERING REPAIR OBSERVED / PHYSICAL CLOSURE PENDING**

Observed repair:
- positive archive -> normalization -> retrieval -> `USE_RETRIEVAL` -> retrieval payload -> `SEQUENCE_PLAN` input path added;
- selected donor mutation must change semantic provider input;
- irrelevant unselected donor mutation must not change semantic provider input;
- nonhistorical regression observed at **185/185 PASS** after adding RFV2 dependency tests.

Verdict: **LOGICAL CONTRACT REPAIRED IN WORKING STATE; NOT YET RESEALED**.

## B-1 — Current R11 CP1 paired Live runner missing
CT finding: `rf_live_parity_runner.py` had no successful CP1 branch; every terminal path returned HOLD/2.

Current status: **OPEN / NOT FIXED**

What was recovered:
- historical P07 PRE09 material contains an earlier paired live/craft parity runner design (`p07_pre09_live_craft_parity.py`) with Reference/Engine paired structure.

What is still missing:
- restoration/integration of that historical runner into current RFV2/RFV3 authority;
- current DB59/Frozen Retrieval Index path in Engine arm;
- current R-E surface craft and R-FV receipt-integrity contracts;
- current-authority paired TestDouble run;
- current-authority real OpenAI CP1 live execution.

Official R-F CP1 live outputs/Provider Receipts remain **0**.

Verdict: **HARD OPEN DEFECT / R140 BLOCKING**.

## B-2 — 181 regression tests were not Live Provider validation
CT finding: provider paths in the regression suite were mocks/test doubles; real provider call tests = 0.

Current status: **CLAIM BOUNDARY CORRECTED; LIVE EVIDENCE STILL PENDING**

Correction:
- local/mock regression is engineering evidence only;
- it must never be relabeled Live Provider validation;
- CT nonformal live evidence is separate and does not count as official R-F CP1.

Verdict: **DOCUMENTATION/CLAIM ISSUE CORRECTED; R-F LIVE STILL NOT DONE**.

## B-3 — Manifest R38/R39 mismatch / package authority drift
Historical CT finding: an earlier manifest declared C2 R38 while delivered C2 was R39.

Current status: **HISTORICAL R38/R39 MISMATCH REPAIRED, BUT NEW CURRENT 9-PACKAGE RESEAL IS PENDING**

Known current previous physical baseline:
- CONTROL R39 SHA256 `47fe62c8acf3401c69174c77c420be0d106703888def2ea2b073a9491b14eeeb`
- PART-A R38 SHA256 `9443d103de0eafd6fb063d1ba860a90e7be32d40227980d867f79808526696b1`
- B1 R10 SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 R39 SHA256 `f396d7fe583f6267c3b17735e690be5e50c35d48f2253ae7ea12a71779ecc920`
- C1 SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
- C2-A SHA256 `6208a1513550525234b85b63103fb64a8c3bca8405a91c019df243a28b8ff975`
- C2-B SHA256 `eac1bb5b424c92c6ae97924d09864412b222e581d34b062e0818e4105ee89f5f`
- D1 SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`
- C2-A || C2-B reconstructs previous C2 R39 authority SHA256 `d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`.

These are **PREVIOUS_PHYSICAL_BASELINE** values only. They do not contain all current RFV2/RFV3 pending repairs.

Verdict: **OLD MISMATCH CLOSED; CURRENT AUTHORITY PROPAGATION OPEN**.

## B-4 — `gpt-5.6-sol` model availability
CT self-correction: model exists and was reachable in CT environment.

Current status: **RESOLVED / NOT A BLOCKER**.

## C-1 — `.pyc` / `.pytest_cache` contamination
CT reported extracted working directory count inflation. GPT later inspected the sealed C2 R39 ZIP and observed exactly 520 overlay files with `.pyc=0` and `.pytest_cache=0` inside the sealed ZIP; local test execution can recreate caches after extraction.

Current status: **NOT CONFIRMED AS SEALED C2 R39 DEFECT**.

Future packaging rule: exclude build/test caches deterministically.

## C-2 — regression command ambiguity
Current status: **DOCUMENTED**

Historical/current R39 command boundary:
`pytest tests --ignore=tests/history_p07_pre09`
was the nonhistorical suite; running all tests included one intentionally preserved history failure before RFV2 repair.

After RFV2 working-state additions, a fresh command/result must be regenerated from repaired bytes before closure.

## C-3 — legacy/history code duplication and dual entrypoints
Current status: **OPEN HYGIENE / DRIFT RISK**

Known issue:
- history modules remain in runtime tree;
- legacy and verified semantic planning entrypoints coexist;
- `external_live_validation.py` historically used a legacy path.

Not presently claimed as repaired.

## C-4 — blind Coordinator Secret inside runtime resources
Current status: **OPEN HYGIENE / MUST BE REMOVED OR PHYSICALLY SEPARATED BEFORE R140 BLINDING**

Do not open historical blind secrets during normal engine execution. Future R140 execution and judging tracks must be physically separated.

## Additional defects found during RFV2 repair
### D-1 — repaired retrieval algorithm implemented but actual verified archive path initially still called old retrieval
Status: **WORKING-STATE REPAIR OBSERVED / RESEAL PENDING**.

### D-2 — work profile restoration used overbroad THICK full-text concatenation rather than bounded functional profile
Status: **WORKING-STATE REPAIR OBSERVED / RESEAL PENDING**.

### D-3 — diagnostic confidence/margin leaked into LLM semantic payload, so irrelevant DB changes could perturb input hash
Status: **WORKING-STATE REPAIR OBSERVED / RESEAL PENDING**.

### D-4 — Frozen Index query path repeated deep CRC/decompression/payload hashing and became operationally too slow
Status: **WORKING-STATE OPTIMIZATION/SEPARATION OBSERVED / RESEAL PENDING**.
Deep payload verification belongs to build/audit; query-time verification keeps outer/member SHA and authority binding.

### D-5 — duplicate amendment numbering (A1.5/A1.6 branches)
Status: **GOVERNANCE CORRECTION DOCUMENTED IN WORKING SESSION; RESEAL/PACKAGE PROPAGATION PENDING**.

## Overall answer
Claude/CT defects are **NOT all finished**.

Closed/resolved enough at scientific interpretation level:
- model availability misdiagnosis;
- old C2 R38/R39 transport mismatch;
- claim boundary that mock regression is not Live;
- sealed C2 cache contamination was not reproduced as a package defect.

Substantively repaired in working state but not physically closed:
- DB59 retrieval/LLM propagation;
- DB dependency positive/negative tests;
- retrieval route wiring/profile/payload stability/Frozen Index behavior.

Still open and blocking final preformal closure:
- current-authority CP1 paired runner restoration/integration;
- current-authority CP1 TestDouble and real OpenAI live run;
- 5-Part / 9-Package physical reseal with all repaired bytes;
- fresh regression/DB59/equivalence/tamper audits from those exact package bytes;
- legacy drift/blind-secret hygiene before Formal R140.

R140 remains **HARD BLOCK**.