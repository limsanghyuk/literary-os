# P07-I4I Blind Score Seal R1

Date: 2026-09-09
Experiment: `P07-I4I-WHOLE-EPISODE-PAIRED-RERENDER-R1`

Valid blind map R3 SHA256:
`7108578ae345390698750729fccf22c66e21056ebe602e1903ec7f7b5a438e82`.

The mapping remained unopened during scoring.

Evaluation classification:
`MASKED_SAME_AGENT__DEVELOPMENT_PREFORMAL__POLICY_BLINDNESS_NOT_INDEPENDENTLY_PROVABLE`.

Blind score artifact SHA256:
`539b4b44bc2ab5db5aea77bb2979866ee363153812228b266786a1643137410f`.

Episode-level sealed scores before unblinding:
- A mean: `8.075`
- B mean: `8.358333333333333`
- B - A: `+0.2833333333333338`
- B nonloss axes vs A: `12/12`
- maximum B axis regression: `0.0`
- critical failures observed: `0`

Scene-stratified diagnostics for the 24 differing scenes are included in the sealed local artifact and were scored before opening the map.

Method boundary: the A/B mapping was masked, but a single agent performed earlier selector/treatment work; therefore strict policy-blind independence is not established. These scores are Development/Preformal evidence only, not independent-human or OpenAI-Live evidence.

Status: `BLIND_SCORES_SEALED__MAP_UNOPENED`.
