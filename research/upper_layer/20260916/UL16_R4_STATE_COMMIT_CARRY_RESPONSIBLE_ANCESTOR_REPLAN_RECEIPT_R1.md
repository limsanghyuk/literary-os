# UL-16 R4 State Commit/Carry + Responsible-Ancestor Replan Receipt R1

Date: 2026-09-16
Status: `PASS_AFTER_DEFECT_REPAIR__STATE_COMMIT_CARRY__RESPONSIBLE_ANCESTOR_REPLAN__NO_AUTHORITY_CHANGE`
Parent runtime: canonical UL-16 R3 semantic-architecture research runtime.
Execution rules: R6 Authority Sync Gate + R5 Turn-Bounded + R4 Atomic Execution.

## 1. Authority precheck
Parent package:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R3_SEMANTIC_ARCH_PASS_20260916.zip`

Parent SHA256:
`495acdc8957c8085e10c22e3a6af3c455be31c73fe1d793242e62e26e224eee8`

The user-supplied/local R3 bytes were rehashed before execution and exactly matched the Hub pointer. ZIP CRC: PASS. Historical cgroup `memory.events max=117`; current transaction delta remained 0; OOM/OOM-kill remained 0.

## 2. Frozen regression evidence
Primary prereg SHA256:
`b4c428979a5a1df0a8316ce7ff3bcbdf452b8f705036d684b6189af495fa3ddb`

Primary cutoff-safe state/carry fixture SHA256:
`48a2293a9cde80c83ee20f8e68a1e876297c20d256d9dfde03a5cc1b86303011`

R3 baseline result SHA256:
`a0d5e7bddcbbac4dd42e20616fc8e060498fb38ac5cde4aefef2100252d2e17f`

Post-fix primary result SHA256:
`43508426885513c39970bfa4cbc84e9ed1d909ad2b14fcd2b25551735e5fa49a`

Full-integration compatibility fixture SHA256:
`d7db7f87afd27f2033fa84b10988a2b75327fb62707c5d390bde9949802ea986`

Full-integration result SHA256:
`e7fe12d1d2e32acbc3b5c6fe219a8a428a7c13adcfeef9022868ce8c87060b15`

A syntax typo in the first compatibility-fixture JSON (`.93`-style number) caused a parser stop before any experiment result existed. It was classified `AUDIT_SCRIPT`, corrected to valid JSON, rehashed, and then executed under the frozen gates above.

## 3. R3 baseline defects confirmed
The exact R3 parent showed the following state-consumption defects:
- relationship state committed generic `RELATIONSHIP_MOVES / RELATION_PRESSURE_HELD` instead of the concrete Scene semantic delta;
- information state was not committed;
- social-ecology state was not committed;
- deferred residue was not carried into a next-state obligation registry;
- no Responsible-Ancestor selector/replan directive existed.

The R3 hash chain and basic event commit still worked; the defect was semantic state consumption and replanning scope, not generic commit availability.

## 4. R4 repair scope
Only three runtime Python files changed relative to R3:
- `literary_os_runtime/state_replanning_integrity.py`;
- `literary_os_runtime/adaptive_showrunner_ul16.py`;
- `literary_os_runtime/__init__.py`.

Repair behavior:
1. compile exact semantic commit packets from canonical/projected Scene contracts;
2. ignore generic placeholder anchors as state mutations;
3. deduplicate repeated scene realization of the same semantic delta;
4. commit exact relationship / information / social-ecology deltas;
5. carry deferred obligation IDs together with their original adaptive-portfolio metadata;
6. preserve canonical state-hash chaining;
7. let the next-episode Active Obligation Compiler consume carried relationship / information / social / deferred state;
8. select the lowest responsible ancestor among `SCENE / SEQUENCE / EPISODE / SERIES`;
9. emit `EPISODE` replan for ordinary cross-episode semantic carry;
10. fail closed on attempts to mutate immutable series anchors.

## 5. Same primary fixture after repair
Exact semantic state is now committed and carried:
- A-B relationship delta preserved exactly;
- information delta preserved exactly;
- both GUILD and CITY social-ecology state deltas preserved exactly;
- deferred `REL-DEF-1` preserved;
- prior/new state hash chain PASS;
- next-episode portfolio reconsumes the exact carried relationship/information/social values;
- deferred obligation remains `due=false`;
- normal cross-episode semantic carry selects Responsible Ancestor = `EPISODE`.

Responsible-Ancestor selector probes:
- one local scene -> `SCENE`;
- multiple scenes in one sequence -> `SEQUENCE`;
- multiple sequences -> `EPISODE`;
- series-anchor touch -> `SERIES`.

Only eight Scene contracts in the primary fixture actually contributed semantic/deferred state to the replan signal after precision repair; unrelated scenes are no longer counted as affected merely because they exist in the episode.

## 6. Full CIG -> Commit -> Carry -> Next-Portfolio integration regression
A separate balanced cutoff-safe compatibility fixture passed the actual adaptive/CIG/canonical route.

Result:
- Adaptive validation: PASS;
- sequence count: 9;
- scene count: 55;
- Canonical Typed IR: PASS;
- Canonical node count: 66;
- Canonical errors: 0;
- Canonical graph hash: `3af644aa9e9724d92bad2578c91e34f35b9da7ca866c31265ff35c638f8c4533`;
- State Integrity status: PASS;
- canonical state carry committed: true;
- state hash chain: PASS;
- exact A-B and C-D relationship deltas: PASS;
- exact B/C information deltas: PASS;
- exact GUILD/CITY social deltas: PASS;
- deferred `RD` carried: PASS;
- next-episode portfolio reconsumption: PASS;
- Responsible Ancestor: `EPISODE`;
- replan decision: `REPLAN_REQUIRED`.

An attempted mutation of immutable series anchor `premise` selected `SERIES` scope but returned `BLOCK`; the committed immutable anchors remained byte-equivalent in the state object.

## 7. Legacy invariance
The legacy no-Scene-semantic commit path was executed on identical input in:
- original canonical R3 package;
- repaired R4 working runtime.

Complete output + trace SHA256 for both:
`d9d618b3d8ce0fbf88617f79c5018360af385584986d3da85982c7a3d6c9f8ae`

Decision: `LEGACY_STATE_CARRY_EXACT_OUTPUT_TRACE_INVARIANT = PASS`.

Thus the new semantic carry/replan path is Candidate/adaptive-only at the state-consumption boundary; the existing legacy commit behavior is preserved.

## 8. Software/runtime regression
- Runtime Python compile: 45/45 PASS.
- Current transaction `memory.events max`: 117 -> 117, delta 0.
- OOM: 0.
- OOM-kill: 0.

## 9. R4 research package
Package:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R4_STATE_CARRY_REPLAN_PASS_20260916.zip`

