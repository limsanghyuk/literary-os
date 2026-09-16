# START HERE — SYNC-R53 POST-SESSION RESEARCH HANDOFF R1

Date: 2026-09-16
Classification: CANONICAL NEW-SESSION HANDOFF / HUB RESEARCH AUTHORITY / PHYSICAL BASELINE = SYNC-R53
Project: Literary OS Development

## 0. READ THIS FIRST

This document is the canonical handoff for the research state reached in the 2026-09-16 session.

### Physical custody baseline

The last developer-held complete 5-Part / 9-Package physical package set is:

`SYNC-R53`

Required read order:

`CONTROL -> A -> B1 -> B2 -> C1 -> C2-A -> C2-B -> D1 -> D2`

The developer explicitly identifies the following as the last physical delivery baseline:

1. CONTROL — SYNC-R53
2. Part A — SYNC-R53
3. Part B1 — byte-unchanged
4. Part B2 — SYNC-R53
5. Part C1 — SYNC-R53 Runtime
6. Part C2-A — SYNC-R53
7. Part C2-B — SYNC-R53
8. Part D1 — DB59 byte-unchanged
9. Part D2 — DB59 byte-unchanged

Changed at SYNC-R53: `CONTROL / A / B2 / C1 / C2-A / C2-B`.
Byte-unchanged at SYNC-R53: `B1 / D1 / D2`.

IMPORTANT: Do not downgrade the physical baseline back to SYNC-R52. Earlier Hub documents may describe R52 as the last physical authority because they predate the developer's later R53 delivery clarification. This handoff supersedes that historical custody statement prospectively.

### Physical package bytes vs Hub records

GitHub Hub records currently prove research state and authority metadata. They do NOT by themselves prove that all nine R53 ZIP/BIN payload bytes are archived in GitHub Releases or repository objects. Treat physical custody and Hub research authority as separate layers.

---

# 1. CURRENT AUTHORITY STACK

- Last developer-held complete physical package baseline: `SYNC-R53`
- Production Engine: `ENG:R47` (unchanged; no promotion performed in this session)
- Candidate Base Engine: `P07-I4H Recovery R3`
- DB Authority: `DB59` frozen
- DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- Formal scored total: `137`
- Latest Formal Authority: `R138`
- Formal R140: `0/0/0`
- Operational Level-3 Claim: `SUSPENDED`
- Level 4: `NOT STARTED`

R54/R55/R56 names were used during local candidate-physicalization attempts in the session, but because complete 9/9 developer delivery was not reliably preserved on the conversation download surface and the container later failed, they MUST NOT replace SYNC-R53 as the developer-held physical baseline.

Treat all post-R53 work below as `POST_R53_HUB_RESEARCH_AND_CANDIDATE_DEVELOPMENT` until a new complete 5-Part / 9-Package set is rebuilt, verified, delivered 9/9, and archived with physical-asset evidence.

---

# 2. SESSION RESEARCH LINEAGE AFTER SYNC-R53

The session continued upper-layer Candidate Engine research rather than promoting ENG:R47.

## 2.1 UL-11 — Blind Continuation Integrity & Isolation Gate

Purpose:
prove that a continuation experiment is not contaminated by target leakage, sibling-candidate sharing, arm sharing, or hidden-target access.

Key findings:

1. Published human dramas cannot be treated as strong hidden-target evidence merely because the target file is unopened; model pretraining memorization remains possible.
2. Hidden-file status is not equivalent to hidden-from-model-weights status.
3. Candidate A/B/C/D must use genuinely fresh isolated provider contexts in a formal/live run.
4. FULL-history and RECENT5 ablation arms must also be isolated from each other.
5. Human target opening must occur only after candidate generation, portfolio, evaluation and selector freeze.
6. Public-work research should include a preregistered `Counterfactual Divergence Arm` so state consumption can be distinguished from memorized canonical continuation.

UL-11 executable failure-injection result reported in-session: `24/24 PASS`.

## 2.2 UL-12 — Fresh-Context Provider Qualification Runner

Purpose:
make the future OpenAI Responses API execution path stateless and auditable.

Key design:

- `conversation` forbidden for qualification runs.
- `previous_response_id` forbidden for qualification runs.
- Each provider call uses a unique `execution_nonce`.
- One Candidate's six-stage chain uses a stable `chain_id`.
- Parent outputs are explicitly passed and hash-bound instead of relying on hidden provider conversation state.
- Actual LIVE qualification requires real provider receipts; virtual receipts can never be promoted to LIVE evidence.

