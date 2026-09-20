# SYNC-R61 Delivery Correction R2 Receipt

Date: 2026-09-20
Status: `PASS__9_OF_9__DELIVERY_BYTES_RETAINED__R1_TRANSPORT_SUPERSEDED`

## Correction
The prior SYNC-R61 R1 Hub physicalization record advanced before its nine transport files were retained/delivered.

R2 preserves the same logical authority while creating a new retained transport set.

Superseded R1 trust root:
`18eaa49ecc2aa514f053466b9718a1e6bda92ea3b6055b28a712cdd71ee3b839`

Current R2 trust root:
`1e592e73665beeaf59aee33cd7c5d72075854d863308ae0262d5237b453edce1`

## Authority
- logical physical authority: SYNC-R61
- active qualified Candidate: exact SYNC-R58 / ADAPTIVE_UL16
- R63: CLOSED FAIL pre-blind
- R64: NOT STARTED
- Production: ENG:R47 / LEGACY_R53
- Runtime DB: DB59

## Physical audit
9/9 transport hash PASS.
C2 logical SHA256:
`067a85718bccd95aba48f7384ea995fbde41c0695204f266e679e30fa9d4c200`

C1 current runtime SHA256:
`30281db791d9bb629218a79c51c230bffb8f9088d79c2cfe6d676f996098b250`

B1/B2/D1/D2 remain byte-identical to SYNC-R60.
CONTROL/A/C1/C2 carry the post-R63 research overlay.

R63 failed source:
`7236eba306305269b06f9924c617139ecca038a5c6697891bac770a07913b7dd`

R63 evidence package:
`ecf5b0569aafb01223c4e0e72750ff9a8998a2debd7affa4cdc1a4fa68e476ee`

ZIP CRC PASS; duplicates/encrypted/unsafe entries = 0; secret audit PASS.
