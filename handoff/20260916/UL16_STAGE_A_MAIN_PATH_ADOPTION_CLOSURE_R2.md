# UL-16 Stage A Main-Path Adoption Closure R2

Date: 2026-09-16
Status: **STAGE_A_CLOSED_PASS__A2_STAGE_B_NOT_STARTED__NO_AUTHORITY_CHANGE**
Preregistration: `handoff/20260916/UL16_CAUSAL_ADOPTION_AND_PROVIDER_QUALIFICATION_PREREG_R1.md`

## Treatment identity
Research-only Candidate planning mode: `ADAPTIVE_UL16`.
Schema generation: `UL16R2`.
Treatment planner code hash: `6202ccba9811ca8c76c4b8ac1c82513f82b7ab1a8cb295346ac8a58b0961c8b3`.
- `adaptive_showrunner_ul16.py` SHA256 `4fbcc494fd5e798c56a81b47ce451b065fd6bc81b108df234dbf362325e12342`
- `canonical_authoring.py` SHA256 `cb338861226323a260ff744710873e2114c485ae89f9b2acf68d7d145bc236f8`

Research runtime package R2:
`LITERARY_OS_UL16_CANDIDATE_RUNTIME_SOURCE_RESEARCH_R2_20260916.zip`
- size 18,674,002 bytes
- SHA256 `f9bdb52f93af1d3878f5d75e16db4d67304456ba78f823e253577265224b9aad`
- ZIP CRC PASS
- persistent Library path: `/Literary_OS/Physical_Archive/RESEARCH_UL16_20260916/`

R1 research runtime remains historical evidence only and is superseded for further UL-16 research by R2. Neither is a SYNC authority.

## Why R2 was required
The first Main-Path integration exposed additional correctness gaps before Stage A could be sealed:
1. a dependent obligation could be unlocked merely because its prerequisite object existed even when the prerequisite was deferred;
2. dependency cycles/unsatisfied prerequisites needed fail-closed disposition;
3. payoff/deadline urgency needed a frozen pressure threshold for due/defer causal testing;
4. owner-concentration diagnostics incorrectly counted deferred/blocked owners as currently schedulable owners;
5. new `BLOCKED_PRECONDITION`, pressure-disposition and pre/post-state semantics required an explicit schema version bump to prevent schema/consumer drift.

R2 fixes:
- `DUE_PRESSURE_THRESHOLD = 0.80` for non-explicit `can_defer` obligations;
- dependency closure accepts a prerequisite only when already satisfied or actually schedulable in the selected-due DAG;
- unresolved/missing/deferred/blocked/cyclic dependencies produce `BLOCKED_PRECONDITION`;
- blocked obligations cannot appear as fulfilled scene transactions;
- diversity/concentration diagnostics use schedulable due owners, not blocked/deferred owners;
- schemas bumped to `AdaptiveObligationPortfolioUL16R2`, `AdaptiveSequenceGraphUL16R2`, `AdaptiveSceneGraphUL16R2`;
- compatibility lowerer marks `UL16_ADAPTIVE_MULTI_OBLIGATION_R2` / grammar `UL16-R2`.

## Stage A public Main-Path conformance — 14/14 PASS
Frozen rich-ensemble packet through the public `run_candidate_canonical_planning` Candidate route:
- public status PASS;
- all three adaptive schemas = UL16R2;
- no `EpisodeSynopsisPlan.v0.3-r1` object in the adaptive forward contract;
- DEFER represented as portfolio disposition in the adaptive forward contract;
- every selected obligation has explicit `SELECTED_DUE` disposition and provenance;
- every sequence has obligation(s), owner(s), state-delta requirement and downstream consumer;
- every scene has necessity, pre-state, post-state and downstream consumer;
- architecture hash recomputation exact;
- Canonical Typed IR V2 validation PASS;
- fixed 2/3-scene lowering absent;
- broadcast scene depth >=46;
- adaptive compatibility mode identifies R2.

Observed architecture: 9 sequences / 54 scenes with per-sequence counts `10,5,5,5,5,8,8,4,4`.
Architecture hash: `2d8b6f101e5371aa43bd11fe91f8138c509a06c4fa3b36610de234c85efc2346`.
Canonical graph hash: `90acee582e5545f0cb63842ee9bbec65bfec6a8099aebe696883f2b38b614165`.

The value 9 here is the broadcast floor reached by this packet, not a fixed quota or upper bound; separate dynamic regression already produced 11 sequences / 97 scenes from a richer obligation portfolio.

## Dedicated dependency / disposition conformance — 30/30 PASS
- missing prerequisite -> dependent `BLOCKED_PRECONDITION`, absent from scenes;
- deferred prerequisite -> prerequisite `DEFERRED`, dependent `BLOCKED_PRECONDITION`, absent from scenes;
- explicitly satisfied prerequisite -> dependent `SELECTED_DUE`, present in scenes, architecture changes;
- payoff pressure 0.79 -> `DEFERRED` and absent from scenes;
- payoff pressure 0.81 -> `SELECTED_DUE` and present in scenes;
- dependency cycle -> cyclic dependents blocked and not falsely fulfilled;
- due loss = 0;
- false deferred fulfillment = 0;
- false blocked fulfillment = 0;
- architecture hash recomputable;
- scene/sequence contract completeness PASS.

## Existing integration regression — PASS
- Legacy default path PASS and hash-invariant;
- explicit adaptive route PASS;
- current-state-derived obligation compiler PASS;
- dynamic architecture >9 sequences PASS;
- future-source leakage returns controlled `HOLD / CANONICAL_IR_COMPILE_FAIL` rather than crashing;
- unknown mode fail-closed PASS;
- all 45 runtime Python modules compile.

## Stage A preregistration decision
Stage A deterministic schema/Main-Path adoption is **CLOSED PASS** for this exact R2 Treatment implementation.

This proves adoption/executability and fail-closed structural integrity only. It does **not** prove literary quality, human-level showrunning, external superiority, live Provider behavior or Production readiness.

## Next frozen boundary
Proceed to UL-16 Stage B A2 Causal Adoption only after freezing:
- eligible intervention case inventory;
- exact batch size;
- aggregation/pass threshold;
- base-state hash per case;
- intervention diff;
- expected affected obligation family;
- unrelated sentinel fields;
- expected direction of architectural change.

Stage B intervention families remain: Relationship, Information, Event/Precondition, Payoff/Deadline, plus Social-Group where explicit evidence exists.

## Authority boundary
Unchanged:
- Physical: SYNC-R53
- Production: ENG:R47
- Candidate Base: P07-I4H Recovery R3
- DB runtime authority: DB59 frozen
- DB64: research-support only
- Formal scored total: 137 / latest R138 / R140 0/0/0
- `UPPER_LAYER_GENERATIVE_QUALITY = NOT_QUALIFIED`

Status token:
`UL16_STAGE_A__R2_MAIN_PATH_ADOPTION_CLOSED_PASS__PUBLIC14_OF_14__DEPENDENCY_DISPOSITION30_OF_30__LEGACY_INVARIANT__FAIL_CLOSED__A2_STAGE_B_NEXT__NO_AUTHORITY_CHANGE`
