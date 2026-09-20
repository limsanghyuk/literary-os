# R70 — F08 Authorized Provider Context Projection and Surface Effect Preregistration R1

Date: 2026-09-21
Status: `PREREGISTERED__IMPLEMENTATION_NOT_STARTED__OUTPUTS_0`

## Sequential identity (연속 연구 식별)
- R66 CLOSED PASS — F01 Boundary-Safe Predicate Parser (경계 안전 술어 파서)
- R67 CLOSED PASS — F07 Dual-Ledger State Carry Runtime (이중 원장 상태 이월 런타임)
- R68 CLOSED PASS — F04 Semantic Transaction Repetition Validator (의미 거래 반복 검증기)
- R69 CLOSED PASS — F06 Counterfactual Scene Necessity Validator (반사실 장면 필요성 검증기)
- R70 CURRENT / PREREGISTERED

## Parent authority (부모 권위)
Physical Authority (물리 권위):
`SYNC-R67`

Active Qualified Candidate (활성 자격 후보):
`R69 F06 / R68 F04 / R67 F07 / R66 F01 lineage`

Current runtime SHA256:
`3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`

Adaptive Showrunner source SHA256:
`740cca05a94dbb59eb9a1600e1c7d98cdc887693aa5ab46fec2bd2eaef78d306`

Production Engine (운영 엔진):
`ENG:R47 / LEGACY_R53`

Runtime DB (런타임 DB):
`DB59 frozen`

Research DB (연구 DB):
`DB64 research-only`

## Causal target (인과 대상)
Only F08:
`Provider Context Insufficiency (제공자 문맥 부족)`

R61 status:
`CONTRIBUTOR`

Observed runtime gap:
ProviderBackedRenderer (제공자 기반 렌더러) already accepts:
- character_context (인물 문맥)
- ensemble_context (앙상블 문맥)
- texture_contract (표면 질감 계약)

but FullEpisodeProviderClosure (전체 회차 제공자 폐쇄)의 default character context currently supplies mainly:
- allowed speakers;
- the same generic voice instruction for each character;
- CURRENT_AUTHORIZED_STATE_ONLY marker.

Default ensemble context supplies mainly:
- ensemble group list;
- generic scene-pressure and no-new-fact rules.

Meanwhile Canonical State / Canonical IR (정본 상태 / 정본 IR) already contains:
- character state (인물 상태);
- relationship state (관계 상태);
- information state (정보 상태);
- social ecology (사회 생태);
and R67 separates planner-only unrealized obligations from factual canonical state.

## Research question (연구 질문)
Can the Candidate project richer but strictly authorized current-state context to the prose Provider without leaking planner-only/future information, and does that richer context improve realized scene craft while preserving semantic/state fidelity?

## Hypothesis (가설)
If Provider Context (제공자 문맥) includes only scene-relevant Canonical Current State (정본 현재 상태):
- character-specific state and voice constraints;
- cast-relevant relationship state;
- cast/scene-relevant information state;
- relevant social group/membership state;
- explicit authority/provenance and planner-only exclusion;

then Provider-rendered scenes will improve:
- Character Voice Differentiation (인물 목소리 구분);
- Relationship Status Pressure (관계 상태 압력);
- Ensemble/World Specificity (앙상블/세계 구체성);
- Subtext and Physicalization (서브텍스트와 행동화);

without increasing:
- Unsupported Novelty (근거 없는 새 사실);
- Future-source leakage (미래 원자료 누출);
- Canonical-state contradiction (정본 상태 모순).

## Control (대조군)
Exact current R69 qualified runtime and its current default provider-context behavior.

No Control mutation.

## Treatment scope (처치 범위)
Permitted files:
- `literary_os_runtime/episode_live_closure.py`
- `literary_os_runtime/provider_backed_renderer.py`
- directly required tests/diagnostics only.

