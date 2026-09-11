# START HERE — P07 I4K New Session Handoff R6
Date: 2026-09-11

## CURRENT PHYSICAL AUTHORITY
`P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R24__I4K5R4A_ATTEMPT1_PRESCORE_G5_REJECTED__ATTEMPT2_SERIES_SEALED__G5A_PENDING`

R24 transport root: `8b42c029f14f344ce7fbfc9407ab3cce1f9692f16ba8659c6045a327e3a8d043`.
Physical closure commit `341228decb44eca7d8218d661366f6119da73a46`.
Delivery manifest commit `a871466f4727476401d0f0a95490d2301d6e7a6f`.
Physical audit commit `aaf47ccd8e317a190d0450c229708d2d795483a5`.

Mandatory package read order: `CONTROL -> A -> B1 -> B2 -> C1 -> C2-A -> C2-B -> D1 -> D2`.

R24 is an audited cumulative reconstruction and logical successor of R23. B1/C1/C2-A/C2-B/D1/D2 are byte-identical to R23. CONTROL/A/B2 were rebuilt from the directly reverified R19 bases, B2 filename metadata was normalized to mismatch 0, and a byte-identical cumulative `research_sync_r24/` overlay was inserted into all three changed transports. Do not describe the rebuilt three ZIPs as byte-descendants of R23.

## CURRENT RESEARCH STATE
Original R4 closed pre-render after the user added Actor-Visible Expression Hygiene; not scored and not a quality failure.

R4A prereg commit `4a4b521c6c69883d08b0590c36156b0ffab5303e` remains immutable. Both arms use Actor-Visible Expression Hygiene; Treatment alone adds frozen PSSB.

Attempt1 mechanical prescore passed: Control 42,037 body chars, Treatment 41,400, 50/50 scenes, 1.5153% gap, all sequences >=3,600, meta leak 0, direct-emotion-stage-pattern 0, exact long duplicate 0. G5 then found a shared semantic nonloss defect: E06 Facility Flow future owner C05 / future shared-flow-map obligation was not explicitly adopted by the final shared Scene Plan. Attempt1 is `REJECTED_PRESCORE__NOT_SCORED__NOT_QUALITY_FAIL`; closure `fcba9b9d2f3bfb57186043a4d41fae6bcca87707`. Mask 0 / judge scores 0 / mapping open 0.

Final provisional Attempt2 is authorized. G5 criterion is unchanged but is now executed as G5A before rendering and G5B after rendering; supplement `36b4965254cb24b7c15c430507f8a37569972bba`.

Attempt2 fresh Series/Episode commit `3bc2da6d8717f2483073fe9cbfd078071f73ea20`:
- Series: `해온 시민극장`
- Episode: `객석 불이 꺼지기 전에`
- outputs: Series/Episode 1; Event Ecology 0; Sequence 0; Scene 0; G5A 0; Control 0; Treatment 0; Mask 0; Judges 0; mapping open 0.

## EXACT NEXT ACTION
Create Attempt2 Event Ecology with explicit mechanism / downstream decision owner / future owner / second-order obligation / `future_adoption_target` for every event. Then shared 10 Sequence -> shared 50 Scene -> G5A. No Control/Treatment rendering before G5A PASS.

## UNCHANGED AUTHORITIES
Active Engine `P07-I4H Recovery R3`; Production `ENG:R47`; DB59 frozen; Formal scored count 137; latest Formal R138; R140 `0/0/0`.
