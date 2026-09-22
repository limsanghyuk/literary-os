# R74 Runtime Recovery / Parent Access Audit R1

Date: 2026-09-23

Status:
`RUNTIME_GATE_PASS__CONTROL_A_DIRECT_BYTE_PASS__SYNC_R72_REMAINING_7_RAW_BYTES_NOT_MATERIALIZABLE__PARENT_9OF9_DIRECT_REVERIFY_INCOMPLETE__R72_EXCLUSION_CUSTODY_HOLD__PRIMARY_OUTPUTS_0`

## Purpose

Resume R74 from the sealed new-session handoff without weakening the physical-package safety gate or the fully-fresh exclusion rule.

## Runtime safety gate

Current session results:
- minimal process gate: PASS
- `/tmp` write/read/delete: PASS
- private Python minimal execution: PASS
- Python `hashlib/json/zipfile` path used successfully
- previous `TransportTimeoutError` was NOT reproduced

Conclusion:
`LOCAL_RUNTIME_ACCESS_RECOVERED`

This clears the prior local runtime-layer hold only. It does not by itself clear the parent-package or R72 exclusion-custody gates.

## Directly mounted SYNC-R72 packages

### CONTROL
- bytes: 122,566,593
- SHA256: `3e937f4fafa29078922418ce89e25e387c0359f1b53b43a583e077eae34b04db`
- canonical manifest match: PASS
- Python ZIP CRC (`testzip()`): PASS
- entries: 1,851

### Part A
- bytes: 137,119,772
- SHA256: `1e5ca2c8e56c6a5326ef618e2a026a2c91a8e613ea7add1d30b521b315c2c217`
- canonical manifest match: PASS
- Python ZIP CRC (`testzip()`): PASS
- entries: 1,951

The command-line `unzip -t` path emitted legacy non-ASCII filename local/central metadata warnings. Python central-directory CRC verification passed, so those warnings are not classified as archive corruption.

## Remaining seven SYNC-R72 packages

Library records and the canonical SYNC-R72 Manifest / Trust Root / SHA256SUMS / Final Alignment files are present for:
- B1
- B2
- C1
- C2-A
- C2-B
- D1
- D2

However current-session raw-byte materialization was attempted for all seven and failed with:
`This Project file does not have an authorized raw-byte materialization path.`

Therefore current-session direct byte verification cannot truthfully be declared for those seven packages.

Consequences:
- current-session parent 9/9 SHA verification: INCOMPLETE
- current-session logical C2 A+B rejoin: NOT EXECUTED
- current-session logical C2 ZIP CRC audit: NOT EXECUTED

Historical sealed authority remains unchanged:
- Physical Authority: **SYNC-R72**
- Manifest SHA256: `05d6e2be8d472b8ff91ac6174d31f41ad41a6da3b89f6983c09eb4911c3b7cf0`
- Trust Root SHA256: `52ce353bdd72ef7574a6f54c4dd946256d8cb88d5ed9c8e9e8c4efddad90606f`
- Logical C2 SHA256: `87b79628a5ffd35b13849009146cf2b8429288befd9d7523a39f7c77af2252a8`

## R72 exclusion custody recheck

GitHub current tree, R72 preregistration history, R72 closure history, R74 custody audit, Project/Library search and current package-access paths were rechecked.

Recovered facts remain:
- R2: 24 primary cases existed; exact IDs not recovered
- R3: fresh 24-case ledger existed; exact IDs not recovered
- R4: fresh 24-case ledger existed; exact IDs not recovered
- R5: fresh 24-case ledger existed; exact IDs not recovered
- R5 ledger commitment:
  `d4398a3568f55258fb664f782f5542431795ab471f944a5df168c5501478a364`

The qualified R74 freeze harness requires exact R2/R3/R4/R5 custody and intentionally fails closed if any revision is missing.

No case IDs were guessed, inferred from style, reconstructed approximately, or silently dropped.

## Scientific / execution consequence

R74 Primary MUST NOT start yet.

Current execution boundary:
`STAGE_M_PASS__FREEZE_HARNESS_PASS__LOCAL_RUNTIME_RECOVERED__PARENT_9OF9_DIRECT_REVERIFY_INCOMPLETE__R72_EXCLUSION_CUSTODY_HOLD__PRIMARY_NOT_STARTED__PRIMARY_OUTPUTS_0`

This is not a scientific FAIL.

No Control primary outputs were created.
No Treatment primary outputs were created.
No efficacy verdict exists.
No R75 work is authorized.

## Physical-package consequence

Mandatory parent-authority gate is not fully satisfied in this session because seven package raw bytes are not mounted/materializable.

Therefore:
`PHYSICALIZATION_HOLD__NO_PACKAGE_MUTATION`

Do not rebuild, rename, split, rejoin, overwrite or reseal SYNC-R72.
Do not create a successor SYNC from this incomplete parent verification state.

## Exact resume boundary

1. Obtain direct raw-byte access to the remaining seven SYNC-R72 packages, especially C2-A and C2-B.
2. Verify 9/9 package sizes and SHA256 against the canonical manifest.
3. Rejoin C2-A+B in `/tmp`; verify logical C2 SHA256 and ZIP CRC.
4. Inspect known R72 evidence paths only.
5. Recover exact R2/R3/R4/R5 primary ledgers/materialization protocols.
6. Verify R5 recovered ledger bytes against `d4398a...`.
7. Build the complete R72 exclusion-custody manifest.
8. Run the already-qualified R74 primary freeze harness.
9. Freeze 24 fully fresh cases before any primary output.
10. Execute exact R69 Control vs unchanged F05 Treatment.
11. Score both arms through the qualified R74 R3 symmetric bridge.
12. Apply P1-P11 and close R74 before any successor physicalization.

## Authority effect

- Physical Authority: unchanged at **SYNC-R72**
- Active Qualified Candidate: unchanged
- Active Runtime: unchanged exact R69
- Production: unchanged ENG:R47 / LEGACY_R53
- Runtime DB: unchanged DB59 frozen
- Research DB: unchanged DB64 R127 research-only
- Operational Level-3: unchanged SUSPENDED / REQUALIFICATION REQUIRED
- Formal R140: NOT STARTED
