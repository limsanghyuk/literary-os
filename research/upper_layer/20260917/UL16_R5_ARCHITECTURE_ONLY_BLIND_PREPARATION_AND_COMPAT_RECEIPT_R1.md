# UL-16 R5 Architecture-Only Blind Preparation + Control Compatibility Receipt R1

Date: 2026-09-17
Status: `PACKETS_SEALED__JUDGMENTS_0__INDEPENDENT_GATE_PENDING__PROVIDER_BLOCKED__NO_AUTHORITY_CHANGE`
Execution rules: R6 Authority Sync Gate + R5 Turn-Bounded + R4 Atomic Execution.

## 1. Parent authority sync
Parent research runtime:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R4_STATE_CARRY_REPLAN_PASS_20260916.zip`

Parent SHA256:
`4fc6411ff91a2f524a0ed2bafc61a6ce98cc80b13521b804a27dd46cf1931558`

The local/uploaded bytes were rehashed and ZIP-tested before this transaction. Exact Hub match: PASS. Historical `memory.events max=117`; current transaction delta remained 0; OOM/OOM-kill remained 0.

## 2. Pre-blind compatibility defect found
While generating the Legacy Control arm, Canonical IR validation failed on every Legacy SceneIR because R3 semantic-hash validation expected `semantic_topology_hash` and `semantic_state_deltas_hash`, fields that unchanged Legacy scene contracts predate.

This was a backward-compatibility defect introduced at the canonical validation boundary, not a Legacy planning-content defect.

Repair:
- when those two semantic hashes are absent, derive deterministic hashes from the existing/empty Legacy semantic topology and state-delta objects at the Canonical boundary;
- do not alter Legacy Episode/Sequence/Scene planning content;
- do not alter Candidate semantic contracts when hashes are already present.

Verification:
- Candidate probe graph before repair: `b3c9c7a7bffb317f590b51f6e6b51aa8c6632ec5567c166c396da212e5f82cc5`;
- Candidate probe graph after repair: same exact hash;
- Candidate output invariance: PASS;
- Legacy probe before repair: `HOLD__CANONICAL_IR_VALIDATION_FAIL`;
- Legacy probe after repair: PASS, 9 sequences / 20 scenes / 31 Canonical nodes;
- Python runtime compile: 45/45 PASS.

Compatibility receipt JSON SHA256:
`e32a07e7f66dacd551262b8bca416bf2e913d75d791a391e624c8054c67c6c8d`.

## 3. R5 research runtime
Package:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R5_ARCH_BLIND_COMPAT_20260917.zip`

SHA256:
`922f9e6ec6f98a4016467f670669b6d16c6866e20c92d5f9ada71e925dd1fd99`

Size:
`19,151,872 bytes`

ZIP CRC: PASS.

Persistent Library:
`/Literary_OS/Physical_Archive/RESEARCH_UL16_ARCH_BLIND_20260917/LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R5_ARCH_BLIND_COMPAT_20260917.zip`

R5 is research evidence only; it does not supersede SYNC-R53 or Production ENG:R47.

## 4. Frozen architecture-only blind design
Six cutoff-safe synthetic current-state architecture pairs were generated before prose rendering. Each pair uses the same input context for both systems and includes Episode Plan, Sequence Plan and Scene Plan only.

Evaluation axes frozen before judgments:
1. Episode multi-strand architecture;
2. Sequence functional diversity;
3. Ensemble/relationship weaving;
4. Information asymmetry use;
5. Social-ecology integration;
6. Scene transaction specificity/necessity;
7. Causal/state continuity;
8. Escalation/turning architecture.

Judges are instructed to reward causal weaving, not raw counts; penalize fixed grids, repetitive phase inflation, generic repeated beats and redundant scenes; and penalize architectures too shallow for a plausible broadcast episode.

Independent gate frozen before external judgments:
- judges: 3;
- pairs per judge: 6;
- total judge-pair judgments: 18;
- Candidate pair wins >=12/18;
- Candidate wins+ties >=15/18;
- no critical-violation majority.

Critical violations:
- future-source leakage visible in packet;
- due-now obligation omitted at architecture level;
- deferred obligation falsely closed;
- arm-identifying implementation leakage.

