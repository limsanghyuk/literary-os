# CURRENT LIBRARY RECOVERY POINTER
Last updated: 2026-10-06

Canonical audit:
`research/operations/20261006/NEW_SESSION_LIBRARY_AND_AUTHORITY_RECONCILIATION_AUDIT_R1.json`

Master recovery:
`handoff/20261006/START_HERE_NEW_SESSION_MASTER_RECOVERY_R26.md`

## Direct Library inspection order / 직접 조사 순서
1. `/Literary_OS`
2. `/Literary_OS/Physical_Archive/SYNC_R77_CURRENT_9PACKAGES`
3. `/Literary_OS/Research_Candidates/UL22AB_CANONICAL`
4. `/Literary_OS/Research_Candidates/UL18_CANONICAL`
5. `/Literary_OS/Research_DB/DB64_R134`

## Expected current observations
- SYNC-R77 physical packages: 9/9 visible
- UL22AB canonical research runtime: 1/1 visible, 18,755,256 bytes
- UL18 canonical historical candidate: 1/1 visible
- DB64-R134: current lookup 0 visible; raw custody unproven

Do not equate Library listing with raw-byte custody.
For any executable candidate, materialize -> size -> SHA256 -> ZIP/CRC before use.
