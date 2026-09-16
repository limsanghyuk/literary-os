# RUNTIME / CONTAINER / HUB TURN-BOUNDED EXECUTION PROTOCOL R5

Date: 2026-09-16
Project: Literary OS Development
Classification: MANDATORY TURN / TOOL ORCHESTRATION SAFETY PROTOCOL
Parent: `RUNTIME_CONTAINER_HUB_ATOMIC_EXECUTION_PROTOCOL_R4.md`

## 1. ROOT CAUSE EXTENSION

R4 correctly identified non-atomic long workflows, large-I/O pressure, late checkpointing, and status-classification ambiguity. A further recurring failure mode is now confirmed:

`TURN_ORCHESTRATION_OVERLOAD`.

Observed pattern:
- many dependent tool calls and checks were chained inside one assistant turn;
- Hub writes could finish successfully while the final user-facing completion message had not yet been emitted;
- the user then reasonably perceived another failure/interruption even though the underlying work and pointers were already committed;
- current runtime health at this diagnosis was normal: memory.current about 1.72 GiB of 4 GiB, historical memory.events max remained 117 with delta 0, oom=0, oom_kill=0, /tmp had no >16 MiB residue, and about 27 GiB disk remained free.

Therefore the recurring issue is not package corruption and not current memory failure. It is an orchestration/turn-boundary defect layered on top of the earlier R4 risks.

## 2. TURN-BOUNDED TRANSACTION RULE

Every assistant turn handling substantive engineering work must close one small transaction before expanding scope.

Default transaction shape:
`PRECHECK -> <=1 bounded mutation/experiment -> RECEIPT -> CURRENT POINTER UPDATE -> VERIFY -> USER COMPLETION MESSAGE`.

Do not continue into the next research stage in the same turn after this closure unless the remaining work is purely lightweight and the user-facing completion message is already safe to emit.

## 3. TOOL-CALL BUDGET

Default budget per atomic transaction:
- no more than 4-6 connector/container actions after precheck;
- no more than one heavy filesystem/corpus action;
- no more than one Hub mutation family before checkpoint;
- if additional work is needed, seal the checkpoint and continue as a new transaction.

This is an orchestration safety budget, not a scientific rule.

## 4. USER-VISIBLE COMPLETION GUARANTEE

After a transaction passes:
1. emit a concise completion update/result before starting another deep tool chain;
2. state exactly what is closed and what remains;
3. do not leave the user with only intermediate progress text after the authoritative receipt and pointer have already been written.

## 5. POINTER CONSISTENCY

The canonical resume surface is `handoff/CURRENT_HANDOFF_POINTER.md`.

A transaction that materially changes research state must update that pointer before any next stage. Secondary pointers may then be reconciled in their own bounded transaction if needed. Do not delay the canonical pointer until the end of a long multi-stage turn.

## 6. EXPECTED STATUS HANDLING

A pre-create exact-path 404 is `EXPECTED_ABSENCE` and must be followed immediately by create/receipt handling without narrating it as a new failure.

Likewise, audit-script status 141, optional utility absence, unsupported raw Library materialization, and search-index misses retain the R4 classifications and do not trigger package/scientific invalidation.

## 7. CURRENT UL-16 APPLICATION

The following work is already closed and must not be repeated merely because a previous turn appeared interrupted:
- R4 atomic execution protocol committed;
- UL-16 actual Main-Path research integration receipt committed;
- `CURRENT_NEXT_RESEARCH_POINTER`, `CURRENT_SESSION_RECOVERY_POINTER`, `CURRENT_DEVELOPER_HUB_AUTHORITY`, and `CURRENT_HANDOFF_POINTER` already point to the UL-16 research-integration state;
- physical authority remains SYNC-R53;
- Production remains ENG:R47;
- Candidate Base authority remains P07-I4H Recovery R3;
- DB59 remains runtime DB authority.

## 8. NEXT EXECUTION RULE

The next research stage must start as a fresh R5-bounded transaction: multi-work cutoff-safe structural replay using small derived fixtures. It must not reopen the full 1GB+ corpus unless sealed receipts are insufficient.

## STATUS TOKEN

`RUNTIME_HUB_R5__TURN_ORCHESTRATION_OVERLOAD_CONFIRMED__TURN_BOUNDED_TRANSACTIONS_REQUIRED__CANONICAL_POINTER_BEFORE_SCOPE_EXPANSION__USER_COMPLETION_MESSAGE_BEFORE_NEXT_DEEP_CHAIN__NO_AUTHORITY_CHANGE`
