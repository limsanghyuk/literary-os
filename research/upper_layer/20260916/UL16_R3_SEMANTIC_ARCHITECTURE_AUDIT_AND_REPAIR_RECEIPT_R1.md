# UL-16 R3 Cutoff-Safe Semantic Architecture Audit & Repair Receipt R1

Date: 2026-09-16
Status: `PASS_AFTER_DEFECT_REPAIR__SEMANTIC_ARCHITECTURE_FIXTURE__NO_AUTHORITY_CHANGE`
Parent runtime: canonical UL-16 R2 research runtime.
Execution rules: R6 Authority Sync Gate + R5 Turn-Bounded + R4 Atomic Execution.

## 1. Authority precheck
Canonical parent package:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R2_20260916.zip`

Canonical parent SHA256:
`7f71484cd2687262d18104b3a9a5cfe727d003d7ed4b616ce8d64702b2da2ca8`

The exact Library asset was materialized into the active container and reverified before execution:
- size: 18,681,762 bytes;
- SHA256: exact Hub match;
- ZIP CRC: PASS.

No stale local package was used.

## 2. Frozen audit scope
The audit was frozen before result inspection around five semantic domains:
- Relationship;
- Social Ecology;
- Ensemble;
- Information;
- Scene Transaction.

Preregistered fixture/hash:
- prereg hash: `776f11408aa47c3627d1c6669961d935bb47c7f5ec14ffa910b072250693fddc`;
- fixture hash: `e5b7a30ae8f9e0f5077370ef9a6db4486f5589d0ff1f8f355f3336c20be11ac7`.

PASS required all of the following:
1. concrete relationship pair + relationship delta survive into each transacting scene;
2. concrete information delta survives into each transacting scene;
3. concrete social delta + group refs survive into each transacting scene;
4. scene cast is transaction-local, not the whole sequence owner union;
5. supplied visible action and obstacle survive into scene anchors;
6. touched deferred pressure survives in `residual_after` / deferred residue;
7. pre/post state, downstream consumer, state-delta requirement and physicalization requirement remain present;
8. due/defer reverse reconstruction remains exact.

The fixture is cutoff-safe synthetic current-state input. No hidden target future episode content is used.

## 3. R2 audit result — defect confirmed
Unmodified canonical R2 result:
- decision: `DEFECT_CONFIRMED`;
- total semantic preservation issues: **90**;
- adaptive validation: FAIL (owner concentration false positive also triggered);
- due/defer reverse reconstruction itself: PASS.

Issue counts:
- `REL_DELTA_LOST`: 46;
- `REL_PAIR_LOST`: 10;
- `INFO_DELTA_LOST`: 3;
- `SOCIAL_DELTA_LOST`: 6;
- `ENSEMBLE_CAST_LEAK`: 7;
- `DEFERRED_RESIDUE_LOST`: 18.

## 4. Root causes
The audit isolated five implementation defects.

### A. Semantic normalization loss
`relationship_delta`, `information_delta` and `social_delta` were retained in obligation objects but `_semantic_scene_anchor()` replaced them with generic strings such as “관계 상태가 바뀐다 / 정보상태가 바뀐다”.

### B. Topology loss
`relationship_pair` and `group_refs` were not carried through Scene blueprint -> Canonical SceneIR -> renderer projection.

### C. Ensemble cast leakage
Each lowered scene inherited the entire sequence `owner_ids`, even when the scene transacted only one obligation. This introduced unrelated participants into a scene.

### D. Deferred residue loss during lowering
The adaptive scene graph correctly tracked `deferred_pressure_ids`, but the legacy-compatible lowered blueprint/contract wrote `residual_after=[]`, erasing the semantic residue at the interface boundary.

### E. Joint-participation false owner concentration
Owner concentration counted every joint owner as a full sequence owner. Multi-owner sequences could therefore be falsely diagnosed as >75% owner concentration. Weighted fractional ownership is required to distinguish participation from monopoly.

## 5. R3 repair
Repair scope relative to canonical R2:
- `literary_os_runtime/adaptive_showrunner_ul16.py`;
- `literary_os_runtime/canonical_ir_v2.py`.

Repairs:
- preserve specific relationship/information/social deltas rather than replacing them with generic placeholders;
- preserve structured `relationship_pairs`, `group_refs`, `transaction_owner_ids`, and `transaction_kinds`;
- use transaction-local scene cast/owner/counterparty;
- preserve touched deferred IDs as `residual_after` in Scene blueprint, Scene contract, Sequence settlement and Canonical SceneIR;
- add hash-bound `semantic_topology` and `semantic_state_deltas` fields to Canonical SceneIR and renderer projection;
- validate topology/state-delta hashes at the Canonical IR boundary;
- use fractional weighted owner concentration for multi-owner sequences;
- make relationship-floor reporting reflect actual required/observed relationship obligation IDs.

## 6. Same-fixture retest — PASS
The identical frozen fixture was rerun without changing the gate.

Post-repair result:
- decision: **PASS**;
- semantic preservation issues: **0**;
- adaptive validation: PASS;
- sequence count: 9;
- scene count: 57;
- sequence scene range: 5..10;
- due recoverable: PASS;
- deferred preserved: PASS;
- lost deferred: 0;
- false deferred fulfillment: 0;
- blocked precondition false fulfillment: 0.

Post-repair architecture hash:
`9989791da6361e2964273e90f9fdc0c0cf043e467db8f98ae232022ec4928291`

## 7. Canonical IR / Renderer boundary retest
The repaired architecture was lowered through the actual R53 Canonical Typed IR V2 implementation.

Result:
- SeriesIR: 1;
- EpisodeIR: 1;
- SequenceIR: 9;
- SceneIR: 57;
- total nodes: 68;
- Canonical validation errors: 0;
- decision: PASS;
- graph hash: `d7a47d049fda9b1dd8afed1f3d1cd3dfa7ea30a9eca599f65e04929421d287d0`;
- renderer projections: 57.

Explicit preservation checks through Canonical SceneIR and renderer projection all PASS for:
- relationship delta/pair;
- information delta;
- social delta/group refs;
- transaction-local topology;
- deferred residue.

Python runtime compilation: **45/45 PASS**.

## 8. R3 research package
Package:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R3_SEMANTIC_ARCH_PASS_20260916.zip`

