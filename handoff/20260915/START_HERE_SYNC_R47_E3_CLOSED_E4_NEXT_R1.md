# START HERE — SYNC-R47 — E3 CLOSED / E4 NEXT
Date: 2026-09-15

## Current physical authority
SYNC-R47
Root SHA256: `fc259f51e177ce5fb24ec918657966ef116e8ca47aa5f41afcbcf989f40d19f8`
Parent: SYNC-R46
Parent Root: `2aafe621ac2c42e5d9558646c2c16ab45701b4025ea8328d6070fc3843dc0cf1`
Required physical read order: `CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2`

## Level-3 entry gates
- E1 Clean Independent/Human Surface: `CLOSED_PASS`
- E2 DB64 Fuel / Full-Planning: `CLOSED_PASS`
- E3 Fresh Whole-Episode Integration: `CLOSED_PASS`
- E4 Multi-Episode State Carry: `NEXT__NOT_STARTED`
- E5 Fault Injection / Autonomous Recovery: PENDING
- E6 Formal Level-3 Qualification: PENDING
- Level 3: NOT ENTERED

## E3 preserved lineage
E3-R1 is immutable FAIL: `FAIL__CRITICAL_META_LEAKAGE__SAFE_NO_COMMIT`.
It produced a 41,637-character / 10-sequence / 50-scene episode. Planning and semantic audit passed, but SC49 leaked internal validation language (`State Commit / 내부 용어`), violating the frozen zero-meta gate. State Commit = 0.

E3-R2 was a prospectively preregistered targeted recovery of only that final-surface boundary defect. Pre-output implementation R1 failed because of double-escaped regex with scientific outputs 0. An attempted R2 freeze did not actually change the source and was superseded pre-output. Final Implementation R3 passed a synthetic unit test. The scientific run changed exactly one line of the frozen E3-R1 surface. Final output: 41,583 chars / 10 sequences / 50 scenes, mechanical PASS, semantic/state PASS, `STATE_COMMIT`, verdict `PASS__E3_FRESH_WHOLE_EPISODE_INTEGRATION_CLOSED`.

## Research-history read order
1. `handoff/CURRENT_SESSION_RECOVERY_POINTER.md`
2. this file
3. `handoff/20260915/RESEARCH_EVOLUTION_MAP_R2.json`
4. `handoff/20260915/LEVEL3_ENTRY_GATE_LEDGER_R4.json`
5. individual immutable experiment records/evidence packages

No FAIL, SUPERSEDED, ABORTED, pre-output implementation incident, claim boundary, or duplicate branch may be silently erased.

## Next legal action
Preregister E4 Multi-Episode State Carry from the committed E3-R2 episode state. E4 must test at least three consecutive committed episode states, including the E3 committed episode as the starting episode in the carry chain or an explicitly frozen successor chain, with no state reset between episodes.

## Unchanged system authorities
- Active Engine: `P07-I4H Recovery R3`
- Production Engine: `ENG:R47`
- Formal scored total: `137`
- Latest Formal: `R138`
- Formal R140: `0/0/0`
- DB64 remains non-Production