## 5. Blind packet integrity
Three external/fresh-context judge packets were produced: J01/J02/J03.

Each packet:
- contains six A/B pairs;
- has Candidate in A exactly three times and B exactly three times;
- contains no `ADAPTIVE_UL16`, `LEGACY_R53`, `UL16`, `ENG:R47`, `R53`, `planning_mode`, `grammar_id`, `CANDIDATE`, or `CONTROL` arm-identifying token;
- was hashed before any external judgment.

J01:
- packet SHA256 `605eacf8f8542c933ae3ef749e3fa467f8d2b8aa5d5cddc72ca29e7fd1f7210d`
- ZIP SHA256 `82f884cd44aff82ccb09b6e4177cb648430522ea08a9c5c525e844cfe755efbb`

J02:
- packet SHA256 `1ca063b826c7606aa051e590782f513b40d245e46f2d33247ad4da733fbcd046`
- ZIP SHA256 `e3f2b9261cbbb89a1c7366e70c9664e3034a59572b4c78da93b6371bd9d33424`

J03:
- packet SHA256 `37c195b762cb238b0935fd4bf55da34d089c0c042d0a42ab74bfead71fa12656`
- ZIP SHA256 `26400c321bb584ef748110a369097272140dec29dfd9e07a0a27209d810631b5`

Public three-judge packet set ZIP SHA256:
`f0c2e38e9b6579d068ee3c7a16e0774265f2f5bbc32c7dbe8293ba941bb06fdc`.

Coordinator secret SHA256:
`68a47e25006b3908362afe4bc5ef230244c63f3a108b51d78dd5938c287627d6`.

Public manifest:
`research/upper_layer/20260917/UL16_R5_ARCHITECTURE_BLIND_PUBLIC_MANIFEST_R1.json`.

## 6. Internal diagnostic — NOT independent evidence
A same-session blind deterministic diagnostic was run only as a preflight/risk detector. It is explicitly NOT counted toward the independent gate.

Two opposing signals were observed:
- Candidate preserved the exact supplied relationship/information/social/visible-action semantic targets at 100% across all six fixtures, while Legacy exact-target coverage was 0%;
- Candidate architecture expanded to 90..103 scenes, while Legacy remained 20 scenes, and the Candidate repeatedly realized one obligation through several generic phase scenes.

This exposes the precise question the external blind judges must decide: whether Candidate breadth and semantic fidelity form coherent dramaturgical architecture, or whether phase expansion creates redundant/bloated planning despite better state coverage.

The same-session assistant does not count as an independent judge and no independent winner is claimed from this diagnostic.

## 7. Independent gate status
Current external/fresh-context sealed judgments received: **0/3 judges, 0/18 pair judgments**.

Therefore:
`INDEPENDENT_ARCHITECTURE_BLIND_GATE = PENDING`.

Real Provider screenplay generation remains BLOCKED until the three sealed judge results are collected and mapping is revealed only after judgments are sealed.

## 8. Authority impact
None.

Unchanged:
- Physical baseline: SYNC-R53;
- Production: ENG:R47;
- Candidate Base authority: P07-I4H Recovery R3;
- runtime DB authority: DB59 frozen;
- Formal total: 137; latest R138; R140 0/0/0.

## 9. Exact next bounded transaction
The next transaction is only:
1. obtain sealed J01/J02/J03 independent/fresh-context JSON judgments without mapping exposure;
2. verify judge packet hashes and response schema;
3. freeze all judgments;
4. reveal coordinator mappings;
5. compute 18 pair outcomes and critical-violation gate;
6. seal the independent architecture-blind result and update CURRENT pointer.

Do not start real Provider screenplay generation before this gate closes.

## STATUS TOKEN
`UL16_R5__ARCHITECTURE_BLIND_PACKETS_SEALED__R5_LEGACY_CANONICAL_COMPAT_PASS__CANDIDATE_OUTPUT_INVARIANT__JUDGMENTS_0_OF_3__INDEPENDENT_GATE_PENDING__PROVIDER_BLOCKED__NO_AUTHORITY_CHANGE`