Permitted changes:
- compile authorized character context (허가된 인물 문맥);
- compile authorized ensemble/social context (허가된 앙상블/사회 문맥);
- context boundary validation (문맥 경계 검증);
- renderer instructions that explicitly distinguish canonical facts from non-facts;
- context provenance/receipt fields.

Prohibited:
- F01 transaction selection changes;
- F04 semantic repetition rule changes;
- F06 scene necessity rule changes;
- F07 State Carry semantics changes;
- Scene Blueprint/Scene Contract content changes;
- sequence allocation;
- obligation compiler;
- DB mutation;
- Production path mutation.

## Authorized Provider Context Contract (허가된 제공자 문맥 계약)

### C1 — Character Current State (인물 현재 상태)
For each cast member, Treatment may project only current canonical state already present in `prior_state.characters`.

If a character-state row contains explicit current voice/speech fields, Treatment may project only those existing fields:
- voice;
- voice_signature;
- speech_style;
- register;
- dialect;
- verbal_habits.

Treatment must not invent biography, speech history or personality facts.

### C2 — Relationship Current State (관계 현재 상태)
Project only `prior_state.relationships` entries that are demonstrably relevant to the current cast/pair.

No future relationship trajectory or planner-only relationship delta may enter as factual context.

### C3 — Information Current State (정보 현재 상태)
Project only current `prior_state.information_state` rows relevant to current cast, explicit scene references or authorized owners.

Unrelated information rows may be omitted.

### C4 — Social Ecology (사회 생태)
Project current group/membership/institution state from:
- `prior_state.social_ecology`;
- current authorized `ecology`;
limited to groups/memberships that intersect current cast or explicit scene group refs.

### C5 — Planner-only exclusion (기획 전용 제외)
`planner_unrealized_obligations` must never be copied into Provider factual context.

Treatment context must carry:
`planner_only_facts_forbidden = true`

and a deterministic excluded-planner count/receipt may be recorded without exposing the planner-only contents.

### C6 — Future-source exclusion (미래 원자료 제외)
No future source, uncommitted future event or trajectory may be presented as current fact.

### C7 — Context authority labels (문맥 권위 라벨)
Treatment payload must distinguish:
- `CANONICAL_FACT`
- `SCENE_CONTRACT_CONSTRAINT`
- `RENDERING_RULE`

No planning intention may be labeled CANONICAL_FACT.

### C8 — Provider instruction consumption (제공자 지침 소비)
Renderer instructions must explicitly require:
- use authorized current state to differentiate voice, status, intimacy, pressure and ensemble behavior;
- never promote omitted/planner-only context into fact;
- do not add biography/history/world facts not authorized by payload.

## Stage A — Deterministic Context Projection Qualification (단계 A — 결정론적 문맥 투영 자격시험)

### Pre-freeze gates
A1. character-specific canonical state projected when present.
A2. cast-relevant relationship state projected.
A3. relevant information state projected.
A4. relevant social ecology projected.
A5. planner-only ledger contents excluded.
A6. unrelated relationship/information/social rows excluded.
A7. Scene Blueprint/Contract hashes unchanged.
A8. Provider request includes enriched Treatment context and explicit boundary instructions.
A9. R66 F01 regression PASS.
A10. R67 F07 regression PASS.
A11. R68 F04 regression PASS.
A12. R69 F06 regression PASS.
A13. whole runtime compile PASS.
A14. Code Boundary Audit confirms F08-only change.

After A1-A14 PASS:
- freeze Treatment runtime/source;
- no context-field tuning after freeze.

### Fresh Stage A set
After source freeze only:
create exactly 12 new synthetic context-projection cases covering:
- distinct character voice signatures;
- relationship intimacy/status asymmetry;
- information asymmetry;
- social group membership;
- institutional role;
- unrelated-state exclusion;
- planner-only exclusion;
- missing optional voice fields;
- multi-cast ensemble;
- conflicting unrelated relationship row;
- mixed information/social case;
- empty-state fallback.

