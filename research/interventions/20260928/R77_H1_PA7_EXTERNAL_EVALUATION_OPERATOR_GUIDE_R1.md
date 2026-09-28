# PA7 External 3-Judge Blind Evaluation — Operator Guide R1

Date: 2026-09-28  
Status: SEALED BEFORE JUDGE OUTPUTS 0/3

## 1. Purpose

This guide tells the coordinator how to run three independent blind evaluations without contaminating the experiment. It does not change screenplay bytes, A/B mapping, scene sample, axes, gates, or thresholds.

## 2. Non-negotiable independence

Run J01, J02, and J03 in three fresh independent evaluator contexts.

For each judge:
- use only that judge's own blind packet and output schema;
- do not provide Project/GitHub context, prior chat, hidden plan, state ledger, model/system lineage, internal scores, another judge's output, or coordinator mapping;
- do not ask the judge to guess which script is experimental, newer, preferred, or produced by a particular system;
- do not let one judge see any other judge response;
- preserve the first complete schema-valid judgment.

The coordinator must not act as one of the judges because the coordinator knows the experiment lineage and holds the hidden mapping.

## 3. Judge-facing files

For Jxx, provide only:
1. Jxx_EVALUATOR_READ_FIRST_R1.md
2. Jxx_BLIND_PACKET.txt
3. Jxx_OUTPUT_SCHEMA.json

Keep Jxx_PACKET_MANIFEST.json and Jxx_PACKAGE_MANIFEST_R2.json with the coordinator for integrity checking. Do not provide COORDINATOR_MAPPING_R1.json to any judge.

## 4. Evaluation order

Each judge should:
1. Read the neutral evaluator read-first file.
2. Read SCRIPT A and SCRIPT B as complete episodes.
3. Score all eight WHOLE_EPISODE_AXES for A and B.
4. Then use the repeated pre-frozen sample block only for the 14 SURFACE_AXES at SC05/12/21/29/38/46.
5. Reconstruct premise, major threads, sequence functions, relationship trajectories, resolved due-now, and deferred/open material separately for A and B.
6. Flag only clearly evidenced critical violations, using only the frozen labels.
7. Choose A/B/TIE for whole-episode preference and surface-craft preference.
8. Return JSON only.

The repeated sample scenes already exist inside the complete scripts. They are repeated only to make surface scoring auditable; they must not be treated as extra scenes when scoring the whole episode.

## 5. Required score completeness

Per judge:
- Whole scores: 2 scripts × 8 axes = 16 numeric scores.
- Surface scores: 2 scripts × 6 scenes × 14 axes = 168 numeric scores.
- Every score must be 1.0–10.0 inclusive; integer or one decimal.
- No score placeholder may remain 0.
- Preferences must be exactly A, B, or TIE.

## 6. Reconstruction and violation notation

Keep the existing output-schema fields.

Each reconstruction array item should begin with:
- `EVIDENCED: ...` when directly supported by screenplay text/action; or
- `INFERRED: ...` when a reasonable inference is required.

Each critical violation entry should be a string:
`LABEL | SCxx[,SCyy] | concise evidence`

Use `[]` when no critical violation is found.

## 7. Raw-output custody

As soon as the judge returns a complete JSON:
1. Save the raw response unchanged.
2. Compute SHA256 and record byte/character length.
3. Validate JSON parse, judge_id, field completeness, score ranges, sample scenes, axis keys, preference enum, and allowed critical labels.
4. If valid, mark it immutable and do not request a better answer.

Do not edit an unfavorable score.

If the response has only transport/UI artifacts (for example Markdown fence or UI annotation) but all substantive fields are present and unambiguous, preserve the raw response first and create a canonicalized copy with a receipt describing exactly the transport-only normalization. Never alter substantive fields.

If substantive fields are missing or ambiguous, do not repair them manually and do not reveal mapping. Preserve the invalid raw output and stop for protocol adjudication.

## 8. Mapping reveal

Do not open/disclose the coordinator mapping until J01, J02, and J03 each have a first schema-valid raw judgment with SHA256 sealed.

Only after 3/3:
- reveal the mapping;
- map A/B to the two experimental arms;
- compute frozen gates.

## 9. Gate calculations

### Absolute gate
For each judge and mapped script:
- whole mean = arithmetic mean of eight whole-axis scores;
- surface mean = arithmetic mean of 84 scene-surface scores (6 × 14).

Mapped target arm must have whole mean >=7.0 for at least 2/3 judges, surface mean >=7.0 for at least 2/3, and no critical violation confirmed by >=2 judges.

### Paired gate
- mapped target surface preference wins >=2/3;
- mapped target whole preference wins + ties >=2/3.

### Focus gate
Frozen focus axes:
- DIALOGUE_SUBTEXT
- CHARACTER_VOICE
- PHYSICALIZATION_ACTION
- PERFORMANCE_DIRECTION_QUALITY
- EMOTION_EXTERNALIZATION
- DIRECTION_DETAIL_ECONOMY

For each focus axis, pool the 18 scores per arm (3 judges × 6 pre-frozen scenes) and compute the median. Delta = target median − comparison median.

Qualification requires:
- target pooled median not lower on CHARACTER_VOICE, DIALOGUE_SUBTEXT, PHYSICALIZATION_ACTION, and KOREAN_SPOKEN_NATURALNESS; and
- at least 4 of the 6 frozen focus axes have delta >= +0.50.

Do not weaken the +0.50 or 4-of-6 threshold after results are seen.

### Recoverability gate
Use the three independent reconstruction outputs. Core consensus requires at least 2/3 judges to recover the same substantive core for:
- episode premise;
- major threads;
- all nine sequence movements in functional order;
- principal relationship trajectories;
- resolved due-now material;
- deferred/open material.

Different wording is acceptable; the same causal/functional proposition must be recovered.

## 10. After PA7

If PA7 passes all frozen gates:
- rebuild the six H1 launch packets at >=40K;
- keep Human targets unopened;
- run PM0 before real-provider H1 C/T.

If PA7 fails any frozen gate:
- preserve the failure;
- do not change the threshold;
- localize the responsible ancestor before a new intervention.
