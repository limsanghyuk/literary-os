# SESSION RESEARCH & EXPERIMENT LEDGER — R59 THROUGH R62 R1

Date: 2026-09-20
Purpose: durable session research ledger for physical recovery after SYNC-R59.

## Core distinction

Two different authorities MUST NOT be conflated:

1. **Last complete developer-held physical package baseline**
   - SYNC-R59
   - 5 logical Parts / 9 transport packages
   - contains the implemented R62 F01 diversification research candidate before external blind closure.

2. **Current active qualified Candidate**
   - SYNC-R58 / ADAPTIVE_UL16
   - because R62 external blind later failed its frozen qualification gate.

Therefore a new session must start custody/reconstruction from **SYNC-R59 physical bytes**, while treating its executable Candidate as **QUARANTINED research evidence**, not as the currently qualified engine.

## R59 — Output-Only Reverse Reconstruction
Canonical:
`research/provider/20260919/R59_P06_OUTPUT_ONLY_REVERSE_RECONSTRUCTION_RESULT_R1.md`

Status:
`CLOSED_HOLD__TEXT_STATE_RECOVERABILITY_INCOMPLETE`

Key evidence:
- J01 blind result SHA256:
  `d7543baf4488112b577bf0ddf4ec35066bcfa1fd72a8f29bb624cfe3a381f2cb`
- due-now state recoverability: 6/6
- deferred/open recoverability: 2/3
- critical hidden-state dependency: DEFER-3
- finding:
  `ARCHITECTURE_STATE_CAN_EXIST_WITHOUT_SURFACE_EVIDENCE`

Research implication:
Architecture state cannot be auto-committed as factual next-episode state without screenplay evidence.

No engine code change in R59.

## R60 — Text-Derived State Carry Closure
Canonical:
`research/state_carry/20260919/R60_TEXT_DERIVED_STATE_CARRY_CLOSURE_RESULT_R1.md`

Status:
`CLOSED_PASS__DUAL_LEDGER_STATE_CARRY`

Artifacts:
- Text Canonical State Ledger
  SHA256 `46b993addce963c96965e2e81fe633a6044881dc9ba84634e1ccf2ad0cc54d2c`
- Planner Unrealized Obligation Ledger
  SHA256 `a09bf714f293ac94e6a0289d82cbf737637798bc93f099874b68a13eb4d23fb1`
- State Carry Audit
  SHA256 `3c59d3ca7b42f7863a41b3004497546f11784b87bfec13a986f0d69a9020ce0e`

Finding:
`Actual Screenplay -> Text-Derived State -> Evidence Validation -> Canonical Commit`

and separately:

`Unrealized Architecture Obligation -> Planner-Only Queue -> Future Surface Realization Required`

Important boundary:
R60 qualified the research contract/reference ledger.
It did NOT implement the F07 dual-ledger rule into runtime code.

## R61 — Dramatic Realization Causal Map
Canonical:
`research/causal_map/20260919/R61_DRAMATIC_REALIZATION_CAUSAL_MAP_RESULT_R1.md`

Status:
`CLOSED__CAUSAL_MAP_COMPLETE`

Findings:
- F01 Stage Grammar Regularity — SUPPORTED / first priority
- F02 Visible-Action Dependence — UNRESOLVED
- F03 Output-only Reconstruction Gap — SUPPORTED but narrowed
- F04 Semantic Repetition Validator Gap — SUPPORTED
- F05 Human Distribution / Count Pressure — UNRESOLVED
- F06 Scene Necessity Declarative — SUPPORTED
- F07 Screenplay-State / Commit-State Gap — CONTRACT_RESOLVED_RUNTIME_PENDING
- F08 Provider Context Insufficiency — CONTRIBUTOR

Decision:
R62 must isolate only F01.

## R62 — F01 Stage-Grammar Diversification
Preregistration:
`research/interventions/20260919/R62_F01_STAGE_GRAMMAR_DIVERSIFICATION_PREREG_R1.md`

Final external-blind result:
`research/interventions/20260920/R62_F01_STAGE_GRAMMAR_DIVERSIFICATION_EXTERNAL_BLIND_RESULT_R1.md`

### Implementation
Control source:
`adaptive_showrunner_ul16.py`
SHA256:
`42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68`

Treatment source SHA256:
`7c150389a688b4d769b96ade341921a77b7fe86289645c0c613a035c6151a377`

R62 changed only F01 stage/transaction selection.
It did not intentionally patch F04/F06/F07-runtime/F08/DB authority.

### Mechanical transmission
12 fresh paired cases.

