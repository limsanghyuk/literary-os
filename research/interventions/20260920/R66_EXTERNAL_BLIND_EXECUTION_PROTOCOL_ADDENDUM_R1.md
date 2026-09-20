# R66 External Blind Quality Execution Protocol Addendum R1

Date: 2026-09-20
Status: `FROZEN_BEFORE_ANY_INDEPENDENT_JUDGMENT`

## Timing
Frozen after:
- R66 preregistration;
- implementation source freeze;
- fresh-input seal;
- Control/Treatment primary execution;
- mechanical PASS;
- selector-safety PASS.

No independent quality judgment has been collected yet.

## Judge execution
- Three independent fresh-context judges: J01, J02, J03.
- Each judge receives only its own sealed packet.
- Each judge evaluates all 12 pairs.
- A/B mapping is exactly 6/6 per judge and hidden.
- No judge may see R62-R66 lineage, source code, coordinator mapping, other judge responses, or desired outcome.
- No judge may search the Literary OS repository or prior conversations.

## Evaluation axes
- TRANSACTION_SPECIFICITY
- CAUSAL_COHERENCE
- RESISTANCE_CHOICE_COST_DEVELOPMENT
- NON_MECHANICAL_PROGRESSION
- SCENE_STEP_NECESSITY
- OBLIGATION_FIDELITY
- SEMANTIC_APPLICABILITY
- UNSUPPORTED_NOVELTY_PREMATURE_RESOLUTION_RISK

## Per-pair aggregation
After all three valid judgments are sealed:
1. Map each judge A/B/TIE to Treatment/Control/TIE using coordinator mapping.
2. >=2 Treatment votes -> Treatment WIN.
3. >=2 Control votes -> Treatment LOSS.
4. Otherwise -> TIE.
5. A Treatment critical violation is critical if >=2/3 judges flag the mapped Treatment arm.

## Frozen overall qualification gate
- Treatment wins >= 7/12
- Treatment wins + ties >= 10/12
- Treatment losses <= 2/12
- zero critical Treatment state/obligation-fidelity violations

A valid unfavorable result is immutable.

## Packet custody
J01 SHA256:
`c87f361fbec52d52b98f840d0045b493839bd5d12a147a54bc0ed552f6edba4b`

J02 SHA256:
`e263ab9c5ed4fc5b96e91f95a0f845607d851021e0d9c0b332f3cdd37df40222`

J03 SHA256:
`390b528c3a7aff921e7143b9657725cd9287c1f77a314e399a5aee950181fde6`

Dispatch bundle SHA256:
`0a5b7f99dcfffebf15a2ace135388511312ca21fd7721fe1ec592aeeff340f0f`

Coordinator mapping secret JSON SHA256:
`be8d1548598bbd49d0908af0d70c968ab0687467feb99747fa245c08c7371748`

Coordinator secret ZIP SHA256:
`86942e71c3f7d289c44df67f63b17ee3811848c36dbbb400788f23a5991204a5`

The mapping content is intentionally not included in judge packets or this Hub document.
