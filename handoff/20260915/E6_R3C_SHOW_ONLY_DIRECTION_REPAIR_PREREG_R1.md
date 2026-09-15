# E6-R3C Show-Only Direction Boundary Repair Prereg R1

Date: 2026-09-15

## Status
`PREREGISTERED__OUTPUTS_0`

## Parent evidence
- Historical physical authority: `SYNC-R52`
- Operational Level-3 claim remains suspended.
- E6-R3A microbench: PASS.
- E6-R3B fresh whole-episode output: immutable FAIL, SAFE_NO_COMMIT.
- E6-R3B failure commit: `745b4e50a092576d7df5f034d0f5bde14bd23dee`
- R3-B scientific surface Git blob: `52d525c5904fb67892398ed4c8476d3adad992e2`

## Problem statement
R3-B repaired the old E6-R2 fixed scene/dialogue topology, direct decisive-agency displacement and crisis-process skipping, but stage directions still sometimes contain authorial explanations of what the action means.

Observed failure class:
`DRAMATURGICAL_COMMENTARY_LEAKAGE_IN_DIRECTION`

Refined causal path:
`SEMANTIC INTENT -> PLAYABLE ACTION + REDUNDANT AUTHORIAL INTERPRETATION`

The repair target is NOT dialogue topology and NOT the frozen R3-B story. The target is the Surface Direction Boundary only.

## Repair hypothesis
A direction boundary that admits only camera/actor-observable information and rejects dramaturgical interpretation will preserve the improved R3 topology while removing authorial explanation from directions.

## SHOW_ONLY_DIRECTION_BOUNDARY R1
Allowed in stage direction:
- place/time/weather/light/sound that can be perceived;
- actor movement, blocking, distance, posture;
- facial change, gaze, breath, voice behavior;
- prop interaction;
- hesitation, pause, silence and failed physical attempt;
- directly observable physical consequence;
- explicit remote-medium/location framing where needed for production continuity.

Forbidden in stage direction:
- explaining the dramatic function of the action;
- naming agency ownership (`행동 주체는 ...`);
- explaining what the image means (`~임이 화면에서 드러난다`);
- summarizing causality after it is already shown (`그 거절 때문에 계획 전체가 바뀐다`);
- stating thematic cost/lesson (`해결은 희생 위에서 가능해진다`);
- explaining relationship meaning (`신뢰 회복은 ... 방식으로 남는다`);
- saying what the writing/scene does (`장면이 끝난다`, `성공을 선언하지 않는다`);
- state/validator/meta vocabulary.

## Detection candidates
The validator must flag direction sentences containing semantic-commentary patterns for coordinator review, including but not limited to:
- `~라는 사실`
- `~로 남는다`
- `~때문에 계획/관계/결정이 바뀐다`
- `해결은 ~ 가능해진다`
- `화면에서 드러난다`
- `장면이 ~`
- `성공을 선언하지 않는다`
- `행동 주체`
- `신뢰 회복`
- `의미/극적/서사/주제/관계 변화` when used as authorial interpretation rather than a visible prop/text within the fiction.

Pattern matching alone does not determine scientific guilt. Coordinator adjudication must inspect the full direction and decide whether the flagged clause is observable/shootable or authorial commentary.

## Stage C1 — detection-only regression
Input is the immutable failed R3-B surface.
The repair/validator may NOT rewrite it.

Pass requirements:
1. Detect all 14 preregistered verified commentary examples from the R3-B internal audit.
2. False-negative count on those frozen examples = 0.
3. Do not classify ordinary scene headings, direct physical action or location-separation directions as failures merely because they contain abstract nouns.
4. Produce only a detection/adjudication receipt; no corrected R3-B surface.

## Stage C2 — fresh dramaturgy microbench
Only after C1 PASS.
Use a completely fresh domain and 12 fresh scenes, not floodgate, wildfire, harbor or railway domains.

Fresh domain:
`해진도 심야도서의료이송센터`

Required 12-scene topology:
- at least 3 two-person scenes;
- at least 2 0-2-line scenes;
- at least 2 5+ speaker scenes;
- at least 2 remote/cross-cut scenes;
- at least 2 civilian/patient-family refusal or choice scenes;
- at least 2 failed-attempt -> altered second-attempt chains;
- one direct relationship fracture/repair scene;
- one irreversible/costly climax action;
- no fixed utterance template.

C2 critical gates:
- authorial direction-commentary criticals = 0;
- dialogue-summary criticals = 0;
- displaced decisive agency criticals = 0;
- major crisis-process omissions = 0;
- spatial continuity criticals = 0;
- repeated-template critical = 0;
- internal/meta leakage = 0;
- systemic Korean particle defect = 0.

## Successor rule
Even C1+C2 PASS does NOT restore Level-3 operational claim.
It only allows a fresh whole-episode successor requalification on a new domain.
The immutable R3-B failed episode may never become that PASS sample.

## Outputs at preregistration
- C1 detection receipt: 0
- C2 scene outputs: 0
- C2 audit: 0
- State Commit: 0
- External judgments: 0

No threshold, frozen R3-B failure example, C2 topology requirement or direction rule may change after first C1 output.
