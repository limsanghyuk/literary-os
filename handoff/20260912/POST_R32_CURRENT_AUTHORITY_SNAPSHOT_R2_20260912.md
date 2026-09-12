# Literary OS — Post-R32 Current Authority Snapshot R2

Date: 2026-09-12
Purpose: authoritative recovery snapshot for the next session when the developer supplies the current 5 logical Parts / 9 physical transport packages.

## 0. Non-negotiable distinction

There are **two different state layers** and they must never be collapsed:

1. **Current Physical Authority = SYNC-R32** — the latest fully materialized and audited 5-Part / 9-transport package set physically delivered to the developer.
2. **Current Hub Research State = post-R32** — additional research completed after SYNC-R32 and sealed in GitHub Hub, but not yet integrated into a new 9-transport physical set.

Therefore: do **not** call SYNC-R33 physical authority yet. The next session must first physicalize SYNC-R33 from the exact R32 parent bytes plus the already sealed deterministic delta.

---

## 1. Current Physical Authority — SYNC-R32

Transport-set root SHA256:
`b37a3774a4f701ab4caabac3cb5e62442403f499d21d89203ef85d199b6a2ffb`

Required read order:
`CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2`

Ordered physical transports:

1. CONTROL — `LITERARY_OS_CURRENT_CONTROL_P07_I4H_RECOVERY_R3_I4C_INGESTION_SYNC_R32_20260912.zip`
   - SHA256 `d75661e4e704efbd0587b4e8e15ec8cb6b5c811b78edfb8b840f5d7c3029ddbf`
2. A — `LITERARY_OS_CURRENT_PART_A_P07_I4H_RECOVERY_R3_I4C_INGESTION_SYNC_R32_20260912.zip`
   - SHA256 `8e8dd81f04cb7888b2344a760aa6ff6ca798e34f1172be59b9d3fca3b3de329a`
3. B1 — `LITERARY_OS_CURRENT_PART_B1_UNCHANGED_R1_20260909.zip`
   - SHA256 `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
4. B2 — `LITERARY_OS_CURRENT_PART_B2_P07_I4H_RECOVERY_R3_I4C_INGESTION_SYNC_R32_20260912.zip`
   - SHA256 `d59abdf58d22d3a1fa825676b9690d74c07252ea5f98d5afc819a73d5248c624`
5. C1 — `LITERARY_OS_CURRENT_C1_RUNTIME_CORE_UNCHANGED_R1_20260909.zip`
   - SHA256 `dcfe8e76e8be66b5dffe0c3dd048fde4fba6267457a9bbf06fed1105b5a8c518`
6. C2-A — `LITERARY_OS_CURRENT_C2_BINARY_A_P07_I4H_RECOVERY_R3_20260909.bin`
   - SHA256 `d1fb7ba65ead633ec13d027d032e4bd3950e973b61408e04b620bd37f7997253`
7. C2-B — `LITERARY_OS_CURRENT_C2_BINARY_B_P07_I4H_RECOVERY_R3_20260909.bin`
   - SHA256 `49d454647f0c1d0920a582c2a5aa222b345719a3d6d396374dcb0921560e9414`
8. D1 — `LITERARY_OS_CURRENT_PART_D1_DB59_UNCHANGED_R1_20260909.zip`
   - SHA256 `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
