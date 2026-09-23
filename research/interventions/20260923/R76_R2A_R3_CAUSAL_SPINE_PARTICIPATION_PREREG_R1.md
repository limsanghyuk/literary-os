# R76-R2A-R3 Causal-Spine Participation Repair — Preregistration R1

Date: 2026-09-23
Status: `PREREGISTERED__OUTPUTS_0`

## Trigger
- Frozen R76 engineering case: R2A-R2 PASS at 9 sequences.
- Fresh replication `SYNTH_R76_NIGHT_FERRY_TERMINAL`: R2A-R2 FAIL at 8 sequences.
- Fresh failure retained full coverage, zero-related-pairs 0, owner-only-four-bundle 0.
- Therefore R2A-R2 over-admits a four-obligation bundle whenever even one internal dependency edge exists.

## Diagnosis
A four-obligation Sequence is still too permissive when:
- only a minority of members participate in the internal dependency graph, or
- three or more independent roots are merely aggregated by owner overlap.

## Frozen R2A-R3 rule
All R2A-R2 gates remain, except the four-member permission is strengthened:

1. New obligation must be related >=2 to EVERY member already in the bundle.
2. Bundle size <=3 is allowed under rule 1.
3. A size-4 bundle is allowed only if BOTH:
   - at least 3 of 4 members participate in at least one internal `depends_on` edge; AND
   - independent-root count within the bundle <=2.
4. Otherwise that fourth obligation starts a new Sequence.
5. No cloning, omission, rewriting, or numeric-target split.
6. R2B semantic-role repair remains unchanged.

## Gates
Run on BOTH:
- original frozen R76 structural case
- previously frozen fresh replication case

For each:
- full obligation coverage exactly once
- clone/omission 0
- zero-related pair 0
- invalid four-member bundle 0
- sequence_count >=9
- sequence_count <=14
- F04 repetition groups after unchanged R2B = 0

Cross-case:
- all gates PASS on both cases before any Stage-B authorization.

## Claim boundary
Structural provider-analog generalization only. No actual OpenAI model-quality equivalence, no screenplay-surface qualification, no Production/Level-3/R140 claim.
