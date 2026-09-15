# E6-R3C C2 Fresh Microbench Audit Result R1

Date: 2026-09-15

## Status
`PASS__R3C_C2_FRESH_MICROBENCH__FRESH_WHOLE_EPISODE_SUCCESSOR_ALLOWED`

## Scientific output
- Fresh domain: `해진도 심야도서의료이송센터`
- Input commit: `9fbeb4d6cdef206479cf1c2d53b047da70ca61ea`
- Surface commit: `c6dd59cd3ce244d0db6e4d62f903de92785451dd`
- 12 fresh scenes
- No R3-B scene rewritten.

## Topology result
Actual scene structures are non-uniform.

Speaking cast sizes present:
`1 / 2 / 3 / 4 / 6`

Two-person scenes:
`C2S02, C2S06, C2S08, C2S11`

Low-dialogue scenes:
- C2S04: 1 spoken line
- C2S10: 0 spoken lines

5+ speaker scenes:
`C2S05, C2S09, C2S12`

Remote/cross-cut scenes:
`C2S03, C2S05, C2S07, C2S09, C2S12`

Civilian/family direct choice or refusal:
- C2S02: Bokja directly refuses a plan that separates her from her son.
- C2S08: Bokja directly chooses the slower rescue craft that permits medical accompaniment.

No fixed utterance-count template is present.

## Crisis-process audit
### Chain 1 — first transport attempt
- C2S05: fast private high-speed boat selected under explicit conditions.
- C2S06: cooling-system warning actually appears; captain Minho directly aborts departure.
- C2S07: rescue craft becomes the alternative but cannot berth directly; a new transfer obstacle appears.
- C2S08-C2S09: family chooses the slower medical-accompanied route; new handoff plan is built.

Result: PASS — no `problem -> solved` jump.

### Chain 2 — rescue-craft handoff
- C2S09: offshore handoff is planned with a seven-minute window and two-rope restraint.
- C2S10: slippery steps are physically prepared and tested.
- C2S12: first transfer motion creates a rope snag; direct pulling is stopped; an irreversible rope cut is chosen; the stretcher is transferred only after that costly action.

Result: PASS.

## Dialogue/agency audit
- Scene-summary self narration: 0 critical.
- Third-person self explanation: 0.
- Decisive refusal/choice assigned to its owner: PASS.
- C2S06 captain Minho personally aborts the unsafe first departure.
- C2S08 Bokja personally chooses the slower accompanied route.
- C2S11 Se-young personally apologizes; Ara personally states the trust condition.
- C2S12 Junho personally chooses and performs the rope cut.

## SHOW_ONLY_DIRECTION audit
Authorial interpretation patterns found as critical violations:
`0`

The directions stay on visible/audible production information: warning lights, switches, clocks, rope tension, foot placement, wet stairs, stretcher movement, channel switching, gaze, pauses, objects and physical consequences.

C2S05 contains the broad montage cue `각 장소에서 다른 준비가 동시에 시작된다.` This is less specific than the preferred action-level direction, but it does not explain dramatic meaning, relationship meaning, agency design or thematic interpretation. It is logged as a non-critical craft note, not a boundary violation. Future whole-episode generation should prefer explicit preparation actions at each cross-cut location.

## Spatial/remote audit
- Remote locations are explicitly labeled where used.
- C2S03 separates center and clinic.
- C2S05 separates center/clinic/breakwater/high-speed boat.
- C2S07 separates breakwater/center/rescue-craft radio.
- C2S09 separates rescue craft/breakwater/clinic/center.
- C2S12 distinguishes breakwater actors from rescue-craft actors and remote center voice.
- No prop is used at a location where it has not been established.

Result: PASS.

## Repetition audit
- No three-line universal dialogue template.
- No fixed four-person scene template.
- No repeated role-separation direction.
- No identical full dialogue line identified as systemic repetition.

Result: PASS.

## Korean surface audit
No systemic character-name particle defect pattern like historical `박수현는 / 윤하진가 / 조태성가` appears in this sample.
No critical/systemic particle defect identified.

Result: PASS.

## C2 verdict
Critical gates:
- authorial direction-commentary criticals = 0 PASS
- dialogue-summary criticals = 0 PASS
- displaced decisive agency criticals = 0 PASS
- major crisis-process omissions = 0 PASS
- spatial continuity criticals = 0 PASS
- repeated-template critical = 0 PASS
- internal/meta leakage = 0 PASS
- systemic Korean particle defect = 0 PASS

Decision:
`PASS__R3C_C2_FRESH_MICROBENCH__FRESH_WHOLE_EPISODE_SUCCESSOR_ALLOWED`

## Claim boundary
This PASS validates the narrowed Show-Only Direction repair on a fresh 12-scene sample only. It does not restore the Level-3 operational claim. A completely fresh whole-episode successor, internal whole-episode PASS, fresh external blind PASS, physical 5-Part/9-Package reseal and Hub pointer update remain required.
