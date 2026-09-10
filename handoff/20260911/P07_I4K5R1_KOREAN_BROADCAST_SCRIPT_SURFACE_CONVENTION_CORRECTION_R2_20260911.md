# P07-I4K-5R1 Korean Broadcast-Script Surface Convention Correction R2

Date: 2026-09-11
Parent physical authority: `P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R19__I4K_RESEARCH_ARCHITECTURE_PROMOTED__I4K5R1_PREREG_SURFACE_REPAIR`
Parent material SHA256: `e8cef1a6431cc7618a898e5856a01f95fe2c856570f100e962dc31c74cf59575`
Experiment outputs before this correction: **0 fresh series / 0 events / 0 sequences / 0 scenes / 0 renders / 0 scores / 0 unblind**.

## Why this correction is needed
The I4K-5 diagnosis correctly identified repeated planning/meta prose and engine-token leakage, but the diagnostic discussion risked overgeneralizing that a long scene-opening direction block is itself a defect. Human broadcast-script conventions do not support that broad claim.

Korean drama-script practice commonly distinguishes:
1. **Scene-opening situation direction (씬 시작 상황지문)** — location/time/atmosphere, ongoing situation, performer state, blocking, props, environment and flow needed to understand the scene. This may be detailed and is not penalized merely for appearing before dialogue or for being long.
2. **Dialogue-adjacent performer cue (대사 인접 배우 지시)** — a concise emotional/behavioral/delivery cue placed close to the relevant line. It may use a parenthetical form or a short action line depending on the script style. Parenthetical formatting is allowed but is not mandatory for every emotional/action beat.
3. **Planning/meta explanation (계획·메타 설명문)** — internal objective labels, sequence-purpose prose, event/engine IDs, architecture rationale or repeated planning summaries that explain why the scene exists instead of presenting the scene. This is the true repair target.

## Corrected interpretation
- Detailed stage direction is explicitly allowed, including explicit actor emotion and action when useful for performance/directing.
- Scene-opening situation direction is a normal broadcast-script surface element and must not be removed merely to reduce prose density.
- Actor micro-direction should normally sit near the dialogue/action it modifies; parenthetical cue is one valid form, not the only valid form.
- Dialogue remains non-expository: do not make characters explain internal narrative architecture or emotions merely because the renderer removed planning prose.
- The repair must remove **planning/meta leakage and mechanical repetition**, not rich mise-en-scène or performance direction.
- No hard cap is placed on the percentage of episode characters occupied by legitimate scene-opening situation direction.
- The old diagnostic figure (~68% scene-entry preface share) is retained as a descriptive observation only. It is **not** a quality-failure gate by itself.

## What remains prohibited
- literal internal IDs/tokens such as `Event Ecology`, `CHxx`, `SQxx`, `thread`, `engine`, `planner`, Treatment/Control labels;
- verbatim or near-verbatim sequence-purpose paragraphs copied into multiple scenes;
- generic identical direction templates mechanically repeated across scenes/sequences;
- explanatory restatement of planning fields that is not necessary for production/performance understanding;
- dialogue that states architecture/control logic.

## What remains protected
- Event -> Sequence -> Scene -> Future causal adoption;
- character/relationship/world continuity;
- second-order decision ownership;
- future-thread ownership;
- detailed scene setting, atmosphere and playable stage direction;
- explicit performer emotion/action direction where dramatically useful;
- metadata-excluded screenplay body >=35,000 chars per arm.

## Scientific status
This is a **pre-output protocol clarification/correction**, not a post-result threshold change. It supersedes any interpretation of SurfaceHygieneContractR1 that treats scene-opening direction length or placement alone as a defect. I4K-5R1 remains prospective and unscored.

Status: `PRE_OUTPUT_CORRECTION_R2__SCENE_OPENING_DIRECTION_PROTECTED__PLANNING_META_REPETITION_REMAINS_REPAIR_TARGET__OUTPUTS_0`
