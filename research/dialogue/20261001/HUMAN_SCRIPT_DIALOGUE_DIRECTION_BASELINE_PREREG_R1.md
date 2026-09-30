# Human Broadcast Script Dialogue / Direction Baseline — Preregistration R1

Date: 2026-10-01
Status: PREREGISTERED__RAW_HUMAN_SCRIPT_SOURCE_ACCESS_PENDING

## Purpose

Measure what the prior 945,719-line subplot study did **not** measure:

- dialogue characters / (dialogue + direction characters);
- direction characters / (dialogue + direction characters);
- dialogue-turn length distribution;
- exchange length before location/time/scene break;
- short-turn and long-turn shares;
- speaker concentration;
- register variation;
- conversational repair markers;
- dialogue-driven state-change evidence.

The purpose is to create a human-script baseline before imposing any numeric dialogue-share gate on Literary OS.

## Source policy

Use only human-authored broadcast screenplay/source-text records already held in the Literary OS corpus/DB archives or separately verified human scripts.

Do not:
- use Literary OS generated scripts in the human baseline;
- use subtitles as a substitute for screenplay directions unless explicitly classified as a separate subtitle stratum;
- mix film and TV drama in the primary drama baseline;
- silently infer speaker/direction boundaries where the source format cannot support a reproducible parse.

Every included work must have:
- work identifier;
- episode identifier;
- source/provenance class;
- parser format class;
- parse-confidence flag.

## Primary strata

At minimum, if source availability permits:
- historical/period drama;
- workplace/professional drama;
- family/ensemble drama;
- crime/legal/mystery;
- romance/rom-com;
- medical/social-institutional drama.

Report pooled and per-stratum distributions.

## Frozen measurements

Per episode:
1. screenplay body characters;
2. dialogue characters;
3. direction/action characters;
4. dialogue share;
5. direction share;
6. dialogue turns;
7. mean/median utterance characters;
8. <=15-character turn share;
9. >=60-character turn share;
10. speaker count;
11. top-4 speaker dialogue share;
12. supporting-speaker dialogue share where historical speaker classifier is available;
13. exchange-run length distribution;
14. formal/polite/casual register markers as diagnostics only;
15. scene count where recoverable.

Per work and pooled:
- mean, median, P10, P25, P75, P90.

## Parser-validation gate

Before corpus-wide measurement:
- hand-audit >=30 episodes across >=6 format classes/works if available;
- speaker-vs-direction classification precision >=0.95 on audited lines;
- scene/heading lines excluded from both dialogue and direction;
- parenthetical actor direction attached consistently by frozen rule;
- parser version/hash sealed.

If parser confidence is insufficient for a source format, exclude that format from primary baseline and report it separately.

## PA8 Control diagnostic comparison

The already-measured Control diagnostic is:
- complete screenplay ~40,588 characters;
- dialogue ~12,618 characters;
- direction/action ~22,863 characters;
- dialogue share ~35.6% of dialogue+direction;
- 566 dialogue turns;
- median utterance ~19 characters;
- <=15-character turns 209.

These are **candidate diagnostics**, not human target values.

The primary human-corpus measurement must be completed before deciding whether 35.6% is below a formal Literary OS dialogue-share floor.

## No quota rule

Do not turn the human median into a hard generation quota automatically.

Any later generation gate must distinguish:
- dialogue quantity;
- dialogue naturalness;
- exposition;
- relationship/subtext function;
- dialogue-driven causal change.

Increasing dialogue characters by padding, repeated confirmation, or expository speeches is a failure, not an improvement.

## Relationship to UL17

UL17 qualifies upper architecture first.
The dialogue baseline is parallel evidence.

Only after current-R69 architecture qualifies should a full screenplay experiment test whether a Dialogue Realization intervention improves:
- spoken naturalness;
- voice separation;
- relational pressure;
- subtext;
- dialogue-driven state change;
while preserving architecture and continuity.

## Authority boundary

No runtime/package/Production/DB/Formal authority change.
