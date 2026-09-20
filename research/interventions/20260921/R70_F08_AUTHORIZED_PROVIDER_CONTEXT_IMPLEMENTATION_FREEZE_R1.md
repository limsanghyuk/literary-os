# R70 F08 Authorized Provider Context — Stage A Implementation Freeze R1

Date: 2026-09-21
Status: `STAGE_A_IMPLEMENTED_SOURCE_FROZEN__FRESH_CONTEXT_CASES_NOT_CREATED__STAGE_B_NOT_STARTED`

## Parent / Control (부모 / 대조군)
Physical Authority (물리 권위):
`SYNC-R67`

Control Runtime (대조 런타임):
`R69 qualified Candidate`

Control Runtime SHA256:
`3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`

## Preregistration (사전등록)
Canonical:
`research/interventions/20260921/R70_F08_AUTHORIZED_PROVIDER_CONTEXT_PREREG_R1.md`

Preregistration commit:
`1a9b9e94a8240093228a232e126d98b1930ce177`

## Frozen Treatment (동결 처치군)
Treatment Runtime ZIP SHA256:
`1e4ca6fd7e60ce9e70507dbb7deb90a2438be6ca62a709222d00ff3b8db13182`

Treatment `episode_live_closure.py` SHA256:
`5f42da69bf1809ad3c01e66d6639473c1d1be522683437adcc4fbeb0153503d3`

Treatment `provider_backed_renderer.py` SHA256:
`d5723ce674cebf30f7415522927fbeb8e0ded11bedad6279b092c2eb2c6e67c6`

Context-only canonical diff SHA256:
`9c0218bbf6054749f3fb74bc36601d4c500b7f1e677fae4514dcd0f4d6637fdf`

Source Freeze Evidence R2 ZIP SHA256:
`30055d3cbbae92ee9db47ffa981c3c9b00603e0edafeda19319b6d89ebb66c86`

## Implementation (구현)
Added Authorized Context Projection (허가 문맥 투영):
- scene-cast extraction;
- current canonical character-state projection;
- current voice/speech constraint projection when explicitly present;
- cast-relevant relationship-state filtering;
- cast/ref-relevant information-state filtering;
- cast/group-relevant social-ecology filtering;
- explicit planner-only exclusion count without exposing planner contents;
- per-scene authorized ensemble context.

Added Context Boundary Guard (문맥 경계 가드):
- blocks planner-only rows marked `factual_access_forbidden=true`;
- blocks explicit planner/future context keys;
- requires canonical authority labels for new Authorized Context schemas.

Renderer Instructions (렌더러 지침) now explicitly require:
- CANONICAL_FACT (정본 사실) may be treated as fact;
- SCENE_CONTRACT_CONSTRAINT (장면 계약 제약)은 extra world fact가 아님;
- use authorized voice/relationship/information/social context for differentiation;
- never promote planner-only, omitted or future information into fact.

Legacy Control Helpers (기존 대조군 헬퍼):
restored unchanged.

## Pre-freeze Stage A Gates (사전 동결 단계 A 게이트)
A1 Character-specific current state projection: PASS  
A2 Cast-relevant relationship projection: PASS  
A3 Relevant information projection: PASS  
A4 Relevant social-ecology projection: PASS  
A5 Planner-only exclusion: PASS  
A6 Unrelated-state exclusion: PASS  
A7 Scene Blueprint/Contract unchanged: PASS  
A8 Provider request consumes enriched context + explicit boundary instructions: PASS  

Context gate receipt SHA256:
`63045f4ba844eac175a64ddfea7e22db5982d388b0ee9a5876ba5f91cdbfffc6`

R66 F01 regression:
`12/12 PASS`
Corrected receipt SHA256:
`0500aa01438d644f2d3d5bedc6161338335c480e70f3a5aee4c5f4cce4d45ff7`

R67 F07 regression:
PASS by exact qualified F07/adaptive source identity; state-carry source remains:
`ce38885171d0f318aeb2142ec16d119814be7fb736ebc361166007b4d2eea087`

R68 F04 regression:
`16/16 PASS`

R69 F06 regression:
`16/16 PASS`

Consolidated regression receipt SHA256:
`63f9288a209123a74854e9c15ed40122e326692fd244260baee536cdccbe7a36`

Runtime Compile (런타임 컴파일):
`45/45 PASS`
Receipt SHA256:
`9a2ada3af31606aad32a50844ef25fdae49ed790ae172de0418e4ca72ee42364`

Code Boundary Audit R2 (코드 경계 감사 R2):
PASS. Legacy Control helpers are AST-identical to R69 Control.
Receipt SHA256:
`d4240135742dd579cae717975ef6dbdfc5191c24b30bfe8f1a4bb547e2299777`

## Freeze Rule (동결 규칙)
This Treatment runtime is immutable for R70 Stage A primary qualification and all Stage B paired payload construction.

Fresh Stage A cases may be created only after this freeze.

No context field, filtering rule, boundary rule or renderer instruction may be tuned after fresh-case creation.

Stage B Provider Execution requires a separate pre-output execution seal specifying exact provider/model/settings and paired payload hashes.

Status token:
`R70_STAGE_A_SOURCE_FROZEN__F08_AUTHORIZED_PROVIDER_CONTEXT__R66_R69_REGRESSION_PASS__FRESH_CONTEXT_CASES_NOT_CREATED__STAGE_B_NOT_STARTED`


## Custody correction note (보관 정정 기록)
The frozen Treatment runtime/source bytes did not change. This document was updated only to point to the final post-repair canonical diff and Source Freeze Evidence R2 after re-verifying that the legacy Control helpers are AST-identical to R69.