Control:
- distinct precursor families: 7
- EVENT / INFORMATION / RELATIONSHIP same-kind diversity: 1 / 1 / 1
- entropy: 2.531148
- repeated stage-path ratio: 0.854167

Treatment:
- distinct precursor families: 10
- EVENT / INFORMATION / RELATIONSHIP same-kind diversity: 4 / 3 / 3
- entropy: 2.807003
- repeated stage-path ratio: 0.791667

Both arms:
- 12/12 architecture validation PASS
- due exactly-once PASS
- deferred preservation PASS
- blocked-precondition preservation PASS
- duplicate concrete action count 0

R58B regression:
- Control 12 sequences / 66 scenes / unique scene functions 12 / PASS
- Treatment 12 sequences / 66 scenes / unique scene functions 19 / PASS

Whole runtime compile:
- 45/45 PASS
- only `literary_os_runtime/adaptive_showrunner_ul16.py` differed after cache removal.

### SYNC-R59 physicalization
Physicalization receipt:
`handoff/20260919/SYNC_R59_R62_PHYSICALIZATION_RECEIPT_R1.md`

Integrated runtime SHA256:
`a6a0e65460948562c2cd7146efcb207a6b02ff77403f67a6bf9049792d95d625`

Candidate overlay SHA256:
`059e10a3b2cb71acf3db8144240ebfebeeac6924daf13fdb2d1858f1a3369e41`

R62 adaptive source SHA256:
`7c150389a688b4d769b96ade341921a77b7fe86289645c0c613a035c6151a377`

C2 logical SHA256:
`ae4fbfbb53c51157890ce45c1f9bf3f5671be4f60e5eed688e5e1f7dc9f95741`

### External blind
J01/J02/J03:
- model/config: GPT-5.6 Sol / High
- independence attestation: true
- 12/12 pairs each
- reported critical violations: 0

Mapped aggregate:
- Treatment wins: 9/12
- ties: 0/12
- Treatment losses: 3/12
- wins+ties: 9/12
- critical Treatment state-fidelity violations: 0

Frozen gate:
- wins >= 7/12 — PASS
- wins+ties >= 10/12 — FAIL
- losses <= 2/12 — FAIL
- no critical violation — PASS

Final:
`R62 = CLOSED_FAIL`
`F01_STAGE_GRAMMAR_DIVERSIFICATION_EFFECT = NOT_QUALIFIED`

Unanimous Treatment-loss clusters:
1. C06_FACTORY_STRIKE
   - investigative THREAD incorrectly mapped to COST_BEARING_CHOICE
   - safe baseline COMPLICATE_THREAD was better.
2. C08_MOUNTAIN_RESCUE
   - relationship boundary negotiation incorrectly mapped to PHYSICAL_RISK_FAILURE
   - safe baseline TEST_BOUNDARY was better.
3. C11_MUSEUM_THEFT
   - unsupported MISINTERPRETATION novelty was injected
   - evidence probe/payoff reuse baseline was better.

Scientific conclusion:
`DIVERSITY_WITHOUT_SEMANTIC_APPLICABILITY_AND_ABSTENTION`

Raw diversification can help, but diversified families must be semantically licensed.
Otherwise:
`ABSTAIN -> SAFE BASELINE`.

## DB continuity
Runtime DB authority remains DB59 frozen:
`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`

DB64 remains development/semantic research DB.
Future consumption doctrine:
`DB64 research fuel + DB59 protected baseline/fallback + identity-safe functional abstraction + utility arbitration + abstention + load/consumption receipts`.

DB64 is never a quota generator and is not Production DB.

## Session-wide authority consequence
- last complete physical package baseline: **SYNC-R59**
- SYNC-R59 scientific status after R62 final gate: **QUARANTINED FAILED RESEARCH SNAPSHOT**
- active qualified Candidate: **SYNC-R58 / ADAPTIVE_UL16**
- Production: **ENG:R47 / LEGACY_R53**
- Production promotion: NONE
- next research number: **R63**
- R63 has not started.

## Runtime incident
At the end of this session, local container / Python execution repeatedly returned:
`TransportTimeoutError`

Classification:
`RUNTIME_TRANSPORT__NOT_SCIENTIFIC_FAILURE__NOT_PACKAGE_CORRUPTION`

This prevents safe new 9-package reseal in the current session.
It does not invalidate existing SYNC-R59 bytes or R59-R62 research evidence.

Status token:
`SESSION_LEDGER_R59_R62__SYNC_R59_LAST_PHYSICAL_BASELINE__R62_FAIL_CLOSED__SYNC_R59_QUARANTINED__ACTIVE_SYNC_R58__R63_NOT_STARTED__CONTAINER_TRANSPORT_HOLD`
