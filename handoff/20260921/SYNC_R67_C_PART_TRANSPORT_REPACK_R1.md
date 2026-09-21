# SYNC-R67 C-Part Transport Repack R1

Date: 2026-09-21
Status: `PASS__TRANSPORT_REPACK_ONLY__PHYSICAL_AUTHORITY_UNCHANGED`

## Purpose (목적)
Correct the Part C packaging layout after C1 Runtime Core (런타임 코어) accumulated duplicated historical runtime and research-evidence copies.

## Authority (권위)
- Physical Authority (물리 권위): **SYNC-R67 — unchanged**
- Active Qualified Candidate (활성 자격 후보): **R69 F06 / R68 F04 / R67 F07 / R66 F01 lineage — unchanged**
- Active Runtime SHA256: `3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`
- Production Engine (운영 엔진): **ENG:R47 / LEGACY_R53 — unchanged**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64 research-only**

## Repack policy (재패키지 정책)
### C1 — Slim Runtime Core (경량 런타임 코어)
C1 now contains the current R69 runtime once and removes duplicated historical Candidate/Parent/Fallback runtime copies and direct `research_sync_*` evidence directories.

C1:
- bytes: `140372821`
- MiB: `133.87`
- SHA256: `44b5e65704da3567ef144133838ce8dda3338768637adf50e517af0c21dfcd80`
- ZIP CRC: PASS
- duplicates: 0
- encrypted: 0
- unsafe paths: 0
- active runtime hash: exact R69 PASS
- live-looking secret findings: 0

### C2 — Archival / research binary (연구·보관 바이너리)
C2-A/B are byte-identical copies of the original SYNC-R67 transports.

C2-A:
`7a1361a3ac0ff68ba2c16a591ffb73d8d1a9d54842d79ae97e2b1712d12024de`

C2-B:
`184e32f269a2a919cacf277491808e5fed0f749cf085153709e0af49921a43ee`

Reassembled C2 logical:
- bytes: `470656060`
- SHA256: `af84d97d59b9383caf5b53e3467e9479c8a3ce226b9e336b750e4b666f873b02`
- CRC: PASS
- duplicate/encrypted/unsafe paths: 0

## Trust
C-Part Repack Trust Root SHA256:
`71ed50ac9c3e440a1e2e3185a78e686c657d4e352a788b9582e61cb3f8c85ea4`

Audit Receipt SHA256:
`aba501aa2843c03fa0c61b6d6b308e6fa56663ceeb98831386e3fb27f9877369`

SHA256SUMS SHA256:
`9828d1b8a1d0cb28947c6debbf323507037a568599af3b2a1123629ff45a3f4e`

## Claim boundary (주장 경계)
This changes transport/package layout only.
It does NOT change:
- R69 research result;
- Active Runtime behavior;
- Physical Authority identity;
- Production Engine;
- DB authority;
- R70 research state.

Future Part C delivery should use this C-Part Repack R1 layout instead of the oversized duplicated C1 layout.
