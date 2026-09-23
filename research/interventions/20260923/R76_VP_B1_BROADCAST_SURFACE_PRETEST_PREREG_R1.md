# R76-VP-B1 Virtual Provider Broadcast Surface Pretest — Preregistration R1

Date: 2026-09-23
Status: `PREREGISTERED__SURFACE_OUTPUTS_0`

## Parent evidence
- R76-R2A-R3 original frozen structural case: PASS, GitHub Actions run 35860614230
- R76-R2A-R3 fresh replication: PASS, GitHub Actions run 35860635840
- R2B evidence-derived transaction-role preservation: PASS on both cases
- Provider contract: Responses-API-like request/response/status/usage/request-id + 400/429/500 boundaries PASS

## Scientific boundary
This is a **Virtual Provider Surface Pretest**.
It is not an actual OpenAI API call and does not claim OpenAI-hosted latency, sampling, safety stack,
neural-weight, or exact provider quality equivalence.

The prose source for this pretest is the current ChatGPT GPT-5.6 Sol model operating in this research session.
The artifact is wrapped in a provider-analog receipt and evaluated as a candidate only.

## Frozen architecture
Use the R2A-R3 original R76 bundle layout:
- SQ01: CHAR01, EV01, INF01
- SQ02: CHAR02, INF02, INF04
- SQ03: INF03, INF06, INF07
- SQ04: INF05, INF08, PAY03
- SQ05: PAY01, REL01, REL02
- SQ06: PAY02, REL03, SOC02
- SQ07: SOC01, EV02
- SQ08: EV03, EV05, EV07
- SQ09: EV04, EV06, EV08

Each due obligation receives two scene contracts: pre-resolution advance + resolution.
Total: 52 scenes.
No scene may be cloned merely for quota.

## Surface requirements
- Korean broadcast screenplay
- >=35,000 characters
- exactly 9 frozen Sequences
- exactly 52 frozen Scenes
- no upper character cap
- dialogue should not explain emotion/state directly when action/stage direction can carry it
- stage direction may be detailed
- important state changes must be visible through action, expression/gaze, hand movement, prop transaction,
  blocking, silence/pause, failed action, approach/withdrawal, or other screen-visible behavior
- no internal schema labels, state_delta, transaction_stage, obligation IDs, evaluator tokens, or research metadata in screenplay prose
- no future episode source
- deferred long-horizon material must remain open

## Mechanical gates
B1 char_count >=35000
B2 sequence headings = 9
B3 scene headings = 52
B4 internal metadata leak = 0
B5 empty scene = 0
B6 every scene contains stage direction/action text
B7 dialogue is present in >=45 scenes
B8 frozen sequence/scene numbering monotonic
B9 no exact duplicated full scene bodies
B10 output hash + virtual provider receipt sealed

## Quality boundary
Mechanical PASS does not equal literary-quality PASS.
Required after candidate generation:
1. Whole-Episode Architecture blind review
2. pre-frozen early/middle/late Scene Surface-Craft blind review
3. Output-only reverse reconstruction
4. evidence-backed state extraction
Only after those may R76-VP-B1 be interpreted beyond a mechanical surface candidate.
