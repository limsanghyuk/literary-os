# P07-I4H Prospective Craft Validation R2 — Result

Date: 2026-09-08
Classification: DEVELOPMENT / PREFORMAL / VIRTUAL / NO FORMAL COUNT DELTA

Preregistration commit: `cde49d2e7945faa9fd0c9cbef0b43850103d8426`
Generation-seal commit: `0aaac69ce75b759ba9a4bdfd9f0a67826792e0a2`
Judgment-seal commit: `3bc8df7969f1fe1dab694b049feede766e42feda`

## Final verdict
`PASS__VIRTUAL_CRAFT_SIGNAL__CONSERVATIVE_SELECTOR_NONLOSS__NO_PROMOTION__NO_LIVE_CLAIM`

## Preregistered gate arithmetic

### Gate A — selected arm best/co-best >=9/12
Selected arm outcomes:
- selected WIN: V01, V02, V04, V05, V06, V07, V08, V09, V11, V12 = 10
- selected CO-BEST/TIE: V10 = 1
- selected LOSS: V03 = 1

Selected best/co-best = **11/12** -> PASS.

### Gate B — selected arm strictly worst <=1/12
Strictly worse selected arm: V03 only = **1/12** -> PASS.

### Gate C — selected intervention scenes nonloss >=4/5 and wins >=3/5
Selected intervention scenes:
- V02 LOW -> Treatment WIN
- V06 STANDARD -> Treatment WIN
- V08 STANDARD -> Treatment WIN
- V10 LOW -> CO-BEST/TIE
- V11 LOW -> Treatment WIN

Nonloss = **5/5** -> PASS.
Outright wins = **4/5** -> PASS.

### Gate D — ABSTAIN scenes Control best/co-best >=6/7
ABSTAIN scenes:
- V01 Control WIN
- V03 Control LOSS
- V04 Control WIN
- V05 Control WIN
- V07 Control WIN
- V09 Control WIN
- V12 Control WIN

Control best/co-best = **6/7** -> PASS.

### Gate E — critical semantic/speaker/source-future violations = 0
Observed = **0** -> PASS.

### Gate F — selected intervention outputs reliability 5/5
V02/V06/V08/V10/V11 = **5/5 PASS**.

### Gate G — no threshold weakening
Thresholds changed after generation = FALSE -> PASS.

All preregistered gates PASS.

## What this result supports
The conservative three-stage doctrine is supported as a **virtual development signal**:

1. start from ABSTAIN rather than from mandatory intervention;
2. intervene mainly where procedural/reveal/kinetic pressure makes externalized action useful;
3. preserve dialogue-heavy surfaces when dialogue itself carries status negotiation, humor, intimacy, or ensemble social texture;
4. use a reliability gate before accepting any intervention output;
5. treat LOW and STANDARD as different risk levels rather than interchangeable style strength.

The result directly reproduces the boundary learned in I4G: `less dialogue` and `more direction` are not universal quality rules. The useful distinction is explanatory audience-facing dialogue versus dialogue that actually performs character/social action.

## Negative finding retained
V03 shows under-intervention risk. The frozen selector abstained, but the LOW counterfactual was better because physicalized shared-object handling strengthened subtext without erasing voice.

This is one miss, not grounds for globally lowering the intervention threshold. The next design may annotate—but must not post-hoc retrofit into this result—a prospective feature such as:
`PHYSICALIZABLE_SUBTEXT_WITHOUT_SOCIAL_TEXTURE_LOSS`.

Any future use of that feature requires its own preregistered test.

## Promotion / state boundary
- Active development engine change: FALSE.
- Active I4D pointer change: FALSE.
- Semantic-contract candidate promotion: FALSE.
- Literal treatment prose promotion: FALSE.
- Formal count delta: 0.
- R140 delta: 0.
- OpenAI Live claim: FALSE.
- Human-writer equivalence claim: FALSE.

## Next allowed research unit
This PASS is sufficient to **design** P07-I4I Variable-scale Whole-Episode Virtual Rerender Pretest, not to claim whole-episode quality in advance.

I4I must retain:
- >=35,000 Unicode characters as a minimum reference floor for a full episode;
- no fixed maximum;
- 9–10 sequences and 45–50 scenes as minimum reference floors, not fixed targets/maxima;
- Scene = Action/Direction + Dialogue;
- dialogue may remain extensive when it performs voice, humor, intimacy, conflict, status, or ensemble social texture;
- explanatory burden should move to playable/filmable action where useful;
- receipted top-down planning and explicit backpropagation rather than silent plan drift;
- no Real Live / CP1 / Formal R140 claim in the virtual environment.

## Claim boundary
The result is same-session, nonindependent, nonblind, synthetic-scene virtual development evidence. It cannot establish external consensus, real-provider parity, or broadcast-scale human competitiveness.