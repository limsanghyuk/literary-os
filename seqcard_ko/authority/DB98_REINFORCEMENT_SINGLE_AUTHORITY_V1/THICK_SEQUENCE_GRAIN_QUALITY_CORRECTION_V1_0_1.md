# DB98 Thick Sequence Grain Quality Correction V1.0.1

Document ID: `DB98_THICK_SEQUENCE_GRAIN_QUALITY_CORRECTION_V1_0_1`  
Parent: `DB98_THICK_SEQUENCE_AUTHORING_AUTHORITY_V1`  
Effective date: 2026-08-08  
Status: `ACTIVE_QUALITY_CORRECTION`

## 0. Reason

Independent ingest audit of `가을동화` found a structural-PASS / grain-HOLD failure: EP01 was authored at the intended semantic grain, while EP02–16 collapsed to minimum-threshold output despite all old light/strong/final validators passing. The failure was not proven factual inaccuracy; it was insufficient semantic depth and missing episode-to-episode carry-over.

This correction prevents block batching from reducing per-episode/per-sequence authorship quality.

## 1. Core rule

**Block is a management and strong-audit unit only. It is never a semantic compression unit.**

For an up-to-8-episode block, every episode must independently receive the same source-reading and semantic-authorship discipline as the accepted reference episode:

`FULL EPISODE SOURCE READ (4 consecutive quarters) → every human sequence reread → Thick authorship at full grain → episode light audit`.

Only after all episodes are individually authored may the block strong audit run.

## 2. Evidence/provenance floor

For every Thick semantic evidence reference, SOURCE refs must resolve to explicit source line ranges `:Lx-Ly` where the source format permits deterministic line addressing.

Every Thick record must carry the active complete six-key source hash set used by the accepted reference implementation:

- `baseline_artifact_sha256`
- `source_text_sha256`
- `scene_card_file_sha256`
- `sequence_blueprint_file_sha256`
- `episode_arc_file_sha256`
- `source_lock_sha256`

A sudden episode-boundary drop in either provenance measure is `G-GRAIN-PROVENANCE FAIL`, not a cosmetic warning.

## 3. Distribution gate — no minimum-threshold gaming

Schema minimum `functional_propositions >= 1` is not a quality pass by itself.

The validator must calculate per episode:

- mean functional propositions per scene;
- share of scenes with exactly one proposition;
- count/share of scenes with two or more propositions;
- event-length distribution as a drift signal, never as a target to pad.

Hard rule: **three consecutive episodes with >=90% of scenes at exactly one functional proposition = `G-GRAIN-DISTRIBUTION FAIL`.**

A sharp discontinuity from a verified reference episode/block in proposition distribution, event specificity, evidence density, or cast-function specificity triggers semantic review even when the hard threshold is not crossed.

Do not add meaningless propositions merely to raise the count. Depth must come from source-supported action, information, link/payoff, character function, or placement/handoff meaning.

## 4. Cross-episode thread rule

`thread_id` is a work-level semantic identity, not an episode-local payoff-candidate ID dump.

When source/CrossEpisodeEdge evidence establishes a continuing thread, its semantic `thread_id` must be reused across episodes from plant/escalation through callback/payoff. Do not force unrelated local moments into a shared thread merely to increase cross-episode counts.

Long-thread validation must report:

- number of semantic thread IDs spanning 2+ episodes;
- unresolved/open thread inventory at each planning boundary;
- missing plant/payoff directions;
- major work-engine threads explicitly (for `가을동화`, `birth_swap` is one such audit anchor).

## 5. R5 PlannerInput carry-over

R5 must carry actual planning-boundary state. `unresolved_payoffs`, `subplot_debt`, and `character_debt` may be empty in a specific episode when source-supported, but they must not be mechanically empty across a work that demonstrably contains unresolved long threads.

Future leakage remains forbidden. A completed-series CrossEpisodeEdge may be used privately to identify an earlier unresolved plant, but PlannerInput emitted for episode N must contain only facts/commitments available before N; it must not expose the later target episode, target scene, or later factual outcome.

## 6. Cast and semantic repetition

Within a sequence, two cast items may not share an identical `desire_or_function` merely because a generic sequence summary was copied to both. Character functions must be character-specific and source-supported.

Exact semantic duplicates and high-frequency boilerplate skeletons are review signals. Repeated schema phrasing is allowed only when functionally necessary and must not substitute for specific meaning.

## 7. R8 accounting

R8 `RuntimeSceneProjection` is a deterministic/derived consumer projection. It proves wiring but is **not an independent authored judgment layer** and must not be counted as separate semantic authorship quality.

## 8. Gaeuldonghwa repair gate and rollout pause

The original `가을동화` package is `INGESTED_GRAIN_HOLD`, not a completed work.

Repair acceptance requires:

1. EP01-quality provenance and grain restored to EP02–16;
2. two block strong audits (EP01–08 / EP09–16);
3. work-level semantic threads and R5 carry-over restored;
4. independent fresh-extraction validation;
5. one five-field ablation on the repaired work.

**No next work starts until item 5 is adjudicated.**

Any work authored before this correction but not independently checked against this grain gate is provisional and must not be counted as post-correction completed solely from its earlier structural/fresh-extract PASS.

## 9. Interpretation

The correction does not say the shallow records were factually false. It says structural validity and uniqueness did not prove the intended analysis grain. The quality target is:

**EP01-level semantic authorship × each episode; up to 8 episodes only as one management/audit block.**
