# P07-I4E R2 Speaker-Authorized Surgical Recovery — Preregistration R1

Date: 2026-09-08
Classification: DEVELOPMENT / PREFORMAL / NO FORMAL COUNT DELTA
Parent physical authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`
Parent Package Set SHA256: `5d385069962b0f40d63ee8256729f4e66aae9a7cf57099dd9d786bc01bc74dae`
Parent C2 SHA256: `1022a4144e582069a3d6ed9d234f100d0b8a3a4323b73039d1454e57f89d75e1`
R1 HOLD result commit: `0ac611af274cd57029454c98cfffc384eb957406`
Frozen R1 final treatment SHA256: `1228b2cd1c389706042b389c40ffb99212b6c2893a2de4a375ac23559a432a82`
Frozen R1 final length: 50 scenes / 35,018 Unicode chars.
Frozen DB59 SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
Formal scored count: 137. R140: 0/0/0 HARD BLOCK.

## 1. Purpose
Recover only the specific whole-episode acceptance defect found in I4E R1: direct-speaking principal characters escaped the frozen per-scene `LiterarySurfaceContractR1` speaker scope. R2 must add a fail-closed speaker-authorization boundary and surgically regenerate only the failed scenes without changing the already-sealed 45 protected scenes.

This is not an opportunity to improve blind scores, rewrite other scenes, change modes, alter semantics, or lower any threshold.

## 2. Frozen affected scenes
Exactly five scenes may change:
`S37, S46, S47, S48, S49`.

All other 45 scenes must remain exact-byte identical to the R1 final treatment.

Frozen mode-selection map remains unchanged, SHA256 `21307a4ef5974c80e799349ac915f124c7fc500b4cb95067ff82ce337cd8b574`.
Frozen semantic contracts remain unchanged.

## 3. Speaker Authorization Guard
Before accepting any generated scene, runtime must derive `allowed_direct_principal_speakers` exclusively from that scene's consumed `LiterarySurfaceContractR1.character_play_state` keys.

The full episode principal-cast universe is the union of the 50 contract principal keys, excluding declared local functional roles such as `옆직원`.

Output acceptance rule:
- if a line with direct speaker label belongs to the principal-cast universe but is not in the scene's allowed principal set => `HOLD__UNAUTHORIZED_PRINCIPAL_SPEAKER`;
- local functional roles may speak when they do not introduce a new principal identity or new unsupported world fact;
- the guard must run after provider text returns but before the scene is accepted into the episode assembly;
- rejected output must not enter State Commit or downstream blind packets.

Renderer/provider packet must also carry the allowed principal list so the model receives the constraint before generation.

## 4. Pre-output proof
Before new prose is generated:
- focused guard tests PASS;
- R1 failed versions of S37/S46/S47/S48/S49 are each rejected by the guard;
- representative protected scenes are accepted;
- exact-byte repair assembler test proves replacing one scene changes only that scene's byte span and no sibling whitespace/line endings.

If any pre-output proof fails, R2 stops before prose generation.

## 5. Generation boundary
Only the five failed scenes may be freshly authored with `IN_SESSION_LLM_SURROGATE__NONLIVE`.
`LiterarySurfaceContractR1` and previously sealed `SurfaceRealizationModeR1` payloads are consumed unchanged.
Human-anchor text remains forbidden before treatment sealing and Stage A PASS.
Python/runtime authors zero literary prose.

## 6. R2 mechanical gates
Final reconstructed episode must satisfy all I4E R1 whole-episode gates unchanged:
- 50 scenes;
- 35,000-45,000 chars;
- unauthorized principal speakers 0;
- contract completeness 50/50;
- critical semantic/continuity violations 0;
- source/future leakage 0;
- exact long-dialogue/narrative duplicate ratios <=0.05;
- forbidden meta leakage 0;
- procedural/control density <=12 / 1,000 chars;
- mean non-empty line length <=45;
- protagonist scene share <=0.65;
- protagonist-group ownership <=0.60;
- non-protagonist-owned sequences >=4;
- independent non-protagonist owner groups >=2;
- 45 protected scenes exact-byte identical to R1 final.

No additional repair cycle is allowed inside R2 after the five surgical scenes are sealed. If any gate fails, R2 HOLD.

## 7. Stage A
Only after final R2 treatment sealing and mechanical PASS, compare fixed 12 scene IDs:
`S03, S07, S11, S14, S19, S21, S28, S33, S37, S41, S45, S50`
against exact I4C-R2 research control.

PASS threshold unchanged:
- Treatment wins >=9/12;
- losses <=3/12;
- zero critical semantic/continuity violations.

## 8. Stage B fresh-human
Only after Stage A PASS, select fresh DB59 human anchors. Do not knowingly reuse exact I4B/I4C/I4D passages where feasible.

Whole-episode human-competitive development signal requires BOTH unchanged I4C thresholds:
- Candidate wins >=3/12;
- Candidate wins + ties >=6/12;
- zero critical semantic/continuity violations.

If failed: `HOLD__MODE_DRIVEN_WHOLE_EPISODE_NOT_HUMAN_COMPETITIVE__NO_LIVE_PROMOTION`.

## 9. State / regression / promotion
Only after all gates pass:
- bind final surface to unchanged canonical semantic carry unless an explicitly justified semantic change occurred;
- State Commit/Carry PASS;
- focused guard/assembler tests + full nonhistorical regression PASS;
- exact final packaged-C2 fresh-materialization regression exit code 0;
- physically reseal 5 Parts / 9 Packages with unchanged packages byte-identical and full CRC/duplicate/unsafe/nested/secret/cross-package/Manifest/Trust Root audit.

Literal treatment prose is research evidence only and must never be hardcoded as policy.

## 10. Non-claims
R2 development PASS would still not establish real OpenAI Live parity, external multi-human consensus, human-writer equivalence, RFV3, CP1 Live, official R-F/R-G, Production promotion, or Formal R140.