Size:
`18,708,729 bytes`

SHA256:
`495acdc8957c8085e10c22e3a6af3c455be31c73fe1d793242e62e26e224eee8`

ZIP CRC:
PASS.

Persistent Library path:
`/Literary_OS/Physical_Archive/RESEARCH_UL16_20260916/LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R3_SEMANTIC_ARCH_PASS_20260916.zip`

Internal audit receipt object hash:
`08ef8b61285898864ad2b96cd5b7267159924a49dd472d69c709de977986f027`.

## 9. Runtime health
Current transaction:
- `memory.events max`: 117 -> 117 (delta 0);
- OOM: 0;
- OOM-kill: 0;
- no memory-pressure HOLD.

## 10. Interpretation boundary
This audit closes a **semantic-preservation software defect** at the current-state obligation -> Sequence -> Scene -> Canonical IR -> Renderer Projection boundary.

It does **not** prove:
- human-level dramatic architecture;
- independent blind literary quality;
- real OpenAI Provider execution;
- full screenplay quality;
- state commit/carry + replan closure;
- physical Candidate promotion.

`UPPER_LAYER_GENERATIVE_QUALITY` therefore remains `NOT_YET_QUALIFIED`.

## 11. Authority impact
None.

Unchanged:
- Physical baseline: SYNC-R53;
- Production Engine: ENG:R47;
- Candidate Base authority: P07-I4H Recovery R3;
- runtime DB authority: DB59 frozen;
- DB64: research-support candidate only;
- Formal total: 137; latest R138; R140 0/0/0.

The new R3 package is research runtime evidence only.

## 12. Next bounded transaction
The next R6+R5 transaction is **State Commit/Carry + Responsible-Ancestor Replan regression on the R3 adaptive semantic graph**.

Do not start architecture blind evaluation or Provider generation until that transaction closes.

## STATUS TOKEN
`UL16_R3__SEMANTIC_ARCHITECTURE_AUDIT_DEFECTS_90_TO_0__RELATIONSHIP_SOCIAL_ENSEMBLE_INFORMATION_SCENE_TRANSACTION_PRESERVED__CANONICAL_68_NODE_PASS__RENDERER_PROJECTION_PASS__NEXT_STATE_CARRY_RESPONSIBLE_ANCESTOR_REPLAN__NO_AUTHORITY_CHANGE`
