# CURRENT SESSION RECOVERY POINTER
Last updated: 2026-09-16

## READ FIRST
`handoff/20260916/START_HERE_SYNC_R53_POSTSESSION_RESEARCH_HANDOFF_R1.md`

Machine-readable state:
`handoff/20260916/R53_POSTSESSION_RESEARCH_STATUS_AND_RESUME_R1.json`

Mandatory runtime / container / Hub safety addendum:
`handoff/20260916/RUNTIME_CONTAINER_AND_HUB_FAILURE_PREVENTION_PROTOCOL_R1.md`

The safety addendum is mandatory before large ZIP/BIN work. It separates runtime/transport, memory/I/O, package integrity, custody/delivery, Hub concurrency/search-index, audit-script, compute-timeout, and scientific failures. GitHub existence/update checks must use exact repository contents paths and the latest blob SHA; code-search zero results are not evidence of absence. Large reconstruction must use streaming I/O, explicit free-space budgeting, and page-cache management.

## PHYSICAL RECOVERY ROOT
**SYNC-R53** is the last complete developer-held 5-Part / 9-Package baseline.

Order:
`CONTROL -> A -> B1 -> B2 -> C1 -> C2-A -> C2-B -> D1 -> D2`

Changed at R53:
`CONTROL / A / B2 / C1 / C2-A / C2-B`

Byte-unchanged at R53:
`B1 / D1 / D2`

Do not recover from R52 unless R53 bytes are genuinely unavailable. Do not treat R54/R55/R56 local build names as physical authority.

## CURRENT DIRECT RECOVERY CHECKPOINT
In the healthy 2026-09-16 runtime, `CONTROL / A / B1 / B2 / C1 / C2-A / C2-B` have now been directly reverified as `7/9` of the R53 transport set.

Confirmed:
- CONTROL/A/B1/B2 outer integrity/safety PASS from the earlier checkpoint.
- C1 SHA256 `b2a06fa2add7f66d31d7ebf32a5264be9431e38b56f098b4241a2858e7da8cf4`; ZIP CRC/safety PASS; manifest 4/4 PASS.
- C2-A SHA256 `aeb14bd4523466445411c8d6c00e38557e4847fce944eb314506ebb19dbc653f`.
- C2-B SHA256 `ee85bab92b3c6ae52ca338ad0f4d5c04582c7fac2491d62e57ccac219b07af2d`.
- C2-A+B reconstruction: 319,254,266-byte valid ZIP, SHA256 `e51da441f932f4bf445ddb09b62cdb0caf940a209a9649d8518075b6f25bffb9`; CRC/safety PASS; manifest 3/3 PASS.
- C1/C2 Candidate runtime overlay byte-identity PASS, SHA256 `d8c622cef4b3b853814efe896208494b7fb2bd6b2399dd6296adde8e498931ef`.
- Narrative Engine Master reconstructed from C1 part001 + C2 part002 at canonical SHA256 `5ee441168e7f3af2586c1a819170b42d504ea6f2bcf25857f696495cda1bd649`; reconstructed ZIP CRC PASS.
- C1/C2 `research_sync_r53` overlay path set 8/8 and bytes identical.

This is a recovery checkpoint only, not a new authority declaration. D1 and D2 remain required for a fresh 9/9 direct physical verification and DB59 canonical reconstruction.

## CONTAINER / AUDIT SAFETY FINDINGS
- cgroup hard memory limit is 4 GiB; no `memory.events max`, OOM, or OOM-kill events occurred during the extended audit.
- page cache rose during large sequential reads but returned to about 1.08 GiB `memory.current` after `POSIX_FADV_DONTNEED` and temp cleanup.
- `/tmp` and `/mnt/data` share the same overlay filesystem/device here, so `/tmp` protects mounted inputs semantically but does not provide separate disk capacity; reconstruction must pre-budget output size and free-space headroom.
- `/dev/shm` is memory-backed and should not be used for large reconstruction without explicit memory budgeting.
- `xxd` was absent; this produced an `AUDIT_SCRIPT` status-127 event, not package corruption. Portable `od`/Python replacement succeeded. Do not assume optional shell utilities exist.

## RECOVERED RESEARCH STATE
Preserve the full upper-layer lineage UL-1..UL-10 plus:

### UL-11
Blind Continuation Integrity & Isolation Gate. Reported preflight: `24/24 PASS`.

### UL-12
Fresh-Context Provider Qualification Runner. Reported preflight: `24/24 PASS`. Qualification calls must not use provider conversation carry or `previous_response_id`; stable candidate `chain_id`, unique request `execution_nonce`, and real provider receipts are required.

### UL-13
End-to-End Hierarchical Surface Qualification. Reported internal preflight: `16/16 PASS`. Candidate full surface: 46 scenes / 38,277 chars. Flat Control: 50 scenes / 35,277 chars. External judge responses: `0`.

## DELIVERY / RUNTIME FAILURE TO REMEMBER
R56 B2 was not reliably present on the user-visible conversation file surface, and the prior session container later failed even on minimal I/O with `TransportTimeoutError`. Therefore future physical successors require explicit attachment/download 9/9 plus durable archive evidence.

Historical/runtime investigations established that `TransportTimeoutError`, `ClientError`, `GeneratedFileUploadError`, page-cache pressure, GitHub/DNS failure, shell/audit-script errors, stale GitHub blob SHA conflicts, search-index delay, and missing user-visible attachment are distinct failure domains. None should be collapsed into package corruption or scientific FAIL without direct evidence.

## EXACT NEXT EXECUTION ORDER
1. Run the mandatory runtime/container/Hub safety preflight.
2. Verify D1 and D2 transport bytes and manifests.
3. Reconstruct DB59 and require canonical SHA256 `a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`.
4. Seal fresh R53 9/9 physical verification; do not change R53 authority merely because verification completes.
5. Reapply post-R53 Candidate research overlay, including UL-11/12/13 and prior UL lineage.
6. Build a NEW SYNC successor number; never rewrite R54/R55/R56 history.
7. Run the 12-step physical-custody gate and archive/deliver 9/9.
8. Conduct UL-13 Stage-1 external Surface-only blind evaluation; seal responses, then Stage-2 plan reveal/fidelity evaluation.
9. Execute actual OpenAI Responses API qualification in fresh isolated contexts with real provider receipts.
10. Repeat full end-to-end Surface qualification before considering Candidate Production promotion.

## UNCHANGED AUTHORITIES
- Production: ENG:R47
- Candidate Base: P07-I4H Recovery R3
- DB: DB59 frozen (`a5cff0fcd43584220f41a4be85b112c7fc5246977d856797d2676546bccb6bc9`)
- Formal scored total: 137
- Latest Formal: R138
- R140: 0/0/0
- Operational Level-3 claim: SUSPENDED
- Level 4: NOT STARTED

## STATUS TOKEN
`RECOVERY__SYNC_R53_PHYSICAL_ROOT__RUNTIME_HUB_SAFETY_R1_MANDATORY__R53_DIRECT_REVERIFY_7_OF_9__ENGINE_MASTER_PASS__D1_D2_DB59_PENDING__POST_R53_UL11_UL12_UL13_PRESERVED__NO_AUTHORITY_CHANGE`
