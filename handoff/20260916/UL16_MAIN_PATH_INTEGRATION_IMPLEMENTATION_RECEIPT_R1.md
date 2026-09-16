# UL-16 Main-Path Integration Implementation Receipt R1

Date: 2026-09-16
Status: RESEARCH_MAIN_PATH_INTEGRATION_PASS__QUALIFICATION_PENDING__NO_AUTHORITY_CHANGE

## Scope
This receipt closes the previously pending implementation step for the Adaptive Multi-Obligation Showrunner Planner in a research working copy of the R53 runtime source. The Production/Legacy path remains unchanged.

## Exact integration point
Base runtime source SHA256: `b3873e98d8f5df44aee22c388ac9b19bf61cbdafd5f9c09cda7f06952125da55`.

Actual R53 generation spine resides in `LITERARY_OS_RUNTIME_SOURCE_CURRENT.zip`, not in the small Candidate upper overlay. The integration therefore changes the research working copy of:
- `literary_os_runtime/canonical_authoring.py`
- new `literary_os_runtime/adaptive_showrunner_ul16.py`

Candidate routing adds explicit `planning_mode=ADAPTIVE_UL16`; default remains `LEGACY_R53`.

## Implemented repair
`ADAPTIVE_UL16` now executes:
`current cutoff-safe state -> typed obligation portfolio -> due/defer separation -> adaptive sequence graph -> adaptive scene graph -> reverse reconstruction -> existing Canonical Typed IR V2`.

Typed obligation kinds:
`EVENT / THREAD / RELATIONSHIP / CHARACTER / INFORMATION / SOCIAL / PAYOFF`.

The current-state compiler consumes committed event, open thread state, character pressure, relationship obligations/current relationship state, social propagation, episode due/defer, partial payoff, and caller-frozen explicit active obligations where supplied.

DB64 R108 is used only as frozen metrology/distributional prior, never target semantic donor.
- DB64 research SHA256: `19f3c446a73408045d02d4d99e168251dca42da3bfa00abaff1d8f9159d7ea46`
- UL16 prior profile hash: `a89dd2f9dd29635f294432703f2f908e2567ddc7c59acb4a90d910fa62689b22`

## Structural result
Synthetic rich-ensemble integration packet:
- Legacy R53: 9 sequences / 20 scenes, per-sequence scene counts `[2,2,2,3,2,2,2,3,2]`.
- ADAPTIVE_UL16: 9 sequences / 59 scenes, per-sequence scene counts `[10,5,5,5,8,5,8,8,5]`.
- due obligation loss: 0.
- lost deferred debt: 0.
- false deferred fulfillment: 0.
- weaving fraction: 0.889.
- Canonical IR: 70 nodes, validation errors 0.

Current-state-derived mode without explicit rich obligation packet also PASSed:
- compiler mode: `CURRENT_STATE_DERIVED`.
- obligations: 15 total / 14 due / 1 deferred.
- 9 sequences / 67 scenes.
- Canonical IR validation PASS.

Dynamic architecture test with 30 obligations:
- 11 sequences / 97 scenes.
- sequence scene range 5..11.
- uniform-grid detector PASS.
This establishes that 9 sequences is a broadcast floor in this prototype, not an exact generation quota or upper bound.

## Legacy non-regression
Normal-path Legacy output was executed before/after integration using the same frozen packet.
- graph hash before: `f27df4468b4d2a8de1dfe50fdd6508a63dddd3d9dbb67d31eeb4428e39f9af6b`
- graph hash after:  `f27df4468b4d2a8de1dfe50fdd6508a63dddd3d9dbb67d31eeb4428e39f9af6b`
- summary bytes: identical.

All 45 Python source modules in the patched working tree compile successfully.

## Fail-closed fixes found during regression
1. Future-source sentinel correctly raised inside Canonical IR, but `canonical_authoring` previously allowed the exception to escape. Fixed: compile exceptions now return `HOLD / CANONICAL_IR_COMPILE_FAIL` rather than crashing.
2. Unknown planning mode returns `HOLD / UNKNOWN_PLANNING_MODE`.
3. Deferred obligations are pressure/ledger only and are forbidden from scene fulfillment until due.

UL16 regression booleans: all PASS:
- legacy normal path;
- explicit adaptive path;
- broadcast depth;
- deferred integrity;
- current-state-derived compiler;
- dynamic non-fixed architecture;
- future-source leak fail-closed;
- unknown-mode fail-closed.

## Research package
Research runtime ZIP:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R1_20260916.zip`

SHA256: `c1dfda09c97771f56aa88adc402c8fe05a03c0fd2b93205b83dafdc8d2101441`
Size: 18,682,082 bytes.
ZIP CRC: PASS.

Persistent Library path:
`/Literary_OS/Physical_Archive/RESEARCH_UL16_20260916/`

This is research custody, not a new SYNC physical authority.

## Remaining qualification boundary
This implementation PASS does NOT prove literary/showrunner quality. Still required before any physical successor or Production promotion:
1. UL-16 A2 causal-adoption interventions across diverse source-cutoff-safe packets;
2. architecture-only independent blind evaluation at Episode, Sequence and Scene levels;
3. real fresh-context Provider execution with receipts;
4. full broadcast screenplay >=35k chars and reverse-reconstruction / state-carry regression;
5. clean new SYNC build and independent 12-step physical-custody gate.

Authority unchanged:
- SYNC-R53 physical root;
- ENG:R47 Production;
- P07-I4H Recovery R3 Candidate Base;
- DB59 runtime DB;
- DB64 research-support only;
- Formal scored 137 / latest R138 / R140 0/0/0.

Status token:
`UL16__RESEARCH_MAIN_PATH_INTEGRATED__LEGACY_HASH_INVARIANT__ADAPTIVE_EXPLICIT_AND_CURRENT_STATE_PASS__DYNAMIC_SEQUENCE_SCENE_PASS__FUTURE_LEAK_FAIL_CLOSED__CANONICAL_ZERO_ERROR__A2_AND_BLIND_PROVIDER_QUALIFICATION_PENDING`