Stage A PASS requires 12/12 contract compliance and zero planner/future leakage.

## Stage B — Live Provider Paired Surface Effect (단계 B — 실시간 제공자 쌍대 표면 효과)

Stage B is required to close F08.

### Provider execution seal
Before any Stage B generation:
seal:
- exact Provider/model identifier;
- API family;
- reasoning configuration;
- max output tokens;
- temperature/sampling settings if applicable;
- exact 12 fresh scene inputs;
- exact Control/Treatment render payload hashes;
- A/B randomization/mapping;
- retry policy.

The same provider/model/settings must be used for both arms of each pair.

No API key is stored in experiment artifacts.

### Stage B inputs
Use 12 fresh scenes selected only after Treatment source freeze.
For each scene:
- same Scene Blueprint;
- same Scene Contract;
- same Texture Contract;
- same output schema;
- same Provider/model/settings.

Only Provider Context differs:
- Control = exact R69 default context behavior;
- Treatment = frozen R70 authorized enriched context.

### Live call validity
A pair is valid only if both arms:
- return real provider provenance;
- include response ID/request ID when supplied by provider;
- pass schema guard;
- pass local semantic contract guard;
- do not use fallback/template rendering.

Provider failure does not become a quality loss; invalid pairs must be reported as invalid according to the frozen retry policy.

### Blind evaluation
After valid paired outputs are sealed:
- hidden A/B mapping;
- 3 independent fresh-context judges;
- judges see only scene input needed for evaluation and A/B surfaces;
- judges do not see R70 lineage, context payloads or mapping.

Axes:
- CHARACTER_VOICE_DIFFERENTIATION (인물 목소리 구분)
- RELATIONSHIP_STATUS_PRESSURE (관계 상태 압력)
- ENSEMBLE_WORLD_SPECIFICITY (앙상블/세계 구체성)
- SUBTEXT_PHYSICALIZATION (서브텍스트/행동화)
- CAUSAL_SEMANTIC_FIDELITY (인과·의미 충실도)
- UNSUPPORTED_NOVELTY_RISK (근거 없는 새 사실 위험; 안전할수록 높은 점수)

Critical violations:
- unauthorized new fact/history/relationship;
- future-source leakage;
- canonical-state contradiction;
- unauthorized speaker/entity;
- scene-contract semantic break.

### Frozen Stage B qualification gate
Treatment:
- wins >= 7/12;
- wins + ties >= 10/12;
- losses <= 2/12;
- zero confirmed critical violations under 2-of-3 judge rule.

A valid unfavorable result is immutable.

## Final R70 verdict (최종 R70 판정)
Stage A PASS alone:
`R70_ACTIVE__CONTEXT_PROJECTION_QUALIFIED__SURFACE_EFFECT_PENDING`

Only Stage A + Stage B PASS establishes:
`F08_AUTHORIZED_PROVIDER_CONTEXT_WITH_SURFACE_EFFECT = QUALIFIED`

If Stage B is unavailable because no live credential/execution environment exists:
- do NOT close PASS;
- freeze all Stage B inputs/protocol;
- status remains `WAITING_LIVE_PROVIDER_EXECUTION`;
- no physical Candidate promotion.

## Claim boundary (주장 경계)
R70 PASS does NOT establish:
- F02 Visible-Action Dependence closure;
- F05 Human Distribution/Count Pressure closure;
- Production promotion.

## Physicalization rule (물리화 규칙)
Only after full R70 PASS:
- create new 5-Part / 9-Package Physical Authority;
- preserve exact R69 runtime as Qualified Parent;
- Production remains unchanged.

Status token:
`R70_PREREGISTERED__F08_PROVIDER_CONTEXT_ONLY__STAGE_A_DETERMINISTIC__STAGE_B_LIVE_PAIRED_REQUIRED__PARENT_SYNC_R67__CONTROL_R69_IMMUTABLE__OUTPUTS_0`
