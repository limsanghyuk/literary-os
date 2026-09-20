# R70 Stage B Live Provider Paired Surface Effect — Execution Protocol R1

Date: 2026-09-21
Status: `SEALED_INPUTS_AND_PAYLOADS__PROVIDER_EXECUTION_SEAL_PENDING__OUTPUTS_0`

## Purpose (목적)
Stage B measures whether Frozen R70 Authorized Provider Context (동결 R70 허가 제공자 문맥) improves actual Provider-rendered Screenplay Surface (제공자 실현 대본 표면) against exact R69 Default Context (정확한 R69 기본 문맥).

## Frozen research boundary (동결 연구 경계)
- Physical Authority (물리 권위): SYNC-R67
- Control Runtime (대조 런타임): exact R69 qualified runtime
- Treatment Runtime (처치 런타임): R70 frozen runtime
- Frozen Treatment Runtime SHA256: `1e4ca6fd7e60ce9e70507dbb7deb90a2438be6ca62a709222d00ff3b8db13182`
- Stage A Result: 12/12 PASS, leakage 0

## Stage B frozen inputs (단계 B 동결 입력)
- Scene input JSON SHA256: `3bf7b1a20317b20f02e45ae70fe59863c8362d9d582bbf84de0d91e643b6017e`
- Paired payload JSON SHA256: `8ad241820986dc383961da47df36d7f19ef31f80a7ab403febdceabb7bc6a169`
- Shared renderer instructions SHA256: `74b37a0cc1daf3add78f9f5329c5ff67b974dfa87206c8df0a3e9cc4fc8637ab`
- Hidden A/B mapping SHA256: `058cff81f62666d32b58cec9d5cf2181552592074e2f48f6bc84f2ec9949849d`
- Mapping balance: Treatment=A 6 / Treatment=B 6

Only Provider Context differs between paired arms.

## Provider Execution Seal (제공자 실행 봉인)
No provider call may occur until `R70_STAGE_B_PROVIDER_EXECUTION_SEAL_R1.json` is finalized with exact model/settings and `status=SEALED_BEFORE_OUTPUTS`.

## Credential policy (자격증명 정책)
`OPENAI_API_KEY` must be injected only through Environment Variable (환경변수) or Secret Manager (비밀 저장소). The raw key is never stored in experiment artifacts.

## Live validity (실시간 유효성)
Each arm is valid only if provider status is OK, live provenance and response ID exist, model identity matches the sealed model, schema/local guard PASS, and no fallback/template renderer is used.

Retry policy:
- maximum 2 attempts per arm;
- only provider/local-contract invalidity may trigger retry;
- no quality-motivated rerun;
- pair invalid if either arm remains invalid.

## Blind evaluation (블라인드 평가)
After valid outputs are sealed, three independent fresh-context judges evaluate 12 hidden A/B pairs on:
- CHARACTER_VOICE_DIFFERENTIATION (인물 목소리 구분)
- RELATIONSHIP_STATUS_PRESSURE (관계 상태 압력)
- ENSEMBLE_WORLD_SPECIFICITY (앙상블/세계 구체성)
- SUBTEXT_PHYSICALIZATION (서브텍스트/행동화)
- CAUSAL_SEMANTIC_FIDELITY (인과·의미 충실도)
- UNSUPPORTED_NOVELTY_RISK (근거 없는 새 사실 위험; 안전할수록 높은 점수)

Frozen final gate:
- Treatment wins >= 7/12
- wins + ties >= 10/12
- losses <= 2/12
- zero confirmed critical violations under 2-of-3 judge rule

## Current status (현재 상태)
No provider output exists yet.
No Candidate promotion is permitted.
Physical Authority remains SYNC-R67.
Production remains ENG:R47 / LEGACY_R53.
