# CURRENT DATABASE RESEARCH POINTER
Last updated: 2026-09-09

## Current database research result
`P07_DB64_9CONTRACT_CONSUMER_QUALIFICATION_R1`

Classification:
`HOLD_FOR_DATA_REPAIR__ENGINE_A2_PROVENANCE_INVARIANCE_REPAIR_REQUIRED__NO_DB_AUTHORITY_PROMOTION`

Result document:
`handoff/20260909/P07_DB64_9CONTRACT_CANDIDATE_QUALIFICATION_R1_RESULT_20260909.md`

Result commit:
`a17e4e8fcf8fd3510995caa347202d2ab7d8ec57`

## Authority boundary
- Active physical authority remains `CURRENT_PHYSICAL_AUTHORITY__P07_I4H_FAIL_CLOSED_RUNTIME_RECOVERY_R3`.
- DB59 remains frozen SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
- DB64 remains a candidate and is not adopted.
- Semantic Alignment Virtual R1 remains a separate candidate; its Live gate is still pending.
- Production ENG:R47, Formal 137, R140 0/0/0, I4I 0/0/0/0 unchanged.

## What passed
- candidate physical integrity and exact 595/595 cross-package pairing;
- zero JSON/JSONL parse errors;
- 식객 C1/C2/C4 118/118;
- selected A2 dependency mutation changes selected semantic/provider-facing content;
- no false Consumer-Ready-A promotion claim;
- current parent engine regression 258/258 PASS.

## Blockers
Data-side:
- PlannerInput unresolved-payoff schema generations are not uniform: thread_id objects, edge_id-only objects, and strings coexist;
- current R3 NAP generates `THREAD:None` for 시티헌터/식객 and exceptions for 스카이캐슬/스타일/시그널/시크릿가든;
- EP01 ThreadState missing for 신사의품격/신의퀴즈1/신화;
- C3/C5/A1/G1/G2 hardening/normalization remains required.

Engine-side:
- unrelated unselected mutation changes full provider-facing payload through global snapshot provenance; this reproduces on frozen DB59 as well;
- full NKB path is authority-locked to DB59, so a later DB64 pilot needs an explicit candidate authority adapter rather than relabeling.

## Next exact order
1. Reinforcement GPT produces a NEW DB64 candidate version with the data-side repairs; preserve current HOLD candidate unchanged.
2. In a separate preregistered engine cycle, repair A2 semantic-selection/provenance separation and null/duplicate evidence-ID fail-closed handling.
3. Re-run DB64 qualification from the frozen control conditions.
4. Only if qualification passes, run paired DB59-vs-DB64 comparative utility under equal packet budget/source cutoff/engine settings.
5. Do not proceed to DB adoption or I4I on the basis of the current DB64 candidate.
