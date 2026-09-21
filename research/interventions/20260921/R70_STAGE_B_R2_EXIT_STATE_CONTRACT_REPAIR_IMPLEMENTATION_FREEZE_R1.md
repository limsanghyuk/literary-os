# R70 Stage B R2 — Exit-State Contract Repair Implementation Freeze R1

Date: 2026-09-21
Status: `SOURCE_FROZEN__FRESH_STAGE_B_CASES_NOT_CREATED__LIVE_OUTPUTS_0`

## Parent
R70 Stage B R1:
`VALIDITY_HOLD__NO_QUALITY_VERDICT`

R1 result commit:
`6e45acd4c93038447a29ce977248634d8fd22760`

R2 preregistration commit:
`5f954f42dbdac47fd7cbdef76ece6249dcdfae52`

## Frozen R2 runtime
Runtime ZIP SHA256:
`34476d35f365a27e7e8e773b05c2951c4febc72bde8104e29f68e1e6d754d31d`

Runtime bytes:
`18680596`

provider_backed_renderer.py SHA256:
`6db93f96c21d50f2aef1981935fc456f03351890d815c242bc608167a595bf58`

episode_live_closure.py:
byte-identical to R70 R1.

Canonical diff SHA256:
`748150ffc270cf2fdb7b09d14271a1da62eda83f3372ac671e3033766c1afe49`

Pre-freeze gates receipt SHA256:
`bb8425ead83529406f756eddf0b1fd01dac190cbf679d7f4e874e8ba9c68ad0b`

Source Freeze Receipt SHA256:
`9eeee531ab9195949044e1fb7676fd823a37cb7febd579e18d4e3097a177108c`

Source Freeze Evidence ZIP SHA256:
`3f03f551335cb03c54c09f9de89e5f17ad48ba28f2a62ada7fb91a5cc8f231e6`

## Exact change
Only:
`literary_os_runtime/provider_backed_renderer.py`

1. Per-scene output schema constrains `exit_state` to a single allowed enum value equal to `scene_blueprint.exit_state`.
2. Provider request consumes the payload's dynamic output schema.
3. Instructions define `exit_state` as a verbatim machine-contract field.
4. Anti-mechanical-copy instruction is restricted to action/dialogue/subtext prose.
5. Exact local exit-state guard remains unchanged.

## Pre-freeze gates
PASS:
- R1 48/48 mismatch diagnosis preserved;
- dynamic single-value exit-state enum;
- request uses dynamic schema;
- machine/prose instruction boundary;
- local guard AST-identical;
- R70 context compiler byte-identical;
- R66/F01 preserved;
- R67/F07 preserved;
- R68/F04 preserved;
- R69/F06 preserved;
- R70 Stage A 12/12 regression;
- runtime compile 45/45;
- code boundary: only provider_backed_renderer.py changed.

## Freeze rule
After this point:
- no R2 runtime tuning;
- no prompt tuning;
- no guard tuning;
- no context tuning.

Fresh R2 Stage B inputs must be created only after this freeze.

## Authority
No authority change:
- Physical Authority: SYNC-R67
- Active Qualified Candidate: R69/R68/R67/R66 lineage
- Production: ENG:R47 / LEGACY_R53
- R70 remains active research only.

Status token:
`R70_STAGE_B_R2_SOURCE_FROZEN__EXIT_STATE_MACHINE_CONTRACT_REPAIRED__FRESH_CASES_NOT_CREATED__OUTPUTS_0`
