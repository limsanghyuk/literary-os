# P07-I4K-5 Pre-Release Protocol Correction R2

Date: 2026-09-10
Experiment: `P07-I4K-5-INDEPENDENT-HUMAN-EXTERNAL-QUALIFICATION-GATE`
Parent prereg commit: `bcad5e951dd9e3358ea7f9696c4ed664ffff58a2`
Parent physical authority: `P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R15__I4K5_PREREG_PACKETS_SEALED_AWAITING_EXTERNAL_JUDGES`

## Trigger
Before any external judge response existed, coordinator-side integrity inspection compared the R1 anonymized packet episode bodies against named I4K-4 Control/Treatment source files. The R1 packets themselves were structurally valid and contained the exact two sealed whole episodes, but this verification made the coordinator capable of inferring R1 A/B identity before judge responses.

## Decision
R1 judge packets are `SUPERSEDED_PRE_RELEASE__DO_NOT_USE_FOR_SCIENTIFIC_JUDGING`.
They were not used to obtain any judge response. Judge responses remain 0; unblind scientific analysis remains 0; no H1-H4 verdict exists.

## R2 repair
Create a completely fresh coordinator-private A/B remapping for J01-J05 using cryptographic randomness in a subprocess that does not print side identity. Do not reveal mapping contents to the coordinator analysis channel. Validate R2 packets only by unordered-set equality to the two sealed anonymized I4K-4 episode surfaces, structure counts, length counts, forbidden-metadata scan, and packet SHA256. Do not report which side corresponds to Control/Treatment.

The judge instruction text may be expanded only to clarify already-frozen axes, evaluation order, anti-bias rules, and output formatting. No scientific threshold, sample unit, episode byte content (aside from anonymized wrapper), scoring axis, critical-violation category, or decision rule may change.

## Frozen scientific rules unchanged
- 3 valid independent external GPT judges required from up to 5 slots.
- First three valid responses in chronological receipt order count.
- J04/J05 replacement-only for no-response or protocol-invalid responses.
- 12 units: U01-U10 sequence pairs, U11 whole-episode architecture, U12 whole-episode broadcast craft.
- Individual judge gate: Treatment wins >=5/12, nonloss >=8/12, losses <=4/12.
- H1 aggregate: Treatment majority wins >=5/12, nonloss >=9/12, losses <=3/12.
- H2: >=2/3 valid judges pass individual gate.
- H3 whole-episode and ceiling-sensitive target-axis criteria unchanged.
- H4 verified critical violations 0, >=10/12 units with 2+ judge agreement, protocol breaches 0.
- Claim boundary unchanged: same-family external GPT consensus is not human or cross-family consensus.

## State at correction seal
Judge responses: 0.
Valid judges: 0.
Scientific unblind: 0.
Verdict: none.
