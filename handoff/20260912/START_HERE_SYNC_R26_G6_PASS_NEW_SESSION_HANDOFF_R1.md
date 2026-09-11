# START HERE — SYNC-R26 / G6 PASS

Date: 2026-09-12

## Physical authority
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R26__I4K5R4A_ATTEMPT2_G6_MASK_PASS__JUDGES_0__MAPPING_CLOSED`
Transport-set root: `c43ad4f04546e4c883ef961a70846d2f4c414abe2eaab86b5ce12f28410e2b1b`
Physical closure: `handoff/20260912/SYNC_R26_G6_MASK_PASS_PHYSICAL_CLOSURE_R1_20260912.md`

## Read order
CONTROL → A → B1 → B2 → C1 → C2-A → C2-B → D1 → D2.

## Exact experiment state
Experiment: `P07-I4K-5R4A-PSSB-EXPRESSION-HYGIENE-INDEPENDENT-FRESH-CONFIRMATION`.
Prereg commit: `4a4b521c6c69883d08b0590c36156b0ffab5303e`.
Exact arms frozen commit: `494190b45db7889de94835de59692b110cbe6a8b`.
Mechanical prescore PASS: `1468ecc329582b443dd09afee57524a80fd92ad5`.
G5B PASS: `f0fb7e701f0083bd1c55442fd97a9788059aa1f1`.
Repeated plan-purpose compliance PASS: `d308fc94f6a6a1a736ad4cd40793ffcddb17d966`.
G6 mask leakage PASS: `b2f68c3aa0a1f7ecda594f2b6034cf9dcabc17cd`.

Control 40,650 chars / Treatment 37,620 chars / 50 scenes each.
Mask=1; independent judge scores=0; mapping open=0.

## Blind artifacts
Masked packet artifact id `10273575016`, artifact digest `sha256:516eff141d544a67ac228d8de9f8c23ee047c05a97730ddef8940cf290d5c399`, internal packet SHA256 `99828302087a214260f0b5e676ac333eb8e7f5c564112849e76e46228506da4f`.
Mapping-secret artifact id `10272549788`, artifact digest `sha256:62b39f82b14701ad19ed954531f6042b145cba59a886775a641ea4b4b5e193ea`, internal mapping SHA256 `01a5791ca7a34006964a376a01c6cf00729d90275fe0a6640a4dd7355824e23b`.
**DO NOT DOWNLOAD OR OPEN THE MAPPING SECRET before all three judge packets are sealed.**

## Exact next legal action
1. G7 duplicate-score / judge-provenance preflight.
2. Run exactly three independent real-provider judges. Each judge sees only the masked packet and scoring contract; hide mapping, R3 result and other judge scores.
3. Require provider receipt for each judge; authoritative test doubles forbidden.
4. Seal all three judge score packets.
5. Only then retrieve/open mapping once.
6. Compute per-judge H1-H4 and cross-judge medians/independent-confirmation rule.
7. Immediately propagate any meaningful result change to a new 5-Part/9-transport physical Sync before proceeding further if session interruption risk remains.

## Do not do
- Do not regenerate or edit Control/Treatment.
- Do not regenerate G6 mask.
- Do not change thresholds or judge count.
- Do not open mapping early.
- Do not promote Active Engine/Production/Formal from G6 PASS.

## Unchanged authorities
Active Engine P07-I4H Recovery R3; Production ENG:R47; DB59 frozen; Formal scored count 137; latest Formal R138; R140 0/0/0.

Status: `SESSION_RECOVERY__SYNC_R26__G6_PASS__JUDGES_0__MAPPING_CLOSED__G7_NEXT`
