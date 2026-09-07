# Current Candidate vs Target Literary Narrative Operating Engine — Architecture / Gap / Virtual Run R1
Date: 2026-09-07
Classification: DEVELOPMENT MAP / NONFORMAL / NO FORMAL COUNT DELTA

## 0. Purpose
Cross-compare the current Literary OS Candidate Engine with the target Literary Narrative Operating Engine and record a fresh local virtual-environment execution. This document does not promote RFV3, CP1 Live, R-F, R-G, or R140.

## 1. Target operating principle
The target system must structurally understand why completed dramas were designed as they were, retrieve the most relevant craft knowledge for the current story-state and planning question, transform that knowledge into a new narrative, and feed diagnosed lower-layer failures back to the minimum responsible upper layer.

Canonical target loop:
`Current Narrative State -> Planning Question Router -> Narrative Knowledge Bus -> Multi-view Retrieval -> Narrative Architecture Packet -> Series/Episode/Ensemble/Sequence/Scene Planning -> Surface Realization -> Diagnostics -> Responsible-Ancestor Replan -> Re-lowering -> State Commit/Carry`.

## 2. Current physical and working state boundary
- Current physical authority: `CURRENT_PHYSICAL_AUTHORITY__P07A_RFV2_CONTROLLED_RECOVERY_R1`.
- Current physical C2 reconstructed SHA256: `1a9355169650d66af0a3f44fb867bad1c00e5dc643e8f28443d1b2f6c6cde62d`.
- Latest P07-B working state additionally found and repaired `retrieve_many()` vs `retrieve()` donor-selection drift, with 186/186 regression PASS, but this latest P07-B repair still requires 9-package reseal before becoming physical authority.
- Formal scored count remains 137; latest formal scored authority R138; R140 remains 0 attempts / 0 outputs / 0 scores.

## 3. Current candidate architecture inventory
### 3.1 Strong/implemented modules
- `series_architecture.py`: multi-axis series architecture, thread windows, episode-function bands, optional writer-room whole-series architecture.
- `series_episode_allocation.py`: series-to-episode allocation.
- `detailed_episode_synopsis.py` / `episode_architecture.py`: episode synopsis/architecture.
- `planning_spine.py`: Character+Relationship+Thread state core, caller-supplied Social Ecology graph, event ownership propagation, macro episode allocation.
- `candidate_portfolio.py` + `selector.py`: ecology-aware candidate portfolio, safety gate, selection/commit.
- `rfv2_retrieval.py`: DB59 THICK event/info/payoff retrieval with work-level TF-IDF/cosine and fail-close low-confidence abstention.
- `semantic_orchestration.py`: provider-backed Series -> Allocation -> Episode -> Retrieval -> Sequence -> Scene semantic hierarchy with receipt chain and semantic contracts.
- `semantic_render_bridge.py` / `provider_backed_renderer.py`: semantic scene -> ordered-beat renderer contract -> provider-backed surface realization.
- `bidirectional_refinement.py`: lower-layer diagnostic -> minimum responsible ancestor routing and LLM replan request.
- `state_replanning_integrity.py`: continuous-state integrity, semantic deltas, canonical-state commit/carry.
- `long_horizon_authoring.py`: multi-episode carry, thread economy, ensemble persistence, closure and cross-work guards.
- `surface_craft_closure.py`: voice/repetition/subtext/physicalization metrology.
- Evidence/receipt/fail-close infrastructure is substantial.

### 3.2 Important modules that exist but are not one continuous main path
1. `semantic_orchestration.STAGES` currently executes:
   `SERIES_PLAN -> EPISODE_ALLOCATION -> EPISODE_PLAN -> SEQUENCE_PLAN -> SCENE_PLAN`.
2. `ENSEMBLE_ECOLOGY_PLAN` has a strict schema and research policy but is not included in `STAGES` and is not called by the current verified main path.
3. `planning_spine.build_social_ecology_graph()` builds ecology only from caller-supplied `narrative_config.groups`; it does not derive ecology from DB59 CharacterArc/RelationshipArc/CastPresence/CharacterLoad/THICK.
4. CandidatePortfolio/Selector/RepairRouting/StateCommit have a working local closed-loop test, but that loop is separate from the provider-backed hierarchical semantic planning path.
5. BidirectionalRefinement exists, including `ENSEMBLE_ECOLOGY_PLAN` routing, but is not automatically invoked after renderer/sequence/episode diagnostics in the main path.
6. Writer-room Series Architecture is present as an optional structural candidate, not the default source-of-truth path.
7. Long-horizon guards exist but the fresh provider-backed single-episode path does not automatically execute a full multi-episode authoring/commit loop.

## 4. Database crosswalk
### 4.1 DB knowledge already available
The reverse-engineered corpus contains strong structural layers: SceneCard, SequenceBlueprint, EpisodeArc, CharacterArc, RelationshipArc, CrossEpisodeEdge, PayoffCandidate, THICK Sequence; R5 PlannerInput and R8 RuntimeSceneProjection exist as execution contracts; EXT6 has useful Entity/CharacterLoad/CastPresence families where available.

