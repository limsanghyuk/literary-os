# SYNC-R53 DIRECT 9/9 RECOVERY VERIFICATION RECEIPT R1

Date: 2026-09-16
Project: Literary OS Development
Classification: DIRECT RECOVERY VERIFICATION RECEIPT / NO AUTHORITY CHANGE

## Result

Fresh direct verification of the developer-held SYNC-R53 transport baseline is complete at `9/9` in the current healthy runtime:

`CONTROL -> A -> B1 -> B2 -> C1 -> C2-A -> C2-B -> D1 -> D2`

This receipt confirms recovery/integrity only. It does NOT create a new SYNC authority, does NOT promote the Candidate, and does NOT prove durable Hub archive custody.

## Transport SHA256 receipts

- CONTROL: `f879b9dfde6e55c88dbac0070f5fb3f4e35482e49bdef33b724eed813f084c69`
- A: `11e3298aa62706a1e30abc41af4d13b13048aa86523a40a4b0f6b6f84ac98314`
- B1: `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2: `12b6e6dd18c224d5bc98dd6714c6a24e3be7b5531d3546db09f7915c5476b3a0`
- C1: `b2a06fa2add7f66d31d7ebf32a5264be9431e38b56f098b4241a2858e7da8cf4`
- C2-A: `aeb14bd4523466445411c8d6c00e38557e4847fce944eb314506ebb19dbc653f`
- C2-B: `ee85bab92b3c6ae52ca338ad0f4d5c04582c7fac2491d62e57ccac219b07af2d`
- D1: `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2: `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

## Archive safety

All ZIP transport packages directly tested passed CRC and had:
- duplicate member names: 0
- unsafe absolute/`..` traversal paths: 0
- unexpected symlinks: 0
- encrypted entries: 0

C2 split transport reconstructed successfully:
- reconstructed size: `319254266` bytes
- reconstructed SHA256: `e51da441f932f4bf445ddb09b62cdb0caf940a209a9649d8518075b6f25bffb9`
- ZIP CRC: PASS
- entries: `3786`

C1/C2 Candidate runtime overlay byte identity:
- SHA256: `d8c622cef4b3b853814efe896208494b7fb2bd6b2399dd6296adde8e498931ef`
- result: PASS

Narrative Engine Master reconstruction:
- size: `204167926` bytes
- SHA256: `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649`
- canonical SHA match: PASS
- ZIP CRC: PASS

## D-layer / DB59 verification

D1 outer package:
- size: `138011573` bytes
- SHA256: `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- ZIP CRC: PASS
- entries: `25`

D2 outer package:
- size: `173393886` bytes
- SHA256: `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`
- ZIP CRC: PASS
- entries: `59`

D1 manifest verification:
- DB59 drama-only learning bundle size+SHA: PASS
- DB59 part001 size+SHA: PASS

D2 manifest verification:
- Drama Analysis Learning Master size+SHA: PASS
- DB59 part002 size+SHA: PASS

D1/D2 corrected DB59 authority pointer bytes are identical:
- pointer SHA256: `1e46e1e5cad89841913f2c9881c5aa36e478226ab8e184884c4026d158f4ba2c`

DB59 reconstruction from D1 part001 + D2 part002:
- reconstructed size: `259756521` bytes
- reconstructed SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- canonical DB59 SHA match: PASS
- ZIP entries: `38852`
- ZIP CRC: PASS
- duplicate/unsafe/symlink/encrypted: `0/0/0/0`

## Runtime safety findings

At the final audit boundary:
- cgroup `memory.max`: `4294967296` bytes (4 GiB)
- `memory.events max=0`, `oom=0`, `oom_kill=0`
- observed `memory.peak`: about `2.18 GiB`
- after page-cache advice/cleanup, `memory.current`: about `1.0 GiB`
- disk free: about `28 GiB`
- inode use: about `1%`
- open-files soft limit: `16384`; no descriptor exhaustion observed
- file-size limit: unlimited

Important durability boundary:
- `/mnt/data` and `/tmp` are on the same overlay filesystem in this runtime.
- the overlay mount reports `fsync=volatile`.
- therefore successful container-local write/fsync/hash is NOT evidence of durable storage outside the ephemeral runtime.
- a future SYNC successor still requires the full 12-step physical-custody gate, including user-visible 9/9 delivery, Hub manifest, durable archive locator, and download/re-hash verification.

## Authority boundary

Unchanged:
- Physical baseline: `SYNC-R53`
- Production Engine: `ENG:R47`
- Candidate Base: `P07-I4H Recovery R3`
- DB Authority: `DB59 frozen`
- Formal scored total: `137`; latest Formal: `R138`; R140: `0/0/0`
- Operational Level-3: `SUSPENDED`
- Level 4: `NOT STARTED`
- External UL-13 responses: `0`
- Live OpenAI qualification outputs: `0`

## Status token

`SYNC_R53_DIRECT_RECOVERY_9_OF_9_PASS__ENGINE_MASTER_CANONICAL_PASS__DB59_CANONICAL_PASS__RUNTIME_HEALTHY__CONTAINER_NOT_DURABLE_ARCHIVE__AUTHORITY_UNCHANGED`
