# P07-I4A Surface Literary Compression / Voice Realization Repair Probe — Preregistration R1

Date: 2026-09-07
Classification: PREFORMAL DEVELOPMENT REPAIR PROBE / NO FORMAL COUNT DELTA
Parent physical authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I3_BROADCAST_BIDIRECTIONAL_LOOP_R1`
Parent C2 SHA256: `6abf3934a2434968a13ac9a83f5b86e97222fc5f1c97019caec7c64a66299e08`
Frozen DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
Parent P07-I4A preregistration: `P07_I4A_PROVIDER_EMULATION_AND_INTERNAL_BLIND_CRAFT_BENCHMARK_PREREG_R1.md`

## 1. Triggering evidence
Internal blind craft benchmark was calibrated before use and then showed Human 12 wins / Candidate 0 wins / Tie 0 across 12 matched scene-function pairs. Objective text metrics over those same pairs showed Candidate mean excerpt length 1,108 vs Human 733 Unicode characters; procedural/verification term density 18.32 vs 0.21 per 1,000 characters; mean non-empty line length 64.7 vs 35.6 characters.

This repair is therefore result-informed in *problem selection* but must be preregistered before any repaired surface is generated. No blind scoring thresholds or human anchors may be changed after repaired outputs are seen.

## 2. Purpose
Test whether a narrow `SCENE_PLAN -> SURFACE_REALIZATION` repair can reduce procedural exposition and improve character-specific voice/subtext without altering upper episode/ensemble/sequence causality.

## 3. Repair scope
Minimum responsible layer is frozen as `SCENE_PLAN / SURFACE_REALIZATION`, not Episode/Ensemble/Sequence, unless a new structural contradiction is discovered. Upper architecture, event ownership, sequence order, thread movement and exit-state contracts are held fixed.

## 4. Frozen repair rules
For six selected P07-I3 scenes:
1. Separate `functional_truth` from `surface_visible_budget`.
2. Internal provenance/verification logic must not be copied into dialogue unless dramatically necessary.
3. At most two explicit procedural/verification concepts may be verbalized per scene unless the scene function is explicitly procedural; even then they must be attached to conflict, choice, status or consequence.
4. `character_agenda_before_information_agenda`: every principal speaker must pursue a personal/social objective before delivering information.
5. Every principal character receives a `voice_signature` containing sentence-length tendency, directness, avoidance strategy, humor/aggression pattern, taboo/avoided vocabulary, and preferred physical behavior.
6. Prefer action/object/withholding/reaction over explanatory speech when the same state transition can be shown.
7. No planning rationale, provenance, scene function, validation rule, uncertainty taxonomy or database language may appear as meta-exposition.
8. Dialogue compression target: preserve required semantic beats while reducing explanatory surface. Do not target a fixed percentage reduction if doing so harms clarity.
9. Preserve scene objective, obstacle, turn, information change, relationship change and exit state.
10. Python may measure/route/validate only; literary rewriting must be performed by an LLM surrogate or Live provider.

## 5. Six-scene development sample
Use six P07-I3 scenes spanning distinct functions and previously observed blind weaknesses. Preferred frozen scene IDs: S11, S14, S21, S33, S37, S50. If a source extraction mismatch makes one unavailable, replace only before first repaired output and record the reason.

## 6. Evaluation design
Create six new anonymous Human-vs-Repaired Candidate pairs using human anchors not used in the original 12-pair main comparison where practicable. Pair by scene function. Randomize LEFT/RIGHT with a new fixed seed and seal mapping separately.

Primary outcome: pairwise Human / Candidate / Tie.
Secondary diagnostics: Dialogue Naturalness, Voice Differentiation, Subtext, Physicalization, Dramatic Compression, Interpersonal Specificity, Ending/Turn Pressure.

## 7. Pass / hold rules
A development improvement signal requires ALL:
- repaired Candidate wins or ties at least 3 of 6 pairs;
- Candidate wins at least 1 of 6 pairs;
- no critical continuity/unsupported-invention violation;
- all six repaired scenes preserve frozen scene semantic contracts;
- procedural-term density decreases materially versus the same six pre-repair scenes;
- no new repetition/template failure.

If Candidate loses 5 or 6 of 6, verdict `SURFACE_REPAIR_INSUFFICIENT__HOLD_FULL_EPISODE_RERENDER`.
If Candidate wins/ties >=3 but continuity breaks, verdict HOLD.
No full 50-scene rerender is allowed before this six-scene gate passes.

## 8. Claim boundary
This is internal development metrology, not external human validation, Live Provider evidence, Production promotion, RFV3, CP1, R-F/R-G or Formal R140.

## 9. Physical persistence
If the repair changes accepted runtime/prompt/control code, and only if the development gate passes, propagate accepted changes into the canonical 5 logical Parts / 9 physical Packages and reseal. Failed repair outputs remain evidence but must not replace P07-I3 current physical authority.
