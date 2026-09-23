# R74–R76 Research Progress R1

Date: 2026-09-23

## Current authority
- Physical Authority: SYNC-R72
- Active Runtime: exact R69
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59 frozen
- Research DB: DB64-R128 research-only
- Operational Level-3: SUSPENDED / REQUALIFICATION REQUIRED

## R74 — F05 Symmetric Measurement
Final status:
`CLOSED_NO_EFFICACY_VERDICT__CANONICAL_R127_RAW_ACCESS_BLOCKED`

Preserved:
- Stage M M1-M7 PASS
- R68 F04 regression 16/16 PASS
- R69 F06 regression 16/16 PASS
- Freeze harness PASS
- R72 R2/R3/R4/R5 exclusion custody recovered
- R3/R4 exact historical selection anchors and R4 20-OK/4-pattern-fail precheck reproduced

Reason for no efficacy verdict:
- canonical preregistration requires exact DB64-R127 raw authority SHA
  `4703e9a99da2deb66eef08f09b08141db6c4d19bc76f77d1c8159dcb7633d6e7`
- original R127 parts still exist in Library custody but current raw-byte materialization policy blocks direct byte verification
- a temporary cohort reconstructed from R128 root planner paths was NOT canonical because the sealed R74 harness enumerates R127 `consumer_ready_r53` paths; that execution is `INVALIDATED_PRE_SCORE__NONCANONICAL_COHORT_ENUMERATION`
- F05 remains NOT QUALIFIED; no Production/Runtime authority change

## R75 — DB64-R128 Causal Schema Consumption
Final status:
`PARTIAL_PASS__CORE_SCHEMA_CAUSALLY_CONSUMED__PAYOFF_AND_EXPLICIT_STATE_DEBT_CHANNELS_NOT_TESTABLE`

Input:
- DB64-R128 logical SHA256:
  `631b002e6bc9c1edb3d33defe3fc9de7e595ac6acbef3d249a4293d03467a91d`
- work: 파라다이스목장
- EP01–EP16 all

Core causal consumption:
- EVENT: 16/16 populated, architecture changed 16/16 under ablation
- INFORMATION: 16/16, changed 16/16
- THREAD: 15/15 populated, changed 15/15
- OWNER/CAST: 16/16, changed 16/16
- future leakage: 0/16

Not testable in this exemplar:
- PAYOFF explicit obligations: 0/16
- relationship_states: 0/16
- character_states: 0/16
- unresolved_payoffs: 0/16
- subplot_debt: 0/16
- character_debt: 0/16

### New consumer defect discovered
EP10 failed because R128_PARADISE_T029 and T030 had the same current_statement/evidence at the current cutoff but distinct dramaturgical labels and source-edge identities.

R75-R2 coalescence was preregistered, then invalidated before repair outputs because the two threads have distinct payoff trajectories.

R75-R3 passed source_edge_id into payoff_ref; duplicate-material collision disappeared, but the exact-R69 mechanical-pattern guard still detected a clone.

R75-R4 repaired the real consumer loss:
- preserve THREAD label as `[THREAD_AXIS:<label>]` in current thread obligation material
- preserve source_edge_id as payoff_ref
- no payoff episode/statement or future source is read

R75-R4 result:
- exact R69 full execution 16/16 PASS
- thread IDs preserved 16/16
- non-thread inputs unchanged 16/16
- future leakage 0
- T029 and T030 both survive as distinct thread obligations

## DB64 structural prior learned for full-scale work
73 verified works / 1,372 episode records:
- sequences median 8; P25–P75 7–11; P90 14
- information shifts median 10; P25–P75 8–16
- payoffs median 3; P25–P75 1–6
- active threads median 6; P25–P75 4–8
- mean cast per sequence median ~3.16
- max cast per sequence median 4

These aggregates only are used as priors; no source story text is copied.

## R76 — Fresh Broadcast-Scale Integrated Episode Qualification
Preregistration SHA256:
`b2395a9daa64d43c243966b71f97926b517a549f149d4d190b9f6a1302dc377e`

Fresh synthetic input SHA256:
`51e5289e6fd8b46b395e1b0e6d07edb6c0e3cb52145dbd2f20b529b7e3479d1e`

Stage A result SHA256:
`6b0d7f208ce60d62905d1c4a234420da72b4936e5c117891b8e51924e50eb9b5`

Stage A status: FAIL
- execution: PASS
- scene count: 52 — scale PASS
- sequence count: 8 — prereg minimum 9 FAIL
- F04 semantic repetition groups: 2 — FAIL
- F06 redundant/mergeable scenes: 0 — PASS
- premature deferred closure: 0 — PASS
- future leakage: 0 — PASS
- physicalization_required missing scenes: 0 — PASS

Runtime issues:
- SEMANTIC_TRANSACTION_REPEAT_GE3
- UNDERDEVELOPED_UNIQUE_SEQUENCE_MATERIAL

### Responsible ancestor localization
Sequence issue:
- exact R69 bundle logic may place up to 4 obligations into one sequence
- two 4-obligation bundles had weak internal cohesion:
  - SQ03: 3 zero-related pairs
  - SQ05: 2 zero-related pairs
- next repair must split weakly coherent bundles by semantic cohesion, not by quota

F04 issue:
- 6 identical ENGAGE_EVENT signatures
- 8 identical PROBE_INFORMATION signatures
- R66 often selects one candidate family and if that candidate fails semantic license, immediately falls back to the baseline instead of trying another licensed semantic family
- full-scale repetition therefore accumulates even when story material differs

## Current next research
Do NOT generate 35,000+ screenplay surface yet; R76 Stage A failed and surface generation would mask an upstream structure defect.

Next:
1. preregister one R76 responsible-ancestor repair
2. repair weak sequence bundle cohesion without obligation cloning or numeric quota padding
3. repair full-scale semantic transaction diversification without relaxing R68 F04 threshold or inventing synonyms
4. rerun the same frozen R76 architecture as engineering retest
5. if it passes, run a fresh R76 replication input
6. only then generate >=35,000-char / >=9-sequence / >=45-scene screenplay surface and external blind evaluation

No Physical Authority, Production, Runtime DB, Operational Level-3, or Formal R140 status changes are claimed here.
