# P07 I4J R1 Fresh Coverage Endpoint Validation — Control Scale-Floor HOLD Closure

Date: 2026-09-10

Experiment: `P07-I4J-R1-FRESH-COVERAGE-ENDPOINT-VALIDATION`

Preregistration commit: `364e92c38772e6c78b1585b40eb6dc769eaebec9`.
Parent physical authority at execution: `P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R2__I4I_R2_CLOSED_PRIMARY_FAIL`.
Parent material SHA256: `6e630bf4039953bd7b9969735c87fe7f273e760aa0811ee6c0322c2ea74b3b84`.

## PRECONTROL FREEZE

Fresh source-free series: `새벽 네 시의 공동주방`.
Episode: `아침까지 남겨둘 것`.

Frozen scale:
- 10 sequences;
- 50 scenes;
- planned Control 38,000 Unicode chars;
- preregistered minimum Control 35,000 Unicode chars.

All 50 scenes explicitly carried the 12 runtime-required Scene→Renderer anchors and the active `SemanticSceneToRendererBridge` accepted 50/50 before Control generation.

Freeze manifest SHA256: `34c06bd359b707f98168562d068d5fa06e66b9feab57617654ddb87ad989c92c`.

## SINGLE CONTROL ATTEMPT

The Control was generated once from the frozen plan and immediately validated before Selector.

Observed Control:
- sequences: 10;
- scenes: 50;
- Unicode chars: `17,928`;
- SHA256: `0a8fbbe0017b1ecb92ae616839441ee4c7050a05a097114162128e5887f5a7ea`.

The Control preserved the frozen structural scale but failed the preregistered `>=35,000` Unicode-character floor.

The output was NOT silently expanded, regenerated, or treated as valid after seeing the miss. The preregistered threshold was not changed.

## FINAL J1 CLASSIFICATION

`HOLD__CONTROL_UNDER_SCALE_FLOOR__NO_SELECTOR__NO_REVISION_POOL__NO_ARMS__NO_SCORES__NO_SCIENTIFIC_H1_H4_VERDICT`

Exact output state at closure:
- Fresh Plan: 1;
- Control attempt: 1;
- Valid Control: 0;
- Selector: 0;
- Revision Pool: 0;
- Coverage Arms: 0;
- Blind Scores: 0.

This is not an H1–H4 scientific FAIL because the experiment did not reach valid scoring. It is a pre-selector integrity/scale HOLD.

## CLAIM BOUNDARY

No change to:
- Active Development Engine `P07-I4H Recovery R3`;
- DB59 frozen authority;
- Production `ENG:R47`;
- Formal scored count `137`;
- latest formal `R138`;
- Formal R140 `0/0/0`;
- Semantic Alignment Virtual R1 remains Live-pending candidate;
- DB64 remains HOLD;
- I4I R1/R2 remain their original Primary FAIL verdicts.

## NEXT GOVERNANCE ACTION

Do not rewrite or extend this Control. Physically synchronize this HOLD evidence into the complete 5-Part / 9-transport research authority before starting any new causal experiment. A future retry must be separately preregistered and should eliminate the Control-scale under-realization risk prospectively rather than editing this output.