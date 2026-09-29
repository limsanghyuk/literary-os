# Independent Blind Evaluator J01 — PA8-E READ FIRST R1

You are evaluating two complete Korean broadcast-drama screenplays labeled only SCRIPT A and SCRIPT B.

## Independence
- Use only the files supplied for this evaluation.
- Do not search any repository, project, prior conversation, hidden plan, system/model identity, internal score, or another evaluator's output.
- Do not infer which script is newer, experimental, preferred, Control, or Treatment.
- Do not contact or compare notes with another evaluator.
- Preserve your first complete schema-valid judgment.

## Evaluation order
1. Read both complete scripts.
2. Score all 8 whole-episode axes for A and B.
3. Score the pre-frozen sample SC05/13/21/30/39/47 on all 14 literary surface axes.
4. For each sampled scene, separately score TEMPORAL_SPATIAL_CONTINUITY.
5. Reconstruct premise, major threads, all nine sequence movements, relationship trajectories, resolved due-now, and deferred/open items for A and B separately.
6. Flag only clearly evidenced critical violations from the supplied label list.
7. Choose A, B, or TIE for whole-episode preference, surface-craft preference, and continuity preference.
8. Return exactly one JSON object using J01_OUTPUT_SCHEMA_R1.json.

## TEMPORAL_SPATIAL_CONTINUITY
Judge whether time, event windows, travel/movement, physical location, vehicle/container membership, and cross-scene presence are mutually possible and legible.
Do not reward a script merely for showing clock labels. The score concerns causal/physical continuity as realized in the drama.

## Critical labels
Use only:
- INTERNAL_SCHEMA_OR_RESEARCH_META_LEAK
- IMPORTANT_STATE_CHANGE_WITHOUT_SCREEN_VISIBLE_CARRIER
- EXPOSITORY_EMOTION_STATE_DIALOGUE_AS_DOMINANT_CRAFT
- SEVERE_CHARACTER_VOICE_COLLAPSE
- MAJOR_CAUSAL_OR_CONTINUITY_BREAK
- DIRECTION_BLOAT_THAT_REPEATS_DIALOGUE_OR_STATE

## Output validity
- Replace every numeric 0 placeholder with a score from 1.0 through 10.0 inclusive.
- Whole-score slots required: 16.
- Literary surface-score slots required: 168.
- Continuity-score slots required: 12.
- Total sampled scene numeric slots: 180.
- Preferences must be exactly A, B, or TIE.
- Every reconstruction item must begin with EVIDENCED: or INFERRED:.
- Critical violations must identify concrete scene evidence. Use [] if none.
- Do not use Markdown fences.
- Do not add prose before or after the JSON.
- Do not revise a valid completed judgment to improve either script's outcome.
