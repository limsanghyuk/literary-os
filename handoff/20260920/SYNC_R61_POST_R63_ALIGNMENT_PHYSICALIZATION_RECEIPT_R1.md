# SYNC-R61 Post-R63 Research Overlay Physicalization Receipt R1

Date: 2026-09-20
Status: `PASS__9_OF_9__NO_ACTIVE_RUNTIME_CHANGE`

SYNC-R61 physically aligns the R63 failed research overlay to the current package authority.

## Parent
SYNC-R60.

## Active authority
SYNC-R58 / ADAPTIVE_UL16 remains the active qualified Candidate.

Active runtime SHA256:
`30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`

## Research evidence
R63 frozen source:
`7236eba306305269b06f9924c617139ecca038a5c6697891bac770a07913b7dd`

R63 result:
`CLOSED_FAIL__PREBLIND_SELECTOR_SAFETY_GATE`

No external blind was dispatched.

## Physical audit
All nine transport hashes passed.
C2 logical SHA256:
`b9b2869c4ae4e1a17282564a49760c27516f6812bf0a18e3c374a0ea21c53e34`

Trust root SHA256:
`18eaa49ecc2aa514f053466b9718a1e6bda92ea3b6055b28a712cdd71ee3b839`

B1, B2, D1, D2 are byte-identical to SYNC-R60.
CONTROL, A, C1, C2 were updated only to carry post-R63 research/authority evidence.

B2 remains 268286597 bytes, 148859 bytes below 256 MiB.

## Container note
The first R63 execution command encountered a TransportTimeoutError. Minimal command and /mnt/data health checks immediately passed, so the incident was treated as a transport-layer failure and not as scientific or package failure.

During large package audits, page-cache pressure raised cgroup max events, but oom=0 and oom_kill=0. Temporary logical C2 was deleted after validation.
