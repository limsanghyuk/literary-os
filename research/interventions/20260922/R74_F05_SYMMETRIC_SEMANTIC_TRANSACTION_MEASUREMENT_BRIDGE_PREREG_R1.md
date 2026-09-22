# R74 — F05 Symmetric Semantic-Transaction Measurement Bridge — Preregistration R1

Date: 2026-09-22

Status:
`PREREGISTERED__OUTPUTS_0__BRIDGE_NOT_EXECUTED__PRIMARY_NOT_STARTED__INPUT_CUSTODY_GATE_REQUIRED`

## Authority
- Physical Authority: **SYNC-R72**
- Active Qualified Candidate: **R69/R68/R67/R66 lineage**
- Active Runtime: exact R69 — SHA256 `3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 R127 research-only**
- R72 Research: **CLOSED FAIL**
- R73: **CLOSED_DIAGNOSTIC_PASS__STAGE_B_EFFICACY_INVALIDATED_METRIC_NONCOMPARABILITY__F05_NOT_QUALIFIED**

## Purpose
Repair the measurement asymmetry discovered in R73 by forcing Control and Treatment through one shared semantic representation and the exact same frozen F04/F06 validators before any F05 efficacy claim.

## Research questions
1. Can one arm-independent bridge convert exact-R69 Control scenes and unchanged-F05 Treatment scenes into semantically comparable scene/transaction records?
2. When the exact same R68 F04 and R69 F06 rules are applied to both arms, do arm labels, serialization order, or story material change the result?
3. On fully fresh paired cases, does unchanged F05 reduce symmetric F04 repetition and/or F06 redundant/mergeable scenes without losing required narrative work?

## Control / Treatment
Control:
- exact current R69 architecture behavior; immutable.

Treatment:
- exact unchanged R72 F05 Adaptive Pressure Allocator R2;
- allocator SHA256 `9aa36906be260b3ae734340e0d9be951692a18088bc1a40ae5c829e166088c0f`;
- no tuning in R74.

Only the measurement bridge may be added. No F01/F02/F04/F06/F07/F08, retrieval, DB, renderer, or Production mutation is allowed.

## Frozen shared measurement authority
### F04
Use the exact R68 frozen rule:
- build material-agnostic Semantic Transaction Signature from transaction_stage, transaction_kind_role, causal_role_profile, state_delta_role_profile, resolution_role;
- exclude names, IDs, literal props/locations/actions/statements from the signature;
- exclude RESOLVE scenes;
- violation only when the same normalized non-RESOLVE signature occurs >=3 times in one episode graph;
- issue token: `SEMANTIC_TRANSACTION_REPEAT_GE3`.

### F06
Use the exact R69 frozen rule:
`NECESSARY_SEPARATE_SCENE`
iff removal causes protected narrative loss AND no lossless adjacent merge exists.

`REDUNDANT_OR_MERGEABLE_SCENE`
iff removal causes no protected loss OR a lossless adjacent merge exists.

Protected contributions are limited to:
- unique obligation resolution;
- unique deferred/open pressure;
- supported factual information/relationship/social delta;
- unique obligation-specific semantic advance;
- dependency-aware causal bridge.

## Symmetric bridge contract
For BOTH arms, the bridge must:
1. discard arm-specific validator result fields before scoring;
2. consume only scene allocation, source obligation/atom bindings, sequence membership, transaction/state roles and protected contribution evidence;
3. reconstruct the same canonical scene record schema;
4. call the same F04 signature/repetition logic;
5. call the same F06 protected-contribution/removal/adjacent-merge logic;
6. expose unresolved fields explicitly; unresolved required semantics invalidate the case rather than defaulting to zero violations;
7. never inspect the arm label while constructing or scoring records.

No missing Treatment semantic field may be treated as “no repetition” or “necessary scene”.

## Stage M — measurement bridge qualification
Must PASS before any R74 primary Treatment effect is scored.

M1 Identity parity:
The same scene graph supplied as Arm A and Arm B yields bit-identical canonical records and F04/F06 outputs.

M2 Arm-swap invariance:
Swapping Control/Treatment labels without changing content does not change per-content metrics.

M3 Serialization invariance:
Reordering object keys / input serialization does not change results.

M4 R68 F04 regression:
The frozen R68 16-case validator set remains 16/16 correct.

M5 R69 F06 regression:
The frozen R69 16-case validator set remains 16/16 correct.

M6 Missing-semantic fail-closed:
If required bridge fields cannot be reconstructed, status is INVALID/UNRESOLVED; the bridge must never impute a zero violation count.

M7 Code boundary:
Bridge is measurement-only; generation/allocation outputs are byte-unchanged.

Any M1-M7 failure => `R74_MEASUREMENT_HOLD`; no efficacy scoring.

## Input custody gate
DB64 raw authority expected:
- logical DB64 SHA256 `4703e9a99da2deb66eef08f09b08141db6c4d19bc76f77d1c8159dcb7633d6e7`.
- source: independently verified `consumer_ready_r53`.

Before any primary output:
- raw input bytes/path references must be recoverable for every selected case;
- every referenced planner/thick/arc/thread-state artifact must exist;
- ledger must be sealed before Treatment execution;
- no replacement after Treatment output.

If custody cannot be verified => `INPUT_CUSTODY_HOLD__NO_PRIMARY_OUTPUT`.

## Freshness rule
Primary efficacy cases must be fully fresh:
- exclude all R71 primary works;
- exclude all R72 R2/R3/R4/R5 primary cases;
- exclude all 41 R73 Stage-A HIGH cases;
- exclude all 24 R73 Stage-B Treatment cases;
- exclude SOURCE HOLD works.

The 17 R73 Control-only/Treatment-naive cases are reserved for bridge recovery/metrology only and may NOT support the fully-fresh efficacy claim.

Reserved 17:
싸인__EP18, 싸인__EP20, 싸인__EP19, 연애시대__EP05, 오나의귀신님__EP01, 싸인__EP02, 드림__EP01, 연애시대__EP07, 오나의귀신님__EP16, 그저바라보다가__EP01, 싸인__EP13, 연애시대__EP08, 연애시대__EP01, 그대웃어요__EP01, 대물__EP01, 내이름은김삼순__EP10, 구르미그린달빛__EP02.

## Primary design
Only after Stage M PASS and custody PASS:
- select exactly 24 fully fresh eligible episodes;
- minimum 12 distinct works;
- maximum 2 episodes/work;
- deterministic SHA-based selection from the eligible pool;
- seal full input ledger before Treatment output.

## Primary symmetric gates
P1 valid paired execution: 24/24.
P2 canonical bridge completeness: 24/24 both arms, unresolved required fields 0.
P3 F04 improvement: Treatment F04 repetition-group count < Control in >=16/24.
P4 F04 non-worsening: Treatment <= Control in >=22/24.
P5 F06 improvement: Treatment redundant/mergeable count < Control in >=12/24 OR, if fewer than 12 Controls have F06 headroom, diagnose ceiling and do not score P5 as efficacy.
P6 F06 non-worsening: Treatment <= Control in 24/24.
P7 due-now required contribution coverage: 100%.
P8 required visible-causal contribution coverage: 100%.
P9 premature deferred closure: 0.
P10 F01/F02/F07 regressions: 0.
P11 confirmed critical violations: 0.

If a headroom prerequisite for a directional gate is absent, do not convert that absence into a Treatment win; report a ceiling diagnostic.

## Blind evaluation
Not part of R74 primary claim. R74 tests deterministic measurement/allocation effects at scene-graph level, not screenplay style.

## Claim boundary
A PASS can establish only:
`F05_SYMMETRIC_SCENE_GRAPH_MEASUREMENT_SIGNAL`.

It does NOT establish:
- screenplay surface quality;
- Provider realization quality;
- Production promotion;
- operational Level-3 restoration;
- DB64 adoption;
- R70 closure;
- Formal R140 start.

## Current execution boundary
At seal time:
- bridge outputs = 0;
- primary Control outputs = 0;
- primary Treatment outputs = 0;
- judgments = 0.

The current local container/Python runtime is infrastructure-HOLD due repeated TransportTimeoutError even on minimal commands. This infrastructure condition is excluded from scientific outcome classification.
