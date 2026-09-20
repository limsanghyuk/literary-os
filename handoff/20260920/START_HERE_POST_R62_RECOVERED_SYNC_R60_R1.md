# START HERE — POST-R62 RECOVERED PHYSICAL AUTHORITY SYNC-R60 R1

Date: 2026-09-20
Status: `CANONICAL_NEW_SESSION_HANDOFF__PHYSICAL_RECOVERY_ALIGNMENT_COMPLETE__R63_NEXT_NOT_STARTED`

## One-sentence authority rule
SYNC-R60 is now the latest complete recovery-aligned 5-Part / 9-Package physical authority. It was rebuilt from developer-held SYNC-R59 bytes plus the post-SYNC-R59 R62 FAIL authority overlay. The active qualified Candidate is exact SYNC-R58 / ADAPTIVE_UL16; SYNC-R59/R62 bytes remain preserved as quarantined research evidence.

## Authority axes
- Latest physical authority: **SYNC-R60**
- Parent physical custody baseline: **SYNC-R59**
- Active qualified Candidate: **SYNC-R58 / ADAPTIVE_UL16**
- Quarantined failed research snapshot: **SYNC-R59 / R62 F01**
- Production: **ENG:R47 / LEGACY_R53**
- Runtime DB: **DB59 frozen**
- Research DB: **DB64**
- R62: **CLOSED FAIL — 9W / 0T / 3L**
- R63: **NOT STARTED**

## SYNC-R60 exact package hashes
- CONTROL: d00b1d7b1aaaf30fc99d7043c2b0124755215f961e0c794989cd817bcc388b89
- A: 2e80c6673be977402297169d481c7d70603b396c783d79751ae0e359b11d07ee
- B1 inherited byte-unchanged: 00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98
- B2: 35d2d47754ab5e8fc71b2220b49317e58e8fd3b899f66205f66e0b7c75793167
- C1: b39ed8434945423c1aa7c4a57bf0794c0612208f0594cdc4db72d3b26d28bef1
- C2-A: 7bf931e3dfbdc908e810660993d14875088c8943ddafa7edf5ffc58db8329b12
- C2-B: a939de91914302668ce85c08e9a671cba44ee368db19c7543e366bda16967aea
- D1 inherited byte-unchanged: a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504
- D2 inherited byte-unchanged: c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4

C2 logical:
- bytes: 375,933,732
- SHA256: 5788e13216a6fe5c86834621efc34a90917a0ebb35c387fc5d7a08c9614ffe04

Trust root SHA256:
657f0986debef9574a7710ad27cc1b41f1cbd189bf297334ff55c49919b476d4

## Runtime bindings
ACTIVE SYNC-R58:
- runtime: 30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250
- overlay: d4215a8a5075054a054d5ca60e10e5992c4139588cccaeb0dabe14281f2fd633
- adaptive source: 42510706a7876e649fe869c48910460f976d4528f0aa0dbd09a98a4256a7eb68

QUARANTINED SYNC-R59/R62:
- runtime: a6a0e65460948562c2cd7146efcb207a6b02ff77403f67a6bf9049792d95d625
- overlay: 059e10a3b2cb71acf3db8144240ebfebeeac6924daf13fdb2d1858f1a3369e41
- adaptive source: 7c150389a688b4d769b96ade341921a77b7fe86289645c0c613a035c6151a377

DB59:
a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9

## Research recovery
- R59 CLOSED HOLD
- R60 CLOSED PASS
- R61 CLOSED
- R62 CLOSED FAIL
- R63 NOT STARTED

R62 was not rerun or rescored. Existing J01/J02/J03 judgments remain immutable. The recovery operation only aligned physical authority with the already-closed scientific result.

## Audit closure
- Parent SYNC-R59 verified 9/9 before rebuild.
- New SYNC-R60 9/9 SHA verification PASS.
- ZIP CRC PASS.
- C2 reassembly PASS.
- C1 generic CURRENT runtime now hashes exactly to qualified SYNC-R58.
- SYNC-R59/R62 evidence remains present and explicitly quarantined.
- DB59 PASS.
- DB64 research split/bundle verification PASS; DB64 remains research-only.
- Secret-pattern audit PASS.
- B2 remains below 256 MiB, but with only 148,859 bytes margin.

## Container incident learning
A post-build `sha256sum -c` initially failed because the checksum file used relative filenames and the command ran outside the output directory. This was a cwd verification error, not package corruption. Re-running from the package directory passed all entries.

Large package rebuilding caused cgroup memory.max pressure events through page cache, but `oom=0` and `oom_kill=0`. Temporary build artifacts were deleted and memory.current fell substantially. Future large rebuilds must continue to use streaming I/O, /tmp intermediates, checkpointed hashes and minimal concurrent decompression.

## Next research
R63 = F01 Semantic Applicability + Abstention Gate.

R63 may now be preregistered as the next research, but this handoff itself contains no R63 code or output.
