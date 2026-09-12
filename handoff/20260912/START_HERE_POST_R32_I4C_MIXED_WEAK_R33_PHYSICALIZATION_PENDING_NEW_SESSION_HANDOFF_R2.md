# START HERE — POST-R32 I4C MIXED/WEAK REPLICATION — R33 PHYSICALIZATION PENDING — R2

Date: 2026-09-12
Audience: next ChatGPT / developer session receiving the current Literary OS 5 logical Parts / 9 physical transport packages.

This document is the primary new-session handoff. Read it only after reading the physical packages in the mandatory order beginning with CONTROL.

---

# A. What the next session will physically receive

The developer will provide the latest fully physicalized package set: **SYNC-R32**.

Physical authority root:
`b37a3774a4f701ab4caabac3cb5e62442403f499d21d89203ef85d199b6a2ffb`

Mandatory package reading order:

`CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2`

The nine transport roles are:

1. CONTROL — SYNC-R32 CONTROL
2. A — SYNC-R32 Part A
3. B1 — unchanged
4. B2 — SYNC-R32 Part B2
5. C1 — unchanged
6. C2-A — unchanged
7. C2-B — unchanged
8. D1 — DB59 unchanged
9. D2 — DB59 unchanged

Exact filenames and hashes are frozen in:
`handoff/20260912/SYNC_R32_I4C_INGESTION_GATE_READY_DELIVERY_MANIFEST_R1_20260912.json`

If any of the nine hashes differ, stop and resolve package integrity before research.

---

# B. Most important recovery rule: R32 physical state is older than Hub research state

SYNC-R32 was physically sealed **before** the three independent I4C evaluator responses were incorporated.

Therefore, if the next session reads only the nine physical packages, it will encounter an older state approximately equivalent to:

`I4C packets sealed / responses 0 / ingestion gate ready / mapping closed`.

That is no longer the latest research state.

The GitHub Hub contains the authoritative post-R32 continuation. The next session must merge the two layers conceptually:

- **Physical bytes authority:** SYNC-R32
- **Research result authority after those bytes:** Hub post-R32 sealed evidence

Do not silently rewrite R32 package contents. Instead, physicalize the Hub delta into SYNC-R33 as the first substantive action.

---

# C. Exact current authorities

No promotion occurred during the post-R32 research.

- Active Development Engine: `P07-I4H Recovery R3`
- Production: `ENG:R47`
- DB Authority: DB59 frozen
- DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- Combined C2 SHA256: `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`
- Formal scored total: `137`
- Latest formal: `R138`
- Formal R140: `0/0/0`

Never infer a Production or Formal promotion from the I4C exploratory replication.

---

# D. R4A branch — frozen, separate, unfinished

R4A must not be mixed with I4C.

Current R4A state:

- Attempt2 Control/Treatment exact frozen surfaces retained
- G6 blind mask PASS
- G7 duplicate-score/provenance PASS
- Provider state: `HOLD__REAL_PROVIDER_SECRET_ABSENT`
- Independent Judges = `0`
- R4A mapping open = `0`
- H1-H4 final verdict = none

The I4C replication mapping was opened legitimately after its own independent 3/3 gate. That does **not** authorize R4A unblind.

If a future session obtains a real provider path for R4A, it must resume under the original R4A preregistration and must not use the I4C result as a Judge hint.

---

# E. Why the I4C replication was run

Prior whole-episode research produced three relevant observations:

1. I4K5 showed a strong common-mode Plan→Surface contamination pattern in a historical case.
2. I4E demonstrated real late continuity/speaker debt, but fixing that debt alone did not restore whole-episode superiority.
3. I4C had no comparable meta/preface/critical-continuity defect yet still lost human comparisons mainly in middle/late positions.

Deterministic surface diagnostics did not isolate a stable single mechanism, producing `NO_STABLE_RESIDUAL_SIGNAL`.

Blind coding of historical I4C Stage-B rationales produced `MIXED_QUALITATIVE_SIGNAL`: relation/status pressure, information irreversibility, ensemble/world specificity, pacing, and physicalization appeared in a mixed pattern rather than one dominant defect.

A fresh unused-scene positional replication was therefore preregistered to test whether middle/late scenes really show broader multi-dimensional craft deficits than early scenes.

---

# F. I4C unused-scene replication design

Preregistration commit:
`b4a323edb9efbecd34e196848f5c9f2c6c260163`

Classification:
`EXPLORATORY_REPLICATION__KNOWLEDGE_ONLY__NO_RENDERER_INTERVENTION__NO_SCORE_REWRITE`

Source:
sealed `I4C_R2_FINAL_SCREENPLAY_R1` only.

Original historical Stage-B scenes were excluded.

Fresh sample selected by frozen deterministic seeds:

- EARLY: `S02, S10, S13, S16`
- MIDDLE: `S23, S26, S27, S29`
- LATE: `S42, S43, S46, S48`

All 12 were masked to opaque AP01–AP12 ids; early/middle/late position was hidden from evaluators.

Frozen 8 craft axes:

