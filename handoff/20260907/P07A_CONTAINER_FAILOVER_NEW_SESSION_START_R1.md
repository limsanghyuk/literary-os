# Literary OS — P07-A Container Failover / New Session Start R1
Date: 2026-09-07
Classification: RECOVERY FAILOVER CHECKPOINT / NONFORMAL / PHYSICAL_CLOSURE_PENDING

## 0. Purpose
Preserve the exact P07-A state when the current ChatGPT session sandbox became unusable, and define the safe start sequence for a fresh session.

## 1. Current scientific authority
- Formal scored count: 137
- Latest formal scored authority: R138
- R140: 0 attempts / 0 outputs / 0 scores
- ENG:R47 Production: immutable
- P06: COMPLETED / PHYSICALLY CLOSED
- P07: ACTIVE PREFORMAL / NOT COMPLETE
- Current priority: P07-A — Authority / Package Recovery
- DB59 frozen SHA256: `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`
- DB64: separate Living DB; never silently substitute for DB59
- RFV3 generation outputs: 0
- CP1 current-authority restoration: OPEN
- Current repaired 9-package physical authority: MISSING
- R140: HARD BLOCK

## 2. Container failure diagnosis
Current session execution paths all return `ClientError` before useful package processing:
- OS/container minimal command path fails, including a no-file `/bin/true` style probe;
- private Python path fails;
- user-visible Python path fails.

Therefore the current failure is not attributable to D1/D2 file contents from available evidence: the container fails before D data are read.

Historical timing also matters: the first recurrent `ClientError` in this resumed session appeared while beginning B1/B2 verification, before D1/D2 fresh-byte processing. Thus Part-D may correlate with a high-load attachment/mount phase, but it is not established as the causal corrupt package.

Allowed interpretation:
`SESSION_SANDBOX_PROVISIONING_OR_ARTIFACT_MOUNT_PATH_FAILURE`

Possible but unproven contributing factor:
- cumulative large attachment/mount pressure, especially around DB-heavy Part-D.

Do NOT claim package corruption without a fresh session byte audit.

## 3. Previous physical baseline accounting
Canonical packages:
`CONTROL / A / B1 / B2 / C1 / C2-A / C2-B / D1 / D2`

All nine were supplied in the interrupted conversation.

Fresh SHA verification completed before infrastructure failure:
- CONTROL
- A
- C1
- C2-A
- C2-B
- `C2-A || C2-B` reconstructed expected previous C2 R39 SHA `d292690dd89ce88e9642bc38c3416d33aa4dc64dea6d0469c3a9ce0a62c10f3b`

Fresh-byte verification still required in a healthy sandbox:
- B1 expected SHA `00b671a5cdf8ecf2d6e54651abdd9606457245f3654a71eba26f6d684faa9c98`
- B2 expected SHA `f396d7fe583f6267c3b17735e690be5e50c35d48f2253ae7ea12a71779ecc920`
- D1 expected SHA `a63a253263d86e461d48b753865c6e993e86de9d6a17a77f199f2c38316ec504`
- D2 expected SHA `c6288a00294a91ecdd1eb20cb086365eefa1a3d8fbb7febd9ba7fe554fc172c4`

All nine remain `PREVIOUS_PHYSICAL_BASELINE` only.

## 4. RFV2 recovery mode
Read:
- `handoff/20260907/P07A_INFRASTRUCTURE_DIAG_AND_RFV2_SOURCE_SURVIVAL_AUDIT_R1.md`
- `handoff/20260907/P07A_RFV2_CONTROLLED_RECOVERY_REIMPLEMENTATION_SPEC_R1.md`

Current recovery decision:
`CONTROLLED_RECOVERY_REIMPLEMENTATION`
unless an exact prior repaired artifact is later found and independently hash/checkpoint verified.

Do not tune toward prior 6/6 or 185/185 observations.

## 5. Fresh-session container isolation protocol
Before uploading any large package in the new session:
1. Read `handoff/CURRENT_SESSION_RECOVERY_POINTER.md` and `handoff/CURRENT_DEVELOPER_HUB_AUTHORITY.md`.
2. Run three health probes before any package mount:
   - minimal OS command;
   - Python `print`/version probe;
   - `/mnt/data` existence/list probe.
3. If those fail, abandon that session before uploading packages.

If healthy, isolate package mounting sequentially:
4. Upload or attach B1 only -> SHA/CRC/duplicate/unsafe/nested audit -> health probe again.
5. Add B2 -> same audit -> health probe again.
6. Add D1 alone -> SHA/CRC/duplicate/unsafe/nested audit -> health probe again.
7. Add D2 -> same audit -> health probe again.
8. If failure first appears immediately after one package mount, record that boundary but do not call the package corrupt until it is independently audited in another healthy session.
9. Reconfirm C2-A || C2-B from current supplied bytes if those files are remounted.

This sequence is specifically intended to distinguish:
- session-sandbox failure;
- cumulative mount/resource pressure;
- a package-specific malformed archive.

## 6. Physical recovery target
Once a healthy container is confirmed:
- complete 9/9 previous-baseline byte audit;
- recover/reimplement RFV2 under the frozen prereresult contract;
- fresh DB59 retrieval/propagation/equivalence/tamper/regression validation;
- propagate into canonical 5 Parts / 9 Packages;
- each package: changed -> new SHA, or unchanged -> byte-identical proof;
- audit 9/9 SHA256, CRC, duplicate=0, unsafe=0, nested ZIP PASS, C2 reassembly, DB59 authority, secret=0;
- rebuild Manifest + Trust Root;
- align Developer Hub + Session Recovery Pointer;
- physically deliver all current 9 packages to the developer.

Only then declare `CURRENT_PHYSICAL_AUTHORITY`.

## 7. New-session mandatory hard blocks
Until P07-A physical closure:
- RFV3 generation: BLOCKED
- CP1 live: BLOCKED
- official R-F: BLOCKED
- R-G freeze: BLOCKED
- Formal R140: HARD BLOCK

## 8. Status token
`CURRENT_SESSION_CONTAINER_UNUSABLE__PART_D_NOT_PROVEN_CAUSAL__FRESH_SESSION_FAILOVER_REQUIRED_FOR_PHYSICAL_PACKAGE_RECOVERY__P07A_PHYSICAL_CLOSURE_PENDING__R140_HARD_BLOCK`
