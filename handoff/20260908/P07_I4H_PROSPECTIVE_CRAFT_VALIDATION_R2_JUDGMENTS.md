# P07-I4H Prospective Craft Validation R2 — Judgment Seal

Date: 2026-09-08
Preregistration commit: `cde49d2e7945faa9fd0c9cbef0b43850103d8426`
Generation-seal commit: `0aaac69ce75b759ba9a4bdfd9f0a67826792e0a2`
Judge classification: `TEMPORALLY_SEPARATED__NONINDEPENDENT__NONBLIND__VIRTUAL_DEVELOPMENT`

No prose changes were made after the generation-seal commit. This document records judgments only; final preregistered gate arithmetic is deferred to the result document.

## Evaluation method
Pass A scored craft on dialogue naturalness, voice specificity, subtext/physicalization, scene action, information control, pacing/economy, relationship/status motion, and turn/carry-forward pressure.

Pass B separately checked semantic fidelity, allowed-speaker fidelity, voice/humor/social-rhythm preservation, exposition, dialogue over-compression, direction bloat/non-playability, malformed Korean, and foreign-script intrusion.

If the two passes pointed in different directions, the conservative outcome was used.

## Per-scene judgments

| Scene | Control craft | Treatment craft | Preservation finding | Conservative judgment |
|---|---:|---:|---|---|
| V01 FAMILY_BREAKFAST_COMEDY | 8.1 | 7.4 | Treatment loses some sibling/mother comic timing and verbal personality although action is clean | **CONTROL WIN** |
| V02 HOSPITAL_RECORDS_DEADLINE | 7.2 | 8.4 | Treatment removes audience-facing procedure explanation while keeping necessary commands and clean action chain | **TREATMENT WIN** |
| V03 ROMANTIC_RETURNED_OBJECT_SUBTEXT | 8.1 | 8.4 | Both preserve relationship state; Treatment gains playable contact/subtext without over-explaining | **TREATMENT WIN** |
| V04 EXECUTIVE_STATUS_NEGOTIATION | 8.5 | 7.8 | Treatment is efficient but compresses the linguistic status duel that is itself the scene action | **CONTROL WIN** |
| V05 NEIGHBORHOOD_ENSEMBLE_BANTER | 8.7 | 7.9 | Treatment preserves facts but reduces distinct community voices and ensemble comic friction | **CONTROL WIN** |
| V06 WHISTLEBLOWER_REVEAL | 7.3 | 8.6 | Treatment makes the reveal and preservation turn legible through action while retaining the key spoken boundary | **TREATMENT WIN** |
| V07 GRIEF_RITUAL_NEW_RELATIONSHIP | 8.6 | 8.0 | Treatment is playable but removes useful direct relationship language; Control better performs consent/boundary negotiation | **CONTROL WIN** |
| V08 FIELD_EVACUATION_URGENT_ACTION | 7.1 | 8.7 | Treatment converts explanation into coordinated action, preserves safety meaning, and strengthens pressure | **TREATMENT WIN** |
| V09 SCHOOL_STAFFROOM_COMMUNITY_FRICTION | 8.4 | 7.7 | Treatment is clean but flattens counselor/teacher professional-social texture | **CONTROL WIN** |
| V10 NEWSROOM_CORRECTION_DEADLINE | 7.8 | 8.0 | Treatment improves execution clarity; Control retains slightly more newsroom reasoning/voice. Neither dominates after preservation pass | **CO-BEST / TIE** |
| V11 ELEVATOR_EVIDENCE_EXIT_ESCALATION | 7.5 | 8.4 | Treatment removes redundant explanation and makes the evidence transfer/exit escalation cinematic without new facts | **TREATMENT WIN** |
| V12 BLIND_DATE_COMIC_MISUNDERSTANDING | 8.8 | 8.2 | Treatment is readable, but Control has stronger embarrassment timing and distinct comic voices | **CONTROL WIN** |

## Mechanical / reliability review of selected outputs
Selected outputs under the preregistered selector:
- V01 Control
- V02 Treatment LOW
- V03 Control
- V04 Control
- V05 Control
- V06 Treatment STANDARD
- V07 Control
- V08 Treatment STANDARD
- V09 Control
- V10 Treatment LOW
- V11 Treatment LOW
- V12 Control

Critical semantic violation: 0.
Unauthorized principal speaker: 0.
Source/future leakage: 0 (synthetic semantic contracts contain no external source continuation).
Malformed-Korean sentinel: 0.
Foreign-script intrusion: 0.
Selected Treatment surfaces passing the surface reliability checklist: V02/V06/V08/V10/V11 = 5/5.

## Important negative finding
V03 is a real selector miss in this virtual sample. The frozen selector chose ABSTAIN, but the LOW counterfactual was better because modest physicalization strengthened romantic subtext without sacrificing voice or relationship texture.

This does **not** justify globally lowering the intervention threshold. I4F demonstrated that over-intervention was the larger historical failure. The narrower inference is that a future selector may need a specific `PHYSICALIZABLE_SUBTEXT_WITHOUT_SOCIAL_TEXTURE_LOSS` eligibility feature so that some quiet relationship scenes can qualify without broadly expanding mode use.

## Boundary
These judgments are not independent or externally blind. They may support only virtual development decisions and may not be promoted to human-competitive or Live evidence.