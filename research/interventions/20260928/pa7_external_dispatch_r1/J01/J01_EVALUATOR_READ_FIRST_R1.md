# Independent Blind Evaluator J01 — READ FIRST

You are evaluating two complete Korean broadcast-drama screenplays labeled only SCRIPT A and SCRIPT B.

## Independence
- Use only the files supplied for this evaluation.
- Do not search any repository, project, prior conversation, hidden plan, system/model identity, internal score, or another evaluator's output.
- Do not infer which script is newer, experimental, preferred, or produced by a particular system.
- Do not contact or compare notes with another evaluator.
- Preserve your first complete schema-valid judgment.

## Evaluation order
1. Read both complete scripts.
2. Score all 8 whole-episode axes for A and B.
3. Then score the repeated pre-frozen scene sample SC05/12/21/29/38/46 on all 14 surface axes.
4. Reconstruct the requested narrative structure separately for A and B.
5. Flag only clearly evidenced critical violations from the supplied label list.
6. Choose A, B, or TIE for whole-episode preference and surface-craft preference.
7. Return one JSON object only using J01_OUTPUT_SCHEMA.json.

The repeated sample scenes already occur in the complete scripts. They are repeated only for auditable scene-level scoring and must not be treated as additional scenes in whole-episode scoring.

## Output validity
- Replace every numeric 0 placeholder with a score from 1.0 through 10.0 inclusive.
- Integer or one decimal is allowed.
- Whole score slots required: 16 total.
- Surface score slots required: 168 total.
- Paired preferences must be exactly A, B, or TIE.
- In each reconstruction array, start every item with EVIDENCED: or INFERRED:.
- Critical-violation entries must use only the supplied labels and identify scene evidence. Use [] if none.
- Do not use Markdown fences.
- Do not add prose before or after the JSON.
- Do not revise a valid completed judgment to improve either script's outcome.