Size:
`18,658,253 bytes`

SHA256:
`4fc6411ff91a2f524a0ed2bafc61a6ce98cc80b13521b804a27dd46cf1931558`

ZIP CRC:
PASS.

Entries:
440.

Persistent Library path:
`/Literary_OS/Physical_Archive/RESEARCH_UL16_20260916/LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R4_STATE_CARRY_REPLAN_PASS_20260916.zip`

Library presence/listing verified. Independent external durable archive re-download/re-hash is not claimed.

## 10. Interpretation boundary
This transaction closes a software-level question:

`adaptive semantic Scene state -> canonical State Commit -> next-state Carry -> next-episode obligation consumption -> responsible-ancestor replan directive`

is now wired and regression-tested.

It does NOT establish:
- human-level dramatic architecture;
- independent blind architecture quality;
- real OpenAI Provider execution;
- full >=35k screenplay quality;
- physical Candidate promotion.

`UPPER_LAYER_GENERATIVE_QUALITY` remains `NOT_YET_QUALIFIED`.

## 11. Authority impact
None.

Unchanged:
- Physical baseline: SYNC-R53;
- Production Engine: ENG:R47;
- Candidate Base authority: P07-I4H Recovery R3;
- runtime DB authority: DB59 frozen;
- DB64: research-support candidate only;
- Formal total: 137; latest R138; R140 0/0/0.

R4 is research runtime evidence only.

## 12. Next bounded transaction
The next R6+R5 transaction is **independent architecture-only blind evaluation** at Episode / Sequence / Scene-plan levels, using current R4 bytes after SHA synchronization.

Do not start real Provider screenplay generation until the architecture-only blind gate closes.

## STATUS TOKEN
`UL16_R4__STATE_COMMIT_CARRY_EXACT_SEMANTICS_PASS__NEXT_EPISODE_RECONSUMPTION_PASS__RESPONSIBLE_ANCESTOR_SCENE_SEQUENCE_EPISODE_SERIES_PASS__IMMUTABLE_SERIES_ANCHOR_BLOCK_PASS__CANONICAL_66_NODE_PASS__LEGACY_EXACT_INVARIANT__NEXT_ARCHITECTURE_BLIND__NO_AUTHORITY_CHANGE`