Critical bug found and repaired during implementation:

Initial design accidentally required the same `execution_nonce` across all six stages while also requiring every API call nonce to be unique. This was contradictory.

Repair:

- `chain_id`: stable across the six stages of one Candidate.
- `execution_nonce`: unique per provider request.

UL-12 executable failure-injection result reported in-session: `24/24 PASS`.

## 2.3 UL-13 — End-to-End Hierarchical Surface Qualification

Purpose:
measure whether upper-layer episode architecture survives all the way through Sequence Plan -> Scene Plan -> full screenplay surface, instead of only looking good in planning artifacts.

Core evaluation stack:

1. Episode Synopsis quality and episode-function completeness.
2. Sequence-to-sequence weaving and dramatic transactions.
3. Scene Plan necessity and parent-plan consumption.
4. Surface realization of the planned state changes.
5. Reverse reconstruction: judges read Surface first and infer the hidden upper architecture, then plans are revealed and plan-to-surface fidelity is evaluated.

Pilot correction:

An early UL-13 pilot had only 16 sentinel surfaces despite complete 46/50-scene plans. That was insufficient for a whole-episode claim. The research was extended to full-episode surfaces.

Reported full surfaces:

- Candidate/Treatment: 46 scenes / 38,277 Korean characters
- Flat Control: 50 scenes / 35,277 Korean characters

Same fixed renderer was used for both arms so the comparison targeted architecture rather than renderer quality.

Important renderer bug found and repaired:

The third automatically selected participant could duplicate participant one/two, leaving only two distinct participants. The renderer was repaired to guarantee distinct participant selection where the scene contract required it.

Reported mechanistic differences:

- Obligation nominal coverage: 100% in BOTH arms.
- Candidate concrete Scene State Delta: 100%.
- Control concrete Scene State Delta: 0% under the frozen internal metric.
- Candidate Scene necessity explicit: 100%.
- Control Scene necessity explicit: 0% under the frozen internal metric.
- Candidate generic sequence transaction: 0/8.
- Control generic sequence transaction: 10/10.
- Candidate parallel-lane sequence: 0/8.
- Control parallel-lane sequence: 10/10.
- Candidate cross-owner weaving: 10/12 = 83.3%.
- Control cross-owner weaving: 4/8 = 50%.
- Candidate sequence lengths: variable (4–8 scenes), CV about 0.242.
- Control sequence lengths: exactly 5 each, CV 0.000.

Research conclusion:
`Obligation Coverage` alone does not measure episode dramaturgy. Both arms can include the same obligations, while only one makes those obligations causally or functionally alter later choices and states.

## 2.4 UL-13 external blind-evaluation protocol

Two-stage external evaluation was prepared:

Stage 1:
- judge sees Surface only;
- reconstructs episode function, central question, plot owners, major causal/functional weaving, relationship/state movement, closure/open debt.

Stage 2:
- only after Stage-1 response is sealed, reveal Synopsis / Sequence Plan / Scene Plan;
- evaluate whether the planned architecture is actually legible in the screenplay and whether plan-to-surface fidelity holds.

A first packet was invalidated before use because arm-identifying strings remained inside the packet (`TREATMENT`, `CONTROL`, `R55`, `LEGACY`, and arm-specific IDs).

Repair:
- neutral A/B remapping;
- Sequence/Scene IDs neutralized;
- leakage-string audit required before release;
- 4 judges x 2 stages = 8 packets;
- A/B assignment balanced 2:2.

External judge responses at the session boundary: `0`.

Do NOT claim external literary-quality PASS yet.

## 2.5 Surface craft boundary remains binding

When future provider-generated screenplay surface is evaluated, preserve the project's craft doctrine:

- Dialogue must not explain plot/state/psychology.
- Exposition and performance direction belong in direction when needed.
- Emotion should be visible through facial-expression shifts, hand/prop behavior, movement, seating, hesitation, failed action, silence, timing and choice rather than direct explanatory dialogue.
- Detailed direction is allowed.
- Minimum episode scale is 35,000 Korean characters; no maximum.
- 9–10 sequences / 45–50 scenes are reference/minimum scale, never fixed generation quotas.

---

# 3. IMPORTANT PRE-UL-11 RESEARCH THAT REMAINS ACTIVE

