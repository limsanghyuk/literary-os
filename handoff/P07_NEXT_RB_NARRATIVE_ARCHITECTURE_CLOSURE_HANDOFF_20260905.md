# P07 R-B Narrative Architecture Closure — Next-Session Handoff
Date: 2026-09-05
Status: NEXT ACTIVE PREFORMAL PHASE / NONFORMAL / NOT YET EXECUTED
Formal count delta: 0

## Purpose
Close the gap between historically validated narrative architecture and the current P07 Verified Closed Loop by proving actual LLM -> Runtime -> LLM consumption and downstream behavioral effect.

## Why R-B is required before Live Craft Parity
Mechanical parity and renderer preservation are insufficient if the engine is still missing or weakening major planning consumers. Live Reference-vs-Engine craft parity should not be run on an incomplete narrative architecture.

## Required active layers
1. Whole Story / Long Arc Constraint Map.
2. Episode Allocation with explicit distributed ownership obligations.
3. Social Ecology Graph.
4. Group Membership / Group Role / Group Pressure.
5. Event Ownership / Plot-Axis Ownership.
6. Detailed Episode Synopsis Plan.
7. THICK Sequence Functional Plan.
8. Sequence Boundary Contract.
9. Scene Plan / Scene Contract.
10. LLM Surface Renderer, with Python prose generation = 0.

## Social Ecology Graph minimum schema
Each active character/group relationship should support:
- character_id / group_id
- membership_type
- role_in_group
- obligation
- resource_or_information_control
- pressure_from_group
- pressure_on_group
- relationship_edges
- independent_goal
- opposition_or_dependency
- active_thread_ids
- event_ownership_ids
- episode_due_or_defer

## Event / Plot-Axis Ownership minimum schema
Each major event or plot axis should support:
- event_id / axis_id
- primary_owner_character_or_group
- initiator
- opposition
- information_owner
- resource_owner
- affected_relationships
- affected_threads
- causal_preconditions
- episode_due_or_defer
- expected_value_shift
- downstream_sequence_ids

Hard rule: protagonist ownership must not be the default. The engine must demonstrate distributed ownership across independent characters/groups when supported by the source/state and episode design.

## Detailed Episode Synopsis obligations
A detailed episode synopsis must explicitly contain:
- episode dramatic function in the whole story
- opening state and terminal state
- primary/secondary plot axes
- ensemble distribution plan
- event ownership map
- thread due/defer map
- relationship movements
- information releases/withholds
- escalation ladder
- midpoint or major structural turn
- terminal pressure / cliff / closure balance
- sequence functional slots to be lowered next

A generic EPISODE_PLAN label is not sufficient unless these obligations are physically present and consumed.

## THICK Sequence + Boundary obligations
Each sequence must carry at minimum:
- goal
- obstacle
- value_shift
- turn_type
- pov_char
- cast_functions
- event_movement
- information_shift
- relationship_movement
- thread_movement
- entry_state
- exit_state
- runtime_share
- boundary trigger/closure rationale

## Consumer Fidelity gates
For every parent->child edge:
- field exists,
- child prompt/request receives it,
- provider receipt records relevant policy/input hashes,
- output behavior changes under preregistered mutation,
- critical parent semantics are preserved or explicitly transformed,
- missing critical consumption -> HOLD.

Mandatory edges:
Whole Story -> Episode Allocation
Episode Allocation -> Social Ecology/Event Ownership
Social Ecology/Event Ownership -> Detailed Episode Synopsis
Detailed Episode Synopsis -> THICK Sequence
THICK Sequence/Boundary -> Scene Plan
Scene Plan -> Renderer Packet

## Mutation/negative controls
Before natural-quality evaluation, inject one controlled defect per layer and prove detection/propagation:
- remove a non-protagonist event owner -> ownership gate must HOLD or replan;
- collapse all group memberships into protagonist axis -> ecology gate must detect protagonist bias;
- delete relationship movement from a due thread -> synopsis/sequence contract must fail;
- replace THICK sequence with thin goal-only sequence -> consumer-fidelity gate must detect missing fields;
- mismatch boundary exit->next entry -> continuity gate must HOLD;
- make event due/defer inconsistent with episode allocation -> allocation/synopsis gate must HOLD.

## Pass conditions — engineering closure only
- all required layers physically called in the verified route;
- provider/request receipts contain research-policy and parent-state hashes;
- critical consumer fields present and used at every edge;
- preregistered mutations detected 100% for critical cases;
- protagonist-only collapse blocked;
- no Python literary prose;
- source/entity/future-source critical violations = 0;
- low-confidence retrieval still uses NO_RETRIEVAL;
- no production promotion claim.

## After R-B only
Proceed to R-C Candidate Portfolio/Critic/R82 safe selection, then R-D long-horizon carry/rollback/Authorized Novelty, then R-E voice/texture, then live craft parity.

## Execution note
At session end the local CAAS backend is unavailable. This document is a handoff design, not an execution result or sealed preregistration package. New session must first reseal authority packages, then freeze a physical R-B preregistration before any R-B outputs are generated.
