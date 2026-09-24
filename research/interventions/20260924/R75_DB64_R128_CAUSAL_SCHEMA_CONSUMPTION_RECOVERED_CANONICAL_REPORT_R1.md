# R75 DB64-R128 Causal Schema Consumption — Recovered Canonical Report R1

Date: 2026-09-24
Recovery status: RECOVERED_FROM_DURABLE_HUB_PROGRESS_RECORD_AND_SEALED_SESSION_EVIDENCE
Authority effect: NONE

## Why this recovered report exists

The durable Hub contains the canonical summary:
research/interventions/20260923/R74_R75_R76_PROGRESS_R1.md

However, several detailed per-run R75 JSON artifacts created during the session were not individually committed before later runtime/container disruption.

This report does NOT invent new results.
It consolidates the R75 design, execution method, repair lineage, and final result already recorded in the durable progress record so a fresh session does not have to reconstruct R75 from conversation memory.

## Research question

Does DB64-R128 human-dramaturgy analysis causally change exact-R69 planning/runtime decisions, rather than merely existing in storage or being retrieved?

## Frozen research input

- Research DB: DB64-R128
- Logical SHA256: 631b002e6bc9c1edb3d33defe3fc9de7e595ac6acbef3d249a4293d03467a91d
- Work: 파라다이스목장
- Episodes: EP01-EP16, all
- Runtime: exact R69
- Runtime SHA256: 3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1
- Runtime DB authority remained DB59; DB64-R128 was research-only.

## Causal-consumption method

For each populated schema channel:
1. Hold all other candidate input fixed.
2. Run exact R69 with the full DB64-derived input.
3. Ablate one channel only.
4. Rerun exact R69.
5. Compare portfolio / due-defer / owner / sequence / scene architecture decisions.
6. If removing the channel changes relevant decisions, the channel is causally consumed at the planning/runtime layer.
7. Empty channels are reported NOT TESTABLE / NOT CONSUMABLE; they are never imputed.

Channels tested:
- EVENT
- INFORMATION
- PAYOFF
- THREAD
- OWNER/CAST
- explicit relationship_states
- character_states
- unresolved_payoffs
- subplot_debt
- character_debt

## Initial defect

EP10 failed under exact R69 because:
- R128_PARADISE_T029
- R128_PARADISE_T030

shared the same current_statement/evidence at the current cutoff while representing distinct dramaturgical thread axes and source-edge identities.

This exposed a DB-to-consumer information-loss defect:
the DB carried distinct thread semantics, but the consumer passed insufficient identity into exact R69.

## Repair lineage

### R75-R2
Proposed coalescing the two thread rows.

Disposition:
INVALIDATED_BEFORE_REPAIR_OUTPUTS.

Reason:
The two threads had distinct payoff trajectories.
Merging them would erase legitimate dramaturgical identity.

### R75-R3
Preserved source_edge_id by passing it into payoff_ref.

Effect:
- duplicate-material collision removed
- exact-R69 mechanical-pattern guard still saw a clone

Disposition:
CLOSED_FAIL__PATTERN_COLLISION_REMAINS

### R75-R4
Final bounded consumer repair.

Rules:
- THREAD only.
- Preserve the DB thread label in consumer material as:
  [THREAD_AXIS:<label>]
- Preserve source_edge_id as payoff_ref.
- Do not read payoff_episode.
- Do not read payoff_statement.
- Do not read target/future source.
- EVENT / INFORMATION / PAYOFF rows remain unchanged.

Result:
- exact R69 full execution: 16/16 PASS
- thread IDs preserved: 16/16
- non-thread inputs unchanged: 16/16
- future leakage: 0
- T029 and T030 survive as distinct obligations

## Final causal-consumption result

Final status:
PARTIAL_PASS__CORE_SCHEMA_CAUSALLY_CONSUMED__PAYOFF_AND_EXPLICIT_STATE_DEBT_CHANNELS_NOT_TESTABLE

Populated channels:
- EVENT: 16/16 populated; architecture changed under ablation 16/16
- INFORMATION: 16/16 populated; changed 16/16
- THREAD: 15/15 populated; changed 15/15
- OWNER/CAST: 16/16 populated; changed 16/16
- future leakage: 0/16

Not testable in this exemplar:
- PAYOFF explicit obligations: 0/16
- relationship_states: 0/16
- character_states: 0/16
- unresolved_payoffs: 0/16
- subplot_debt: 0/16
- character_debt: 0/16

## Claim boundary

R75 establishes causal consumption only for populated EVENT / INFORMATION / THREAD / OWNER-CAST channels at the exact-R69 planning layer on the R128 exemplar.

It does NOT establish:
- causal consumption for empty channels
- DB64 runtime adoption
- screenplay quality
- Production promotion
- Operational Level-3
- Formal R140

## Canonical source of truth

Primary durable historical summary:
research/interventions/20260923/R74_R75_R76_PROGRESS_R1.md

This recovered report exists to make R75 directly reconstructable from Hub without relying on chat memory.
