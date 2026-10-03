# UL20 — F04 Trusted Causal-Root Partition Repair Preregistration R1

Date: 2026-10-03  
Status: `PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0`

## Trigger / 발동 원인
UL19-R2 closed at a frozen Pre-Blind Mechanical HOLD(맹검 전 기계적 보류). The current SYNC-R76 Treatment reached broadcast depth on multiple variants and preserved due/deferred/open-touch legality, but R68 F04 raised `SEMANTIC_TRANSACTION_REPEAT_GE3` on scenes with distinct owners, actions, consequences, and in several groups distinct causal roots.

R69 F06 simultaneously classified the affected scenes as necessary separate scenes rather than redundant/mergeable.

Responsible boundary:
`R68_F04_SEMANTIC_TRANSACTION_SIGNATURE__CAUSAL_ROOT_BLINDNESS`

## Parent Authority / 부모 권위
Physical Authority: **SYNC-R76**  
Active Runtime: **UL18_F2_SUCCESSOR_RUNTIME_R1**  
Runtime SHA256: `56254a8f52b19651638ab21ece2c35618e621e3aedc02d917efb6e22ca11db88`  
Adaptive source SHA256: `f2a22d1156f50152b8de1ae745d16e3189f6731758a83b8cc7dc2b37e8e8553b`  
Qualified Parent: exact R69  
Production: **ENG:R47 / LEGACY_R53**  
Runtime DB: **DB59 frozen**

## Research Question / 연구 질문
Can F04 preserve its historical material-agnostic clone detection while avoiding false repetition when the same coarse semantic transaction role is independently required by multiple **trusted, frozen causal roots**?

## Intervention Boundary / 개입 경계
Only the F04 semantic-repetition grouping logic may change.

Allowed:
- add a helper that derives an optional trusted causal-root partition key from frozen obligation source evidence;
- partition an existing coarse F04 semantic signature by trusted root evidence only when that evidence validates;
- add diagnostics/receipts/tests.

Forbidden:
- changing scene generation;
- changing obligation selection, sequencing, weaving, stage choice, visible action, or resolution behavior;
- changing F01, F06, F07, UL18 open-touch semantics;
- lowering repetition threshold below/above 3;
- using obligation id, character id, literal statement, literal action, or arbitrary root label as a uniqueness escape;
- DB/Provider/Production mutation.

## Trusted Causal-Root Evidence Contract / 신뢰 인과근원 증거 계약
A source obligation may optionally carry:

`causal_root_evidence = {
  source_record_id: <stable pre-output current-state record id>,
  source_record_type: <event/state/relationship/institutional/deadline/history/etc>,
  established_before_target_episode: true,
  evidence_hash: SHA256(canonical evidence payload)
}`

and:

`causal_root_evidence_payload = <canonical JSON object describing the frozen source record>`

Validation requirements:
1. both evidence object and payload exist;
2. `established_before_target_episode == true`;
3. non-empty stable `source_record_id` and `source_record_type`;
4. runtime recomputes SHA256 over the canonical payload and it equals `evidence_hash`;
5. partition identity is based on validated source-record identity/evidence, **not** the free-text `causal_root` label.

If any requirement fails:
`NO_TRUSTED_ROOT_PARTITION -> HISTORICAL_R68_GROUPING`.

## Proposed Rule / 제안 규칙
F04 keeps the existing material-agnostic semantic signature.

For non-RESOLVE scenes:
- without trusted root evidence: count repetitions exactly as historical R68;
- with trusted root evidence: count the coarse semantic signature **within the validated root partition**.

A violation remains:
`same coarse semantic transaction signature >= 3 inside one trusted root partition`
or
`>= 3 in the historical unpartitioned bucket`.

This means multiple independently established roots may use the same dramatic transaction role without automatically becoming clones.

## Anti-Gaming / 우회 방지
The following must still flag:
- three repeated transactions with no root evidence;
- three repeated transactions where only free-text `causal_root` labels differ;
- three repeated transactions with the same validated source-record identity but different root labels;
- three repeated transactions with invalid/mismatched evidence hashes.

The following may separate:
- three same-role transactions with three different valid pre-output source-record identities and matching evidence hashes.

Root partition never overrides F06:
- redundant/mergeable scenes remain rejectable by Counterfactual Scene Necessity(반사실 장면 필요성);
- trusted roots are not proof that a scene is necessary.

## Historical Regression Gates / 역사 회귀 관문
Before any qualification:
- R68 frozen fresh suite: **16/16**, FP0/FN0;
- R66 F01: preserved;
- R67 F07: preserved;
- R69 F06: preserved;
- UL18 open-touch four-state matrix and B06 repair: preserved;
- Python compile: 45/45 PASS;
- unrelated Python source drift: 0.

## Deterministic Pre-Freeze Cases / 사전 동결 결정론 사례
Before source freeze, test at least:
1. SAME_ROOT_REPEAT_3 -> FLAG
2. FREE_TEXT_FAKE_ROOT_LABELS_3_NO_EVIDENCE -> FLAG
3. SAME_VALIDATED_SOURCE_ID_DIFFERENT_LABELS -> FLAG
4. INVALID_EVIDENCE_HASHES -> FLAG
5. THREE_VALID_INDEPENDENT_ROOTS -> NO FLAG
6. TWO_SAME_ROOT_PLUS_ONE_INDEPENDENT -> NO >=3 ROOT-PARTITION FLAG
7. THREE_VALID_ROOTS_BUT_REDUNDANT_SCENES -> F04 may not flag, but F06 must still identify redundancy/mergeability
8. METADATA_SENTINEL -> unrelated architecture output unchanged

## Source Freeze / 소스 동결
Only after deterministic and historical regression gates pass:
- hash source;
- seal diff;
- no tuning after fresh primary case creation.

## Fresh Primary Qualification / 신규 주요 자격시험
After source freeze create a fresh 16-case suite:
- 8 expected repetition violations;
- 8 expected non-violations;
- include valid/invalid root-evidence cases, mixed partitions, blocked/open/deferred profiles, and F06 interaction.
Inputs are sealed before Treatment execution.

PASS requires:
- 16/16 classification;
- FP=0, FN=0;
- historical R68 16/16 unchanged;
- R66/R67/R69/UL18 regressions PASS;
- no generation-output drift outside validation diagnostics.

## Authority Boundary / 권위 경계
UL20 is research-only. A PASS does not modify SYNC-R76.
If UL20 becomes a qualified successor, it requires a new runtime identity and a separately audited successor physicalization before UL19 architecture blind can resume.

DB64-R134 remains untouched.

Status token:
`UL20_PREREGISTERED__F04_TRUSTED_CAUSAL_ROOT_PARTITION_ONLY__PARENT_SYNC_R76__NO_OUTPUTS`