1. `DIALOGUE_SUBTEXT`
2. `CHARACTER_VOICE`
3. `RELATIONSHIP_STATUS_PRESSURE`
4. `PHYSICALIZATION_ACTION`
5. `PACING_ESCALATION_TIME_PRESSURE`
6. `ENSEMBLE_WORLD_SPECIFICITY`
7. `INFORMATION_REVEAL_IRREVERSIBILITY`
8. `LINE_ECONOMY_RHYTHM`

Each evaluator rated each axis:

- 0 = no material deficit
- 1 = minor/local deficit
- 2 = material scene-level deficit

Three fresh independent GPT sessions were required.

---

# G. Independent evaluation method and provenance

The procedure intentionally inherited the earlier I4K-5 external multi-GPT method.

Each evaluator had to run in a separate fresh GPT conversation and receive only its own blind packet.

They were instructed not to:

- search Literary OS or GitHub,
- infer scene position,
- inspect mapping,
- see another evaluator's response,
- use historical winner information.

Canonical responses were sealed before unblind:

## J01
Commit:
`76b09dcdee07ae2df1368b5caf1291872ef1f478`

SHA256:
`6bc7d546dabe96dea8785d4f7f97520fc91cc32ecfeb9a6209a82386180e1799`

## J02
Commit:
`17c3980273625a57352d37aa3fb5fce958c73660`

SHA256:
`d7128feed3e5a1a7e54bca8cb53f0031d52b996a2a524da3f45e521b627712d2`

## J03
Commit:
`e6a91142ff0d6ae04fd054936f2ab5661ead78ac`

SHA256:
`92103ff48714a5b2f552c298ec17f74813bb02e38991f216586069fd115317df`

All three were structurally valid and independent-attested.

---

# H. Three-of-three gate and unblind custody

Three-of-three validation status:

`PASS__THREE_VALID_RESPONSES__UNBLIND_AUTHORIZED`

Workflow run:
`34678041251`

Job:
`103511339068`

Gate receipt SHA256:
`711032cc23dcbe25c2f510037ab204c29d5da97632fdb7939fe8c2c7068de4a9`

Seal commit:
`8c4f4ec929972ed9f799309ec58fc529dfece989`

Only after that gate passed was I4C replication mapping replay allowed.

Exact mapping byte replay:

- expected SHA256 `46f8972c408250614761733ac29da956d1f1eecd3b0d3dbe9d14f13877ff2377`
- replayed SHA256 same
- bytes `1501`
- status `PASS__EXACT_MAPPING_BYTE_SEAL_REPRODUCED`
- commit `6b9eb840ba3e8cf88ae5721094f1ae0cb5f826fb`

This proves the post-response unblind used the exact pre-sealed mapping rather than a result-following remap.

---

# I. Final I4C positional replication result

Final result:
`MIXED_OR_WEAK_REPLICATION`

Final receipt:
`handoff/20260912/I4C_UNUSED_SCENE_POSITIONAL_REPLICATION_FINAL_RECEIPT_R1_20260912.json`

Final receipt commit:
`f808af0a0482ba775bcac4df4128726ad5ac0827`

Aggregation run:
`34679153731`

Job:
`103514388174`

Artifact:
`10293716231`

Artifact digest:
`sha256:2a57753b8f430c088a2e17b54837f0c37879f132e07791abf157f33634fd1615`

## Frozen stratum metrics

EARLY:
- mean breadth `1.0`
- mean severity `1.0`
- material breadth `0.0`

MIDDLE:
- mean breadth `2.0`
- mean severity `2.0`
- material breadth `0.0`

LATE:
- mean breadth `1.75`
- mean severity `1.75`
- material breadth `0.0`

MIDDLE+LATE pooled:
- mean breadth `1.875`
- mean severity `1.875`

Difference MIDDLE+LATE minus EARLY:
- breadth `+0.875`
- severity `+0.875`

Independent evaluator direction:
- J01 middle/late worse: true, delta `+0.375`
- J02 middle/late worse: true, delta `+0.625`
- J03 middle/late worse: true, delta `+0.25`
- agreement = `3/3`

## Frozen thresholds

Strong positive replication required all of:

- breadth delta >= `+1.0`
- severity delta >= `+2.0`
- >= `2/3` evaluators with middle/late worse

Outcome:

- breadth threshold: FAIL
- severity threshold: FAIL
- evaluator direction: PASS

Hence the only valid decision is:

`MIXED_OR_WEAK_REPLICATION`

Do not reinterpret this as either a clean PASS or a clean NO-SIGNAL result.

Correct meaning:
there is consistent directional support that middle/late scenes are somewhat weaker, but the preregistered strong claim of broad/material multi-axis positional degradation did not reproduce.

No cross-evaluator median axis reached severity 2 in any scene. Material breadth was 0 in all strata.

---

# J. Scientific claim boundary

This result is:

- knowledge-only,
- one sealed I4C episode,
- 12 previously unused scenes,
- three independent GPT conversations,
- exploratory replication.

It is **not**:

- human consensus,
- cross-family consensus,
- population generalization,
- proof of a single causal craft defect,
- permission for a generic renderer patch,
- Production promotion evidence,
- Formal R140 evidence,
- historical score rewrite.

