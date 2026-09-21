# SYNC-R67 C1 / C2-A Redelivery Recovery R1

Date: 2026-09-21
Status: `DELIVERY_RECOVERY__PHYSICAL_AUTHORITY_SYNC_R67_UNCHANGED__R70_STATE_UNCHANGED`

## Problem (문제)
User could not download:
1. Part C1 — R69 Runtime Core (런타임 코어)
2. Part C2-A — SYNC-R67

Investigation found two distinct causes.

### C2-A
The exact original C2-A bytes are still present locally.

Historical/current sealed values:
- bytes: `235328030`
- SHA256: `7a1361a3ac0ff68ba2c16a591ffb73d8d1a9d54842d79ae97e2b1712d12024de`

Therefore C2-A is a delivery-surface problem only.
For reliable redelivery it is split into <=80 MiB parts; reassembly must reproduce the exact historical C2-A SHA above.

### C1
The original post-R69 SYNC-R67 C1 retained file is no longer present in the current /mnt/data surface.

Historical sealed original C1:
- bytes: `384388452`
- SHA256: `3c4f79fd766bca655c891870eca9b9c35998d06cba153453d3720d8a54ac9a7e`

A byte-identical source copy was not available in current retained storage, so no claim of byte-identical reconstruction is made.

A logical Recovery R1 was reconstructed from the last retained valid C1 lineage plus exact frozen R68/R69 runtimes and evidence.

Recovery C1:
- bytes: `366837474`
- SHA256: `9a09e970f4285473dada97c02340bfdaea35ea01bfe220d225c07f33ebf01056`
- ZIP CRC: PASS
- duplicates: 0
- CURRENT R69 runtime SHA: `3d104f635f3c2aea5812917c8b273d1a5fc250b13165f3f88509e0b7a07437b1`
- R68 parent runtime SHA: `af0fd4dc4ba3d7037e1d98ed8ec4177b155cae10936e8210e9e443a07ed69696`

Recovery Trust Root SHA256:
`41e69f4fc14de4e153c6b3a5c78ab49a121b42607cce53f7743b553f0458e4fc`

Recovery Audit SHA256:
`8ef4a85533022ef9278011acca27a16740847809d422473747c9aadc9e542e48`

## Delivery format (전달 형식)
To avoid large-file surface/materialization limits:
- C1 Recovery R1 is split into five <=80 MiB parts.
- C2-A exact original is split into three <=80 MiB parts.
- A Python reassembler and SHA256 manifest are supplied.
- Reassembler verifies every part hash and final assembled hash before reporting OK.

Manifest SHA256:
`2e5b48fbec5e9b7e7294e999ddbe3f0eef4004b7fc6fd0f7a1d596e9e23de311`

Reassembler SHA256:
`ea5f1c18e995323de0185125850516cefe1b7ea43e07ec67c5d901cadec4164c`

## Authority boundary (권위 경계)
This is a delivery recovery only.

- Physical Authority remains **SYNC-R67**.
- Historical original SYNC-R67 Trust Root remains historical evidence.
- Recovery Trust Root must be used for the Recovery C1.
- C2-A remains byte-identical to the historical original.
- R70 remains `ACTIVE__STAGE_A_PASS__STAGE_B_WAITING_LIVE_PROVIDER_EXECUTION`.
- Production remains `ENG:R47 / LEGACY_R53`.
