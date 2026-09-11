# P07 I4K Research Sync R24 — Physical Closure R1

Date: 2026-09-11

Physical research authority: `P07_I4H_RECOVERY_R3__POST_R3_RESEARCH_SYNC_R24__I4K5R4A_ATTEMPT1_PRESCORE_G5_REJECTED__ATTEMPT2_SERIES_SEALED__G5A_PENDING`

Transport-set root: `8b42c029f14f344ce7fbfc9407ab3cce1f9692f16ba8659c6045a327e3a8d043`
Parent logical Sync R23 root: `8c2c283ac7f378b30c23a255d5d9835afc1b056df8865710a09999ffb296e901`.

R24 is an audited cumulative reconstruction: six immutable transports are byte-identical to R23; CONTROL/A/B2 are rebuilt from the verified R19 local bases, with the R20 B2 filename-metadata repair effectively normalized by a clean streaming rebuild and a cumulative R20→R23 + post-R23 R4A overlay. It is a logical successor of R23 and does not claim byte-descendant identity for the three rebuilt ZIPs.

Changed: CONTROL / A / B2. Byte-identical: B1 / C1 / C2-A / C2-B / D1 / D2.

Final physical audit: PASS. Combined C2 `58d28ecc900dcc62f820e7523294f840d506f451aecef12ea7b1b3d97ec2a9f7` / 318368553 bytes / 3774 entries. DB59 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9` / 259756521 bytes. Overlay identical across CONTROL/A/B2 = True.

Research state physically propagated: R4A Attempt1 mechanical prescore PASS but G5 semantic nonloss FAIL, prescore-rejected with mask/scores/mapping 0; final Attempt2 authorized and fresh Series/Episode `해온 시민극장 / 객석 불이 꺼지기 전에` sealed. Next legal action: fresh Attempt2 Event Ecology -> 10 Sequence -> 50 Scene -> G5A before render.

Active Engine remains P07-I4H Recovery R3; Production ENG:R47; DB59 frozen; Formal 137; latest R138; R140 0/0/0.