Do not lower the preregistered thresholds after seeing the +0.875 values.

---

# K. CAAS/Jupyter/container incident

During post-R32 processing, the current session's Python/container transport path repeatedly returned `TransportTimeoutError`, including on minimal operations. Files and GitHub APIs remained functional; GitHub Actions remained functional.

The scientific pipeline therefore moved to GitHub Actions as a deterministic execution surface.

Incident receipt commit:
`313faf92c029df010f925c960ab24409b3e3f3ce`

No sample, threshold, score, response, mapping, or decision rule was changed because of this failover.

The next session must test its own runtime from scratch; do not assume the failure persists.

---

# L. Why SYNC-R33 is mandatory before new research

Meaningful post-R32 research exists in Hub but is not yet physically included in the developer's 9 packages.

A deterministic physical delta is already sealed:

`handoff/20260912/SYNC_R33_PENDING_DETERMINISTIC_DELTA_MANIFEST_R1_20260912.json`

Commit:
`b34a5c0437186afa415dfdc7a30d58284c12a8e7`

The new session must **not** begin another experiment first.

First physicalize R33 from exact R32 parent bytes.

R33 rules:

- append-only changes to `CONTROL / A / B2`
- append overlay root `research_sync_r33/`
- keep `B1 / C1 / C2-A / C2-B / D1 / D2` byte-identical to R32
- use only the exact Hub files enumerated by the delta manifest
- preserve sealed result bytes and provenance
- never insert R4A mapping secret

Required overlay sources are enumerated in the deterministic delta manifest and include:

- J01/J02/J03 canonical responses
- three-of-three gate PASS receipt
- mapping replay verifier
- mapping replay PASS receipt
- positional replication aggregator
- final result receipt
- CAAS incident/failover receipt

---

# M. Exact first actions in the new session

Do these in order:

1. Confirm all 9 developer-provided files exist.
2. Read `CONTROL` first.
3. Read `A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2`.
4. Verify all 9 SHA256s against the SYNC-R32 delivery manifest.
5. Verify transport root = `b37a3774a4f701ab4caabac3cb5e62442403f499d21d89203ef85d199b6a2ffb`.
6. Read `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`.
7. Read `handoff/CURRENT_HANDOFF_POINTER.md`.
8. Read `handoff/20260912/POST_R32_CURRENT_AUTHORITY_SNAPSHOT_R2_20260912.md`.
9. Read this handoff R2.
10. Read the final I4C receipt and R33 deterministic delta manifest.
11. Test runtime with a minimal command before large archive operations.
12. If runtime works, build SYNC-R33 immediately.
13. Audit changed ZIPs: CRC, duplicate paths, unsafe paths, symlink, encrypted entries, parent entry preservation.
14. Verify the R33 overlay is byte-identical across CONTROL/A/B2.
15. Verify unchanged six transports are exactly byte-identical to R32.
16. Recompute 9 hashes and transport root.
17. Create R33 Delivery Manifest, Physical Audit, Physical Closure, Root Input, SHA256SUMS.
18. Only after audit PASS update CURRENT PHYSICAL AUTHORITY to R33.
19. Preserve R4A Judges=0 / Mapping closed.
20. Only after R33 closure plan the next fresh craft-mechanism research.

If runtime fails again, do not fabricate a physical R33. Keep R32 physical authority and record the incident; Hub research result remains valid and sealed.

---

# N. Next scientific question after R33 closure

Do not ask merely “is late episode craft worse?” again. That question now has weak directional support but failed strong replication thresholds.

The next research must narrow to a specific reproducible mechanism.

A valid next prospective study should:

- use fresh/unseen material,
- preregister hypothesis and thresholds before generation,
- isolate one or a small set of craft mechanisms,
- retain absolute surface hygiene gates,
- retain relative Control/Treatment effect tests,
- preserve actual load/contract-consumption receipts,
- preserve independent evaluation separation,
- avoid generic renderer modification from the weak positional result alone.

Candidate mechanisms should only be chosen after reviewing all prior evidence, including relation/status pressure, information irreversibility, ensemble/world specificity, pacing, and physicalization, but no single axis has yet earned causal-intervention authority.

---

# O. Developer safety notes

- Never type API keys into ChatGPT.
- If provider validation is resumed, use environment variables / secret manager and return only receipts/hashes.
- Avoid bulk extraction of large C2/DB archives when not necessary.
- Previous container failures were transport/runtime related; use minimal-command checks before expensive operations.
- Do not rename sealed historical artifacts merely to fix revision-label ambiguity.
- Keep revision axes explicit: `SYNC-*`, `FORMAL-*`, `ENGREC-*`, `EXP-*`, etc.

---

# P. Current status token

`PHYSICAL_SYNC_R32__POST_R32_I4C_3OF3_VALID__EXACT_MAPPING_REPLAY_PASS__MIXED_OR_WEAK_REPLICATION__R33_PHYSICALIZATION_PENDING__R4A_JUDGES_0_MAPPING_CLOSED__NO_AUTHORITY_PROMOTION`
