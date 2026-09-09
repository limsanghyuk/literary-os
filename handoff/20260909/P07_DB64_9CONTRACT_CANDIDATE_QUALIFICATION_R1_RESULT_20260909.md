# P07 DB64 / 9-Contract Candidate Qualification R1 — Result

Date: 2026-09-09

## FINAL CLASSIFICATION
`HOLD_FOR_DATA_REPAIR__ENGINE_A2_PROVENANCE_INVARIANCE_REPAIR_REQUIRED__NO_DB_AUTHORITY_PROMOTION`

Current active physical authority remains:
`CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_RECOVERY_R3`.

DB59 remains frozen at:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.

Semantic Alignment Virtual R1 remains a separate shadow candidate and is not used as a Live-qualified authority here.

## PREREGISTERED INPUTS
- SIKGAEK individual candidate SHA256 `802a4e43463d976b52dfe6daee9d3478a84166a26f1896da582876183acff82e`
- cumulative DB64 candidate SHA256 `59461a454ab64304d21af69fbb3b6985d85c8fd4991e14c32c1c015f685878ec`
- R51 Learning Bundle SHA256 `1f3a7202758198ce4843d7f243467d4b117b1ea9b5cff34c91094310f4c41d28`

## PHYSICAL / PAIRING GATE
PASS.
- individual: 598 entries, CRC PASS, duplicate 0, unsafe 0;
- DB64: 41,121 entries, CRC PASS, duplicate 0, unsafe 0;
- R51 bundle: 11,686 entries, CRC PASS, duplicate 0, unsafe 0;
- JSON/JSONL parse errors: 0 across all three;
- individual DB_MIRROR 595/595 byte-identical to DB64;
- Learning Bundle DB_MIRROR 595/595 byte-identical to DB64;
- individual and Learning mirror 595/595 byte-identical.

## STATIC 9-CONTRACT FINDINGS — 식객
- C1 decision/consequence nonempty 118/118;
- C2 SEQUENCE boundary + scene membership 118/118;
- C3: 118/118 use before/after shorthand, explicit entry/current/delta/trigger/exit/unresolved_carry/next_constraint slots 0; thread-bearing rows without explicit carry/next = 22;
- C4 DIRECT_SOURCE_AUTHORED + source refs/hash 118/118;
- C5 status SUPPORTED 118/118, but independent epistemic object 0 and owner grounding is fused with C5;
- A1 static sidecar lacks planning_question, target_consumer, execution_stage, selected_record_ids, selection_reason and provenance execution receipt fields;
- G1 static sidecar lacks normalized db_authority_id/schema_version/canonical_or_derived/episode_cutoff fields;
- G2 repair rows omit observed_layer and one row also lacks protected_scope;
- no false promotion: supplied closure remains `CONSUMER_READY_CANDIDATE / A2_PENDING`, `consumer_ready_A=false`.

## CURRENT-R3 NARRATIVE KNOWLEDGE BUS COMPATIBILITY
63 canonical works with EP02 PlannerInput were tested against the current R3 snapshot + NAP packet builder.
- snapshot PASS 60/63;
- packet PASS 56/63;
- 4 packet exceptions: 스카이캐슬, 스타일, 시그널, 시크릿가든 because `unresolved_payoffs` are string rows and current NAP expects dict rows;
- 시티헌터 and 식객 use `edge_id` without `thread_id`, producing duplicate `THREAD:None` evidence IDs;
- missing required EP01 ThreadState: 신사의품격, 신의퀴즈1, 신화;
- 스토브리그 Social Ecology derives only one group and correctly fail-closes as `INSUFFICIENT_EVIDENCE`.

PlannerInput thread-schema census in current DB64:
- total unresolved rows 20,640;
- canonical `thread_id` rows 19,611;
- edge-only rows 430 = 시티헌터 324 + 식객 106;
- non-dict string rows 599 = 스카이캐슬 175 + 스타일 249 + 시그널 78 + 시크릿가든 97.

Frozen DB59 comparison: 18,205 unresolved payoff rows use `thread_id`; edge-only rows 0 in the frozen control snapshot.

## A1/A2 PILOT
Frozen target: 식객 EP02, source cutoff EP01.

A1 execution receipt could be assembled from existing bytes, but selected thread evidence contained duplicate `THREAD:None`, so the packet is not engine-adoption clean.

A2 selected mutation:
PASS — selected 성찬 Character State semantic hash changed; literary payload changed; provider-facing sequence payload changed.

A2 irrelevant-unselected mutation:
FAIL — selected IDs, selected semantic hashes and literary payload stayed invariant, but the global snapshot hash changed; that provenance is embedded in full NAP, therefore provider-facing sequence payload hash changed.

The same provenance-only provider-input change reproduces against frozen DB59. Thus this A2 invariance blocker is an existing engine packet/provenance separation defect, not a DB64-only literary-data defect.

## COMPARATIVE UTILITY
`NOT_RUN__PREREQUISITE_HOLD`.
A DB59-vs-DB64 quality comparison would currently confound schema/consumer compatibility and engine A2 packet defects. No quality winner claim is permitted.

## REQUIRED DATA REPAIR
1. Normalize unresolved payoff consumer contract to stable `thread_id`; do not permit null/duplicate evidence IDs.
2. Normalize string-form unresolved payoffs to structured derived/runtime records without rewriting canonical literary prose.
3. Restore missing EP01 ThreadState for 신사의품격, 신의퀴즈1, 신화 from valid source-grounded evidence only.
4. Harden C3 applicable state slots and separate C5 epistemic status from owner grounding.
5. Normalize A1/G1/G2 execution/repair receipts and add preregisterable A2_TEST_TARGETS.
6. Preserve 스토브리그 insufficient Social Ecology as UNKNOWN/HOLD unless stronger source-grounded evidence exists; do not invent groups.

## REQUIRED ENGINE RESEARCH — SEPARATE CYCLE
Preregister a semantic-selection/provenance separation repair:
- preserve global snapshot hash in audit/receipt chain;
- provider semantic input should contain selected evidence and selected provenance only;
- selected mutation must change provider semantic input;
- irrelevant unselected mutation may change audit evidence root but must not change provider semantic input;
- add fail-closed null/duplicate evidence-ID guard;
- future DB64 pilot must use an explicit candidate authority adapter; never relabel DB64 as DB59.

## FIXED STATE
- Active physical authority: I4H Recovery R3 unchanged;
- Production ENG:R47;
- Formal 137;
- latest formal R138;
- R140 0/0/0;
- I4I 0/0/0/0;
- DB59 frozen;
- DB64 not adopted.

Parent engine post-qualification regression: 258/258 PASS.