### 4.2 What current RFV2 actually retrieves
Current RFV2 literary profile is intentionally bounded to:
- `event`
- `info_shift(mode/before/after)`
- `plant_payoff(kind/statement)`

It does not yet use CharacterArc, RelationshipArc, THICK cast/participation, ThreadState, CharacterLoad, CastPresence, Episode-axis ownership, or derived Social Ecology in the active retrieval profile.

### 4.3 Resulting gap
`FUNCTIONAL_EVENT_DB_RETRIEVAL = CONNECTED`
while
`FULL_NARRATIVE_ARCHITECTURE_DB_CONSUMPTION = OPEN`.

This is the current highest-priority architecture gap.

## 5. Current-vs-target map
| Target function | Current status | Gap / action |
|---|---|---|
| Source-safe state kernel | PARTIAL-STRONG | R5/state modules exist; unify current runtime state with DB-derived Character/Relationship/Thread state |
| Whole-series architecture | PARTIAL-STRONG | multi-axis + writer-room architecture exist; choose one canonical main-path contract |
| Episode allocation | STRONG | connect ownership/ecology evidence rather than caller-only priors |
| Detailed episode synopsis | STRONG/PARTIAL | make it consume Narrative Architecture Packet rather than only upstream provider output |
| Social ecology | SCHEMA+MODULE, NOT DB-WIRED | derive evidence view from DB; insert `ENSEMBLE_ECOLOGY_PLAN` between Episode and Sequence |
| Event/plot ownership | MODULE, CALLER-SUPPLIED | ground owner/counterparty/consequence in DB/current state evidence |
| Character/relationship retrieval | DATA EXISTS, MAIN RETRIEVAL MISSING | create dedicated Character/Relationship retrieval views |
| Thread/payoff retrieval | PARTIAL | integrate ThreadState/CrossEpisodeEdge/R5 open-thread state with RFV2 |
| Multi-view retrieval router | MISSING | add Planning Question Router + view-specific retrieval |
| Narrative Architecture Packet | MISSING | normalize selected evidence/constraints/provenance for provider stages |
| Candidate portfolio/selector | IMPLEMENTED, SEPARATE | integrate before episode/sequence commitment |
| Sequence/scene lowering | STRONG | already contract-checked; add ecology/relationship payloads |
| Surface provider path | STRONG MECHANICS, LIVE OPEN | local/test-double path works; CP1 current-authority Live still open |
| Bidirectional refinement | ROUTER IMPLEMENTED, NOT CLOSED LOOP | invoke diagnostics automatically and re-run minimum responsible ancestor |
| State commit/carry | IMPLEMENTED, SEPARATE | integrate after accepted episode render and before next episode |
| Physical persistence | DOCTRINE FIXED | every meaningful code/science unit must reseal 5 Parts/9 Packages before next stage |

## 6. Fresh virtual-environment execution
### 6.1 Current-code local mechanics
`tools/local_end_to_end_mechanics.py` freshly executed PASS.
Path:
`SERIES_PLAN -> EPISODE_ALLOCATION -> EPISODE_PLAN -> FUNCTIONAL_RETRIEVAL -> SEQUENCE_PLAN -> SCENE_PLAN -> SEMANTIC_RENDER_BRIDGE -> SCRIPTED_RENDERER -> SCRIPTED_INDEPENDENT_JUDGE`.
The same run correctly blocks Live evidence eligibility because Scripted providers have no trusted provider receipt.

`tools/local_closed_loop_mechanics.py` freshly executed PASS.
Path:
`CANDIDATE_PORTFOLIO -> SAFETY_GATE -> SELECTOR_COMMIT -> REPAIR_ROUTING_SENTINEL -> CONTINUOUS_STATE_INTEGRITY -> CIG -> CANONICAL_STATE_COMMIT -> STATE_HASH_CARRY`.

Important finding: both mechanics are individually alive, but they are not yet one integrated authoring loop.

### 6.2 Fresh synthetic drama probe
Original development probe: an 8-episode urban-redevelopment/government-audit ensemble drama. EP02 requires city-audit team, tenant coalition, and family-company pressures to collide.

Current DB59 RFV2 query result:
- decision: `NO_RETRIEVAL`
- confidence: `0.09519044` (LOW; threshold 0.10)
- fit margin: `0.00506539` (diagnostic only)
- top works: 수호천사 0.09519044; 불한당 0.09012505; 스위치 0.08826774; 스카이캐슬 0.08629261.

Interpretation:
- positive: engine correctly abstains instead of injecting weak donor evidence;
- negative: event/info/payoff-only RFV2 cannot exploit DB59's richer Character/Relationship/Ensemble data for a new social-ecology question.

