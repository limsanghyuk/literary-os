# R74 Runtime / Physical Package Safety Protocol R1

Date: 2026-09-22

Status:
`ACTIVE_SAFETY_PROTOCOL__CONTAINER_UNAVAILABLE__PHYSICAL_AUTHORITY_FROZEN_AT_SYNC_R72`

## Incident classification

Observed repeatedly on 2026-09-22:
- container minimal command -> TransportTimeoutError
- private Python runtime -> TransportTimeoutError
- visible Jupyter runtime -> TransportTimeoutError

A minimal health command also failed:
`/bin/echo CONTAINER_HEALTH_OK`

At the same time, GitHub Actions executed R74 Stage M and freeze-harness tests successfully.

Conclusion:
`SESSION_RUNTIME_LAYER_FAILURE__NOT_DB_CORRUPTION__NOT_SCIENTIFIC_FAIL`

No evidence supports corruption of the already-sealed SYNC-R72 package set.

## Mandatory physical-package safety gate

Do not create, modify, split, rejoin, reseal, rename, or upload a successor 5-Part / 9-Package set until ALL of the following pass in one healthy runtime session:

1. minimal process gate
   - `/bin/echo HEALTH_OK`
2. filesystem gate
   - known-path read under `/mnt/data`
   - write/read/delete probe under `/tmp`
3. Python gate
   - import hashlib, json, zipfile
   - create/read/delete one small temporary file
4. parent-authority gate
   - verify all 9 parent package sizes and SHA256 values against the canonical manifest
   - verify parent logical C2 rejoin SHA
5. memory/OOM gate
   - no current OOM event / no active memory-pressure failure where inspectable

Any failure:
`PHYSICALIZATION_HOLD__NO_PACKAGE_MUTATION`

## Large-file operating rules

- Never recursively hash all of `/mnt/data` or a large package tree.
- Use known-path / manifest-directed inspection only.
- Do not reconstruct large logical C2 or DB archives directly in `/mnt/data`.
- Use `/tmp` for large intermediate rejoin/build work.
- Copy only audited final artifacts to `/mnt/data`.
- Never overwrite an existing SYNC output directory.
- Never reuse a previously published SYNC ID.
- Build into a uniquely named candidate directory first.
- Hub CURRENT pointers are updated only AFTER local physical audit and package attachment success.

## 5-Part / 9-Package audit rules

Before declaring a successor Physical Authority:
- CONTROL CRC PASS
- A CRC PASS
- B1 CRC PASS
- B2 CRC PASS
- C1 CRC PASS
- C2-A/B exact split sizes recorded
- logical C2 rejoin SHA256 PASS
- logical C2 ZIP CRC PASS
- duplicate entries = 0
- encrypted entries = 0
- unsafe paths = 0
- D1 CRC PASS
- D2 CRC PASS
- inherited packages explicitly byte-checked against parent
- 9-package manifest created
- Trust Root created
- SHA256SUMS created
- READ FIRST created
- post-build re-verification performed

If any package was truncated, partially uploaded, name-collided, or has an unexpected hash:
- quarantine the candidate;
- do not update CURRENT authority;
- do not reuse the same SYNC name;
- recover from the last byte-verified parent or exact retained logical source.

## Scientific boundary

TransportTimeoutError, ClientError, GeneratedFileUploadError, upload truncation, and workflow indexing delay are infrastructure events unless independently reproduced as engine failures.

They must not:
- become scientific FAILs;
- change preregistered thresholds;
- alter sample selection;
- justify rerunning valid provider outputs;
- justify inventing missing custody artifacts.

## Current protected state

- Physical Authority: SYNC-R72
- Manifest SHA256: `05d6e2be8d472b8ff91ac6174d31f41ad41a6da3b89f6983c09eb4911c3b7cf0`
- Trust Root SHA256: `52ce353bdd72ef7574a6f54c4dd946256d8cb88d5ed9c8e9e8c4efddad90606f`
- Logical C2 SHA256: `87b79628a5ffd35b13849009146cf2b8429288befd9d7523a39f7c77af2252a8`

These remain current until a later session passes the mandatory physical-package safety gate and completes a successor reseal.