9. D2 — `LITERARY_OS_CURRENT_PART_D2_DB59_UNCHANGED_R1_20260909.zip`
   - SHA256 `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

SYNC-R32 delivery manifest:
`handoff/20260912/SYNC_R32_I4C_INGESTION_GATE_READY_DELIVERY_MANIFEST_R1_20260912.json`

Important: SYNC-R32 was sealed when the I4C unused-scene replication was still at `PACKETS_SEALED / RESPONSES_0 / INGESTION_GATE_READY / MAPPING_CLOSED`. Therefore the package contents alone are **not the latest research state**.

---

## 2. Unchanged operating authorities

These did not change after SYNC-R32:

- Active Development Engine: `P07-I4H Recovery R3`
- Production: `ENG:R47`
- Combined C2 SHA256: `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7`
- DB Authority: DB59 frozen
- DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- Formal scored total: `137`
- Latest formal authority: `R138`
- Formal R140: `0/0/0`

No Production promotion, Active Engine promotion, DB promotion, formal-count increment, or R140 execution occurred.

---

## 3. R4A Track — still frozen and separate

R4A state remains unchanged:

- G6 leak-resistant blind mask: PASS
- G7 duplicate-score / provenance preflight: PASS
- Provider state: `HOLD__REAL_PROVIDER_SECRET_ABSENT`
- Mask = 1
- Independent Judges = 0
- R4A mapping open = 0
- Control/Treatment surfaces remain exact frozen bytes
- No H1-H4 scientific verdict exists yet

Do not infer anything about R4A from the I4C replication. The I4C mapping was legitimately opened after its own independent-evaluator gate; the R4A mapping was not opened and remains separate.

---

## 4. Post-R32 evolution research actually completed

### 4.1 Independent evaluator method inherited from prior I4K-5

Three fresh GPT conversations were used independently as J01/J02/J03. Each evaluator received only its own blind packet and was prohibited from seeing:

- other evaluator results,
- hidden mapping,
- GitHub/Hub,
- historical winner labels,
- prior project result context.

This follows the earlier I4K-5 external multi-GPT pattern: separate fresh conversations, independent attestations, three valid responses sealed before unblind.

### 4.2 Three responses sealed

Canonical response commits:

- J01 commit `76b09dcdee07ae2df1368b5caf1291872ef1f478`
  - SHA256 `6bc7d546dabe96dea8785d4f7f97520fc91cc32ecfeb9a6209a82386180e1799`
- J02 commit `17c3980273625a57352d37aa3fb5fce958c73660`
  - SHA256 `d7128feed3e5a1a7e54bca8cb53f0031d52b996a2a524da3f45e521b627712d2`
- J03 commit `e6a91142ff0d6ae04fd054936f2ab5661ead78ac`
  - SHA256 `92103ff48714a5b2f552c298ec17f74813bb02e38991f216586069fd115317df`

All three satisfied the frozen response contract: 12 opaque scenes exactly once, all 8 axes present with integer 0/1/2 scores, evidence notes present, evaluator/model metadata present, independence attestation=true.

### 4.3 Three-of-three gate

Status:
`PASS__THREE_VALID_RESPONSES__UNBLIND_AUTHORIZED`

- Workflow run `34678041251`
- Job `103511339068`
- Gate receipt SHA256 `711032cc23dcbe25c2f510037ab204c29d5da97632fdb7939fe8c2c7068de4a9`
- Seal commit `8c4f4ec929972ed9f799309ec58fc529dfece989`

Only after this PASS was the I4C replication mapping allowed to be opened.

### 4.4 Exact mapping replay

The I4C replication mapping was reconstructed deterministically from the preregistered frozen seeds and reproduced the pre-release seal byte-for-byte.

- Expected SHA256: `46f8972c408250614761733ac29da956d1f1eecd3b0d3dbe9d14f13877ff2377`
- Replayed SHA256: same
- Mapping bytes: `1501`
- Status: `PASS__EXACT_MAPPING_BYTE_SEAL_REPRODUCED`
- Seal commit: `6b9eb840ba3e8cf88ae5721094f1ae0cb5f826fb`

Again: this applies only to I4C unused-scene replication. R4A mapping remains closed.

### 4.5 Final frozen-rule aggregation

Final result file:
`handoff/20260912/I4C_UNUSED_SCENE_POSITIONAL_REPLICATION_FINAL_RECEIPT_R1_20260912.json`

Final result commit:
`f808af0a0482ba775bcac4df4128726ad5ac0827`

Metrics:

- EARLY mean breadth = `1.0`
- EARLY mean severity = `1.0`
- MIDDLE mean breadth = `2.0`
- MIDDLE mean severity = `2.0`
- LATE mean breadth = `1.75`
- LATE mean severity = `1.75`
- MIDDLE+LATE pooled mean breadth = `1.875`
- MIDDLE+LATE pooled mean severity = `1.875`
- MIDDLE+LATE minus EARLY breadth = `+0.875`
- MIDDLE+LATE minus EARLY severity = `+0.875`
- Individual evaluator direction agreement = `3/3` middle+late worse than early

Frozen strong-positive thresholds:

- breadth delta >= `+1.0`
- severity delta >= `+2.0`
- evaluator directional agreement >= `2/3`

Threshold outcome:

- breadth: FAIL (`+0.875 < +1.0`)
- severity: FAIL (`+0.875 < +2.0`)
- evaluator direction agreement: PASS (`3/3`)

Final scientific decision:
`MIXED_OR_WEAK_REPLICATION`

Interpretation:

- All three independent GPT evaluators saw a directional middle/late degradation signal.
- The effect did not reach the preregistered strong positional-replication thresholds.
- No cross-evaluator median axis reached severity 2 in any scene; material-breadth remained 0 in all strata.
- Therefore the earlier `MIXED_QUALITATIVE_SIGNAL` receives weak directional support, not strong replication.
- This result does **not** authorize a generic renderer patch.

Claim boundary:
Knowledge-only replication on one sealed I4C episode, 12 previously unused scenes, three independent GPT conversations. It is not human consensus, cross-family consensus, population generalization, historical-score rewrite, Formal R140 evidence, or Production promotion evidence.

---

## 5. Runtime / container incident

After R32, the local CAAS/Jupyter/container transport plane repeatedly returned `TransportTimeoutError`, including for very small Python/container calls. GitHub API and GitHub Actions remained operational.

Scientific execution was therefore failovered to deterministic GitHub Actions without changing:

- preregistered samples,
- thresholds,
- evaluator responses,
- mapping,
- scoring rules,
- result classification.

Incident receipt commit:
`313faf92c029df010f925c960ab24409b3e3f3ce`

The new session must not assume the container is still broken. It must test a minimal command first.

---

## 6. Pending physicalization — SYNC-R33

A deterministic R32→R33 delta has already been sealed.

Manifest:
`handoff/20260912/SYNC_R33_PENDING_DETERMINISTIC_DELTA_MANIFEST_R1_20260912.json`

Commit:
`b34a5c0437186afa415dfdc7a30d58284c12a8e7`

Target physical mutation plan:

- Changed, append-only: `CONTROL / A / B2`
- Byte-identical from R32: `B1 / C1 / C2-A / C2-B / D1 / D2`
- Overlay root: `research_sync_r33/`

Required R33 overlay includes at minimum:

1. J01 response
2. J02 response
3. J03 response
4. 3-of-3 gate PASS receipt
5. exact mapping replay verifier
6. exact mapping replay PASS receipt
7. positional replication aggregator
8. final `MIXED_OR_WEAK_REPLICATION` receipt
9. CAAS transport incident/failover receipt

Do not modify or reinterpret those sealed files while physicalizing them.

Required physical audit:

- changed ZIP CRC PASS
- duplicate names = 0
- unsafe paths = 0
- symlink = 0
- encrypted entries = 0
- parent R32 entries preserved
- `research_sync_r33/` overlay byte-identical in CONTROL/A/B2
- unchanged six transports exact SHA equality to R32
- recompute ordered 9 transport SHA256 values
- recompute transport-set root
- generate Delivery Manifest / Physical Audit / Physical Closure / Root Input / SHA256SUMS

Only after all physical audit checks PASS may CURRENT PHYSICAL AUTHORITY move from SYNC-R32 to SYNC-R33.

---

## 7. Mandatory new-session bootstrap order

When the developer supplies the 9 SYNC-R32 packages to a new session:

1. Read `CONTROL` first. Never start from B/C/D.
2. Continue `A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2`.
3. Verify every transport SHA against Section 1 and root `b37a3774...2ffb`.
4. Read Hub `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`.
5. Read `handoff/CURRENT_HANDOFF_POINTER.md`.
6. Read the detailed handoff document referenced there.
7. Understand that the packages stop at R32 ingestion-gate-ready state, while Hub has the later `MIXED_OR_WEAK_REPLICATION` result.
8. Test the container with a minimal command.
9. If container works, **physicalize SYNC-R33 before any new scientific experiment** using the sealed deterministic delta manifest.
10. Audit and close R33.
11. Update all CURRENT pointers to physical SYNC-R33 only after audit PASS.
12. Preserve the R4A frozen branch exactly as Judges=0 / Mapping closed.
13. Only after R33 closure may the next craft-mechanism experiment be preregistered.

---

## 8. Next research after R33 — allowed and forbidden

### Forbidden

- Do not patch renderer based solely on `MIXED_OR_WEAK_REPLICATION`.
- Do not retroactively lower breadth/severity thresholds.
- Do not rewrite the historical I4C verdict.
- Do not open R4A mapping.
- Do not claim R4A independent confirmation.
- Do not promote Production / Active Engine / DB / Formal counts.

### Allowed after R33 physical closure

Design a fresh prospective craft-mechanism study only if the hypothesis is narrower and mechanistically specific. The existing evidence says the middle/late weakness is directional but multi-dimensional and below the strong positional threshold. A new intervention must therefore target a reproducible craft mechanism on fresh/unseen material and keep these layers separate:

`Semantic Architecture → Contract/Load Consumption → Surface Realization → Absolute Surface Hygiene → Relative Effect → Independent Evaluation → Human/Formal Promotion`

---

## 9. Current status token

`PHYSICAL_SYNC_R32__HUB_POST_R32_I4C_MIXED_OR_WEAK_REPLICATION__3OF3_VALID__I4C_MAPPING_EXACT_REPLAY_PASS__R4A_JUDGES_0_MAPPING_CLOSED__SYNC_R33_PHYSICALIZATION_REQUIRED_FIRST`
