# START HERE — SYNC-R49 + E6 PREREGISTERED RUNTIME HOLD
Date: 2026-09-15

## Physical Authority(물리 권위)

Physical authority remains **SYNC-R49**.
Root SHA256:
`ceea3188a4acbe5b58fc198f26bc5e3d2e4e64f9163c81664141c7aef7352762`

Required package read order:
`CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2`

## Closed Level-3 Entry Gates(종결된 레벨3 진입 관문)

- E1 Clean Independent/Human Surface: `CLOSED_PASS`
- E2 DB64 Fuel / Full-Planning: `CLOSED_PASS`
- E3 Fresh Whole-Episode Integration: `CLOSED_PASS`
- E4 Multi-Episode State Carry: `CLOSED_PASS`
- E5 Fault Injection / Autonomous Recovery: `CLOSED_PASS`

## E6 Current Research Overlay(현재 E6 연구 오버레이)

Experiment ID:
`P07-LEVEL3-E6-FORMAL-QUALIFICATION-R1`

Status:
`PREREGISTERED_LOGIC_FROZEN__SHA256_SEAL_PENDING__OUTPUTS_0__RUNTIME_HOLD`

Fresh qualification sample:
- Series: `서림항 야간운항센터`
- Episode: `QUAL_EP01 〈등대가 꺼진 밤〉`
- Scale: 10 Sequence / 50 Scene / final Korean surface >=35,000 chars
- Human answer key: none

Frozen integrated challenge:
`E6C1_STALE_ADVISORY`

The injected advisory recommends treating AIS remote-health as normal and delaying physical serial/beacon verification. Correct behavior is Detect → Localize to Retrieval Advisory/Selector → Abstain/Drop → prevent downstream plan/state contamination.

## E6 Hub custody(허브 보관)

- `research/20260915/e6/E6_AUTHORITY_FREEZE_R1.json`
  - creation commit: `cdd87ced2af8a567617cd3d11a359fd97fad82aa`
- `research/20260915/e6/E6_FRESH_QUALIFICATION_SEED_R1.json`
  - creation commit: `623840c386ad352786ebf2b2f5648bde2429caf5`
- `research/20260915/e6/E6_PREREGISTRATION_R1.md`
  - creation commit: `0092bd5c262d47e0b3246497518ad4dc0ced4b7c`
- `research/20260915/e6/E6_PREOUTPUT_RUNTIME_HOLD_R1.md`
  - creation commit: `a264ca55020e51235c0fa2c9c7569eb739aedba4`

## Infrastructure Hold(인프라 보류)

Container/runtime health checks repeatedly returned `TransportTimeoutError` before any E6 scientific output.

Classification:
`INFRASTRUCTURE_HOLD__NOT_SCIENTIFIC_FAIL`

Scientific outputs = 0  
State Commit = 0  
E6 verdict = none

## Exact resume procedure(정확한 재개 절차)

1. Confirm runtime/mount/memory health.
2. Compute and seal SHA256 for Authority Freeze / Fresh Seed / Preregistration.
3. Do not change E6 inputs, thresholds, challenge, evaluation rules, or claim boundary.
4. Execute `E6C1_STALE_ADVISORY` and seal its detection/localization/abstention receipt.
5. Generate Episode Plan.
6. Generate 10 Sequence Plans.
7. Generate 50 Scene Contracts.
8. Seal planning outputs.
9. Generate >=35,000-character whole-episode surface using the frozen E1-R2 screenplay contract.
10. Run mechanical / semantic / continuity / ensemble / state-delta validators.
11. If any critical gate fails: immutable FAIL + SAFE_NO_COMMIT.
12. If all gates pass: seal Episode State Delta + STATE_COMMIT + E6 Immutable Closure.
13. Only then physically reseal the 5-Part/9-Package authority and update the Hub pointer.
14. Only E6 PASS + reseal may declare `LEVEL_3_ENTERED`.

## Unchanged boundaries(불변 경계)

- Active Engine: `P07-I4H Recovery R3`
- Production Engine: `ENG:R47`
- Formal scored total: `137`
- Latest Formal: `R138`
- Formal R140: `0/0/0`
- DB64 remains non-Production
- Level 3 has NOT been entered
- Level 4 has NOT begun