The following post-R53 research lineage remains part of the Candidate research state and must be preserved:

- UL-1/UL-2 Upper-Layer Foundation and DB64 prior analysis.
- UL-3 Main-Path Consumption Receipt.
- UL-4 Multi-Position Continuation preregistration.
- UL-5 Counterfactual Portfolio + Selector/Abstention.
- UL-6 Narrative Weaving Graph, later broadened from causal-only to allow justified functional/thematic weaving.
- UL-7 Responsible-Ancestor Replan.
- UL-8 Forward/Reverse Architecture Closure.
- UL-9 Long-Horizon State Consumption preregistration.
- UL-10 Integrated Upper-Layer Qualification Harness.

Key lessons from the virtual Provider Analog experiments:

1. Fixed 10-sequence / 50-scene templates are not allowed as generation targets.
2. Architecture should emerge from narrative obligation and dramatic need.
3. Direct causal weaving is not the only legitimate weaving; functional/thematic weaving is allowed when removal would materially weaken episode function or durable-debt progression.
4. Finale/late-series architecture needs `Terminal Closure Ledger` / narrative-obligation accounting rather than fixed sequence quotas.
5. DB64 `runtime_safe` records were found to contain some future payoff/closure references. A `Cutoff-Safe State Projection` layer was introduced to strip future references before blind continuation use.
6. Same-session ChatGPT analogs cannot prove clean candidate independence or FULL-vs-RECENT5 context ablation; formal claims require fresh isolated provider contexts.
7. Famous/public target episodes remain vulnerable to pretraining memorization; use counterfactual divergence and memorization-risk controls.
8. A research module passing in isolation is insufficient; it must be consumed by the actual Candidate Main Path and final hashes must bind to final post-replan artifacts.

---

# 4. LOCAL CANDIDATE-PHYSICALIZATION ATTEMPTS R54–R56

During the session, candidate-physicalization builds named R54, R55 and R56 were produced and locally tested in the working environment.

Reported local validation included:

- R54 Candidate Overlay regression: 33/33 PASS.
- R55 Candidate Overlay regression: 57/57 PASS.
- R56 Candidate Overlay regression: 67/67 PASS.
- Production Runtime Source was intended to remain byte-unchanged.
- Narrative Engine Master and DB59 were reported as unchanged/reconstructable.

However, the session later discovered a critical custody/delivery problem:

- not every large R56 file was actually registered on the conversation download surface;
- R56 Part B2 was specifically missing from the user-visible file surface;
- later the container began failing even on minimal I/O with `TransportTimeoutError`;
- therefore R56 could not be safely reconstituted/re-delivered before the session boundary.

One additional metadata defect was found during R56 preparation:
R55 C1/C2 `PART_MANIFEST` metadata still referenced an older R54 authority/overlay even though the payload had evolved. The repair was planned/applied prospectively in R56, but because R56 was not conclusively delivered 9/9, R53 remains the physical baseline.

Rule for the next session:
Do not treat locally named R54/R55/R56 as developer-held physical authority. They are research/development evidence only until rebuilt from the R53 baseline and delivered/archived under the new physical-custody gate described below.

---

# 5. NEW PHYSICAL-CUSTODY GATE — REQUIRED BEFORE NEXT SYNC PROMOTION

The session exposed that `container file exists` and `developer can download file` are different states.

Every future 5-Part / 9-Package promotion must satisfy ALL of the following:

1. Build PASS.
2. ZIP CRC / binary integrity PASS.
3. Per-package SHA256 PASS.
4. C2-A + C2-B reconstruction PASS.
5. Candidate C1/C2 overlay byte-identity PASS where applicable.
6. B1/D1/D2 unchanged-claim verification PASS where applicable.
7. Narrative Engine Master reconstruction against canonical SHA PASS.
8. DB59 reconstruction against canonical SHA PASS.
9. Conversation/File-surface attachment existence audit: `9/9`.
10. User-visible download-surface audit: `9/9`.
11. Hub Physical Package Manifest written with filename, size, SHA256, custody status and archive locator.
12. Prefer durable GitHub Release/Artifact storage or another approved large-asset archive so a future container failure does not destroy recoverability.

Only after all twelve should a new `SYNC-Rxx__DEVELOPER_DELIVERY_COMPLETE__9_OF_9` be declared.

---

# 6. HUB / PHYSICAL STORAGE STATUS AT HANDOFF

