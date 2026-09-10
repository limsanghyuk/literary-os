# P07-I4K-2 External Search Ablation — Closure R1

Date: 2026-09-10
Experiment: `P07-I4K-R2-EXTERNAL-SEARCH-ABLATION`
Classification: DEVELOPMENT / PREFORMAL / MASKED SAME-AGENT
Final verdict: `FAIL__H2_EXTERNAL_ONLY_CAUSAL_FIT_DEGRADATION__NO_ADVANCE_TO_I4K3`

## Frozen baseline
Parent physical authority: `P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R4__I4K0_EXIT_PASS__I4K1_PASS_TO_I4K2`
Parent material SHA256: `90b0cbd6702be6eccea6f203f015ad7ce6e43bbd5dfa8fd5fb6bd0543cee76ab`
Fresh world: `해오름동 저녁돌봄식탁`
Arms: INTERNAL_ONLY 24 / EXTERNAL_ONLY 24 / COMBINED 24.
Preregistered evaluation: 72 masked candidates x 7 axes. Thresholds were not changed after output.

## Seals
Preregistration SHA256: `3c2bd18e9621a37b9ab1ed43bd10c244ed38c1887768586c634815d55bfaef71`
INTERNAL_ONLY SHA256: `3852bc9745819f6259ae936e55bb3bff6812bcdc16015868c5076217ff68a802`
EXTERNAL_ONLY SHA256: `df59bb4b0b38cfb39fa565ff93bdd974716737670cbb277346106c48edb1cb13`
COMBINED SHA256: `3222870823f1ca74a4100c93a1eaef398a97f7c4f2bd363fc018cf6d7437aacd`
Mask map SHA256: `41f7063f974f5e84ac72d18c41b3ecad8bde88cae1c4bb624f5d89420d972918`
Masked packet SHA256: `db013d5bd570a260430f7a759e5fead1b4c7777bd2de798a589fdaace68c5e3a`
Blind score SHA256: `58fef30ee7ee51241997b0bd20f1b63c7b611ca6b7b6800d133b6af3e66aa21c`
Unblinded result SHA256: `e303b57f363513f33440ea20b0aaf7811da1477fb61bc5818d74676f4463beb1`
Final closure ZIP R2 SHA256: `d7ecbd0a6a3336ded2d7f9f09ab94c11c07a14b6736efb221396c8a5ee0187fe`

## Arm means
- INTERNAL_ONLY all-7 mean: 7.422619
- EXTERNAL_ONLY all-7 mean: 7.723214
- COMBINED all-7 mean: 8.669643

## Hypotheses
H1 PASS: COMBINED minus best single all-7 mean = +0.946429 >= +0.25.

H2 FAIL: EXTERNAL_ONLY minus INTERNAL_ONLY mean across institutional/social plausibility + non-generic specificity = +0.520833 >= +0.40, but EXTERNAL_ONLY causal-fit delta = -0.750000, below the preregistered -0.40 floor.

H3 PASS: COMBINED minus best single ensemble+future mean = +0.947917 >= +0.20; coincidence-safety margin = +0.375 >= -0.10.

H4 PASS: hard-gate counts zero; all arms 24/24 hard-gate-valid; every COMBINED origin 6/6 had seven-axis mean >=6.5; EXTERNAL_ONLY causal-fit >=6.5 was 24/24.

## Interpretation
External Reality Mechanisms alone improved institutional/social plausibility and mechanism specificity, but when used as the initiating event source without mandatory attachment to current Character/Relationship causality they weakened causal fit to the frozen narrative state beyond the preregistered tolerance.

The COMBINED arm was strongest, but this experiment required H1-H4 all PASS. Therefore I4K-2 is FAIL and may not advance to I4K-3 from this result.

## Post experiment regression
Current nonhistorical regression: `258/258 PASS`.
Runtime code changed: false.
DB changed: false.
Active engine changed: false.
Formal count delta: 0.
Production change: false.
Actual OpenAI Live: false.

## Next boundary
Do not rewrite H2 or lower its causal-fit floor. Before any I4K-3 causal adoption study, perform a separate diagnosis/repair study of external-mechanism-to-current-state attachment/routing and then a fresh preregistered replication.