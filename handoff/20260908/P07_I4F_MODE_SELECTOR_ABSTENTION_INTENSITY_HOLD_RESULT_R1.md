# P07-I4F Mode Selector / Abstention / Operator Intensity Probe — HOLD Result R1

Date: 2026-09-08
Classification: DEVELOPMENT / PREFORMAL / NO FORMAL COUNT DELTA
Preregistration commit: `09f556b9e979623460ee5f5419eb1d51166d4d3a`
Parent active authority: `CURRENT_PHYSICAL_AUTHORITY__P07_I4D_SURFACE_REALIZATION_MODES_R1`
Parent active C2 SHA256: `1022a4144e582069a3d6ed9d234f100d0b8a3a4323b73039d1454e57f89d75e1`
Parent cumulative research authority: `CURRENT_PHYSICAL_RESEARCH_AUTHORITY__P07_I4D_ACTIVE__I4C_I4E_EVIDENCE_SYNC_R1`

## Final verdict
`HOLD__SELECTOR_OVERAPPLIES_MODE__ABSTENTION_PRECISION_INSUFFICIENT__NO_PROMOTION`

No threshold was weakened. No selector/intensity code may be promoted. State Commit is blocked. Active engine remains exact P07-I4D.

## Pre-output / causal result
- prospective selector decisions frozen before new prose;
- prospective scenes: `S01/S04/S08/S12/S16/S18/S22/S24/S29/S32/S38/S44`;
- protected sentinels: `S07/S11/S14`;
- selector decision validation 15/15 PASS;
- protected sentinels selected NONE 3/3;
- selected intensity changes actual provider literary payload hash;
- irrelevant metadata leaves consumed literary payload invariant;
- NONE omits `surface_realization_mode` payload;
- principal play/voice completeness PASS;
- Human Anchor inspected = FALSE;
- focused selector tests 6/6 PASS;
- selector-decision canonical SHA256 `fba72565deb34b95f6be155b2c289411a56a279848a55e6b2d6c02261c8d889e`.

## Tri-arm generation
For each prospective scene, three semantically constrained arms were sealed:
- NONE = exact sealed I4C-R2 scene reuse;
- MODE_LOW = new in-session LLM surrogate NONLIVE;
- MODE_STANDARD = new in-session LLM surrogate NONLIVE.

36 total arms; 24 new prose outputs. Mechanical gate PASS:
- unauthorized principal speaker 0;
- critical semantic/continuity violation 0;
- source/future leakage 0;
- forbidden meta leakage 0;
- long exact dialogue/narrative duplicate 0;
- LOW/STANDARD procedural vocabulary density within +20% of scene NONE arm.

All-arms SHA256 `121db12d8152c736669b0f0aa1605fd31b9cb16079df1cf0c46f32bebc1b2dc5`.
Generation-seal SHA256 `10427c7a2674056ef5d3d544805de5e836c9b9d850b4567b411aff1a0b2c970c`.
Blind packet SHA256 `4ee4ff8deabb3b122e229e45aa468b0c587e53a50a5938065926817ab5c048a8`.
Sealed mapping SHA256 `cafc342e8157df01c7a567d7a29e630cb7eaed5c061ff93e3b9f259778ad945d`.

## Blind judgment discipline
The 12 triads were fully judged before mapping reveal.
Judgment SHA256 `66d033933c21565867d20d3d7499a19486b0d5827f88fa8c8364277952c4a7d7`.

The blind judge penalized genuine residual surface defects where present, including malformed lexical/grammar artifacts such as `회계회계실`, `장부을`, `양식를`, `문서을`, `남김한다`, `차판`, and `위치를 보기한다`. These defects were not repaired after blind evaluation started.

## Preregistered gates A-F
A. Protected abstention: S07/S11/S14 -> NONE 3/3 and unchanged — **PASS**.

B. Frozen selected arm blind-best/co-best >=8/12:
- actual **5/12** — **FAIL**.

C. Selected arm strictly worst <=1/12:
- actual **5/12** — **FAIL**.

D. Selected MODE scenes (8): selected arm vs NONE non-loss >=6/8 and outright wins >=4/8:
- non-loss **1/8**;
- outright wins **1/8** — **FAIL**.

E. Selected NONE scenes S08/S12/S18/S32: NONE best/co-best >=3/4:
- actual **4/4** — **PASS**.

F. Selected intensity vs opposite intensity non-loss >=6/8:
- actual **3/8** — **FAIL**.

All A-F were required. Overall selector result = **FAIL**.

## Scene-level diagnosis
Blind best arm was NONE on **10/12** prospective scenes. Only:
- S16 -> STANDARD best;
- S29 -> LOW best.

The frozen selector correctly selected the best arm on:
- S08 NONE;
- S12 NONE;
- S18 NONE;
- S29 LOW;
- S32 NONE.

The selector chose a strictly worst arm on five scenes:
- S01 STANDARD;
- S04 LOW;
- S16 LOW;
- S22 LOW;
- S38 STANDARD.

For the eight scenes where the selector chose a mode, only S29's chosen mode beat NONE. This is strong evidence that the current decision policy over-applies modes.

## Interpretation
I4F does NOT show that abstention is ineffective. The opposite is supported: all four prospectively frozen NONE decisions were correct (4/4), and NONE was blind-best on 10/12 scenes overall. The failure is selector calibration: its intervention threshold is too permissive and its intensity choice is insufficiently precise.

A confound is also recorded: several generated LOW/STANDARD arms retained lexical/grammar degradation after the preregistered mechanical checks. This is a genuine surface-quality failure of those arms and must not be removed post hoc. Future selector research should separate predicted *need for intervention* from predicted *realization reliability*, so a high-risk mode output can be rejected/abstained before adoption.

## State / promotion rule
Because gates B/C/D/F failed:
- canonical State Commit = BLOCKED;
- no new carry;
- prior semantic carry remains `5a5a0511b726ce880d96bbd093faa73f95949e7afae49aea6cd0ca0308c24a7c`;
- no selector/intensity promotion;
- no active C2 change;
- no promotion regression is required or run;
- Active Engine Authority remains P07-I4D.

State-Commit block receipt SHA256 `533b29d505ff69506c105ead6851c85c01b4ade9230717fb5908af9b0e33c046`.
Local result-ledger SHA256 `c7597318a9b33fc3cea46e39c5e777d6c6f1251e160beebfeaca6bd1c9d7da3b`.

## Next research implication
Do not start another 50-scene rerender. Do not strengthen every mode. The next unit should test a more conservative two-stage decision boundary:
1. `INTERVENE?` with a strong abstention prior and output-risk gate;
2. only if intervention is justified, `LOW vs STANDARD` intensity.

Prospective calibration should target a materially higher NONE rate, separate scene-need confidence from mode-output reliability, and preserve protected-scene invariance. Thresholds must not be lowered.

Before that next unit starts, all I4F evidence must be synchronized into the cumulative 5 Parts / 9 Packages research authority as `RESEARCH_EVIDENCE_ONLY__NOT_ACTIVE_POLICY`.

## Claim boundary
This is internal single-model blind selector calibration evidence only. It does not establish whole-episode human competitiveness, external human consensus, human-writer equivalence, real OpenAI Live parity, RFV3, CP1 Live, official R-F/R-G, Production promotion, or Formal R140 closure.