GitHub Hub currently contains research and handoff records and older release assets, but this session did not verify a complete archived R53 9-package byte set in GitHub Releases.

Therefore distinguish:

- `SYNC-R53`: last developer-held physical baseline.
- GitHub Hub: research / authority / handoff records.
- Complete R53 bytes archived in Hub: NOT PROVEN in this session.

A future recovery task should archive the full R53 baseline or the next rebuilt successor into a durable package archive and bind the archive to a Physical Package Manifest.

---

# 7. EXACT NEXT RESEARCH / EXECUTION BOUNDARY

The next session should NOT invent another upper-layer theory first.

Priority order:

## P0 — Recover physical build environment

Confirm container/runtime I/O health before large-package work.

## P1 — Recover/rebuild from SYNC-R53 physical baseline

Use the developer-held R53 package set as the physical root.
Do not use R52 as the baseline.

## P2 — Reapply post-R53 Candidate research overlay

Reintegrate the validated UL-11 / UL-12 / UL-13 gates plus earlier UL-1..UL-10 research into the Candidate Runtime in a clean build.

## P3 — Build next physical candidate authority

Use a NEW SYNC number. Do not retroactively mutate R54/R55/R56 history.

The new set must pass the 12-step Physical-Custody Gate above and be delivered/archived 9/9.

## P4 — External UL-13 blind evaluation

Run Stage 1 Surface-only blind evaluation first.
Seal responses.
Then run Stage 2 plan reveal.
Do not reveal mapping early.
Do not claim external PASS until results exist.

## P5 — Actual OpenAI Provider qualification

Once a safe runtime is available, run the Candidate through fresh isolated OpenAI Responses API contexts.

For qualification:
- no `conversation` reuse;
- no `previous_response_id` reuse;
- unique provider request / execution nonce per call;
- stable candidate chain id;
- real response id / request id / model / usage receipts;
- sibling candidates isolated;
- FULL/RECENT5 arms isolated;
- hidden target unopened until selector freeze;
- counterfactual divergence for public works;
- no API key pasted into ChatGPT.

## P6 — End-to-end provider replication

Repeat the UL-13 methodology with actual provider-generated full episode surfaces >=35,000 chars:

`Series/Episode state -> Episode Synopsis -> Sequence Plan -> Scene Plan -> full Surface -> reverse reconstruction -> blind external evaluation`

Only after this can the project credibly evaluate whether the Candidate Engine's improved upper architecture is visible at the screenplay surface under real Provider conditions.

---

# 8. PRODUCTION PROMOTION RULE

Do NOT replace ENG:R47 merely because post-R53 Candidate research exists.

Production promotion requires, at minimum:

1. fresh-context LIVE Provider receipts;
2. multi-position continuation evidence;
3. Candidate independence / leakage gates;
4. external blind evaluation;
5. end-to-end plan-to-surface preservation;
6. State Carry / regression safety;
7. complete physical package reseal and custody 9/9;
8. explicit new Production ENG authority that supersedes ENG:R47.

Until then:

`PRODUCTION_ENGINE = ENG:R47`

---

# 9. CLAIM BOUNDARIES

Allowed claims:

- Candidate upper-layer architecture research materially advanced after R53.
- Virtual analogs found and repaired multiple contract, isolation, weaving, closure, leakage and surface-qualification defects.
- UL-13 established a method to judge whole-episode architecture from the final screenplay surface, not just plans.
- A complete new physical successor to R53 still needs clean rebuild + 9/9 custody verification.

Disallowed claims:

- Do not say R54/R55/R56 replaced R53 as developer-held physical authority.
- Do not say the current Candidate has been promoted to Production.
- Do not say Live OpenAI Provider qualification has already passed.
- Do not say external UL-13 blind evaluation has passed; responses were 0 at handoff.
- Do not say GitHub currently archives all nine R53 payload bytes unless independently verified.

---

# 10. NEW-SESSION START COMMAND

A new session should begin by reading this document first, then verify the current Hub pointers and the developer-supplied SYNC-R53 physical packages.

Recommended first operational statement:

`Recovered: Physical baseline SYNC-R53; post-R53 Hub research includes UL-11/12/13 and prior UL-1..10 lineage; Production ENG:R47 unchanged; next step is clean physical rebuild with custody 9/9, then external UL-13 blind evaluation / real fresh-context Provider qualification.`

Do not ask the developer to repeat research already recorded here unless a required physical file is genuinely unavailable.
