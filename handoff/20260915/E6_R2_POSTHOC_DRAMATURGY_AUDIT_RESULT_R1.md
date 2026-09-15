# E6-R2 Post-hoc Dramaturgy Construct-Validity Audit Result R1

Date: 2026-09-15

## Decision
`CONSTRUCT_VALIDITY_FAIL__HISTORICAL_E6_R2_PASS_PRESERVED__LEVEL3_OPERATIONAL_CLAIM_SUSPENDED__FRESH_DRAMATURGY_REQUALIFICATION_REQUIRED`

## Scope
This result does not rewrite the historical E6-R2 binary result under its original frozen gates. It evaluates whether those gates were sufficient to support the broader claim that E6-R2 demonstrated broadcast-screenplay dramaturgy quality.

## Direct report evidence accepted
The user-supplied full-script review states that it read all 10 sequences / QSC01-QSC50 and judged the script itself, not earlier PASS/FAIL declarations or generation code. It reports:
- 45,064 characters;
- 10 sequences / 50 scenes;
- 300 dialogue utterances;
- every scene exactly 6 utterances;
- every scene exactly 4 speaking characters;
- only 153 distinct dialogue strings;
- three identical dialogue lines repeated 50 times each = 150/300 utterances;
- one identical role-separation direction repeated 50 times;
- 139 limited-scope Korean particle errors after named characters.

These measurements support a systemic rather than isolated template problem.

## Frozen-dimension findings

### 1. DIALOGUE_AS_ACTION — FAIL
Scene-level evidence in the report shows dialogue frequently restating scene design, intent or psychology instead of acting on another character.
Examples documented by the report:
- QSC01: characters verbalize who is trying to raise evacuation rate and who is holding transport.
- QSC33: a character verbalizes the explanation that an early-completion request was mere schedule management.
- QSC49: Mina speaks about herself in third person: `민아는 계정승인 때문에 업무배제를 예상한다.`
This is incompatible with the frozen requirement that dialogue function as demand/refusal/question/concealment/negotiation/attack/avoidance/confession/choice rather than scene-summary narration.

### 2. DIRECTION_DIALOGUE_SEPARATION — FAIL
The report repeatedly finds directions that state desired evaluation outcomes or repeat scene logic rather than providing playable behavior. The same role-separation direction appears 50 times. This turns the surface into plan-explanation plus verbal restatement rather than complementary action + speech.

### 3. DRAMATIC_AGENCY — FAIL
The report documents decisive acts being reported by other characters instead of enacted by the responsible character:
- QSC09: the bus chief's refusal is reported by another character.
- QSC40: Hajin's approval is reported by another character.
- QSC48: a proposal Hajin should make to Taeseong is spoken by Mina.
- QSC49: the work-retention decision is explained by another character.
This removes dramatic agency from the decision owner.

### 4. CAUSAL_PROCESS_ONSCREEN — FAIL
The report documents repeated jumps from problem declaration to resolution declaration:
- QSC17: slow lift response -> attach manual-assist personnel, without visible test/failure/process.
- QSC43: possible late final bus -> depart earlier, without showing what changed or what cost was paid.
- QSC44: roster issue -> corrected by comparison, without dramatized causal steps.
The frozen audit rule requires visible failure -> attempt -> new information/obstacle -> choice/cost -> consequence for major crises.

### 5. SCENE_RHYTHM_VARIANCE — FAIL
Every one of 50 scenes has exactly four speakers and six utterances. Three identical lines account for half of all dialogue utterances. This is direct systemic evidence of a fixed renderer template materially suppressing scene rhythm.

### 6. CHARACTER_VOICE_DIFFERENTIATION — FAIL
Because the same generic operating lines are assigned across scenes and characters, occupation, hierarchy, temperament and relationship-specific language are materially flattened. The report explicitly notes that all characters begin to sound like the same operating principle.

### 7. SPATIAL_CONTINUITY — FAIL
The report documents multiple scenes where location and prop/blocking logic are not shootably clear, including QSC03, QSC27 and QSC35. Co-presence versus remote communication is unclear, and some props/actions do not fit the stated location.

### 8. HUMAN_STAKE_VISIBILITY — FAIL
The episode repeatedly treats 214 evacuees and vulnerable residents as counts reported by staff. Resident dissatisfaction and risk are predominantly reported rather than enacted by specific residents with choices and consequences.

### 9. CLIMAX_AND_ENDING_DISTINCTION — FAIL
QSC41-QSC45, which should contain the evacuation climax, retain the same six-utterance template. QSC50 ends with state-list reporting and the same recurring operating language rather than a distinct final image/action.

### 10. KOREAN_SURFACE_CORRECTNESS — FAIL
The report identifies 139 limited-scope name+particle errors and additional noun-particle problems. This is not the primary dramaturgy defect, but it independently blocks broadcast readiness.

## Root-cause diagnosis
The dominant defect is **contract-to-surface literalization through a fixed ensemble template**:
1. scene-contract summaries/intent/state changes are converted into spoken explanation;
2. the renderer forces a fixed 4-person / 6-utterance scaffold;
3. generic validation language is reused as dialogue;
4. directions describe role separation / state interpretation rather than playable behavior;
5. important action owners are displaced by report speech;
6. crisis processes are compressed into declared outcomes.

This is different from the E6-R1 internal-token leakage defect. E6-R1 fixed lexical/meta leakage; E6-R2 shows that **semantic plan leakage can still occur in natural Korean prose**.

## Historical-result handling
Preserve:
`E6-R2 = PASS_UNDER_ORIGINAL_FROZEN_GATES`

Narrow claim boundary:
`E6-R2 does not establish whole-episode broadcast dramaturgy quality.`

Operational maturity handling:
`LEVEL_3_ENTERED` remains a historical declaration but is `SUSPENDED_FOR_OPERATIONAL_CLAIMS_PENDING_DRAMATURGY_REQUALIFICATION`.

## L3C1 disposition
`L3C1_CROSS_DOMAIN_ENDURANCE = HOLD_PREOUTPUT__SUPERSEDED_BY_DRAMATURGY_REPAIR`
Reason: endurance testing the current renderer would primarily demonstrate persistence of a known dramaturgy defect. No L3C1 scientific output had begun.

## Next legal experiment
`E6-R3 WHOLE-EPISODE DRAMATURGY REPAIR + FRESH REQUALIFICATION`
The successor must repair the renderer/contract interface and validator coverage, then qualify on a fresh domain/sample. The E6-R2 script may be used only as regression evidence, never edited into a PASS replacement.