The same fresh episode was passed through current verified semantic orchestration with ScriptedSemanticProvider (development surrogate):
- planning status PASS
- retrieval `NO_RETRIEVAL`
- Episode->Sequence semantic contract ACCEPT
- Sequence->Scene contracts ACCEPT for SQ1/SQ2/SQ3
- structure PASS: 3 sequences / 6 scenes
- provider/test-double only; no Live evidence claim.

### 6.3 Surface diagnostic
Two surfaces were tested from the same scene contracts.

A. Historical Python Template Fallback, executed from current code:
- generated text contains mechanical lexical stitching such as `서진·파쇄`, `영수증·분리한다`, awkward Korean, and templated subtext.
- conclusion: the Python fallback is a mechanics/fallback fixture, not a literary-quality renderer.

B. In-session LLM surrogate outputs passed through current `semantic_render_bridge` + `provider_backed_renderer` contract:
- 6/6 scenes COMMIT under local contract guard;
- ordered beats preserved;
- unauthorized speakers 0;
- exit-state mismatches 0;
- no Live Provider receipt, therefore development diagnostic only.

Representative surrogate excerpt:
```
씬 S03 — 구청 후문 앞 자판기 / 밤
한도윤: 어제 네 시 십칠 분.
윤서진: 뭐가.
도윤이 종이에 ‘16:17’만 적어 자판기 위에 놓는다.
한도윤: 그 시간에 누가 구청 들어왔는지, 정말 몰라?
윤서진: 알고 있으면 화면부터 보여 줘.
한도윤: 화면 보여 주면 사람 하나 잘려.
서진이 종이를 집어 접지 않고 그대로 돌려놓는다.
윤서진: 우리 아버지 회사, 왔어.
한도윤: 그걸 왜 내가 먼저 알아야 하지?
```

Interpretation: semantic contracts can support playable scenes when an LLM supplies surface craft, but the current local engine does not itself create strong Korean dramatic prose without a provider.

## 7. Revised target architecture
```
SOURCE / ORIGINAL BRIEF
  -> Narrative State Kernel
  -> Series / Writer-Room Architecture
  -> Episode Allocation
  -> Episode Plan
  -> Planning Question Router
       -> Macro Retrieval View
       -> Character State View
       -> Relationship State View
       -> Ensemble / Social Ecology View
       -> Thread / Payoff / Information View
       -> Sequence Function View
       -> Negative / Mismatch View
  -> Narrative Architecture Packet (provenance-bound)
  -> ENSEMBLE_ECOLOGY_PLAN
  -> Candidate Portfolio
  -> Safety / Critic / Selector Commit
  -> Sequence Plan
  -> Scene Plan
  -> Provider-backed Surface Realization
  -> Craft / Continuity / Ecology / Thread Diagnostics
  -> Bidirectional Responsible-Ancestor Router
       -> minimum-stage LLM replan
       -> re-lowering
  -> CIG / Canonical State Commit
  -> carry to next episode
```

## 8. Next engineering/scientific order
1. Physically reseal the already-passed P07-B canonical retrieval parity repair into 5 Parts/9 Packages.
2. Build a `Schema x Consumer x Coverage x Provenance` matrix over DB59.
3. Implement `PlanningQuestionRouter` and `NarrativeArchitecturePacket`.
4. Implement multi-view DB adapters beginning with existing CharacterArc, RelationshipArc, THICK cast/participation, R5 state, ThreadState/CrossEpisodeEdge; do not invent missing facts.
5. Build `SocialEcologyEvidenceView` as a derived, provenance-bound view; UNKNOWN when evidence is insufficient.
6. Insert `ENSEMBLE_ECOLOGY_PLAN` into the verified semantic main path between Episode Plan and Sequence Plan.
7. Integrate CandidatePortfolio/Selector before sequence commitment.
8. Integrate diagnostic -> BidirectionalRefinement -> replan -> re-lowering into the same path.
9. Integrate accepted episode -> CIG -> canonical state commit -> next-episode carry.
10. Run P07-B2 mechanical adoption pretest with selected/unselected mutation for Character/Relationship/Ensemble/Thread views.
11. Reseal 5 Parts/9 Packages.
12. Run a small causal craft pretest: event-only retrieval vs +character/relationship vs +ensemble/ecology vs +thread/payoff.
13. Supersede RFV3 R1 before outputs if needed; recommended clean arms: A Summary-only, B Pre-repair/no retrieval, C Functional retrieval, D Full Narrative Architecture DB consumption, E D + Bidirectional Refinement.
14. Only after this: CP1 current-authority integration -> official R-F paired Live -> R-G freeze -> Formal R140.

## 9. Current position statement
The project is no longer at the stage of proving that individual modules can exist. It is at the integration stage where already-proven research components must become one provenance-bound, DB-grounded, provider-backed, bidirectionally refinable narrative operating loop.

The immediate bottleneck is not raw database size and not sequence/scene schema absence. It is the `NARRATIVE_ARCHITECTURE_DB_CONSUMPTION_AND_MAIN_PATH_INTEGRATION_GAP`.
