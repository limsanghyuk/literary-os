# P07 I4K5R4A G6 Mask Start Checkpoint R1

Date: 2026-09-12
Classification: DEVELOPMENT_PREFORMAL__SESSION_RESILIENT_CHECKPOINT
Parent physical authority: SYNC-R25
Parent transport root: `238704e04574386d430d0dfe9b187ca2d6028bc37919bf5e0be463d2b2ed5863`
Experiment: `P07-I4K-5R4A-PSSB-EXPRESSION-HYGIENE-INDEPENDENT-FRESH-CONFIRMATION`
Prereg commit: `4a4b521c6c69883d08b0590c36156b0ffab5303e`
Exact-arm freeze commit: `494190b45db7889de94835de59692b110cbe6a8b`
Mechanical prescore PASS: `1468ecc329582b443dd09afee57524a80fd92ad5`
G5B PASS: `f0fb7e701f0083bd1c55442fd97a9788059aa1f1`
Repeated-plan-purpose compliance PASS: `d308fc94f6a6a1a736ad4cd40793ffcddb17d966`

## Current exact state
- Control: 40,650 chars, 50 scenes, frozen.
- Treatment: 37,620 chars, 50 scenes, frozen.
- Surface mutation after freeze: PROHIBITED.
- Mask: 0.
- Independent judge scores: 0.
- Mapping open: 0.

## G6 frozen contract
- U01-U10: corresponding full sequence surfaces.
- U11: whole-episode architecture/continuity after full read.
- U12: whole-episode broadcast surface/craft after full read.
- Neutral A/B labels randomized independently per unit.
- A/B byte lengths equalized per unit.
- Mapping stored separately and not opened before all three judge score packets are sealed.
- R3 result, source-arm labels, source paths/hashes, other judge scores hidden from judges.
- Authoritative judge test double forbidden.

## Recovery rule
If the session ends before G6 completes, resume by reading this checkpoint and the current pointers, verify that no mask/judge/mapping artifact has already advanced on main, then continue from G6 mask construction only. Never regenerate or mutate frozen Control/Treatment.

Status: `G6_MASK_START__OUTPUTS_0__SESSION_RESILIENT_CHECKPOINT`
